import copy
import json
from pathlib import Path

from tools import run_validation_gates as runner
from tools import validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest as gate


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


def _load_chain():
    config = _load_config()
    artifacts, failures = gate.load_chain_artifacts(REPO_ROOT, config)
    assert failures == []
    assert artifacts is not None
    return artifacts


def _exact_row_files() -> list[Path]:
    root = REPO_ROOT / "docs/master_plan/atomic_rows"
    return sorted(root.rglob("*.exact_rows.jsonl")) if root.exists() else []


def test_c1_manifest_schema_validates(capsys):
    config = _load_config()
    schema = _load_schema()

    assert gate.validate_manifest_payload(config, schema, repo_root=REPO_ROOT) == []

    exit_code = gate.main(["--repo-root", str(REPO_ROOT)])

    assert exit_code == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_c1_consumes_all_repair_chain_inputs():
    config = _load_config()
    report = _validated_report()
    failures, present = gate.validate_required_path_existence(config, REPO_ROOT)

    assert failures == []
    for prefix in ("repair_pr_a", "repair_pr_b", "repair_pr_c0", "repair_pr_c"):
        fields = [field for field in present if field.startswith(prefix)]
        assert fields
        assert all(present[field] for field in fields)
    assert report["source_input_audit"]["repair_pr_a_files_present"] is True
    assert report["source_input_audit"]["repair_pr_b_files_present"] is True
    assert report["source_input_audit"]["repair_pr_c0_files_present"] is True
    assert report["source_input_audit"]["repair_pr_c_files_present"] is True


def test_c1_family_distribution_matches_c0_and_dry_run():
    artifacts = _load_chain()
    expected = gate.expected_normalized_ranges()

    assert gate._normalize_c0_ranges(artifacts.repair_pr_c0_report) == expected
    assert gate._normalize_dry_run_ranges(artifacts.repair_pr_c_report) == expected
    assert _load_config()["expected_family_plan"] == gate.expected_family_plan()
    assert _validated_report()["cross_artifact_consistency"]["c0_distribution_matches_dry_run"] is True


def test_c1_total_rows_final_index_and_quantum_total():
    report = _validated_report()
    consistency = report["cross_artifact_consistency"]

    assert consistency["family_count_matches"] is True
    assert consistency["total_rows_match"] is True
    assert consistency["final_row_index_matches"] is True
    assert consistency["dry_run_would_generate_total_rows"] == 4183
    assert consistency["quantum_forward_total_rows_match"] is True


def test_c1_agent_governance_family_consistency():
    report = _validated_report()
    family = next(
        item for item in report["expected_family_plan"] if item["family_id"] == "009_lifecycle_agent_binding"
    )

    assert family["expected_row_count"] == 270
    assert family["expected_agent_governance_family_flag"] is True
    assert report["cross_artifact_consistency"]["agent_governance_family_rows_match"] is True


def test_c1_row_ranges_contiguous_non_overlapping_no_gaps():
    ranges = gate.expected_normalized_ranges()
    covered = []
    for item in ranges:
        covered.extend(range(item["start_row_index"], item["end_row_index"] + 1))

    assert gate.ranges_are_contiguous(ranges) is True
    assert gate.ranges_non_overlapping(ranges) is True
    assert gate.ranges_have_no_gaps(ranges) is True
    assert covered == list(range(1, 4184))


def test_c1_validation_gate_order_is_coherent(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    indices = [command_names.index(name) for name in gate.DEPENDENCY_ORDER]

    assert indices == sorted(indices)
    assert tuple(command_names[index] for index in indices) == gate.DEPENDENCY_ORDER


def test_c1_run_validation_gates_includes_c1():
    text = (REPO_ROOT / "tools/run_validation_gates.py").read_text(encoding="utf-8")

    assert "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py" in text


def test_c1_fail_closed_tests_expose_success_marker():
    text = (REPO_ROOT / "tests/fail_closed/test_run_validation_gates.py").read_text(
        encoding="utf-8"
    )

    assert gate.SUCCESS_MARKER in text
    assert "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py" in text


def test_c1_dry_run_report_does_not_serialize_exact_rows():
    dry_run_report = _load_chain().repair_pr_c_report

    for key in gate.DISALLOWED_TOP_LEVEL_REPORT_KEYS_FOR_EXACT_ROWS:
        assert key not in dry_run_report
    assert gate.count_exact_row_record_shapes(dry_run_report) == 0
    assert gate.has_full_row_id_list(dry_run_report) is False
    assert gate.dry_run_report_serializes_exact_rows(dry_run_report) is False
    assert gate.max_preview_row_ids_per_family(dry_run_report) <= 2


def test_c1_forbidden_artifacts_remain_absent():
    failures, state = gate.validate_forbidden_artifacts(REPO_ROOT)
    report = _validated_report()

    assert failures == []
    assert state.exact_row_sources_directory_exists is False
    assert state.exact_row_sources_allowed_by_repair_pr_d is True
    assert state.bundle_exists is False
    assert state.bundle_sha_exists is False
    assert report["forbidden_artifact_absence"]["exact_row_sources_directory_absent"] is False
    assert report["forbidden_artifact_absence"]["atomicrows_bundle_absent"] is True
    assert report["forbidden_artifact_absence"]["atomicrows_bundle_sha_absent"] is True


def test_c1_accepts_post_d_exact_row_source_jsonl_files_without_creating_them():
    assert len(_exact_row_files()) == 15
    report = _validated_report()
    assert report["forbidden_artifact_absence"]["exact_row_files_absent"] is False
    assert report["post_d_transition_audit"]["repair_pr_c1_did_not_write_exact_rows"] is True


def test_c1_no_sha_freeze_final_readiness():
    config = _load_config()
    report = _validated_report()

    assert config["bundle_sha_written"] is False
    assert config["freeze_created"] is False
    assert config["final_readiness_created"] is False
    assert report["authority_boundary_audit"]["no_sha_created"] is True
    assert report["authority_boundary_audit"]["no_freeze_created"] is True
    assert report["authority_boundary_audit"]["no_final_readiness_created"] is True


def test_c1_no_runtime_live_order_source_connector_profit_authority():
    report = _validated_report()["authority_boundary_audit"]

    assert report["no_runtime_authority_created"] is True
    assert report["no_live_authority_created"] is True
    assert report["no_order_authority_created"] is True
    assert report["no_source_fact_acceptance_created"] is True
    assert report["no_connector_semantic_binding_created"] is True
    assert report["no_profit_evidence_created"] is True


def test_c1_no_replay_paper_optimizer_quantum_backend_execution():
    dry_run = _load_chain().repair_pr_c_report["no_authority_created"]
    report = _validated_report()["authority_boundary_audit"]

    assert dry_run["replay_execution_created"] is False
    assert dry_run["paper_execution_created"] is False
    assert dry_run["optimizer_execution_created"] is False
    assert dry_run["quantum_backend_execution_created"] is False
    assert report["no_replay_paper_execution_created"] is True
    assert report["no_optimizer_execution_created"] is True
    assert report["no_quantum_backend_execution_created"] is True


def test_c1_no_quantum_advantage_or_profit_evidence():
    report = _validated_report()

    assert report["authority_boundary_audit"]["no_quantum_advantage_evidence_created"] is True
    assert report["authority_boundary_audit"]["no_profit_evidence_created"] is True
    assert report["authority_boundary_audit"]["no_latency_evidence_created"] is True
    assert report["authority_boundary_audit"]["no_execution_superiority_evidence_created"] is True
    assert report["quantum_forward_audit"]["no_quantum_advantage_claim"] is True
    assert report["quantum_forward_audit"]["no_quantum_profit_evidence"] is True


def test_c1_quantum_forward_metadata_only():
    config = _load_config()
    report = _validated_report()
    policy = config["quantum_forward_metadata_only_policy"]

    assert tuple(policy["quantum_forward_family_ids"]) == gate.QUANTUM_FORWARD_FAMILY_IDS
    assert policy["quantum_forward_total_rows"] == 1103
    assert policy["quantum_metadata_only"] is True
    assert report["quantum_forward_audit"]["quantum_metadata_only"] is True
    for field in (
        "qaoa_execution_created",
        "vqe_execution_created",
        "annealing_execution_created",
        "qubo_solver_execution_created",
        "ising_solver_execution_created",
    ):
        assert policy[field] is False
        assert report["quantum_forward_audit"][field] is False


def test_c1_agent_eligibility_deny_by_default_matrix_pending():
    config = _load_config()["agent_eligibility_policy"]
    report = _validated_report()["agent_eligibility_audit"]

    assert config["agent_eligibility_required_for_future_rows"] is True
    assert config["deny_by_default_pending_d2_e0"] is True
    assert config["no_specific_agent_family_assignments_created"] is True
    assert config["no_specific_agent_row_assignments_created"] is True
    assert config["repair_pr_d2_e0_agent_family_eligibility_matrix_required"] is True
    assert report["agent_eligibility_required"] is True
    assert report["deny_by_default_pending_d2_e0"] is True


def test_c1_pr_d_preconditions_reported_but_not_executed():
    report = _validated_report()
    pr_d = report["pr_d_readiness_without_materialization"]

    assert pr_d["repair_pr_d_precondition_audit_passed"] is True
    assert pr_d["repair_pr_d_still_required_to_generate_exact_rows"] is False
    assert pr_d["repair_pr_d_not_executed_by_c1"] is True
    assert pr_d["exact_rows_still_absent"] is False
    assert report["post_d_transition_audit"]["current_exact_row_sources_presence_allowed_by_repair_pr_d"] is True


def test_c1_master_plan_not_modified():
    unchanged, failures = gate.expansion_gate.validate_master_plan_not_modified(REPO_ROOT)

    assert unchanged is True
    assert failures == []


def test_c1_validator_writes_only_c1_report():
    config = _load_config()
    upstream_report_fields = [
        "repair_pr_a_authority_classifier_bridge_report_path",
        "repair_pr_b_expansion_report_path",
        "repair_pr_c0_distribution_report_path",
        "repair_pr_c_dry_run_report_path",
    ]
    before = {
        field: (REPO_ROOT / config[field]).read_bytes() for field in upstream_report_fields
    }

    assert gate.main(["--repo-root", str(REPO_ROOT)]) == 0

    after = {
        field: (REPO_ROOT / config[field]).read_bytes() for field in upstream_report_fields
    }
    assert after == before
    assert (REPO_ROOT / gate.DEFAULT_REPORT).exists()
    assert (REPO_ROOT / "docs/master_plan/atomic_rows/exact_row_sources").is_dir()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()


def test_c1_report_validation_result_pass():
    report = _validated_report()
    first = gate.serialize_report(report)
    second = gate.serialize_report(json.loads(first))

    assert report["validation_result"] == "PASS_PRE_MATERIALIZATION_AUDIT_ONLY"
    assert first == second
    assert report == json.loads(first)


def test_c1_validator_fails_closed_on_distribution_or_authority_drift():
    config = _load_config()
    schema = _load_schema()

    mutated = copy.deepcopy(config)
    mutated["expected_family_plan"][0]["expected_row_count"] = 391
    failures = gate.validate_manifest_payload(mutated, schema, repo_root=REPO_ROOT)
    assert any("expected_family_plan" in failure or "expected_row_count" in failure for failure in failures)

    mutated = copy.deepcopy(config)
    mutated["authority_boundary_policy"]["no_quantum_backend_execution_created"] = False
    failures = gate.validate_manifest_payload(mutated, schema, repo_root=REPO_ROOT)
    assert any("no_quantum_backend_execution_created" in failure for failure in failures)
