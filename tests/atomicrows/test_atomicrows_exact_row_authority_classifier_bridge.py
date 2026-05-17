import json
from pathlib import Path

from tools import run_validation_gates as runner
from tools import validate_atomicrows_exact_row_authority_classifier_bridge as gate


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

    assert gate.validate_config_payload(config, schema) == []

    exit_code = gate.main(["--repo-root", str(REPO_ROOT)])

    assert exit_code == 0
    assert gate.SUCCESS_MARKER in capsys.readouterr().out


def test_report_is_deterministic_and_preserves_core_repair_a_facts():
    report = _validated_report()
    first = gate.serialize_report(report)
    second = gate.serialize_report(json.loads(first))

    assert first == second
    assert report["generated_at_utc"] == "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
    assert report["report_type"] == "ATOMICROWS_EXACT_ROW_AUTHORITY_CLASSIFIER_BRIDGE_REPORT"
    assert report["artifact_id"] == "ATOMICROWS_EXACT_ROW_AUTHORITY_CLASSIFIER_BRIDGE"
    assert report["validation_result"] == "PASS"
    assert report["validator_stdout_marker"] == gate.SUCCESS_MARKER
    assert report["bridge_created"] is True
    assert report["exact_rows_created"] is False
    assert report["atomicrows_bundle_jsonl_created"] is False
    assert report["atomicrows_bundle_sha256_created"] is False
    assert report["sha_computed"] is False
    assert report["freeze_authority_created"] is False
    assert report["final_readiness_created"] is False
    assert report["current_target_total_rows"] == 4183
    assert report["target_total_row_count_is_planning_only_until_exact_rows_generated"] is True
    assert report["pr97_expansion_plan_present"] is True
    assert report["pr98_blueprints_are_not_exact_rows"] is True
    assert report["pr99_path_b_remains_current_blocked_state"] is True
    assert report["pr100_sha_freeze_gate_remains_blocked"] is True
    assert report["master_plan_unchanged"] is True


def test_authority_classes_and_field_fill_rules_are_complete_and_fail_closed():
    config = _load_config()
    report = _validated_report()

    assert tuple(config["authority_classes"]) == gate.REQUIRED_AUTHORITY_CLASSES
    assert tuple(report["authority_classes"]) == gate.REQUIRED_AUTHORITY_CLASSES
    assert tuple(
        entry["authority_class"] for entry in config["field_authority_handling"]
    ) == gate.REQUIRED_AUTHORITY_CLASSES

    handling = {
        entry["authority_class"]: entry for entry in config["field_authority_handling"]
    }
    for authority in gate.REQUIRED_AUTHORITY_CLASSES:
        assert handling[authority]["value_policy"]
    for authority in gate.INTERNAL_AUTHORITY_CLASSES:
        assert handling[authority]["source_pointer_required"] is True
        assert handling[authority]["block_code_required"] is False
        assert handling[authority]["block_code"] is None

    rules = {rule["rule_id"]: rule for rule in config["field_fill_rules"]}
    assert tuple(rules) == gate.REQUIRED_FIELD_FILL_RULE_IDS
    assert rules["EXTERNAL_FACT_RULE"]["authority_classes"] == [
        "ACCEPTED_SOURCE_EVIDENCE_REQUIRED"
    ]
    assert rules["EXTERNAL_FACT_RULE"]["block_code"] == "SOURCE_EVIDENCE_REQUIRED"
    assert rules["RUNTIME_PRIVATE_STATE_RULE"]["authority_classes"] == [
        "RUNTIME_RECEIPT_REQUIRED"
    ]
    assert rules["RUNTIME_PRIVATE_STATE_RULE"]["block_code"] == "RUNTIME_RECEIPT_REQUIRED"
    assert rules["REPLAY_RESULT_RULE"]["authority_classes"] == ["REPLAY_RESULT_REQUIRED"]
    assert rules["REPLAY_RESULT_RULE"]["block_code"] == "REPLAY_RESULT_REQUIRED"
    assert rules["PAPER_RESULT_RULE"]["authority_classes"] == ["PAPER_RESULT_REQUIRED"]
    assert rules["PAPER_RESULT_RULE"]["block_code"] == "PAPER_RESULT_REQUIRED"
    assert rules["OPTIMIZER_RESULT_RULE"]["authority_classes"] == [
        "OPTIMIZER_RESULT_REQUIRED"
    ]
    assert rules["OPTIMIZER_RESULT_RULE"]["block_code"] == "OPTIMIZER_RESULT_REQUIRED"
    assert rules["QUANTUM_BACKEND_RESULT_RULE"]["authority_classes"] == [
        "QUANTUM_BACKEND_RECEIPT_REQUIRED"
    ]
    assert (
        rules["QUANTUM_BACKEND_RESULT_RULE"]["block_code"]
        == "QUANTUM_BACKEND_RECEIPT_REQUIRED"
    )
    assert "NO_RUNTIME_RECEIPT_INVENTION" in rules["NO_FABRICATION_RULE"]["value_policy"]
    assert "NO_QUANTUM_BACKEND_OUTPUT_INVENTION" in rules["NO_FABRICATION_RULE"]["value_policy"]
    assert report["owner_approval_cannot_fabricate_bundle_rows_or_external_evidence"] is True


def test_row_doctrine_architecture_future_files_row_id_law_and_recovery_sequence():
    config = _load_config()
    report = _validated_report()

    doctrine = config["row_field_doctrine"]
    assert doctrine["every_future_exact_row_field_requires_value_or_null"] is True
    assert doctrine["every_future_exact_row_field_requires_authority_class"] is True
    assert doctrine["internally_sourced_fields_require_source_pointer"] is True
    assert doctrine["blocked_fields_require_block_code"] is True
    assert doctrine["every_future_exact_row_requires_agent_eligibility_block"] is True
    assert doctrine["unknown_authority_allowed"] is False
    assert doctrine["blank_authority_class_allowed"] is False

    assert report["canonical_row_fill_architecture_defined"] is True
    architecture = config["canonical_row_fill_architecture"]
    assert architecture["row_family_expansion_manifest_future_only"] is True
    assert architecture["field_authority_classifier_required"] is True
    assert architecture["deterministic_row_generator_future_only"] is True
    assert architecture["owner_review_gate_future_only"] is True
    assert architecture["bundle_materializer_future_only"] is True
    assert architecture["sha_freeze_materializer_future_only"] is True
    assert architecture["final_readiness_gate_future_only"] is True
    components = {
        item["component_id"]: item
        for item in architecture["AtomicRowsExactRowMaterializationBridge"]
    }
    assert components["ROW_FAMILY_EXPANSION_MANIFEST"]["creates_rows_by_itself"] is False
    assert components["BUNDLE_MATERIALIZER"]["future_pr_only"] is True
    assert components["SHA_FREEZE_MATERIALIZER"]["future_pr_only"] is True
    assert components["FINAL_READINESS_GATE"]["future_pr_only"] is True

    strategy = config["future_row_file_strategy"]
    assert report["future_row_file_strategy_defined"] is True
    assert strategy["exact_row_source_directory"] == "docs/master_plan/atomic_rows/exact_row_sources/"
    assert tuple(strategy["exact_row_source_files"]) == gate.REQUIRED_EXACT_ROW_SOURCE_FILES
    assert strategy["bundle_output"] == "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl"
    assert strategy["sha_output"] == "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256"
    assert strategy["future_only_no_files_created_by_this_pr"] is True
    assert (REPO_ROOT / "docs/master_plan/atomic_rows/exact_row_sources").is_dir()
    assert (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl").exists()
    assert not (REPO_ROOT / "docs/master_plan/atomic_rows/AtomicRows.bundle.sha256").exists()
    for field in gate.FUTURE_VALIDATOR_TRUE_FIELDS:
        assert strategy["future_validators_must_prove"][field] is True

    row_id_law = config["future_row_id_law"]
    assert report["future_row_id_law_defined"] is True
    assert row_id_law["format"] == "AR_EXACT_<family_number>_<family_slug>_<six_digit_family_index>"
    assert row_id_law["example"] == "AR_EXACT_012_QUANTUM_ADVISORY_OPTIMIZATION_000001"
    assert row_id_law["deterministic"] is True
    assert row_id_law["hand_invented_ad_hoc_ids_allowed"] is False
    assert row_id_law["row_ids_encode_family_number_family_slug_and_family_local_index"] is True
    assert (
        row_id_law["global_row_index_rule"]
        == "CUMULATIVE_PRIOR_FAMILY_ROW_COUNT_PLUS_ROW_INDEX_WITHIN_FAMILY"
    )

    schema_doctrine = config["future_exact_row_schema_doctrine"]
    assert report["future_exact_row_schema_doctrine_defined"] is True
    assert tuple(schema_doctrine["required_fields"]) == gate.REQUIRED_FUTURE_ROW_SCHEMA_FIELDS
    assert "agent_eligibility" in schema_doctrine["required_fields"]
    assert schema_doctrine["live_order_authority_allowed_default"] is False
    assert schema_doctrine["direct_quantum_order_authority_allowed_default"] is False
    assert schema_doctrine["quantum_execution_allowed_default"] is False
    assert schema_doctrine["quantum_advantage_claim_allowed_default"] is False
    assert schema_doctrine["profit_evidence_created_default"] is False
    assert schema_doctrine["latency_evidence_created_default"] is False
    assert schema_doctrine["execution_superiority_evidence_created_default"] is False
    assert schema_doctrine["quantum_advantage_evidence_created_default"] is False

    sequence = config["recovery_pr_sequence_doctrine"]["sequence"]
    assert report["recovery_pr_sequence_doctrine_defined"] is True
    assert [item["repair_pr"] for item in sequence] == [
        "Repair PR A",
        "Repair PR B",
        "Repair PR C",
        "Repair PR D",
        "Repair PR E",
        "Repair PR F",
        "Roadmap PR #101",
    ]
    assert sequence[0]["creates_exact_rows"] is False
    assert sequence[0]["creates_bundle"] is False
    assert sequence[0]["creates_sha_freeze"] is False


def test_agent_eligibility_governance_is_deny_by_default_and_access_scoped():
    config = _load_config()
    report = _validated_report()
    governance = config["agent_eligibility_governance"]

    assert report["agent_eligibility_governance_required"] is True
    assert report["agent_access_policy_rows_required"] is True
    assert report["deny_by_default_agent_access_policy_required"] is True
    assert governance["required_for_every_future_exact_row"] is True
    assert governance["deny_by_default"] is True
    assert governance["row_existence_grants_access"] is False
    assert governance["family_membership_grants_access"] is False
    assert governance["parameter_existence_grants_access"] is False
    assert governance["algorithm_applicability_grants_access"] is False
    assert governance["quantum_applicability_grants_access"] is False
    assert governance["owner_quantum_priority_grants_access"] is False
    assert governance["replay_paper_eligibility_grants_live_access"] is False
    assert governance["static_selection_eligibility_grants_order_authority"] is False
    assert governance["static_handoff_eligibility_grants_order_authority"] is False
    assert governance["missing_agent_binding_blocks_access"] is True
    assert governance["missing_algorithm_binding_blocks_access"] is True
    assert governance["missing_command_matrix_blocks_access"] is True
    assert governance["unknown_eligibility_state_blocks_access"] is True
    assert governance["live_use_allowed_default"] is False
    assert governance["direct_order_authority_allowed_default"] is False
    assert governance["direct_quantum_order_authority_allowed_default"] is False
    assert governance["owner_override_allowed_for_internal_access"] is True
    assert governance["owner_override_cannot_create_external_fact_or_runtime_receipt"] is True
    assert (
        governance[
            "owner_override_cannot_create_agent_live_order_authority_without_later_live_scope"
        ]
        is True
    )

    block = governance["default_agent_eligibility_block"]
    for field in gate.DEFAULT_AGENT_ELIGIBILITY_ARRAY_FIELDS:
        assert block[field] == []
    assert block["access_decision_default"] == "DENY"
    assert block["access_grant_state"] == "BLOCKED_UNTIL_AGENT_BINDING_AND_OWNER_POLICY_PASS"
    assert block["live_use_allowed"] is False
    assert block["direct_order_authority_allowed"] is False
    assert block["direct_quantum_order_authority_allowed"] is False

    assert tuple(config["future_governance_row_kinds"]) == gate.REQUIRED_GOVERNANCE_ROW_KINDS
    assert tuple(config["access_states"]) == gate.REQUIRED_ACCESS_STATES
    assert tuple(config["agent_access_evaluator_decision_order"]) == gate.REQUIRED_ACCESS_DECISION_STEPS
    assert config["agent_access_default_decision"] == "DENY"
    assert (
        config["future_exact_row_family_governance"]["primary_policy_row_file"]
        == "009_lifecycle_agent_binding.exact_rows.jsonl"
    )
    assert tuple(
        config["future_exact_row_family_governance"][
            "policy_rows_may_cross_reference_families"
        ]
    ) == gate.REQUIRED_CROSS_REFERENCE_FAMILIES


def test_forbidden_artifacts_absent_master_plan_unchanged_and_no_runtime_authority_created():
    config = _load_config()
    report = _validated_report()

    assert report["forbidden_artifacts_absent"] == {
        "AtomicRows.bundle.jsonl": False,
        "AtomicRows.bundle.sha256": True,
        "exact_row_sources": True,
    }
    assert report["exact_row_source_directory_exists"] is True
    assert len(report["exact_row_source_files_found"]) == 15
    assert report["current_exact_row_sources_presence_allowed_by_repair_pr_d"] is True
    assert (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (REPO_ROOT / gate.EXACT_ROW_SOURCES_DIR).is_dir()
    assert gate.validate_master_plan_not_modified(REPO_ROOT) == []
    assert gate.validate_static_surface(REPO_ROOT / "tools" / f"{Path(gate.__file__).stem}.py") == []

    no_authority = config["no_authority_created"]
    for field in gate.NO_AUTHORITY_FALSE_FIELDS:
        assert no_authority[field] is False
        assert report["no_authority_created"][field] is False
    assert no_authority["exact_rows_created"] is False
    assert no_authority["atomicrows_bundle_jsonl_created"] is False
    assert no_authority["atomicrows_bundle_sha256_created"] is False
    assert no_authority["sha_computed"] is False
    assert no_authority["freeze_authority_created"] is False
    assert no_authority["final_readiness_created"] is False
    assert no_authority["runtime_live_order_authority_created"] is False
    assert no_authority["source_fact_authority_created"] is False
    assert no_authority["connector_semantic_authority_created"] is False
    assert no_authority["profit_evidence_created"] is False
    assert no_authority["latency_evidence_created"] is False
    assert no_authority["execution_superiority_evidence_created"] is False
    assert no_authority["quantum_backend_authority_created"] is False
    assert no_authority["quantum_advantage_evidence_created"] is False


def test_run_validation_gates_includes_bridge_after_pr100_and_before_terminal_gates(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr97_index = command_names.index("validate_atomicrows_full_bundle_row_expansion_plan.py")
    pr98_index = command_names.index("validate_atomicrows_bundle_row_family_source_files.py")
    pr99_index = command_names.index(
        "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py"
    )
    pr100_index = command_names.index("validate_atomicrows_bundle_sha_freeze_authority_gate.py")
    bridge_index = command_names.index(
        "validate_atomicrows_exact_row_authority_classifier_bridge.py"
    )
    generated_index = command_names.index("validate_generated_derivative_bootstrap_gate_static.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr97_index < pr98_index < pr99_index < pr100_index < bridge_index
    assert bridge_index < generated_index < no_runtime_index
    assert commands[bridge_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_exact_row_authority_classifier_bridge.py"),
    ]
