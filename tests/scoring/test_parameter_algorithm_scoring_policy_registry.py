import copy
import json
from pathlib import Path
import re
import shutil

import pytest

from tools import validate_parameter_algorithm_scoring_policy_registry as gate


REPO_ROOT = Path(".")
BOUNDARY_TMP_ROOT = Path("tests/fixtures/scoring/.tmp/parameter_algorithm_scoring_boundary_case")


def _registry() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.DEFAULT_PRODUCTION_REGISTRY)


def _fixture() -> dict:
    return json.loads((REPO_ROOT / gate.DEFAULT_FIXTURE).read_text(encoding="utf-8"))


def _report() -> dict:
    assert gate.main([]) == 0
    return json.loads((REPO_ROOT / gate.DEFAULT_REPORT).read_text(encoding="utf-8"))


def _component(payload: dict, name: str) -> dict:
    for entry in payload["scoring_components"]:
        if entry["component_name"] == name:
            return entry
    raise AssertionError(f"missing component {name}")


def _formula(payload: dict, formula_id: str) -> dict:
    for entry in payload["formula_definitions"]:
        if entry["formula_id"] == formula_id:
            return entry
    raise AssertionError(f"missing formula {formula_id}")


def _failures(payload: dict) -> list[str]:
    return gate.validate_policy_payload(payload, label="TEST")


def _assert_failure_contains(payload: dict, reason_code: str) -> None:
    failures = _failures(payload)
    assert any(reason_code in failure for failure in failures), failures


def test_validator_emits_success_marker_and_byte_stable_report(capsys):
    assert gate.main([]) == 0
    first_output = capsys.readouterr()
    assert first_output.out.strip() == gate.SUCCESS_MARKER
    first_report = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()

    assert gate.main([]) == 0
    second_output = capsys.readouterr()
    assert second_output.out.strip() == gate.SUCCESS_MARKER
    second_report = (REPO_ROOT / gate.DEFAULT_REPORT).read_bytes()

    assert first_report == second_report


def test_all_required_scoring_components_are_present():
    registry = _registry()
    names = [entry["component_name"] for entry in registry["scoring_components"]]
    assert names == list(gate.COMPONENT_ORDER)
    assert set(gate.LINEAGE_REQUIRED_COMPONENTS).issubset(names)


def test_all_required_formulas_are_present():
    registry = _registry()
    assert [entry["formula_id"] for entry in registry["formula_definitions"]] == list(gate.FORMULA_ORDER)
    assert [entry["output_name"] for entry in registry["formula_definitions"]] == list(gate.FORMULA_OUTPUT_ORDER)


def test_base_score_formula_is_formula_only_without_scoring_execution():
    base = _formula(_registry(), "BASE_SCORE_FORMULA")
    assert base["output_name"] == "base_score"
    assert base["formula_expression"] == gate.FORMULA_EXPECTATIONS["BASE_SCORE_FORMULA"]["formula_expression"]
    assert base["formula_execution_created"] is False
    assert base["scoring_result_created"] is False
    assert base["ranking_created"] is False
    assert base["selection_created"] is False


def test_quantum_boost_formula_is_static_and_references_pr82_pr83_metadata():
    quantum = _formula(_registry(), "QUANTUM_BOOST_FORMULA")
    assert quantum["formula_expression"] == (
        "quantum_applicability_score * quantum_priority_multiplier * "
        "owner_quantum_priority_boost"
    )
    assert quantum["allowed_input_components"] == [
        "quantum_applicability_score",
        "quantum_priority_multiplier",
        "owner_quantum_priority_boost",
    ]
    assert "PR82_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY" in quantum["upstream_metadata_sources"]
    assert "PR83_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY" in quantum["upstream_metadata_sources"]
    assert quantum["formula_execution_created"] is False
    assert quantum["scoring_result_created"] is False


def test_final_selection_score_formula_is_not_selected_stack_or_trade():
    final = _formula(_registry(), "FINAL_SELECTION_SCORE_FORMULA")
    assert final["formula_expression"] == "base_score + quantum_boost"
    assert final["allowed_input_components"] == ["base_score", "quantum_boost"]
    assert final["formula_execution_created"] is False
    assert final["ranking_created"] is False
    assert final["selection_created"] is False


@pytest.mark.parametrize(
    ("component_name", "field"),
    [
        ("expected_net_profit_score", "creates_profit_evidence"),
        ("latency_fit_score", "creates_latency_superiority_evidence"),
        ("optimizer_score", "creates_optimizer_execution"),
        ("runtime_readiness_score", "creates_runtime_readiness_receipt"),
        ("replay_paper_score", "creates_replay_paper_result"),
    ],
)
def test_placeholder_components_do_not_create_evidence_or_execution(component_name, field):
    component = _component(_registry(), component_name)
    assert component[field] is False
    assert component["creates_real_score"] is False


def test_source_currentness_penalty_is_not_source_retrieval_or_acceptance():
    component = _component(_registry(), "source_currentness_penalty")
    assert component["creates_source_retrieval"] is False
    assert component["creates_source_acceptance"] is False


def test_execution_cost_penalty_is_not_venue_fee_tick_or_cost_fact():
    component = _component(_registry(), "execution_cost_penalty")
    assert component["creates_venue_fee_tick_cost_fact"] is False
    assert "NOT_VENUE_FACT" in component["default_static_placeholder_value"]


def test_owner_override_score_is_internal_only_and_cannot_fabricate_external_facts():
    component = _component(_registry(), "owner_override_score")
    assert component["internal_only_flag"] is True
    assert component["creates_source_retrieval"] is False
    assert component["creates_source_acceptance"] is False
    assert component["creates_profit_evidence"] is False


def test_pr84_consumes_pr82_quantum_applicability_metadata():
    failures, labels = gate.validate_pr82_registry(REPO_ROOT)
    assert failures == []
    assert labels == set(gate.PR82_LABEL_ORDER)
    registry = _registry()
    assert registry["pr82_quantum_applicability_metadata_consumed"] is True
    assert _component(registry, "quantum_applicability_score")["consumes_pr82_quantum_applicability_metadata"] is True


def test_pr84_consumes_pr83_owner_quantum_priority_policy_metadata():
    failures, policy = gate.validate_pr83_policy(REPO_ROOT)
    assert failures == []
    assert policy is not None
    registry = _registry()
    assert registry["pr83_owner_quantum_priority_policy_consumed"] is True
    assert _component(registry, "quantum_priority_multiplier")["consumes_pr83_owner_quantum_priority_policy"] is True
    assert _component(registry, "owner_quantum_priority_boost")["consumes_pr83_owner_quantum_priority_policy"] is True


def test_future_pr85_to_pr92_consumer_references_exist_without_execution():
    registry = _registry()
    assert [entry["consumer_id"] for entry in registry["future_consumers"]] == list(gate.FUTURE_CONSUMER_ORDER)
    assert all(entry["pr84_creates_consumer_execution"] is False for entry in registry["future_consumers"])


def test_no_scoring_ranking_selection_optimizer_replay_paper_live_source_connector_profit_or_backend_artifact_created():
    registry = _registry()
    for field in gate.NO_AUTHORITY_FALSE_FIELDS:
        assert registry["required_no_authority_flags"][field] is False
    report = _report()
    for field in gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()


def test_fixture_declares_required_synthetic_cases_and_no_authority():
    fixture = _fixture()
    assert gate.validate_fixture(fixture) == []
    assert fixture["mode"] == "SOURCE_REQUIRED"
    assert fixture["execution"] == "DISABLED"
    assert fixture["formula_registry_only_flag"] is True
    assert fixture["quantum_backend_execution_created"] is False
    assert fixture["optimizer_execution_created"] is False
    assert fixture["profit_evidence_created"] is False


def test_missing_semantic_task_id_blocks():
    payload = copy.deepcopy(_registry())
    payload.pop("semantic_task_id")
    failures = _failures(payload)
    assert any("semantic_task_id" in failure for failure in failures), failures


def test_wrong_semantic_task_id_blocks():
    payload = copy.deepcopy(_registry())
    payload["semantic_task_id"] = "ROADMAP-SCORING-POLICY-REGISTRY"
    failures = _failures(payload)
    assert any(gate.SEMANTIC_TASK_ID in failure for failure in failures), failures


def test_missing_required_component_blocks():
    payload = copy.deepcopy(_registry())
    payload["scoring_components"] = [
        entry for entry in payload["scoring_components"] if entry["component_name"] != "agent_binding_score"
    ]
    _assert_failure_contains(payload, "SCORING_POLICY_BLOCKED_MISSING_REQUIRED_COMPONENT")


def test_duplicate_component_blocks():
    payload = copy.deepcopy(_registry())
    payload["scoring_components"].append(copy.deepcopy(payload["scoring_components"][0]))
    _assert_failure_contains(payload, "SCORING_POLICY_BLOCKED_DUPLICATE_COMPONENT")


def test_unknown_component_blocks():
    payload = copy.deepcopy(_registry())
    payload["scoring_components"][0]["component_name"] = "unknown_component_score"
    _assert_failure_contains(payload, "SCORING_POLICY_BLOCKED_UNKNOWN_COMPONENT")


def test_missing_required_formula_blocks():
    payload = copy.deepcopy(_registry())
    payload["formula_definitions"] = [
        entry for entry in payload["formula_definitions"] if entry["formula_id"] != "BASE_SCORE_FORMULA"
    ]
    _assert_failure_contains(payload, "SCORING_POLICY_BLOCKED_MISSING_REQUIRED_FORMULA")


def test_duplicate_formula_blocks():
    payload = copy.deepcopy(_registry())
    payload["formula_definitions"].append(copy.deepcopy(payload["formula_definitions"][0]))
    _assert_failure_contains(payload, "SCORING_POLICY_BLOCKED_DUPLICATE_FORMULA")


def test_unknown_formula_blocks():
    payload = copy.deepcopy(_registry())
    payload["formula_definitions"][0]["formula_id"] = "UNKNOWN_FORMULA"
    _assert_failure_contains(payload, "SCORING_POLICY_BLOCKED_UNKNOWN_FORMULA")


def test_formula_references_unknown_input_blocks():
    payload = copy.deepcopy(_registry())
    _formula(payload, "BASE_SCORE_FORMULA")["allowed_input_components"].append("unknown_component_score")
    _assert_failure_contains(payload, "SCORING_POLICY_BLOCKED_INVALID_FORMULA_INPUT")


def test_formula_produces_unknown_output_blocks():
    payload = copy.deepcopy(_registry())
    _formula(payload, "BASE_SCORE_FORMULA")["output_name"] = "unknown_score_output"
    _assert_failure_contains(payload, "SCORING_POLICY_BLOCKED_INVALID_FORMULA_OUTPUT")


@pytest.mark.parametrize(
    "missing_input",
    [
        "quantum_applicability_score",
        "quantum_priority_multiplier",
        "owner_quantum_priority_boost",
    ],
)
def test_quantum_boost_missing_required_input_blocks(missing_input):
    payload = copy.deepcopy(_registry())
    formula = _formula(payload, "QUANTUM_BOOST_FORMULA")
    formula["allowed_input_components"] = [
        item for item in formula["allowed_input_components"] if item != missing_input
    ]
    _assert_failure_contains(payload, missing_input)


@pytest.mark.parametrize("missing_input", ["base_score", "quantum_boost"])
def test_final_selection_score_missing_required_input_blocks(missing_input):
    payload = copy.deepcopy(_registry())
    formula = _formula(payload, "FINAL_SELECTION_SCORE_FORMULA")
    formula["allowed_input_components"] = [
        item for item in formula["allowed_input_components"] if item != missing_input
    ]
    _assert_failure_contains(payload, missing_input)


@pytest.mark.parametrize(
    ("formula_field", "reason_code"),
    [
        ("formula_execution_created", "SCORING_POLICY_BLOCKED_FORMULA_EXECUTION_FORBIDDEN"),
        ("scoring_result_created", "SCORING_POLICY_BLOCKED_SCORING_RESULT_FORBIDDEN"),
        ("ranking_created", "SCORING_POLICY_BLOCKED_RANKING_FORBIDDEN"),
        ("selection_created", "SCORING_POLICY_BLOCKED_SELECTION_FORBIDDEN"),
    ],
)
def test_forbidden_formula_claim_fields_block(formula_field, reason_code):
    payload = copy.deepcopy(_registry())
    _formula(payload, "BASE_SCORE_FORMULA")[formula_field] = True
    _assert_failure_contains(payload, reason_code)


@pytest.mark.parametrize(
    ("field", "reason_code"),
    [
        ("optimizer_execution_created", "SCORING_POLICY_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN"),
        ("optimizer_arbitration_created", "SCORING_POLICY_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN"),
        ("quantum_backend_execution_created", "SCORING_POLICY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN"),
        ("quantum_simulator_execution_created", "SCORING_POLICY_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN"),
        ("runtime_authority_created", "SCORING_POLICY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ("live_authority_created", "SCORING_POLICY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ("order_authority_created", "SCORING_POLICY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ("source_retrieval_created", "SCORING_POLICY_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN"),
        ("source_acceptance_created", "SCORING_POLICY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN"),
        ("connector_semantic_binding_created", "SCORING_POLICY_BLOCKED_CONNECTOR_BINDING_FORBIDDEN"),
        ("runtime_cash_receipt_created", "SCORING_POLICY_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN"),
        ("private_state_fetch_created", "SCORING_POLICY_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN"),
        ("profit_evidence_created", "SCORING_POLICY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN"),
        ("quantum_advantage_claim_created", "SCORING_POLICY_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN"),
        ("latency_superiority_claim_created", "SCORING_POLICY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN"),
        ("execution_superiority_claim_created", "SCORING_POLICY_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN"),
        ("random_scoring_policy_used", "SCORING_POLICY_BLOCKED_RANDOM_POLICY_FORBIDDEN"),
        ("atomicrows_bundle_jsonl_created", "SCORING_POLICY_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN"),
        ("atomicrows_bundle_sha256_created", "SCORING_POLICY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN"),
    ],
)
def test_forbidden_no_authority_flags_block(field, reason_code):
    payload = copy.deepcopy(_registry())
    payload["required_no_authority_flags"][field] = True
    _assert_failure_contains(payload, reason_code)


@pytest.mark.parametrize(
    ("component_name", "field", "reason_code"),
    [
        ("replay_paper_score", "creates_replay_paper_result", "SCORING_POLICY_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN"),
        ("expected_net_profit_score", "creates_profit_evidence", "SCORING_POLICY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN"),
        ("latency_fit_score", "creates_latency_superiority_evidence", "SCORING_POLICY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN"),
        ("execution_cost_penalty", "creates_execution_superiority_evidence", "SCORING_POLICY_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN"),
    ],
)
def test_forbidden_component_evidence_flags_block(component_name, field, reason_code):
    payload = copy.deepcopy(_registry())
    _component(payload, component_name)[field] = True
    _assert_failure_contains(payload, reason_code)


def _clean_boundary_tmp_root() -> None:
    if BOUNDARY_TMP_ROOT.exists():
        shutil.rmtree(BOUNDARY_TMP_ROOT)


def _temp_boundary_root() -> Path:
    _clean_boundary_tmp_root()
    (BOUNDARY_TMP_ROOT / gate.PR76_SHORT_TEST).parent.mkdir(parents=True, exist_ok=True)
    (BOUNDARY_TMP_ROOT / gate.PR76_SHORT_TEST).write_text("", encoding="utf-8")
    return BOUNDARY_TMP_ROOT


def test_atomicrows_bundle_jsonl_presence_does_not_create_sha_freeze_authority():
    root = _temp_boundary_root()
    try:
        (root / gate.CANONICAL_BUNDLE_JSONL).parent.mkdir(parents=True, exist_ok=True)
        (root / gate.CANONICAL_BUNDLE_JSONL).write_text("", encoding="utf-8")
        failures = gate.validate_filesystem_boundaries(root)
        assert not any("SCORING_POLICY_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN" in failure for failure in failures)
        assert not (root / gate.CANONICAL_BUNDLE_SHA256).exists()
    finally:
        _clean_boundary_tmp_root()


def test_atomicrows_bundle_sha256_creation_blocks():
    root = _temp_boundary_root()
    try:
        (root / gate.CANONICAL_BUNDLE_SHA256).parent.mkdir(parents=True, exist_ok=True)
        (root / gate.CANONICAL_BUNDLE_SHA256).write_text("", encoding="utf-8")
        failures = gate.validate_filesystem_boundaries(root)
        assert any("SCORING_POLICY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN" in failure for failure in failures)
    finally:
        _clean_boundary_tmp_root()


def test_old_long_runtime_resolver_allowlist_filename_reintroduction_blocks():
    root = _temp_boundary_root()
    try:
        (root / gate.PR76_OLD_LONG_TEST).parent.mkdir(parents=True, exist_ok=True)
        (root / gate.PR76_OLD_LONG_TEST).write_text("", encoding="utf-8")
        failures = gate.validate_filesystem_boundaries(root)
        assert any("old long runtime resolver allowlist filename" in failure for failure in failures)
    finally:
        _clean_boundary_tmp_root()


def test_report_is_deterministic_and_has_no_nondeterministic_leaks():
    report = _report()
    assert gate.validate_report_is_deterministic(report) == []
    serialized = gate.serialize_report(report)
    assert "STATIC_DETERMINISTIC_NO_WALL_CLOCK" in serialized
    assert not re.search(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-", serialized)
    assert not re.search(r"\b20[0-9]{2}-[0-9]{2}-[0-9]{2}T", serialized)
    assert "\\\\" not in serialized


def test_registry_ordering_is_deterministic():
    registry = _registry()
    assert [entry["component_name"] for entry in registry["scoring_components"]] == list(gate.COMPONENT_ORDER)
    assert [entry["formula_id"] for entry in registry["formula_definitions"]] == list(gate.FORMULA_ORDER)
    assert [entry["artifact_id"] for entry in registry["upstream_dependencies"]] == list(gate.DEPENDENCY_ORDER)
    assert [entry["consumer_id"] for entry in registry["future_consumers"]] == list(gate.FUTURE_CONSUMER_ORDER)
    assert registry["reason_codes"] == list(gate.REASON_CODE_ORDER)
