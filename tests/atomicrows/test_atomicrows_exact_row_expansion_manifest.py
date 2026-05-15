import copy
import json
from pathlib import Path

from tools import run_validation_gates as runner
from tools import validate_atomicrows_exact_row_expansion_manifest as gate


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_config() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.DEFAULT_CONFIG)


def _load_schema() -> dict:
    return gate.load_json(REPO_ROOT / gate.DEFAULT_SCHEMA)


def _load_pr97_plan() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.PR97_PLAN)


def _load_pr97_report() -> dict:
    return gate.load_json(REPO_ROOT / gate.PR97_REPORT)


def _load_pr97_schema() -> dict:
    return gate.load_json(REPO_ROOT / gate.PR97_SCHEMA)


def _validated_report() -> dict:
    result = gate.validate(repo_root=REPO_ROOT)
    assert result.ok, result.failures
    assert result.report is not None
    return result.report


def test_static_yaml_validates_against_schema_and_validator_emits_marker(capsys):
    config = _load_config()
    schema = _load_schema()
    derivation = gate.derive_current_distribution(
        REPO_ROOT, _load_pr97_plan(), _load_pr97_report(), _load_pr97_schema()
    )

    assert gate.validate_config_payload(config, schema, derivation) == []

    exit_code = gate.main(["--repo-root", str(REPO_ROOT)])

    assert exit_code == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_report_is_deterministic_and_currentized_to_c0_distribution():
    report = _validated_report()
    first = gate.serialize_report(report)
    second = gate.serialize_report(json.loads(first))

    assert first == second
    assert report["generated_at_utc"] == "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
    assert report["report_type"] == "ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST_REPORT"
    assert report["artifact_id"] == "ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST"
    assert report["validation_result"] == gate.PASS_OWNER_APPROVED_DISTRIBUTION_READY
    assert report["validator_stdout_marker"] == gate.SUCCESS_MARKER
    assert report["manifest_created"] is True
    assert report["manifest_state"] == gate.EXACT_DISTRIBUTION_READY_STATE
    assert report["exact_distribution_ready"] is True
    assert report["owner_distribution_required"] is False
    assert report["distribution_authority"] == gate.OWNER_APPROVED_COUNT_AUTHORITY
    assert report["distribution_source_pointer"] == gate.OWNER_APPROVED_DISTRIBUTION_CONFIG.as_posix()
    assert report["owner_required_decision"] is None
    assert report["family_counts_sum"] == 4183
    assert report["row_ranges_contiguous"] is True
    assert report["final_row_index"] == 4183
    assert report["pr97_missing_count_finding_preserved"] is True
    assert report["historical_owner_distribution_required_before_c0"] is True
    assert report["c0_owner_distribution_supplied"] is True


def test_owner_approved_counts_order_and_ranges_are_computed():
    config = _load_config()
    report = _validated_report()
    derivation = gate.derive_current_distribution(
        REPO_ROOT, _load_pr97_plan(), _load_pr97_report(), _load_pr97_schema()
    )

    assert derivation.source == gate.OWNER_APPROVED_COUNT_AUTHORITY
    assert derivation.family_counts_sum == 4183
    assert derivation.row_ranges_contiguous is True
    assert derivation.final_row_index == 4183
    assert [family["family_slug"] for family in config["families"]] == list(
        gate.REQUIRED_FAMILY_SLUGS
    )
    assert [family["family_slug"] for family in report["families"]] == list(
        gate.REQUIRED_FAMILY_SLUGS
    )
    for family in config["families"]:
        slug = family["family_slug"]
        assert family["target_row_count"] == derivation.counts[slug]
        assert family["count_authority"] == gate.OWNER_APPROVED_COUNT_AUTHORITY
        assert family["distribution_state"] == gate.EXACT_DISTRIBUTION_READY_STATE
        assert (
            family["owner_review_state"]
            == "OWNER_EXACT_DISTRIBUTION_APPROVED_NO_ROWS_CREATED"
        )
        assert (family["row_index_start"], family["row_index_end"]) == derivation.ranges[slug]
    assert derivation.ranges["001_signal_features"] == (1, 390)
    assert derivation.ranges["002_scoring_ranking"] == (391, 720)
    assert derivation.ranges["003_normalization_calibration"] == (721, 940)
    assert derivation.ranges["004_risk_control"] == (941, 1255)
    assert derivation.ranges["005_execution_connector_boundary"] == (1256, 1535)
    assert derivation.ranges["006_capital_sizing_cash"] == (1536, 1755)
    assert derivation.ranges["007_latency_routing"] == (1756, 2005)
    assert derivation.ranges["008_error_guard_fail_closed"] == (2006, 2225)
    assert derivation.ranges["009_lifecycle_agent_binding"] == (2226, 2495)
    assert derivation.ranges["010_source_evidence_connector_semantic"] == (2496, 2810)
    assert derivation.ranges["011_replay_paper_validation"] == (2811, 3080)
    assert derivation.ranges["012_quantum_advisory_optimization"] == (3081, 3370)
    assert derivation.ranges["013_quantum_qubo_ising_metadata"] == (3371, 3635)
    assert derivation.ranges["014_quantum_qaoa_vqe_annealing_metadata"] == (3636, 3900)
    assert derivation.ranges["015_quantum_portfolio_hybrid_comparator"] == (3901, 4183)

    mutated = copy.deepcopy(config)
    mutated["families"][0]["row_index_end"] = 391
    failures = gate.validate_config_payload(mutated, _load_schema(), derivation)
    assert any("row_index range" in failure for failure in failures)


def test_pr97_missing_count_finding_remains_historical_context():
    current = gate.derive_pr97_explicit_distribution(
        _load_pr97_plan(), _load_pr97_report(), _load_pr97_schema()
    )
    assert current.validation_result == gate.PASS_BLOCKED_EXPECTED
    assert current.explicit_distribution_found is False
    assert current.counts is None

    config = _load_config()
    derivation = config["count_derivation"]
    assert derivation["pr97_explicit_distribution_checked"] is True
    assert derivation["pr97_explicit_distribution_found"] is False
    assert (
        derivation["pr97_absence_reason"]
        == "PR97_DECLARES_OWNER_REVIEW_REQUIRED_AND_NO_EXACT_PER_FAMILY_COUNTS"
    )
    assert derivation["historical_owner_distribution_required_before_c0"] is True
    assert (
        derivation["historical_owner_required_decision_before_c0"]
        == "EXACT_15_FAMILY_ROW_COUNT_DISTRIBUTION"
    )
    assert derivation["c0_owner_distribution_supplied"] is True


def test_upstream_repair_chain_is_preserved_and_forbidden_artifacts_remain_absent():
    report = _validated_report()

    assert report["pr97_expansion_plan_present"] is True
    assert report["pr98_blueprints_are_not_exact_rows"] is True
    assert report["pr99_path_b_remains_current_blocked_state"] is True
    assert report["pr100_sha_freeze_gate_remains_blocked"] is True
    assert report["repair_pr_a_bridge_present"] is True
    assert report["repair_pr_a_bridge_preserved"] is True
    assert report["repair_pr_a_authority_classifier_preserved"] is True
    assert report["repair_pr_a_agent_eligibility_governance_preserved"] is True
    assert report["forbidden_artifacts_absent"] == {
        "AtomicRows.bundle.jsonl": True,
        "AtomicRows.bundle.sha256": True,
        "exact_row_sources": True,
    }
    assert (REPO_ROOT / "docs/master_plan/atomic_rows/exact_row_sources").is_dir()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()


def test_quantum_forward_families_are_preserved_without_execution_or_advantage_claims():
    config = _load_config()
    report = _validated_report()
    families = {family["family_slug"]: family for family in config["families"]}
    quantum_counts = {
        "012_quantum_advisory_optimization": 290,
        "013_quantum_qubo_ising_metadata": 265,
        "014_quantum_qaoa_vqe_annealing_metadata": 265,
        "015_quantum_portfolio_hybrid_comparator": 283,
    }

    assert sum(quantum_counts.values()) == 1103
    assert report["quantum_forward_families_preserved"] is True
    for slug, expected_count in quantum_counts.items():
        assert families[slug]["target_row_count"] == expected_count
        assert families[slug]["quantum_relevance_class"] == gate.QUANTUM_RELEVANCE_BY_FAMILY[slug]
        assert "QUANTUM_METADATA" in families[slug]["subfamily_classes"]
        for field in gate.QUANTUM_FALSE_FIELDS:
            assert families[slug][field] is False
    assert report["quantum_backend_authority_created"] is False
    assert report["quantum_advantage_evidence_created"] is False


def test_family_009_agent_governance_is_primary_and_deny_by_default():
    config = _load_config()
    report = _validated_report()
    family = config["families"][8]

    assert family["family_slug"] == "009_lifecycle_agent_binding"
    assert family["target_row_count"] == 270
    assert (
        family["agent_governance_relevance_class"]
        == "PRIMARY_AGENT_ROW_ACCESS_GOVERNANCE_FAMILY"
    )
    assert family["future_policy_row_kinds_allowed"] == list(gate.REQUIRED_POLICY_ROW_KINDS)
    assert "AGENT_ACCESS_POLICY" in family["subfamily_classes"]
    assert "FAMILY_ACCESS_POLICY" in family["subfamily_classes"]
    assert family["access_decision_default"] == "DENY"
    for field in gate.AGENT_DENY_FALSE_FIELDS:
        assert family[field] is False
    assert all(
        item["agent_eligibility_governance_required_for_future_rows"] is True
        and item["deny_by_default_agent_access_required"] is True
        for item in config["families"]
    )
    assert report["agent_governance_family_preserved"] is True
    assert report["deny_by_default_agent_access_preserved"] is True
    assert report["distribution_counts_grant_agent_access"] is False
    assert report["distribution_counts_grant_trading_authority"] is False
    assert report["distribution_counts_grant_live_authority"] is False
    assert report["distribution_counts_grant_order_authority"] is False
    assert report["distribution_counts_grant_quantum_backend_authority"] is False
    assert report["specific_agent_family_assignments_created"] is False
    assert report["specific_agent_row_assignments_created"] is False
    assert report["agent_family_assignment_matrix_future_required"] is True


def test_no_authority_or_evidence_is_created_and_master_plan_is_unchanged():
    config = _load_config()
    report = _validated_report()

    for field in gate.NO_AUTHORITY_FALSE_FIELDS:
        assert config["no_authority_created"][field] is False
    for field in (
        "exact_rows_created",
        "exact_row_source_directory_created",
        "atomicrows_bundle_jsonl_created",
        "atomicrows_bundle_sha256_created",
        "sha_computed",
        "freeze_authority_created",
        "final_readiness_created",
        "runtime_live_order_authority_created",
        "source_fact_authority_created",
        "connector_semantic_authority_created",
        "profit_evidence_created",
        "latency_evidence_created",
        "execution_superiority_evidence_created",
        "optimizer_execution_created",
        "quantum_backend_authority_created",
        "quantum_advantage_evidence_created",
        "specific_agent_family_assignments_created",
        "specific_agent_row_assignments_created",
    ):
        assert report[field] is False
    assert report["master_plan_unchanged"] is True


def test_run_validation_gates_includes_manifest_after_bridge_and_before_c0(
    monkeypatch,
):
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
    dry_run_index = command_names.index(
        "validate_atomicrows_exact_row_generator_dry_run_manifest.py"
    )

    assert bridge_index < manifest_index < c0_index < dry_run_index
    assert commands[c0_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py"
        ),
    ]
    assert commands[manifest_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_exact_row_expansion_manifest.py"),
    ]
