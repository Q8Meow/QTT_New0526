"""Typed append-only receipt, event, and value-lineage contracts for Tranche C."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from .context import exact_decimal, parse_utc
from .errors import ContractValidationError, ReasonCode
from .models import ComputationExecutionReceiptV1


def _required(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{name} is required")


def _identifier_tuple(value: object, name: str, *, allow_empty: bool = True) -> None:
    if not isinstance(value, tuple) or any(not isinstance(item, str) or not item for item in value):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be a string tuple")
    if not allow_empty and not value:
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{name} must not be empty")
    if len(value) != len(set(value)):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be unique")


def _time(value: datetime | str, name: str) -> datetime:
    return parse_utc(value, field_name=name)


def _canonical_decimal_text(value: str, name: str) -> None:
    _required(value, name)
    if str(exact_decimal(value, field_name=name)) != value:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be canonical Decimal text")


def _require_declared_scale(value: str, scale: int, name: str) -> None:
    if isinstance(scale, bool) or not isinstance(scale, int) or scale < 0:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "scale must be nonnegative integer")
    if exact_decimal(value, field_name=name).as_tuple().exponent != -scale:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{name} precision does not match its declared scale",
        )


@dataclass(frozen=True, slots=True)
class NoEffectFlagsV1:
    provider_connection_allowed: bool = False
    private_state_read_allowed: bool = False
    replay_or_paper_execution_allowed: bool = False
    llm_inference_allowed: bool = False
    qpu_execution_allowed: bool = False
    mode_or_allow_activation_allowed: bool = False
    order_release_allowed: bool = False
    capital_mutation_allowed: bool = False

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not bool or value:
                raise ContractValidationError(
                    ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                    f"Tranche-C no-effect flag {field.name} must be exact false",
                )


NO_EFFECTS_V1 = NoEffectFlagsV1()


class EconomicRecordTypeV1(StrEnum):
    DURABLE_COMPUTATION_RECEIPT = "DURABLE_COMPUTATION_RECEIPT"
    ECONOMIC_EVENT = "ECONOMIC_EVENT"
    JOURNAL_TRANSACTION = "JOURNAL_TRANSACTION"
    JOURNAL_POSTING = "JOURNAL_POSTING"
    STATE_TRANSITION = "STATE_TRANSITION"
    IDEMPOTENCY_CLAIM = "IDEMPOTENCY_CLAIM"
    OUTBOX_INTENT = "OUTBOX_INTENT"
    REVERSAL = "REVERSAL"
    RECONCILIATION_BREAK = "RECONCILIATION_BREAK"
    ORDER_INTENT = "ORDER_INTENT"
    EXECUTION_CUSTODY = "EXECUTION_CUSTODY"


ECONOMIC_RECORD_PAYLOAD_CLASS: Mapping[EconomicRecordTypeV1, tuple[str, str]] = MappingProxyType(
    {
        EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT: ("receipts", "DurableComputationExecutionReceiptRecordV1"),
        EconomicRecordTypeV1.ECONOMIC_EVENT: ("receipts", "EconomicEventRecordV1"),
        EconomicRecordTypeV1.JOURNAL_TRANSACTION: ("accounting", "JournalTransactionV1"),
        EconomicRecordTypeV1.JOURNAL_POSTING: ("accounting", "JournalPostingV1"),
        EconomicRecordTypeV1.STATE_TRANSITION: ("lifecycle", "StateTransitionReceiptV1"),
        EconomicRecordTypeV1.IDEMPOTENCY_CLAIM: ("idempotency", "IdempotencyClaimReceiptV1"),
        EconomicRecordTypeV1.OUTBOX_INTENT: ("outbox", "OutboxIntentRecordV1"),
        EconomicRecordTypeV1.REVERSAL: ("rollback", "ReversalReceiptV1"),
        EconomicRecordTypeV1.RECONCILIATION_BREAK: ("accounting", "ReconciliationBreakReceiptV1"),
        EconomicRecordTypeV1.ORDER_INTENT: ("lifecycle", "OrderIntentRecordV1"),
        EconomicRecordTypeV1.EXECUTION_CUSTODY: ("lifecycle", "ExecutionCustodyReceiptV1"),
    }
)


@dataclass(frozen=True, slots=True)
class EconomicReceiptEventSpineV1:
    record_id: str
    record_type: EconomicRecordTypeV1
    schema_version: str
    semantic_owner: str
    implementation_owner: str
    context_ref: str
    effective_at: datetime | str
    recorded_at: datetime | str
    causation_id: str
    correlation_id: str
    traceparent: str
    tracestate: str
    sequence: int
    aggregate_id: str
    aggregate_version: int
    authority_class: str
    typed_payload: object
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        for name in (
            "record_id", "schema_version", "semantic_owner", "implementation_owner",
            "context_ref", "causation_id", "correlation_id", "traceparent", "tracestate",
            "aggregate_id", "authority_class",
        ):
            _required(getattr(self, name), name)
        if not isinstance(self.record_type, EconomicRecordTypeV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "record_type must be allowlisted")
        if self.causation_id == self.correlation_id:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "causation and correlation identities must remain distinct")
        if self.traceparent in {self.record_id, self.aggregate_id, self.causation_id, self.correlation_id}:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "trace context cannot be economic identity")
        for name in ("sequence", "aggregate_version"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be nonnegative integer")
        expected_module, expected_class = ECONOMIC_RECORD_PAYLOAD_CLASS[self.record_type]
        if (
            type(self.typed_payload).__name__ != expected_class
            or type(self.typed_payload).__module__.rsplit(".", 1)[-1] != expected_module
        ):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "record discriminator/payload type mismatch")
        if not isinstance(self.no_effect_flags, NoEffectFlagsV1):
            raise ContractValidationError(ReasonCode.RUNTIME_EFFECT_FORBIDDEN, "typed no-effect flags are required")
        object.__setattr__(self, "effective_at", _time(self.effective_at, "effective_at"))
        object.__setattr__(self, "recorded_at", _time(self.recorded_at, "recorded_at"))


@dataclass(frozen=True, slots=True)
class DurableComputationExecutionReceiptRecordV1:
    record_id: str
    existing_receipt: ComputationExecutionReceiptV1
    execution_context_ref: str
    input_snapshot_ref: str
    input_value_lineage_refs: tuple[str, ...]
    dependency_receipt_refs: tuple[str, ...]
    started_at: datetime | str
    completed_at: datetime | str
    latency_ns: int
    output_unit: str
    output_basis: str
    accounting_class: str
    fallback_used: bool
    warning_codes: tuple[str, ...]
    failure_code: str | None
    consumer_ref: str
    mode_ref: str
    no_order_authority_flag: bool = True

    def __post_init__(self) -> None:
        for name in (
            "record_id", "execution_context_ref", "input_snapshot_ref", "output_unit",
            "output_basis", "accounting_class", "consumer_ref", "mode_ref",
        ):
            _required(getattr(self, name), name)
        if type(self.existing_receipt) is not ComputationExecutionReceiptV1:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "existing_receipt must be exact ComputationExecutionReceiptV1")
        _identifier_tuple(self.input_value_lineage_refs, "input_value_lineage_refs", allow_empty=False)
        _identifier_tuple(self.dependency_receipt_refs, "dependency_receipt_refs")
        _identifier_tuple(self.warning_codes, "warning_codes")
        if self.failure_code is not None:
            _required(self.failure_code, "failure_code")
        if isinstance(self.latency_ns, bool) or not isinstance(self.latency_ns, int) or self.latency_ns < 0:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "latency_ns must be nonnegative integer")
        if type(self.fallback_used) is not bool or self.no_order_authority_flag is not True:
            raise ContractValidationError(ReasonCode.RUNTIME_EFFECT_FORBIDDEN, "receipt must retain no-order authority")
        started = _time(self.started_at, "started_at")
        completed = _time(self.completed_at, "completed_at")
        if completed < started:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "completed_at precedes started_at")
        object.__setattr__(self, "started_at", started)
        object.__setattr__(self, "completed_at", completed)


@dataclass(frozen=True, slots=True)
class TypedEconomicAmountV1:
    amount_text: str
    currency_or_asset: str
    ledger_unit: str
    basis: str
    scale: int
    rounding_policy_ref: str

    def __post_init__(self) -> None:
        for name in ("amount_text", "currency_or_asset", "ledger_unit", "basis", "rounding_policy_ref"):
            _required(getattr(self, name), name)
        _canonical_decimal_text(self.amount_text, "amount_text")
        _require_declared_scale(self.amount_text, self.scale, "amount_text")


@dataclass(frozen=True, slots=True)
class EconomicEventRecordV1:
    economic_event_id: str
    event_class: str
    semantic_owner: str
    aggregate_id: str
    event_sequence: int
    effective_at: datetime | str
    recorded_at: datetime | str
    source_record_refs: tuple[str, ...]
    typed_amounts: tuple[TypedEconomicAmountV1, ...]
    lifecycle_state_before: str
    lifecycle_state_after: str
    authority_class: str

    def __post_init__(self) -> None:
        for name in ("economic_event_id", "event_class", "semantic_owner", "aggregate_id", "lifecycle_state_before", "lifecycle_state_after", "authority_class"):
            _required(getattr(self, name), name)
        if isinstance(self.event_sequence, bool) or not isinstance(self.event_sequence, int) or self.event_sequence < 0:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "event_sequence must be nonnegative integer")
        _identifier_tuple(self.source_record_refs, "source_record_refs")
        if not isinstance(self.typed_amounts, tuple) or any(not isinstance(row, TypedEconomicAmountV1) for row in self.typed_amounts):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "typed_amounts must contain typed amounts")
        if not self.source_record_refs:
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "economic event source lineage is required")
        if self.event_class not in {"NO_FILL", "PREFLIGHT_BLOCKED", "NO_ECONOMIC_EFFECT", "ORDER_INTENT"} and not self.typed_amounts:
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "economic-effect event requires at least one typed amount")
        if "PROVIDER" in self.authority_class.upper():
            raise ContractValidationError(ReasonCode.CAPABILITY_DENIED, "Tranche C cannot manufacture provider-origin economic truth")
        object.__setattr__(self, "effective_at", _time(self.effective_at, "effective_at"))
        object.__setattr__(self, "recorded_at", _time(self.recorded_at, "recorded_at"))


@dataclass(frozen=True, slots=True)
class ValueLineageNodeV1:
    value_node_id: str
    record_ref: str
    field_id: str
    value_text: str
    value_kind: str
    unit: str
    basis: str
    currency_or_asset: str
    scale: int
    effective_at: datetime | str
    recorded_at: datetime | str
    source_authority_class: str

    def __post_init__(self) -> None:
        for name in ("value_node_id", "record_ref", "field_id", "value_text", "value_kind", "unit", "basis", "currency_or_asset", "source_authority_class"):
            _required(getattr(self, name), name)
        _canonical_decimal_text(self.value_text, "value_text")
        _require_declared_scale(self.value_text, self.scale, "value_text")
        object.__setattr__(self, "effective_at", _time(self.effective_at, "effective_at"))
        object.__setattr__(self, "recorded_at", _time(self.recorded_at, "recorded_at"))


@dataclass(frozen=True, slots=True)
class ValueLineageEdgeV1:
    lineage_edge_id: str
    producer_record_id: str
    producer_field_id: str
    consumer_record_id: str
    consumer_field_id: str
    source_value_text: str
    target_value_text: str
    source_unit: str
    target_unit: str
    source_basis: str
    target_basis: str
    transformation_id: str
    materiality_class: str
    effective_at: datetime | str
    recorded_at: datetime | str
    causation_id: str
    correlation_id: str
    producer_node_id: str
    consumer_node_id: str
    conversion_policy_ref: str

    def __post_init__(self) -> None:
        for name in (
            "lineage_edge_id", "producer_record_id", "producer_field_id", "consumer_record_id",
            "consumer_field_id", "source_value_text", "target_value_text", "source_unit",
            "target_unit", "source_basis", "target_basis", "transformation_id",
            "materiality_class", "causation_id", "correlation_id",
        ):
            _required(getattr(self, name), name)
        _canonical_decimal_text(self.source_value_text, "source_value_text")
        _canonical_decimal_text(self.target_value_text, "target_value_text")
        for name in ("producer_node_id", "consumer_node_id", "conversion_policy_ref"):
            _required(getattr(self, name), name)
        if self.producer_record_id == self.consumer_record_id and self.producer_field_id == self.consumer_field_id:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "lineage self-cycle is forbidden")
        if self.causation_id == self.correlation_id:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "causation and correlation must be distinct")
        transformation_class = VALUE_TRANSFORMATION_REGISTRY_V1.get(self.transformation_id)
        if transformation_class is None:
            raise ContractValidationError(ReasonCode.UNKNOWN_IMPLEMENTATION, "lineage transformation is not centrally registered")
        if transformation_class == "IDENTITY":
            if (
                self.source_value_text != self.target_value_text
                or self.source_unit != self.target_unit
                or self.source_basis != self.target_basis
                or self.conversion_policy_ref != "IDENTITY_NO_CONVERSION"
            ):
                raise ContractValidationError(ReasonCode.UNIT_BASIS_MISMATCH, "identity lineage cannot convert or mutate a value")
        elif transformation_class == "UNIT_CONVERSION" and (
            self.source_unit == self.target_unit or self.source_basis != self.target_basis
        ):
            raise ContractValidationError(ReasonCode.UNIT_BASIS_MISMATCH, "unit conversion lineage must change only the declared unit")
        elif transformation_class == "BASIS_CONVERSION" and (
            self.source_basis == self.target_basis or self.source_unit != self.target_unit
        ):
            raise ContractValidationError(ReasonCode.UNIT_BASIS_MISMATCH, "basis conversion lineage must change only the declared basis")
        object.__setattr__(self, "effective_at", _time(self.effective_at, "effective_at"))
        object.__setattr__(self, "recorded_at", _time(self.recorded_at, "recorded_at"))


@dataclass(frozen=True, slots=True)
class CausalLineageV1:
    causation_id: str
    correlation_id: str
    traceparent: str
    tracestate: str
    linked_record_refs: tuple[str, ...]
    relationship_classes: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("causation_id", "correlation_id", "traceparent", "tracestate"):
            _required(getattr(self, name), name)
        if self.causation_id == self.correlation_id or self.traceparent in {self.causation_id, self.correlation_id}:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "trace/correlation/causation identities must remain distinct")
        _identifier_tuple(self.linked_record_refs, "linked_record_refs", allow_empty=False)
        _identifier_tuple(self.relationship_classes, "relationship_classes", allow_empty=False)


@dataclass(frozen=True, slots=True)
class BitemporalLineageV1:
    record_id: str
    effective_at: datetime | str
    recorded_at: datetime | str
    supersedes_ref: str | None = None
    correction_ref: str | None = None
    source_revision_ref: str | None = None

    def __post_init__(self) -> None:
        _required(self.record_id, "record_id")
        for name in ("supersedes_ref", "correction_ref", "source_revision_ref"):
            value = getattr(self, name)
            if value is not None:
                _required(value, name)
        object.__setattr__(self, "effective_at", _time(self.effective_at, "effective_at"))
        object.__setattr__(self, "recorded_at", _time(self.recorded_at, "recorded_at"))


@dataclass(frozen=True, slots=True)
class LineageReconstructionV1:
    reconstruction_id: str
    effective_cutoff: datetime | str
    recorded_cutoff: datetime | str
    aggregate_scope: tuple[str, ...]
    included_record_refs: tuple[str, ...]
    excluded_late_record_refs: tuple[str, ...]
    projection_version: str

    def __post_init__(self) -> None:
        _required(self.reconstruction_id, "reconstruction_id")
        _required(self.projection_version, "projection_version")
        _identifier_tuple(self.aggregate_scope, "aggregate_scope", allow_empty=False)
        _identifier_tuple(self.included_record_refs, "included_record_refs")
        _identifier_tuple(self.excluded_late_record_refs, "excluded_late_record_refs")
        if set(self.included_record_refs) & set(self.excluded_late_record_refs):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "a record cannot be included and excluded")
        object.__setattr__(self, "effective_cutoff", _time(self.effective_cutoff, "effective_cutoff"))
        object.__setattr__(self, "recorded_cutoff", _time(self.recorded_cutoff, "recorded_cutoff"))


def validate_lineage_acyclic_v1(edges: tuple[ValueLineageEdgeV1, ...]) -> None:
    """Reject a cyclic producer-to-consumer value graph deterministically."""

    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        producer = edge.producer_node_id
        consumer = edge.consumer_node_id
        adjacency.setdefault(producer, set()).add(consumer)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "value-lineage graph is cyclic")
        if node in visited:
            return
        visiting.add(node)
        for child in sorted(adjacency.get(node, ())):
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(adjacency):
        visit(node)


VALUE_TRANSFORMATION_REGISTRY_V1: Mapping[str, str] = MappingProxyType(
    {
        "IDENTITY": "IDENTITY",
        "EXPLICIT_UNIT_CONVERSION": "UNIT_CONVERSION",
        "EXPLICIT_BASIS_CONVERSION": "BASIS_CONVERSION",
        "QUANTIZATION": "QUANTIZATION",
        **{f"MATH-{number}": "REGISTERED_FORMULA" for number in range(26, 39)},
    }
)
