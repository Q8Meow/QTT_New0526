"""Centralized 9-row Tranche-C no-write execution contract matrix."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ComputationControlPlaneError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.idempotency import (
    DuplicateEventDispositionV1,
    IdempotencyClaimReceiptV1,
    IdempotencyClaimStateV1,
    IdempotencyOutcomeV1,
    canonical_request_json_v1,
    decide_duplicate_event_v1,
    decide_existing_claim_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.lifecycle import (
    ClockEvidenceV1,
    ClockFreshnessPolicyV1,
    EconomicIdentitySetV1,
    ExecutionCustodyReceiptV1,
    FillAccumulatorV1,
    GateDispositionV1,
    ORDER_INTENT_STATE_MACHINE_V1,
    OrderIntentRecordV1,
    PREFLIGHT_GATE_CLASSES,
    PreflightTerminalOutcomeV1,
    PretradeGateBundleV1,
    PretradeGateResultV1,
    RateLimitDispositionV1,
    RateLimitBudgetV1,
    StateTransitionReceiptV1,
    TransitionDispositionV1,
    validate_clock_freshness_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.outbox import (
    OutboxDispatchStateV1,
    OutboxIntentRecordV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    QKUComputationControlPlaneV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    ST12C_CONTROL_COVERAGE_MATRIX,
    ST12C_NO_EFFECT_FLAGS,
    ST12C_REFERENCE_ADAPTER_MATRIX,
    ST12C_REQUIRED_ASSERTION_CLASSES,
    validate_domain,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)
EXECUTION_CASES = tuple(row for row in ST12C_CONTROL_COVERAGE_MATRIX if row.domain == "execution")


def _gates(*, failed: str | None = None) -> tuple[PretradeGateResultV1, ...]:
    return tuple(
        PretradeGateResultV1(
            gate_class=gate,
            disposition=GateDispositionV1.FAIL if gate == failed else GateDispositionV1.PASS,
            evidence_ref=f"evidence::{gate}",
            reason_code="FAILED" if gate == failed else "PASS",
        )
        for gate in PREFLIGHT_GATE_CLASSES
    )


def _order_intent(*, state: str = "CONTRACT_ONLY", no_order: bool = True) -> OrderIntentRecordV1:
    return OrderIntentRecordV1(
        "intent", "candidate", "snapshot", ("component-v1",), "venue", "market", "contract",
        "BUY_YES", "10", "0.50", "LIMIT", "GTC", NOW + timedelta(minutes=1),
        "owner-envelope", "NO_TRADE", ("risk", "cash", "source"), state, no_order,
    )


@pytest.mark.parametrize("case", EXECUTION_CASES, ids=lambda row: row.control_slug)
def test_execution_contract_matrix(case) -> None:
    assert case.required_assertion_classes == ST12C_REQUIRED_ASSERTION_CLASSES
    assert case.adapter_applicability == ST12C_REFERENCE_ADAPTER_MATRIX
    assert case.expected_no_effect_flags == ST12C_NO_EFFECT_FLAGS
    assert all(flag.startswith("NO_") for flag in case.expected_no_effect_flags)
    assert validate_domain("execution").passed

    slug = case.control_slug
    if slug == "ack-reject-fill-custody":
        custody = ExecutionCustodyReceiptV1(
            "custody", "event", "provider-request", "intent", "attempt", "provider-order", "ACK",
            "fixture-payload", NOW, NOW, "sequence-1", "PROVIDER_PENDING", "ACKNOWLEDGED",
            "DETERMINISTIC_FIXTURE_ONLY",
        )
        assert custody.candidate_state == "ACKNOWLEDGED"
        with pytest.raises(ComputationControlPlaneError):
            ExecutionCustodyReceiptV1(
                "custody-2", "event-2", "provider-request-2", "intent", "attempt-2", "provider-order-2", "ACK",
                "provider-payload", NOW, NOW, "sequence-2", "PROVIDER_PENDING", "ACKNOWLEDGED", "PROVIDER_TRUTH",
            )
    elif slug == "clock-and-stale-checks":
        policy = ClockFreshnessPolicyV1("clock-policy", timedelta(seconds=5), timedelta(seconds=1), timedelta(seconds=10))
        evidence = ClockEvidenceV1(
            NOW, NOW, NOW + timedelta(milliseconds=100), NOW,
            NOW + timedelta(milliseconds=100), NOW + timedelta(milliseconds=200),
            NOW + timedelta(milliseconds=300), NOW + timedelta(milliseconds=400),
            NOW + timedelta(milliseconds=500), 1_000_000,
        )
        receipt = validate_clock_freshness_v1(evidence, policy)
        assert receipt.policy_ref == policy.policy_id and receipt.monotonic_duration_ns == 1_000_000
        with pytest.raises(ComputationControlPlaneError):
            validate_clock_freshness_v1(
                ClockEvidenceV1(
                    NOW - timedelta(seconds=30), NOW - timedelta(seconds=30), NOW,
                    NOW - timedelta(seconds=30), NOW, NOW, NOW, NOW, NOW, 1_000_000,
                ),
                policy,
            )
    elif slug == "idempotency-key":
        request = canonical_request_json_v1({"amount": "1.00", "command": "book"})
        claim = IdempotencyClaimReceiptV1("claim", "key", "COMMAND", request, IdempotencyClaimStateV1.COMPLETED, "receipt", NOW, NOW, None)
        assert decide_existing_claim_v1(claim, request).outcome is IdempotencyOutcomeV1.REPLAYED_SAME_PAYLOAD
        assert decide_existing_claim_v1(claim, canonical_request_json_v1({"amount": "2.00", "command": "book"})).outcome is IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD
        assert decide_duplicate_event_v1(request, request) is DuplicateEventDispositionV1.EXACT_DUPLICATE
        assert decide_duplicate_event_v1(request, canonical_request_json_v1({"amount": "3.00", "command": "book"})) is DuplicateEventDispositionV1.CONFLICT_QUARANTINED
        identities = EconomicIdentitySetV1("intent", "command", "attempt", "provider-request", "request", "trace", "transaction", "event")
        assert len({getattr(identities, name) for name in identities.__slots__}) == 8
        with pytest.raises(ComputationControlPlaneError):
            EconomicIdentitySetV1("same", "same", "attempt", "provider-request", "request", "trace", "transaction", "event")
    elif slug == "order-intent-contract":
        intent = _order_intent()
        assert intent.no_order_authority_flag and intent.intent_state == "CONTRACT_ONLY"
        assert _order_intent(state="SUBMIT_DISABLED").intent_state == "SUBMIT_DISABLED"
        with pytest.raises(ComputationControlPlaneError):
            _order_intent(no_order=False)
        with pytest.raises(ComputationControlPlaneError):
            OrderIntentRecordV1("intent", "candidate", "snapshot", ("component",), "venue", "market", "contract", "BUY", "10.0", ".5", "LIMIT", "GTC", NOW, "owner", "mode", ("gate",), "SUBMITTED", True)
    elif slug == "order-state-machine":
        accepted = StateTransitionReceiptV1(
            "transition", "intent", "ORDER_INTENT_STATE_MACHINE_V1", "DRAFT", "VALIDATE", "VALIDATED",
            TransitionDispositionV1.ACCEPTED, "event", 0, 1, NOW, NOW, "ACCEPTED", False,
        )
        duplicate = StateTransitionReceiptV1(
            "transition-dup", "intent", "ORDER_INTENT_STATE_MACHINE_V1", "VALIDATED", "VALIDATE", "VALIDATED",
            TransitionDispositionV1.EXACT_DUPLICATE, "event", 1, 1, NOW, NOW, "DUPLICATE", False,
        )
        assert accepted.aggregate_version_after == 1 and duplicate.aggregate_version_after == 1
        with pytest.raises(ComputationControlPlaneError):
            StateTransitionReceiptV1(
                "bad", "intent", "ORDER_INTENT_STATE_MACHINE_V1", "DRAFT", "SUBMIT", "SUBMIT_DISABLED",
                TransitionDispositionV1.ACCEPTED, "event-bad", 0, 1, NOW, NOW, "BAD", False,
            )
        with pytest.raises(ComputationControlPlaneError):
            StateTransitionReceiptV1(
                "bad-duplicate", "intent", "ORDER_INTENT_STATE_MACHINE_V1", "VALIDATED", "VALIDATE", "SUBMIT_DISABLED",
                TransitionDispositionV1.EXACT_DUPLICATE, "event-duplicate", 1, 1, NOW, NOW, "DUPLICATE", False,
            )
        reconciled = StateTransitionReceiptV1(
            "ambiguous", "future-order", "FUTURE_ORDER_CUSTODY_STATE_MACHINE_V1",
            "PROVIDER_PENDING", "TIMEOUT", "UNKNOWN_RECONCILIATION_REQUIRED",
            TransitionDispositionV1.RECONCILIATION_REQUIRED, "event-timeout", 2, 3,
            NOW, NOW, "AMBIGUOUS", True,
        )
        assert reconciled.reconciliation_required and reconciled.aggregate_version_after == 3
    elif slug == "partial-fill-races":
        fills = FillAccumulatorV1("100", (("fill-1", 1, NOW, "40", canonical_request_json_v1({"q": "40"})), ("fill-1", 1, NOW, "40", canonical_request_json_v1({"q": "40"})), ("fill-2", 2, NOW, "60", canonical_request_json_v1({"q": "60"}))))
        assert fills.filled_quantity == Decimal("100") and fills.remaining_quantity == 0
        with pytest.raises(ComputationControlPlaneError):
            FillAccumulatorV1("100", (("fill", 1, NOW, "60", "{}"), ("fill", 1, NOW, "61", "{}")))
        with pytest.raises(ComputationControlPlaneError):
            FillAccumulatorV1("100", (("f1", 1, NOW, "60", "{}"), ("f2", 2, NOW, "41", "{}")))
        with pytest.raises(ComputationControlPlaneError):
            FillAccumulatorV1("100", (("f1", 1, NOW, "20", "{}"), ("f2", 1, NOW, "20", "{}")))
    elif slug == "pretrade-gates":
        passed = PretradeGateBundleV1(_gates(), PreflightTerminalOutcomeV1.SUBMIT_DISABLED, True)
        blocked = PretradeGateBundleV1(_gates(failed="CASH"), PreflightTerminalOutcomeV1.PREFLIGHT_BLOCKED, False)
        assert passed.outbox_intent_allowed and not blocked.outbox_intent_allowed
        with pytest.raises(ComputationControlPlaneError):
            PretradeGateBundleV1(_gates(failed="SOURCE"), PreflightTerminalOutcomeV1.SUBMIT_DISABLED, True)
    elif slug == "rate-limit-control":
        admitted = RateLimitBudgetV1(
            "budget", "provider", "account", "orders", "one-minute", "source-binding",
            "10", "10", (("CREATE", "2", "1"), ("CANCEL", "1", "0")),
            "CREATE", 2, NOW, NOW + timedelta(minutes=1), None, None,
        )
        assert admitted.admission_decision.disposition is RateLimitDispositionV1.ADMIT
        assert admitted.admission_decision.remaining_units_after == Decimal("6")
        deferred = RateLimitBudgetV1(
            "budget-2", "provider", "account", "orders", "one-minute", "source-binding",
            "10", "1", (("CREATE", "2", "1"),), "CREATE", 2,
            NOW, NOW + timedelta(minutes=1), None, "1",
        )
        assert deferred.admission_decision.disposition is RateLimitDispositionV1.DEFER
        assert deferred.admission_decision.next_eligible_at is not None
        with pytest.raises(ComputationControlPlaneError):
            RateLimitBudgetV1(
                "budget", "provider", "account", "orders", "one-minute", "source-binding",
                "10", "10", (), "CREATE", 1, NOW, NOW + timedelta(minutes=1), None, None,
            )
    elif slug == "single-release-authority":
        intent = OutboxIntentRecordV1("outbox", "FUTURE_RELEASE_CONTRACT", "aggregate", "receipt", NOW)
        assert intent.dispatch_state is OutboxDispatchStateV1.RECORDED_NOT_DISPATCHABLE
        assert intent.dispatch_attempt_count == 0 and intent.next_eligible_at is None
        with pytest.raises(ComputationControlPlaneError):
            OutboxIntentRecordV1("outbox-2", "TOPIC", "aggregate", "receipt", NOW, dispatch_attempt_count=1)
        public = {name for name, value in QKUComputationControlPlaneV1.__dict__.items() if callable(value) and not name.startswith("_")}
        assert not {"submit", "cancel", "amend", "sign", "dispatch", "send"} & public
        assert "SUBMIT_DISABLED" in ORDER_INTENT_STATE_MACHINE_V1.terminal_states
    else:  # pragma: no cover - coverage meta-test makes this unreachable
        raise AssertionError(f"unhandled control case {slug}")
