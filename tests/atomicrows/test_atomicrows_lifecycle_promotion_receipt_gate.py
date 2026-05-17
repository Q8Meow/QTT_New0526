from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import build_atomicrows_parameter_lifecycle_report as lifecycle_builder
from tools import validate_atomicrows_lifecycle_promotion_receipt_gate as gate


REPO_ROOT = Path(".")
REGISTRY = Path("docs/master_plan/atomic_rows/AtomicRowsParameterLifecycleRegistry.yaml")
LIFECYCLE_REPORT = Path("docs/master_plan/generated/AtomicRowsParameterLifecycleReport.json")
SCHEMA = Path("schemas/atomicrows/atomicrows_lifecycle_promotion_receipt_gate.schema.json")
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_lifecycle_promotion_receipt_gate_blocked.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/AtomicRowsLifecyclePromotionReceiptGate.report.json"
)
CANONICAL_BUNDLE = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
CANONICAL_BUNDLE_SHA = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.sha256")


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _registry() -> dict:
    return lifecycle_builder.load_registry(REGISTRY)


def _lifecycle_report() -> dict:
    return json.loads(LIFECYCLE_REPORT.read_text(encoding="utf-8"))


def _entries_by_pattern() -> dict[str, dict]:
    return {entry["row_pattern_id"]: entry for entry in _registry()["entries"]}


def _attempt(fixture: dict, attempt_id: str) -> dict:
    for attempt in fixture["attempted_promotions"]:
        if attempt["attempt_id"] == attempt_id:
            return attempt
    raise AssertionError(f"missing attempt {attempt_id}")


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_schema_declares_receipt_types_statuses_and_report_fields():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    report_schema = schema["$defs"]["promotion_receipt_gate_report"]

    assert schema["additionalProperties"] is False
    assert schema["$defs"]["receipt_type"]["enum"] == list(gate.RECEIPT_TYPES)
    assert schema["$defs"]["lifecycle_status"]["enum"] == list(
        lifecycle_builder.LIFECYCLE_STATUSES
    )
    assert report_schema["required"] == list(gate._empty_report())
    assert report_schema["properties"]["report_type"]["const"] == gate.REPORT_TYPE


def test_fixture_report_is_deterministic_and_has_expected_counts():
    first, first_failures = gate.build_report(
        fixture=_fixture(),
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )
    second, second_failures = gate.build_report(
        fixture=_fixture(),
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )

    assert first_failures == []
    assert second_failures == []
    assert first == second
    assert gate.serialize_report(first) == gate.serialize_report(second)
    assert first == json.loads(REPORT.read_text(encoding="utf-8"))
    assert first["attempted_promotion_count"] == 14
    assert first["allowed_promotion_count"] == 7
    assert first["blocked_promotion_count"] == 7
    assert first["invalid_promotion_count"] == 0
    assert first["optimizer_promotion_allowed_count"] == 0
    assert first["runtime_promotion_allowed_count"] == 0
    assert first["live_promotion_allowed_count"] == 0
    assert first["quantum_backend_promotion_allowed_count"] == 0
    assert first["missing_receipt_count"] == 2
    assert first["mismatched_receipt_type_count"] == 1
    assert first["missing_evidence_locator_count"] == 12
    assert first["final_ready"] is False
    assert first["authority_boundary_all_false"] is True


def test_dev_mode_passes_but_final_mode_remains_incomplete():
    dev = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        lifecycle_report_path=LIFECYCLE_REPORT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )
    final = gate.validate(
        mode="final",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        lifecycle_report_path=LIFECYCLE_REPORT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )

    assert dev.failures == ()
    assert final.ok is False
    _assert_failure_contains(final.failures, "final mode incomplete")


def test_required_transition_receipt_type_map_and_terminal_rules():
    assert (
        gate.expected_receipt_type("INVENTORY_ONLY", "RESEARCH_CANDIDATE")
        == "OWNER_RESEARCH_TRIAGE_RECEIPT"
    )
    assert (
        gate.expected_receipt_type("RESEARCH_CANDIDATE", "SOURCE_EVIDENCE_REQUIRED")
        == "SOURCE_EVIDENCE_TARGET_RECEIPT"
    )
    assert (
        gate.expected_receipt_type(
            "SOURCE_EVIDENCE_REQUIRED",
            "RANGE_VALIDATED_STATIC_ONLY",
        )
        == "SOURCE_EVIDENCE_ACCEPTANCE_RECEIPT"
    )
    assert (
        gate.expected_receipt_type("RANGE_VALIDATED_STATIC_ONLY", "REPLAY_PAPER_CANDIDATE")
        == "REPLAY_PAPER_CANDIDATE_RECEIPT"
    )
    assert (
        gate.expected_receipt_type("REPLAY_PAPER_CANDIDATE", "REPLAY_PAPER_VALIDATED")
        == "DUAL_RESULT_REVIEW_RECEIPT"
    )
    assert (
        gate.expected_receipt_type("REPLAY_PAPER_VALIDATED", "OPTIMIZER_ELIGIBLE")
        == "OPTIMIZER_ELIGIBILITY_RECEIPT"
    )
    assert (
        gate.expected_receipt_type("OPTIMIZER_ELIGIBLE", "RUNTIME_ELIGIBLE")
        == "RUNTIME_ELIGIBILITY_RECEIPT"
    )
    assert (
        gate.expected_receipt_type("RUNTIME_ELIGIBLE", "LIVE_ELIGIBLE")
        == "LIVE_OWNER_APPROVAL_RECEIPT"
    )
    assert (
        gate.expected_receipt_type("RESEARCH_CANDIDATE", "QUARANTINED_UNPROVEN")
        == "QUARANTINE_RECEIPT"
    )
    assert (
        gate.expected_receipt_type("SOURCE_EVIDENCE_REQUIRED", "RETIRED_NOT_USEFUL")
        == "RETIREMENT_RECEIPT"
    )
    assert gate.expected_receipt_type("RETIRED_NOT_USEFUL", "QUARANTINED_UNPROVEN") is None
    assert gate.expected_receipt_type("LIVE_ELIGIBLE", "RETIRED_NOT_USEFUL") is None


def test_missing_receipt_and_mismatched_receipt_type_block_promotion():
    fixture = _fixture()
    entries = _entries_by_pattern()
    entry = entries["atomicrows_inventory_only_bundle_absent_pattern"]

    missing = gate.decide_promotion(
        entry,
        "INVENTORY_ONLY",
        "RESEARCH_CANDIDATE",
        None,
    )
    assert missing.allowed is False
    assert missing.missing_receipt is True

    mismatch_attempt = _attempt(
        fixture,
        "research_candidate_to_source_evidence_blocked_by_mismatched_receipt_type",
    )
    mismatch = gate.decide_promotion(
        entries["external_microstructure_feature_candidate_pattern"],
        mismatch_attempt["from_status"],
        mismatch_attempt["to_status"],
        mismatch_attempt["receipt"],
    )
    assert mismatch.allowed is False
    assert mismatch.mismatched_receipt_type is True


def test_optimizer_runtime_live_and_quantum_promotions_need_explicit_receipts():
    fixture = _fixture()
    entries = _entries_by_pattern()
    classical = entries["edge_parameter_stack_replay_candidate_pattern"]
    quantum = entries["quantum_advisory_parameter_candidate_pattern"]

    optimizer_receipt = copy.deepcopy(
        _attempt(
            fixture,
            "replay_validated_to_optimizer_blocked_without_source_range_replay_paper_evidence",
        )["receipt"]
    )
    optimizer_blocked = gate.decide_promotion(
        classical,
        "REPLAY_PAPER_VALIDATED",
        "OPTIMIZER_ELIGIBLE",
        optimizer_receipt,
    )
    assert optimizer_blocked.allowed is False
    assert optimizer_blocked.missing_evidence_locator_reasons

    support = optimizer_receipt["supporting_receipt_locators"]
    support["source_evidence_acceptance_receipt_locator"] = "synthetic://source"
    support["range_validation_receipt_locator"] = "synthetic://range"
    support["replay_result_receipt_locator"] = "synthetic://replay"
    support["paper_result_receipt_locator"] = "synthetic://paper"
    assert gate.decide_promotion(
        classical,
        "REPLAY_PAPER_VALIDATED",
        "OPTIMIZER_ELIGIBLE",
        optimizer_receipt,
    ).allowed

    runtime_missing = gate.decide_promotion(
        classical,
        "OPTIMIZER_ELIGIBLE",
        "RUNTIME_ELIGIBLE",
        None,
    )
    assert runtime_missing.allowed is False
    assert runtime_missing.missing_receipt is True

    runtime_receipt = copy.deepcopy(
        _attempt(
            fixture,
            "quantum_optimizer_to_runtime_blocked_without_backend_provider_evidence",
        )["receipt"]
    )
    runtime_receipt["quantum_backend_provider_evidence_required"] = False
    assert gate.decide_promotion(
        classical,
        "OPTIMIZER_ELIGIBLE",
        "RUNTIME_ELIGIBLE",
        runtime_receipt,
    ).allowed

    live_receipt = copy.deepcopy(
        _attempt(fixture, "runtime_to_live_blocked_without_live_canary_receipt")["receipt"]
    )
    assert not gate.decide_promotion(
        classical,
        "RUNTIME_ELIGIBLE",
        "LIVE_ELIGIBLE",
        live_receipt,
    ).allowed
    live_receipt["supporting_receipt_locators"][
        "live_canary_eligibility_receipt_locator"
    ] = "synthetic://live-canary"
    assert gate.decide_promotion(
        classical,
        "RUNTIME_ELIGIBLE",
        "LIVE_ELIGIBLE",
        live_receipt,
    ).allowed

    quantum_blocked = gate.decide_promotion(
        quantum,
        "OPTIMIZER_ELIGIBLE",
        "RUNTIME_ELIGIBLE",
        _attempt(
            fixture,
            "quantum_optimizer_to_runtime_blocked_without_backend_provider_evidence",
        )["receipt"],
    )
    assert quantum_blocked.allowed is False
    assert any(
        "quantum backend/provider evidence" in reason
        for reason in quantum_blocked.missing_evidence_locator_reasons
    )


def test_false_allowed_promotion_claim_fails_closed():
    fixture = _fixture()
    _attempt(
        fixture,
        "inventory_only_to_research_candidate_blocked_by_direct_yaml_edit_without_receipt",
    )["declared_promotion_allowed"] = True

    report, failures = gate.build_report(
        fixture=fixture,
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )

    assert report["invalid_promotion_count"] == 1
    _assert_failure_contains(failures, "prohibited lifecycle promotion")


def test_promotion_receipt_gate_does_not_create_atomicrows_bundle_or_hash():
    assert CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()

    result = gate.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        lifecycle_report_path=LIFECYCLE_REPORT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )

    assert result.failures == ()
    assert CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
