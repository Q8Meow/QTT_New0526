import copy
import json
from pathlib import Path

from tools import run_validation_gates as runner
from tools import validate_atomicrows_owner_approved_exact_15_family_count_distribution as gate


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_config() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.DEFAULT_CONFIG)


def _load_schema() -> dict:
    return gate.load_json(REPO_ROOT / gate.DEFAULT_SCHEMA)


def _validated_report() -> dict:
    result = gate.validate(repo_root=REPO_ROOT)
    assert result.ok, result.failures
    assert result.report is not None
    return result.report


def test_static_yaml_validates_against_schema_and_validator_emits_marker(capsys):
    config = _load_config()
    schema = _load_schema()

    failures, _ = gate.validate_distribution_payload(config, schema)
    assert failures == []

    exit_code = gate.main(["--repo-root", str(REPO_ROOT)])

    assert exit_code == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_report_is_deterministic_and_records_owner_distribution_authority():
    report = _validated_report()
    first = gate.serialize_report(report)
    second = gate.serialize_report(json.loads(first))

    assert first == second
    assert report["generated_at_utc"] == "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
    assert report["report_type"] == gate.REPORT_TYPE
    assert report["artifact_id"] == gate.ARTIFACT_ID
    assert report["validation_result"] == gate.VALIDATION_RESULT
    assert report["validator_stdout_marker"] == gate.SUCCESS_MARKER
    assert report["owner_distribution_approval_created"] is True
    assert report["owner_approval_scope"] == gate.APPROVAL_SCOPE
    assert report["distribution_authority"] == gate.DISTRIBUTION_AUTHORITY
    assert report["distribution_authority_class"] == gate.DISTRIBUTION_AUTHORITY_CLASS
    assert report["target_total_row_count"] == 4183
    assert report["family_count_total"] == 15
    assert report["counts_sum"] == 4183
    assert report["row_ranges_contiguous"] is True
    assert report["final_row_index"] == 4183


def test_distribution_order_counts_sum_and_row_ranges_are_computed():
    config = _load_config()
    _, row_ranges = gate.validate_distribution_payload(config, _load_schema())

    assert [(item["family_number"], item["family_slug"], item["target_row_count"]) for item in config["distribution"]] == list(
        gate.FAMILY_DISTRIBUTION
    )
    assert sum(item["target_row_count"] for item in config["distribution"]) == 4183
    assert row_ranges == gate.compute_row_ranges()
    assert row_ranges[0] == {
        "family_number": 1,
        "family_slug": "001_signal_features",
        "target_row_count": 390,
        "row_index_start": 1,
        "row_index_end": 390,
    }
    assert row_ranges[-1] == {
        "family_number": 15,
        "family_slug": "015_quantum_portfolio_hybrid_comparator",
        "target_row_count": 283,
        "row_index_start": 3901,
        "row_index_end": 4183,
    }
    for previous, current in zip(row_ranges, row_ranges[1:]):
        assert previous["row_index_end"] + 1 == current["row_index_start"]

    mutated = copy.deepcopy(config)
    mutated["distribution"][0]["target_row_count"] = 391
    failures, _ = gate.validate_distribution_payload(mutated, _load_schema())
    assert any("target_row_count" in failure or "sum" in failure for failure in failures)

    mutated = copy.deepcopy(config)
    mutated["distribution"][0], mutated["distribution"][1] = (
        mutated["distribution"][1],
        mutated["distribution"][0],
    )
    failures, _ = gate.validate_distribution_payload(mutated, _load_schema())
    assert any("canonical" in failure or "family_number" in failure for failure in failures)


def test_quantum_forward_distribution_is_metadata_only():
    config = _load_config()
    report = _validated_report()
    quantum = config["quantum_forward_distribution"]

    assert tuple(quantum["quantum_family_slugs"]) == gate.QUANTUM_FAMILY_SLUGS
    assert quantum["quantum_family_total_rows"] == 1103
    assert report["quantum_family_total_rows"] == 1103
    assert report["quantum_forward_family_metadata_preserved"] is True
    assert report["quantum_metadata_future_requirement_scope_only"] is True
    for field in gate.QUANTUM_FALSE_FIELDS:
        assert quantum[field] is False
    assert report["quantum_execution_created"] is False
    assert report["quantum_backend_executed"] is False
    assert report["quantum_advantage_claim_created"] is False
    assert report["quantum_advantage_evidence_created"] is False


def test_agent_governance_distribution_grants_no_access_or_assignments():
    config = _load_config()
    report = _validated_report()
    agent = config["agent_governance_distribution"]

    assert agent["primary_agent_governance_family"] == "009_lifecycle_agent_binding"
    assert agent["primary_agent_governance_family_rows"] == 270
    assert report["agent_governance_family_rows"] == 270
    assert agent["deny_by_default_agent_access_preserved"] is True
    assert agent["future_agent_governance_row_kinds_preserved"] is True
    for field in gate.AGENT_GOVERNANCE_FALSE_FIELDS:
        assert agent[field] is False
    assert agent["agent_family_assignment_matrix_future_required"] is True
    assert report["agent_family_assignment_matrix_future_required"] is True
    assert report["specific_agent_family_assignments_created"] is False
    assert report["specific_agent_row_assignments_created"] is False
    assert report["distribution_counts_grant_agent_access"] is False
    assert report["distribution_counts_grant_trading_authority"] is False
    assert report["distribution_counts_grant_live_authority"] is False
    assert report["distribution_counts_grant_order_authority"] is False
    assert report["distribution_counts_grant_quantum_backend_authority"] is False


def test_no_forbidden_outputs_or_authority_are_created_and_master_plan_is_unchanged():
    config = _load_config()
    report = _validated_report()
    forbidden = report["forbidden_artifacts_absent"]

    for field in gate.NOT_AUTHORIZED_FALSE_FIELDS:
        assert config["not_authorized_by_this_approval"][field] is False
    for field in gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert forbidden["exact_row_sources"] is True
    assert forbidden["AtomicRows.bundle.jsonl"] is True
    assert forbidden["AtomicRows.bundle.sha256"] is True
    assert forbidden["specific_agent_family_assignment_artifact"] is True
    assert forbidden["specific_agent_row_assignment_artifact"] is True
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/exact_row_sources").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()
    assert report["master_plan_unchanged"] is True


def test_repair_chain_and_manifest_currentization_are_proven():
    report = _validated_report()

    assert report["repair_pr_a_bridge_preserved"] is True
    assert report["repair_pr_b_manifest_currentized"] is True
    assert report["pr98_blueprints_remain_not_exact_rows"] is True
    assert report["pr99_path_b_remains_historical_until_exact_rows_generated"] is True
    assert report["pr100_sha_freeze_gate_remains_blocked_until_bundle_exists"] is True


def test_schema_rejects_bad_authority_claims_through_validator():
    config = _load_config()

    mutated = copy.deepcopy(config)
    mutated["not_authorized_by_this_approval"]["bundle_created"] = True
    failures, _ = gate.validate_distribution_payload(mutated, _load_schema())
    assert any("bundle_created" in failure for failure in failures)

    mutated = copy.deepcopy(config)
    mutated["agent_governance_distribution"]["specific_agent_family_assignments_created"] = True
    failures, _ = gate.validate_distribution_payload(mutated, _load_schema())
    assert any("specific_agent_family_assignments_created" in failure for failure in failures)

    mutated = copy.deepcopy(config)
    mutated["quantum_forward_distribution"]["quantum_advantage_claim_created"] = True
    failures, _ = gate.validate_distribution_payload(mutated, _load_schema())
    assert any("quantum_advantage_claim_created" in failure for failure in failures)


def test_run_validation_gates_includes_c0_between_repair_a_and_repair_b(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    bridge_index = command_names.index(
        "validate_atomicrows_exact_row_authority_classifier_bridge.py"
    )
    c0_index = command_names.index(
        "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py"
    )
    manifest_index = command_names.index(
        "validate_atomicrows_exact_row_expansion_manifest.py"
    )
    generated_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )

    assert bridge_index < c0_index < manifest_index < generated_index
    assert commands[c0_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py"
        ),
    ]
