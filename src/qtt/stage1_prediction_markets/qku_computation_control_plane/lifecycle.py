"""No-write lifecycle, preflight, timing, custody, fill, and rate-budget contracts."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_CEILING
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from .context import exact_decimal, parse_utc
from .errors import ContractValidationError, LifecycleContractError, ReasonCode
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
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be unique")


def _canonical_decimal_text(value: str, name: str) -> Decimal:
    _required(value, name)
    result = exact_decimal(value, field_name=name)
    if str(result) != value:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be canonical Decimal text")
    return result


@dataclass(frozen=True, slots=True)
class StateTransitionRegistryV1:
    registry_id: str
    states: frozenset[str]
    allowed_transitions: frozenset[tuple[str, str]]
    terminal_states: frozenset[str] = frozenset()
    blocking_states: frozenset[str] = frozenset()
    contract_boundary_only: bool = False

    def __post_init__(self) -> None:
        _required(self.registry_id, "registry_id")
        if not self.states or any(not state for state in self.states):
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "state registry cannot be empty")
        if any(source not in self.states or target not in self.states for source, target in self.allowed_transitions):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "transition references undeclared state")
        if not self.terminal_states <= self.states or not self.blocking_states <= self.states:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "terminal/blocking state is undeclared")
        if type(self.contract_boundary_only) is not bool:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "contract_boundary_only must be bool")

    def validate(self, prior_state: str, candidate_state: str) -> None:
        if (prior_state, candidate_state) not in self.allowed_transitions:
            raise LifecycleContractError(
                ReasonCode.ILLEGAL_STATE_TRANSITION,
                f"illegal {self.registry_id} transition {prior_state}->{candidate_state}",
            )


def _registry(
    registry_id: str,
    states: tuple[str, ...],
    transitions: tuple[tuple[str, str], ...],
    *, terminal: tuple[str, ...] = (), blocking: tuple[str, ...] = (), boundary: bool = False,
) -> StateTransitionRegistryV1:
    return StateTransitionRegistryV1(
        registry_id, frozenset(states), frozenset(transitions), frozenset(terminal), frozenset(blocking), boundary
    )


UNIT_OF_WORK_STATE_MACHINE_V1 = _registry(
    "UNIT_OF_WORK_STATE_MACHINE_V1",
    ("NEW", "ACTIVE", "COMMITTING", "COMMITTED", "ROLLING_BACK", "ROLLED_BACK", "CONFLICT", "RETRY_EXHAUSTED", "REJECTED"),
    (("NEW", "ACTIVE"), ("ACTIVE", "COMMITTING"), ("COMMITTING", "COMMITTED"), ("ACTIVE", "ROLLING_BACK"), ("COMMITTING", "ROLLING_BACK"), ("ROLLING_BACK", "ROLLED_BACK"), ("ACTIVE", "CONFLICT"), ("ACTIVE", "REJECTED"), ("ACTIVE", "RETRY_EXHAUSTED")),
    terminal=("COMMITTED", "ROLLED_BACK", "CONFLICT", "RETRY_EXHAUSTED", "REJECTED"),
)
IDEMPOTENCY_CLAIM_STATE_MACHINE_V1 = _registry(
    "IDEMPOTENCY_CLAIM_STATE_MACHINE_V1",
    ("UNSEEN", "ACQUIRED", "COMPLETED", "FAILED_RETRYABLE", "FAILED_FINAL", "CONFLICT"),
    (("UNSEEN", "ACQUIRED"), ("ACQUIRED", "COMPLETED"), ("ACQUIRED", "FAILED_RETRYABLE"), ("ACQUIRED", "FAILED_FINAL"), ("UNSEEN", "CONFLICT")),
)
ORDER_INTENT_STATE_MACHINE_V1 = _registry(
    "ORDER_INTENT_STATE_MACHINE_V1",
    ("DRAFT", "VALIDATED", "PREFLIGHT_BLOCKED", "SUBMIT_DISABLED", "ROUTER_BOUNDARY_CONTRACT_ONLY", "EXPIRED"),
    (("DRAFT", "VALIDATED"), ("DRAFT", "PREFLIGHT_BLOCKED"), ("VALIDATED", "SUBMIT_DISABLED"), ("VALIDATED", "ROUTER_BOUNDARY_CONTRACT_ONLY"), ("DRAFT", "EXPIRED"), ("VALIDATED", "EXPIRED")),
    terminal=("PREFLIGHT_BLOCKED", "SUBMIT_DISABLED", "ROUTER_BOUNDARY_CONTRACT_ONLY", "EXPIRED"),
)
FUTURE_ORDER_CUSTODY_STATE_MACHINE_V1 = _registry(
    "FUTURE_ORDER_CUSTODY_STATE_MACHINE_V1",
    ("RELEASE_REQUESTED", "PROVIDER_PENDING", "ACKNOWLEDGED", "PARTIALLY_FILLED", "FILLED", "REJECTED", "CANCEL_PENDING", "CANCELLED", "REPLACE_PENDING", "EXPIRED", "SETTLED", "UNKNOWN_RECONCILIATION_REQUIRED"),
    (("RELEASE_REQUESTED", "PROVIDER_PENDING"), ("PROVIDER_PENDING", "ACKNOWLEDGED"), ("PROVIDER_PENDING", "REJECTED"), ("PROVIDER_PENDING", "UNKNOWN_RECONCILIATION_REQUIRED"), ("ACKNOWLEDGED", "PARTIALLY_FILLED"), ("ACKNOWLEDGED", "FILLED"), ("ACKNOWLEDGED", "CANCEL_PENDING"), ("ACKNOWLEDGED", "EXPIRED"), ("PARTIALLY_FILLED", "PARTIALLY_FILLED"), ("PARTIALLY_FILLED", "FILLED"), ("PARTIALLY_FILLED", "CANCEL_PENDING"), ("CANCEL_PENDING", "CANCELLED"), ("CANCEL_PENDING", "PARTIALLY_FILLED"), ("CANCELLED", "PARTIALLY_FILLED"), ("FILLED", "SETTLED"), ("PARTIALLY_FILLED", "SETTLED"), ("UNKNOWN_RECONCILIATION_REQUIRED", "ACKNOWLEDGED"), ("UNKNOWN_RECONCILIATION_REQUIRED", "PARTIALLY_FILLED"), ("UNKNOWN_RECONCILIATION_REQUIRED", "FILLED"), ("UNKNOWN_RECONCILIATION_REQUIRED", "REJECTED"), ("UNKNOWN_RECONCILIATION_REQUIRED", "CANCELLED")),
    boundary=True,
)
OUTBOX_INTENT_STATE_MACHINE_V1 = _registry(
    "OUTBOX_INTENT_STATE_MACHINE_V1",
    ("RECORDED_NOT_DISPATCHABLE", "FUTURE_DISPATCH_ELIGIBLE", "FUTURE_DISPATCHED", "FUTURE_ACKNOWLEDGED", "FUTURE_FAILED"),
    (("RECORDED_NOT_DISPATCHABLE", "FUTURE_DISPATCH_ELIGIBLE"), ("FUTURE_DISPATCH_ELIGIBLE", "FUTURE_DISPATCHED"), ("FUTURE_DISPATCHED", "FUTURE_ACKNOWLEDGED"), ("FUTURE_DISPATCHED", "FUTURE_FAILED")),
    boundary=True,
)
POSITION_STATE_MACHINE_V1 = _registry(
    "POSITION_STATE_MACHINE_V1",
    ("FLAT", "OPEN", "PARTIALLY_CLOSED", "CLOSED_AWAITING_SETTLEMENT", "SETTLED", "DISPUTED", "CORRECTION_REQUIRED"),
    (("FLAT", "OPEN"), ("OPEN", "OPEN"), ("OPEN", "PARTIALLY_CLOSED"), ("OPEN", "CLOSED_AWAITING_SETTLEMENT"), ("PARTIALLY_CLOSED", "PARTIALLY_CLOSED"), ("PARTIALLY_CLOSED", "CLOSED_AWAITING_SETTLEMENT"), ("CLOSED_AWAITING_SETTLEMENT", "SETTLED"), ("CLOSED_AWAITING_SETTLEMENT", "DISPUTED"), ("DISPUTED", "SETTLED"), ("SETTLED", "CORRECTION_REQUIRED"), ("CORRECTION_REQUIRED", "SETTLED")),
)
RECONCILIATION_STATE_MACHINE_V1 = _registry(
    "RECONCILIATION_STATE_MACHINE_V1",
    ("NOT_RUN", "MATCHED", "BREAK_NONMATERIAL", "BREAK_MATERIAL", "UNKNOWN", "RESOLVING", "RESOLVED"),
    (("NOT_RUN", "MATCHED"), ("NOT_RUN", "BREAK_NONMATERIAL"), ("NOT_RUN", "BREAK_MATERIAL"), ("NOT_RUN", "UNKNOWN"), ("BREAK_NONMATERIAL", "RESOLVING"), ("BREAK_MATERIAL", "RESOLVING"), ("UNKNOWN", "RESOLVING"), ("RESOLVING", "RESOLVED"), ("RESOLVED", "MATCHED")),
    blocking=("BREAK_MATERIAL", "UNKNOWN", "RESOLVING"),
)

STATE_TRANSITION_REGISTRIES: Mapping[str, StateTransitionRegistryV1] = MappingProxyType(
    {row.registry_id: row for row in (
        UNIT_OF_WORK_STATE_MACHINE_V1, IDEMPOTENCY_CLAIM_STATE_MACHINE_V1,
        ORDER_INTENT_STATE_MACHINE_V1, FUTURE_ORDER_CUSTODY_STATE_MACHINE_V1,
        OUTBOX_INTENT_STATE_MACHINE_V1, POSITION_STATE_MACHINE_V1, RECONCILIATION_STATE_MACHINE_V1,
    )}
)

CASH_STATE_EVENT_EFFECTS: Mapping[str, tuple[str, str] | str] = MappingProxyType(
    {
        "RESERVE_CREATED": ("AVAILABLE_CASH", "RESERVED_CASH"),
        "RESERVE_RELEASED": ("RESERVED_CASH", "AVAILABLE_CASH"),
        "FILL_EXECUTED": "BALANCED_VENUE_SIDE_SPECIFIC_POSTINGS",
        "EXIT_REALIZED": "REALIZED_EXIT_NET_CASH_FROM_ACCEPTED_EXIT_FILL",
        "SETTLEMENT_ACCEPTED": ("PENDING_CASH", "REALIZED_SETTLEMENT_NET_CASH_OR_SETTLED_SPENDABLE_CASH"),
        "QUARANTINE_CREATED": ("AVAILABLE_OR_SETTLED_SPENDABLE", "QUARANTINED_CASH"),
    }
)


class TransitionDispositionV1(StrEnum):
    ACCEPTED = "ACCEPTED"
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    REJECTED = "REJECTED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class StateTransitionReceiptV1:
    transition_id: str
    aggregate_id: str
    transition_family: str
    prior_state: str
    event_class: str
    candidate_state: str
    disposition: TransitionDispositionV1
    event_identity: str
    aggregate_version_before: int
    aggregate_version_after: int
    effective_at: datetime | str
    recorded_at: datetime | str
    reason_code: str
    reconciliation_required: bool

    def __post_init__(self) -> None:
        for name in ("transition_id", "aggregate_id", "transition_family", "prior_state", "event_class", "candidate_state", "event_identity", "reason_code"):
            _required(getattr(self, name), name)
        if self.transition_family not in STATE_TRANSITION_REGISTRIES:
            raise LifecycleContractError(ReasonCode.ILLEGAL_STATE_TRANSITION, "unknown transition registry")
        for name in ("aggregate_version_before", "aggregate_version_after"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be nonnegative integer")
        if not isinstance(self.disposition, TransitionDispositionV1) or type(self.reconciliation_required) is not bool:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "transition disposition must be typed")
        if self.disposition is TransitionDispositionV1.ACCEPTED:
            STATE_TRANSITION_REGISTRIES[self.transition_family].validate(self.prior_state, self.candidate_state)
            if self.aggregate_version_after != self.aggregate_version_before + 1 or self.reconciliation_required:
                raise LifecycleContractError(ReasonCode.ILLEGAL_STATE_TRANSITION, "accepted transition version/disposition invalid")
        elif self.disposition is TransitionDispositionV1.EXACT_DUPLICATE:
            if (
                self.aggregate_version_after != self.aggregate_version_before
                or self.candidate_state != self.prior_state
                or self.reconciliation_required
            ):
                raise LifecycleContractError(ReasonCode.DUPLICATE_EVENT_CONFLICT, "duplicate must not mutate version")
        elif self.disposition is TransitionDispositionV1.RECONCILIATION_REQUIRED:
            if (
                self.transition_family != FUTURE_ORDER_CUSTODY_STATE_MACHINE_V1.registry_id
                or self.candidate_state != "UNKNOWN_RECONCILIATION_REQUIRED"
                or not self.reconciliation_required
                or self.aggregate_version_after != self.aggregate_version_before + 1
            ):
                raise LifecycleContractError(ReasonCode.RECONCILIATION_REQUIRED, "ambiguous provider transition must enter the typed reconciliation state once")
            FUTURE_ORDER_CUSTODY_STATE_MACHINE_V1.validate(self.prior_state, self.candidate_state)
        elif self.aggregate_version_after != self.aggregate_version_before or self.reconciliation_required:
            raise LifecycleContractError(ReasonCode.ILLEGAL_STATE_TRANSITION, "rejected transition must not mutate version or require reconciliation")
        object.__setattr__(self, "effective_at", parse_utc(self.effective_at, field_name="effective_at"))
        object.__setattr__(self, "recorded_at", parse_utc(self.recorded_at, field_name="recorded_at"))


@dataclass(frozen=True, slots=True)
class EconomicIdentitySetV1:
    semantic_economic_intent_id: str
    command_id: str
    attempt_id: str
    provider_request_id: str
    request_id: str
    trace_id: str
    transaction_id: str
    event_id: str

    def __post_init__(self) -> None:
        values = []
        for field in fields(self):
            value = getattr(self, field.name)
            _required(value, field.name)
            values.append(value)
        if len(values) != len(set(values)):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "economic, request, trace, transaction, and event identities must remain distinct")


@dataclass(frozen=True, slots=True)
class OrderIntentRecordV1:
    economic_intent_id: str
    trade_plan_candidate_ref: str
    snapshot_ref: str
    component_version_refs: tuple[str, ...]
    venue_ref: str
    market_ref: str
    contract_ref: str
    outcome_or_side: str
    quantity_text: str
    limit_price_text: str
    order_type: str
    time_in_force: str
    expires_at: datetime | str
    owner_envelope_ref: str
    mode_ref: str
    risk_cash_source_gate_refs: tuple[str, ...]
    intent_state: str
    no_order_authority_flag: bool = True

    def __post_init__(self) -> None:
        for name in ("economic_intent_id", "trade_plan_candidate_ref", "snapshot_ref", "venue_ref", "market_ref", "contract_ref", "outcome_or_side", "quantity_text", "limit_price_text", "order_type", "time_in_force", "owner_envelope_ref", "mode_ref", "intent_state"):
            _required(getattr(self, name), name)
        _refs(self.component_version_refs, "component_version_refs", required=True)
        _refs(self.risk_cash_source_gate_refs, "risk_cash_source_gate_refs", required=True)
        quantity = _canonical_decimal_text(self.quantity_text, "quantity_text")
        price = _canonical_decimal_text(self.limit_price_text, "limit_price_text")
        if quantity <= 0 or price < 0 or price > 1:
            raise LifecycleContractError(ReasonCode.OUT_OF_DOMAIN, "order intent quantity/price outside no-write contract domain")
        if self.intent_state not in {"CONTRACT_ONLY", "SUBMIT_DISABLED"} or self.no_order_authority_flag is not True:
            raise LifecycleContractError(ReasonCode.RUNTIME_EFFECT_FORBIDDEN, "order intent has no order authority")
        object.__setattr__(self, "expires_at", parse_utc(self.expires_at, field_name="expires_at"))


class GateDispositionV1(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    STALE = "STALE"


PREFLIGHT_GATE_CLASSES = (
    "SOURCE", "MODEL", "FRESHNESS", "VENUE", "CAP", "RISK", "CASH", "ACCOUNTING",
    "CONDUCT", "KILL", "MODE", "SNAPSHOT", "IDEMPOTENCY",
)


@dataclass(frozen=True, slots=True)
class PretradeGateResultV1:
    gate_class: str
    disposition: GateDispositionV1
    evidence_ref: str
    reason_code: str

    def __post_init__(self) -> None:
        if self.gate_class not in PREFLIGHT_GATE_CLASSES or not isinstance(self.disposition, GateDispositionV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "pretrade gate is not allowlisted")
        _required(self.evidence_ref, "evidence_ref")
        _required(self.reason_code, "reason_code")


class PreflightTerminalOutcomeV1(StrEnum):
    PREFLIGHT_BLOCKED = "PREFLIGHT_BLOCKED"
    SUBMIT_DISABLED = "SUBMIT_DISABLED"
    ROUTER_BOUNDARY_CONTRACT_ONLY = "ROUTER_BOUNDARY_CONTRACT_ONLY"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True, slots=True)
class PretradeGateBundleV1:
    gate_results: tuple[PretradeGateResultV1, ...]
    terminal_outcome: PreflightTerminalOutcomeV1
    outbox_intent_allowed: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.gate_results, tuple) or {row.gate_class for row in self.gate_results} != set(PREFLIGHT_GATE_CLASSES) or len(self.gate_results) != len(PREFLIGHT_GATE_CLASSES):
            raise LifecycleContractError(ReasonCode.INCOMPLETE_CONTRACT, "every preflight gate must appear exactly once")
        if not isinstance(self.terminal_outcome, PreflightTerminalOutcomeV1) or type(self.outbox_intent_allowed) is not bool:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "preflight outcome must be typed")
        all_pass = all(row.disposition is GateDispositionV1.PASS for row in self.gate_results)
        if all_pass and self.terminal_outcome is PreflightTerminalOutcomeV1.PREFLIGHT_BLOCKED:
            raise LifecycleContractError(ReasonCode.INVALID_CONTRACT, "all-PASS gates cannot report PREFLIGHT_BLOCKED")
        if not all_pass and self.terminal_outcome is not PreflightTerminalOutcomeV1.PREFLIGHT_BLOCKED:
            raise LifecycleContractError(ReasonCode.OPERATION_BLOCKED, "a non-PASS gate must fail closed")
        if not all_pass and self.outbox_intent_allowed:
            raise LifecycleContractError(ReasonCode.RUNTIME_EFFECT_FORBIDDEN, "blocked preflight cannot record an outbox intent")


@dataclass(frozen=True, slots=True)
class ClockFreshnessPolicyV1:
    policy_id: str
    ttl: timedelta
    maximum_clock_skew: timedelta
    maximum_source_age: timedelta

    def __post_init__(self) -> None:
        _required(self.policy_id, "policy_id")
        for field_name in ("ttl", "maximum_clock_skew", "maximum_source_age"):
            value = getattr(self, field_name)
            if not isinstance(value, timedelta) or value <= timedelta(0):
                raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"explicit positive {field_name} is required")


@dataclass(frozen=True, slots=True)
class ClockEvidenceV1:
    source_at: datetime | str
    event_at: datetime | str
    observed_at: datetime | str
    effective_at: datetime | str
    available_at: datetime | str
    received_at: datetime | str
    processed_at: datetime | str
    decision_at: datetime | str
    recorded_at: datetime | str
    monotonic_duration_ns: int

    def __post_init__(self) -> None:
        for name in (
            "source_at", "event_at", "observed_at", "effective_at", "available_at",
            "received_at", "processed_at", "decision_at", "recorded_at",
        ):
            object.__setattr__(self, name, parse_utc(getattr(self, name), field_name=name))
        if isinstance(self.monotonic_duration_ns, bool) or not isinstance(self.monotonic_duration_ns, int) or self.monotonic_duration_ns < 0:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "monotonic duration must be caller-supplied nonnegative integer")
        if not (
            self.available_at <= self.received_at <= self.processed_at <= self.decision_at <= self.recorded_at  # type: ignore[operator]
        ):
            raise LifecycleContractError(ReasonCode.FRESHNESS_VIOLATION, "local availability/processing timestamps are regressive")


@dataclass(frozen=True, slots=True)
class FreshnessClockReceiptV1:
    policy_ref: str
    evidence: ClockEvidenceV1
    source_age: timedelta
    source_clock_skew: timedelta
    availability_delay: timedelta
    monotonic_duration_ns: int
    disposition: GateDispositionV1 = GateDispositionV1.PASS

    def __post_init__(self) -> None:
        _required(self.policy_ref, "policy_ref")
        if not isinstance(self.evidence, ClockEvidenceV1) or self.disposition is not GateDispositionV1.PASS:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "freshness receipt must represent typed PASS evidence")
        for name in ("source_age", "source_clock_skew", "availability_delay"):
            if not isinstance(getattr(self, name), timedelta):
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be a timedelta")
        if self.monotonic_duration_ns != self.evidence.monotonic_duration_ns:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "monotonic duration receipt mismatch")


def validate_clock_freshness_v1(evidence: ClockEvidenceV1, policy: ClockFreshnessPolicyV1) -> FreshnessClockReceiptV1:
    if not isinstance(evidence, ClockEvidenceV1) or not isinstance(policy, ClockFreshnessPolicyV1):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "typed clock evidence and policy are required")
    source_age = evidence.decision_at - evidence.event_at  # type: ignore[operator]
    skew = abs(evidence.observed_at - evidence.source_at)  # type: ignore[operator]
    availability_delay = evidence.received_at - evidence.available_at  # type: ignore[operator]
    if source_age < -policy.maximum_clock_skew or source_age > policy.maximum_source_age or skew > policy.maximum_clock_skew:
        raise LifecycleContractError(ReasonCode.FRESHNESS_VIOLATION, "clock/source evidence is stale or skewed")
    if availability_delay < -policy.maximum_clock_skew:
        raise LifecycleContractError(ReasonCode.FRESHNESS_VIOLATION, "availability timestamp is future-inconsistent")
    if evidence.monotonic_duration_ns > int(policy.ttl.total_seconds() * 1_000_000_000):
        raise LifecycleContractError(ReasonCode.FRESHNESS_VIOLATION, "operation TTL expired")
    return FreshnessClockReceiptV1(
        policy.policy_id, evidence, source_age, skew, availability_delay, evidence.monotonic_duration_ns
    )


class RateLimitDispositionV1(StrEnum):
    ADMIT = "ADMIT"
    DEFER = "DEFER"
    REJECT = "REJECT"


@dataclass(frozen=True, slots=True)
class RateLimitAdmissionDecisionV1:
    disposition: RateLimitDispositionV1
    total_cost_units: Decimal
    remaining_units_after: Decimal
    next_eligible_at: datetime | None
    reason_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.disposition, RateLimitDispositionV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "rate-limit disposition must be typed")
        for name in ("total_cost_units", "remaining_units_after"):
            value = exact_decimal(getattr(self, name), field_name=name)
            if value < 0:
                raise ContractValidationError(ReasonCode.OUT_OF_DOMAIN, f"{name} must be nonnegative")
            object.__setattr__(self, name, value)
        if self.next_eligible_at is not None:
            object.__setattr__(self, "next_eligible_at", parse_utc(self.next_eligible_at, field_name="next_eligible_at"))
        _required(self.reason_code, "reason_code")


@dataclass(frozen=True, slots=True)
class RateLimitBudgetV1:
    budget_ref: str
    provider_ref: str
    account_scope_ref: str
    endpoint_ref: str
    window_ref: str
    source_binding_ref: str
    capacity_units: Decimal | str | int
    remaining_units: Decimal | str | int
    operation_costs: tuple[tuple[str, Decimal | str | int, Decimal | str | int], ...]
    operation_class: str
    item_count: int
    evaluated_at: datetime | str
    reset_at: datetime | str
    retry_after_until: datetime | str | None
    refill_units_per_second: Decimal | str | int | None
    admission_decision: RateLimitAdmissionDecisionV1 = field(init=False)

    def __post_init__(self) -> None:
        for name in ("budget_ref", "provider_ref", "account_scope_ref", "endpoint_ref", "window_ref", "source_binding_ref", "operation_class"):
            _required(getattr(self, name), name)
        capacity = exact_decimal(self.capacity_units, field_name="capacity_units")
        remaining = exact_decimal(self.remaining_units, field_name="remaining_units")
        if capacity <= 0 or remaining < 0 or remaining > capacity or not self.operation_costs:
            raise LifecycleContractError(ReasonCode.RATE_LIMIT_BUDGET_REQUIRED, "injected positive capacity, bounded remaining budget, and costs are required")
        if isinstance(self.item_count, bool) or not isinstance(self.item_count, int) or self.item_count < 1:
            raise LifecycleContractError(ReasonCode.RATE_LIMIT_BUDGET_REQUIRED, "item_count must be an explicit positive integer")
        costs: dict[str, tuple[Decimal, Decimal]] = {}
        for row in self.operation_costs:
            if not isinstance(row, tuple) or len(row) != 3:
                raise LifecycleContractError(ReasonCode.RATE_LIMIT_BUDGET_REQUIRED, "each operation cost requires base and per-item cost")
            name, base, per_item = row
            _required(name, "operation_cost.name")
            base_value = exact_decimal(base, field_name=f"operation_cost[{name}].base")
            item_value = exact_decimal(per_item, field_name=f"operation_cost[{name}].per_item")
            if name in costs or base_value < 0 or item_value < 0 or base_value + item_value <= 0:
                raise LifecycleContractError(ReasonCode.RATE_LIMIT_BUDGET_REQUIRED, "operation costs must be explicit, unique, and nonnegative with positive total")
            costs[name] = (base_value, item_value)
        if self.operation_class not in costs:
            raise LifecycleContractError(ReasonCode.RATE_LIMIT_BUDGET_REQUIRED, "operation class is absent from the injected budget")
        evaluated = parse_utc(self.evaluated_at, field_name="evaluated_at")
        reset = parse_utc(self.reset_at, field_name="reset_at")
        retry_after = None if self.retry_after_until is None else parse_utc(self.retry_after_until, field_name="retry_after_until")
        if reset <= evaluated:
            raise LifecycleContractError(ReasonCode.RATE_LIMIT_BUDGET_REQUIRED, "stale/reset budget requires a fresh injected binding")
        refill = None if self.refill_units_per_second is None else exact_decimal(self.refill_units_per_second, field_name="refill_units_per_second")
        if refill is not None and refill <= 0:
            raise LifecycleContractError(ReasonCode.RATE_LIMIT_BUDGET_REQUIRED, "refill rate must be positive when supplied")
        base_cost, item_cost = costs[self.operation_class]
        total_cost = base_cost + item_cost * Decimal(self.item_count)
        next_eligible: datetime | None = None
        if retry_after is not None and retry_after > evaluated:
            disposition = RateLimitDispositionV1.DEFER
            remaining_after = remaining
            next_eligible = retry_after
            reason = "RETRY_AFTER_ACTIVE"
        elif total_cost <= remaining:
            disposition = RateLimitDispositionV1.ADMIT
            remaining_after = remaining - total_cost
            reason = "INJECTED_BUDGET_ADMITS"
        else:
            disposition = RateLimitDispositionV1.DEFER
            remaining_after = remaining
            next_eligible = reset
            reason = "INSUFFICIENT_INJECTED_BUDGET"
            if refill is not None:
                deficit = total_cost - remaining
                microseconds = int((deficit * Decimal(1_000_000) / refill).to_integral_value(rounding=ROUND_CEILING))
                refill_at = evaluated + timedelta(microseconds=microseconds)
                next_eligible = min(reset, refill_at)
        object.__setattr__(self, "capacity_units", capacity)
        object.__setattr__(self, "remaining_units", remaining)
        object.__setattr__(self, "operation_costs", tuple((name, *costs[name]) for name, *_ in self.operation_costs))
        object.__setattr__(self, "evaluated_at", evaluated)
        object.__setattr__(self, "reset_at", reset)
        object.__setattr__(self, "retry_after_until", retry_after)
        object.__setattr__(self, "refill_units_per_second", refill)
        object.__setattr__(self, "admission_decision", RateLimitAdmissionDecisionV1(disposition, total_cost, remaining_after, next_eligible, reason))


CUSTODY_EVENT_CANDIDATE_STATES: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "ACK": frozenset({"ACKNOWLEDGED"}),
        "REJECT": frozenset({"REJECTED"}),
        "FILL": frozenset({"PARTIALLY_FILLED", "FILLED"}),
        "CANCEL": frozenset({"CANCELLED"}),
        "EXPIRY": frozenset({"EXPIRED"}),
        "TIMEOUT": frozenset({"UNKNOWN_RECONCILIATION_REQUIRED"}),
        "SETTLEMENT": frozenset({"SETTLED"}),
    }
)


@dataclass(frozen=True, slots=True)
class ExecutionCustodyReceiptV1:
    custody_receipt_id: str
    event_identity: str
    provider_request_ref: str
    economic_intent_ref: str
    attempt_ref: str
    provider_order_ref: str
    event_class: str
    source_payload_custody_ref: str
    effective_at: datetime | str
    recorded_at: datetime | str
    sequence_ref: str
    prior_state: str
    candidate_state: str
    authority_class: str

    def __post_init__(self) -> None:
        for field in fields(self):
            if field.name not in {"effective_at", "recorded_at"}:
                _required(getattr(self, field.name), field.name)
        if self.authority_class != "DETERMINISTIC_FIXTURE_ONLY":
            raise LifecycleContractError(ReasonCode.CAPABILITY_DENIED, "Tranche C cannot manufacture provider truth")
        if self.event_class not in CUSTODY_EVENT_CANDIDATE_STATES or self.candidate_state not in CUSTODY_EVENT_CANDIDATE_STATES[self.event_class]:
            raise LifecycleContractError(ReasonCode.ILLEGAL_STATE_TRANSITION, "custody event class and candidate state conflict")
        FUTURE_ORDER_CUSTODY_STATE_MACHINE_V1.validate(self.prior_state, self.candidate_state)
        object.__setattr__(self, "effective_at", parse_utc(self.effective_at, field_name="effective_at"))
        object.__setattr__(self, "recorded_at", parse_utc(self.recorded_at, field_name="recorded_at"))


@dataclass(frozen=True, slots=True)
class FillAccumulatorV1:
    order_quantity: Decimal | str | int
    accepted_fills: tuple[tuple[str, int, datetime | str, Decimal | str | int, str], ...] = ()

    def __post_init__(self) -> None:
        maximum = exact_decimal(self.order_quantity, field_name="order_quantity")
        if maximum <= 0:
            raise LifecycleContractError(ReasonCode.OUT_OF_DOMAIN, "order quantity must be positive")
        identities: dict[str, tuple[int, datetime, Decimal, str]] = {}
        sequences: dict[int, str] = {}
        total = Decimal(0)
        normalized = []
        for identity, sequence, effective_at, quantity, payload_json in self.accepted_fills:
            _required(identity, "fill identity")
            _required(payload_json, "fill payload")
            if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
                raise LifecycleContractError(ReasonCode.INVALID_CONTRACT, "fill sequence must be positive integer")
            when = parse_utc(effective_at, field_name="fill.effective_at")
            amount = exact_decimal(quantity, field_name="fill.quantity")
            if amount <= 0:
                raise LifecycleContractError(ReasonCode.OUT_OF_DOMAIN, "fill quantity must be positive")
            candidate = (sequence, when, amount, payload_json)
            if deterministic_json(safe_json_loads(payload_json)) != payload_json:
                raise LifecycleContractError(ReasonCode.INVALID_CONTRACT, "fill payload must be exact deterministic JSON text")
            if identity in identities:
                if identities[identity] != candidate:
                    raise LifecycleContractError(ReasonCode.DUPLICATE_EVENT_CONFLICT, "same fill identity has conflicting payload")
                continue
            if sequence in sequences:
                raise LifecycleContractError(ReasonCode.DUPLICATE_EVENT_CONFLICT, "distinct fills cannot claim the same declared sequence")
            identities[identity] = candidate
            sequences[sequence] = identity
            total += amount
            if total > maximum:
                raise LifecycleContractError(ReasonCode.OUT_OF_DOMAIN, "fills exceed remaining order quantity")
            normalized.append((identity, sequence, when, amount, payload_json))
        normalized.sort(key=lambda row: (row[1], row[2], row[0]))
        object.__setattr__(self, "order_quantity", maximum)
        object.__setattr__(self, "accepted_fills", tuple(normalized))

    @property
    def filled_quantity(self) -> Decimal:
        return sum((row[3] for row in self.accepted_fills), Decimal(0))

    @property
    def remaining_quantity(self) -> Decimal:
        return self.order_quantity - self.filled_quantity  # type: ignore[operator]


FINAL_RELEASE_AUTHORITY = "ExecutionRouterV1_FUTURE_SOLE_OWNER_NOT_IMPLEMENTED"
FORBIDDEN_EXECUTION_METHODS = frozenset({"submit", "cancel", "amend", "sign", "dispatch", "send"})


class ST12HFinalizationStateV1(StrEnum):
    """Exact non-runtime ST12-H implementation/publication custody states."""

    HELD = "HELD"
    PHASE0_VERIFIED_IMPLEMENTATION_HELD = "PHASE0_VERIFIED_IMPLEMENTATION_HELD"
    IMPLEMENTATION_AUTHORIZED = "IMPLEMENTATION_AUTHORIZED"
    IMPLEMENTATION_IN_PROGRESS = "IMPLEMENTATION_IN_PROGRESS"
    FOCUSED_VALIDATED = "FOCUSED_VALIDATED"
    GENERATED_STABLE = "GENERATED_STABLE"
    AFFECTED_SCOPE_VALIDATED = "AFFECTED_SCOPE_VALIDATED"
    FULL_LOCAL_VALIDATED = "FULL_LOCAL_VALIDATED"
    DRAFT_PR_OPEN = "DRAFT_PR_OPEN"
    INDEPENDENT_CODE_AUDIT_PENDING = "INDEPENDENT_CODE_AUDIT_PENDING"
    INDEPENDENT_CODE_AUDIT_PASS = "INDEPENDENT_CODE_AUDIT_PASS"
    MERGE_HELD = "MERGE_HELD"
    MERGED_MAIN_GREEN = "MERGED_MAIN_GREEN"
    OWNER_ACCEPTED = "OWNER_ACCEPTED"


ST12H_FINALIZATION_STATE_MACHINE_V1: Mapping[
    ST12HFinalizationStateV1,
    tuple[ST12HFinalizationStateV1, ...],
] = MappingProxyType(
    {
        ST12HFinalizationStateV1.HELD: (
            ST12HFinalizationStateV1.PHASE0_VERIFIED_IMPLEMENTATION_HELD,
        ),
        ST12HFinalizationStateV1.PHASE0_VERIFIED_IMPLEMENTATION_HELD: (
            ST12HFinalizationStateV1.IMPLEMENTATION_AUTHORIZED,
        ),
        ST12HFinalizationStateV1.IMPLEMENTATION_AUTHORIZED: (
            ST12HFinalizationStateV1.IMPLEMENTATION_IN_PROGRESS,
        ),
        ST12HFinalizationStateV1.IMPLEMENTATION_IN_PROGRESS: (
            ST12HFinalizationStateV1.FOCUSED_VALIDATED,
        ),
        ST12HFinalizationStateV1.FOCUSED_VALIDATED: (
            ST12HFinalizationStateV1.GENERATED_STABLE,
        ),
        ST12HFinalizationStateV1.GENERATED_STABLE: (
            ST12HFinalizationStateV1.AFFECTED_SCOPE_VALIDATED,
        ),
        ST12HFinalizationStateV1.AFFECTED_SCOPE_VALIDATED: (
            ST12HFinalizationStateV1.FULL_LOCAL_VALIDATED,
        ),
        ST12HFinalizationStateV1.FULL_LOCAL_VALIDATED: (
            ST12HFinalizationStateV1.DRAFT_PR_OPEN,
        ),
        ST12HFinalizationStateV1.DRAFT_PR_OPEN: (
            ST12HFinalizationStateV1.INDEPENDENT_CODE_AUDIT_PENDING,
        ),
        ST12HFinalizationStateV1.INDEPENDENT_CODE_AUDIT_PENDING: (
            ST12HFinalizationStateV1.INDEPENDENT_CODE_AUDIT_PASS,
        ),
        ST12HFinalizationStateV1.INDEPENDENT_CODE_AUDIT_PASS: (
            ST12HFinalizationStateV1.MERGE_HELD,
        ),
        ST12HFinalizationStateV1.MERGE_HELD: (),
        ST12HFinalizationStateV1.MERGED_MAIN_GREEN: (
            ST12HFinalizationStateV1.OWNER_ACCEPTED,
        ),
        ST12HFinalizationStateV1.OWNER_ACCEPTED: (),
    }
)


def validate_st12h_finalization_transition_v1(
    current: ST12HFinalizationStateV1,
    proposed: ST12HFinalizationStateV1,
    receipt_refs: tuple[str, ...],
) -> None:
    """Validate one explicit H custody transition without performing it."""

    if type(current) is not ST12HFinalizationStateV1 or type(proposed) is not ST12HFinalizationStateV1:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            "ST12-H transition states must be exact enum values",
        )
    if (
        not isinstance(receipt_refs, tuple)
        or not receipt_refs
        or len(set(receipt_refs)) != len(receipt_refs)
        or any(
            not isinstance(value, str)
            or not value
            or value != value.strip()
            for value in receipt_refs
        )
    ):
        raise ContractValidationError(
            ReasonCode.INCOMPLETE_CONTRACT,
            "ST12-H transitions require ordered unique canonical receipt refs",
        )
    if proposed not in ST12H_FINALIZATION_STATE_MACHINE_V1[current]:
        reason = (
            ReasonCode.LATER_TRANCHE_AUTHORITY_REQUIRED
            if current is ST12HFinalizationStateV1.MERGE_HELD
            or proposed is ST12HFinalizationStateV1.MERGED_MAIN_GREEN
            else ReasonCode.TRANSACTION_STATE_INVALID
        )
        raise ContractValidationError(
            reason,
            f"ST12-H transition {current.value}->{proposed.value} is not authorized",
        )
