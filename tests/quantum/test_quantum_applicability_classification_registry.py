import copy
import json
from pathlib import Path
import re
import shutil

import pytest

from tools import validate_quantum_applicability_classification_registry as gate


REPO_ROOT = Path(".")
BOUNDARY_TMP_ROOT = Path("tests/fixtures/quantum/.tmp_boundary_case")


def _registry() -> dict:
    return gate.load_yaml(REPO_ROOT / gate.DEFAULT_PRODUCTION_REGISTRY)


def _fixture() -> dict:
    return json.loads((REPO_ROOT / gate.DEFAULT_FIXTURE).read_text(encoding="utf-8"))


def _canonical() -> dict:
    return gate.canonical_family_map(REPO_ROOT)


def _entry(payload: dict, family_id: str) -> dict:
    for entry in payload["family_classifications"]:
        if entry["family_id"] == family_id:
            return entry
    raise AssertionError(f"missing family_id {family_id}")


def _failures(payload: dict) -> list[str]:
    return gate.validate_registry_payload(payload, _canonical(), label="TEST")


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


def test_every_required_label_is_declared_and_covered():
    registry = _registry()
    assert registry["classification_labels"] == list(gate.LABEL_ORDER)

    covered = {
        label
        for entry in registry["family_classifications"]
        for label in entry["applicability_labels"]
    }
    assert set(gate.LABEL_ORDER).issubset(covered)


@pytest.mark.parametrize(
    ("family_id", "label"),
    [
        ("QTT_ALGORITHM_FAMILY_008_TRUE_QUANTUM_OPTIMIZER", "TRUE_QUANTUM"),
        ("QTT_ALGORITHM_FAMILY_007_QUANTUM_INSPIRED_OPTIMIZER", "QUANTUM_INSPIRED"),
        (
            "QTT_ALGORITHM_FAMILY_009_HYBRID_CLASSICAL_QUANTUM_OPTIMIZER",
            "HYBRID_CLASSICAL_QUANTUM",
        ),
        ("QTT_ALGORITHM_FAMILY_010_QUBO_COMPATIBLE_ALGORITHM", "QUBO_COMPATIBLE"),
        ("QTT_ALGORITHM_FAMILY_011_ISING_COMPATIBLE_ALGORITHM", "ISING_COMPATIBLE"),
        ("QTT_ALGORITHM_FAMILY_012_QAOA_COMPATIBLE_ALGORITHM", "QAOA_COMPATIBLE"),
        ("QTT_ALGORITHM_FAMILY_013_VQE_COMPATIBLE_ALGORITHM", "VQE_COMPATIBLE"),
        (
            "QTT_ALGORITHM_FAMILY_014_ANNEALING_COMPATIBLE_ALGORITHM",
            "ANNEALING_COMPATIBLE",
        ),
        (
            "QTT_ALGORITHM_FAMILY_015_QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE_ALGORITHM",
            "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE",
        ),
        ("QTT_ALGORITHM_FAMILY_001_CLASSICAL_SIGNAL_ALGORITHM", "CLASSICAL_ONLY"),
    ],
)
def test_label_examples_are_metadata_only_without_execution_or_claims(family_id, label):
    entry = _entry(_registry(), family_id)
    assert label in entry["applicability_labels"]
    assert entry["metadata_only_flag"] is True
    assert entry["backend_execution_created"] is False
    assert entry["quantum_backend_execution_created"] is False
    assert entry["quantum_simulator_execution_created"] is False
    assert entry["optimizer_arbitration_created"] is False
    assert entry["scoring_execution_created"] is False
    assert entry["ranking_created"] is False
    assert entry["selection_created"] is False
    assert entry["quantum_advantage_claim_created"] is False
    assert entry["profit_evidence_created"] is False


def test_quantum_specific_compatibility_labels_do_not_execute_algorithms():
    registry = _registry()
    assert _entry(registry, "QTT_ALGORITHM_FAMILY_010_QUBO_COMPATIBLE_ALGORITHM")[
        "qubo_solve_execution_created"
    ] is False
    assert _entry(registry, "QTT_ALGORITHM_FAMILY_011_ISING_COMPATIBLE_ALGORITHM")[
        "ising_solve_execution_created"
    ] is False
    assert _entry(registry, "QTT_ALGORITHM_FAMILY_012_QAOA_COMPATIBLE_ALGORITHM")[
        "qaoa_execution_created"
    ] is False
    assert _entry(registry, "QTT_ALGORITHM_FAMILY_013_VQE_COMPATIBLE_ALGORITHM")[
        "vqe_execution_created"
    ] is False
    assert _entry(registry, "QTT_ALGORITHM_FAMILY_014_ANNEALING_COMPATIBLE_ALGORITHM")[
        "annealing_execution_created"
    ] is False
    portfolio = _entry(
        registry,
        "QTT_ALGORITHM_FAMILY_015_QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE_ALGORITHM",
    )
    assert portfolio["capital_allocation_created"] is False
    assert portfolio["live_portfolio_optimization_created"] is False
    assert portfolio["profit_evidence_created"] is False


def test_classical_only_families_remain_valid_comparators():
    classical = _entry(_registry(), "QTT_ALGORITHM_FAMILY_001_CLASSICAL_SIGNAL_ALGORITHM")
    assert classical["applicability_labels"] == ["CLASSICAL_ONLY"]
    assert classical["primary_quantum_applicability_class"] == "CLASSICAL_ONLY"
    assert classical["classical_only_comparator_valid"] is True
    assert classical["classical_comparator_required"] is False


def test_owner_override_is_internal_metadata_only():
    override = _entry(_registry(), "QUANTUM_BACKEND_INTERNAL_ROUTING_FAMILY")
    assert override["owner_override_applied"] is True
    assert override["owner_override_basis"] == "OWNER_GLOBAL_OVERRIDE"
    assert override["owner_override_external_fact_fabrication_created"] is False
    assert override["quantum_backend_execution_created"] is False
    assert override["quantum_advantage_claim_created"] is False
    assert override["optimizer_arbitration_created"] is False
    assert override["profit_evidence_created"] is False


def test_future_pr_dependency_flags_are_present():
    registry = _registry()
    assert registry["future_owner_quantum_priority_policy_required"] is True
    assert registry["future_scoring_policy_required"] is True
    assert registry["future_optimizer_arbitration_required"] is True


def test_fixture_declares_required_synthetic_cases_and_no_authority():
    fixture = _fixture()
    failures = gate.validate_fixture(fixture)
    assert failures == []
    assert fixture["mode"] == "SOURCE_REQUIRED"
    assert fixture["execution"] == "DISABLED"
    assert fixture["quantum_backend_execution_created"] is False
    assert fixture["profit_evidence_created"] is False


def test_unknown_family_id_blocks():
    payload = copy.deepcopy(_registry())
    payload["family_classifications"][0]["family_id"] = "UNKNOWN_QUANTUM_FAMILY"
    _assert_failure_contains(payload, "QUANTUM_APPLICABILITY_BLOCKED_UNKNOWN_FAMILY_ID")


def test_duplicate_family_id_blocks():
    payload = copy.deepcopy(_registry())
    payload["family_classifications"].append(copy.deepcopy(payload["family_classifications"][0]))
    _assert_failure_contains(payload, "QUANTUM_APPLICABILITY_BLOCKED_DUPLICATE_FAMILY_ID")


def test_unknown_applicability_label_blocks():
    payload = copy.deepcopy(_registry())
    _entry(payload, "QTT_ALGORITHM_FAMILY_007_QUANTUM_INSPIRED_OPTIMIZER")[
        "applicability_labels"
    ] = ["UNKNOWN_QUANTUM_LABEL"]
    _assert_failure_contains(payload, "QUANTUM_APPLICABILITY_BLOCKED_UNKNOWN_LABEL")


def test_missing_required_label_coverage_blocks():
    payload = copy.deepcopy(_registry())
    _entry(payload, "QTT_ALGORITHM_FAMILY_013_VQE_COMPATIBLE_ALGORITHM")[
        "applicability_labels"
    ] = ["TRUE_QUANTUM"]
    _assert_failure_contains(
        payload, "QUANTUM_APPLICABILITY_BLOCKED_MISSING_REQUIRED_LABEL_COVERAGE"
    )


def test_invalid_primary_quantum_applicability_class_blocks():
    payload = copy.deepcopy(_registry())
    _entry(payload, "QTT_ALGORITHM_FAMILY_010_QUBO_COMPATIBLE_ALGORITHM")[
        "primary_quantum_applicability_class"
    ] = "QUBO_COMPATIBLE"
    _assert_failure_contains(payload, "QUANTUM_APPLICABILITY_BLOCKED_INVALID_PRIMARY_CLASS")


def test_classical_only_conflict_with_quantum_label_blocks():
    payload = copy.deepcopy(_registry())
    classical = _entry(payload, "QTT_ALGORITHM_FAMILY_001_CLASSICAL_SIGNAL_ALGORITHM")
    classical["applicability_labels"] = ["TRUE_QUANTUM", "CLASSICAL_ONLY"]
    _assert_failure_contains(payload, "QUANTUM_APPLICABILITY_BLOCKED_CLASSICAL_ONLY_CONFLICT")


@pytest.mark.parametrize(
    ("field", "reason_code"),
    [
        ("backend_execution_created", "QUANTUM_APPLICABILITY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN"),
        (
            "quantum_backend_execution_created",
            "QUANTUM_APPLICABILITY_BLOCKED_BACKEND_EXECUTION_FORBIDDEN",
        ),
        (
            "quantum_simulator_execution_created",
            "QUANTUM_APPLICABILITY_BLOCKED_SIMULATOR_EXECUTION_FORBIDDEN",
        ),
        ("qaoa_execution_created", "QUANTUM_APPLICABILITY_BLOCKED_QAOA_EXECUTION_FORBIDDEN"),
        ("vqe_execution_created", "QUANTUM_APPLICABILITY_BLOCKED_VQE_EXECUTION_FORBIDDEN"),
        (
            "annealing_execution_created",
            "QUANTUM_APPLICABILITY_BLOCKED_ANNEALING_EXECUTION_FORBIDDEN",
        ),
        ("qubo_solve_execution_created", "QUANTUM_APPLICABILITY_BLOCKED_QUBO_SOLVE_FORBIDDEN"),
        ("ising_solve_execution_created", "QUANTUM_APPLICABILITY_BLOCKED_ISING_SOLVE_FORBIDDEN"),
        (
            "optimizer_arbitration_created",
            "QUANTUM_APPLICABILITY_BLOCKED_OPTIMIZER_ARBITRATION_FORBIDDEN",
        ),
        ("scoring_execution_created", "QUANTUM_APPLICABILITY_BLOCKED_SCORING_FORBIDDEN"),
        ("ranking_created", "QUANTUM_APPLICABILITY_BLOCKED_RANKING_FORBIDDEN"),
        ("selection_created", "QUANTUM_APPLICABILITY_BLOCKED_SELECTION_FORBIDDEN"),
        (
            "runtime_authority_created",
            "QUANTUM_APPLICABILITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
        ),
        (
            "live_authority_created",
            "QUANTUM_APPLICABILITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
        ),
        (
            "order_authority_created",
            "QUANTUM_APPLICABILITY_BLOCKED_RUNTIME_LIVE_ORDER_AUTHORITY_FORBIDDEN",
        ),
        (
            "source_retrieval_created",
            "QUANTUM_APPLICABILITY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
        ),
        (
            "source_acceptance_created",
            "QUANTUM_APPLICABILITY_BLOCKED_SOURCE_ACCEPTANCE_FORBIDDEN",
        ),
        (
            "connector_semantic_binding_created",
            "QUANTUM_APPLICABILITY_BLOCKED_CONNECTOR_BINDING_FORBIDDEN",
        ),
        (
            "quantum_advantage_claim_created",
            "QUANTUM_APPLICABILITY_BLOCKED_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN",
        ),
        ("profit_evidence_created", "QUANTUM_APPLICABILITY_BLOCKED_PROFIT_EVIDENCE_FORBIDDEN"),
        (
            "latency_superiority_claim_created",
            "QUANTUM_APPLICABILITY_BLOCKED_LATENCY_SUPERIORITY_CLAIM_FORBIDDEN",
        ),
        (
            "execution_superiority_claim_created",
            "QUANTUM_APPLICABILITY_BLOCKED_EXECUTION_SUPERIORITY_CLAIM_FORBIDDEN",
        ),
        (
            "random_classification_used",
            "QUANTUM_APPLICABILITY_BLOCKED_RANDOM_CLASSIFICATION_FORBIDDEN",
        ),
    ],
)
def test_forbidden_root_claim_fields_block(field, reason_code):
    payload = copy.deepcopy(_registry())
    payload[field] = True
    _assert_failure_contains(payload, reason_code)


def test_owner_override_external_fact_fabrication_attempt_blocks():
    payload = copy.deepcopy(_registry())
    _entry(payload, "QUANTUM_BACKEND_INTERNAL_ROUTING_FAMILY")[
        "owner_override_external_fact_fabrication_created"
    ] = True
    _assert_failure_contains(
        payload, "QUANTUM_APPLICABILITY_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT"
    )


def _clean_boundary_tmp_root() -> None:
    if BOUNDARY_TMP_ROOT.exists():
        shutil.rmtree(BOUNDARY_TMP_ROOT)


def _temp_boundary_root() -> Path:
    _clean_boundary_tmp_root()
    (BOUNDARY_TMP_ROOT / gate.PR76_SHORT_TEST).parent.mkdir(parents=True, exist_ok=True)
    (BOUNDARY_TMP_ROOT / gate.PR76_SHORT_TEST).write_text("", encoding="utf-8")
    (BOUNDARY_TMP_ROOT / gate.CURRENT_QUANTUM_SCHEMA_SURFACE).parent.mkdir(
        parents=True, exist_ok=True
    )
    (BOUNDARY_TMP_ROOT / gate.CURRENT_QUANTUM_SCHEMA_SURFACE).write_text(
        "{}", encoding="utf-8"
    )
    return BOUNDARY_TMP_ROOT


def test_atomicrows_bundle_jsonl_creation_blocks():
    root = _temp_boundary_root()
    try:
        (root / gate.CANONICAL_BUNDLE_JSONL).parent.mkdir(parents=True, exist_ok=True)
        (root / gate.CANONICAL_BUNDLE_JSONL).write_text("", encoding="utf-8")
        failures = gate.validate_filesystem_boundaries(root)
        assert any("QUANTUM_APPLICABILITY_BLOCKED_ATOMICROWS_BUNDLE_FORBIDDEN" in failure for failure in failures)
    finally:
        _clean_boundary_tmp_root()


def test_atomicrows_bundle_sha256_creation_blocks():
    root = _temp_boundary_root()
    try:
        (root / gate.CANONICAL_BUNDLE_SHA256).parent.mkdir(parents=True, exist_ok=True)
        (root / gate.CANONICAL_BUNDLE_SHA256).write_text("", encoding="utf-8")
        failures = gate.validate_filesystem_boundaries(root)
        assert any("QUANTUM_APPLICABILITY_BLOCKED_ATOMICROWS_SHA_FORBIDDEN" in failure for failure in failures)
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
    assert registry["classification_labels"] == list(gate.LABEL_ORDER)
    assert [entry["family_id"] for entry in registry["family_classifications"]] == sorted(
        entry["family_id"] for entry in registry["family_classifications"]
    )
    assert [entry["family_id"] for entry in registry["blocked_classifications"]] == sorted(
        entry["family_id"] for entry in registry["blocked_classifications"]
    )
    assert registry["reason_codes"] == list(gate.REASON_CODE_ORDER)


def test_generated_report_has_no_nondeterministic_values_or_platform_paths():
    report = gate.build_report(_registry(), _canonical())
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
