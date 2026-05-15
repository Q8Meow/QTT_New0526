import copy
import json
from pathlib import Path

from tools import run_validation_gates as runner
from tools import validate_atomicrows_exact_row_generator_dry_run_manifest as gate


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


def _exact_row_files() -> list[Path]:
    root = REPO_ROOT / "docs/master_plan/atomic_rows"
    return sorted(root.rglob("*.exact_rows.jsonl")) if root.exists() else []


def test_dry_run_manifest_schema_validates(capsys):
    config = _load_config()
    schema = _load_schema()
    forbidden_failures, forbidden_state = gate.validate_forbidden_artifacts(REPO_ROOT)

    assert forbidden_failures == []
    assert gate.validate_manifest_payload(config, schema, forbidden_state) == []

    exit_code = gate.main(["--repo-root", str(REPO_ROOT)])

    assert exit_code == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_dry_run_consumes_required_repair_chain_inputs():
    config = _load_config()
    report = _validated_report()
    sources, failures = gate._load_sources(REPO_ROOT)

    assert failures == []
    assert sources is not None
    assert gate.validate_source_inputs(sources) == []
    assert config["source_inputs"] == report["source_inputs"]
    assert report["checks"]["source_inputs_present"] is True
    assert report["checks"]["source_inputs_consumed"] is True
    assert config["source_inputs"]["authority_classifier_bridge_path"] == gate.AUTHORITY_CLASSIFIER_BRIDGE_PATH.as_posix()
    assert config["source_inputs"]["expansion_manifest_path"] == gate.EXPANSION_MANIFEST_PATH.as_posix()
    assert config["source_inputs"]["owner_approved_distribution_path"] == gate.OWNER_APPROVED_DISTRIBUTION_PATH.as_posix()


def test_dry_run_family_counts_match_c0_exactly():
    config = _load_config()
    report = _validated_report()
    expected_ranges = gate.compute_family_ranges()

    assert [entry["family_id"] for entry in config["family_generation_plan"]] == list(
        gate.REQUIRED_FAMILY_IDS
    )
    assert [entry["family_id"] for entry in report["family_generation_plan"]] == list(
        gate.REQUIRED_FAMILY_IDS
    )
    for expected, manifest_entry, report_entry in zip(
        expected_ranges, config["family_generation_plan"], report["family_generation_plan"]
    ):
        assert manifest_entry["family_id"] == expected.family_id
        assert manifest_entry["row_count"] == expected.row_count
        assert manifest_entry["start_row_index"] == expected.start_row_index
        assert manifest_entry["end_row_index"] == expected.end_row_index
        assert report_entry["family_id"] == expected.family_id
        assert report_entry["row_count"] == expected.row_count
        assert report_entry["start_row_index"] == expected.start_row_index
        assert report_entry["end_row_index"] == expected.end_row_index


def test_dry_run_total_and_final_index():
    report = _validated_report()

    assert report["actual_dry_run"]["would_generate_total_rows"] == 4183
    assert report["actual_dry_run"]["family_count"] == 15
    assert report["actual_dry_run"]["first_row_index"] == 1
    assert report["actual_dry_run"]["final_row_index"] == 4183
    assert report["checks"]["total_rows_match"] is True
    assert report["checks"]["final_row_index_matches"] is True


def test_dry_run_row_ranges_contiguous_no_gaps_no_overlaps():
    ranges = gate.compute_family_ranges()
    covered = []
    for item in ranges:
        covered.extend(range(item.start_row_index, item.end_row_index + 1))

    assert gate.ranges_are_contiguous(ranges) is True
    assert gate.ranges_non_overlapping(ranges) is True
    assert gate.ranges_have_no_gaps(ranges) is True
    assert covered == list(range(1, 4184))


def test_dry_run_row_ids_are_deterministic():
    first = [
        gate.generate_row_id_preview("001_signal_features", 1),
        gate.generate_row_id_preview("001_signal_features", 390),
        gate.generate_row_id_preview("015_quantum_portfolio_hybrid_comparator", 283),
    ]
    second = [
        gate.generate_row_id_preview("001_signal_features", 1),
        gate.generate_row_id_preview("001_signal_features", 390),
        gate.generate_row_id_preview("015_quantum_portfolio_hybrid_comparator", 283),
    ]
    config = _load_config()

    assert first == second
    assert first == [
        "AR_EXACT_001_SIGNAL_FEATURES_000001",
        "AR_EXACT_001_SIGNAL_FEATURES_000390",
        "AR_EXACT_015_QUANTUM_PORTFOLIO_HYBRID_COMPARATOR_000283",
    ]
    assert config["row_id_generation_policy"]["deterministic"] is True
    assert config["row_id_generation_policy"]["no_randomization"] is True
    assert config["row_id_generation_policy"]["no_timestamp_in_row_id"] is True
    assert config["row_id_generation_policy"]["no_environment_dependent_value_in_row_id"] is True
    assert config["row_id_generation_policy"]["no_filesystem_order_dependency"] is True


def test_dry_run_report_created_without_exact_rows():
    report = _validated_report()
    report_path = REPO_ROOT / gate.DEFAULT_REPORT

    assert report_path.exists()
    assert report["report_type"] == gate.REPORT_TYPE
    assert report["validation_result"] == gate.VALIDATION_RESULT
    assert report["exact_rows_written"] is False
    assert _exact_row_files() == []
    assert gate._contains_large_exact_row_list(report) is False
    assert "exact_rows" not in report
    assert "source_rows" not in report


def test_dry_run_forbidden_artifacts_remain_absent():
    failures, forbidden_state = gate.validate_forbidden_artifacts(REPO_ROOT)
    report = _validated_report()

    assert failures == []
    assert forbidden_state.exact_row_sources_directory_created is False
    assert forbidden_state.bundle_written is False
    assert forbidden_state.bundle_sha_written is False
    assert forbidden_state.exact_row_files == ()
    assert report["forbidden_artifact_absence"]["exact_row_sources_directory_absent"] is True
    assert report["forbidden_artifact_absence"]["AtomicRows.bundle.jsonl_absent"] is True
    assert report["forbidden_artifact_absence"]["AtomicRows.bundle.sha256_absent"] is True
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/exact_row_sources").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()


def test_dry_run_no_sha_freeze_final_readiness():
    config = _load_config()
    report = _validated_report()

    assert config["bundle_sha_written"] is False
    assert config["freeze_created"] is False
    assert config["final_readiness_created"] is False
    assert config["no_authority_created"]["sha_computed"] is False
    assert config["no_authority_created"]["freeze_authority_created"] is False
    assert config["no_authority_created"]["final_readiness_created"] is False
    assert report["bundle_sha_written"] is False
    assert report["freeze_created"] is False
    assert report["final_readiness_created"] is False
    assert report["no_authority_created"]["sha_computed"] is False


def test_dry_run_authority_source_pointer_block_code_policy_for_all_rows():
    report = _validated_report()
    field_plan = report["field_presence_plan"]

    assert field_plan["total_future_rows_checked_in_memory"] == 4183
    assert field_plan["planned_authority_class_present_count"] == 4183
    assert field_plan["planned_source_pointer_policy_present_count"] == 4183
    assert field_plan["planned_block_code_policy_present_count"] == 4183
    assert report["checks"]["authority_class_policy_present_for_all_future_rows"] is True
    assert report["checks"]["source_pointer_policy_present_for_all_future_rows"] is True
    assert report["checks"]["block_code_policy_present_for_all_future_rows"] is True


def test_dry_run_agent_eligibility_required_but_no_specific_assignments():
    config = _load_config()
    report = _validated_report()

    assert config["agent_eligibility_policy"]["agent_eligibility_required"] is True
    assert config["agent_eligibility_policy"]["future_eligibility_matrix_required"] is True
    assert config["agent_eligibility_policy"]["specific_agent_family_assignments_created"] is False
    assert config["agent_eligibility_policy"]["specific_agent_row_assignments_created"] is False
    assert config["agent_eligibility_policy"]["live_order_agent_authority_created"] is False
    assert config["agent_eligibility_policy"]["quantum_backend_agent_authority_created"] is False
    assert report["field_presence_plan"]["planned_agent_eligibility_present_count"] == 4183
    assert report["checks"]["agent_eligibility_policy_present_for_all_future_rows"] is True
    assert report["blocked_future_work"]["repair_pr_d2_e0_agent_family_eligibility_matrix_required"] is True
    assert report["no_authority_created"]["specific_agent_family_assignments_created"] is False
    assert report["no_authority_created"]["specific_agent_row_assignments_created"] is False


def test_dry_run_quantum_forward_metadata_only():
    report = _validated_report()
    families = {entry["family_id"]: entry for entry in report["family_generation_plan"]}

    assert report["actual_dry_run"]["quantum_forward_total_rows"] == 1103
    assert report["checks"]["quantum_forward_metadata_policy_present_for_quantum_families"] is True
    for family_id, metadata_class in gate.QUANTUM_METADATA_CLASSES.items():
        family = families[family_id]
        assert family["quantum_forward_family_flag"] is True
        assert family["quantum_metadata_authority"] == "METADATA_ONLY_NOT_BACKEND_OUTPUT"
        assert family["quantum_metadata_class"] == metadata_class
        assert family["quantum_backend_execution_created"] is False
        assert family["quantum_simulator_execution_created"] is False
        assert family["quantum_provider_execution_created"] is False
        assert family["quantum_advantage_claim_created"] is False
        assert family["quantum_profit_evidence_created"] is False
    assert report["no_authority_created"]["quantum_backend_execution_created"] is False
    assert report["no_authority_created"]["quantum_provider_execution_created"] is False
    assert report["no_authority_created"]["quantum_advantage_evidence_created"] is False


def test_dry_run_no_external_fact_or_connector_semantic_authority():
    config = _load_config()
    report = _validated_report()

    assert config["source_pointer_policy"]["source_facts_retrieved_by_this_pr"] is False
    assert config["source_pointer_policy"]["source_facts_accepted_by_this_pr"] is False
    assert config["source_pointer_policy"]["connector_semantics_populated_by_this_pr"] is False
    assert config["source_pointer_policy"]["external_fact_authority_created_by_this_pr"] is False
    assert config["source_pointer_policy"]["source_required_policy_for_missing_external_facts"] == "SOURCE_EVIDENCE_REQUIRED"
    assert report["checks"]["no_source_fact_acceptance_created"] is True
    assert report["checks"]["no_connector_semantic_binding_created"] is True
    assert report["checks"]["no_venue_api_provider_facts_fabricated"] is True
    assert report["no_authority_created"]["source_fact_acceptance_created"] is False
    assert report["no_authority_created"]["connector_semantic_binding_created"] is False


def test_run_validation_gates_includes_dry_run_gate(monkeypatch):
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
    manifest_index = command_names.index("validate_atomicrows_exact_row_expansion_manifest.py")
    dry_run_index = command_names.index(
        "validate_atomicrows_exact_row_generator_dry_run_manifest.py"
    )
    generated_index = command_names.index("validate_generated_derivative_bootstrap_gate_static.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert bridge_index < c0_index < manifest_index < dry_run_index < generated_index
    assert dry_run_index < no_runtime_index
    assert commands[dry_run_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_exact_row_generator_dry_run_manifest.py"),
    ]
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/exact_row_sources").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()


def test_master_plan_not_modified_by_repair_pr_c():
    modified, failures = gate.expansion_gate.validate_master_plan_not_modified(REPO_ROOT)

    assert modified is True
    assert failures == []


def test_no_exact_row_sources_directory_created_by_validator():
    assert gate.main(["--repo-root", str(REPO_ROOT)]) == 0
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/exact_row_sources").exists()
    assert _exact_row_files() == []


def test_no_bundle_or_sha_created_by_validator():
    assert gate.main(["--repo-root", str(REPO_ROOT)]) == 0
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()


def test_dry_run_validator_fails_closed_on_authority_claims():
    config = _load_config()
    schema = _load_schema()
    forbidden_failures, forbidden_state = gate.validate_forbidden_artifacts(REPO_ROOT)
    assert forbidden_failures == []

    mutated = copy.deepcopy(config)
    mutated["no_authority_created"]["quantum_backend_execution_created"] = True
    failures = gate.validate_manifest_payload(mutated, schema, forbidden_state)
    assert any("quantum_backend_execution_created" in failure for failure in failures)

    mutated = copy.deepcopy(config)
    mutated["family_generation_plan"][0]["row_count"] = 391
    failures = gate.validate_manifest_payload(mutated, schema, forbidden_state)
    assert any("row_count" in failure for failure in failures)

    mutated = copy.deepcopy(config)
    mutated["agent_eligibility_policy"]["specific_agent_row_assignments_created"] = True
    failures = gate.validate_manifest_payload(mutated, schema, forbidden_state)
    assert any("specific_agent_row_assignments_created" in failure for failure in failures)


def test_dry_run_report_is_deterministic_json():
    report = _validated_report()
    first = gate.serialize_report(report)
    second = gate.serialize_report(json.loads(first))

    assert first == second
    assert report == json.loads(first)
