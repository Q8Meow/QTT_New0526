"""Centralized 16-row Tranche-C accounting contract matrix."""

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

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
    BinaryBookSnapshotV1,
    FeeScheduleBindingV1,
    FillQuantityDistributionArtifactV1,
    binary_book_implied_asks_v1,
    expected_partial_fill_quantity_v1,
    global_prediction_market_fee_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ComputationControlPlaneError,
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
    TRANCHE_C_PARAMETER_APPLICATION_BINDINGS,
    TRANCHE_C_PARAMETER_POLICIES,
    TrancheCExplicitParameterValueV1,
    resolve_tranche_c_parameter_v1,
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
        touches = binary_book_implied_asks_v1(snapshot=BinaryBookSnapshotV1("book", "sequence", "source", "USD", "PAYOUT", ("0.40", "0.42"), ("0.50", "0.56"), "1"))
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


def _reversal_atomic_records() -> TrancheCAtomicRecordSetV1:
    original, original_postings = _journal()
    bundle = build_journal_reversal_v1(
        original_transaction=original,
        original_postings=original_postings,
        reversal_receipt_id="reversal-atomic",
        reversal_event_ref="event-reversal",
        reversal_transaction_id="journal-reversal",
        reversal_posting_ids=("reversal-debit", "reversal-credit"),
        requested_amount_by_original_posting=None,
        previously_reversed_by_original_posting={},
        reason_code="CORRECTION",
        authority_ref="OWNER_FIXTURE",
        effective_at=NOW,
        recorded_at=NOW,
    )
    amount = TypedEconomicAmountV1("1.00", "USD", "USD", "SETTLED", 2, "TEST::CENT")
    event = EconomicEventRecordV1("event-reversal", "CORRECTION", "AccountingAndTCAServiceV1", "aggregate-1", 2, NOW, NOW, ("journal-1",), (amount,), "OPEN", "OPEN", "DETERMINISTIC_FIXTURE")
    spine = EconomicReceiptEventSpineV1("receipt-reversal", EconomicRecordTypeV1.ECONOMIC_EVENT, "1", "AccountingAndTCAServiceV1", "QKUComputationControlPlaneV1", "context", NOW, NOW, "cause-reversal", "correlation-reversal", "00-trace-reversal", "trace-state", 2, "aggregate-1", 2, "CONTRACT_ONLY", event)
    transition = StateTransitionReceiptV1("transition-reversal", "aggregate-1", "POSITION_STATE_MACHINE_V1", "OPEN", "CORRECTION", "OPEN", TransitionDispositionV1.ACCEPTED, "event-identity-reversal", 1, 2, NOW, NOW, "CORRECTION", False)
    claim = IdempotencyClaimReceiptV1("claim-reversal", "key-reversal", "REVERSAL", canonical_request_json_v1({"command": "reverse", "original": "journal-1"}), IdempotencyClaimStateV1.ACQUIRED, None, NOW, None, None)
    return TrancheCAtomicRecordSetV1(
        claim, (spine,), (event,), (), bundle.transaction, bundle.postings,
        transition, "receipt-reversal", reversal_links=(bundle.receipt,),
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
        resolved = resolve_tranche_c_parameter_v1(
            parameter_id,
            explicit_value=TrancheCExplicitParameterValueV1(
                parameter_id,
                policy.day1_seed_or_resolution_rule,
                policy.canonical_owner,
                binding.active_stage1_value_authority,
                f"injected-packet::{parameter_id}",
            ),
        )
        assert resolved.authority_ref == binding.active_stage1_value_authority
    dormant = next(
        parameter_id
        for parameter_id, policy in TRANCHE_C_PARAMETER_POLICIES.items()
        if policy.applicability_state == "DORMANT_FUTURE_MARKET_PRESERVED_FAIL_CLOSED"
    )
    with pytest.raises(ComputationControlPlaneError):
        resolve_tranche_c_parameter_v1(dormant)
