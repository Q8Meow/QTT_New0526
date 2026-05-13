import copy
import json
from pathlib import Path
import re
import shutil

import pytest

from tools import validate_quantum_classical_optimizer_arbitration_gate as gate


REPO_ROOT = Path(".")
BOUNDARY_TMP_ROOT = Path("tests/fixtures/quantum/.tmp/optimizer_arbitration_boundary_case")


def _registry() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.DEFAULT_PRODUCTION_REGISTRY)


def _schema() -> dict:
    return gate.load_json(REPO_ROOT / gate.DEFAULT_SCHEMA)


def _fixture() -> dict:
    return json.loads((REPO_ROOT / gate.DEFAULT_FIXTURE).read_text(encoding="utf-8"))


def _report() -> dict:
    assert gate.main([]) == 0
    return json.loads((REPO_ROOT / gate.DEFAULT_REPORT).read_text(encoding="utf-8"))


def _arbitration_fixture(payload: dict, fixture_id: str) -> dict:
    for item in payload["optimizer_arbitration_fixtures"]:
        if item["arbitration_fixture_id"] == fixture_id:
            return item
    raise AssertionError(f"missing arbitration fixture {fixture_id}")


def _fixture_failures(payload: dict) -> list[str]:
    pr82_failures, labels = gate.pr85_gate.pr84_gate.validate_pr82_registry(REPO_ROOT)
    pr83_failures, policy = gate.pr85_gate.pr84_gate.validate_pr83_policy(REPO_ROOT)
    pr85_failures, pr85_report = gate.validate_pr85_gate(REPO_ROOT)
    assert pr82_failures == []
    assert pr83_failures == []
    assert pr85_failures == []
    return gate.validate_fixture(
        payload,
        pr82_labels=labels,
        pr83_policy=policy,
        pr85_report=pr85_report,
    )


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


def test_required_arbitration_modes_are_present():
    registry = _registry()
    assert registry["arbitration_modes"] == list(gate.ARBITRATION_MODE_ORDER)


def test_all_arbitration_fixtures_are_synthetic_static_fixture_only():
    fixture = _fixture()
    assert [item["arbitration_fixture_id"] for item in fixture["optimizer_arbitration_fixtures"]] == list(gate.REQUIRED_ARBITRATION_FIXTURE_IDS)
    for item in fixture["optimizer_arbitration_fixtures"]:
        assert item["arbitration_fixture_source"] == "SYNTHETIC_STATIC_FIXTURE_ONLY"
        assert item["arbitration_fixture_authority"] == "NON_RUNTIME_NON_LIVE_TEST_FIXTURE"
        assert item["arbitration_decision_authority"] == "STATIC_FIXTURE_ONLY_NOT_SELECTION"
        assert item["real_optimizer_result_created"] is False
        assert item["real_generated_candidate_claim_created"] is False
        assert item["selected_stack_claim_created"] is False
        assert item["profit_evidence_created"] is False
        assert item["quantum_advantage_claim_created"] is False


def test_pr86_consumes_pr82_pr83_pr84_and_pr85_static_metadata():
    report = _report()
    assert report["pr82_quantum_applicability_labels"] == list(gate.pr85_gate.pr84_gate.PR82_LABEL_ORDER)
    assert report["pr83_supported_quantum_priority_modes"] == list(gate.pr85_gate.pr84_gate.PR83_MODE_ORDER)
    assert report["pr84_formula_ids"] == list(gate.pr85_gate.FORMULA_ORDER)
    assert report["pr85_ranked_candidate_descriptor_ids"] == [
        "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE",
        "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE",
        "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE",
        "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE",
        "TIE_BREAK_STABILITY_FIXTURE_A",
        "TIE_BREAK_STABILITY_FIXTURE_B",
    ]
    assert report["quantum_applicability_source"]["artifact_id"] == "PR82_QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY"
    assert report["owner_quantum_priority_source"]["artifact_id"] == "PR83_QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY"
    assert report["scoring_policy_source"]["artifact_id"] == "PR84_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY"
    assert report["scoring_ranking_gate_source"]["artifact_id"] == "PR85_PARAMETER_STACK_SCORING_AND_RANKING_GATE"


def test_mode_fixtures_preserve_static_arbitration_semantics():
    fixture = _fixture()
    classical = _arbitration_fixture(fixture, "CLASSICAL_BASELINE_FIXTURE")
    quantum = _arbitration_fixture(fixture, "QUANTUM_CHALLENGER_FIXTURE")
    hybrid = _arbitration_fixture(fixture, "HYBRID_COMPARE_THEN_SELECT_FIXTURE")
    quantum_first = _arbitration_fixture(fixture, "QUANTUM_FIRST_FIXTURE")
    owner_quantum = _arbitration_fixture(fixture, "OWNER_FORCED_QUANTUM_FIXTURE")
    owner_classical = _arbitration_fixture(fixture, "OWNER_FORCED_CLASSICAL_FIXTURE")

    assert classical["arbitration_decision"] == "USE_CLASSICAL_BASELINE_FIXTURE"
    assert classical["classical_comparator_present"] is True
    assert classical["optimizer_execution_created"] is False

    assert quantum["arbitration_decision"] == "USE_QUANTUM_CHALLENGER_FIXTURE"
    assert "TRUE_QUANTUM" in quantum["quantum_applicability_labels"]
    assert quantum["classical_comparator_present"] is True
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_simulator_execution_created"] is False

    assert hybrid["arbitration_decision"] == "USE_HYBRID_COMPARISON_FIXTURE"
    assert hybrid["classical_baseline_fixture_id"] == "CLASSICAL_BASELINE_FIXTURE"
    assert hybrid["quantum_challenger_fixture_id"] == "QUANTUM_CHALLENGER_FIXTURE"
    assert hybrid["final_selection_created"] is False

    assert quantum_first["owner_quantum_priority_mode"] == "QUANTUM_FIRST"
    assert quantum_first["fallback_to_classical_available"] is True

    assert owner_quantum["owner_override_basis"] == "OWNER_GLOBAL_OVERRIDE"
    assert owner_quantum["owner_forced_quantum_applied"] is True
    assert owner_quantum["owner_override_external_fact_fabrication_created"] is False

    assert owner_classical["owner_override_basis"] == "OWNER_FAIL_SAFE_CLASSICAL_FALLBACK"
    assert owner_classical["owner_forced_classical_applied"] is True
    assert owner_classical["quantum_challenger_allowed"] is False


def test_deterministic_arbitration_decisions_and_tie_break_output():
    report = _report()
    assert report["arbitration_ordered_fixture_ids"] == list(gate.EXPECTED_ORDERED_VALID_FIXTURE_IDS)
    assert report["static_arbitration_fixture_decision_ids"] == list(gate.EXPECTED_ORDERED_VALID_FIXTURE_IDS)
    assert report["arbitration_ordered_fixture_ids"][-2:] == [
        "TIEBREAK_ARBITRATION_STABILITY_FIXTURE_A",
        "TIEBREAK_ARBITRATION_STABILITY_FIXTURE_B",
    ]

    fixture = _fixture()
    a = _arbitration_fixture(fixture, "TIEBREAK_ARBITRATION_STABILITY_FIXTURE_A")
    b = _arbitration_fixture(fixture, "TIEBREAK_ARBITRATION_STABILITY_FIXTURE_B")
    assert a["final_selection_score_fixture_metadata"] == b["final_selection_score_fixture_metadata"]
    assert a["base_score_fixture_metadata"] == b["base_score_fixture_metadata"]
    assert a["total_penalty_metadata"] == b["total_penalty_metadata"]
    assert a["uncertainty_metadata"] == b["uncertainty_metadata"]
    assert a["arbitration_order"] == 7
    assert b["arbitration_order"] == 8


def test_blocked_invalid_fixtures_are_traceable_and_unselected():
    fixture = _fixture()
    backend = _arbitration_fixture(fixture, "BLOCKED_BACKEND_EXECUTION_ATTEMPT_FIXTURE")
    missing = _arbitration_fixture(fixture, "BLOCKED_MISSING_CLASSICAL_COMPARATOR_FIXTURE")

    assert backend["arbitration_decision"] == "BLOCK_ARBITRATION_FIXTURE"
    assert backend["valid_for_arbitration_flag"] is False
    assert backend["blocked_reason_codes"] == [
        "OPTIMIZER_ARBITRATION_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN",
        "OPTIMIZER_ARBITRATION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        "OPTIMIZER_ARBITRATION_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
    ]
    assert missing["arbitration_decision"] == "BLOCK_ARBITRATION_FIXTURE"
    assert missing["classical_comparator_required"] is True
    assert missing["classical_comparator_present"] is False
    assert missing["blocked_reason_codes"] == [
        "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_CLASSICAL_COMPARATOR"
    ]

    report = _report()
    assert report["blocked_arbitration_fixture_ids"] == [
        "BLOCKED_BACKEND_EXECUTION_ATTEMPT_FIXTURE",
        "BLOCKED_MISSING_CLASSICAL_COMPARATOR_FIXTURE",
    ]


def test_highest_priority_fixture_is_not_final_selection_or_live_authority_and_future_scope_is_closed():
    report = _report()
    assert report["highest_priority_arbitration_fixture_id"] == "OWNER_FORCED_QUANTUM_FIXTURE"
    assert report["static_arbitration_decision_is_final_selected_stack"] is False
    assert report["static_arbitration_decision_is_live_order_authority"] is False
    assert report["future_pr87_candidate_generation_implemented"] is False
    assert report["future_pr88_trade_context_selection_implemented"] is False
    assert report["future_pr90_replay_paper_competition_implemented"] is False
    assert report["future_live_authority_implemented"] is False


def test_no_runtime_live_order_source_connector_profit_backend_simulator_optimizer_or_replay_artifacts_created():
    registry = _registry()
    report = _report()
    for field in gate.NO_AUTHORITY_FALSE_FIELDS:
        assert registry["required_no_authority_flags"][field] is False
    for field in gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (REPO_ROOT / gate.CANONICAL_BUNDLE_SHA256).exists()


def test_missing_semantic_task_id_blocks():
    payload = _registry()
    payload.pop("semantic_task_id")
    failures = _registry_failures(payload)
    assert any("semantic_task_id" in failure for failure in failures), failures


def test_wrong_semantic_task_id_blocks():
    payload = _registry()
    payload["semantic_task_id"] = "ROADMAP-OPTIMIZER-ARBITRATION-GATE"
    failures = _registry_failures(payload)
    assert any(gate.SEMANTIC_TASK_ID in failure for failure in failures), failures


@pytest.mark.parametrize(
    "dependency_id",
    [
        "PR82_QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY",
        "PR83_QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY",
        "PR84_PARAMETER_ALGORITHM_SCORING_POLICY_REGISTRY",
        "PR85_PARAMETER_STACK_SCORING_AND_RANKING_GATE",
    ],
)
def test_missing_required_upstream_dependency_blocks(dependency_id):
    payload = _registry()
    payload["upstream_dependencies"] = [
        item for item in payload["upstream_dependencies"] if item["artifact_id"] != dependency_id
    ]
    _assert_registry_failure_contains(
        payload,
        "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD",
    )


def test_unknown_arbitration_mode_blocks():
    payload = _fixture()
    _arbitration_fixture(payload, "QUANTUM_CHALLENGER_FIXTURE")["arbitration_mode"] = "UNKNOWN_MODE"
    _assert_fixture_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_ARBITRATION_MODE")


def test_duplicate_arbitration_fixture_id_blocks():
    payload = _fixture()
    payload["optimizer_arbitration_fixtures"].append(copy.deepcopy(payload["optimizer_arbitration_fixtures"][0]))
    _assert_fixture_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_DUPLICATE_ARBITRATION_FIXTURE")


def test_fixture_not_marked_synthetic_static_blocks():
    payload = _fixture()
    _arbitration_fixture(payload, "CLASSICAL_BASELINE_FIXTURE")["arbitration_fixture_source"] = "REAL_OPTIMIZER_OUTPUT"
    _assert_fixture_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD")


@pytest.mark.parametrize(
    ("field", "reason_code"),
    [
        ("real_optimizer_result_created", "OPTIMIZER_ARBITRATION_BLOCKED_REAL_OPTIMIZER_RESULT_FORBIDDEN"),
        ("classical_optimizer_execution_created", "OPTIMIZER_ARBITRATION_BLOCKED_CLASSICAL_OPTIMIZER_EXECUTION_FORBIDDEN"),
        ("quantum_optimizer_execution_created", "OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_OPTIMIZER_EXECUTION_FORBIDDEN"),
        ("backend_execution_created", "OPTIMIZER_ARBITRATION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN"),
        ("quantum_backend_execution_created", "OPTIMIZER_ARBITRATION_BLOCKED_BACKEND_EXECUTION_FORBIDDEN"),
        ("quantum_simulator_execution_created", "OPTIMIZER_ARBITRATION_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN"),
        ("qaoa_execution_created", "OPTIMIZER_ARBITRATION_BLOCKED_QAOA_EXECUTION_FORBIDDEN"),
        ("vqe_execution_created", "OPTIMIZER_ARBITRATION_BLOCKED_VQE_EXECUTION_FORBIDDEN"),
        ("annealing_execution_created", "OPTIMIZER_ARBITRATION_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN"),
        ("qubo_solve_execution_created", "OPTIMIZER_ARBITRATION_BLOCKED_QUBO_SOLVE_FORBIDDEN"),
        ("ising_solve_execution_created", "OPTIMIZER_ARBITRATION_BLOCKED_ISING_SOLVE_FORBIDDEN"),
        ("real_generated_candidate_claim_created", "OPTIMIZER_ARBITRATION_BLOCKED_REAL_GENERATED_CANDIDATE_CLAIM"),
        ("final_selection_created", "OPTIMIZER_ARBITRATION_BLOCKED_FINAL_SELECTION_FORBIDDEN"),
        ("selected_stack_created", "OPTIMIZER_ARBITRATION_BLOCKED_SELECTED_STACK_FORBIDDEN"),
        ("selected_stack_claim_created", "OPTIMIZER_ARBITRATION_BLOCKED_SELECTED_STACK_FORBIDDEN"),
        ("replay_execution_created", "OPTIMIZER_ARBITRATION_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN"),
        ("paper_execution_created", "OPTIMIZER_ARBITRATION_BLOCKED_REPLAY_PAPER_RESULT_FORBIDDEN"),
        ("runtime_authority_created", "OPTIMIZER_ARBITRATION_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ("live_authority_created", "OPTIMIZER_ARBITRATION_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ("order_authority_created", "OPTIMIZER_ARBITRATION_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ("source_retrieval_created", "OPTIMIZER_ARBITRATION_BLOCKED_SOURCE_RETRIEVAL_FORBIDDEN"),
        ("source_acceptance_created", "OPTIMIZER_ARBITRATION_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN"),
        ("connector_semantic_binding_created", "OPTIMIZER_ARBITRATION_BLOCKED_CONNECTOR_BINDING_FORBIDDEN"),
        ("runtime_cash_receipt_created", "OPTIMIZER_ARBITRATION_BLOCKED_RUNTIME_CASH_RECEIPT_FORBIDDEN"),
        ("private_state_fetch_created", "OPTIMIZER_ARBITRATION_BLOCKED_PRIVATE_STATE_FETCH_FORBIDDEN"),
        ("profit_evidence_created", "OPTIMIZER_ARBITRATION_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN"),
        ("quantum_advantage_claim_created", "OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN"),
        ("latency_superiority_claim_created", "OPTIMIZER_ARBITRATION_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN"),
        ("execution_superiority_claim_created", "OPTIMIZER_ARBITRATION_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN"),
    ],
)
def test_arbitration_fixture_forbidden_claim_fields_block(field, reason_code):
    payload = _fixture()
    _arbitration_fixture(payload, "QUANTUM_CHALLENGER_FIXTURE")[field] = True
    _assert_fixture_failure_contains(payload, reason_code)


@pytest.mark.parametrize(
    "field",
    ["classical_optimizer_execution_created", "quantum_optimizer_execution_created", "optimizer_execution_created", "backend_execution_created", "real_optimizer_result_created", "final_selection_created", "random_arbitration_used"],
)
def test_registry_forbidden_no_authority_flags_block(field):
    payload = _registry()
    payload["required_no_authority_flags"][field] = True
    _assert_registry_failure_contains(payload, gate.FIELD_REASON_CODES[field])


def test_unknown_pr82_applicability_label_blocks():
    payload = _fixture()
    _arbitration_fixture(payload, "QUANTUM_CHALLENGER_FIXTURE")["quantum_applicability_labels"] = ["UNKNOWN_Q_LABEL"]
    _assert_fixture_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_QUANTUM_APPLICABILITY_LABEL")


def test_unknown_pr83_owner_quantum_priority_mode_blocks():
    payload = _fixture()
    _arbitration_fixture(payload, "QUANTUM_CHALLENGER_FIXTURE")["owner_quantum_priority_mode"] = "UNKNOWN_QUANTUM_MODE"
    _assert_fixture_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_UNKNOWN_OWNER_QUANTUM_PRIORITY_MODE")


def test_missing_pr84_scoring_policy_reference_blocks():
    payload = _registry()
    payload["scoring_policy_source"]["artifact_id"] = "UNKNOWN_PR84"
    _assert_registry_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD")


def test_missing_pr85_ranking_reference_blocks():
    payload = _fixture()
    _arbitration_fixture(payload, "QUANTUM_CHALLENGER_FIXTURE")["score_breakdown_source"] = "UNKNOWN_PR85_CANDIDATE"
    _assert_fixture_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_REQUIRED_FIXTURE_FIELD")


def test_hybrid_without_classical_comparator_blocks():
    payload = _fixture()
    hybrid = _arbitration_fixture(payload, "HYBRID_COMPARE_THEN_SELECT_FIXTURE")
    hybrid["classical_baseline_fixture_id"] = None
    _assert_fixture_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_CLASSICAL_COMPARATOR")


def test_hybrid_without_quantum_challenger_blocks():
    payload = _fixture()
    hybrid = _arbitration_fixture(payload, "HYBRID_COMPARE_THEN_SELECT_FIXTURE")
    hybrid["quantum_challenger_fixture_id"] = None
    _assert_fixture_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_MISSING_QUANTUM_CHALLENGER")


def test_quantum_first_without_owner_policy_permission_blocks():
    payload = _fixture()
    quantum_first = _arbitration_fixture(payload, "QUANTUM_FIRST_FIXTURE")
    quantum_first["owner_quantum_priority_mode"] = "QUANTUM_NEUTRAL"
    _assert_fixture_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_QUANTUM_PRIORITY_NOT_PERMITTED")


def test_owner_forced_quantum_without_owner_basis_blocks():
    payload = _fixture()
    _arbitration_fixture(payload, "OWNER_FORCED_QUANTUM_FIXTURE")["owner_override_basis"] = "NONE"
    _assert_fixture_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_OWNER_FORCED_MODE_WITHOUT_OWNER_BASIS")


def test_owner_forced_classical_without_owner_or_failsafe_basis_blocks():
    payload = _fixture()
    _arbitration_fixture(payload, "OWNER_FORCED_CLASSICAL_FIXTURE")["owner_override_basis"] = "NONE"
    _assert_fixture_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_OWNER_FORCED_MODE_WITHOUT_OWNER_BASIS")


def test_random_arbitration_policy_blocks():
    payload = _registry()
    payload["arbitration_policy"]["random_arbitration_allowed"] = True
    _assert_registry_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_RANDOM_ARBITRATION_FORBIDDEN")


def test_ambiguous_tie_break_policy_blocks():
    payload = _registry()
    payload["arbitration_policy"]["tie_break_order"] = payload["arbitration_policy"]["tie_break_order"][:-1]
    _assert_registry_failure_contains(payload, "OPTIMIZER_ARBITRATION_BLOCKED_TIE_BREAK_AMBIGUOUS")


def _clean_boundary_tmp_root() -> None:
    if BOUNDARY_TMP_ROOT.exists():
        shutil.rmtree(BOUNDARY_TMP_ROOT)


def _temp_boundary_root() -> Path:
    _clean_boundary_tmp_root()
    (BOUNDARY_TMP_ROOT / gate.PR76_SHORT_TEST).parent.mkdir(parents=True, exist_ok=True)
    (BOUNDARY_TMP_ROOT / gate.PR76_SHORT_TEST).write_text("", encoding="utf-8")
    return BOUNDARY_TMP_ROOT


def test_atomicrows_bundle_jsonl_creation_blocks():
    root = _temp_boundary_root()
    try:
        (root / gate.CANONICAL_BUNDLE_JSONL).parent.mkdir(parents=True, exist_ok=True)
        (root / gate.CANONICAL_BUNDLE_JSONL).write_text("", encoding="utf-8")
        failures = gate.validate_filesystem_boundaries(root)
        assert any("OPTIMIZER_ARBITRATION_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN" in failure for failure in failures)
    finally:
        _clean_boundary_tmp_root()


def test_atomicrows_bundle_sha256_creation_blocks():
    root = _temp_boundary_root()
    try:
        (root / gate.CANONICAL_BUNDLE_SHA256).parent.mkdir(parents=True, exist_ok=True)
        (root / gate.CANONICAL_BUNDLE_SHA256).write_text("", encoding="utf-8")
        failures = gate.validate_filesystem_boundaries(root)
        assert any("OPTIMIZER_ARBITRATION_BLOCKED_ATOMICROWS_SHA_FORBIDDEN" in failure for failure in failures)
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
    assert report["arbitration_fixture_ids"] == list(gate.REQUIRED_ARBITRATION_FIXTURE_IDS)
    assert report["upstream_dependency_ids"] == list(gate.DEPENDENCY_ORDER)
    assert report["future_consumer_ids"] == list(gate.FUTURE_CONSUMER_ORDER)
    assert report["reason_codes"] == list(gate.REASON_CODE_ORDER)
    assert report["deterministic_blocked_fixture_ordering"] is True
