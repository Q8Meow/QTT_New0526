"""Pure double-entry accounting, TCA, cash, exposure, and reconciliation owner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, localcontext
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping, Sequence

from .context import decimal_context_v1, exact_decimal, parse_utc
from .errors import AccountingContractError, ContractValidationError, ReasonCode
from .serialization import deterministic_json, safe_json_loads


def _required(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{name} is required")


def _refs(value: object, name: str, *, required: bool = False) -> None:
    if not isinstance(value, tuple) or any(not isinstance(item, str) or not item for item in value):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be a string tuple")
    if required and not value:
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{name} is required")
    if len(value) != len(set(value)):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must contain unique refs")


def _canonical_decimal_text(value: str, name: str) -> Decimal:
    _required(value, name)
    result = exact_decimal(value, field_name=name)
    if str(result) != value:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be canonical Decimal text")
    return result


def _require_declared_scale(value: Decimal, scale: int, name: str) -> None:
    if isinstance(scale, bool) or not isinstance(scale, int) or scale < 0:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "scale must be nonnegative integer")
    if value.as_tuple().exponent != -scale:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{name} precision does not match its declared scale",
        )


class EntrySideV1(StrEnum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class NormalBalanceV1(StrEnum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class CashStateClassV1(StrEnum):
    MARKED_PNL = "MARKED_PNL"
    UNREALIZED_PNL = "UNREALIZED_PNL"
    PROJECTED_EXECUTABLE_NET_CASH = "PROJECTED_EXECUTABLE_NET_CASH"
    REALIZED_EXIT_NET_CASH = "REALIZED_EXIT_NET_CASH"
    REALIZED_SETTLEMENT_NET_CASH = "REALIZED_SETTLEMENT_NET_CASH"
    AVAILABLE_CASH = "AVAILABLE_CASH"
    RESERVED_CASH = "RESERVED_CASH"
    SETTLED_SPENDABLE_CASH = "SETTLED_SPENDABLE_CASH"
    PENDING_CASH = "PENDING_CASH"
    OWNER_PROTECTED_CASH = "OWNER_PROTECTED_CASH"
    QUARANTINED_CASH = "QUARANTINED_CASH"
    COLLATERAL_OR_MARGIN_LOCK = "COLLATERAL_OR_MARGIN_LOCK"


class ReconciliationStateV1(StrEnum):
    RECONCILED = "RECONCILED"
    IMMATERIAL_BREAK = "IMMATERIAL_BREAK"
    MATERIAL_BREAK = "MATERIAL_BREAK"
    UNKNOWN = "UNKNOWN"


class CostEmbeddingV1(StrEnum):
    EXPLICIT = "EXPLICIT"
    ALREADY_EMBEDDED = "ALREADY_EMBEDDED"


@dataclass(frozen=True, slots=True)
class AccountingAmountV1:
    amount_text: str
    currency_or_asset: str
    ledger_unit: str
    basis: str
    scale: int
    rounding_policy_ref: str

    def __post_init__(self) -> None:
        amount = _canonical_decimal_text(self.amount_text, "amount_text")
        for name in ("currency_or_asset", "ledger_unit", "basis", "rounding_policy_ref"):
            _required(getattr(self, name), name)
        _require_declared_scale(amount, self.scale, "amount_text")

    @property
    def decimal(self) -> Decimal:
        return exact_decimal(self.amount_text, field_name="amount_text")

    @property
    def partition(self) -> tuple[str, str, str]:
        return self.ledger_unit, self.currency_or_asset, self.basis


@dataclass(frozen=True, slots=True)
class JournalAccountV1:
    account_id: str
    account_class: str
    normal_balance: NormalBalanceV1
    ledger_unit: str
    currency_or_asset: str
    basis: str
    active_state: str

    def __post_init__(self) -> None:
        for name in ("account_id", "account_class", "ledger_unit", "currency_or_asset", "basis", "active_state"):
            _required(getattr(self, name), name)
        if not isinstance(self.normal_balance, NormalBalanceV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "normal_balance must be typed")


@dataclass(frozen=True, slots=True)
class JournalPostingV1:
    posting_id: str
    journal_transaction_id: str
    account_id: str
    entry_side: EntrySideV1
    amount_text: str
    ledger_unit: str
    currency_or_asset: str
    basis: str
    scale: int
    effective_at: datetime | str
    recorded_at: datetime | str
    source_event_ref: str

    def __post_init__(self) -> None:
        for name in ("posting_id", "journal_transaction_id", "account_id", "ledger_unit", "currency_or_asset", "basis", "source_event_ref"):
            _required(getattr(self, name), name)
        if not isinstance(self.entry_side, EntrySideV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "entry_side must be DEBIT or CREDIT")
        amount = _canonical_decimal_text(self.amount_text, "amount_text")
        if amount <= 0:
            raise AccountingContractError(ReasonCode.OUT_OF_DOMAIN, "posting magnitude must be positive")
        _require_declared_scale(amount, self.scale, "amount_text")
        object.__setattr__(self, "effective_at", parse_utc(self.effective_at, field_name="effective_at"))
        object.__setattr__(self, "recorded_at", parse_utc(self.recorded_at, field_name="recorded_at"))

    @property
    def transaction_id(self) -> str:
        """Accounting-contract alias for the canonical receipt field name."""

        return self.journal_transaction_id

    @property
    def magnitude(self) -> Decimal:
        return exact_decimal(self.amount_text, field_name="amount_text")

    @property
    def signed_conservation_value(self) -> Decimal:
        return self.magnitude if self.entry_side is EntrySideV1.DEBIT else -self.magnitude

    @property
    def partition(self) -> tuple[str, str, str]:
        return self.ledger_unit, self.currency_or_asset, self.basis


@dataclass(frozen=True, slots=True)
class JournalTransactionV1:
    journal_transaction_id: str
    transaction_class: str
    economic_event_refs: tuple[str, ...]
    posting_refs: tuple[str, ...]
    effective_at: datetime | str
    recorded_at: datetime | str
    description_code: str
    authority_class: str
    reversal_of_transaction_id: str | None = None

    def __post_init__(self) -> None:
        _required(self.journal_transaction_id, "journal_transaction_id")
        _required(self.transaction_class, "transaction_class")
        _required(self.description_code, "description_code")
        _required(self.authority_class, "authority_class")
        _refs(self.economic_event_refs, "economic_event_refs", required=True)
        _refs(self.posting_refs, "posting_refs", required=True)
        if len(self.posting_refs) < 2:
            raise AccountingContractError(ReasonCode.ACCOUNTING_IMBALANCE, "journal requires at least two postings")
        if self.reversal_of_transaction_id is not None:
            _required(self.reversal_of_transaction_id, "reversal_of_transaction_id")
            if "REVERS" not in self.transaction_class.upper() and "CORRECTION" not in self.transaction_class.upper():
                raise AccountingContractError(ReasonCode.REVERSAL_INVALID, "only reversal/correction transactions may link an original")
        object.__setattr__(self, "effective_at", parse_utc(self.effective_at, field_name="effective_at"))
        object.__setattr__(self, "recorded_at", parse_utc(self.recorded_at, field_name="recorded_at"))


@dataclass(frozen=True, slots=True)
class PositionProjectionV1:
    position_id: str
    venue_ref: str
    market_ref: str
    contract_ref: str
    outcome_or_side: str
    quantity_text: str
    cost_basis_text: str
    position_state: str
    event_refs: tuple[str, ...]
    effective_at: datetime | str
    recorded_at: datetime | str

    def __post_init__(self) -> None:
        for name in ("position_id", "venue_ref", "market_ref", "contract_ref", "outcome_or_side", "position_state"):
            _required(getattr(self, name), name)
        _canonical_decimal_text(self.quantity_text, "quantity_text")
        _canonical_decimal_text(self.cost_basis_text, "cost_basis_text")
        _refs(self.event_refs, "event_refs", required=True)
        object.__setattr__(self, "effective_at", parse_utc(self.effective_at, field_name="effective_at"))
        object.__setattr__(self, "recorded_at", parse_utc(self.recorded_at, field_name="recorded_at"))


class PositionEventClassV1(StrEnum):
    ACCEPTED_FILL = "ACCEPTED_FILL"
    CORRECTION = "CORRECTION"
    REVERSAL = "REVERSAL"
    SETTLEMENT = "SETTLEMENT"


@dataclass(frozen=True, slots=True)
class PositionEventV1:
    event_identity: str
    causation_id: str
    event_class: PositionEventClassV1
    sequence: int
    signed_quantity_text: str
    signed_cost_basis_text: str
    effective_at: datetime | str
    recorded_at: datetime | str
    canonical_payload_json: str

    def __post_init__(self) -> None:
        _required(self.event_identity, "event_identity")
        _required(self.causation_id, "causation_id")
        _required(self.canonical_payload_json, "canonical_payload_json")
        if deterministic_json(safe_json_loads(self.canonical_payload_json)) != self.canonical_payload_json:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "position event payload must be canonical deterministic JSON")
        if not isinstance(self.event_class, PositionEventClassV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "position event class must be typed")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 1:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "position event sequence must be positive")
        quantity = _canonical_decimal_text(self.signed_quantity_text, "signed_quantity_text")
        _canonical_decimal_text(self.signed_cost_basis_text, "signed_cost_basis_text")
        if self.event_class is PositionEventClassV1.SETTLEMENT and quantity != 0:
            raise AccountingContractError(ReasonCode.INVALID_CONTRACT, "settlement cannot manufacture position quantity")
        object.__setattr__(self, "effective_at", parse_utc(self.effective_at, field_name="effective_at"))
        object.__setattr__(self, "recorded_at", parse_utc(self.recorded_at, field_name="recorded_at"))


def project_position_v1(
    *, position_id: str, venue_ref: str, market_ref: str, contract_ref: str,
    outcome_or_side: str, events: Sequence[PositionEventV1],
) -> PositionProjectionV1:
    """Project position state only from ordered accepted append-only event classes."""

    if not events:
        raise AccountingContractError(ReasonCode.INCOMPLETE_CONTRACT, "position projection requires accepted events")
    accepted: list[PositionEventV1] = []
    seen: dict[str, PositionEventV1] = {}
    last_sequence = 0
    for event in events:
        if not isinstance(event, PositionEventV1):
            raise AccountingContractError(ReasonCode.INVALID_CONTRACT, "position input is not a typed accepted event")
        existing = seen.get(event.event_identity)
        if existing is not None:
            if existing != event:
                raise AccountingContractError(ReasonCode.DUPLICATE_EVENT_CONFLICT, "position event identity has conflicting payload")
            continue
        if event.sequence <= last_sequence:
            raise AccountingContractError(ReasonCode.ILLEGAL_STATE_TRANSITION, "position event sequence is regressive or duplicated")
        seen[event.event_identity] = event
        accepted.append(event)
        last_sequence = event.sequence
    quantity = sum((exact_decimal(event.signed_quantity_text, field_name="signed_quantity_text") for event in accepted), Decimal(0))
    cost = sum((exact_decimal(event.signed_cost_basis_text, field_name="signed_cost_basis_text") for event in accepted), Decimal(0))
    settled = accepted[-1].event_class is PositionEventClassV1.SETTLEMENT
    state = "SETTLED" if settled and quantity == 0 else "CLOSED_AWAITING_SETTLEMENT" if quantity == 0 else "OPEN"
    return PositionProjectionV1(
        position_id=position_id,
        venue_ref=venue_ref,
        market_ref=market_ref,
        contract_ref=contract_ref,
        outcome_or_side=outcome_or_side,
        quantity_text=str(quantity),
        cost_basis_text=str(cost),
        position_state=state,
        event_refs=tuple(event.event_identity for event in accepted),
        effective_at=max(event.effective_at for event in accepted),
        recorded_at=max(event.recorded_at for event in accepted),
    )


@dataclass(frozen=True, slots=True)
class CrossVenueTransferV1:
    transfer_id: str
    source_venue_ref: str
    destination_venue_ref: str
    amount: AccountingAmountV1
    source_posting_ref: str
    destination_posting_ref: str
    transfer_state: str

    def __post_init__(self) -> None:
        for name in ("transfer_id", "source_venue_ref", "destination_venue_ref", "source_posting_ref", "destination_posting_ref", "transfer_state"):
            _required(getattr(self, name), name)
        if self.source_venue_ref == self.destination_venue_ref or self.source_posting_ref == self.destination_posting_ref:
            raise AccountingContractError(ReasonCode.INVALID_CONTRACT, "cross-venue transfer requires distinct paired books/postings")
        if not isinstance(self.amount, AccountingAmountV1) or self.amount.decimal <= 0:
            raise AccountingContractError(ReasonCode.OUT_OF_DOMAIN, "cross-venue transfer amount must be positive and typed")
        if self.transfer_state not in {"PENDING_IN_TRANSIT", "SETTLED_PAIRED"}:
            raise AccountingContractError(ReasonCode.INVALID_CONTRACT, "unmatched transfer must remain pending")


_TCA_COMPONENTS = (
    "spread_cost", "slippage_cost", "impact_cost", "fees", "rebates",
    "latency_cost", "adverse_selection_cost", "opportunity_cost", "other_declared_costs",
)


@dataclass(frozen=True, slots=True)
class TCADecompositionV1:
    tca_id: str
    decision_benchmark_ref: str
    fill_refs: tuple[str, ...]
    spread_cost: Decimal | str | int
    slippage_cost: Decimal | str | int
    impact_cost: Decimal | str | int
    fees: Decimal | str | int
    rebates: Decimal | str | int
    latency_cost: Decimal | str | int
    adverse_selection_cost: Decimal | str | int
    opportunity_cost: Decimal | str | int
    other_declared_costs: Decimal | str | int
    total_cost: Decimal | str | int
    embedding_attribution: tuple[tuple[str, CostEmbeddingV1], ...]

    def __post_init__(self) -> None:
        _required(self.tca_id, "tca_id")
        _required(self.decision_benchmark_ref, "decision_benchmark_ref")
        _refs(self.fill_refs, "fill_refs")
        values: dict[str, Decimal] = {}
        for name in (*_TCA_COMPONENTS, "total_cost"):
            values[name] = exact_decimal(getattr(self, name), field_name=name)
            object.__setattr__(self, name, values[name])
        if not isinstance(self.embedding_attribution, tuple):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "embedding_attribution must be typed tuple")
        attribution = dict(self.embedding_attribution)
        if set(attribution) != set(_TCA_COMPONENTS) or len(attribution) != len(self.embedding_attribution):
            raise AccountingContractError(ReasonCode.INVALID_CONTRACT, "every TCA component must be attributed exactly once")
        if any(not isinstance(value, CostEmbeddingV1) for value in attribution.values()):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "TCA attribution values must be typed")
        computed = sum((values[name] for name in _TCA_COMPONENTS if attribution[name] is CostEmbeddingV1.EXPLICIT), Decimal(0))
        if computed != values["total_cost"]:
            raise AccountingContractError(ReasonCode.ACCOUNTING_IMBALANCE, "TCA total would omit or double count a component")


@dataclass(frozen=True, slots=True)
class ExposureProjectionV1:
    projection_id: str
    classification_dimensions: tuple[tuple[str, str], ...]
    signed_exposure_values: tuple[Decimal | str | int, ...]
    position_refs: tuple[str, ...]
    effective_at: datetime | str
    recorded_at: datetime | str

    def __post_init__(self) -> None:
        _required(self.projection_id, "projection_id")
        if not self.classification_dimensions or len(self.classification_dimensions) != len(self.signed_exposure_values):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "exposure dimensions and values must align")
        if len(self.classification_dimensions) != len(set(self.classification_dimensions)):
            raise AccountingContractError(ReasonCode.UNIT_BASIS_MISMATCH, "incompatible exposure partitions cannot be collapsed")
        object.__setattr__(self, "signed_exposure_values", tuple(exact_decimal(value, field_name="signed_exposure") for value in self.signed_exposure_values))
        _refs(self.position_refs, "position_refs", required=True)
        object.__setattr__(self, "effective_at", parse_utc(self.effective_at, field_name="effective_at"))
        object.__setattr__(self, "recorded_at", parse_utc(self.recorded_at, field_name="recorded_at"))


@dataclass(frozen=True, slots=True)
class CashStateProjectionV1:
    projection_id: str
    cash_class: CashStateClassV1
    amount_text: str
    currency_or_asset: str
    basis: str
    event_refs: tuple[str, ...]
    journal_refs: tuple[str, ...]
    effective_at: datetime | str
    recorded_at: datetime | str
    reconciliation_state: ReconciliationStateV1

    def __post_init__(self) -> None:
        _required(self.projection_id, "projection_id")
        if not isinstance(self.cash_class, CashStateClassV1) or not isinstance(self.reconciliation_state, ReconciliationStateV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "cash/reconciliation classes must be typed")
        _canonical_decimal_text(self.amount_text, "amount_text")
        _required(self.currency_or_asset, "currency_or_asset")
        _required(self.basis, "basis")
        _refs(self.event_refs, "event_refs", required=True)
        _refs(self.journal_refs, "journal_refs", required=True)
        object.__setattr__(self, "effective_at", parse_utc(self.effective_at, field_name="effective_at"))
        object.__setattr__(self, "recorded_at", parse_utc(self.recorded_at, field_name="recorded_at"))

    @property
    def amount(self) -> Decimal:
        return exact_decimal(self.amount_text, field_name="amount_text")


@dataclass(frozen=True, slots=True)
class ReconciliationRunV1:
    run_id: str
    internal_projection_refs: tuple[str, ...]
    external_snapshot_ref: str
    as_of: datetime | str
    break_refs: tuple[str, ...]
    terminal_state: ReconciliationStateV1
    blocks_new_exposure: bool

    def __post_init__(self) -> None:
        _required(self.run_id, "run_id")
        _refs(self.internal_projection_refs, "internal_projection_refs", required=True)
        _required(self.external_snapshot_ref, "external_snapshot_ref")
        _refs(self.break_refs, "break_refs")
        if not isinstance(self.terminal_state, ReconciliationStateV1) or type(self.blocks_new_exposure) is not bool:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "reconciliation outcome must be typed")
        expected_block = self.terminal_state in {ReconciliationStateV1.MATERIAL_BREAK, ReconciliationStateV1.UNKNOWN}
        if self.blocks_new_exposure is not expected_block:
            raise AccountingContractError(ReasonCode.RECONCILIATION_REQUIRED, "material or unknown reconciliation must block exposure")
        object.__setattr__(self, "as_of", parse_utc(self.as_of, field_name="as_of"))


@dataclass(frozen=True, slots=True)
class ReconciliationBreakReceiptV1:
    break_receipt_id: str
    reconciliation_run_id: str
    break_class: str
    internal_ref: str
    external_snapshot_ref: str
    field_id: str
    internal_value_text: str
    external_value_text: str
    unit: str
    basis: str
    materiality: ReconciliationStateV1
    disposition: str
    blocks_new_exposure: bool
    effective_at: datetime | str
    recorded_at: datetime | str

    def __post_init__(self) -> None:
        for name in ("break_receipt_id", "reconciliation_run_id", "break_class", "internal_ref", "external_snapshot_ref", "field_id", "internal_value_text", "external_value_text", "unit", "basis", "disposition"):
            _required(getattr(self, name), name)
        expected = self.materiality in {ReconciliationStateV1.MATERIAL_BREAK, ReconciliationStateV1.UNKNOWN}
        if type(self.blocks_new_exposure) is not bool or self.blocks_new_exposure is not expected:
            raise AccountingContractError(ReasonCode.RECONCILIATION_REQUIRED, "break blocking flag conflicts with materiality")
        object.__setattr__(self, "effective_at", parse_utc(self.effective_at, field_name="effective_at"))
        object.__setattr__(self, "recorded_at", parse_utc(self.recorded_at, field_name="recorded_at"))


class AccountingAndTCAServiceV1:
    """Sole pure semantic owner; it performs no persistence or external I/O."""

    @staticmethod
    def validate_journal(transaction: JournalTransactionV1, postings: Sequence[JournalPostingV1], accounts: Mapping[str, JournalAccountV1]) -> None:
        if len(postings) < 2 or tuple(posting.posting_id for posting in postings) != transaction.posting_refs:
            raise AccountingContractError(ReasonCode.ACCOUNTING_IMBALANCE, "transaction/posting references do not match")
        balances: dict[tuple[str, str, str], Decimal] = {}
        for posting in postings:
            if posting.journal_transaction_id != transaction.journal_transaction_id:
                raise AccountingContractError(ReasonCode.ACCOUNTING_IMBALANCE, "posting belongs to a different transaction")
            account = accounts.get(posting.account_id)
            if account is None or account.active_state != "ACTIVE":
                raise AccountingContractError(ReasonCode.INVALID_CONTRACT, "posting account is absent or inactive")
            if posting.partition != (account.ledger_unit, account.currency_or_asset, account.basis):
                raise AccountingContractError(ReasonCode.UNIT_BASIS_MISMATCH, "posting/account unit partition differs")
            balances[posting.partition] = balances.get(posting.partition, Decimal(0)) + posting.signed_conservation_value
        nonzero = {partition: value for partition, value in balances.items() if value != 0}
        if nonzero:
            raise AccountingContractError(ReasonCode.ACCOUNTING_IMBALANCE, f"journal is not exact-zero by partition: {nonzero}")

    @staticmethod
    def deployable_capital(
        *, settled_spendable_cash: AccountingAmountV1, reserve_cash_floor: AccountingAmountV1,
        owner_protected_cash: AccountingAmountV1, quarantined_capital: AccountingAmountV1,
        reconciliation_state: ReconciliationStateV1,
    ) -> Decimal:
        amounts = (settled_spendable_cash, reserve_cash_floor, owner_protected_cash, quarantined_capital)
        if len({amount.partition for amount in amounts}) != 1:
            raise AccountingContractError(ReasonCode.UNIT_BASIS_MISMATCH, "deployable-capital inputs must share one partition")
        if any(amount.decimal < 0 for amount in amounts):
            raise AccountingContractError(ReasonCode.OUT_OF_DOMAIN, "deployable-capital inputs must be nonnegative")
        if reconciliation_state in {ReconciliationStateV1.MATERIAL_BREAK, ReconciliationStateV1.UNKNOWN}:
            raise AccountingContractError(ReasonCode.RECONCILIATION_REQUIRED, "unreconciled cash is unavailable")
        with localcontext(decimal_context_v1()) as context:
            value = context.subtract(
                context.subtract(context.subtract(settled_spendable_cash.decimal, reserve_cash_floor.decimal), owner_protected_cash.decimal),
                quarantined_capital.decimal,
            )
        return max(Decimal(0), value)

    @staticmethod
    def validate_reserve_conservation(
        *, available_cash: AccountingAmountV1, reserved_cash: AccountingAmountV1,
        pending_cash: AccountingAmountV1, owner_protected_cash: AccountingAmountV1,
        quarantined_cash: AccountingAmountV1, accepted_cash_basis: AccountingAmountV1,
    ) -> None:
        amounts = (available_cash, reserved_cash, pending_cash, owner_protected_cash, quarantined_cash, accepted_cash_basis)
        if len({amount.partition for amount in amounts}) != 1:
            raise AccountingContractError(ReasonCode.UNIT_BASIS_MISMATCH, "reserve conservation cannot cross partitions")
        if any(amount.decimal < 0 for amount in amounts):
            raise AccountingContractError(ReasonCode.OUT_OF_DOMAIN, "reserve-conservation inputs must be nonnegative")
        left = sum((amount.decimal for amount in amounts[:-1]), Decimal(0))
        if left != accepted_cash_basis.decimal:
            raise AccountingContractError(ReasonCode.ACCOUNTING_IMBALANCE, "cash reserve conservation residual is nonzero")


CASH_STATE_CLASS_REGISTRY: Mapping[str, CashStateClassV1] = MappingProxyType({row.value: row for row in CashStateClassV1})
if len(CASH_STATE_CLASS_REGISTRY) != 12:
    raise RuntimeError("cash-state registry must contain exactly twelve orthogonal classes")
