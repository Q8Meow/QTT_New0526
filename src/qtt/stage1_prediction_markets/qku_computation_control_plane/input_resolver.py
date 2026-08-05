"""Strict formula-input and runtime-parameter owner-packet resolution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum
import math
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .bindings import (
    CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
    FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
    FormulaInputAdmissionClassV1,
    FormulaInputAuthorityBindingV1,
    ST12DMath39RawInputBindingV1,
)
from .context import (
    exact_decimal,
    finite_float,
)
from .errors import (
    FreshnessError,
    InputAuthorityError,
    NumericDomainError,
    PointInTimeError,
    ReasonCode,
)
from .freshness import (
    FreshnessPolicyV1,
    FreshnessReceiptV1,
    FreshnessResolverV1,
)
from .point_in_time import (
    PointInTimeClocksV1,
    PointInTimeFieldClassV1,
    PointInTimePolicyV1,
    PointInTimeReceiptV1,
    classify_point_in_time_semantics,
)
from .models import (
    ComputationExecutionContextV1,
    ComputationScopeV1,
    ImplementationVersionPinV1,
    OwnerActionConfirmationReceiptV1,
    ReadOnlyKillSubmitStateV1,
    ST12FEvidenceReferenceV1,
)
from .specification import FROZEN_FORMULA_REQUIREMENTS


def _freeze(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType(
            {str(key): _freeze(item) for key, item in value.items()}
        )
    if isinstance(value, list | tuple):
        return tuple(_freeze(item) for item in value)
    return value


def thaw_input(value: object) -> object:
    """Return a private mutable call value without changing authoritative state."""

    if isinstance(value, Mapping):
        return {str(key): thaw_input(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_input(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class OwnerValuePacketV1:
    packet_id: str
    owner_id: str
    packet_type: str
    schema_id: str
    schema_version: str
    context_id: str
    scope: ComputationScopeV1
    source_epoch_id: str
    input_version: str
    clocks: PointInTimeClocksV1
    ttl: timedelta
    values: Mapping[str, object]
    authorized_binding_ids: tuple[str, ...]
    producer_receipt_id: str
    producer_receipt_type: str
    source_state_and_claim_lineage: str
    provider_sequence: int | str | None = None
    revision: int | str | None = None
    prior_revision_available_time: object | None = None
    source_conflict: bool = False

    def __post_init__(self) -> None:
        required = (
            self.packet_id,
            self.owner_id,
            self.packet_type,
            self.schema_id,
            self.schema_version,
            self.context_id,
            self.source_epoch_id,
            self.input_version,
            self.producer_receipt_id,
            self.producer_receipt_type,
            self.source_state_and_claim_lineage,
        )
        if any(not isinstance(value, str) or not value for value in required):
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "owner packet identity and lineage fields are required",
            )
        if type(self.scope) is not ComputationScopeV1:
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "owner packet requires an exact ComputationScopeV1",
            )
        if self.input_version != self.input_version.strip():
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "owner packet input_version must be canonical text",
            )
        if not isinstance(self.clocks, PointInTimeClocksV1):
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "owner packet requires typed six-clock point-in-time state",
            )
        if not isinstance(self.ttl, timedelta) or self.ttl <= timedelta(0):
            raise InputAuthorityError(
                ReasonCode.FRESHNESS_VIOLATION,
                "owner packet TTL must be positive",
            )
        if (
            not isinstance(self.values, Mapping)
            or not self.values
            or not isinstance(self.authorized_binding_ids, tuple)
            or not self.authorized_binding_ids
            or len(self.authorized_binding_ids)
            != len(set(self.authorized_binding_ids))
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "owner packet needs values and exact unique binding identities",
            )
        if type(self.source_conflict) is not bool:
            raise InputAuthorityError(
                ReasonCode.SOURCE_CONFLICT,
                "source conflict state must be an exact boolean",
            )
        object.__setattr__(self, "values", _freeze(dict(self.values)))


@dataclass(frozen=True, slots=True)
class ResolvedFormulaInputV1:
    binding_id: str
    math_spec_id: str
    input_name: str
    value: object
    owner_id: str
    packet_id: str
    field_path: str
    point_in_time_receipt: PointInTimeReceiptV1
    freshness_receipt: FreshnessReceiptV1
    producer_receipt_id: str


@dataclass(frozen=True, slots=True)
class FormulaInputResolutionV1:
    math_spec_id: str
    execution_context: ComputationExecutionContextV1
    inputs: tuple[ResolvedFormulaInputV1, ...]
    authoritative_values: Mapping[str, object]
    packet_refs: tuple[str, ...]
    receipt_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not self.math_spec_id
            or not isinstance(
                self.execution_context, ComputationExecutionContextV1
            )
            or not self.inputs
            or len({row.input_name for row in self.inputs}) != len(self.inputs)
            or tuple(self.authoritative_values)
            != tuple(row.input_name for row in self.inputs)
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                "resolved formula inputs are incomplete or out of declared order",
            )

    @property
    def context_id(self) -> str:
        return self.execution_context.context_id


class Math39BookEventKindV1(StrEnum):
    DISPLAYED_BEFORE_ORDER = "DISPLAYED_BEFORE_ORDER"
    PRIOR_ADDITION = "PRIOR_ADDITION"
    PRIOR_CANCELLATION = "PRIOR_CANCELLATION"
    TRADE_AHEAD = "TRADE_AHEAD"


def _math39_utc(value: object, name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
        or value.utcoffset().total_seconds() != 0
    ):
        raise InputAuthorityError(
            ReasonCode.POINT_IN_TIME_VIOLATION,
            f"MATH-39 {name} must be an aware UTC timestamp",
        )
    return value


def _math39_decimal(value: object, name: str, *, nonnegative: bool) -> Decimal:
    if (
        not isinstance(value, Decimal)
        or isinstance(value, bool)
        or not value.is_finite()
        or nonnegative
        and value < 0
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_VALUE_CONFLICT,
            f"MATH-39 {name} must be an exact finite"
            + (" nonnegative" if nonnegative else "")
            + " Decimal",
        )
    return value


@dataclass(frozen=True, slots=True)
class Math39OrderAcknowledgementV1:
    order_id: str
    venue_id: str
    instrument_id: str
    side: str
    price: Decimal
    acknowledged_at: datetime
    available_at: datetime
    matching_priority: str
    venue_evidence_ref: str
    unit: str
    basis: str
    producer_receipt_ref: str

    def __post_init__(self) -> None:
        for name in (
            "order_id",
            "venue_id",
            "instrument_id",
            "side",
            "matching_priority",
            "venue_evidence_ref",
            "unit",
            "basis",
            "producer_receipt_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or value != value.strip():
                raise InputAuthorityError(
                    ReasonCode.INPUT_PACKET_MISMATCH,
                    f"MATH-39 acknowledgement {name} must be canonical text",
                )
        _math39_decimal(self.price, "acknowledgement price", nonnegative=True)
        acknowledged = _math39_utc(self.acknowledged_at, "acknowledged_at")
        available = _math39_utc(self.available_at, "ack available_at")
        if acknowledged > available:
            raise InputAuthorityError(
                ReasonCode.POINT_IN_TIME_VIOLATION,
                "MATH-39 acknowledgement cannot be available before its event time",
            )
        if self.matching_priority != "PRICE_TIME_FIFO":
            raise InputAuthorityError(
                ReasonCode.MATCHING_PRIORITY_UNKNOWN,
                "MATH-39 acknowledgement lacks exact matching-priority evidence",
            )
        if self.unit != "units" or self.basis != "ACKNOWLEDGED_INSERTION_POINT":
            raise InputAuthorityError(
                ReasonCode.UNIT_BASIS_OR_PRECISION_INVALID,
                "MATH-39 acknowledgement lacks exact unit/basis evidence",
            )


@dataclass(frozen=True, slots=True)
class Math39SequencedBookEventV1:
    event_id: str
    sequence: int
    event_kind: Math39BookEventKindV1
    venue_id: str
    instrument_id: str
    side: str
    price: Decimal
    quantity: Decimal
    event_time: datetime
    available_at: datetime
    priority_order_id: str
    venue_evidence_ref: str
    unit: str
    basis: str
    producer_receipt_ref: str
    ahead_of_order: bool = True

    def __post_init__(self) -> None:
        for name in (
            "event_id",
            "venue_id",
            "instrument_id",
            "side",
            "priority_order_id",
            "venue_evidence_ref",
            "unit",
            "basis",
            "producer_receipt_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or value != value.strip():
                raise InputAuthorityError(
                    ReasonCode.INPUT_PACKET_MISMATCH,
                    f"MATH-39 book event {name} must be canonical text",
                )
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int):
            raise InputAuthorityError(
                ReasonCode.SEQUENCE_GAP,
                "MATH-39 sequence must be an exact integer",
            )
        if type(self.event_kind) is not Math39BookEventKindV1:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "MATH-39 event kind must be the exact finite enum",
            )
        _math39_decimal(self.price, "event price", nonnegative=True)
        _math39_decimal(self.quantity, "event quantity", nonnegative=True)
        event_time = _math39_utc(self.event_time, "event_time")
        available = _math39_utc(self.available_at, "event available_at")
        if event_time > available:
            raise InputAuthorityError(
                ReasonCode.POINT_IN_TIME_VIOLATION,
                "MATH-39 event cannot be available before occurrence",
            )
        if (
            self.unit != "units"
            or self.basis != "ACKNOWLEDGED_INSERTION_POINT"
            or self.ahead_of_order is not True
        ):
            raise InputAuthorityError(
                ReasonCode.UNIT_BASIS_OR_PRECISION_INVALID,
                "MATH-39 events require exact ahead-of-order unit/basis custody",
            )


@dataclass(frozen=True, slots=True)
class ResolvedRuntimeParameterValueV1:
    binding_id: str
    parameter_id: str
    parameter_symbol: str
    value: object
    unit_or_basis: str
    owner_id: str
    packet_id: str
    field_path: str
    point_in_time_receipt: PointInTimeReceiptV1
    freshness_receipt: FreshnessReceiptV1
    producer_receipt_id: str

    def __post_init__(self) -> None:
        if (
            self.binding_id != f"RPVOB::{self.parameter_id}"
            or not self.parameter_symbol
            or not self.unit_or_basis
            or not self.owner_id
            or not self.packet_id
            or not self.field_path
            or not self.producer_receipt_id
        ):
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                "resolved runtime parameter identity or lineage is incomplete",
            )


@dataclass(frozen=True, slots=True)
class RuntimeParameterValueResolutionV1:
    parameter_id: str
    execution_context: ComputationExecutionContextV1
    resolved: ResolvedRuntimeParameterValueV1
    receipt_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            not self.parameter_id
            or not isinstance(
                self.execution_context, ComputationExecutionContextV1
            )
            or self.resolved.parameter_id != self.parameter_id
            or self.receipt_refs
            != (
                self.resolved.producer_receipt_id,
                self.resolved.point_in_time_receipt.receipt_id,
                self.resolved.freshness_receipt.receipt_id,
            )
        ):
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                "runtime parameter resolution receipt is inconsistent",
            )

    @property
    def context_id(self) -> str:
        return self.execution_context.context_id


class CanonicalOwnerPacketRegistryV1:
    """Immutable local view of canonical owners; requests cannot add/select owners."""

    def __init__(self, packets: tuple[OwnerValuePacketV1, ...] = ()) -> None:
        if (
            not isinstance(packets, tuple)
            or any(not isinstance(packet, OwnerValuePacketV1) for packet in packets)
            or len({packet.packet_id for packet in packets}) != len(packets)
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "owner packet registry requires unique typed immutable packets",
            )
        by_binding: dict[tuple[object, ...], list[OwnerValuePacketV1]] = {}
        by_context_binding: dict[
            tuple[str, str], list[OwnerValuePacketV1]
        ] = {}
        for packet in packets:
            for binding_id in packet.authorized_binding_ids:
                by_binding.setdefault(
                    self._packet_binding_key(packet, binding_id), []
                ).append(packet)
                by_context_binding.setdefault(
                    (packet.context_id, binding_id), []
                ).append(packet)
        if any(len(rows) != 1 for rows in by_binding.values()):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                "canonical registry has conflicting packets for one exact scope/version binding",
            )
        self._packets = packets
        self._by_id = MappingProxyType(
            {packet.packet_id: packet for packet in packets}
        )
        self._by_binding = MappingProxyType(
            {key: rows[0] for key, rows in by_binding.items()}
        )
        self._by_context_binding = MappingProxyType(
            {key: tuple(rows) for key, rows in by_context_binding.items()}
        )

    @staticmethod
    def _packet_binding_key(
        packet: OwnerValuePacketV1,
        binding_id: str,
    ) -> tuple[object, ...]:
        return (
            packet.context_id,
            packet.clocks.as_of_time,
            packet.source_epoch_id,
            packet.input_version,
            packet.scope.identity_tuple,
            binding_id,
        )

    @staticmethod
    def _context_binding_key(
        context: ComputationExecutionContextV1,
        binding_id: str,
    ) -> tuple[object, ...]:
        return (
            context.context_id,
            context.as_of,
            context.source_epoch_id,
            context.input_version,
            context.scope.identity_tuple,
            binding_id,
        )

    @property
    def packets(self) -> tuple[OwnerValuePacketV1, ...]:
        return self._packets

    def packet_for(
        self,
        *,
        context: ComputationExecutionContextV1,
        binding_id: str,
    ) -> OwnerValuePacketV1:
        if not isinstance(context, ComputationExecutionContextV1):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "packet lookup requires ComputationExecutionContextV1",
            )
        try:
            return self._by_binding[
                self._context_binding_key(context, binding_id)
            ]
        except KeyError as exc:
            candidates = self._by_context_binding.get(
                (context.context_id, binding_id), ()
            )
            if any(
                packet.scope == context.scope
                and packet.input_version == context.input_version
                and packet.source_epoch_id == context.source_epoch_id
                for packet in candidates
            ):
                raise PointInTimeError(
                    ReasonCode.POINT_IN_TIME_VIOLATION,
                    f"{binding_id} packet as_of differs from the execution context",
                ) from exc
            if any(
                packet.scope == context.scope
                and packet.input_version == context.input_version
                and packet.clocks.as_of_time == context.as_of
                for packet in candidates
            ):
                raise FreshnessError(
                    ReasonCode.SOURCE_EPOCH_STALE,
                    f"{binding_id} packet source epoch differs from the execution context",
                ) from exc
            if candidates:
                raise InputAuthorityError(
                    ReasonCode.INPUT_SCOPE_MISMATCH,
                    f"{binding_id} packet scope or input version differs",
                ) from exc
            raise InputAuthorityError(
                ReasonCode.INPUT_OWNER_MISSING,
                f"canonical owner packet is absent for {binding_id}",
            ) from exc

    def packet_by_id(self, packet_id: str) -> OwnerValuePacketV1:
        try:
            return self._by_id[packet_id]
        except KeyError as exc:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                f"owner packet identity is absent: {packet_id}",
            ) from exc

    def with_internal_computation_receipt(
        self, packet: OwnerValuePacketV1
    ) -> CanonicalOwnerPacketRegistryV1:
        if (
            packet.owner_id != "QKUComputationControlPlaneV1.MATH-01"
            or packet.packet_type != "ComputationExecutionReceiptV1::MATH-01"
            or packet.schema_id
            != "ComputationExecutionReceiptV1::MATH-01::SCHEMA"
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_OWNER_MISMATCH,
                "only the exact registered MATH-01 dependency receipt may be added",
            )
        return CanonicalOwnerPacketRegistryV1((*self._packets, packet))


def _extract(values: Mapping[str, object], field_path: str) -> object:
    if field_path in values:
        return values[field_path]
    current: object = values
    for token in field_path.split("."):
        if not isinstance(current, Mapping) or token not in current:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                f"owner packet lacks exact field path {field_path}",
            )
        current = current[token]
    return current


def _parse_typed(value: object, binding: FormulaInputAuthorityBindingV1) -> object:
    token = binding.input_type.casefold()
    try:
        if token == "decimal string" or "decimal string" in token and not (
            "list" in token or "vector" in token
        ):
            return exact_decimal(value, field_name=binding.input_name)  # type: ignore[arg-type]
        if token in {"float64", "float"}:
            return finite_float(value, field_name=binding.input_name)  # type: ignore[arg-type]
    except NumericDomainError as exc:
        raise InputAuthorityError(
            ReasonCode.INPUT_VALUE_CONFLICT,
            f"{binding.input_name} failed canonical numeric extraction",
        ) from exc
    if token in {"int", "integer"}:
        if isinstance(value, bool) or not isinstance(value, int):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be an exact integer",
            )
        return value
    if token in {"bool", "boolean"}:
        if type(value) is not bool:
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be an exact boolean",
            )
        return value
    if token in {"enum", "str", "string"}:
        if not isinstance(value, str) or not value:
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be nonempty exact text",
            )
        return value
    if token in {"decimal string list", "list[decimal string]"}:
        if not isinstance(value, list | tuple):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be a Decimal-string list",
            )
        try:
            return tuple(
                exact_decimal(item, field_name=binding.input_name)  # type: ignore[arg-type]
                for item in value
            )
        except NumericDomainError as exc:
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} contains a noncanonical Decimal",
            ) from exc
    if token == "list[float64]":
        if not isinstance(value, list | tuple):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be a float64 list",
            )
        try:
            return tuple(
                finite_float(item, field_name=binding.input_name)  # type: ignore[arg-type]
                for item in value
            )
        except NumericDomainError as exc:
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} contains a nonfinite float64",
            ) from exc
    if token == "list[list[float64]]":
        if not isinstance(value, list | tuple) or any(
            not isinstance(row, list | tuple) for row in value
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be a nested float64 list",
            )
        try:
            return tuple(
                tuple(
                    finite_float(item, field_name=binding.input_name)  # type: ignore[arg-type]
                    for item in row
                )
                for row in value
            )
        except NumericDomainError as exc:
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} contains a nonfinite float64",
            ) from exc
    if token == "list[int]":
        if (
            not isinstance(value, list | tuple)
            or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be an exact integer list",
            )
        return tuple(value)
    if token in {"list[str]", "ordered unique string list"}:
        if (
            not isinstance(value, list | tuple)
            or any(not isinstance(item, str) or not item for item in value)
            or (
                token == "ordered unique string list"
                and len(set(value)) != len(value)
            )
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be a valid ordered text list",
            )
        return tuple(value)
    if token == "list[record]":
        if (
            not isinstance(value, list | tuple)
            or any(not isinstance(item, Mapping) for item in value)
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be a record list",
            )
        return tuple(_freeze(dict(item)) for item in value)
    if token in {
        "mapping",
        "qtt_cqm_grammar_v1 record",
        "qtt_dqm_grammar_v1 record",
    }:
        if not isinstance(value, Mapping):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be a typed mapping",
            )
        return _freeze(dict(value))
    if token == "ordered list[nonnegative or inf]":
        if not isinstance(value, list | tuple):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} must be an ordered threshold list",
            )
        normalized: list[float | str] = []
        for item in value:
            if isinstance(item, str) and item.upper() == "INF":
                normalized.append("INF")
                continue
            try:
                number = finite_float(item, field_name=binding.input_name)  # type: ignore[arg-type]
            except NumericDomainError as exc:
                raise InputAuthorityError(
                    ReasonCode.INPUT_VALUE_CONFLICT,
                    f"{binding.input_name} contains an invalid threshold",
                ) from exc
            if number < 0:
                raise InputAuthorityError(
                    ReasonCode.INPUT_VALUE_CONFLICT,
                    f"{binding.input_name} thresholds must be nonnegative",
                )
            normalized.append(number)
        ordered_values = tuple(
            math.inf if item == "INF" else item for item in normalized
        )
        if any(
            left > right
            for left, right in zip(
                ordered_values, ordered_values[1:], strict=False
            )
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"{binding.input_name} thresholds must be ordered",
            )
        return tuple(normalized)
    return _freeze(value)


def _canonical_equal(left: object, right: object) -> bool:
    if isinstance(left, Decimal):
        try:
            return left == exact_decimal(right, field_name="caller_assertion")  # type: ignore[arg-type]
        except ValueError:
            return False
    if isinstance(left, float):
        if math.isinf(left):
            return (
                isinstance(right, float)
                and not isinstance(right, bool)
                and left == right
            )
        try:
            candidate = finite_float(right, field_name="caller_assertion")  # type: ignore[arg-type]
        except ValueError:
            return False
        return math.isclose(left, candidate, rel_tol=0.0, abs_tol=0.0)
    if isinstance(left, Mapping):
        if not isinstance(right, Mapping) or tuple(left) != tuple(right):
            return False
        return all(_canonical_equal(left[key], right[key]) for key in left)
    if isinstance(left, tuple):
        if not isinstance(right, list | tuple) or len(left) != len(right):
            return False
        return all(_canonical_equal(a, b) for a, b in zip(left, right, strict=True))
    return type(left) is type(right) and left == right


def _sequence_revision_requirements(text: str) -> tuple[bool, bool]:
    token = text.casefold()
    if "not applicable" in token:
        return False, False
    sequence = (
        "sequence required" in token
        or "provider-native sequence" in token
        or "sequence/revision required" in token
    )
    revision = (
        "revision required" in token
        or "sequence/revision required" in token
    )
    return sequence, revision


def _parse_runtime_parameter_value(
    value: object,
    *,
    parameter_id: str,
    parameter_symbol: str,
    extraction: str,
) -> object:
    if "parse as DECIMAL_STRING" in extraction:
        try:
            return exact_decimal(value, field_name=parameter_symbol)  # type: ignore[arg-type]
        except ValueError as exc:
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                f"{parameter_id} requires an exact finite Decimal string",
            ) from exc
    if "parse as INTEGER" in extraction:
        if isinstance(value, bool) or not isinstance(value, int):
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                f"{parameter_id} requires an exact integer",
            )
        return value
    if "parse as BOOLEAN" in extraction:
        if type(value) is not bool:
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                f"{parameter_id} requires an exact boolean",
            )
        return value
    if "parse as CANONICAL_ENUM_OR_RULE" in extraction:
        if not isinstance(value, str) or not value:
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                f"{parameter_id} requires a nonempty canonical token",
            )
        return value
    if "parse as TYPED_STRUCT_OR_COLLECTION" in extraction:
        if not isinstance(value, Mapping | list | tuple) or not value:
            raise InputAuthorityError(
                ReasonCode.PARAMETER_BINDING_MISMATCH,
                f"{parameter_id} requires a nonempty typed structure",
            )
        return _freeze(value)
    raise InputAuthorityError(
        ReasonCode.PARAMETER_BINDING_MISMATCH,
        f"{parameter_id} has an unsupported frozen extraction contract",
    )


def _require_execution_context(
    context: object,
) -> ComputationExecutionContextV1:
    if not isinstance(context, ComputationExecutionContextV1):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCOPE_MISMATCH,
            "value resolution requires ComputationExecutionContextV1",
        )
    return context


def _admit_formula_input_binding(
    binding: FormulaInputAuthorityBindingV1,
    packet: OwnerValuePacketV1,
) -> None:
    if (
        binding.admission_class
        is FormulaInputAdmissionClassV1.ACCEPTED_OWNER_PACKET_REQUIRED_BEFORE_CONTEXTUAL_COMPUTABILITY
    ):
        return
    if (
        binding.admission_class
        is FormulaInputAdmissionClassV1.EXACT_REGISTERED_UPSTREAM_RECEIPT_REQUIRED_BEFORE_CONTEXTUAL_COMPUTABILITY
        and packet.producer_receipt_id
        and packet.producer_receipt_type
    ):
        return
    raise InputAuthorityError(
        ReasonCode.INPUT_PACKET_MISMATCH,
        f"{binding.binding_id} lacks its exact typed admission precondition",
    )


def _validate_formula_input_context(
    context: ComputationExecutionContextV1,
) -> ComputationExecutionContextV1:
    context = _require_execution_context(context)
    FreshnessResolverV1.assert_context_current(context)
    return context


def _resolve_formula_input_binding(
    math_spec_id: str,
    *,
    binding: FormulaInputAuthorityBindingV1,
    context: ComputationExecutionContextV1,
    owner_registry: CanonicalOwnerPacketRegistryV1,
    caller_assertions: Mapping[str, object],
) -> ResolvedFormulaInputV1:
    """Apply the sole owner/schema/scope/PIT/freshness/value admission body."""

    packet = owner_registry.packet_for(
        context=context,
        binding_id=binding.binding_id,
    )
    _admit_formula_input_binding(binding, packet)
    if packet.owner_id != binding.accepted_upstream_owner_id:
        raise InputAuthorityError(
            ReasonCode.INPUT_OWNER_MISMATCH,
            f"{binding.binding_id} packet owner is not canonical",
        )
    if packet.packet_type != binding.accepted_packet_or_snapshot_type:
        raise InputAuthorityError(
            ReasonCode.INPUT_PACKET_MISMATCH,
            f"{binding.binding_id} packet type is not accepted",
        )
    if (
        packet.schema_id != binding.schema_id
        or packet.schema_version != binding.schema_version
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCHEMA_MISMATCH,
            f"{binding.binding_id} schema identity/version differs",
        )
    if (
        packet.context_id != context.context_id
        or packet.scope != context.scope
        or packet.input_version != context.input_version
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCOPE_MISMATCH,
            f"{binding.binding_id} packet execution scope differs",
        )
    if packet.producer_receipt_type != binding.producer_receipt_type:
        raise InputAuthorityError(
            ReasonCode.INPUT_PACKET_MISMATCH,
            f"{binding.binding_id} producer receipt type differs",
        )
    if packet.source_conflict:
        raise InputAuthorityError(
            ReasonCode.SOURCE_CONFLICT,
            f"{binding.binding_id} owner packet has an unresolved conflict",
        )
    if (
        packet.source_state_and_claim_lineage
        != binding.source_state_and_claim_lineage
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_PACKET_MISMATCH,
            f"{binding.binding_id} source/state/claim lineage differs",
        )
    raw_value = _extract(packet.values, binding.exact_field_path)
    value = _parse_typed(raw_value, binding)
    if binding.input_name in caller_assertions:
        assertion = _parse_typed(
            caller_assertions[binding.input_name], binding
        )
        if not _canonical_equal(value, assertion):
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"caller comparison assertion differs for {binding.binding_id}",
            )
    semantics = str(
        next(
            row["point_in_time_semantics"]
            for row in FROZEN_FORMULA_REQUIREMENTS[math_spec_id].raw[
                "typed_inputs"
            ]
            if row["name"] == binding.input_name
        )
    )
    pit = PointInTimePolicyV1.validate(
        receipt_id=f"PIT::{packet.packet_id}::{binding.binding_id}",
        field_class=classify_point_in_time_semantics(semantics),
        clocks=packet.clocks,
        context=context,
        prior_revision_available_time=packet.prior_revision_available_time,
    )
    require_sequence, require_revision = _sequence_revision_requirements(
        binding.provider_native_sequence_or_revision
    )
    freshness = FreshnessResolverV1.validate(
        receipt_id=f"FRESHNESS::{packet.packet_id}::{binding.binding_id}",
        clocks=packet.clocks,
        context=context,
        packet_source_epoch_id=packet.source_epoch_id,
        policy=FreshnessPolicyV1(
            ttl=packet.ttl,
            require_provider_sequence=require_sequence,
            require_revision=require_revision,
        ),
        provider_sequence=packet.provider_sequence,
        revision=packet.revision,
    )
    return ResolvedFormulaInputV1(
        binding_id=binding.binding_id,
        math_spec_id=math_spec_id,
        input_name=binding.input_name,
        value=value,
        owner_id=packet.owner_id,
        packet_id=packet.packet_id,
        field_path=binding.exact_field_path,
        point_in_time_receipt=pit,
        freshness_receipt=freshness,
        producer_receipt_id=packet.producer_receipt_id,
    )


def _admit_runtime_parameter_binding(binding: object) -> None:
    raw = getattr(binding, "raw", None)
    exact_fields = (
        getattr(binding, "accepted_upstream_owner_id", None),
        getattr(binding, "accepted_packet_or_snapshot_type", None),
        getattr(binding, "schema_id", None),
        getattr(binding, "schema_version", None),
        getattr(binding, "producer_receipt_type", None),
        raw.get("source_state_and_claim_lineage") if isinstance(raw, Mapping) else None,
    )
    if (
        getattr(binding, "value_state", None) != "RUNTIME_BINDING_REQUIRED"
        or not isinstance(raw, Mapping)
        or raw.get("current_computation_admission")
        != "BLOCKED_PENDING_ACCEPTED_UPSTREAM_VALUE_PACKET"
        or any(
            not isinstance(value, str)
            or not value
            or value != value.strip()
            for value in exact_fields
        )
    ):
        raise InputAuthorityError(
            ReasonCode.PARAMETER_BINDING_MISMATCH,
            "runtime parameter owner admission metadata is incomplete or altered",
        )


def _resolve_math39_raw_packet(
    binding: ST12DMath39RawInputBindingV1,
    *,
    context: ComputationExecutionContextV1,
    owner_registry: CanonicalOwnerPacketRegistryV1,
) -> tuple[OwnerValuePacketV1, PointInTimeReceiptV1, FreshnessReceiptV1]:
    packet = owner_registry.packet_for(context=context, binding_id=binding.binding_id)
    if packet.owner_id != binding.accepted_upstream_owner_id:
        raise InputAuthorityError(
            ReasonCode.INPUT_OWNER_MISMATCH,
            f"{binding.binding_id} packet owner is not canonical",
        )
    if (
        packet.packet_type != binding.accepted_packet_or_snapshot_type
        or packet.schema_id != binding.schema_id
        or packet.schema_version != binding.schema_version
        or packet.producer_receipt_type != binding.producer_receipt_type
        or packet.source_state_and_claim_lineage
        != binding.source_state_and_claim_lineage
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_PACKET_MISMATCH,
            f"{binding.binding_id} packet/schema/lineage identity differs",
        )
    if packet.source_conflict:
        raise InputAuthorityError(
            ReasonCode.SOURCE_CONFLICT,
            f"{binding.binding_id} has unresolved source conflict",
        )
    pit = PointInTimePolicyV1.validate(
        receipt_id=f"PIT::{packet.packet_id}::{binding.binding_id}",
        field_class=PointInTimeFieldClassV1.OBSERVATION,
        clocks=packet.clocks,
        context=context,
        prior_revision_available_time=packet.prior_revision_available_time,
    )
    is_events = binding.input_name == "sequenced_book_events"
    freshness = FreshnessResolverV1.validate(
        receipt_id=f"FRESHNESS::{packet.packet_id}::{binding.binding_id}",
        clocks=packet.clocks,
        context=context,
        packet_source_epoch_id=packet.source_epoch_id,
        policy=FreshnessPolicyV1(
            ttl=packet.ttl,
            require_provider_sequence=is_events,
            require_revision=not is_events,
        ),
        provider_sequence=packet.provider_sequence,
        revision=packet.revision,
    )
    return packet, pit, freshness


def resolve_math39_formula_inputs(
    *,
    context: ComputationExecutionContextV1,
    owner_registry: CanonicalOwnerPacketRegistryV1,
    caller_assertions: Mapping[str, object] | None = None,
) -> FormulaInputResolutionV1:
    """Resolve two raw owner packets into the four immutable Decimal terms."""

    context = _validate_formula_input_context(context)
    bindings = CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-39"]
    if (
        len(bindings) != 2
        or any(type(row) is not ST12DMath39RawInputBindingV1 for row in bindings)
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCHEMA_MISMATCH,
            "MATH-39 requires exactly two additive raw bindings",
        )
    packet_rows = {
        binding.input_name: _resolve_math39_raw_packet(
            binding,
            context=context,
            owner_registry=owner_registry,
        )
        for binding in bindings
        if isinstance(binding, ST12DMath39RawInputBindingV1)
    }
    events_packet, events_pit, events_freshness = packet_rows[
        "sequenced_book_events"
    ]
    ack_packet, ack_pit, ack_freshness = packet_rows["order_ack"]
    events = _extract(events_packet.values, "book.sequenced_book_events")
    acknowledgement = _extract(ack_packet.values, "execution.order_ack")
    if (
        not isinstance(events, tuple)
        or not events
        or any(type(row) is not Math39SequencedBookEventV1 for row in events)
        or type(acknowledgement) is not Math39OrderAcknowledgementV1
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCHEMA_MISMATCH,
            "MATH-39 raw packets require exact immutable typed event/ack records",
        )
    ack = acknowledgement
    if (
        ack.venue_id != context.scope.venue_scope_id
        or ack.instrument_id != context.scope.instrument_or_contract_scope_id
        or ack.producer_receipt_ref != ack_packet.producer_receipt_id
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_SCOPE_MISMATCH,
            "MATH-39 acknowledgement identity scope differs",
        )
    if ack.acknowledged_at > context.as_of or ack.available_at > context.as_of:
        raise InputAuthorityError(
            ReasonCode.POINT_IN_TIME_VIOLATION,
            "MATH-39 acknowledgement is not available at the context as-of",
        )
    sequences = tuple(row.sequence for row in events)
    if sequences != tuple(range(sequences[0], sequences[0] + len(sequences))):
        raise InputAuthorityError(
            ReasonCode.SEQUENCE_GAP,
            "MATH-39 event stream contains a sequence gap or reorder",
        )
    if sum(
        row.event_kind is Math39BookEventKindV1.DISPLAYED_BEFORE_ORDER
        for row in events
    ) != 1:
        raise InputAuthorityError(
            ReasonCode.INPUT_VALUE_CONFLICT,
            "MATH-39 requires exactly one displayed insertion-point quantity",
        )
    for row in events:
        if (
            row.venue_id != ack.venue_id
            or row.instrument_id != ack.instrument_id
            or row.side != ack.side
            or row.price != ack.price
            or row.priority_order_id != ack.order_id
            or row.venue_evidence_ref != ack.venue_evidence_ref
            or row.producer_receipt_ref != events_packet.producer_receipt_id
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "MATH-39 event identity or venue-evidence custody differs",
            )
        if (
            row.event_time > context.as_of
            or row.available_at > context.as_of
            or row.event_kind is Math39BookEventKindV1.DISPLAYED_BEFORE_ORDER
            and row.event_time > ack.acknowledged_at
            or row.event_kind is not Math39BookEventKindV1.DISPLAYED_BEFORE_ORDER
            and row.event_time < ack.acknowledged_at
        ):
            raise InputAuthorityError(
                ReasonCode.POINT_IN_TIME_VIOLATION,
                "MATH-39 event temporal custody differs from acknowledgement",
            )
    by_kind = {
        kind: sum(
            (row.quantity for row in events if row.event_kind is kind),
            start=Decimal(0),
        )
        for kind in Math39BookEventKindV1
    }
    values = MappingProxyType(
        {
            "displayed_quantity_before_order": by_kind[
                Math39BookEventKindV1.DISPLAYED_BEFORE_ORDER
            ],
            "net_prior_additions": by_kind[Math39BookEventKindV1.PRIOR_ADDITION],
            "observed_prior_cancellations": by_kind[
                Math39BookEventKindV1.PRIOR_CANCELLATION
            ],
            "observed_trades_ahead": by_kind[Math39BookEventKindV1.TRADE_AHEAD],
        }
    )
    assertions = caller_assertions or MappingProxyType({})
    if set(assertions) - set(values):
        raise InputAuthorityError(
            ReasonCode.INPUT_VALUE_CONFLICT,
            "MATH-39 caller assertions contain undeclared derived terms",
        )
    if any(
        name in assertions and not _canonical_equal(value, assertions[name])
        for name, value in values.items()
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_VALUE_CONFLICT,
            "MATH-39 caller assertion differs from raw owner reconstruction",
        )
    resolved = tuple(
        ResolvedFormulaInputV1(
            binding_id=f"DERIVED::MATH-39::{name}",
            math_spec_id="MATH-39",
            input_name=name,
            value=value,
            owner_id="QKUComputationControlPlaneV1",
            packet_id=events_packet.packet_id,
            field_path=f"derived.{name}",
            point_in_time_receipt=events_pit,
            freshness_receipt=events_freshness,
            producer_receipt_id=events_packet.producer_receipt_id,
        )
        for name, value in values.items()
    )
    receipt_refs = tuple(
        dict.fromkeys(
            (
                events_packet.producer_receipt_id,
                events_pit.receipt_id,
                events_freshness.receipt_id,
                ack_packet.producer_receipt_id,
                ack_pit.receipt_id,
                ack_freshness.receipt_id,
                *(row.producer_receipt_ref for row in events),
                ack.producer_receipt_ref,
            )
        )
    )
    return FormulaInputResolutionV1(
        math_spec_id="MATH-39",
        execution_context=context,
        inputs=resolved,
        authoritative_values=values,
        packet_refs=(events_packet.packet_id, ack_packet.packet_id),
        receipt_refs=receipt_refs,
    )


class FormulaInputResolverV1:
    """Resolve every value from the package-named owner, never from the request."""

    @staticmethod
    def resolve(
        math_spec_id: str,
        *,
        context: ComputationExecutionContextV1,
        owner_registry: CanonicalOwnerPacketRegistryV1,
        caller_assertions: Mapping[str, object] | None = None,
    ) -> FormulaInputResolutionV1:
        if math_spec_id == "MATH-39":
            return resolve_math39_formula_inputs(
                context=context,
                owner_registry=owner_registry,
                caller_assertions=caller_assertions,
            )
        context = _validate_formula_input_context(context)
        try:
            bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_spec_id]
        except KeyError as exc:
            raise InputAuthorityError(
                ReasonCode.UNKNOWN_IMPLEMENTATION,
                f"unknown frozen formula input contract: {math_spec_id}",
            ) from exc
        assertions = caller_assertions or MappingProxyType({})
        unknown = set(assertions) - {binding.input_name for binding in bindings}
        if unknown:
            raise InputAuthorityError(
                ReasonCode.INPUT_VALUE_CONFLICT,
                f"caller assertions contain undeclared inputs: {sorted(unknown)}",
            )
        resolved: list[ResolvedFormulaInputV1] = []
        for binding in bindings:
            resolved.append(
                _resolve_formula_input_binding(
                    math_spec_id,
                    binding=binding,
                    context=context,
                    owner_registry=owner_registry,
                    caller_assertions=assertions,
                )
            )
        return FormulaInputResolutionV1(
            math_spec_id=math_spec_id,
            execution_context=context,
            inputs=tuple(resolved),
            authoritative_values=MappingProxyType(
                {row.input_name: row.value for row in resolved}
            ),
            packet_refs=tuple(dict.fromkeys(row.packet_id for row in resolved)),
            receipt_refs=tuple(
                item
                for row in resolved
                for item in (
                    row.producer_receipt_id,
                    row.point_in_time_receipt.receipt_id,
                    row.freshness_receipt.receipt_id,
                )
            ),
        )


class RuntimeParameterValueResolverV1:
    """Resolve one runtime parameter only from its exact frozen owner packet."""

    @staticmethod
    def resolve(
        parameter_id: str,
        *,
        context: ComputationExecutionContextV1,
        owner_registry: CanonicalOwnerPacketRegistryV1,
        caller_assertion: object | None = None,
    ) -> RuntimeParameterValueResolutionV1:
        context = _require_execution_context(context)
        FreshnessResolverV1.assert_context_current(context)
        from .parameter_policy import (
            CUMULATIVE_PARAMETER_POLICIES,
            RUNTIME_PARAMETER_OWNER_BINDINGS,
        )

        try:
            binding = RUNTIME_PARAMETER_OWNER_BINDINGS[parameter_id]
            policy = CUMULATIVE_PARAMETER_POLICIES[parameter_id]
        except KeyError as exc:
            raise InputAuthorityError(
                ReasonCode.PARAMETER_OWNER_MISSING,
                f"no runtime owner interface exists for {parameter_id}",
            ) from exc
        _admit_runtime_parameter_binding(binding)
        packet = owner_registry.packet_for(
            context=context,
            binding_id=binding.binding_id,
        )
        if packet.owner_id != binding.accepted_upstream_owner_id:
            raise InputAuthorityError(
                ReasonCode.INPUT_OWNER_MISMATCH,
                f"{parameter_id} packet owner is not canonical",
            )
        if packet.packet_type != binding.accepted_packet_or_snapshot_type:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                f"{parameter_id} packet type is not accepted",
            )
        if (
            packet.schema_id != binding.schema_id
            or packet.schema_version != binding.schema_version
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCHEMA_MISMATCH,
                f"{parameter_id} schema identity/version differs",
            )
        if (
            packet.context_id != context.context_id
            or packet.scope != context.scope
            or packet.input_version != context.input_version
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                f"{parameter_id} packet execution scope differs",
            )
        if packet.producer_receipt_type != binding.producer_receipt_type:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                f"{parameter_id} producer receipt type differs",
            )
        if packet.source_conflict:
            raise InputAuthorityError(
                ReasonCode.SOURCE_CONFLICT,
                f"{parameter_id} owner packet has an unresolved conflict",
            )
        if (
            packet.source_state_and_claim_lineage
            != str(binding.raw["source_state_and_claim_lineage"])
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                f"{parameter_id} source/state/claim lineage differs",
            )
        value = _parse_runtime_parameter_value(
            _extract(packet.values, binding.exact_field_path),
            parameter_id=parameter_id,
            parameter_symbol=binding.parameter_symbol,
            extraction=str(binding.raw["canonical_typed_value_extraction"]),
        )
        if caller_assertion is not None:
            assertion = _parse_runtime_parameter_value(
                caller_assertion,
                parameter_id=parameter_id,
                parameter_symbol=binding.parameter_symbol,
                extraction=str(binding.raw["canonical_typed_value_extraction"]),
            )
            if not _canonical_equal(value, assertion):
                raise InputAuthorityError(
                    ReasonCode.INPUT_VALUE_CONFLICT,
                    f"caller comparison assertion differs for {parameter_id}",
                )
        pit = PointInTimePolicyV1.validate(
            receipt_id=f"PIT::{packet.packet_id}::{binding.binding_id}",
            field_class=PointInTimeFieldClassV1.OBSERVATION,
            clocks=packet.clocks,
            context=context,
            prior_revision_available_time=packet.prior_revision_available_time,
        )
        require_sequence, require_revision = _sequence_revision_requirements(
            str(binding.raw["provider_native_sequence_or_revision"])
        )
        freshness = FreshnessResolverV1.validate(
            receipt_id=f"FRESHNESS::{packet.packet_id}::{binding.binding_id}",
            clocks=packet.clocks,
            context=context,
            packet_source_epoch_id=packet.source_epoch_id,
            policy=FreshnessPolicyV1(
                ttl=packet.ttl,
                require_provider_sequence=require_sequence,
                require_revision=require_revision,
            ),
            provider_sequence=packet.provider_sequence,
            revision=packet.revision,
        )
        resolved = ResolvedRuntimeParameterValueV1(
            binding_id=binding.binding_id,
            parameter_id=parameter_id,
            parameter_symbol=binding.parameter_symbol,
            value=value,
            unit_or_basis=str(policy.crosswalk["unit_or_basis"]),
            owner_id=packet.owner_id,
            packet_id=packet.packet_id,
            field_path=binding.exact_field_path,
            point_in_time_receipt=pit,
            freshness_receipt=freshness,
            producer_receipt_id=packet.producer_receipt_id,
        )
        return RuntimeParameterValueResolutionV1(
            parameter_id=parameter_id,
            execution_context=context,
            resolved=resolved,
            receipt_refs=(
                packet.producer_receipt_id,
                pit.receipt_id,
                freshness.receipt_id,
            ),
        )


ST12D_SAFETY_BINDING_ID = "ST12D::SAFETY::KILL_SUBMIT"
ST12D_OWNER_ACTION_BINDING_ID = "ST12D::OWNER_ACTION::CONFIRMATION"


def _exact_d_owner_payload(
    *,
    registry: CanonicalOwnerPacketRegistryV1,
    context: ComputationExecutionContextV1,
    binding_id: str,
    owner_id: str,
    packet_type: str,
    schema_id: str,
    field_path: str,
    payload_type: type[object],
) -> object:
    packet = registry.packet_for(context=context, binding_id=binding_id)
    if (
        packet.owner_id != owner_id
        or packet.packet_type != packet_type
        or packet.schema_id != schema_id
        or packet.schema_version != "1.0.0"
        or packet.source_conflict
    ):
        raise InputAuthorityError(
            ReasonCode.INPUT_PACKET_MISMATCH,
            f"{binding_id} canonical owner packet identity differs",
        )
    pit = PointInTimePolicyV1.validate(
        receipt_id=f"PIT::{packet.packet_id}::{binding_id}",
        field_class=PointInTimeFieldClassV1.OBSERVATION,
        clocks=packet.clocks,
        context=context,
        prior_revision_available_time=packet.prior_revision_available_time,
    )
    FreshnessResolverV1.validate(
        receipt_id=f"FRESHNESS::{packet.packet_id}::{binding_id}",
        clocks=packet.clocks,
        context=context,
        packet_source_epoch_id=packet.source_epoch_id,
        policy=FreshnessPolicyV1(ttl=packet.ttl),
        provider_sequence=packet.provider_sequence,
        revision=packet.revision,
    )
    payload = _extract(packet.values, field_path)
    if type(payload) is not payload_type:
        raise InputAuthorityError(
            ReasonCode.INPUT_SCHEMA_MISMATCH,
            f"{binding_id} payload is not {payload_type.__name__}",
        )
    if not pit.receipt_id:
        raise InputAuthorityError(
            ReasonCode.POINT_IN_TIME_VIOLATION,
            f"{binding_id} produced no point-in-time receipt",
        )
    return payload


class CurrentSafetyStateAdapterV1:
    """Exact read-only adapter for the existing safety owner interface."""

    def __init__(self, registry: CanonicalOwnerPacketRegistryV1) -> None:
        if not isinstance(registry, CanonicalOwnerPacketRegistryV1):
            raise InputAuthorityError(
                ReasonCode.INPUT_OWNER_MISSING,
                "current safety adapter requires the canonical packet registry",
            )
        self._registry = registry

    def read_kill_submit_state(
        self, context: ComputationExecutionContextV1
    ) -> ReadOnlyKillSubmitStateV1:
        payload = _exact_d_owner_payload(
            registry=self._registry,
            context=context,
            binding_id=ST12D_SAFETY_BINDING_ID,
            owner_id="SafetyStateProjectionProtocolV1",
            packet_type="ReadOnlyKillSubmitStateV1",
            schema_id="ReadOnlyKillSubmitStateV1::SCHEMA",
            field_path="safety.kill_submit_state",
            payload_type=ReadOnlyKillSubmitStateV1,
        )
        assert isinstance(payload, ReadOnlyKillSubmitStateV1)
        if payload.scope_ref != context.context_id:
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "safety state scope differs from the exact execution context",
            )
        return payload


class CurrentPreFEvidenceAdapterV1:
    """Truthful current evidence adapter: future F states remain interface-only."""

    @staticmethod
    def read_evidence_reference(
        context: ComputationExecutionContextV1,
        *,
        causation_id: str,
        correlation_id: str,
    ) -> ST12FEvidenceReferenceV1:
        from .mode_snapshot_policy import pre_f_unavailable_reference

        return pre_f_unavailable_reference(
            observed_at=context.as_of,
            valid_until=context.as_of + context.maximum_age,
            causation_id=causation_id,
            correlation_id=correlation_id,
        )


class CurrentOwnerActionConfirmationAdapterV1:
    """Exact read-only adapter for current owner-action confirmation receipts."""

    def __init__(self, registry: CanonicalOwnerPacketRegistryV1) -> None:
        if not isinstance(registry, CanonicalOwnerPacketRegistryV1):
            raise InputAuthorityError(
                ReasonCode.INPUT_OWNER_MISSING,
                "owner-action adapter requires the canonical packet registry",
            )
        self._registry = registry

    def read_owner_action_confirmation(
        self, context: ComputationExecutionContextV1
    ) -> OwnerActionConfirmationReceiptV1:
        payload = _exact_d_owner_payload(
            registry=self._registry,
            context=context,
            binding_id=ST12D_OWNER_ACTION_BINDING_ID,
            owner_id="OwnerActionSemanticProtocolV1",
            packet_type="OwnerActionConfirmationReceiptV1",
            schema_id="OwnerActionConfirmationReceiptV1::SCHEMA",
            field_path="owner_action.confirmation",
            payload_type=OwnerActionConfirmationReceiptV1,
        )
        assert isinstance(payload, OwnerActionConfirmationReceiptV1)
        return payload


class CurrentModeSnapshotInputResolverV1:
    """Concrete D resolver composed from separate exact current-owner adapters."""

    def __init__(
        self,
        *,
        repo_root: str | Path,
        owner_registry: CanonicalOwnerPacketRegistryV1,
    ) -> None:
        self._repo_root = Path(repo_root).resolve()
        self._owner_registry = owner_registry
        self._safety = CurrentSafetyStateAdapterV1(owner_registry)
        self._evidence = CurrentPreFEvidenceAdapterV1()
        self._owner_action = CurrentOwnerActionConfirmationAdapterV1(owner_registry)

    @property
    def owner_registry(self) -> CanonicalOwnerPacketRegistryV1:
        return self._owner_registry

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    def resolve_mode_snapshot_inputs(
        self,
        request: object,
        capability_decision: object,
    ) -> object:
        from .agent_policy import AgentCapabilityDecisionV1
        from .implementation_registry import ST12D_MATH_IMPLEMENTATION_REGISTRY
        from .mode_snapshot_policy import ModeSnapshotCandidateInputsV1
        from .parameter_policy import (
            ST12D_SNAPSHOT_PARAMETER_BINDING_IDS,
            resolve_st12d_value_policy_refs,
        )
        from .protocols import ExistingOwnerProjectionAdapterV1
        from .stack_resolver import preflight_snapshot_computation_bundle

        context = getattr(request, "context", None)
        if (
            type(capability_decision) is not AgentCapabilityDecisionV1
            or not isinstance(context, ComputationExecutionContextV1)
            or getattr(request, "request_id", None) != capability_decision.request_id
            or getattr(request, "principal_id", None)
            != capability_decision.principal_id
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "current D resolution requires the exact admitted E identity/context",
            )
        if len(capability_decision.st12c_causation_correlation_refs) < 2:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "admitted E decision lacks causation/correlation lineage",
            )
        causation_id, correlation_id = (
            capability_decision.st12c_causation_correlation_refs[:2]
        )
        safety = self._safety.read_kill_submit_state(context)
        evidence = self._evidence.read_evidence_reference(
            context,
            causation_id=causation_id,
            correlation_id=correlation_id,
        )
        owner_action = self._owner_action.read_owner_action_confirmation(context)
        projection_adapter = ExistingOwnerProjectionAdapterV1(self._repo_root)
        readiness = projection_adapter.load_readiness()
        pretrade = projection_adapter.load_pretrade()
        svc = projection_adapter.load_svc()
        agent_orch = projection_adapter.load_agent_orch()
        policy_refs = resolve_st12d_value_policy_refs(
            ST12D_SNAPSHOT_PARAMETER_BINDING_IDS
        )
        parameter_value_refs = tuple(policy_refs[parameter_id] for parameter_id in policy_refs)
        parameter_policy_snapshot_ref = (
            f"ComputationParameterPolicyV1::{context.parameter_policy_version}"
        )
        source_epoch_refs = tuple(
            dict.fromkeys(
                (
                    context.source_epoch_id,
                    *(packet.source_epoch_id for packet in self._owner_registry.packets),
                )
            )
        )
        bundle = preflight_snapshot_computation_bundle(
            context=context,
            owner_registry=self._owner_registry,
            parameter_policy_snapshot_ref=parameter_policy_snapshot_ref,
            parameter_value_refs=parameter_value_refs,
            source_epoch_refs=source_epoch_refs,
        )
        implementation_pins = tuple(
            ImplementationVersionPinV1(
                math_spec_id=math_id,
                implementation_id=(
                    ST12D_MATH_IMPLEMENTATION_REGISTRY[
                        math_id
                    ].contract.implementation_id
                ),
            )
            for math_id in ST12D_MATH_IMPLEMENTATION_REGISTRY
        )
        if context.implementation_versions != implementation_pins:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                "D execution context implementation pins differ from the selected bundle",
            )
        receipt_lineage_refs = tuple(
            dict.fromkeys(
                (
                    capability_decision.agent_orch_receipt_ref,
                    safety.state_ref,
                    owner_action.receipt_ref,
                    bundle.preflight_receipt_ref,
                    *bundle.receipt_refs,
                    f"READINESS1::{readiness.source_version}",
                    f"PRETRADE1::{pretrade.source_version}",
                    f"SVC1::{svc.source_version}",
                    f"AGENT-ORCH1::{agent_orch.source_version}",
                )
            )
        )
        expires_at = min(
            context.as_of + context.maximum_age,
            safety.valid_until,
            owner_action.valid_until,
        )
        return ModeSnapshotCandidateInputsV1(
            request_id=capability_decision.request_id,
            principal_id=capability_decision.principal_id,
            task_id=capability_decision.task_id,
            current_agent_id=capability_decision.current_agent_id,
            capability_decision_ref=capability_decision.decision_id,
            computation_bundle_ref=bundle.bundle_ref,
            context_ref=context.context_id,
            formula_spec_refs=tuple(ST12D_MATH_IMPLEMENTATION_REGISTRY),
            implementation_version_pins=implementation_pins,
            binding_profile_ref=(
                f"ComputationBindingProfileV1::{context.binding_profile_version}"
            ),
            parameter_policy_snapshot_ref=parameter_policy_snapshot_ref,
            parameter_value_refs=parameter_value_refs,
            source_epoch_refs=source_epoch_refs,
            receipt_lineage_refs=receipt_lineage_refs,
            readiness_state_ref=f"READINESS1::{readiness.source_version}",
            pretrade_state_ref=f"PRETRADE1::{pretrade.source_version}",
            owner_action_policy_ref=owner_action.owner_action_policy_ref,
            current_mode=context.scope.mode_context_id,
            requested_mode="HOTPATH_CANDIDATE_ONLY",
            expected_owner_state_ref=f"SVC1::{svc.source_version}",
            candidate_version=context.input_version,
            created_at=context.as_of,
            evaluated_at=context.as_of,
            expires_at=expires_at,
            causation_id=causation_id,
            correlation_id=correlation_id,
            evidence_reference=evidence,
            kill_submit_state=safety,
            computation_bundle_closure=bundle,
            owner_action_confirmation=owner_action,
        )
