import copy
import json
from pathlib import Path

from tools import validate_owner_dashboard_approval_static_screen_contract as gate


REPO_ROOT = Path(".")
_REPORT_CACHE: dict | None = None


def _report() -> dict:
    global _REPORT_CACHE
    if _REPORT_CACHE is None:
        assert gate.main([]) == 0
        _REPORT_CACHE = json.loads((REPO_ROOT / gate.DEFAULT_REPORT).read_text(encoding="utf-8"))
    return _REPORT_CACHE


def _packet() -> dict:
    return _report()["owner_dashboard_approval_static_screen_contract_packet"]


def _screens() -> list[dict]:
    return _packet()["screens"]


def _screen(screen_id: str) -> dict:
    for item in _screens():
        if item["screen_id"] == screen_id:
            return item
    raise AssertionError(f"missing screen: {screen_id}")


def _components() -> list[dict]:
    return [
        component
        for screen in _screens()
        for component in screen["components"]
    ]


def _component(component_id: str) -> dict:
    for item in _components():
        if item["component_id"] == component_id:
            return item
    raise AssertionError(f"missing component: {component_id}")


def _registry() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.DEFAULT_PRODUCTION_REGISTRY)


def _write_registry(tmp_path: Path, registry: dict) -> Path:
    path = tmp_path / "mutated_owner_dashboard_approval_static_screen_contract.json"
    path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _validate_mutated_registry(tmp_path: Path, registry: dict) -> gate.ValidationResult:
    return gate.validate(
        repo_root=REPO_ROOT,
        registry_path=_write_registry(tmp_path, registry),
        output_path=tmp_path / "OwnerDashboardApprovalStaticScreenContract.report.json",
    )


def test_pr96_metadata_and_owner_prompt_semantic_task_id_are_verified():
    report = _report()

    assert report["roadmap_pr_label"] == "PR #96"
    assert report["github_pr_number_policy"] == "may differ"
    assert report["semantic_task_id"] == gate.SEMANTIC_TASK_ID
    assert report["semantic_task_id_source"] == "owner prompt semantic task controls"
    assert report["blueprint_semantic_task_id"] == gate.BLUEPRINT_SEMANTIC_TASK_ID
    assert report["validator_marker"] == gate.SUCCESS_MARKER
    assert report["upstream_pr93_report_marker"] == "QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY_OK"
    assert report["upstream_pr94_report_marker"] == "QTT_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE_OK"
    assert report["upstream_pr95_report_marker"] == "QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_OK"


def test_owner_dashboard_approval_static_screen_contract_is_deterministic_across_runs():
    assert gate.main([]) == 0
    first_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    first_report = json.loads(first_report_bytes)

    assert gate.main([]) == 0
    second_report_bytes = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()
    second_report = json.loads(second_report_bytes)

    assert first_report_bytes == second_report_bytes
    assert first_report["screen_count"] == second_report["screen_count"]
    assert first_report["owner_dashboard_approval_static_screen_contract_packet"]["canonical_screen_order"] == (
        second_report["owner_dashboard_approval_static_screen_contract_packet"]["canonical_screen_order"]
    )


def test_required_screen_concepts_exist_in_stable_order_with_required_components():
    packet = _packet()

    assert packet["canonical_screen_order"] == list(gate.REQUIRED_SCREEN_CONCEPT_ORDER)
    assert packet["screen_class_mapping"] == gate.SCREEN_CLASS_BY_ID
    assert packet["duplicate_screen_id_count"] == 0
    assert packet["duplicate_component_id_count"] == 0
    assert packet["duplicate_route_key_count"] == 0
    for screen_id, component_ids in gate.REQUIRED_COMPONENT_IDS_BY_SCREEN.items():
        assert packet["component_order_by_screen"][screen_id] == list(component_ids)


def test_pr95_menu_refs_are_known_and_scope_concept_mapping_is_explicit():
    packet = _packet()

    assert packet["pr95_canonical_menu_option_ids"] == list(gate.CANONICAL_OPTION_ORDER)
    assert packet["pr95_prompt_concept_to_option_id_map"] == _registry()[
        "pr95_prompt_concept_to_option_id_map"
    ]
    assert packet["canonical_scope_substitution_policy"]["APPLY_TO_ROW"]["option_id"] == (
        "APPLY_TO_ONE_ROW"
    )
    assert packet["canonical_scope_substitution_policy"]["APPLY_TO_FAMILY"]["option_id"] == (
        "APPLY_TO_PARAMETER_FAMILY"
    )
    assert packet["unknown_menu_option_count"] == 0
    assert packet["silent_alias_count"] == 0
    assert set(_screen("OWNER_APPROVAL_MENU_PANEL")["allowed_menu_option_ids"]) == set(
        gate.CANONICAL_OPTION_ORDER
    )


def test_every_screen_and_component_is_static_handoff_only_with_disabled_effects():
    for screen in _screens():
        assert screen["static_only_flag"] is True
        assert screen["handoff_only_flag"] is True
        assert screen["route_creates_runtime_endpoint_flag"] is False
        assert "NO_ACCEPTED_OR_APPLIED_INPUT_VALUE" in screen["required_owner_inputs"]
        for field in gate.SCREEN_NO_AUTHORITY_FLAG_FIELDS:
            assert screen["screen_no_authority_flags"][field] is False
        for blocked in gate.CRITICAL_BLOCKED_EFFECTS:
            assert blocked in screen["blocked_effects"]

    for component in _components():
        assert component["static_display_only_flag"] is True
        for field in gate.COMPONENT_FALSE_FLAG_FIELDS:
            assert component[field] is False
        for disabled in gate.REQUIRED_DISABLED_EFFECTS:
            assert disabled in component["disabled_effects"]


def test_static_relationships_to_pr93_pr94_and_pr95_are_reference_only():
    packet = _packet()

    assert packet["upstream_owner_approval_request_queue_registry_ref"]["validation_marker"] == (
        "QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY_OK"
    )
    assert packet["upstream_owner_override_receipt_authoring_gate_ref"]["validation_marker"] == (
        "QTT_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE_OK"
    )
    assert packet["upstream_owner_dashboard_approval_menu_schema_ref"]["validation_marker"] == (
        "QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_OK"
    )
    assert _component("QUEUE_OVERVIEW_PENDING_REQUEST_LIST")["creates_state_mutation_flag"] is False
    assert _component("CONFIRMATION_NO_RECEIPT_NOTICE")["creates_receipt_flag"] is False


def test_runtime_live_order_source_connector_profit_and_receipt_boundaries_are_zero():
    report = _report()

    for field in gate.NO_AUTHORITY_FLAG_FIELDS:
        assert _packet()[field] is False
        assert report[field] is False
    for field in gate.ZERO_COUNT_FIELDS:
        assert _packet()[field] == 0
        assert report[field] == 0
    assert report["creates_owner_approval_receipt"] is False
    assert report["creates_owner_override_receipt"] is False
    assert report["creates_order_authority"] is False
    assert report["creates_profit_evidence"] is False
    assert report["creates_latency_evidence"] is False


def test_live_runtime_quantum_boundary_options_are_static_metadata_only():
    runtime = _component("BOUNDARY_APPROVE_RUNTIME_METADATA_ONLY")
    live = _component("BOUNDARY_APPROVE_LIVE_USE_METADATA_ONLY")
    quantum = _component("BOUNDARY_APPROVE_QUANTUM_BACKEND_METADATA_ONLY")

    assert runtime["menu_option_ids"] == ["APPROVE_RUNTIME"]
    assert live["menu_option_ids"] == ["APPROVE_LIVE_USE"]
    assert quantum["menu_option_ids"] == ["APPROVE_QUANTUM_BACKEND"]
    for component in [runtime, live, quantum]:
        assert component["creates_runtime_action_flag"] is False
        assert component["creates_live_order_authority_flag"] is False
        assert component["creates_quantum_execution_flag"] is False
        assert component["creates_profit_or_latency_claim_flag"] is False
    assert _component("BOUNDARY_NO_LIVE_ELIGIBILITY")["creates_live_order_authority_flag"] is False
    assert _component("BOUNDARY_NO_ORDER_AUTHORITY")["creates_live_order_authority_flag"] is False
    assert _component("BOUNDARY_NO_QUANTUM_EXECUTION")["creates_quantum_execution_flag"] is False


def test_apply_globally_display_does_not_create_global_mutation():
    global_scope = _component("TARGET_SCOPE_GLOBAL_SCOPE")
    global_block = _component("TARGET_SCOPE_GLOBAL_BLOCKED_EFFECTS")

    assert global_scope["menu_option_ids"] == ["APPLY_GLOBALLY"]
    assert global_block["menu_option_ids"] == ["APPLY_GLOBALLY"]
    assert "GLOBAL_MUTATION" in _packet()["blocked_effects"]
    assert _report()["creates_global_mutation"] is False


def test_atomicrows_pr97_bundle_hash_and_runtime_artifacts_are_absent():
    report = _report()

    forbidden_paths = [
        gate.CANONICAL_BUNDLE_JSONL.as_posix(),
        gate.CANONICAL_BUNDLE_SHA256.as_posix(),
        "docs/master_plan/generated/AtomicRowsFullBundleRowExpansionPlan.report.json",
        "tools/validate_atomicrows_full_bundle_row_expansion_plan.py",
        "tests/atomicrows/test_atomicrows_full_bundle_row_expansion_plan.py",
        "src/qtt/dashboard_runtime",
        "src/qtt/telegram_runtime",
        "src/qtt/owner_dashboard_runtime",
        "src/qtt/dashboard_service",
        "src/qtt/web_server",
    ]
    for path in forbidden_paths:
        assert not (REPO_ROOT / path).exists(), path
    assert report["atomicrows_bundle_jsonl_exists"] is False
    assert report["atomicrows_bundle_sha256_exists"] is False
    assert report["pr97_atomicrows_full_bundle_row_expansion_plan_exists"] is False


def test_missing_required_screen_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["screens"] = [
        screen for screen in registry["screens"] if screen["screen_id"] != "OWNER_APPROVAL_MENU_PANEL"
    ]

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("screen" in failure and "canonical order" in failure for failure in result.failures)


def test_missing_required_component_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    queue_screen = registry["screens"][0]
    queue_screen["components"] = [
        component
        for component in queue_screen["components"]
        if component["component_id"] != "QUEUE_OVERVIEW_PENDING_REQUEST_LIST"
    ]

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("QUEUE_OVERVIEW_PENDING_REQUEST_LIST" in failure for failure in result.failures)


def test_duplicate_screen_component_and_route_ids_fail_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["screens"].append(copy.deepcopy(registry["screens"][0]))
    registry["screens"][0]["components"].append(copy.deepcopy(registry["screens"][0]["components"][0]))
    registry["screens"][1]["route_key_static_only"] = registry["screens"][0]["route_key_static_only"]

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("duplicate screen_id" in failure for failure in result.failures)
    assert any("duplicate component_id" in failure for failure in result.failures)
    assert any("duplicate route_key_static_only" in failure for failure in result.failures)


def test_unknown_pr95_menu_option_and_silent_alias_fail_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["screens"][0]["allowed_menu_option_ids"].append("UNKNOWN_OWNER_MENU_OPTION")

    unknown_result = _validate_mutated_registry(tmp_path, registry)

    assert unknown_result.ok is False
    assert any("UNKNOWN_OWNER_MENU_OPTION" in failure for failure in unknown_result.failures)

    alias_registry = copy.deepcopy(_registry())
    alias_registry["screens"][0]["components"][0]["menu_option_ids"].append("APPLY_TO_ROW")

    alias_result = _validate_mutated_registry(tmp_path, alias_registry)

    assert alias_result.ok is False
    assert any("APPLY_TO_ROW" in failure for failure in alias_result.failures)


def test_unknown_component_class_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["screens"][0]["components"][0]["component_class"] = "UNKNOWN_COMPONENT_CLASS"

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("UNKNOWN_COMPONENT_CLASS" in failure for failure in result.failures)


def test_executable_route_endpoint_or_callback_fails_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["screens"][0]["route_key_static_only"] = "/owner/approve"
    registry["screens"][0]["route_creates_runtime_endpoint_flag"] = True

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("route_key_static_only" in failure for failure in result.failures)
    assert any("route_creates_runtime_endpoint_flag" in failure for failure in result.failures)


def test_dashboard_runtime_ui_service_and_receipt_claims_fail_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["creates_dashboard_runtime_service_flag"] = True
    registry["creates_dashboard_runtime_ui_flag"] = True
    registry["creates_owner_approval_receipt_flag"] = True
    registry["creates_owner_override_receipt_flag"] = True
    registry["screens"][0]["components"][0]["creates_receipt_flag"] = True

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("creates_dashboard_runtime_service_flag" in failure for failure in result.failures)
    assert any("creates_dashboard_runtime_ui_flag" in failure for failure in result.failures)
    assert any("creates_owner_approval_receipt_flag" in failure for failure in result.failures)
    assert any("creates_owner_override_receipt_flag" in failure for failure in result.failures)
    assert any("creates_receipt_flag" in failure for failure in result.failures)


def test_source_connector_runtime_live_order_profit_claims_fail_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["creates_source_fact_flag"] = True
    registry["creates_connector_semantic_flag"] = True
    registry["creates_runtime_cash_receipt_flag"] = True
    registry["creates_live_promotion_flag"] = True
    registry["creates_order_authority_flag"] = True
    registry["creates_order_submission_flag"] = True
    registry["creates_profit_evidence_flag"] = True
    registry["creates_latency_evidence_flag"] = True

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    for field in [
        "creates_source_fact_flag",
        "creates_connector_semantic_flag",
        "creates_runtime_cash_receipt_flag",
        "creates_live_promotion_flag",
        "creates_order_authority_flag",
        "creates_order_submission_flag",
        "creates_profit_evidence_flag",
        "creates_latency_evidence_flag",
    ]:
        assert any(field in failure for failure in result.failures)


def test_quantum_backend_execution_and_advantage_claims_fail_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["creates_quantum_backend_execution_flag"] = True
    registry["creates_quantum_advantage_evidence_flag"] = True
    registry["screens"][-1]["components"][2]["creates_quantum_execution_flag"] = True

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    assert any("creates_quantum_backend_execution_flag" in failure for failure in result.failures)
    assert any("creates_quantum_advantage_evidence_flag" in failure for failure in result.failures)
    assert any("creates_quantum_execution_flag" in failure for failure in result.failures)


def test_atomicrows_bundle_hash_and_pr97_plan_claims_fail_closed(tmp_path):
    registry = copy.deepcopy(_registry())
    registry["no_authority_flags"]["creates_atomicrows_bundle_jsonl"] = True
    registry["no_authority_flags"]["creates_atomicrows_bundle_sha256"] = True
    registry["no_authority_flags"]["creates_pr97_atomicrows_full_bundle_row_expansion_plan"] = True
    registry["no_authority_flags"]["creates_atomicrows_row_family_source_files"] = True
    registry["no_authority_flags"]["creates_atomicrows_bundle_builder"] = True

    result = _validate_mutated_registry(tmp_path, registry)

    assert result.ok is False
    for field in [
        "creates_atomicrows_bundle_jsonl",
        "creates_atomicrows_bundle_sha256",
        "creates_pr97_atomicrows_full_bundle_row_expansion_plan",
        "creates_atomicrows_row_family_source_files",
        "creates_atomicrows_bundle_builder",
    ]:
        assert any(field in failure for failure in result.failures)
