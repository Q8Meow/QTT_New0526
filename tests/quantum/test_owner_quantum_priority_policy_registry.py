import copy
import json
from pathlib import Path
import re
import shutil

import pytest

from tools import validate_owner_quantum_priority_policy_registry as gate


REPO_ROOT = Path(".")
BOUNDARY_TMP_ROOT = Path("tests/fixtures/quantum/.tmp_owner_priority_boundary_case")


def _registry() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.DEFAULT_PRODUCTION_REGISTRY)


def _fixture() -> dict:
    return json.loads((REPO_ROOT / gate.DEFAULT_FIXTURE).read_text(encoding="utf-8"))


def _mode(payload: dict, mode: str) -> dict:
    for entry in payload["mode_policies"]:
        if entry["mode"] == mode:
            return entry
    raise AssertionError(f"missing mode {mode}")


def _failures(payload: dict) -> list[str]:
    return gate.validate_policy_payload(
        payload,
        known_labels=set(gate.LABEL_ORDER),
        known_primary_classes=set(gate.PRIMARY_CLASS_ORDER),
        label="TEST",
    )


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


def test_every_required_mode_is_present_in_canonical_order():
    registry = _registry()
    assert registry["supported_quantum_priority_modes"] == list(gate.MODE_ORDER)
    assert [entry["mode"] for entry in registry["mode_policies"]] == list(gate.MODE_ORDER)


def test_quantum_neutral_is_metadata_only_multiplier_neutral_and_no_preference():
    neutral = _mode(_registry(), "QUANTUM_NEUTRAL")
    assert neutral["metadata_only_flag"] is True
    assert neutral["priority_multiplier"] == 1.0
    assert neutral["quantum_applicable_family_multiplier"] == 1.0
    assert neutral["tie_breaker_enabled"] is False
    assert neutral["owner_can_force"] is False
    assert neutral["classical_comparator_required"] is False


def test_quantum_preferred_is_metadata_only_without_scoring_ranking_or_selection():
    registry = _registry()
    preferred = _mode(registry, "QUANTUM_PREFERRED")
    assert preferred["metadata_only_flag"] is True
    assert preferred["priority_multiplier"] == 1.1
    assert preferred["quantum_applicable_family_multiplier"] == 1.05
    assert registry["scoring_execution_created"] is False
    assert registry["ranking_created"] is False
    assert registry["selection_created"] is False


def test_quantum_strongly_preferred_is_stronger_bounded_metadata_only():
    registry = _registry()
    preferred = _mode(registry, "QUANTUM_PREFERRED")
    strong = _mode(registry, "QUANTUM_STRONGLY_PREFERRED")
    assert strong["metadata_only_flag"] is True
    assert strong["priority_multiplier"] > preferred["priority_multiplier"]
    assert gate.PRIORITY_MULTIPLIER_MIN <= strong["priority_multiplier"] <= gate.PRIORITY_MULTIPLIER_MAX
    assert registry["scoring_execution_created"] is False
    assert registry["ranking_created"] is False
    assert registry["selection_created"] is False


def test_quantum_first_is_metadata_only_without_optimizer_backend_or_selection():
    registry = _registry()
    quantum_first = _mode(registry, "QUANTUM_FIRST")
    assert quantum_first["metadata_only_flag"] is True
    assert quantum_first["priority_multiplier"] >= _mode(registry, "QUANTUM_STRONGLY_PREFERRED")["priority_multiplier"]
    assert registry["optimizer_execution_created"] is False
    assert registry["quantum_backend_execution_created"] is False
    assert registry["quantum_simulator_execution_created"] is False
    assert registry["selection_created"] is False


def test_owner_forced_quantum_is_internal_only_and_preserves_false_evidence_fields():
    registry = _registry()
    forced = _mode(registry, "OWNER_FORCED_QUANTUM")
    assert forced["owner_can_force"] is True
    assert registry["owner_override_basis"] == "OWNER_GLOBAL_OVERRIDE"
    assert registry["owner_forced_quantum_internal_only"] is True
    assert registry["owner_forced_quantum_bypasses_future_gates"] is False
    for field in (
        "owner_override_external_fact_fabrication_created",
        "quantum_backend_execution_created",
        "quantum_simulator_execution_created",
        "optimizer_execution_created",
        "optimizer_arbitration_created",
        "scoring_execution_created",
        "ranking_created",
        "selection_created",
        "quantum_advantage_claim_created",
        "profit_evidence_created",
    ):
        assert registry[field] is False


def test_hybrid_compare_then_quantum_tiebreak_requires_classical_comparator_without_execution():
    registry = _registry()
    hybrid = _mode(registry, "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK")
    assert hybrid["hybrid_compare_required_before_quantum_preference"] is True
    assert hybrid["classical_comparator_required"] is True
    assert hybrid["future_optimizer_arbitration_required"] is True
    assert registry["optimizer_arbitration_created"] is False
    assert registry["scoring_execution_created"] is False
    assert registry["ranking_created"] is False
    assert registry["selection_created"] is False


def test_classical_only_remains_valid_comparator_metadata():
    registry = _registry()
    assert registry["classical_only_families_valid_as_comparators"] is True
    assert all(
        "CLASSICAL_ONLY" in policy["allowed_applicability_labels"]
        for policy in registry["mode_policies"]
    )
    assert all(
        "CLASSICAL_ONLY" in policy["allowed_primary_quantum_applicability_classes"]
        for policy in registry["mode_policies"]
    )


def test_pr83_consumes_pr82_applicability_labels_and_pr82_metadata_boundaries():
    failures, labels, primary_classes = gate.validate_pr82_registry(REPO_ROOT)
    assert failures == []
    assert labels == set(gate.LABEL_ORDER)
    assert primary_classes == set(gate.PRIMARY_CLASS_ORDER)

    registry = _registry()
    for policy in registry["mode_policies"]:
        assert set(policy["allowed_applicability_labels"]).issubset(labels)
        assert set(policy["allowed_primary_quantum_applicability_classes"]).issubset(primary_classes)


def test_future_pr_dependency_and_consumer_contract_fields_are_present_without_execution():
    registry = _registry()
    assert registry["future_scoring_policy_required"] is True
    assert registry["future_stack_ranking_gate_required"] is True
    assert registry["future_optimizer_arbitration_required"] is True
    assert registry["future_candidate_stack_generation_required"] is True
    assert registry["future_trade_context_stack_selection_required"] is True
    assert registry["future_consumer_contract_fields"] == list(gate.FUTURE_CONSUMER_CONTRACT_FIELDS)
    assert registry["future_consumer_contract_execution_created"] is False


def test_no_runtime_live_order_source_connector_profit_backend_or_selection_artifact_created():
    registry = _registry()
    for field in gate.ROOT_FALSE_FIELDS:
        assert registry[field] is False


def test_fixture_declares_required_synthetic_cases_and_no_authority():
    fixture = _fixture()
    assert gate.validate_fixture(fixture) == []
    assert fixture["mode"] == "SOURCE_REQUIRED"
    assert fixture["execution"] == "DISABLED"
    assert fixture["quantum_backend_execution_created"] is False
    assert fixture["optimizer_execution_created"] is False
    assert fixture["profit_evidence_created"] is False


def test_unknown_quantum_priority_mode_blocks():
    payload = copy.deepcopy(_registry())
    payload["supported_quantum_priority_modes"][0] = "UNKNOWN_QUANTUM_PRIORITY_MODE"
    payload["mode_policies"][0]["mode"] = "UNKNOWN_QUANTUM_PRIORITY_MODE"
    _assert_failure_contains(payload, "OWNER_QUANTUM_PRIORITY_BLOCKED_UNKNOWN_MODE")


def test_duplicate_quantum_priority_mode_blocks():
    payload = copy.deepcopy(_registry())
    payload["mode_policies"].append(copy.deepcopy(payload["mode_policies"][0]))
    _assert_failure_contains(payload, "OWNER_QUANTUM_PRIORITY_BLOCKED_DUPLICATE_MODE")


def test_missing_required_mode_blocks():
    payload = copy.deepcopy(_registry())
    payload["mode_policies"] = payload["mode_policies"][:-1]
    _assert_failure_contains(payload, "OWNER_QUANTUM_PRIORITY_BLOCKED_MISSING_REQUIRED_MODE")


def test_invalid_default_quantum_priority_mode_blocks():
    payload = copy.deepcopy(_registry())
    payload["default_quantum_priority_mode"] = "UNKNOWN_DEFAULT_MODE"
    _assert_failure_contains(payload, "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_DEFAULT_MODE")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("priority_multiplier", 0.99),
        ("priority_multiplier", 1.51),
        ("quantum_applicable_family_multiplier", 0.99),
        ("quantum_applicable_family_multiplier", 1.21),
    ],
)
def test_invalid_multiplier_bounds_block(field, value):
    payload = copy.deepcopy(_registry())
    _mode(payload, "QUANTUM_PREFERRED")[field] = value
    _assert_failure_contains(payload, "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_MULTIPLIER")


def test_quantum_neutral_with_non_neutral_multiplier_blocks():
    payload = copy.deepcopy(_registry())
    _mode(payload, "QUANTUM_NEUTRAL")["priority_multiplier"] = 1.01
    _assert_failure_contains(payload, "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_MULTIPLIER")


def test_strongly_preferred_not_greater_than_preferred_blocks():
    payload = copy.deepcopy(_registry())
    _mode(payload, "QUANTUM_STRONGLY_PREFERRED")["priority_multiplier"] = 1.10
    _assert_failure_contains(payload, "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_MULTIPLIER")


def test_quantum_first_less_than_strongly_preferred_blocks():
    payload = copy.deepcopy(_registry())
    _mode(payload, "QUANTUM_FIRST")["priority_multiplier"] = 1.20
    _assert_failure_contains(payload, "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_MULTIPLIER")


def test_owner_forced_quantum_without_owner_override_basis_blocks():
    payload = copy.deepcopy(_registry())
    payload["default_quantum_priority_mode"] = "OWNER_FORCED_QUANTUM"
    payload["owner_override_basis"] = "NONE"
    _assert_failure_contains(
        payload,
        "OWNER_QUANTUM_PRIORITY_BLOCKED_OWNER_FORCED_MODE_WITHOUT_OWNER_BASIS",
    )


def test_hybrid_tiebreak_without_classical_comparator_blocks():
    payload = copy.deepcopy(_registry())
    _mode(payload, "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK")["classical_comparator_required"] = False
    failures = _failures(payload)
    assert any("HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK" in failure for failure in failures), failures


def test_unknown_pr82_applicability_label_blocks():
    payload = copy.deepcopy(_registry())
    _mode(payload, "QUANTUM_PREFERRED")["allowed_applicability_labels"] = ["UNKNOWN_PR82_LABEL"]
    _assert_failure_contains(payload, "OWNER_QUANTUM_PRIORITY_BLOCKED_INVALID_APPLICABILITY_LABEL")


def test_owner_override_external_fact_fabrication_attempt_blocks():
    payload = copy.deepcopy(_registry())
    payload["owner_override_external_fact_fabrication_created"] = True
    _assert_failure_contains(
        payload,
        "OWNER_QUANTUM_PRIORITY_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
    )


@pytest.mark.parametrize(
    ("field", "reason_code"),
    [
        ("backend_execution_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN"),
        ("quantum_backend_execution_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN"),
        ("quantum_simulator_execution_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN"),
        ("qaoa_execution_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_QAOA_EXECUTION_FORBIDDEN"),
        ("vqe_execution_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_VQE_EXECUTION_FORBIDDEN"),
        ("annealing_execution_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN"),
        ("qubo_solve_execution_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_QUBO_SOLVE_FORBIDDEN"),
        ("ising_solve_execution_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_ISING_SOLVE_FORBIDDEN"),
        ("optimizer_execution_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_OPTIMIZER_EXECUTION_FORBIDDEN"),
        ("optimizer_arbitration_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN"),
        ("scoring_execution_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_SCORING_FORBIDDEN"),
        ("ranking_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_RANKING_FORBIDDEN"),
        ("selection_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_SELECTION_FORBIDDEN"),
        ("runtime_authority_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ("live_authority_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ("order_authority_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN"),
        ("source_retrieval_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN"),
        ("source_acceptance_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN"),
        ("connector_semantic_binding_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_CONNECTOR_BINDING_FORBIDDEN"),
        ("replay_execution_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_REPLAY_PAPER_PROOF_FORBIDDEN"),
        ("paper_execution_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_REPLAY_PAPER_PROOF_FORBIDDEN"),
        ("quantum_advantage_claim_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN"),
        ("profit_evidence_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN"),
        ("latency_superiority_claim_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN"),
        ("execution_superiority_claim_created", "OWNER_QUANTUM_PRIORITY_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN"),
        ("random_policy_used", "OWNER_QUANTUM_PRIORITY_BLOCKED_RANDOM_POLICY_FORBIDDEN"),
    ],
)
def test_forbidden_root_claim_fields_block(field, reason_code):
    payload = copy.deepcopy(_registry())
    payload[field] = True
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
        assert not any("OWNER_QUANTUM_PRIORITY_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN" in failure for failure in failures)
        assert not (root / gate.CANONICAL_BUNDLE_SHA256).exists()
    finally:
        _clean_boundary_tmp_root()


def test_atomicrows_bundle_sha256_creation_blocks():
    root = _temp_boundary_root()
    try:
        (root / gate.CANONICAL_BUNDLE_SHA256).parent.mkdir(parents=True, exist_ok=True)
        (root / gate.CANONICAL_BUNDLE_SHA256).write_text("", encoding="utf-8")
        failures = gate.validate_filesystem_boundaries(root)
        assert any("OWNER_QUANTUM_PRIORITY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN" in failure for failure in failures)
    finally:
        _clean_boundary_tmp_root()


def test_old_long_runtime_resolver_allowlist_filename_reintroduction_blocks():
    root = _temp_boundary_root()
    try:
        (root / gate.PR76_OLD_LONG_TEST).parent.mkdir(parents=True, exist_ok=True)
        (root / gate.PR76_OLD_LONG_TEST).write_text("", encoding="utf-8")
        failures = gate.validate_filesystem_boundaries(root)
        assert any("old long runtime resolver allowlist filename must remain absent" in failure for failure in failures)
    finally:
        _clean_boundary_tmp_root()


def test_deterministic_ordering_is_enforced():
    registry = _registry()
    assert registry["supported_quantum_priority_modes"] == list(gate.MODE_ORDER)
    assert [entry["mode"] for entry in registry["mode_policies"]] == list(gate.MODE_ORDER)
    assert [entry["mode_or_policy_id"] for entry in registry["blocked_policies"]] == list(gate.BLOCKED_POLICY_ORDER)
    assert registry["reason_codes"] == list(gate.REASON_CODE_ORDER)
    for policy in registry["mode_policies"]:
        assert policy["allowed_primary_quantum_applicability_classes"] == list(gate.PRIMARY_CLASS_ORDER)
        assert policy["allowed_applicability_labels"] == list(gate.LABEL_ORDER)


def test_generated_report_has_no_nondeterministic_values_or_platform_paths():
    report = gate.build_report(_registry(), set(gate.LABEL_ORDER), REPO_ROOT)
    text = gate.serialize_report(report)

    assert text == gate.serialize_report(copy.deepcopy(report))
    assert report["generated_at_utc"] == "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
    assert not re.search(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        text,
    )
    assert not re.search(r"\b20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}", text)
    assert not re.search(r"[A-Za-z]:\\\\|\\\\", text)
    assert gate.validate_report_is_deterministic(report) == []
