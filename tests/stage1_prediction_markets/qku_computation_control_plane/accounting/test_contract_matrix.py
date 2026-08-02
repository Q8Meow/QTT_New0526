"""Centralized 16-row Tranche-C accounting contract matrix."""

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane import (
    implementation_registry as implementation_registry_module,
)

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.accounting import (
    AccountingAmountV1,
    AccountingAndTCAServiceV1,
    CASH_STATE_CLASS_REGISTRY,
    CashStateClassV1,
    CashStateProjectionV1,
    CostEmbeddingV1,
    CrossVenueTransferV1,
    EntrySideV1,
    ExposureProjectionV1,
    JournalAccountV1,
    JournalPostingV1,
    JournalTransactionV1,
    NormalBalanceV1,
    PositionEventClassV1,
    PositionEventV1,
    ReconciliationRunV1,
    ReconciliationStateV1,
    TCADecompositionV1,
    project_position_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    QuantizationPolicyV1,
    QuantizationRoundingV1,
    exact_decimal,
    quantize_decimal_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.economic_math import (
    ActivePriceGridRangeV1,
    BinaryBookSnapshotV1,
    FeeScheduleBindingV1,
    FillQuantityDistributionArtifactV1,
    TRANCHE_C_MATH_SPECIFICATIONS,
    binary_book_implied_asks_v1,
    expected_partial_fill_quantity_v1,
    global_prediction_market_fee_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ComputationControlPlaneError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.idempotency import (
    IdempotencyClaimReceiptV1,
    IdempotencyClaimStateV1,
    canonical_request_json_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.lifecycle import (
    FillAccumulatorV1,
    StateTransitionReceiptV1,
    TransitionDispositionV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import (
    InMemoryPersistenceAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
    TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES,
    TRANCHE_C_PARAMETER_APPLICATION_BINDINGS,
    TRANCHE_C_PARAMETER_POLICIES,
    TrancheCDrawdownCalibrationArtifactV1,
    TrancheCParameterEvidenceClassV1,
    TrancheCParameterEvidenceV1,
    TrancheCExplicitParameterValueV1,
    TrancheCParameterPolicyClassV1,
    resolve_tranche_c_parameter_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    IMPLEMENTATION_REGISTRY,
    TRANCHE_C_IMPLEMENTATION_REGISTRY,
    compute_math_36_kalshi_binary_book_transform,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.outbox import (
    OutboxIntentRecordV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    EconomicEventRecordV1,
    EconomicReceiptEventSpineV1,
    EconomicRecordTypeV1,
    TypedEconomicAmountV1,
    ValueLineageEdgeV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.rollback import (
    build_journal_reversal_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import (
    SQLiteReferenceAdapterV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.transaction import (
    TransactionRetryPolicyV1,
    TransactionTerminalStateV1,
    TrancheCAtomicRecordSetV1,
    TrancheCUnitOfWorkV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    ST12C_CONTROL_COVERAGE_MATRIX,
    ST12C_NO_EFFECT_FLAGS,
    ST12C_ORIGINAL_TEST_TO_MATRIX_LOCATOR,
    ST12C_REFERENCE_ADAPTER_MATRIX,
    ST12C_REQUIRED_ASSERTION_CLASSES,
    validate_domain,
    validate_st12c_control_coverage_matrix,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)
DYNAMIC_OBSERVED_AT = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
DYNAMIC_EVALUATED_AT = datetime(2026, 1, 1, 0, 1, tzinfo=UTC)
DYNAMIC_RESOLUTION_AT = datetime(2026, 1, 1, 0, 2, tzinfo=UTC)
DYNAMIC_VALID_UNTIL = datetime(2026, 1, 1, 1, 0, tzinfo=UTC)
ACCOUNTING_CASES = tuple(row for row in ST12C_CONTROL_COVERAGE_MATRIX if row.domain == "accounting")


@pytest.fixture
def reference_directory():
    with TemporaryDirectory(prefix="qtt-st12c-") as directory:
        yield Path(directory)


def _amount(value: str, *, basis: str = "SETTLED") -> AccountingAmountV1:
    return AccountingAmountV1(value, "USD", "USD", basis, 2, "TEST::CENT")


def _accounts(*, second_basis: str = "SETTLED") -> dict[str, JournalAccountV1]:
    return {
        "cash": JournalAccountV1("cash", "ASSET", NormalBalanceV1.DEBIT, "USD", "USD", "SETTLED", "ACTIVE"),
        "clearing": JournalAccountV1("clearing", "LIABILITY", NormalBalanceV1.CREDIT, "USD", "USD", second_basis, "ACTIVE"),
    }


def _journal(*, credit: str = "1.00") -> tuple[JournalTransactionV1, tuple[JournalPostingV1, ...]]:
    postings = (
        JournalPostingV1("posting-debit", "journal-1", "cash", EntrySideV1.DEBIT, "1.00", "USD", "USD", "SETTLED", 2, NOW, NOW, "event-1"),
        JournalPostingV1("posting-credit", "journal-1", "clearing", EntrySideV1.CREDIT, credit, "USD", "USD", "SETTLED", 2, NOW, NOW, "event-1"),
    )
    return JournalTransactionV1("journal-1", "FILL", ("event-1",), tuple(row.posting_id for row in postings), NOW, NOW, "FILL_ACCEPTED", "DETERMINISTIC_FIXTURE"), postings


@pytest.mark.parametrize("case", ACCOUNTING_CASES, ids=lambda row: row.control_slug)
def test_accounting_contract_matrix(case) -> None:
    assert case.required_assertion_classes == ST12C_REQUIRED_ASSERTION_CLASSES
    assert case.adapter_applicability == ST12C_REFERENCE_ADAPTER_MATRIX
    assert case.expected_no_effect_flags == ST12C_NO_EFFECT_FLAGS
    assert all(flag.startswith("NO_") for flag in case.expected_no_effect_flags)
    assert validate_domain("accounting").passed

    slug = case.control_slug
    if slug == "capital-and-reserves":
        value = AccountingAndTCAServiceV1.deployable_capital(
            settled_spendable_cash=_amount("100.00"), reserve_cash_floor=_amount("10.00"),
            owner_protected_cash=_amount("5.00"), quarantined_capital=_amount("3.00"),
            reconciliation_state=ReconciliationStateV1.RECONCILED,
        )
        mutated = AccountingAndTCAServiceV1.deployable_capital(
            settled_spendable_cash=_amount("100.00"), reserve_cash_floor=_amount("11.00"),
            owner_protected_cash=_amount("5.00"), quarantined_capital=_amount("3.00"),
            reconciliation_state=ReconciliationStateV1.RECONCILED,
        )
        assert (value, mutated) == (Decimal("82.00"), Decimal("81.00"))
        with pytest.raises(ComputationControlPlaneError):
            AccountingAndTCAServiceV1.deployable_capital(
                settled_spendable_cash=_amount("100.00"), reserve_cash_floor=_amount("10.00", basis="PROJECTED"),
                owner_protected_cash=_amount("5.00"), quarantined_capital=_amount("3.00"),
                reconciliation_state=ReconciliationStateV1.RECONCILED,
            )
        with pytest.raises(ComputationControlPlaneError):
            AccountingAndTCAServiceV1.deployable_capital(
                settled_spendable_cash=_amount("100.00"), reserve_cash_floor=_amount("-1.00"),
                owner_protected_cash=_amount("5.00"), quarantined_capital=_amount("3.00"),
                reconciliation_state=ReconciliationStateV1.RECONCILED,
            )
    elif slug == "cash-state-separation":
        assert len(CASH_STATE_CLASS_REGISTRY) == 12
        assert len({row.value for row in CashStateClassV1}) == 12
        assert CashStateClassV1.UNREALIZED_PNL is not CashStateClassV1.SETTLED_SPENDABLE_CASH
        with pytest.raises(ValueError):
            CashStateClassV1("REALIZED_CASH")
        projected = CashStateProjectionV1("cash-p", CashStateClassV1.PROJECTED_EXECUTABLE_NET_CASH, "10.00", "USD", "PROJECTED", ("event",), ("journal",), NOW, NOW, ReconciliationStateV1.RECONCILED)
        settled = CashStateProjectionV1("cash-s", CashStateClassV1.SETTLED_SPENDABLE_CASH, "10.00", "USD", "SETTLED", ("event",), ("journal",), NOW, NOW, ReconciliationStateV1.RECONCILED)
        assert projected.cash_class is not settled.cash_class and projected.basis != settled.basis
    elif slug == "correction-and-reversal":
        journal, postings = _journal()
        bundle = build_journal_reversal_v1(
            original_transaction=journal, original_postings=postings,
            reversal_receipt_id="reversal-1", reversal_event_ref="event-reversal",
            reversal_transaction_id="journal-reversal", reversal_posting_ids=("reversal-debit", "reversal-credit"),
            requested_amount_by_original_posting=None, previously_reversed_by_original_posting={},
            reason_code="CORRECTION", authority_ref="OWNER", effective_at=NOW, recorded_at=NOW,
        )
        assert bundle.transaction.reversal_of_transaction_id == journal.journal_transaction_id
        assert all(row.decimal == 0 for row in bundle.receipt.remaining_reversible_amounts)
        with pytest.raises(ComputationControlPlaneError):
            build_journal_reversal_v1(
                original_transaction=journal, original_postings=postings,
                reversal_receipt_id="reversal-2", reversal_event_ref="event-reversal-2",
                reversal_transaction_id="journal-reversal-2", reversal_posting_ids=("r3", "r4"),
                requested_amount_by_original_posting={"posting-debit": "2", "posting-credit": "2"},
                previously_reversed_by_original_posting={}, reason_code="BAD", authority_ref="OWNER",
                effective_at=NOW, recorded_at=NOW,
            )
    elif slug == "cross-venue-conservation":
        transfer = CrossVenueTransferV1("transfer", "venue-a", "venue-b", _amount("10.00"), "posting-a", "posting-b", "PENDING_IN_TRANSIT")
        assert transfer.source_venue_ref != transfer.destination_venue_ref
        AccountingAndTCAServiceV1.validate_reserve_conservation(
            available_cash=_amount("60.00"), reserved_cash=_amount("20.00"), pending_cash=_amount("10.00"),
            owner_protected_cash=_amount("5.00"), quarantined_cash=_amount("5.00"), accepted_cash_basis=_amount("100.00"),
        )
        with pytest.raises(ComputationControlPlaneError):
            AccountingAndTCAServiceV1.validate_reserve_conservation(
                available_cash=_amount("60.00"), reserved_cash=_amount("20.00"), pending_cash=_amount("10.00"),
                owner_protected_cash=_amount("5.00"), quarantined_cash=_amount("4.00"), accepted_cash_basis=_amount("100.00"),
            )
    elif slug == "decimal-boundaries":
        assert exact_decimal("1.2500", field_name="money") == Decimal("1.2500")
        with pytest.raises(ComputationControlPlaneError):
            exact_decimal(1.25, field_name="money")
        with pytest.raises(ComputationControlPlaneError):
            AccountingAmountV1("+1.00", "USD", "USD", "SETTLED", 2, "TEST")
        with pytest.raises(ComputationControlPlaneError):
            AccountingAmountV1("1.0", "USD", "USD", "SETTLED", 2, "TEST")
    elif slug == "double-entry-conservation":
        journal, postings = _journal()
        AccountingAndTCAServiceV1.validate_journal(journal, postings, _accounts())
        bad_journal, bad_postings = _journal(credit="0.99")
        with pytest.raises(ComputationControlPlaneError):
            AccountingAndTCAServiceV1.validate_journal(bad_journal, bad_postings, _accounts())
    elif slug == "exposure-aggregation":
        projection = ExposureProjectionV1("exposure-1", (("VENUE_A|USD|PAYOUT_1|NET", "10"),), ("10",), ("position-1",), NOW, NOW)
        assert projection.signed_exposure_values == (Decimal("10"),)
        with pytest.raises(ComputationControlPlaneError):
            ExposureProjectionV1("bad", (("VENUE_A", "10"), ("VENUE_A", "10")), ("10", "-10"), ("p1",), NOW, NOW)
    elif slug == "fee-rebate-treatment":
        binding = FeeScheduleBindingV1("CATEGORY", "venue", "market-category", "v1", "source-epoch", datetime(2025, 1, 1, tzinfo=UTC), None, NOW, ("PLATFORM_FEE", "BUILDER_FEE_SEPARATE_ADDITIVE"), (("PLATFORM_FEE", ".05"),))
        policy = QuantizationPolicyV1("fee-5dp", "fee", "0.00001", QuantizationRoundingV1.HALF_EVEN, "USD", "USD", "FEE", 5, binding.binding_ref)
        fee = global_prediction_market_fee_v1(contracts="100", fee_rate=".05", price=".5", schedule_binding=binding, quantization_policy=policy, receipt_id="fee-r1")
        changed_binding = FeeScheduleBindingV1("CATEGORY-CHANGED", "venue", "market-category", "v2", "source-epoch-2", datetime(2025, 1, 1, tzinfo=UTC), None, NOW, ("PLATFORM_FEE", "BUILDER_FEE_SEPARATE_ADDITIVE"), (("PLATFORM_FEE", ".04"),))
        changed_policy = QuantizationPolicyV1("fee-5dp-changed", "fee", "0.00001", QuantizationRoundingV1.HALF_EVEN, "USD", "USD", "FEE", 5, changed_binding.binding_ref)
        changed = global_prediction_market_fee_v1(contracts="100", fee_rate=".04", price=".5", schedule_binding=changed_binding, quantization_policy=changed_policy, receipt_id="fee-r2")
        assert (fee.amount_after_rounding, changed.amount_after_rounding) == (Decimal("1.25000"), Decimal("1.00000"))
        with pytest.raises(ComputationControlPlaneError):
            global_prediction_market_fee_v1(contracts="100", fee_rate=".05", price=".5", schedule_binding=object(), quantization_policy=policy, receipt_id="bad")
        with pytest.raises(ComputationControlPlaneError):
            global_prediction_market_fee_v1(contracts="100", fee_rate=".04", price=".5", schedule_binding=binding, quantization_policy=policy, receipt_id="spoofed-rate")
    elif slug == "fill-branch-accounting":
        artifact = FillQuantityDistributionArtifactV1("distribution", "1", "source", "scope", 30, NOW, datetime(2027, 1, 1, tzinfo=UTC), "100", "0", (("0", ".2"), ("50", ".3"), ("100", ".5")))
        mutated = FillQuantityDistributionArtifactV1("distribution-2", "1", "source", "scope", 30, NOW, datetime(2027, 1, 1, tzinfo=UTC), "100", "0", (("0", ".3"), ("50", ".3"), ("100", ".4")))
        assert expected_partial_fill_quantity_v1(artifact=artifact) == Decimal("65")
        assert expected_partial_fill_quantity_v1(artifact=mutated) == Decimal("55")
        with pytest.raises(ComputationControlPlaneError):
            expected_partial_fill_quantity_v1(artifact=FillQuantityDistributionArtifactV1("bad", "1", "source", "scope", 30, NOW, datetime(2027, 1, 1, tzinfo=UTC), "100", "0", (("0", ".2"), ("100", ".7"))))
        fills = FillAccumulatorV1("100", (("fill-1", 1, NOW, "40", canonical_request_json_v1({"q": "40"})), ("fill-1", 1, NOW, "40", canonical_request_json_v1({"q": "40"}))))
        assert fills.filled_quantity == Decimal("40")
    elif slug == "pnl-classification":
        pnl = {CashStateClassV1.MARKED_PNL, CashStateClassV1.UNREALIZED_PNL, CashStateClassV1.REALIZED_EXIT_NET_CASH, CashStateClassV1.REALIZED_SETTLEMENT_NET_CASH}
        assert len(pnl) == 4 and CashStateClassV1.SETTLED_SPENDABLE_CASH not in pnl
    elif slug == "position-lifecycle":
        fill = PositionEventV1("accepted-fill", "cause-fill", PositionEventClassV1.ACCEPTED_FILL, 1, "10", "4.00", NOW, NOW, canonical_request_json_v1({"q": "10"}))
        position = project_position_v1(position_id="position-1", venue_ref="venue", market_ref="market", contract_ref="contract", outcome_or_side="YES", events=(fill, fill))
        assert position.event_refs == ("accepted-fill",)
        with pytest.raises(ComputationControlPlaneError):
            project_position_v1(position_id="position-2", venue_ref="venue", market_ref="market", contract_ref="contract", outcome_or_side="YES", events=())
    elif slug == "reconciliation":
        run = ReconciliationRunV1("run-1", ("projection",), "injected-snapshot", NOW, ("break",), ReconciliationStateV1.MATERIAL_BREAK, True)
        assert run.blocks_new_exposure
        with pytest.raises(ComputationControlPlaneError):
            ReconciliationRunV1("run-2", ("projection",), "snapshot", NOW, ("break",), ReconciliationStateV1.UNKNOWN, False)
    elif slug == "rounding-and-quantization":
        policy = QuantizationPolicyV1("cent", "amount", ".01", QuantizationRoundingV1.HALF_EVEN, "USD", "USD", "SETTLED", 2, "OWNER")
        receipt = quantize_decimal_v1("1.005", policy=policy, receipt_id="rounding-1")
        assert (receipt.pre_value, receipt.post_value, receipt.residual) == (Decimal("1.005"), Decimal("1.00"), Decimal("0.005"))
        with pytest.raises(ComputationControlPlaneError):
            quantize_decimal_v1(1.005, policy=policy, receipt_id="bad")
    elif slug == "settlement-resolution":
        assert CashStateClassV1.PENDING_CASH.value != CashStateClassV1.REALIZED_SETTLEMENT_NET_CASH.value
        assert CashStateClassV1.REALIZED_SETTLEMENT_NET_CASH.value != CashStateClassV1.SETTLED_SPENDABLE_CASH.value
        pending = CashStateProjectionV1("pending", CashStateClassV1.PENDING_CASH, "10.00", "USD", "CONTESTED", ("settlement-fixture",), ("journal",), NOW, NOW, ReconciliationStateV1.UNKNOWN)
        assert pending.reconciliation_state is ReconciliationStateV1.UNKNOWN and pending.cash_class is CashStateClassV1.PENDING_CASH
    elif slug == "tca-decomposition":
        attribution = tuple((name, CostEmbeddingV1.EXPLICIT) for name in ("spread_cost", "slippage_cost", "impact_cost", "fees", "rebates", "latency_cost", "adverse_selection_cost", "opportunity_cost", "other_declared_costs"))
        tca = TCADecompositionV1("tca-1", "decision", ("fill",), "1", "0", "0", "1", "-.25", "0", "0", "0", "0", "1.75", attribution)
        assert tca.total_cost == Decimal("1.75")
        with pytest.raises(ComputationControlPlaneError):
            TCADecompositionV1("bad", "decision", ("fill",), "1", "0", "0", "1", "-.25", "0", "0", "0", "0", "2", attribution)
    elif slug == "unit-and-basis":
        touches = binary_book_implied_asks_v1(
            snapshot=BinaryBookSnapshotV1(
                "book", "sequence", "source", "USD", "PAYOUT",
                ("0.40", "0.42"), ("0.50", "0.56"), "1", 5, 5,
                "CURRENT_CONTIGUOUS_SNAPSHOT_PLUS_DELTAS",
                (ActivePriceGridRangeV1("0.00", "1.00", "0.01"),),
            )
        )
        assert (touches.yes_implied_ask, touches.no_implied_ask) == (Decimal("0.44"), Decimal("0.58"))
        journal, postings = _journal()
        with pytest.raises(ComputationControlPlaneError):
            AccountingAndTCAServiceV1.validate_journal(journal, postings, _accounts(second_basis="PROJECTED"))
    else:  # pragma: no cover - the meta-test makes this unreachable
        raise AssertionError(f"unhandled control case {slug}")


def _atomic_records(*, credit: str = "1.00", claim_id: str = "claim-1", claim_key: str = "key-1", no_fill: bool = False):
    if no_fill:
        event = EconomicEventRecordV1("event-no-fill", "NO_FILL", "AccountingAndTCAServiceV1", "aggregate-no-fill", 1, NOW, NOW, ("fixture",), (), "FLAT", "FLAT", "DETERMINISTIC_FIXTURE")
        spine = EconomicReceiptEventSpineV1("receipt-no-fill", EconomicRecordTypeV1.ECONOMIC_EVENT, "1", "AccountingAndTCAServiceV1", "QKUComputationControlPlaneV1", "context", NOW, NOW, "cause-no-fill", "correlation-no-fill", "00-trace-no-fill", "trace-state", 1, "aggregate-no-fill", 1, "CONTRACT_ONLY", event)
        transition = StateTransitionReceiptV1("transition-no-fill", "aggregate-no-fill", "POSITION_STATE_MACHINE_V1", "FLAT", "NO_FILL", "FLAT", TransitionDispositionV1.REJECTED, "event-identity-no-fill", 0, 0, NOW, NOW, "NO_FILL", False)
        claim = IdempotencyClaimReceiptV1(claim_id, claim_key, "COMMAND", canonical_request_json_v1({"command": "no-fill"}), IdempotencyClaimStateV1.ACQUIRED, None, NOW, None, None)
        return TrancheCAtomicRecordSetV1(claim, (spine,), (event,), (), None, (), transition, "receipt-no-fill")
    journal, postings = _journal(credit=credit)
    amount = TypedEconomicAmountV1("1.00", "USD", "USD", "SETTLED", 2, "TEST::CENT")
    event = EconomicEventRecordV1("event-1", "FILL", "AccountingAndTCAServiceV1", "aggregate-1", 1, NOW, NOW, ("fixture",), (amount,), "FLAT", "OPEN", "DETERMINISTIC_FIXTURE")
    spine = EconomicReceiptEventSpineV1("receipt-1", EconomicRecordTypeV1.ECONOMIC_EVENT, "1", "AccountingAndTCAServiceV1", "QKUComputationControlPlaneV1", "context", NOW, NOW, "cause", "correlation", "00-trace", "trace-state", 1, "aggregate-1", 1, "CONTRACT_ONLY", event)
    transition = StateTransitionReceiptV1("transition-1", "aggregate-1", "POSITION_STATE_MACHINE_V1", "FLAT", "FILL", "OPEN", TransitionDispositionV1.ACCEPTED, "event-identity", 0, 1, NOW, NOW, "ACCEPTED", False)
    claim = IdempotencyClaimReceiptV1(claim_id, claim_key, "COMMAND", canonical_request_json_v1({"command": "one"}), IdempotencyClaimStateV1.ACQUIRED, None, NOW, None, None)
    lineage = ValueLineageEdgeV1(
        "lineage-1", "receipt-1", "typed_payload", "event-1", "typed_amounts[0]",
        "1.00", "1.00", "USD", "USD", "SETTLED", "SETTLED", "IDENTITY", "MATERIAL",
        NOW, NOW, "cause-lineage", "correlation-lineage", "node-receipt", "node-event",
        "IDENTITY_NO_CONVERSION",
    )
    return TrancheCAtomicRecordSetV1(claim, (spine,), (event,), (lineage,), journal, postings, transition, "receipt-1")


def _reversal_atomic_records(
    *,
    suffix: str = "atomic",
    claim_key: str = "key-reversal",
    request_token: str = "full",
    requested_amount: str | None = None,
    previously_reversed: str | None = None,
    aggregate_version: int = 2,
    original_transaction: JournalTransactionV1 | None = None,
    original_postings: tuple[JournalPostingV1, ...] | None = None,
    reversal_transaction_id: str | None = None,
    remaining_override: str | None = None,
) -> TrancheCAtomicRecordSetV1:
    if original_transaction is None or original_postings is None:
        original_transaction, original_postings = _journal()
    event_id = f"event-reversal-{suffix}"
    transaction_id = reversal_transaction_id or f"journal-reversal-{suffix}"
    requested = (
        None
        if requested_amount is None
        else {
            posting.posting_id: requested_amount
            for posting in original_postings
        }
    )
    prior = (
        {}
        if previously_reversed is None
        else {
            posting.posting_id: previously_reversed
            for posting in original_postings
        }
    )
    bundle = build_journal_reversal_v1(
        original_transaction=original_transaction,
        original_postings=original_postings,
        reversal_receipt_id=f"reversal-{suffix}",
        reversal_event_ref=event_id,
        reversal_transaction_id=transaction_id,
        reversal_posting_ids=tuple(
            f"reversal-{suffix}-{index}"
            for index in range(len(original_postings))
        ),
        requested_amount_by_original_posting=requested,
        previously_reversed_by_original_posting=prior,
        reason_code="CORRECTION",
        authority_ref="OWNER_FIXTURE",
        effective_at=NOW,
        recorded_at=NOW,
    )
    reversal_receipt = bundle.receipt
    if remaining_override is not None:
        reversal_receipt = replace(
            reversal_receipt,
            remaining_reversible_amounts=tuple(
                AccountingAmountV1(
                    remaining_override,
                    posting.currency_or_asset,
                    posting.ledger_unit,
                    posting.basis,
                    posting.scale,
                    "IDENTITY_FROM_ORIGINAL_POSTING",
                )
                for posting in original_postings
            ),
        )
    amount = TypedEconomicAmountV1("1.00", "USD", "USD", "SETTLED", 2, "TEST::CENT")
    event = EconomicEventRecordV1(event_id, "CORRECTION", "AccountingAndTCAServiceV1", "aggregate-1", aggregate_version, NOW, NOW, (original_transaction.journal_transaction_id,), (amount,), "OPEN", "OPEN", "DETERMINISTIC_FIXTURE")
    spine = EconomicReceiptEventSpineV1(f"receipt-reversal-{suffix}", EconomicRecordTypeV1.ECONOMIC_EVENT, "1", "AccountingAndTCAServiceV1", "QKUComputationControlPlaneV1", "context", NOW, NOW, f"cause-reversal-{suffix}", f"correlation-reversal-{suffix}", f"00-trace-reversal-{suffix}", "trace-state", aggregate_version, "aggregate-1", aggregate_version, "CONTRACT_ONLY", event)
    transition = StateTransitionReceiptV1(f"transition-reversal-{suffix}", "aggregate-1", "POSITION_STATE_MACHINE_V1", "OPEN", "CORRECTION", "OPEN", TransitionDispositionV1.ACCEPTED, f"event-identity-reversal-{suffix}", aggregate_version - 1, aggregate_version, NOW, NOW, "CORRECTION", False)
    claim = IdempotencyClaimReceiptV1(f"claim-reversal-{suffix}", claim_key, "REVERSAL", canonical_request_json_v1({"command": "reverse", "original": original_transaction.journal_transaction_id, "request": request_token}), IdempotencyClaimStateV1.ACQUIRED, None, NOW, None, None)
    return TrancheCAtomicRecordSetV1(
        claim, (spine,), (event,), (), bundle.transaction, bundle.postings,
        transition, f"receipt-reversal-{suffix}", reversal_links=(reversal_receipt,),
    )


@pytest.mark.parametrize("adapter_kind", ("memory", "sqlite"))
def test_reference_adapter_atomic_commit_rollback_and_replay(adapter_kind, reference_directory) -> None:
    adapter = (
        InMemoryPersistenceAdapterV1()
        if adapter_kind == "memory"
        else SQLiteReferenceAdapterV1(reference_directory / "reference.db", busy_timeout_ms=0, max_transaction_attempts=1)
    )
    unit = TrancheCUnitOfWorkV1(adapter, TransactionRetryPolicyV1(1))
    committed = unit.execute(unit_of_work_id="uow-1", records=_atomic_records(), accounts=_accounts(), started_at=NOW, completed_at=NOW)
    original_before_reversal = deterministic_json(adapter.get_record("journal-1"))
    reversed_receipt = unit.execute(unit_of_work_id="uow-reversal", records=_reversal_atomic_records(), accounts=_accounts(), started_at=NOW, completed_at=NOW)
    replayed = unit.execute(unit_of_work_id="uow-2", records=_atomic_records(), accounts=_accounts(), started_at=NOW, completed_at=NOW)
    duplicate_delivery = unit.execute(unit_of_work_id="uow-3", records=_atomic_records(claim_id="claim-2", claim_key="key-2"), accounts=_accounts(), started_at=NOW, completed_at=NOW)
    no_fill = unit.execute(unit_of_work_id="uow-no-fill", records=_atomic_records(claim_id="claim-no-fill", claim_key="key-no-fill", no_fill=True), accounts={}, started_at=NOW, completed_at=NOW)
    assert committed.transaction_state is TransactionTerminalStateV1.COMMITTED
    assert reversed_receipt.transaction_state is TransactionTerminalStateV1.COMMITTED
    assert replayed.transaction_state is TransactionTerminalStateV1.COMMITTED
    assert duplicate_delivery.transaction_state is TransactionTerminalStateV1.COMMITTED
    assert no_fill.transaction_state is TransactionTerminalStateV1.COMMITTED
    assert replayed.committed_record_refs == ("receipt-1",)
    assert adapter.get_idempotency_result("key-1") == "receipt-1"
    assert adapter.get_idempotency_result("key-2") == "receipt-1"
    assert adapter.get_idempotency_result("key-no-fill") == "receipt-no-fill"
    assert deterministic_json(adapter.get_record("journal-1")) == original_before_reversal
    assert adapter.get_record("reversal-atomic") is not None
    assert len(adapter.reconstruct_as_of(effective_cutoff=NOW, recorded_cutoff=NOW, aggregate_scope=())) == 17
    assert len(adapter.reconstruct_as_of(effective_cutoff=NOW, recorded_cutoff=NOW, aggregate_scope=("aggregate-1",))) == 6
    assert deterministic_json(adapter.get_record("receipt-1")) == deterministic_json(_atomic_records().receipt_records[0])
    with pytest.raises(ComputationControlPlaneError):
        replace(
            _atomic_records(claim_id="claim-circular", claim_key="key-circular"),
            optional_outbox_intent=OutboxIntentRecordV1(
                "outbox-circular", "NO_WRITE", "aggregate-1", "outbox-circular", NOW
            ),
        )
    if hasattr(adapter, "close"):
        adapter.close()

    if adapter_kind == "sqlite":
        contention_path = reference_directory / "contention.db"
        holder = SQLiteReferenceAdapterV1(contention_path, busy_timeout_ms=0, max_transaction_attempts=1)
        contender = SQLiteReferenceAdapterV1(contention_path, busy_timeout_ms=0, max_transaction_attempts=1)
        holder_transaction = holder.begin_transaction()
        holder.acquire_idempotency_claim(
            holder_transaction,
            _atomic_records(claim_id="claim-holder", claim_key="key-contention").idempotency_claim,
        )
        contention = TrancheCUnitOfWorkV1(contender, TransactionRetryPolicyV1(1)).execute(
            unit_of_work_id="uow-contention",
            records=_atomic_records(claim_id="claim-contender", claim_key="key-contention"),
            accounts=_accounts(),
            started_at=NOW,
            completed_at=NOW,
        )
        assert contention.transaction_state is TransactionTerminalStateV1.RETRY_EXHAUSTED
        assert contender.get_idempotency_result("key-contention") is None
        holder_transaction.rollback()
        holder.close()
        contender.close()

    rollback_adapter = (
        InMemoryPersistenceAdapterV1()
        if adapter_kind == "memory"
        else SQLiteReferenceAdapterV1(reference_directory / "rollback.db", busy_timeout_ms=0, max_transaction_attempts=1)
    )
    rolled_back = TrancheCUnitOfWorkV1(rollback_adapter, TransactionRetryPolicyV1(1)).execute(
        unit_of_work_id="uow-bad", records=_atomic_records(credit="0.99"), accounts=_accounts(), started_at=NOW, completed_at=NOW
    )
    assert rolled_back.transaction_state is TransactionTerminalStateV1.ROLLED_BACK
    assert rollback_adapter.get_record("receipt-1") is None
    assert rollback_adapter.get_idempotency_result("key-1") is None
    if hasattr(rollback_adapter, "close"):
        rollback_adapter.close()


REVERSAL_HISTORY_SCENARIOS = (
    "full-then-full",
    "partial-then-remainder",
    "partial-then-over",
    "same-key-replay",
    "same-key-conflict",
    "same-uow-original",
    "receipt-remaining-mismatch",
    "journal-link-bijection",
)


@pytest.mark.parametrize("adapter_kind", ("memory", "sqlite"))
@pytest.mark.parametrize("scenario", REVERSAL_HISTORY_SCENARIOS)
def test_persisted_reversal_history_matrix(
    adapter_kind, scenario, reference_directory
) -> None:
    adapter = (
        InMemoryPersistenceAdapterV1()
        if adapter_kind == "memory"
        else SQLiteReferenceAdapterV1(
            reference_directory / f"reversal-{scenario}.db",
            busy_timeout_ms=0,
            max_transaction_attempts=1,
        )
    )
    unit = TrancheCUnitOfWorkV1(adapter, TransactionRetryPolicyV1(1))
    if scenario == "same-uow-original":
        original, original_postings = _journal()
        before = deterministic_json(
            adapter.reconstruct_as_of(
                effective_cutoff=NOW,
                recorded_cutoff=NOW,
                aggregate_scope=(),
            )
        )
        result = unit.execute(
            unit_of_work_id="uow-same-uow",
            records=_reversal_atomic_records(
                suffix="same-uow",
                original_transaction=original,
                original_postings=original_postings,
                reversal_transaction_id=original.journal_transaction_id,
            ),
            accounts=_accounts(),
            started_at=NOW,
            completed_at=NOW,
        )
        assert result.transaction_state is TransactionTerminalStateV1.ROLLED_BACK
        assert result.failure_code == ReasonCode.REVERSAL_INVALID.value
        assert deterministic_json(
            adapter.reconstruct_as_of(
                effective_cutoff=NOW,
                recorded_cutoff=NOW,
                aggregate_scope=(),
            )
        ) == before
        assert adapter.get_record("journal-1") is None
        if hasattr(adapter, "close"):
            adapter.close()
        return

    original_result = unit.execute(
        unit_of_work_id=f"uow-original-{scenario}",
        records=_atomic_records(),
        accounts=_accounts(),
        started_at=NOW,
        completed_at=NOW,
    )
    assert original_result.transaction_state is TransactionTerminalStateV1.COMMITTED

    if scenario == "journal-link-bijection":
        valid = _reversal_atomic_records(suffix="bijection")
        assert valid.journal_transaction is not None
        link = valid.reversal_links[0]
        before = deterministic_json(
            adapter.reconstruct_as_of(
                effective_cutoff=NOW,
                recorded_cutoff=NOW,
                aggregate_scope=(),
            )
        )
        mutations = (
            {"reversal_links": ()},
            {
                "journal_transaction": replace(
                    valid.journal_transaction,
                    reversal_of_transaction_id=None,
                )
            },
            {
                "reversal_links": (
                    replace(
                        link,
                        original_event_or_transaction_ref="journal-other",
                    ),
                )
            },
            {
                "reversal_links": (
                    replace(link, reversal_event_ref="event-other"),
                )
            },
        )
        for mutation in mutations:
            with pytest.raises(ComputationControlPlaneError):
                replace(valid, **mutation)
            assert deterministic_json(
                adapter.reconstruct_as_of(
                    effective_cutoff=NOW,
                    recorded_cutoff=NOW,
                    aggregate_scope=(),
                )
            ) == before
            assert (
                adapter.get_idempotency_result(
                    valid.idempotency_claim.idempotency_key
                )
                is None
            )
        unwritten_refs = (
            *(record.record_id for record in valid.receipt_records),
            *(event.economic_event_id for event in valid.economic_events),
            valid.journal_transaction.journal_transaction_id,
            *(posting.posting_id for posting in valid.journal_postings),
            valid.state_transition.transition_id,
            link.reversal_receipt_id,
        )
        assert all(adapter.get_record(ref) is None for ref in unwritten_refs)
        if hasattr(adapter, "close"):
            adapter.close()
        return

    if scenario == "receipt-remaining-mismatch":
        first_result = None
        proposed = _reversal_atomic_records(
            suffix="bad-remaining",
            remaining_override="0.01",
        )
    else:
        first_full = scenario == "full-then-full"
        first_records = _reversal_atomic_records(
            suffix="a",
            claim_key="key-reversal-a",
            request_token="full-a" if first_full else "partial-a",
            requested_amount=None if first_full else "0.40",
        )
        first_result = unit.execute(
            unit_of_work_id=f"uow-first-{scenario}",
            records=first_records,
            accounts=_accounts(),
            started_at=NOW,
            completed_at=NOW,
        )
        assert first_result.transaction_state is TransactionTerminalStateV1.COMMITTED
        if scenario == "full-then-full":
            proposed = _reversal_atomic_records(
                suffix="b", request_token="full-b", aggregate_version=3
            )
        elif scenario == "partial-then-remainder":
            proposed = _reversal_atomic_records(
                suffix="b",
                request_token="remainder-b",
                requested_amount="0.60",
                previously_reversed="0.40",
                aggregate_version=3,
            )
        elif scenario == "partial-then-over":
            proposed = _reversal_atomic_records(
                suffix="b",
                request_token="over-b",
                requested_amount="0.70",
                aggregate_version=3,
            )
        elif scenario == "same-key-replay":
            proposed = _reversal_atomic_records(
                suffix="b",
                claim_key="key-reversal-a",
                request_token="partial-a",
                requested_amount="0.40",
                aggregate_version=3,
            )
        else:
            proposed = _reversal_atomic_records(
                suffix="b",
                claim_key="key-reversal-a",
                request_token="conflicting-payload",
                requested_amount="0.40",
                aggregate_version=3,
            )

    before_second = deterministic_json(
        adapter.reconstruct_as_of(
            effective_cutoff=NOW,
            recorded_cutoff=NOW,
            aggregate_scope=(),
        )
    )
    second_result = unit.execute(
        unit_of_work_id=f"uow-second-{scenario}",
        records=proposed,
        accounts=_accounts(),
        started_at=NOW,
        completed_at=NOW,
    )
    if scenario == "partial-then-remainder":
        assert second_result.transaction_state is TransactionTerminalStateV1.COMMITTED
    elif scenario == "same-key-replay":
        assert second_result.transaction_state is TransactionTerminalStateV1.COMMITTED
        assert first_result is not None
        assert second_result.committed_record_refs == first_result.committed_record_refs[:1]
        assert deterministic_json(
            adapter.reconstruct_as_of(
                effective_cutoff=NOW,
                recorded_cutoff=NOW,
                aggregate_scope=(),
            )
        ) == before_second
    elif scenario == "same-key-conflict":
        assert second_result.transaction_state is TransactionTerminalStateV1.CONFLICT
        assert second_result.failure_code == ReasonCode.IDEMPOTENCY_CONFLICT.value
    else:
        assert second_result.transaction_state is TransactionTerminalStateV1.ROLLED_BACK
        assert second_result.failure_code == ReasonCode.REVERSAL_INVALID.value

    if scenario not in {"partial-then-remainder", "same-key-replay"}:
        assert deterministic_json(
            adapter.reconstruct_as_of(
                effective_cutoff=NOW,
                recorded_cutoff=NOW,
                aggregate_scope=(),
            )
        ) == before_second
        assert adapter.get_record(proposed.reversal_links[0].reversal_receipt_id) is None
        assert adapter.get_record(proposed.journal_transaction.journal_transaction_id) is None
        assert all(
            adapter.get_record(posting.posting_id) is None
            for posting in proposed.journal_postings
        )

    history_transaction = adapter.begin_transaction()
    history = adapter.load_committed_reversal_history(
        history_transaction, "journal-1"
    )
    history_transaction.rollback()
    assert all(
        row.cumulative_reversed_amount.decimal
        + row.remaining_reversible_amount.decimal
        == row.original_posting.magnitude
        for row in history.posting_history
    )
    if scenario in {"full-then-full", "partial-then-remainder"}:
        assert all(
            row.remaining_reversible_amount.decimal == 0
            for row in history.posting_history
        )
    if hasattr(adapter, "close"):
        adapter.close()


def _binary_book_snapshot(**changes) -> BinaryBookSnapshotV1:
    values = {
        "snapshot_ref": "book-snapshot",
        "sequence_ref": "sequence-5",
        "source_binding_ref": "source-binding",
        "unit": "USD",
        "basis": "PAYOUT",
        "yes_bids": ("0.40", "0.42"),
        "no_bids": ("0.50", "0.56"),
        "payout": "1.00",
        "book_sequence": 5,
        "expected_sequence": 5,
        "book_state": "CURRENT_CONTIGUOUS_SNAPSHOT_PLUS_DELTAS",
        "active_price_grid_ranges": (
            ActivePriceGridRangeV1("0.00", "1.00", "0.01"),
        ),
    }
    values.update(changes)
    return BinaryBookSnapshotV1(**values)


def test_math_36_canonical_snapshot_and_compatibility_matrix(monkeypatch) -> None:
    assert TRANCHE_C_MATH_SPECIFICATIONS["MATH-36"].implementation is binary_book_implied_asks_v1
    assert TRANCHE_C_IMPLEMENTATION_REGISTRY["MATH-36"].callable is binary_book_implied_asks_v1
    assert IMPLEMENTATION_REGISTRY["MATH-36"].callable is compute_math_36_kalshi_binary_book_transform

    snapshot = _binary_book_snapshot()
    canonical = binary_book_implied_asks_v1(snapshot=snapshot)
    calls: list[BinaryBookSnapshotV1] = []

    def _canonical_spy(*, snapshot):
        calls.append(snapshot)
        return binary_book_implied_asks_v1(snapshot=snapshot)

    monkeypatch.setattr(
        implementation_registry_module,
        "binary_book_implied_asks_v1",
        _canonical_spy,
    )
    compatibility = compute_math_36_kalshi_binary_book_transform(
        snapshot.yes_bids,
        snapshot.no_bids,
        snapshot.payout,
        snapshot.book_sequence,
        snapshot.expected_sequence,
        snapshot.book_state,
        ({"minimum": "0.00", "maximum": "1.00", "step": "0.01"},),
    )
    assert len(calls) == 1
    assert compatibility == {
        "best_yes_bid": Decimal("0.42"),
        "best_no_bid": Decimal("0.56"),
        "derived_yes_ask": canonical.yes_implied_ask,
        "derived_no_ask": canonical.no_implied_ask,
        "book_sequence": canonical.book_sequence,
    }
    assert (
        canonical.snapshot_ref,
        canonical.sequence_ref,
        canonical.source_binding_ref,
        canonical.book_sequence,
    ) == (
        snapshot.snapshot_ref,
        snapshot.sequence_ref,
        snapshot.source_binding_ref,
        snapshot.book_sequence,
    )
    mutations = (
        {"expected_sequence": 4},
        {"book_state": "NONCONTIGUOUS"},
        {"yes_bids": ("0.405", "0.42")},
        {"payout": "1.005"},
    )
    for mutation in mutations:
        with pytest.raises(ComputationControlPlaneError):
            _binary_book_snapshot(**mutation)


def _parameter_evidence(
    parameter_id: str,
    evidence_class: TrancheCParameterEvidenceClassV1,
    *,
    evidence_ref: str | None = None,
    **changes,
) -> TrancheCParameterEvidenceV1:
    policy = TRANCHE_C_PARAMETER_POLICIES[parameter_id]
    binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS[parameter_id]
    values = {
        "evidence_class": evidence_class,
        "evidence_ref": evidence_ref or f"evidence::{parameter_id}",
        "family_evidence_binding_ref": str(
            policy.raw["family_evidence_binding_ref"]
        ),
        "value_source_class": str(policy.raw["effective_value_source_class"]),
        "source_or_binding_refs": tuple(
            policy.raw["effective_source_state_refs"]
        ),
        "source_currentization_refs": tuple(
            policy.raw["source_currentization_refs"]
        ),
        "active_scope_ref": str(policy.raw["master_plan_section_id"]),
        "source_epoch_ref": str(policy.raw["currentization_version"]),
        "canonical_owner_ref": policy.canonical_owner,
        "authority_ref": binding.active_stage1_value_authority,
        "declared_unit_or_basis": str(policy.raw["effective_unit_or_basis"]),
        "observed_at": DYNAMIC_OBSERVED_AT,
        "evaluated_at": DYNAMIC_EVALUATED_AT,
        "valid_until": DYNAMIC_VALID_UNTIL,
        "constraint_refs": (
            policy.reference_range_or_constraint,
            str(policy.raw["effective_bounded_search_space_or_fit_constraint"]),
            str(policy.raw["effective_unit_or_basis"]),
        ),
    }
    values.update(changes)
    return TrancheCParameterEvidenceV1(**values)


def _drawdown_calibration_artifact(
    **changes,
) -> TrancheCDrawdownCalibrationArtifactV1:
    policy = TRANCHE_C_PARAMETER_POLICIES["ST10-PARAM::1531"]
    binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS["ST10-PARAM::1531"]
    values = {
        "calibration_bundle_ref": "calibration::drawdown-ra-11b",
        "approved_sleeve_max_drawdown_budget": Decimal("0.10"),
        "warning_threshold": Decimal("0.05"),
        "freeze_threshold": Decimal("0.10"),
        "canonical_owner_ref": policy.canonical_owner,
        "authority_ref": binding.active_stage1_value_authority,
        "active_scope_ref": str(policy.raw["master_plan_section_id"]),
        "source_epoch_ref": str(policy.raw["currentization_version"]),
        "observed_at": DYNAMIC_OBSERVED_AT,
        "evaluated_at": DYNAMIC_EVALUATED_AT,
        "valid_until": DYNAMIC_VALID_UNTIL,
    }
    values.update(changes)
    return TrancheCDrawdownCalibrationArtifactV1(**values)


PARAMETER_ADMISSIBILITY_CASES = (
    "fixed-pass",
    "fixed-alternate",
    "singleton-pass",
    "singleton-alternate",
    "bounded-pass",
    "bounded-outside",
    "bounded-wrong-type",
    "bounded-wrong-unit",
    "source-pass",
    "source-missing-evidence",
    "calibration-pass",
    "calibration-missing-evidence",
    "unsupported-structural-constraint",
)


@pytest.mark.parametrize("case", PARAMETER_ADMISSIBILITY_CASES)
def test_parameter_admissibility_matrix(case) -> None:
    fixed_id = "ST10-PARAM::0115"
    singleton_id = "ST10-PARAM::1544"
    bounded_id = "ST10-PARAM::0064"
    source_id = "ST10-PARAM::3277"
    calibration_id = "ST10-PARAM::1531"
    structural_id = "ST10-PARAM::3797"
    parameter_id = {
        "fixed-pass": fixed_id,
        "fixed-alternate": fixed_id,
        "singleton-pass": singleton_id,
        "singleton-alternate": singleton_id,
        "bounded-pass": bounded_id,
        "bounded-outside": bounded_id,
        "bounded-wrong-type": bounded_id,
        "bounded-wrong-unit": bounded_id,
        "source-pass": source_id,
        "source-missing-evidence": source_id,
        "calibration-pass": calibration_id,
        "calibration-missing-evidence": calibration_id,
        "unsupported-structural-constraint": structural_id,
    }[case]
    policy = TRANCHE_C_PARAMETER_POLICIES[parameter_id]
    binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS[parameter_id]
    value: object = policy.day1_seed_or_resolution_rule
    unit: str | None = None
    evidence: TrancheCParameterEvidenceV1 | None = None
    calibration_artifact: TrancheCDrawdownCalibrationArtifactV1 | None = None
    expected_pass = case.endswith("pass")
    if case == "fixed-alternate":
        value = "ALLOWED"
    elif case == "singleton-pass":
        value, unit = Decimal("1.0"), "gross leverage cap"
    elif case == "singleton-alternate":
        value, unit = Decimal("1.1"), "gross leverage cap"
    elif case == "bounded-pass":
        value, unit = Decimal("0.00"), "USD"
    elif case == "bounded-outside":
        value, unit = Decimal("-0.01"), "USD"
    elif case == "bounded-wrong-type":
        value, unit = "0.00", "USD"
    elif case == "bounded-wrong-unit":
        value, unit = Decimal("0.00"), "EUR"
    elif case.startswith("source"):
        unit = str(policy.raw["effective_unit_or_basis"])
        if case == "source-pass":
            evidence = _parameter_evidence(
                parameter_id,
                TrancheCParameterEvidenceClassV1.SOURCE_OR_RUNTIME_BINDING,
            )
    elif case.startswith("calibration"):
        value = Decimal("0.05")
        unit = str(policy.raw["effective_unit_or_basis"])
        if case == "calibration-pass":
            calibration_artifact = _drawdown_calibration_artifact()
            evidence = _parameter_evidence(
                parameter_id,
                TrancheCParameterEvidenceClassV1.CALIBRATED_ARTIFACT,
                evidence_ref=calibration_artifact.calibration_bundle_ref,
            )
    elif case == "unsupported-structural-constraint":
        value = {"id_": "EXACT_CONTRACT_OR_PACKET_IDENTITY"}

    explicit = TrancheCExplicitParameterValueV1(
        parameter_id=parameter_id,
        value=value,
        canonical_owner=policy.canonical_owner,
        authority_ref=binding.active_stage1_value_authority,
        source_packet_ref=(
            evidence.evidence_ref
            if evidence is not None
            else f"packet::{case}"
        ),
        declared_unit_or_basis=unit,
        evidence=evidence,
        drawdown_calibration_artifact=calibration_artifact,
    )
    resolution_at = (
        DYNAMIC_RESOLUTION_AT
        if TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES[parameter_id]
        in {
            TrancheCParameterPolicyClassV1.SOURCE_OR_RUNTIME_BOUND,
            TrancheCParameterPolicyClassV1.CALIBRATION_REQUIRED,
        }
        else None
    )
    if not expected_pass:
        with pytest.raises(ComputationControlPlaneError):
            resolve_tranche_c_parameter_v1(
                parameter_id,
                explicit_value=explicit,
                resolution_at=resolution_at,
            )
        return
    resolved = resolve_tranche_c_parameter_v1(
        parameter_id,
        explicit_value=explicit,
        resolution_at=resolution_at,
    )
    assert resolved.admissibility_receipt.terminal_state == "PASS"
    assert (
        resolved.value_or_rule
        == resolved.admissibility_receipt.canonical_normalized_value
    )
    assert resolved.admissibility_receipt.policy_class is TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES[parameter_id]


def test_dynamic_parameter_evidence_compound_matrix() -> None:
    source_ids = tuple(
        parameter_id
        for parameter_id, policy_class in
        TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES.items()
        if policy_class
        is TrancheCParameterPolicyClassV1.SOURCE_OR_RUNTIME_BOUND
    )
    assert len(source_ids) == 2
    for parameter_id in source_ids:
        policy = TRANCHE_C_PARAMETER_POLICIES[parameter_id]
        binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS[parameter_id]
        evidence = _parameter_evidence(
            parameter_id,
            TrancheCParameterEvidenceClassV1.SOURCE_OR_RUNTIME_BINDING,
        )
        explicit = TrancheCExplicitParameterValueV1(
            parameter_id=parameter_id,
            value=policy.day1_seed_or_resolution_rule,
            canonical_owner=policy.canonical_owner,
            authority_ref=binding.active_stage1_value_authority,
            source_packet_ref=evidence.evidence_ref,
            declared_unit_or_basis=str(policy.raw["effective_unit_or_basis"]),
            evidence=evidence,
        )
        resolved = resolve_tranche_c_parameter_v1(
            parameter_id,
            explicit_value=explicit,
            resolution_at=DYNAMIC_RESOLUTION_AT,
        )
        receipt = resolved.admissibility_receipt
        assert (
            receipt.active_scope_ref,
            receipt.source_epoch_ref,
            receipt.family_evidence_binding_ref,
            receipt.value_source_class,
            receipt.resolution_at,
        ) == (
            evidence.active_scope_ref,
            evidence.source_epoch_ref,
            evidence.family_evidence_binding_ref,
            evidence.value_source_class,
            DYNAMIC_RESOLUTION_AT,
        )
        with pytest.raises(ComputationControlPlaneError):
            resolve_tranche_c_parameter_v1(
                parameter_id,
                explicit_value=explicit,
            )
        future_observed = datetime(2026, 1, 1, 0, 3, tzinfo=UTC)
        evidence_mutations = (
            {"valid_until": DYNAMIC_RESOLUTION_AT},
            {
                "observed_at": future_observed,
                "evaluated_at": future_observed,
            },
            {"active_scope_ref": "WRONG_SCOPE"},
            {"source_epoch_ref": "WRONG_EPOCH"},
            {"value_source_class": "WRONG_VALUE_SOURCE"},
            {"family_evidence_binding_ref": "WRONG_FAMILY_BINDING"},
            {"source_or_binding_refs": ("WRONG_SOURCE_STATE",)},
            {"source_currentization_refs": ("WRONG_CURRENTIZATION",)},
            {"authority_ref": "WRONG_AUTHORITY"},
            {"canonical_owner_ref": "WRONG_OWNER"},
            {"declared_unit_or_basis": "WRONG_UNIT"},
        )
        for mutation in evidence_mutations:
            bad_evidence = replace(evidence, **mutation)
            with pytest.raises(ComputationControlPlaneError):
                resolve_tranche_c_parameter_v1(
                    parameter_id,
                    explicit_value=replace(explicit, evidence=bad_evidence),
                    resolution_at=DYNAMIC_RESOLUTION_AT,
                )
        with pytest.raises(ComputationControlPlaneError):
            resolve_tranche_c_parameter_v1(
                parameter_id,
                explicit_value=replace(explicit, value="AMBIGUOUS_TOKEN"),
                resolution_at=DYNAMIC_RESOLUTION_AT,
            )
        with pytest.raises(ComputationControlPlaneError):
            resolve_tranche_c_parameter_v1(
                parameter_id,
                explicit_value=replace(
                    explicit,
                    authority_ref="WRONG_AUTHORITY",
                    declared_unit_or_basis="WRONG_UNIT",
                ),
                resolution_at=DYNAMIC_RESOLUTION_AT,
            )

    drawdown_bundle = _drawdown_calibration_artifact()
    drawdown_resolutions = {}
    for parameter_id, value in (
        ("ST10-PARAM::1531", drawdown_bundle.warning_threshold),
        ("ST10-PARAM::1532", drawdown_bundle.freeze_threshold),
    ):
        policy = TRANCHE_C_PARAMETER_POLICIES[parameter_id]
        binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS[parameter_id]
        evidence = _parameter_evidence(
            parameter_id,
            TrancheCParameterEvidenceClassV1.CALIBRATED_ARTIFACT,
            evidence_ref=drawdown_bundle.calibration_bundle_ref,
        )
        explicit = TrancheCExplicitParameterValueV1(
            parameter_id=parameter_id,
            value=value,
            canonical_owner=policy.canonical_owner,
            authority_ref=binding.active_stage1_value_authority,
            source_packet_ref=evidence.evidence_ref,
            declared_unit_or_basis=str(policy.raw["effective_unit_or_basis"]),
            evidence=evidence,
            drawdown_calibration_artifact=drawdown_bundle,
        )
        drawdown_resolutions[parameter_id] = resolve_tranche_c_parameter_v1(
            parameter_id,
            explicit_value=explicit,
            resolution_at=DYNAMIC_RESOLUTION_AT,
        )
    assert drawdown_resolutions["ST10-PARAM::1531"].value_or_rule == Decimal("0.05")
    assert drawdown_resolutions["ST10-PARAM::1532"].value_or_rule == Decimal("0.10")
    assert {
        resolution.admissibility_receipt.calibration_bundle_ref
        for resolution in drawdown_resolutions.values()
    } == {drawdown_bundle.calibration_bundle_ref}

    warning_policy = TRANCHE_C_PARAMETER_POLICIES["ST10-PARAM::1531"]
    warning_binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS["ST10-PARAM::1531"]
    warning_evidence = _parameter_evidence(
        "ST10-PARAM::1531",
        TrancheCParameterEvidenceClassV1.CALIBRATED_ARTIFACT,
        evidence_ref=drawdown_bundle.calibration_bundle_ref,
    )
    warning_explicit = TrancheCExplicitParameterValueV1(
        parameter_id="ST10-PARAM::1531",
        value=drawdown_bundle.warning_threshold,
        canonical_owner=warning_policy.canonical_owner,
        authority_ref=warning_binding.active_stage1_value_authority,
        source_packet_ref=warning_evidence.evidence_ref,
        declared_unit_or_basis=str(
            warning_policy.raw["effective_unit_or_basis"]
        ),
        evidence=warning_evidence,
        drawdown_calibration_artifact=drawdown_bundle,
    )
    with pytest.raises(ComputationControlPlaneError):
        resolve_tranche_c_parameter_v1(
            "ST10-PARAM::1531",
            explicit_value=replace(
                warning_explicit,
                drawdown_calibration_artifact=None,
            ),
            resolution_at=DYNAMIC_RESOLUTION_AT,
        )
    artifact_mutations = (
        {"approved_sleeve_max_drawdown_budget": None},
        {"approved_sleeve_max_drawdown_budget": 0.1},
        {"approved_sleeve_max_drawdown_budget": Decimal("NaN")},
        {"freeze_threshold": Decimal("Infinity")},
        {"warning_threshold": Decimal("0.04")},
        {"freeze_threshold": Decimal("0.09")},
        {
            "warning_threshold": Decimal("0.10"),
            "freeze_threshold": Decimal("0.10"),
        },
        {"active_scope_ref": "WRONG_SCOPE"},
        {"source_epoch_ref": "WRONG_EPOCH"},
        {"canonical_owner_ref": "WRONG_OWNER"},
        {"authority_ref": "WRONG_AUTHORITY"},
        {"valid_until": DYNAMIC_RESOLUTION_AT},
        {"calibration_bundle_ref": "calibration::mixed-bundle"},
    )
    for mutation in artifact_mutations:
        with pytest.raises(ComputationControlPlaneError):
            mutated_bundle = _drawdown_calibration_artifact(**mutation)
            resolve_tranche_c_parameter_v1(
                "ST10-PARAM::1531",
                explicit_value=replace(
                    warning_explicit,
                    drawdown_calibration_artifact=mutated_bundle,
                ),
                resolution_at=DYNAMIC_RESOLUTION_AT,
            )


def test_control_coverage_meta_matrix() -> None:
    validate_st12c_control_coverage_matrix()
    rows = ST12C_CONTROL_COVERAGE_MATRIX
    assert len(rows) == 25
    assert sum(row.domain == "accounting" for row in rows) == 16
    assert sum(row.domain == "execution" for row in rows) == 9
    assert len(ST12C_ORIGINAL_TEST_TO_MATRIX_LOCATOR) == 25
    assert {math_id for row in rows for math_id in row.math_oracle_vector_links} == {f"MATH-{number}" for number in range(26, 39)}
    root = Path(__file__).resolve().parents[1]
    assert tuple(path.name for path in (root / "accounting").glob("test_*.py")) == ("test_contract_matrix.py",)
    assert tuple(path.name for path in (root / "execution").glob("test_*.py")) == ("test_contract_matrix.py",)
    repo_root = Path(__file__).resolve().parents[4]
    assert (repo_root / "tools" / "independent_validate_qku_computation_control_plane_accounting.py").is_file()
    assert (repo_root / "tools" / "independent_validate_qku_computation_control_plane_execution.py").is_file()
    assert len(rows) + 2 == 27
    assert len(TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES) == 80
    assert set(TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES) == set(TRANCHE_C_PARAMETER_POLICIES)
    assert set(TRANCHE_C_PARAMETER_ADMISSIBILITY_CLASSES.values()) == set(TrancheCParameterPolicyClassV1)
    source_bound = tuple(
        parameter_id
        for parameter_id, policy in TRANCHE_C_PARAMETER_POLICIES.items()
        if policy.applicability_state == "SOURCE_BOUND_MUTABLE_VALUE"
    )
    assert len(source_bound) == 2
    for parameter_id in source_bound:
        with pytest.raises(ComputationControlPlaneError):
            resolve_tranche_c_parameter_v1(parameter_id)
        policy = TRANCHE_C_PARAMETER_POLICIES[parameter_id]
        binding = TRANCHE_C_PARAMETER_APPLICATION_BINDINGS[parameter_id]
        evidence = _parameter_evidence(
            parameter_id,
            TrancheCParameterEvidenceClassV1.SOURCE_OR_RUNTIME_BINDING,
        )
        resolved = resolve_tranche_c_parameter_v1(
            parameter_id,
            explicit_value=TrancheCExplicitParameterValueV1(
                parameter_id,
                policy.day1_seed_or_resolution_rule,
                policy.canonical_owner,
                binding.active_stage1_value_authority,
                evidence.evidence_ref,
                str(policy.raw["effective_unit_or_basis"]),
                evidence,
            ),
            resolution_at=DYNAMIC_RESOLUTION_AT,
        )
        assert resolved.authority_ref == binding.active_stage1_value_authority
        assert resolved.admissibility_receipt.terminal_state == "PASS"
    dormant = next(
        parameter_id
        for parameter_id, policy in TRANCHE_C_PARAMETER_POLICIES.items()
        if policy.applicability_state == "DORMANT_FUTURE_MARKET_PRESERVED_FAIL_CLOSED"
    )
    with pytest.raises(ComputationControlPlaneError):
        resolve_tranche_c_parameter_v1(dormant)
