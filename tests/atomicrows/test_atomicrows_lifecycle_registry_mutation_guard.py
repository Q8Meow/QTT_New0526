from __future__ import annotations

import copy
import json
from pathlib import Path

from tools import build_atomicrows_parameter_lifecycle_report as lifecycle_builder
from tools import validate_atomicrows_lifecycle_registry_mutation_guard as guard


REPO_ROOT = Path(".")
REGISTRY = Path("docs/master_plan/atomic_rows/AtomicRowsParameterLifecycleRegistry.yaml")
LIFECYCLE_REPORT = Path("docs/master_plan/generated/AtomicRowsParameterLifecycleReport.json")
PROMOTION_GATE_REPORT = Path(
    "docs/master_plan/generated/AtomicRowsLifecyclePromotionReceiptGate.report.json"
)
SCHEMA = Path(
    "schemas/atomicrows/atomicrows_lifecycle_registry_mutation_guard.schema.json"
)
FIXTURE = Path(
    "tests/fixtures/atomicrows/"
    "synthetic_atomicrows_lifecycle_registry_mutation_guard_blocked.v1.fixture.json"
)
REPORT = Path(
    "docs/master_plan/generated/AtomicRowsLifecycleRegistryMutationGuard.report.json"
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
    for attempt in fixture["attempted_mutations"]:
        if attempt["attempt_id"] == attempt_id:
            return attempt
    raise AssertionError(f"missing attempt {attempt_id}")


def _assert_failure_contains(failures: list[str] | tuple[str, ...], fragment: str) -> None:
    assert any(fragment in failure for failure in failures), failures


def test_schema_declares_mutation_classes_statuses_owner_receipts_and_report_fields():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    report_schema = schema["$defs"]["mutation_guard_report"]

    assert schema["additionalProperties"] is False
    assert schema["$defs"]["mutation_class"]["enum"] == list(guard.MUTATION_CLASSES)
    assert schema["$defs"]["owner_override_receipt_type"]["enum"] == list(
        guard.OWNER_OVERRIDE_RECEIPT_TYPES
    )
    assert schema["$defs"]["lifecycle_status"]["enum"] == list(
        lifecycle_builder.LIFECYCLE_STATUSES
    )
    assert report_schema["required"] == list(guard._empty_report())
    assert report_schema["properties"]["report_type"]["const"] == guard.REPORT_TYPE


def test_fixture_report_is_deterministic_and_has_expected_counts():
    first, first_failures = guard.build_report(
        fixture=_fixture(),
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )
    second, second_failures = guard.build_report(
        fixture=_fixture(),
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )

    assert first_failures == []
    assert second_failures == []
    assert first == second
    assert guard.serialize_report(first) == guard.serialize_report(second)
    assert first == json.loads(REPORT.read_text(encoding="utf-8"))
    assert first["attempted_mutation_count"] == 18
    assert first["allowed_mutation_count"] == 3
    assert first["blocked_mutation_count"] == 15
    assert first["invalid_mutation_count"] == 0
    assert first["authority_increasing_mutation_count"] == 11
    assert first["authority_increasing_allowed_count"] == 0
    assert first["status_change_count"] == 2
    assert first["status_change_allowed_count"] == 0
    assert first["optimizer_authority_mutation_allowed_count"] == 0
    assert first["runtime_authority_mutation_allowed_count"] == 0
    assert first["live_authority_mutation_allowed_count"] == 0
    assert first["quantum_backend_authority_mutation_allowed_count"] == 0
    assert first["row_addition_count"] == 2
    assert first["row_removal_count"] == 1
    assert first["missing_receipt_count"] == 11
    assert first["mismatched_receipt_count"] == 1
    assert first["owner_override_mutation_count"] == 4
    assert first["owner_override_allowed_count"] == 2
    assert first["owner_override_blocked_count"] == 2
    assert first["owner_override_external_fact_fabrication_blocked_count"] == 1
    assert first["final_ready"] is False
    assert first["authority_boundary_all_false"] is True


def test_dev_mode_passes_but_final_mode_remains_incomplete():
    dev = guard.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        lifecycle_report_path=LIFECYCLE_REPORT,
        promotion_gate_report_path=PROMOTION_GATE_REPORT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )
    final = guard.validate(
        mode="final",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        lifecycle_report_path=LIFECYCLE_REPORT,
        promotion_gate_report_path=PROMOTION_GATE_REPORT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )

    assert dev.failures == ()
    assert final.ok is False
    _assert_failure_contains(final.failures, "final mode incomplete")


def test_status_escalation_and_terminal_status_reactivation_need_receipts():
    entries = _entries_by_pattern()
    fixture = _fixture()

    direct_escalation = guard.decide_mutation(
        entries["atomicrows_inventory_only_bundle_absent_pattern"],
        _attempt(fixture, "direct_status_escalation_without_promotion_receipt_blocked"),
    )
    assert direct_escalation.allowed is False
    assert direct_escalation.missing_receipt is True

    quarantine_reactivation = guard.decide_mutation(
        entries["unproven_false_eligibility_claim_pattern"],
        _attempt(
            fixture,
            "quarantined_unproven_to_research_candidate_without_receipt_blocked",
        ),
    )
    assert quarantine_reactivation.allowed is False
    assert quarantine_reactivation.authority_increasing is True


def test_false_authority_mutations_are_blocked_without_matching_receipts():
    entries = _entries_by_pattern()
    fixture = _fixture()

    cases = [
        (
            "edge_parameter_stack_replay_candidate_pattern",
            "optimizer_eligibility_false_to_true_without_required_receipts_blocked",
            "optimizer_authority",
        ),
        (
            "edge_parameter_stack_replay_candidate_pattern",
            "runtime_eligibility_false_to_true_without_runtime_receipt_blocked",
            "runtime_authority",
        ),
        (
            "edge_parameter_stack_replay_candidate_pattern",
            "live_eligibility_false_to_true_without_live_owner_approval_blocked",
            "live_authority",
        ),
        (
            "source_dependent_parameter_value_pattern",
            "allowed_range_widening_without_range_validation_receipt_blocked",
            "authority_increasing",
        ),
        (
            "edge_parameter_stack_replay_candidate_pattern",
            "default_value_policy_into_active_authority_without_receipts_blocked",
            "optimizer_authority",
        ),
    ]
    for pattern_id, attempt_id, flag in cases:
        decision = guard.decide_mutation(entries[pattern_id], _attempt(fixture, attempt_id))
        assert decision.allowed is False
        assert getattr(decision, flag) is True


def test_quantum_and_source_backed_authority_need_specific_evidence():
    entries = _entries_by_pattern()
    fixture = _fixture()

    quantum = guard.decide_mutation(
        entries["quantum_advisory_parameter_candidate_pattern"],
        _attempt(
            fixture,
            "quantum_backend_authority_without_backend_provider_evidence_blocked",
        ),
    )
    assert quantum.allowed is False
    assert quantum.quantum_backend_authority is True
    assert quantum.mismatched_receipt is True

    source_backed = guard.decide_mutation(
        entries["external_microstructure_feature_candidate_pattern"],
        _attempt(
            fixture,
            "source_backed_authority_without_accepted_source_evidence_blocked",
        ),
    )
    assert source_backed.allowed is False
    assert source_backed.missing_receipt is True


def test_owner_override_receipts_are_limited_to_internal_policy_only():
    entries = _entries_by_pattern()
    fixture = _fixture()

    allowed = guard.decide_mutation(
        entries["external_microstructure_feature_candidate_pattern"],
        _attempt(fixture, "owner_override_internal_policy_route_note_allowed"),
    )
    assert allowed.allowed is True
    assert allowed.owner_override_used is True

    external_fact = guard.decide_mutation(
        entries["source_dependent_parameter_value_pattern"],
        _attempt(fixture, "owner_override_fabricating_external_source_facts_blocked"),
    )
    assert external_fact.allowed is False
    assert external_fact.owner_override_external_fact_fabrication_blocked is True

    live_grant = guard.decide_mutation(
        entries["edge_parameter_stack_replay_candidate_pattern"],
        _attempt(
            fixture,
            "owner_override_granting_live_order_authority_without_live_receipts_blocked",
        ),
    )
    assert live_grant.allowed is False
    assert live_grant.owner_override_blocked is True


def test_row_addition_defaults_to_inventory_only_and_row_removal_needs_receipt():
    entries = _entries_by_pattern()
    fixture = _fixture()

    safe_addition = guard.decide_mutation(
        None,
        _attempt(fixture, "row_addition_inventory_only_default_allowed"),
    )
    assert safe_addition.allowed is True

    active_addition = guard.decide_mutation(
        None,
        _attempt(fixture, "row_addition_active_optimizer_authority_without_receipts_blocked"),
    )
    assert active_addition.allowed is False
    assert active_addition.optimizer_authority is True

    removal = guard.decide_mutation(
        entries["external_microstructure_feature_candidate_pattern"],
        _attempt(
            fixture,
            "row_removal_without_retirement_or_quarantine_receipt_blocked",
        ),
    )
    assert removal.allowed is False
    assert removal.missing_receipt is True


def test_unknown_class_status_missing_identity_and_false_allowed_claim_fail_closed():
    fixture = _fixture()
    fixture["attempted_mutations"][0]["mutation_class"] = "UNKNOWN_MUTATION"
    report, failures = guard.build_report(
        fixture=fixture,
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )
    assert report["invalid_mutation_count"] == 1
    _assert_failure_contains(failures, "unknown mutation_class")

    fixture = _fixture()
    fixture["attempted_mutations"][0]["from_status"] = "UNKNOWN_STATUS"
    report, failures = guard.build_report(
        fixture=fixture,
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )
    assert report["invalid_mutation_count"] == 1
    _assert_failure_contains(failures, "unknown from_status")

    fixture = _fixture()
    fixture["attempted_mutations"][0]["row_pattern_id"] = null_id = None
    assert null_id is None
    report, failures = guard.build_report(
        fixture=fixture,
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )
    assert report["invalid_mutation_count"] == 1
    _assert_failure_contains(failures, "exactly one")

    fixture = _fixture()
    _attempt(
        fixture,
        "optimizer_eligibility_false_to_true_without_required_receipts_blocked",
    )["declared_mutation_allowed"] = True
    report, failures = guard.build_report(
        fixture=fixture,
        registry=_registry(),
        lifecycle_report=_lifecycle_report(),
    )
    assert report["invalid_mutation_count"] == 1
    _assert_failure_contains(failures, "prohibited registry mutation")


def test_matching_receipt_can_allow_authority_increasing_mutation_without_live_authority():
    fixture = _fixture()
    attempt = copy.deepcopy(
        _attempt(
            fixture,
            "optimizer_eligibility_false_to_true_without_required_receipts_blocked",
        )
    )
    attempt["receipt"] = copy.deepcopy(
        _attempt(
            fixture,
            "quantum_backend_authority_without_backend_provider_evidence_blocked",
        )["receipt"]
    )
    attempt["receipt"]["receipt_type"] = "OPTIMIZER_ELIGIBILITY_RECEIPT"
    support = attempt["receipt"]["supporting_receipt_locators"]
    support["source_evidence_acceptance_receipt_locator"] = "synthetic://source"
    support["range_validation_receipt_locator"] = "synthetic://range"
    support["replay_result_receipt_locator"] = "synthetic://replay"
    support["paper_result_receipt_locator"] = "synthetic://paper"

    decision = guard.decide_mutation(
        _entries_by_pattern()["edge_parameter_stack_replay_candidate_pattern"],
        attempt,
    )

    assert decision.allowed is True
    assert decision.optimizer_authority is True
    assert decision.live_authority is False


def test_registry_mutation_guard_does_not_create_atomicrows_bundle_or_hash():
    assert not CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()

    result = guard.validate(
        mode="dev",
        repo_root=REPO_ROOT,
        registry_path=REGISTRY,
        lifecycle_report_path=LIFECYCLE_REPORT,
        promotion_gate_report_path=PROMOTION_GATE_REPORT,
        schema_path=SCHEMA,
        fixture_path=FIXTURE,
    )

    assert result.failures == ()
    assert not CANONICAL_BUNDLE.exists()
    assert not CANONICAL_BUNDLE_SHA.exists()
