import copy
import json
from pathlib import Path
import re
import shutil

import pytest

from tools import validate_parameter_stack_scoring_and_ranking_gate as gate


REPO_ROOT = Path(".")
BOUNDARY_TMP_ROOT = Path("tests/fixtures/selection/.tmp/parameter_stack_scoring_boundary_case")


def _registry() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.DEFAULT_PRODUCTION_REGISTRY)


def _schema() -> dict:
    return gate.load_json(REPO_ROOT / gate.DEFAULT_SCHEMA)


def _fixture() -> dict:
    return json.loads((REPO_ROOT / gate.DEFAULT_FIXTURE).read_text(encoding="utf-8"))


def _report() -> dict:
    assert gate.main([]) == 0
    return json.loads((REPO_ROOT / gate.DEFAULT_REPORT).read_text(encoding="utf-8"))


def _candidate(payload: dict, candidate_id: str) -> dict:
    for candidate in payload["candidate_stack_descriptors"]:
        if candidate["candidate_stack_descriptor_id"] == candidate_id:
            return candidate
    raise AssertionError(f"missing candidate {candidate_id}")


def _fixture_failures(payload: dict) -> list[str]:
    pr82_failures, labels = gate.pr84_gate.validate_pr82_registry(REPO_ROOT)
    pr83_failures, policy = gate.pr84_gate.validate_pr83_policy(REPO_ROOT)
    assert pr82_failures == []
    assert pr83_failures == []
    failures, _scores = gate.validate_fixture(payload, pr82_labels=labels, pr83_policy=policy)
    return failures


def _registry_failures(payload: dict) -> list[str]:
    failures = gate.schema_subset_failures(payload, _schema(), "TEST")
    failures.extend(gate.validate_gate_payload(payload, repo_root=REPO_ROOT))
    return failures


def _assert_registry_failure_contains(payload: dict, reason_code: str) -> None:
    failures = _registry_failures(payload)
    assert any(reason_code in failure for failure in failures), failures


def _assert_fixture_failure_contains(payload: dict, reason_code: str) -> None:
    failures = _fixture_failures(payload)
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


def test_required_candidate_descriptors_are_present_and_synthetic_static_only():
    fixture = _fixture()
    assert [item["candidate_stack_descriptor_id"] for item in fixture["candidate_stack_descriptors"]] == list(gate.REQUIRED_CANDIDATE_IDS)
    for candidate in fixture["candidate_stack_descriptors"]:
        assert candidate["candidate_descriptor_source"] == "SYNTHETIC_STATIC_FIXTURE_ONLY"
        assert candidate["candidate_descriptor_authority"] == "NON_RUNTIME_NON_LIVE_TEST_FIXTURE"
        assert candidate["real_generated_candidate_claim_created"] is False
        assert candidate["selected_stack_claim_created"] is False
        assert candidate["profit_evidence_created"] is False


def test_pr85_consumes_pr82_pr83_and_pr84_static_metadata():
    report = _report()
    assert report["pr82_quantum_applicability_labels"] == list(gate.pr84_gate.PR82_LABEL_ORDER)
    assert report["pr83_supported_quantum_priority_modes"] == list(gate.pr84_gate.PR83_MODE_ORDER)
    assert report["pr84_formula_ids"] == list(gate.FORMULA_ORDER)
    assert report["policy_source"]["artifact_id"] == "PR84_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY"
    assert report["quantum_applicability_source"]["artifact_id"] == "PR82_QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY"
    assert report["owner_quantum_priority_source"]["artifact_id"] == "PR83_QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY"


def test_deterministic_score_breakdown_and_ranking_are_produced_for_fixtures_only():
    report = _report()
    assert report["ranked_candidate_descriptor_ids"] == [
        "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE",
        "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE",
        "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE",
        "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE",
        "TIE_BREAK_STABILITY_FIXTURE_A",
        "TIE_BREAK_STABILITY_FIXTURE_B",
    ]
    owner = report["static_ranked_candidate_descriptors"][0]
    assert owner["score_breakdown"]["base_score"] == 0.4944
    assert owner["score_breakdown"]["quantum_boost"] == 0.084
    assert owner["score_breakdown"]["final_selection_score"] == 0.5784
    assert owner["eligible_for_future_selection_flag"] is False
    assert owner["selected_stack_claim_created"] is False


def test_ties_are_resolved_by_lexicographic_candidate_id():
    report = _report()
    assert report["ranked_candidate_descriptor_ids"][-2:] == [
        "TIE_BREAK_STABILITY_FIXTURE_A",
        "TIE_BREAK_STABILITY_FIXTURE_B",
    ]
    fixture = _fixture()
    a = _candidate(fixture, "TIE_BREAK_STABILITY_FIXTURE_A")
    b = _candidate(fixture, "TIE_BREAK_STABILITY_FIXTURE_B")
    assert a["score_breakdown"] == b["score_breakdown"]
    assert a["rank"] == 5
    assert b["rank"] == 6


def test_classical_only_remains_valid_comparator_metadata():
    fixture = _fixture()
    classical = _candidate(fixture, "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE")
    assert classical["quantum_applicability_labels"] == ["CLASSICAL_ONLY"]
    assert classical["classical_comparator_metadata_present"] is True
    assert classical["valid_for_ranking_flag"] is True
    assert classical["quantum_advantage_claim_created"] is False


def test_quantum_applicable_fixture_ranks_higher_only_when_owner_policy_permits():
    report = _report()
    ranked = report["ranked_candidate_descriptor_ids"]
    assert ranked.index("QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE") < ranked.index("CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE")

    fixture = _fixture()
    quantum = _candidate(fixture, "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE")
    quantum["owner_quantum_priority_mode"] = "QUANTUM_NEUTRAL"
    _assert_fixture_failure_contains(
        fixture,
        "STACK_SCORING_RANKING_BLOCKED_OWNER_QUANTUM_PRIORITY_NOT_PERMITTED",
    )


def test_hybrid_tiebreak_fixture_requires_classical_comparator_metadata():
    fixture = _fixture()
    hybrid = _candidate(fixture, "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE")
    assert hybrid["classical_comparator_candidate_descriptor_id"] == "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE"
    assert hybrid["classical_comparator_metadata_present"] is True

    hybrid["classical_comparator_metadata_present"] = False
    _assert_fixture_failure_contains(
        fixture,
        "STACK_SCORING_RANKING_BLOCKED_CLASSICAL_COMPARATOR_MISSING",
    )


def test_owner_override_influences_internal_fixture_ranking_only():
    fixture = _fixture()
    owner = _candidate(fixture, "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE")
    assert owner["owner_override_applied"] is True
    assert owner["owner_override_internal_only_flag"] is True
    assert owner["owner_override_external_fact_fabrication_created"] is False
    assert owner["source_retrieval_created"] is False
    assert owner["runtime_cash_receipt_created"] is False
    assert owner["profit_evidence_created"] is False


def test_blocked_candidate_is_traceable_unranked_and_keeps_reason_codes():
    fixture = _fixture()
    blocked = _candidate(fixture, "BLOCKED_INVALID_STACK_FIXTURE")
    assert blocked["valid_for_ranking_flag"] is False
    assert blocked["rank"] is None
    assert blocked["blocked_reason_codes"] == [
        "STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD",
        "STACK_SCORING_RANKING_BLOCKED_UNKNOWN_QUANTUM_APPLICABILITY_LABEL",
    ]
    report = _report()
    assert report["blocked_candidate_descriptor_ids"] == ["BLOCKED_INVALID_STACK_FIXTURE"]


def test_highest_ranked_fixture_is_not_final_selection_and_future_scope_is_not_implemented():
    report = _report()
    assert report["highest_ranked_candidate_descriptor_id"] == "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE"
    assert report["highest_ranked_candidate_is_final_selected_stack"] is False
    assert report["final_selection_score_is_final_selection"] is False
    assert report["future_pr86_optimizer_arbitration_implemented"] is False
    assert report["future_pr87_candidate_generation_implemented"] is False
    assert report["future_pr88_trade_context_selection_implemented"] is False


def test_no_runtime_live_order_source_connector_profit_backend_or_replay_artifacts_created():
    registry = _registry()
    report = _report()
    for field in gate.NO_AUTHORITY_FALSE_FIELDS:
        assert registry["required_no_authority_flags"][field] is False
    for field in gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()


def test_missing_semantic_task_id_blocks():
    payload = _registry()
    payload.pop("semantic_task_id")
    failures = _registry_failures(payload)
    assert any("semantic_task_id" in failure for failure in failures), failures


def test_wrong_semantic_task_id_blocks():
    payload = _registry()
    payload["semantic_task_id"] = "ROADMAP-STACK-SCORING-RANKING-GATE"
    failures = _registry_failures(payload)
    assert any(gate.SEMANTIC_TASK_ID in failure for failure in failures), failures


@pytest.mark.parametrize(
    "dependency_id",
    [
        "PR82_QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY",
        "PR83_QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY",
        "PR84_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY",
    ],
)
def test_missing_required_upstream_dependency_blocks(dependency_id):
    payload = _registry()
    payload["upstream_dependencies"] = [
        item for item in payload["upstream_dependencies"] if item["artifact_id"] != dependency_id
    ]
    _assert_registry_failure_contains(
        payload,
        "STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD",
    )


def test_unknown_candidate_descriptor_blocks():
    payload = _fixture()
    extra = copy.deepcopy(payload["candidate_stack_descriptors"][0])
    extra["candidate_stack_descriptor_id"] = "UNKNOWN_STACK_FIXTURE"
    payload["candidate_stack_descriptors"].append(extra)
    _assert_fixture_failure_contains(
        payload,
        "STACK_SCORING_RANKING_BLOCKED_UNKNOWN_CANDIDATE_DESCRIPTOR",
    )


def test_duplicate_candidate_descriptor_blocks():
    payload = _fixture()
    payload["candidate_stack_descriptors"].append(copy.deepcopy(payload["candidate_stack_descriptors"][0]))
    _assert_fixture_failure_contains(
        payload,
        "STACK_SCORING_RANKING_BLOCKED_DUPLICATE_CANDIDATE_DESCRIPTOR",
    )


def test_candidate_not_marked_synthetic_static_blocks():
    payload = _fixture()
    _candidate(payload, "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE")["candidate_descriptor_source"] = "REAL_GENERATED_CANDIDATE"
    _assert_fixture_failure_contains(
        payload,
        "STACK_SCORING_RANKING_BLOCKED_MISSING_REQUIRED_DESCRIPTOR_FIELD",
    )


@pytest.mark.parametrize(
    ("field", "reason_code"),
    [
        ("real_generated_candidate_claim_created", "STACK_SCORING_RANKING_BLOCKED_REAL_GENERATED_CANDIDATE_CLAIM"),
        ("selected_stack_claim_created", "STACK_SCORING_RANKING_BLOCKED_SELECTED_STACK_FORBIDDEN"),
        ("final_selection_created", "STACK_SCORING_RANKING_BLOCKED_FINAL_SELECTION_FORBIDDEN"),
        ("optimizer_execution_created", "STACK_SCORING_RANKING_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN"),
        ("optimizer_arbitration_created", "STACK_SCORING_RANKING_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN"),
        ("quantum_backend_execution_created", "STACK_SCORING_RANKING_BLOCKED_BACKEND_EXECUTION_FORBIDDEN"),
        ("quantum_simulator_execution_created", "STACK_SCORING_RANKING_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN"),
        ("replay_execution_created", "STACK_SCORING_RANKING_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN"),
        ("paper_execution_created", "STACK_SCORING_RANKING_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN"),
        ("runtime_authority_created", "STACK_SCORING_RANKING_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ("live_authority_created", "STACK_SCORING_RANKING_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ("order_authority_created", "STACK_SCORING_RANKING_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ("source_retrieval_created", "STACK_SCORING_RANKING_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN"),
        ("source_acceptance_created", "STACK_SCORING_RANKING_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN"),
        ("connector_semantic_binding_created", "STACK_SCORING_RANKING_BLOCKED_CONNECTOR_BINDING_FORBIDDEN"),
        ("runtime_cash_receipt_created", "STACK_SCORING_RANKING_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN"),
        ("private_state_fetch_created", "STACK_SCORING_RANKING_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN"),
        ("profit_evidence_created", "STACK_SCORING_RANKING_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN"),
        ("quantum_advantage_claim_created", "STACK_SCORING_RANKING_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN"),
        ("latency_superiority_claim_created", "STACK_SCORING_RANKING_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN"),
        ("execution_superiority_claim_created", "STACK_SCORING_RANKING_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN"),
    ],
)
def test_candidate_forbidden_claim_fields_block(field, reason_code):
    payload = _fixture()
    _candidate(payload, "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE")[field] = True
    _assert_fixture_failure_contains(payload, reason_code)


@pytest.mark.parametrize(
    "field",
    ["real_candidate_stack_generation_created", "final_selection_created", "random_ranking_used"],
)
def test_registry_forbidden_no_authority_flags_block(field):
    payload = _registry()
    payload["required_no_authority_flags"][field] = True
    _assert_registry_failure_contains(payload, gate.FIELD_REASON_CODES[field])


def test_missing_score_breakdown_blocks():
    payload = _fixture()
    _candidate(payload, "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE").pop("score_breakdown")
    _assert_fixture_failure_contains(payload, "STACK_SCORING_RANKING_BLOCKED_MISSING_SCORE_BREAKDOWN")


@pytest.mark.parametrize("field", ["base_score", "quantum_boost", "final_selection_score"])
def test_missing_required_score_breakdown_field_blocks(field):
    payload = _fixture()
    _candidate(payload, "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE")["score_breakdown"].pop(field)
    _assert_fixture_failure_contains(payload, "STACK_SCORING_RANKING_BLOCKED_MISSING_SCORE_BREAKDOWN")


def test_unknown_scoring_component_blocks():
    payload = _fixture()
    inputs = _candidate(payload, "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE")["scoring_component_inputs"]
    inputs["unknown_component_score"] = 0.1
    _assert_fixture_failure_contains(payload, "STACK_SCORING_RANKING_BLOCKED_UNKNOWN_SCORING_COMPONENT")


def test_unknown_pr82_applicability_label_blocks():
    payload = _fixture()
    _candidate(payload, "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE")["quantum_applicability_labels"] = ["UNKNOWN_Q_LABEL"]
    _assert_fixture_failure_contains(payload, "STACK_SCORING_RANKING_BLOCKED_UNKNOWN_QUANTUM_APPLICABILITY_LABEL")


def test_unknown_pr83_owner_quantum_priority_mode_blocks():
    payload = _fixture()
    _candidate(payload, "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE")["owner_quantum_priority_mode"] = "UNKNOWN_QUANTUM_MODE"
    _assert_fixture_failure_contains(payload, "STACK_SCORING_RANKING_BLOCKED_OWNER_QUANTUM_PRIORITY_NOT_PERMITTED")


def test_pr84_formula_mismatch_blocks():
    payload = _fixture()
    _candidate(payload, "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE")["score_breakdown"]["final_selection_score"] = 999
    _assert_fixture_failure_contains(payload, "STACK_SCORING_RANKING_ALLOWED_PR84_FORMULA_POLICY")


def test_random_ranking_policy_blocks():
    payload = _registry()
    payload["ranking_policy"]["random_sort_allowed"] = True
    _assert_registry_failure_contains(payload, "STACK_SCORING_RANKING_BLOCKED_RANDOM_RANKING_FORBIDDEN")


def test_ambiguous_tie_break_policy_blocks():
    payload = _registry()
    payload["ranking_policy"]["tie_break_order"] = payload["ranking_policy"]["tie_break_order"][:-1]
    _assert_registry_failure_contains(payload, "STACK_SCORING_RANKING_BLOCKED_TIE_BREAK_AMBIGUOUS")


def test_hybrid_tiebreak_without_classical_comparator_blocks():
    payload = _fixture()
    hybrid = _candidate(payload, "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE")
    hybrid["classical_comparator_candidate_descriptor_id"] = None
    _assert_fixture_failure_contains(payload, "STACK_SCORING_RANKING_BLOCKED_CLASSICAL_COMPARATOR_MISSING")


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
        assert not any("STACK_SCORING_RANKING_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN" in failure for failure in failures)
        assert not (root / gate.CANONICAL_BUNDLE_SHA256).exists()
    finally:
        _clean_boundary_tmp_root()


def test_atomicrows_bundle_sha256_creation_blocks():
    root = _temp_boundary_root()
    try:
        (root / gate.CANONICAL_BUNDLE_SHA256).parent.mkdir(parents=True, exist_ok=True)
        (root / gate.CANONICAL_BUNDLE_SHA256).write_text("", encoding="utf-8")
        failures = gate.validate_filesystem_boundaries(root)
        assert any("STACK_SCORING_RANKING_BLOCKED_ATOMICROWS_SHA_FORBIDDEN" in failure for failure in failures)
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


def test_output_ordering_is_deterministic():
    report = _report()
    assert report["candidate_descriptor_ids"] == list(gate.REQUIRED_CANDIDATE_IDS)
    assert report["upstream_dependency_ids"] == list(gate.DEPENDENCY_ORDER)
    assert report["future_consumer_ids"] == list(gate.FUTURE_CONSUMER_ORDER)
    assert report["reason_codes"] == list(gate.REASON_CODE_ORDER)
    assert report["deterministic_blocked_candidate_ordering"] is True
