"""Strict formula-input and runtime-parameter owner-packet resolution."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction
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
    _native_require,
    _native_utc_nanoseconds,
    _native_retail_finite_decimal_text_v1,
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
    PITDataContractErrorV1,
    PITDepthClassV2,
    PITInputAvailabilityV2,
    PITReasonCodeV1,
    PointInTimeClocksV1,
    PointInTimeFieldClassV1,
    PointInTimePolicyV1,
    PointInTimeReceiptV1,
    classify_point_in_time_semantics,
)
from .stage1_launch_graph import Stage1VenueProfileIdV1
from .models import (
    ComputationExecutionContextV1,
    ComputationScopeV1,
    ImplementationVersionPinV1,
    NO_EFFECTS_V1,
    OwnerActionConfirmationReceiptV1,
    ReadOnlyKillSubmitStateV1,
    ST12FEvidenceReferenceV1,
    ST12FEvidenceStateV1,
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
            packet = self._by_binding[
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

        _admit_public_packet_custody_v1(registry=self, packet=packet, context=context, binding_id=binding_id)
        return packet

    def packet_by_id(self, packet_id: str) -> OwnerValuePacketV1:
        try:
            packet = self._by_id[packet_id]
        except KeyError as exc:
            raise InputAuthorityError(
                ReasonCode.INPUT_PACKET_MISMATCH,
                f"owner packet identity is absent: {packet_id}",
            ) from exc

        _admit_public_packet_custody_v1(registry=self, packet=packet, context=None)
        return packet

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
        packet = _prepare_public_computation_descendant_v1(parent=self, packet=packet)
        registry = CanonicalOwnerPacketRegistryV1((*self._packets, packet))
        _inherit_public_registry_custody_v1(parent=self, child=registry, descendant=packet)
        return registry


_PUBLIC_OWNER_REGISTRIES_V1: dict[int, tuple] = {}
_PUBLIC_OWNER_REGISTRY_KEYS_V1: dict[tuple, object] = {}
_PUBLIC_OWNER_PACKET_ORIGINS_V1: dict[str, tuple] = {}
_PUBLIC_NATIVE_CONTEXT_BINDINGS_V1: set[tuple] = set()
_PUBLIC_NATIVE_CONTEXTS_V1: set[tuple] = set()
_PUBLIC_DERIVED_PACKET_CUSTODY_V1: dict[int, tuple] = {}
_PUBLIC_RESPONSE_DEPENDENCIES_V1: ContextVar[dict | None] = ContextVar(
    "public_response_dependencies_v1", default=None,
)


def _admit_public_packet_custody_v1(*, registry, packet, context, binding_id=None):
    """A packet copy or a new registry cannot inherit an issued view's custody."""
    issued = _PUBLIC_OWNER_PACKET_ORIGINS_V1.get(packet.packet_id)
    bindings = packet.authorized_binding_ids if binding_id is None else (binding_id,)
    keys = tuple(registry._packet_binding_key(packet, item) for item in bindings)
    native_required = (keys[0][:-1] in _PUBLIC_NATIVE_CONTEXTS_V1
                       or any(key in _PUBLIC_NATIVE_CONTEXT_BINDINGS_V1 for key in keys))
    if context is not None:
        native_required = native_required or registry._context_binding_key(context, bindings[0])[:-1] in _PUBLIC_NATIVE_CONTEXTS_V1
    if issued is None and not native_required:
        return
    proof = _PUBLIC_OWNER_REGISTRIES_V1.get(id(registry))
    origin = None if proof is None else proof[1].get(id(packet))
    if (issued is None or issued[0] is not packet or proof is None
            or proof[0] is not registry or origin is None or origin[0] is not packet
            or origin[2] is not issued[2]
            or native_required and any(entry[12] is not True for entry, _fence in origin[4])):
        raise InputAuthorityError(ReasonCode.INPUT_PACKET_MISMATCH,
                                  "public packet lacks original registry/publication custody")
    if context is not None and context != proof[2]:
        raise InputAuthorityError(ReasonCode.INPUT_SCOPE_MISMATCH,
                                  "issued public execution context or freshness budget changed")
    from ..orderbook_event_state_snapshot.handoff import _require_public_publication_custody_v1
    from .source_policy import _public_response_fence_v1

    for entry, fence in origin[4]:
        _require_public_publication_custody_v1(publication=entry[0], native_only=native_required)
        with _public_response_fence_v1(fence):
            pass
    if context is not None and any(registry._context_binding_key(context, item) != key
                                   for item, key in zip(bindings, keys)):
        raise InputAuthorityError(ReasonCode.INPUT_SCOPE_MISMATCH, "issued public context changed")
    dependencies = _PUBLIC_RESPONSE_DEPENDENCIES_V1.get()
    if dependencies is not None:
        for entry, fence in origin[4]:
            dependencies[(id(entry[0]), id(fence))] = (entry, fence)


def _prepare_public_computation_descendant_v1(*, parent, packet):
    """Verify the existing edge using its registered computation/conversion owners.

    Public constructor arguments alone cannot attach custody to an invented
    descendant. This check stays in the existing resolver owner and leaves the
    legacy stack producer and its reference receipt identities unchanged.
    """
    proof = _PUBLIC_OWNER_REGISTRIES_V1.get(id(parent))
    if proof is None:
        return packet
    from .serialization import deterministic_json
    from .implementation_registry import invoke_formula_v34
    from .unit_conversion import ConversionIdentityV1, UnitBasisDescriptorV1, UnitConversionOwnerV1

    context = proof[2]
    resolution = FormulaInputResolverV1.resolve("MATH-01", context=context, owner_registry=parent)
    computed = invoke_formula_v34("MATH-01", resolution.authoritative_values)
    converted, _receipt = UnitConversionOwnerV1.convert(
        conversion_id=ConversionIdentityV1.DECIMAL_PROBABILITY_TO_FINITE_FLOAT64,
        value=computed, source=UnitBasisDescriptorV1("Decimal", "scalar", "dimensionless", "winning payout-normalized probability"),
        target=UnitBasisDescriptorV1("float64", "scalar", "probability points", "unit interval"),
        context=context, receipt_id=f"CONVERSION::{context.context_id}::MATH-01::MATH-02")
    source_packets = tuple(parent.packet_by_id(identity) for identity in resolution.packet_refs)
    expected_clocks = PointInTimeClocksV1(**{
        name: max(getattr(source.clocks, name) for source in source_packets)
        for name in ("observed_time", "effective_time", "available_time", "received_time", "processed_time")
    }, as_of_time=context.as_of)
    _native_require(type(packet) is OwnerValuePacketV1 and packet.scope == context.scope
                    and packet.context_id == context.context_id and packet.source_epoch_id == context.source_epoch_id
                    and packet.input_version == context.input_version and packet.clocks == expected_clocks
                    and packet.ttl == min(source.ttl for source in source_packets)
                    and dict(packet.values) == {"output.implied_probability": converted}
                    and packet.authorized_binding_ids == ("FIVAB::MATH-02::market_implied_probability",),
                    "derived public receipt differs from the exact registered producer result")
    closure = {}
    for source in source_packets:
        _admit_public_packet_custody_v1(registry=parent, packet=source, context=context)
        origin = proof[1].get(id(source))
        if origin is not None:
            for entry, fence in origin[4]:
                closure[(id(entry[0]), id(fence))] = (entry, fence)
    _native_require(closure, "derived computation has no selected public dependency")
    identity = deterministic_json(("PUBLIC_DERIVED_MATH01_V1", context.context_id,
        context.as_of.isoformat(), context.source_epoch_id, context.input_version,
        context.scope.identity_tuple, tuple(source.packet_id for source in source_packets)))
    packet = replace(packet, packet_id=identity, producer_receipt_id=identity)
    prior = _PUBLIC_OWNER_PACKET_ORIGINS_V1.get(identity)
    if prior is not None:
        _native_require(prior[0] == packet, "derived public receipt conflicts with an earlier computation")
        packet = prior[0]
    _PUBLIC_DERIVED_PACKET_CUSTODY_V1[id(packet)] = (packet, parent, tuple(closure.values()))
    return packet


def _inherit_public_registry_custody_v1(*, parent, child, descendant=None):
    proof = _PUBLIC_OWNER_REGISTRIES_V1.get(id(parent))
    if proof is None:
        return
    _native_require(proof[0] is parent, "public registry identity changed")
    origins = dict(proof[1])
    if descendant is not None:
        prepared = _PUBLIC_DERIVED_PACKET_CUSTODY_V1.get(id(descendant))
        _native_require(prepared is not None and prepared[0] is descendant and prepared[1] is parent,
                        "derived MATH-01 receipt lacks its actual registered producer custody")
        closure = prepared[2]
        entry = (descendant, child, closure[0][0], closure[0][1], closure)
        origins[id(descendant)] = entry
        _PUBLIC_OWNER_PACKET_ORIGINS_V1.setdefault(descendant.packet_id, entry)
        if entry[2][12]:
            for binding_id in descendant.authorized_binding_ids:
                key = child._packet_binding_key(descendant, binding_id)
                _PUBLIC_NATIVE_CONTEXT_BINDINGS_V1.add(key)
                _PUBLIC_NATIVE_CONTEXTS_V1.add(key[:-1])
    _PUBLIC_OWNER_REGISTRIES_V1[id(child)] = (child, MappingProxyType(origins), proof[2])


def _join_public_owner_dependencies_v1(*, registry, dependencies):
    """Join separately owned packets without changing their owner or origin."""
    _native_require(type(registry) is CanonicalOwnerPacketRegistryV1
                    and type(dependencies) is CanonicalOwnerPacketRegistryV1,
                    "public dependency join needs the existing exact registry type")
    proof = _PUBLIC_OWNER_REGISTRIES_V1.get(id(registry))
    _native_require(proof is not None and proof[0] is registry, "unissued public registry")
    selected = tuple(proof[1].values())
    _native_require(selected, "empty public dependency closure")
    template = selected[0][0]
    for packet in dependencies.packets:
        _native_require(packet.scope == template.scope and packet.context_id == template.context_id
                        and packet.source_epoch_id == template.source_epoch_id
                        and packet.input_version == template.input_version
                        and packet.clocks.as_of_time == template.clocks.as_of_time,
                        "separately owned dependency has a different selected context")
        _admit_public_packet_custody_v1(registry=dependencies, packet=packet, context=None)
    if selected[0][2][12]:
        dependency_proof = _PUBLIC_OWNER_REGISTRIES_V1.get(id(dependencies))
        _native_require(dependency_proof is not None and dependency_proof[0] is dependencies
                        and all(dependency_proof[1].get(id(packet)) is not None
                                and dependency_proof[1][id(packet)][2][12] for packet in dependencies.packets),
                        "native dependency owner custody is unavailable")
    child = CanonicalOwnerPacketRegistryV1((*registry.packets, *dependencies.packets))
    _inherit_public_registry_custody_v1(parent=registry, child=child)
    other = _PUBLIC_OWNER_REGISTRIES_V1.get(id(dependencies))
    if other is not None:
        _PUBLIC_OWNER_REGISTRIES_V1[id(child)] = (child, MappingProxyType({
            **_PUBLIC_OWNER_REGISTRIES_V1[id(child)][1], **other[1]}), proof[2])
    return child


def issue_public_owner_registry_v1(*, publication, context, binding_ids,
                                   source_bindings, applicability=None):
    return _issue_public_owner_registry_v1(publication=publication, context=context, binding_ids=binding_ids,
        source_bindings=source_bindings, applicability=applicability, order_history_dependencies=None)


def _issue_public_order_history_registry_v1(*, publication, context, source_bindings, dependencies, applicability=None):
    """Join actual public changes to separately owned acknowledgement/priority facts."""
    registry = _issue_public_owner_registry_v1(publication=publication, context=context,
        binding_ids=("FIVAB::sequenced_book_events::MATH-39",), source_bindings=source_bindings,
        applicability=applicability, order_history_dependencies=dependencies)
    ack_binding = "FIVAB::order_ack::MATH-39"
    ack = dependencies.packet_for(context=context, binding_id=ack_binding)
    acknowledgement = CanonicalOwnerPacketRegistryV1((ack,))
    proof = _PUBLIC_OWNER_REGISTRIES_V1.get(id(dependencies))
    if proof is not None:
        _PUBLIC_OWNER_REGISTRIES_V1[id(acknowledgement)] = (acknowledgement, proof[1], context)
    return _join_public_owner_dependencies_v1(registry=registry, dependencies=acknowledgement)


def _issue_public_fee_registry_v1(*, publication, context, binding_ids, source_bindings, applicability,
                                fills, order_ref, prior_unrounded, prior_collected, prior_rounding_overpayment,
                                carry_evidence_refs, fresh_hypothetical_order, include_deferred_taker_rebate):
    """Issue the existing PRETRADE fee-owned fields from sealed source evidence.

    Model, fill-probability, unobserved terminal-branch and reserve packets remain separate.
    Native admission requires account/carry custody, which the source owner holds
    unavailable until its qualification exists; fixture origins stay synthetic.
    """
    import time
    from .context import _public_refs_v1
    from .serialization import deterministic_json
    from .source_policy import (_resolve_public_publication_fee_epochs_v1,
                                _prepare_public_response_fence_v1, _public_response_fence_v1)
    from ..orderbook_event_state_snapshot.handoff import (
        _require_public_publication_handle_v1, _public_committed_observations_v1, _public_committed_translations_v1,
        _public_selected_metadata_sources_v1,
    )
    from ...pretrade.pr169_pretrade1_resolvers import (
        compose_public_fee_cashflows_v1, compose_public_contractual_settlement_cashflow_v1,
    )

    entry = _require_public_publication_handle_v1(publication=publication)
    _native_require(type(context) is ComputationExecutionContextV1, "fee registry requires an exact context")
    _public_refs_v1(binding_ids)
    _native_require(type(source_bindings) is tuple and source_bindings
        and len({id(row) for row in source_bindings}) == len(source_bindings)
        and all(any(row is admitted for admitted in entry[5]) for row in source_bindings),
        "fee registry source identities are not admitted by this publication")
    metadata_rows = tuple(row for row in entry[4] if row.instrument_id == context.scope.instrument_or_contract_scope_id
        and row.market_id == context.scope.market_scope_id and row.profile_id.value == context.scope.venue_scope_id)
    _native_require(len(metadata_rows) == 1 and context.source_epoch_id == entry[10] and context.input_version == entry[11]
        and context.scope.input_snapshot_id == entry[7].record_id, "fee registry publication context mismatch")
    metadata = metadata_rows[0]
    _native_require(metadata.event_id_or_none is None or metadata.event_id_or_none == context.scope.event_scope_id,
                    "fee registry event scope mismatch")
    known = _native_utc_nanoseconds(context.as_of.isoformat())
    _native_require(entry[8] <= known <= ((time.time_ns()+999)//1000)*1000,
                    "fee registry context predates issuance or is in the future")
    owned = {"entry_trade_cashflow_total", "platform_fee_total", "expected_rebate_total"}
    terminal = {"win_terminal_cashflow_total", "lose_terminal_cashflow_total"}
    rows = {row.binding_id: (math_id, row) for math_id in ("MATH-06", "MATH-07")
            for row in CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
            if row.input_name in owned or math_id == "MATH-06" and row.input_name in terminal}
    _native_require(set(binding_ids) <= set(rows), "fee registry cannot supply another owner's economic inputs")
    selected = tuple(rows[identity] for identity in binding_ids)
    epochs = _resolve_public_publication_fee_epochs_v1(publication=publication, instrument_id=metadata.instrument_id,
        known_as_of_ns=known, applicability=applicability, fills=fills)
    if entry[12]:
        raise InputAuthorityError(ReasonCode.INPUT_OWNER_MISSING,
                                  "native conditional-fill and order-carry owner custody unavailable")
    settlement = None
    requested_terminal = {row.input_name for _,row in selected} & terminal
    if requested_terminal:
        settlement = compose_public_contractual_settlement_cashflow_v1(metadata=metadata,
            translations=_public_committed_translations_v1(publication=publication),known_as_of_ns=known,fills=fills)
        _native_require(requested_terminal == {settlement["field_name"]},
                        "unobserved settlement branch requires its separate accepted owner input")
    originals = {row.observation_id: row for row in _public_committed_observations_v1(publication=publication)}
    material_refs = {ref for epoch in epochs for ref in epoch.source_observation_refs}
    material_refs.update(row[0] for row in metadata.field_lineage)
    if settlement is not None:
        material_refs.update(settlement["source_observation_refs"])
    required_sources = {row.binding_id for row in _public_selected_metadata_sources_v1(publication=publication,
        metadata=metadata_rows,known_as_of_ns=known)}
    for ref in material_refs:
        original = originals.get(ref)
        if original is not None:
            required_sources.update(original.source_binding_refs)
        else:
            owners = tuple(source for source in entry[5] if ref in source.original_evidence_refs)
            _native_require(owners, "fee metadata or rule lacks its accepted source original")
            required_sources.update(source.binding_id for source in owners)
    _native_require(required_sources <= {source.binding_id for source in source_bindings},
                    "fee registry omits a material catalog, accepted rule or history source")
    source_bindings = tuple(source for source in source_bindings if source.binding_id in required_sources)
    _native_require(all(row.accepted_upstream_owner_id == "PRETRADE1"
        and all("FormulaExecutionContractV1::"+math_id in source.permitted_consumer_ids for source in source_bindings)
        for math_id, row in selected), "fee source does not permit the selected PRETRADE consumer")
    if metadata.profile_id is Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT:
        _native_require(len({row.epoch_id for row in epochs if row.liquidity_role == "TAKER"}) <= 1,
                        "Retail cross-regime order cap requires accepted cap-domain evidence")
    terms = compose_public_fee_cashflows_v1(profile_id=metadata.profile_id, market_scope=(metadata.instrument_id,),
        epochs=epochs, applicability=applicability, known_as_of_ns=known, fills=fills, order_ref=order_ref,
        cap_domain_epoch_refs=tuple(epoch.epoch_id for epoch in epochs), prior_unrounded=prior_unrounded,
        prior_collected=prior_collected, prior_rounding_overpayment=prior_rounding_overpayment,
        carry_evidence_refs=carry_evidence_refs, fresh_hypothetical_order=fresh_hypothetical_order,
        include_deferred_taker_rebate=include_deferred_taker_rebate)
    if settlement is not None:
        terms = dict(terms,**{settlement["field_name"]:settlement["value"]})
    maximum_age_ns = ((context.maximum_age.days*86400+context.maximum_age.seconds)*1000000
                      + context.maximum_age.microseconds)*1000
    observed_ns = min(entry[8], metadata.known_at_ns, *(row.known_at_ns for row in source_bindings))
    expiry = min(observed_ns+maximum_age_ns, *(epoch.expires_at_ns for epoch in epochs))
    _native_require(known < expiry, "fee economic input is stale at the selected context")
    fence = _prepare_public_response_fence_v1(binding=entry[1]._binding, sources=source_bindings,
        metadata=metadata_rows, applicability=applicability, not_after_ns=expiry)
    moment = lambda value: datetime(1970, 1, 1, tzinfo=UTC)+timedelta(microseconds=(value+999)//1000)
    # Conditional future fill times are retained in the immutable input identity;
    # they never replace the source's observation/availability clocks.
    clocks = PointInTimeClocksV1(moment(observed_ns), moment(observed_ns), moment(entry[8]),
        moment(entry[8]), moment(entry[8]), context.as_of)
    inputs = (tuple((str(fill.contracts),str(fill.price),fill.side,fill.liquidity_role,fill.fill_at_ns) for fill in fills),
        order_ref, str(prior_unrounded), str(prior_collected), str(prior_rounding_overpayment), carry_evidence_refs,
        fresh_hypothetical_order, include_deferred_taker_rebate, tuple(row.epoch_id for row in epochs))
    packets = []
    for _, row in selected:
        identity = deterministic_json(("PUBLIC_PRETRADE_FEE_V1", entry[7].record_id,
            entry[7].typed_payload.source_use_action_ref, context.context_id,
            context.scope.identity_tuple, context.source_epoch_id, context.input_version, known, maximum_age_ns,
            applicability.qualification_ref, applicability.generation, row.binding_id, inputs))
        packet = OwnerValuePacketV1(packet_id=identity, owner_id=row.accepted_upstream_owner_id,
            packet_type=row.accepted_packet_or_snapshot_type, schema_id=row.schema_id, schema_version=row.schema_version,
            context_id=context.context_id, scope=context.scope, source_epoch_id=context.source_epoch_id,
            input_version=context.input_version, clocks=clocks, ttl=context.maximum_age,
            values={row.exact_field_path: terms[row.input_name]}, authorized_binding_ids=(row.binding_id,),
            producer_receipt_id=identity, producer_receipt_type=row.producer_receipt_type,
            source_state_and_claim_lineage=row.source_state_and_claim_lineage, provider_sequence=None, revision=None)
        prior = _PUBLIC_OWNER_PACKET_ORIGINS_V1.get(identity)
        if prior is not None:
            _native_require(prior[2] is entry and prior[0] == packet, "fee packet identity conflicts with an earlier issuance")
            packet = prior[0]
        packets.append(packet)
    registry = CanonicalOwnerPacketRegistryV1(tuple(packets))
    origins = {id(packet): (packet, registry, entry, fence, ((entry,fence),)) for packet in packets}
    with _public_response_fence_v1(fence):
        _PUBLIC_OWNER_REGISTRIES_V1[id(registry)] = (registry, MappingProxyType(origins), context)
        for packet in packets:
            _PUBLIC_OWNER_PACKET_ORIGINS_V1.setdefault(packet.packet_id, origins[id(packet)])
            if entry[12]:
                key = registry._packet_binding_key(packet, packet.authorized_binding_ids[0])
                _PUBLIC_NATIVE_CONTEXT_BINDINGS_V1.add(key)
                _PUBLIC_NATIVE_CONTEXTS_V1.add(key[:-1])
        return registry


def _project_public_order_history_v1(*, publication, context, translations, sources, dependencies):
    """A public aggregate never creates order-aware priority classification."""
    from ..orderbook_event_state_snapshot.handoff import _require_public_publication_custody_v1
    from .context import _public_counter_v1

    entry = _require_public_publication_custody_v1(publication=publication)
    _native_require(type(dependencies) is CanonicalOwnerPacketRegistryV1,
                    "public queue history requires separately owned acknowledgement and priority evidence")
    proof = _PUBLIC_OWNER_REGISTRIES_V1.get(id(dependencies))
    if entry[12]:
        _native_require(proof is not None and proof[0] is dependencies and all(
            id(packet) in proof[1] and all(origin[12] for origin, _fence in proof[1][id(packet)][4])
            for packet in dependencies.packets), "native order-aware priority custody is unavailable")
    resolution = FormulaInputResolverV1.resolve("MATH-39", context=context, owner_registry=dependencies)
    _native_require(len(dependencies.packets) == 2, "queue projection accepts only its two separately owned dependencies")
    event_packet, ack_packet = tuple(dependencies.packet_by_id(ref) for ref in resolution.packet_refs)
    events = _extract(event_packet.values, "book.sequenced_book_events")
    ack = _extract(ack_packet.values, "execution.order_ack")
    history = tuple(row for row in translations if row.stream_disposition.get("instrument_id") == ack.instrument_id
                    and row.stream_disposition.get("event_kind") in {"BOOK_SNAPSHOT", "BOOK_DELTA"})
    _native_require(history and len(history) == len(events), "order-aware evidence does not cover the complete public change history")
    _native_require(entry[1]._binding._capture.scope.profile_id is not Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT,
                    "PIT_PROVIDER_SEQUENCE_UNAVAILABLE: Retail has no change-level history")
    previous_quantity = None
    projected = []
    for index, (translation, event) in enumerate(zip(history, events, strict=True)):
        body = translation.normalized_frame.parsed_source_scalar_tree_or_none
        clock = translation.exact_clock_companion["provider_event_or_none"]
        _native_require(clock is not None and int(clock["utc_ns_text"]) == _native_utc_nanoseconds(event.event_time.isoformat())
                        and event.event_id == translation.observation_ref,
                        "order-aware event identity/time differs from the exact public original")
        native_kind = translation.stream_disposition["event_kind"]
        _native_require((index == 0 and native_kind == "BOOK_SNAPSHOT") or (index > 0 and native_kind == "BOOK_DELTA"),
                        "order-aware history requires one initial anchor and subsequent changes")
        _native_require(not (event.quantity.is_zero() and event.quantity.is_signed()), "signed-zero order-aware quantity")
        if translation.normalized_frame.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT:
            sequence = body["seq"]
            message = body["msg"]
            _native_require(ack.side in {"YES_BID", "NO_BID"}, "Kalshi order-aware side requires its outcome-side book basis")
            side = "yes" if ack.side == "YES_BID" else "no"
            if native_kind == "BOOK_SNAPSHOT":
                levels = message[side + "_dollars"]
                matching = [(position, quantity) for position, (price, quantity) in enumerate(levels) if Fraction(price) == Fraction(ack.price)]
                _native_require(len(matching) == 1, "acknowledged price has no unique displayed native level")
                position, quantity = matching[0]
                change = Fraction(quantity)
                quantity_pointer = f"/msg/{side}_dollars_fp/{position}/1"
            else:
                _native_require(message["side"] == side.upper() and Fraction(message["price_dollars"]) == Fraction(ack.price),
                                "native delta is outside the acknowledged side/price")
                change = Fraction(message["delta_fp"])
                quantity_pointer = "/msg/delta_fp"
        else:
            _native_require(body["U"] == body["u"], "MATH-39 cannot renumber an inclusive native update range")
            sequence = body["u"]
            _native_require(ack.side in {"BID", "ASK"}, "Gemini order-aware side unavailable")
            side = "b" if ack.side == "BID" else "a"
            matching = [(position, quantity) for position, (price, quantity) in enumerate(body[side]) if Fraction(price) == Fraction(ack.price)]
            _native_require(len(matching) == 1, "acknowledged price has no unique native absolute update")
            position, quantity = matching[0]
            current = Fraction(quantity)
            change = current if native_kind == "BOOK_SNAPSHOT" else current - previous_quantity
            previous_quantity = current
            quantity_pointer = f"/{side}/{position}/1"
        _public_counter_v1(sequence, allow_zero=True)
        material = tuple(row for source in sources for row in source.field_bindings
                         if row[4] == quantity_pointer and row[1] == "DECIMAL_TEXT" and row[2] == "CONTRACT_COUNT"
                         and row[5] == "EXACT_DECIMAL_TEXT")
        _native_require(len(material) == 1 and (translation.observation_ref, quantity_pointer,
            material[0][0], material[0][5]) in translation.field_lineage, "native queue quantity basis is unavailable")
        expected_kind = (Math39BookEventKindV1.DISPLAYED_BEFORE_ORDER if native_kind == "BOOK_SNAPSHOT"
                         else Math39BookEventKindV1.PRIOR_ADDITION if change >= 0 else None)
        _native_require(event.sequence == sequence and Fraction(event.quantity) == abs(change)
            and (event.event_kind is expected_kind if expected_kind is not None else event.event_kind in {
                Math39BookEventKindV1.PRIOR_CANCELLATION, Math39BookEventKindV1.TRADE_AHEAD}),
            "order-aware classification/quantity differs from actual native change history")
        projected.append(replace(event, producer_receipt_ref=entry[7].record_id,
            available_at=max(event.available_at, datetime(1970,1,1,tzinfo=UTC)+timedelta(microseconds=(entry[8]+999)//1000))))
    return tuple(projected)


def _issue_public_owner_registry_v1(*, publication, context, binding_ids,
                                  source_bindings, applicability, order_history_dependencies):
    """Project only selected existing bindings from an original issued view."""
    from ..orderbook_event_state_snapshot.handoff import (
        _require_public_publication_custody_v1, _public_committed_translations_v1,
        _public_selected_metadata_sources_v1, _public_committed_observations_v1,
    )
    from ..orderbook_event_state_snapshot.integrity import validate_pit_book_integrity_v2
    from .context import _public_refs_v1
    from .source_policy import _prepare_public_response_fence_v1, _public_response_fence_v1
    from .receipts import _public_identity_v1
    from .serialization import deterministic_json
    import time

    entry = _require_public_publication_custody_v1(publication=publication)
    _native_require(type(context) is ComputationExecutionContextV1, "public registry requires an exact context")
    _public_refs_v1(binding_ids)
    _native_require(len(binding_ids) <= 64 and type(source_bindings) is tuple and source_bindings
                    and all(any(row is admitted for admitted in entry[5]) for row in source_bindings),
                    "public registry source identities are not admitted by this publication")
    _native_require(context.source_epoch_id == entry[10] and context.input_version == entry[11],
                    "public registry source epoch/input version mismatch")
    registry_key = (id(publication), context, binding_ids, tuple(id(row) for row in source_bindings), id(applicability),
                    id(order_history_dependencies))
    existing = _PUBLIC_OWNER_REGISTRY_KEYS_V1.get(registry_key)
    if existing is not None:
        for packet in existing.packets:
            _admit_public_packet_custody_v1(registry=existing, packet=packet, context=context)
        return existing
    states = tuple(state for state in entry[3].values()
                   if state.instrument_id == context.scope.instrument_or_contract_scope_id
                   and state.market_id == context.scope.market_scope_id
                   and state.profile_id.value == context.scope.venue_scope_id)
    _native_require(len(states) == 1, "public registry context does not select exactly one published instrument")
    state = states[0]
    _native_require(context.scope.input_snapshot_id == state.state_id,
                    "public registry snapshot identity differs from the published state")
    _native_require(any((state.source_receipt_ref, state.rights_receipt_ref)
                        in set(zip(source.source_receipt_refs, source.rights_receipt_refs)) for source in source_bindings),
                    "selected source bindings do not own this published state")
    metadata_rows = tuple(row for row in entry[4] if row.instrument_id == state.instrument_id)
    _native_require(len(metadata_rows) == 1, "public registry metadata selection is ambiguous")
    metadata = metadata_rows[0]
    original_by_id = {row.observation_id: row for row in _public_committed_observations_v1(publication=publication)}
    committed_translations = _public_committed_translations_v1(publication=publication)
    selected_originals = {row.observation_ref for row in committed_translations
                          if row.stream_disposition.get("instrument_id") == state.instrument_id}
    selected_originals.update(row[0] for row in metadata.field_lineage if row[0] in original_by_id)
    required_sources = {ref for identity in selected_originals for ref in original_by_id[identity].source_binding_refs}
    required_sources.update(row.binding_id for row in _public_selected_metadata_sources_v1(publication=publication,
        metadata=metadata_rows,known_as_of_ns=_native_utc_nanoseconds(context.as_of.isoformat())))
    for original_ref, _, _, _ in metadata.field_lineage:
        if original_ref not in original_by_id:
            required_sources.update(row.binding_id for row in entry[5] if original_ref in row.original_evidence_refs)
    _native_require(required_sources <= {row.binding_id for row in source_bindings},
                    "a material original source binding is missing")
    source_bindings = tuple(row for row in source_bindings if row.binding_id in required_sources)
    _native_require(metadata.event_id_or_none is None or metadata.event_id_or_none == context.scope.event_scope_id,
                    "public registry event scope mismatch")
    validate_pit_book_integrity_v2(state)
    as_of_ns = _native_utc_nanoseconds(context.as_of.isoformat())
    _native_require(entry[8] <= as_of_ns, "public registry context predates actual handle issuance")
    _native_require(as_of_ns <= ((time.time_ns()+999)//1000)*1000, "public registry context is in the future")
    for item in (*source_bindings, metadata):
        _native_require(item.known_at_ns <= as_of_ns < item.expires_at_ns
                        and item.effective_from_ns <= as_of_ns
                        and (item.effective_until_ns_or_none is None or as_of_ns < item.effective_until_ns_or_none),
                        "selected public rule is unavailable at the requested as-of")
    rows = {binding.binding_id: (math_id, binding)
            for math_id, bindings in CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID.items() for binding in bindings}
    selected_rows = []
    for binding_id in binding_ids:
        _native_require(binding_id in rows, "unknown public consumer binding")
        math_id, row = rows[binding_id]
        _native_require(all("FormulaExecutionContractV1::"+math_id in source.permitted_consumer_ids
                            for source in source_bindings), "public source does not permit the selected consumer")
        selected_rows.append((math_id, row))
    yes = tuple(sorted((level for level in state.levels if level.canonical_side == "YES_BID" and level.quantity > 0), key=lambda level: level.price))
    no = tuple(sorted((level for level in state.levels if level.canonical_side == "NO_BID" and level.quantity > 0), key=lambda level: level.price))
    bids = tuple(level for level in state.levels if level.canonical_side == "BID" and level.quantity > 0)
    asks = tuple(level for level in state.levels if level.canonical_side == "ASK" and level.quantity > 0)
    best_bid = bids[0].price_text if bids else None
    best_ask = asks[0].price_text if asks else None
    if state.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT and any(
            math_id != "MATH-39" and row.input_name != "contract_price" for math_id, row in selected_rows):
        _native_require(metadata.price_orientation == "OUTCOME_SIDE" and metadata.payout_amount_or_none is not None,
                        "Kalshi selected price orientation/payout unavailable")
        best_bid = yes[-1].price_text if yes else None
        best_ask = (_native_retail_finite_decimal_text_v1(Fraction(metadata.payout_amount_or_none)-Fraction(no[-1].price))
                    if no else None)
    trades = tuple(row for row in committed_translations
        if row.stream_disposition.get("instrument_id") == state.instrument_id
        and row.stream_disposition.get("event_kind") == "TRADE")
    price_translation = trades[-1] if trades else None
    values = {}
    for math_id, row in selected_rows:
        owner, name = row.accepted_upstream_owner_id, row.input_name
        if owner in {"SelectedVenuePublicMarketDataOwnerV1", "KalshiAcceptedOrderBookStateOwnerV1"}:
            _native_require(state.state_vector.lifecycle_state == "ADMISSIBLE",
                            "selected public lifecycle requires accepted metadata refresh")
        if owner in {"SelectedVenuePublicMarketDataOwnerV1", "KalshiAcceptedOrderBookStateOwnerV1"} and name != "contract_price":
            _native_require(metadata.lifecycle["state"] == "OPEN"
                            and state.state_vector.availability_state.value in {"AVAILABLE_CURRENT_STATE", "AVAILABLE_CHANGE_LEVEL"},
                            "selected public lifecycle/depth capability is unavailable")
        if owner == "SelectedVenuePublicMarketDataOwnerV1" and math_id == "MATH-01" and name == "contract_price":
            _native_require(price_translation is not None and metadata.lifecycle["state"] == "OPEN"
                             and state.state_vector.lifecycle_state == "ADMISSIBLE"
                            and metadata.price_orientation in {"YES", "NO"}
                            and metadata.payout_basis_or_none == "USD_PER_CONTRACT",
                            "admitted trade price orientation/payoff basis unavailable")
            pointer = {Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: "/p",
                       Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: "/trade/price/value",
                       Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT:
                           "/msg/yes_price_dollars" if metadata.price_orientation == "YES" else "/msg/no_price_dollars"}.get(state.profile_id)
            original = original_by_id[price_translation.observation_ref]
            price_sources = tuple(source for source in source_bindings if source.binding_id in original.source_binding_refs)
            fields = tuple(row for source in price_sources for row in source.field_bindings
                if row[4] == pointer and row[1] == "DECIMAL_TEXT" and row[5] == "EXACT_DECIMAL_TEXT"
                and row[2] == "USD_PER_CONTRACT")
            _native_require(len(fields) == 1 and (original.observation_id,pointer,fields[0][0],fields[0][5])
                            in price_translation.field_lineage, "trade price has no exact accepted currency-per-contract binding")
            normalized_price = price_translation.normalized_frame.parsed_source_scalar_tree_or_none
            price = (normalized_price["msg"][pointer.rsplit("/", 1)[1]]
                     if state.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT else normalized_price["price"])
            _native_require(type(price) is str and Fraction(price) >= 0, "invalid admitted contract price")
            values[row.binding_id] = price
        elif owner == "SelectedVenuePublicMarketDataOwnerV1" and name in {
                "best_bid", "best_ask", "same_instrument_snapshot", "snapshot_state"}:
            _native_require(best_bid is not None and best_ask is not None and Fraction(best_bid) <= Fraction(best_ask)
                            and state.state_vector.continuity_state.value == "CONTIGUOUS",
                            "public contiguous top-of-book capability is unavailable")
            values[row.binding_id] = {"best_bid": best_bid, "best_ask": best_ask,
                "same_instrument_snapshot": True, "snapshot_state": "CURRENT_CONTIGUOUS_BOOK"}[name]
        elif owner in {"KalshiAcceptedOrderBookStateOwnerV1", "KalshiMarketMetadataOwnerV1"}:
            _native_require(state.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT and math_id == "MATH-36",
                            "Kalshi owner cannot publish another profile")
            sequence = state.last_provider_sequence_end_or_none
            _native_require(type(sequence) is int, "Kalshi covered native sequence unavailable")
            public_values = {
                "yes_bids": tuple(level.price_text for level in yes),
                "no_bids": tuple(level.price_text for level in no),
                "book_sequence": sequence, "expected_sequence": sequence,
                "book_state": "CURRENT_CONTIGUOUS_SNAPSHOT_PLUS_DELTAS",
                "payout": metadata.payout_amount_or_none,
                "price_ranges": tuple({"minimum": low, "maximum": high, "step": step}
                                      for low, high, step in metadata.price_bands),
            }
            _native_require(name in public_values and public_values[name] is not None,
                            "selected Kalshi metadata capability unavailable")
            values[row.binding_id] = public_values[name]
        elif row.binding_id == "FIVAB::sequenced_book_events::MATH-39":
            values[row.binding_id] = _project_public_order_history_v1(publication=publication, context=context,
                translations=committed_translations, sources=source_bindings, dependencies=order_history_dependencies)
        else:
            raise InputAuthorityError(ReasonCode.INPUT_OWNER_MISSING,
                                      "selected public field requires its separately accepted producer")
    # These are the derived immutable view's receipt/processing clocks, not
    # replacements for original QTT receive/parse clocks retained by the handle.
    issued_at = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=(entry[8]+999)//1000)
    observations = tuple(row for row in committed_translations
                         if row.stream_disposition.get("instrument_id") == state.instrument_id
                         and row.stream_disposition.get("event_kind") in {"BOOK_SNAPSHOT", "BOOK_DELTA", "BOOK_REPLACEMENT"})
    book_selected = any(row.input_name != "contract_price" for _, row in selected_rows)
    _native_require(observations or not book_selected, "published book input lacks original observation clocks")
    last = (observations[-1] if observations else price_translation).exact_clock_companion
    observed_ns = int(last["received"]["utc_ns_text"])
    observed_at = datetime.fromisoformat(last["received"]["receipt_utc_floor"].replace("Z", "+00:00"))
    event = last["provider_event_or_none"]
    effective_at = (datetime.fromisoformat(event["receipt_utc_floor"].replace("Z", "+00:00"))
                    if event is not None else observed_at)
    clocks = PointInTimeClocksV1(observed_at, effective_at, issued_at, issued_at, issued_at, context.as_of)
    trade_clocks = None
    trade_observed_ns = None
    if price_translation is not None:
        trade_clock = price_translation.exact_clock_companion
        trade_observed_ns = int(trade_clock["received"]["utc_ns_text"])
        trade_observed = datetime.fromisoformat(trade_clock["received"]["receipt_utc_floor"].replace("Z", "+00:00"))
        trade_effective = trade_clock["provider_event_or_none"]
        _native_require(trade_effective is not None, "admitted trade has no exact provider event time")
        trade_effective = datetime.fromisoformat(trade_effective["receipt_utc_floor"].replace("Z", "+00:00"))
        trade_clocks = PointInTimeClocksV1(trade_observed, trade_effective, issued_at, issued_at, issued_at, context.as_of)
    metadata_observed = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=metadata.known_at_ns//1000)
    metadata_effective = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=metadata.effective_from_ns//1000)
    metadata_clocks = PointInTimeClocksV1(metadata_observed, metadata_effective, issued_at, issued_at, issued_at, context.as_of)
    maximum_age_ns = ((context.maximum_age.days*86400+context.maximum_age.seconds)*1000000
                      + context.maximum_age.microseconds)*1000
    observed_boundaries = tuple(metadata.known_at_ns if row.accepted_upstream_owner_id == "KalshiMarketMetadataOwnerV1"
                                else trade_observed_ns if row.input_name == "contract_price"
                                else observed_ns for _, row in selected_rows)
    economic_expiry = min(observed_boundaries)+maximum_age_ns
    additional_closure = {}
    if order_history_dependencies is not None:
        dependency_proof = _PUBLIC_OWNER_REGISTRIES_V1.get(id(order_history_dependencies))
        for dependency in order_history_dependencies.packets:
            ttl_ns = ((dependency.ttl.days*86400+dependency.ttl.seconds)*1000000+dependency.ttl.microseconds)*1000
            economic_expiry = min(economic_expiry, _native_utc_nanoseconds(dependency.clocks.observed_time.isoformat())+ttl_ns)
            if dependency_proof is not None:
                for owner_entry, owner_fence in dependency_proof[1][id(dependency)][4]:
                    additional_closure[(id(owner_entry[0]),id(owner_fence))] = (owner_entry,owner_fence)
    _native_require(as_of_ns < economic_expiry, "public economic input is stale at the selected context")
    fence = _prepare_public_response_fence_v1(binding=entry[1]._binding, sources=source_bindings,
        metadata=metadata_rows, applicability=applicability, not_after_ns=economic_expiry)
    packets = tuple(OwnerValuePacketV1(
        packet_id=deterministic_json(("PUBLIC_OWNER_PACKET_V1", entry[7].record_id,
            entry[7].typed_payload.source_use_action_ref, context.context_id, context.scope.identity_tuple,
            context.source_epoch_id, context.input_version, row.binding_id, entry[8], as_of_ns, maximum_age_ns)),
        owner_id=row.accepted_upstream_owner_id, packet_type=row.accepted_packet_or_snapshot_type,
        schema_id=row.schema_id, schema_version=row.schema_version, context_id=context.context_id,
        scope=context.scope, source_epoch_id=context.source_epoch_id, input_version=context.input_version,
        clocks=metadata_clocks if row.accepted_upstream_owner_id == "KalshiMarketMetadataOwnerV1"
            else trade_clocks if row.input_name == "contract_price" else clocks,
        ttl=context.maximum_age, values={row.exact_field_path: values[row.binding_id]},
        authorized_binding_ids=(row.binding_id,), producer_receipt_id=entry[7].record_id,
        producer_receipt_type=row.producer_receipt_type, source_state_and_claim_lineage=row.source_state_and_claim_lineage,
        provider_sequence=None if row.input_name == "contract_price" else state.last_provider_sequence_end_or_none, revision=None,
    ) for index, (_math_id, row) in enumerate(selected_rows))
    retained = []
    for packet in packets:
        prior = _PUBLIC_OWNER_PACKET_ORIGINS_V1.get(packet.packet_id)
        if prior is not None:
            _native_require(prior[2] is entry and prior[0] == packet,
                            "public packet identity conflicts with an earlier issuance")
            packet = prior[0]
        retained.append(packet)
    packets = tuple(retained)
    registry = CanonicalOwnerPacketRegistryV1(packets)
    closure = ((entry,fence), *additional_closure.values())
    origins = {id(packet): (packet, registry, entry, fence, closure, order_history_dependencies) for packet in packets}
    with _public_response_fence_v1(fence):
        _PUBLIC_OWNER_REGISTRIES_V1[id(registry)] = (registry, MappingProxyType(origins), context)
        _PUBLIC_OWNER_REGISTRY_KEYS_V1[registry_key] = registry
        for packet in packets:
            _PUBLIC_OWNER_PACKET_ORIGINS_V1.setdefault(packet.packet_id, origins[id(packet)])
            if entry[12]:
                key = registry._packet_binding_key(packet, packet.authorized_binding_ids[0])
                _PUBLIC_NATIVE_CONTEXT_BINDINGS_V1.add(key)
                _PUBLIC_NATIVE_CONTEXTS_V1.add(key[:-1])
        return registry


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
    public_origin = _PUBLIC_OWNER_PACKET_ORIGINS_V1.get(packet.packet_id)
    if public_origin is not None and public_origin[0] is packet:
        # The frozen public binding declares sequence/revision alternatives.
        # Issued book inputs carry the actual covered sequence; do not invent a
        # provider revision from a local generation or receive ordinal.
        if "sequence/revision required" in binding.provider_native_sequence_or_revision.casefold():
            require_sequence, require_revision = True, False
            if binding.binding_id == "FIVAB::MATH-01::contract_price":
                # The private factory emits this binding only from an admitted
                # committed scalar trade. Its exact snapshot is the alternative
                # named by the existing binding; no sequence is manufactured.
                _native_require(packet.scope.input_snapshot_id == context.scope.input_snapshot_id
                                and packet.provider_sequence is None and packet.revision is None,
                                "scalar trade snapshot identity differs")
                require_sequence = False
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
    by_kind = {kind: Decimal(_native_retail_finite_decimal_text_v1(sum(
        (Fraction(row.quantity) for row in events if row.event_kind is kind), start=Fraction(0))))
        for kind in Math39BookEventKindV1}
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
            receipt_refs=tuple(dict.fromkeys(
                item
                for row in resolved
                for item in (
                    row.producer_receipt_id,
                    row.point_in_time_receipt.receipt_id,
                    row.freshness_receipt.receipt_id,
                )
            )),
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
    """Gate-first D resolver; all repository projections are injected preloaded."""

    def __init__(
        self,
        *,
        repo_root: str | Path,
        owner_registry: CanonicalOwnerPacketRegistryV1,
        canonical_f_evidence_owner: object | None = None,
    ) -> None:
        if canonical_f_evidence_owner is not None and not callable(
            getattr(canonical_f_evidence_owner, "read_evidence_reference", None)
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_OWNER_MISMATCH,
                "F evidence owner must expose the exact read-only reference method",
            )
        self._repo_root = Path(repo_root).resolve()
        self._owner_registry = owner_registry
        self._safety = CurrentSafetyStateAdapterV1(owner_registry)
        self._evidence = (
            CurrentPreFEvidenceAdapterV1()
            if canonical_f_evidence_owner is None
            else canonical_f_evidence_owner
        )
        self._owner_action = CurrentOwnerActionConfirmationAdapterV1(owner_registry)

    @property
    def owner_registry(self) -> CanonicalOwnerPacketRegistryV1:
        return self._owner_registry

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    @property
    def canonical_f_evidence_owner(self) -> object:
        """Return the immutable injected owner; requests cannot replace it."""

        return self._evidence

    @staticmethod
    def _admitted_context(
        request: object,
        capability_decision: object,
    ) -> tuple[object, ComputationExecutionContextV1, str, str]:
        from .agent_policy import AgentCapabilityDecisionV1

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
        return capability_decision, context, causation_id, correlation_id

    @staticmethod
    def _typed_f_reference_query(
        request: object,
        decision: object,
        context: ComputationExecutionContextV1,
        *,
        causation_id: str,
        correlation_id: str,
        safety_receipt_ref: str,
    ) -> object | None:
        from .evidence import FToDEvidenceReferenceQueryV1

        requested_evidence_id = getattr(request, "evidence_id", None)
        expected_input_lock_id = getattr(request, "input_lock_id", None)
        requested_component = getattr(request, "component_id", None)
        expected_epochs = getattr(request, "source_epoch_refs", None)
        evidence_refs = tuple(getattr(decision, "evidence_refs", ()))
        scope_refs = tuple(getattr(decision, "scope_refs", ()))
        request_refs = tuple(getattr(request, "source_candidate_refs", ()))
        tagged_refs = tuple(dict.fromkeys((*request_refs, *evidence_refs)))

        if not isinstance(requested_evidence_id, str) or not requested_evidence_id:
            matches = tuple(
                ref.split("=", 1)[1]
                for ref in tagged_refs
                if ref.startswith("ST12F_EVIDENCE_ID=") and "=" in ref
            )
            requested_evidence_id = matches[0] if len(matches) == 1 else None
        if not isinstance(expected_input_lock_id, str) or not expected_input_lock_id:
            matches = tuple(
                ref.split("=", 1)[1]
                for ref in tagged_refs
                if ref.startswith("ST12F_INPUT_LOCK_ID=") and "=" in ref
            )
            expected_input_lock_id = matches[0] if len(matches) == 1 else None
        if not isinstance(requested_component, str) or not requested_component:
            tagged_matches = tuple(
                ref.split("=", 1)[1]
                for ref in tagged_refs
                if ref.startswith("ST12F_COMPONENT_OR_TEMPLATE_REF=")
                and "=" in ref
            )
            scope_matches = tuple(ref for ref in scope_refs if ref.startswith("MATH-"))
            requested_component = (
                tagged_matches[0]
                if len(tagged_matches) == 1
                else scope_matches[0]
                if len(scope_matches) == 1
                else None
            )
        if not isinstance(expected_epochs, tuple) or not expected_epochs:
            expected_epochs = tuple(
                ref.split("ST12F_SOURCE_EPOCH=", 1)[1]
                for ref in tagged_refs
                if ref.startswith("ST12F_SOURCE_EPOCH=")
            )
        if (
            not isinstance(requested_evidence_id, str)
            or not requested_evidence_id
            or not isinstance(expected_input_lock_id, str)
            or not expected_input_lock_id
            or not isinstance(requested_component, str)
            or not requested_component
            or not isinstance(expected_epochs, tuple)
            or not expected_epochs
        ):
            return None
        return FToDEvidenceReferenceQueryV1(
            query_id=f"ST12D-F-QUERY::{getattr(decision, 'request_id')}",
            requested_evidence_id=requested_evidence_id,
            requested_component_or_template_ref=requested_component,
            expected_input_lock_id=expected_input_lock_id,
            expected_source_epoch_refs=expected_epochs,
            evaluated_at=context.as_of,
            request_read_lineage_refs=tuple(
                dict.fromkeys(
                    (
                        getattr(decision, "agent_orch_receipt_ref"),
                        safety_receipt_ref,
                        causation_id,
                        correlation_id,
                    )
                )
            ),
        )

    @staticmethod
    def _validate_f_reference_for_d(
        *,
        context: ComputationExecutionContextV1,
        query: object | None,
        reference: ST12FEvidenceReferenceV1,
        causation_id: str,
        correlation_id: str,
    ) -> ST12FEvidenceReferenceV1:
        if reference.evidence_state is not ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE:
            return reference
        valid = (
            query is not None
            and reference.reference_id != "EXPLICIT_ABSENCE"
            and reference.evidence_id == getattr(query, "requested_evidence_id", None)
            and reference.component_or_template_ref
            == getattr(query, "requested_component_or_template_ref", None)
            and reference.input_lock_id
            == getattr(query, "expected_input_lock_id", None)
            and reference.source_epoch_refs
            == getattr(query, "expected_source_epoch_refs", None)
            and reference.lane == "REPLAY_PAPER"
            and reference.terminal_state == "CLOSED_INDEPENDENTLY_VALIDATED"
            and reference.evidence_ref.startswith("ST12F-RECEIPT::")
            and reference.contract_version == "1.4"
            and reference.no_effect_flags == NO_EFFECTS_V1
            and reference.observed_at
            <= getattr(query, "evaluated_at", context.as_of)
            <= reference.valid_until
        )
        if valid:
            return reference
        from .mode_snapshot_policy import pre_f_unavailable_reference

        return pre_f_unavailable_reference(
            observed_at=context.as_of,
            valid_until=context.as_of,
            causation_id=causation_id,
            correlation_id=correlation_id,
        )

    def resolve_mode_snapshot_preconstruction_gate(
        self,
        request: object,
        capability_decision: object,
    ) -> object:
        from .mode_snapshot_policy import ModeSnapshotPreconstructionGateV1

        decision, context, causation_id, correlation_id = self._admitted_context(
            request,
            capability_decision,
        )
        safety = self._safety.read_kill_submit_state(context)
        safety_packet = self._owner_registry.packet_for(
            context=context,
            binding_id=ST12D_SAFETY_BINDING_ID,
        )
        if getattr(self._evidence, "supports_typed_reference_query", False):
            query = self._typed_f_reference_query(
                request,
                decision,
                context,
                causation_id=causation_id,
                correlation_id=correlation_id,
                safety_receipt_ref=safety_packet.producer_receipt_id,
            )
            evidence = self._evidence.read_evidence_reference(
                context,
                causation_id=causation_id,
                correlation_id=correlation_id,
                query=query,
            )
            evidence = self._validate_f_reference_for_d(
                context=context,
                query=query,
                reference=evidence,
                causation_id=causation_id,
                correlation_id=correlation_id,
            )
        else:
            evidence = self._evidence.read_evidence_reference(
                context,
                causation_id=causation_id,
                correlation_id=correlation_id,
            )
        evidence_receipt_refs = (
            (
                f"ST12F-RECEIPT::{evidence.reference_id}::D_EVIDENCE_REFERENCE",
            )
            if evidence.evidence_state
            is ST12FEvidenceStateV1.EVIDENCE_REFERENCE_AVAILABLE
            else ()
        )
        return ModeSnapshotPreconstructionGateV1(
            request_id=decision.request_id,
            principal_id=decision.principal_id,
            task_id=decision.task_id,
            current_agent_id=decision.current_agent_id,
            capability_decision_ref=decision.decision_id,
            context_ref=context.context_id,
            current_mode=context.scope.mode_context_id,
            requested_mode="HOTPATH_CANDIDATE_ONLY",
            candidate_version=context.input_version,
            evaluated_at=context.as_of,
            expires_at=min(
                context.as_of + context.maximum_age,
                safety.valid_until,
                evidence.valid_until,
            ),
            causation_id=causation_id,
            correlation_id=correlation_id,
            receipt_lineage_refs=tuple(
                dict.fromkeys(
                    (
                        decision.agent_orch_receipt_ref,
                        safety_packet.producer_receipt_id,
                        *evidence_receipt_refs,
                    )
                )
            ),
            source_epoch_refs=tuple(
                dict.fromkeys(
                    (
                        safety_packet.source_epoch_id,
                        *evidence.source_epoch_refs,
                    )
                )
            ),
            evidence_reference=evidence,
            kill_submit_state=safety,
        )

    def enrich_mode_snapshot_candidate(
        self,
        request: object,
        capability_decision: object,
        preconstruction_gate: object,
        owner_projections: object,
    ) -> object:
        from .implementation_registry import ST12D_MATH_IMPLEMENTATION_REGISTRY
        from .mode_snapshot_policy import (
            ModeSnapshotCandidateInputsV1,
            ModeSnapshotPreconstructionGateV1,
        )
        from .parameter_policy import (
            ST12D_PARAMETER_POLICY_SET_VERSION,
            resolve_st12d_snapshot_parameter_values,
        )
        from .protocols import PreloadedOwnerProjectionBundleV1
        from .stack_resolver import preflight_snapshot_computation_bundle
        from .models import SnapshotParameterResolutionStateV1

        decision, context, causation_id, correlation_id = self._admitted_context(
            request,
            capability_decision,
        )
        if (
            type(preconstruction_gate) is not ModeSnapshotPreconstructionGateV1
            or type(owner_projections) is not PreloadedOwnerProjectionBundleV1
            or preconstruction_gate.request_id != decision.request_id
            or preconstruction_gate.context_ref != context.context_id
            or preconstruction_gate.causation_id != causation_id
            or preconstruction_gate.correlation_id != correlation_id
        ):
            raise InputAuthorityError(
                ReasonCode.INPUT_SCOPE_MISMATCH,
                "D enrichment requires the admitted gate and one preloaded owner bundle",
            )
        owner_action = self._owner_action.read_owner_action_confirmation(context)
        owner_action_packet = self._owner_registry.packet_for(
            context=context,
            binding_id=ST12D_OWNER_ACTION_BINDING_ID,
        )
        resolved_parameter_values = resolve_st12d_snapshot_parameter_values(
            context=context,
            owner_registry=self._owner_registry,
        )
        unavailable = tuple(
            row
            for row in resolved_parameter_values
            if row.resolution_state
            is SnapshotParameterResolutionStateV1.REQUIRED_OWNER_VALUE_UNAVAILABLE
        )
        if unavailable:
            raise InputAuthorityError(
                unavailable[0].diagnostic_reason_codes[0],
                "D candidate construction is blocked by unresolved snapshot parameter values: "
                + ", ".join(row.parameter_id for row in unavailable),
            )
        parameter_value_refs = tuple(
            row.resolved_value_ref for row in resolved_parameter_values
        )
        parameter_policy_snapshot_ref = (
            f"ComputationParameterPolicyV1::{ST12D_PARAMETER_POLICY_SET_VERSION}"
        )
        formula_input_resolutions = tuple(
            FormulaInputResolverV1.resolve(
                math_id,
                context=context,
                owner_registry=self._owner_registry,
            )
            for math_id in ST12D_MATH_IMPLEMENTATION_REGISTRY
        )
        consumed_formula_epochs = tuple(
            self._owner_registry.packet_by_id(packet_id).source_epoch_id
            for resolution in formula_input_resolutions
            for packet_id in resolution.packet_refs
        )
        source_epoch_refs = tuple(
            dict.fromkeys(
                (
                    *consumed_formula_epochs,
                    *(
                        epoch
                        for row in resolved_parameter_values
                        for epoch in row.source_epoch_refs
                    ),
                    *preconstruction_gate.source_epoch_refs,
                    owner_action_packet.source_epoch_id,
                    *owner_projections.source_epoch_refs,
                )
            )
        )
        bundle = preflight_snapshot_computation_bundle(
            context=context,
            owner_registry=self._owner_registry,
            parameter_policy_snapshot_ref=parameter_policy_snapshot_ref,
            parameter_value_refs=parameter_value_refs,
            resolved_parameter_values=resolved_parameter_values,
            source_epoch_refs=source_epoch_refs,
            formula_input_resolutions=formula_input_resolutions,
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
                    decision.agent_orch_receipt_ref,
                    *preconstruction_gate.receipt_lineage_refs,
                    owner_action.receipt_ref,
                    owner_action_packet.producer_receipt_id,
                    *(
                        ref
                        for resolution in formula_input_resolutions
                        for ref in resolution.receipt_refs
                    ),
                    *(
                        ref
                        for row in resolved_parameter_values
                        for ref in (
                            *row.producer_receipt_refs,
                            *row.point_in_time_receipt_refs,
                            *row.freshness_receipt_refs,
                        )
                    ),
                    *(
                        (
                            owner_action.predecessor_transition_receipt_ref_or_explicit_absence,
                        )
                        if owner_action.predecessor_transition_receipt_proposal_or_explicit_absence
                        is not None
                        else ()
                    ),
                    *owner_projections.receipt_refs,
                )
            )
        )
        expires_at = min(
            context.as_of + context.maximum_age,
            preconstruction_gate.kill_submit_state.valid_until,
            owner_action.valid_until,
        )
        return ModeSnapshotCandidateInputsV1(
            request_id=decision.request_id,
            principal_id=decision.principal_id,
            task_id=decision.task_id,
            current_agent_id=decision.current_agent_id,
            capability_decision_ref=decision.decision_id,
            computation_bundle_ref=bundle.bundle_ref,
            context_ref=context.context_id,
            formula_spec_refs=tuple(ST12D_MATH_IMPLEMENTATION_REGISTRY),
            implementation_version_pins=implementation_pins,
            binding_profile_ref=(
                f"ComputationBindingProfileV1::{context.binding_profile_version}"
            ),
            parameter_policy_snapshot_ref=parameter_policy_snapshot_ref,
            parameter_value_refs=parameter_value_refs,
            resolved_parameter_values=resolved_parameter_values,
            source_epoch_refs=source_epoch_refs,
            receipt_lineage_refs=receipt_lineage_refs,
            readiness_state_ref=(
                f"READINESS1::{owner_projections.readiness.source_version}"
            ),
            pretrade_state_ref=(
                f"PRETRADE1::{owner_projections.pretrade.source_version}"
            ),
            owner_action_policy_ref=owner_action.owner_action_policy_ref,
            current_mode=context.scope.mode_context_id,
            requested_mode="HOTPATH_CANDIDATE_ONLY",
            expected_owner_state_ref=(
                f"SVC1::{owner_projections.svc.source_version}"
            ),
            candidate_version=context.input_version,
            created_at=context.as_of,
            evaluated_at=context.as_of,
            expires_at=expires_at,
            causation_id=causation_id,
            correlation_id=correlation_id,
            evidence_reference=preconstruction_gate.evidence_reference,
            kill_submit_state=preconstruction_gate.kill_submit_state,
            computation_bundle_closure=bundle,
            owner_action_confirmation=owner_action,
        )


PIT_PUBLIC_INPUT_OWNER_IDS_V1 = frozenset(
    {
        "SelectedVenuePublicMarketDataOwnerV1",
        "KalshiAcceptedOrderBookStateOwnerV1",
        "KalshiMarketMetadataOwnerV1",
    }
)
PIT_PUBLIC_ORIGIN_CLASSES_V1 = frozenset(
    {
        "ACCEPTED_POINT_IN_TIME_SNAPSHOT",
        "ACCEPTED_VERSIONED_MARKET_METADATA",
    }
)
PIT_RAW_INPUT_PACKET_TYPES_V1 = frozenset({"SequencedBookEventsPacketV1"})


def _pit_input_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


def _pit_input_text_tuple(
    value: object,
    name: str,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple or (not allow_empty and not value):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be an exact tuple",
        )
    result = tuple(_pit_input_text(item, name) for item in value)
    if len(result) != len(set(result)):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
            f"{name} contains duplicate identities",
        )
    return result


@dataclass(frozen=True, slots=True)
class PITFormulaInputAuthorityPartitionV1:
    all_binding_ids: frozenset[str]
    pit_applicable_binding_ids: frozenset[str]
    non_pit_binding_ids: frozenset[str]
    canonical_binding_order: tuple[str, ...]
    pit_applicable_binding_order: tuple[str, ...]
    non_pit_binding_order: tuple[str, ...]
    all_row_count: int
    pit_row_count: int
    non_pit_row_count: int
    intersection_empty: bool
    union_complete: bool
    duplicate_binding_identity_count: int
    duplicate_object_inclusion_count: int
    unclassified_row_type_count: int

    def __post_init__(self) -> None:
        for name in (
            "all_binding_ids",
            "pit_applicable_binding_ids",
            "non_pit_binding_ids",
        ):
            value = getattr(self, name)
            if type(value) is not frozenset or any(
                type(item) is not str or not item for item in value
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact text frozenset",
                )
        for name, expected_set in (
            ("canonical_binding_order", self.all_binding_ids),
            ("pit_applicable_binding_order", self.pit_applicable_binding_ids),
            ("non_pit_binding_order", self.non_pit_binding_ids),
        ):
            ordered = _pit_input_text_tuple(
                getattr(self, name), name, allow_empty=True
            )
            if frozenset(ordered) != expected_set:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                    f"{name} does not equal its binding-ID set",
                )
        for name in (
            "all_row_count",
            "pit_row_count",
            "non_pit_row_count",
            "duplicate_binding_identity_count",
            "duplicate_object_inclusion_count",
            "unclassified_row_type_count",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be a nonnegative exact integer",
                )
        if type(self.intersection_empty) is not bool or type(
            self.union_complete
        ) is not bool:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "partition laws must be exact booleans",
            )
        if (
            self.all_row_count != len(self.canonical_binding_order)
            or self.pit_row_count != len(self.pit_applicable_binding_order)
            or self.non_pit_row_count != len(self.non_pit_binding_order)
            or self.pit_row_count + self.non_pit_row_count != self.all_row_count
            or not self.intersection_empty
            or not self.union_complete
            or self.duplicate_binding_identity_count
            or self.duplicate_object_inclusion_count
            or self.unclassified_row_type_count
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "formula-input authority partition is not exact and total",
            )


def _pit_formula_rows_once() -> tuple[object, ...]:
    rows: list[object] = []
    for math_id, values in CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID.items():
        _pit_input_text(math_id, "math_id")
        if type(values) is not tuple:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "formula-input authority registry values must be exact tuples",
            )
        rows.extend(values)
    return tuple(rows)


def _pit_binding_id(row: object) -> str:
    if type(row) not in {
        FormulaInputAuthorityBindingV1,
        ST12DMath39RawInputBindingV1,
    }:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"unclassified formula-input authority row type: {type(row).__name__}",
        )
    return _pit_input_text(row.binding_id, "binding_id")


def _pit_row_is_applicable(row: object) -> bool:
    if type(row) is FormulaInputAuthorityBindingV1:
        return (
            row.accepted_upstream_owner_id in PIT_PUBLIC_INPUT_OWNER_IDS_V1
            and row.allowed_origin_class in PIT_PUBLIC_ORIGIN_CLASSES_V1
        )
    if type(row) is ST12DMath39RawInputBindingV1:
        return (
            row.accepted_upstream_owner_id
            == "SelectedVenuePublicMarketDataOwnerV1"
            and row.accepted_packet_or_snapshot_type in PIT_RAW_INPUT_PACKET_TYPES_V1
            and row.binding_id == "FIVAB::sequenced_book_events::MATH-39"
            and row.input_name == "sequenced_book_events"
        )
    _pit_binding_id(row)
    raise AssertionError("unreachable unclassified formula-input row")


def partition_pit_formula_input_authority_v1() -> PITFormulaInputAuthorityPartitionV1:
    """Partition the current registry once, preserving exact canonical order."""

    rows = _pit_formula_rows_once()
    all_ids: list[str] = []
    pit_ids: list[str] = []
    non_pit_ids: list[str] = []
    object_ids: list[int] = []
    unclassified = 0
    for row in rows:
        if type(row) not in {
            FormulaInputAuthorityBindingV1,
            ST12DMath39RawInputBindingV1,
        }:
            unclassified += 1
            continue
        binding_id = _pit_binding_id(row)
        all_ids.append(binding_id)
        object_ids.append(id(row))
        (pit_ids if _pit_row_is_applicable(row) else non_pit_ids).append(binding_id)
    duplicate_binding_count = len(all_ids) - len(set(all_ids))
    duplicate_object_count = len(object_ids) - len(set(object_ids))
    all_set = frozenset(all_ids)
    pit_set = frozenset(pit_ids)
    non_pit_set = frozenset(non_pit_ids)
    return PITFormulaInputAuthorityPartitionV1(
        all_binding_ids=all_set,
        pit_applicable_binding_ids=pit_set,
        non_pit_binding_ids=non_pit_set,
        canonical_binding_order=tuple(all_ids),
        pit_applicable_binding_order=tuple(pit_ids),
        non_pit_binding_order=tuple(non_pit_ids),
        all_row_count=len(rows),
        pit_row_count=len(pit_ids),
        non_pit_row_count=len(non_pit_ids),
        intersection_empty=pit_set.isdisjoint(non_pit_set),
        union_complete=pit_set | non_pit_set == all_set,
        duplicate_binding_identity_count=duplicate_binding_count,
        duplicate_object_inclusion_count=duplicate_object_count,
        unclassified_row_type_count=unclassified,
    )


@dataclass(frozen=True, slots=True)
class PITInputCapabilityV2:
    capability_id: str
    profile_id: Stage1VenueProfileIdV1
    binding_id: str
    math_spec_id: str
    input_name: str
    accepted_packet_or_snapshot_type: str
    source_field_path: str
    declared_input_type: str
    declared_shape_or_none: str | None
    unit_or_basis: str
    transform: str
    required_clock_fields: tuple[str, ...]
    required_depth_class_or_none: PITDepthClassV2 | None
    provider_sequence_required: bool
    provider_publication_time_required: bool
    required_state: str
    source_contract_ref: str
    rights_receipt_ref: str
    availability: PITInputAvailabilityV2
    unavailable_reason_or_none: PITReasonCodeV1 | None
    event_or_snapshot_ref_or_none: str | None
    freshness_receipt_ref_or_none: str | None
    context_id: str
    source_epoch_id: str
    input_version: str

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "profile_id must be an exact Stage1VenueProfileIdV1",
            )
        for name in (
            "capability_id",
            "binding_id",
            "math_spec_id",
            "input_name",
            "accepted_packet_or_snapshot_type",
            "source_field_path",
            "declared_input_type",
            "unit_or_basis",
            "transform",
            "required_state",
            "source_contract_ref",
            "rights_receipt_ref",
            "context_id",
            "source_epoch_id",
            "input_version",
        ):
            _pit_input_text(getattr(self, name), name)
        if self.declared_shape_or_none is not None:
            _pit_input_text(self.declared_shape_or_none, "declared_shape_or_none")
        _pit_input_text_tuple(
            self.required_clock_fields,
            "required_clock_fields",
            allow_empty=False,
        )
        if self.required_depth_class_or_none is not None and type(
            self.required_depth_class_or_none
        ) is not PITDepthClassV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TOP_LEVEL_DEPTH_ONLY,
                "required depth class has the wrong exact type",
            )
        for name in (
            "provider_sequence_required",
            "provider_publication_time_required",
        ):
            if type(getattr(self, name)) is not bool:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact boolean",
                )
        if type(self.availability) is not PITInputAvailabilityV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "availability has the wrong exact type",
            )
        if self.unavailable_reason_or_none is not None and type(
            self.unavailable_reason_or_none
        ) is not PITReasonCodeV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "unavailable reason has the wrong exact type",
            )
        for name in (
            "event_or_snapshot_ref_or_none",
            "freshness_receipt_ref_or_none",
        ):
            value = getattr(self, name)
            if value is not None:
                _pit_input_text(value, name)
        if self.availability is PITInputAvailabilityV2.AVAILABLE:
            if (
                self.unavailable_reason_or_none is not None
                or self.event_or_snapshot_ref_or_none is None
                or self.freshness_receipt_ref_or_none is None
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                    "available capability requires exact event and freshness lineage",
                )
        elif (
            self.unavailable_reason_or_none is None
            or self.event_or_snapshot_ref_or_none is not None
            or self.freshness_receipt_ref_or_none is not None
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "unavailable capability requires a reason and no admitted lineage",
            )

    @property
    def key(self) -> tuple[Stage1VenueProfileIdV1, str]:
        return (self.profile_id, self.binding_id)


@dataclass(frozen=True, slots=True)
class PITFormulaInputPacketV2:
    packet_id: str
    profile_id: Stage1VenueProfileIdV1
    binding_id: str
    context_id: str
    source_epoch_id: str
    input_version: str
    declared_input_type: str
    declared_shape_or_none: str | None
    unit_or_basis: str
    source_field_path: str
    value: object
    event_or_snapshot_ref: str
    freshness_receipt_ref: str

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "packet profile has the wrong exact type",
            )
        for name in (
            "packet_id",
            "binding_id",
            "context_id",
            "source_epoch_id",
            "input_version",
            "declared_input_type",
            "unit_or_basis",
            "source_field_path",
            "event_or_snapshot_ref",
            "freshness_receipt_ref",
        ):
            _pit_input_text(getattr(self, name), name)
        if self.declared_shape_or_none is not None:
            _pit_input_text(self.declared_shape_or_none, "declared_shape_or_none")
        object.__setattr__(self, "value", _freeze(self.value))

    @property
    def key(self) -> tuple[Stage1VenueProfileIdV1, str]:
        return (self.profile_id, self.binding_id)


@dataclass(frozen=True, slots=True)
class PITResolvedFormulaInputV2:
    profile_id: Stage1VenueProfileIdV1
    binding_id: str
    math_spec_id: str
    input_name: str
    value: object
    declared_input_type: str
    declared_shape_or_none: str | None
    unit_or_basis: str
    source_field_path: str
    context_id: str
    source_epoch_id: str
    input_version: str
    packet_ref: str
    event_or_snapshot_ref: str
    freshness_receipt_ref: str

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "resolved profile has the wrong exact type",
            )
        for name in (
            "binding_id",
            "math_spec_id",
            "input_name",
            "declared_input_type",
            "unit_or_basis",
            "source_field_path",
            "context_id",
            "source_epoch_id",
            "input_version",
            "packet_ref",
            "event_or_snapshot_ref",
            "freshness_receipt_ref",
        ):
            _pit_input_text(getattr(self, name), name)
        if self.declared_shape_or_none is not None:
            _pit_input_text(self.declared_shape_or_none, "declared_shape_or_none")
        object.__setattr__(self, "value", _freeze(self.value))


@dataclass(frozen=True, slots=True)
class PITFormulaInputResolutionV2:
    resolution_id: str
    context_id: str
    source_epoch_id: str
    input_version: str
    resolved_inputs: tuple[PITResolvedFormulaInputV2, ...]
    unavailable_capabilities: tuple[PITInputCapabilityV2, ...]
    required_keys: frozenset[tuple[Stage1VenueProfileIdV1, str]]
    exact_key_set_equal: bool

    def __post_init__(self) -> None:
        for name in (
            "resolution_id",
            "context_id",
            "source_epoch_id",
            "input_version",
        ):
            _pit_input_text(getattr(self, name), name)
        if type(self.resolved_inputs) is not tuple or any(
            type(value) is not PITResolvedFormulaInputV2
            for value in self.resolved_inputs
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "resolved_inputs must be exact PITResolvedFormulaInputV2 values",
            )
        if type(self.unavailable_capabilities) is not tuple or any(
            type(value) is not PITInputCapabilityV2
            for value in self.unavailable_capabilities
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "unavailable_capabilities must contain exact capabilities",
            )
        if type(self.required_keys) is not frozenset or any(
            type(key) is not tuple
            or len(key) != 2
            or type(key[0]) is not Stage1VenueProfileIdV1
            or type(key[1]) is not str
            for key in self.required_keys
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "required_keys has an invalid exact key",
            )
        if type(self.exact_key_set_equal) is not bool or not self.exact_key_set_equal:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "formula-input resolution key set is not exact",
            )


def _pit_resolution_binding_metadata(binding_id: str) -> dict[str, object]:
    matches = tuple(
        row
        for row in _pit_formula_rows_once()
        if type(row)
        in {FormulaInputAuthorityBindingV1, ST12DMath39RawInputBindingV1}
        and row.binding_id == binding_id
        and _pit_row_is_applicable(row)
    )
    if len(matches) != 1:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
            "capability binding identity does not resolve exactly once",
        )
    row = matches[0]
    if type(row) is FormulaInputAuthorityBindingV1:
        shape_by_exact_type = {
            "Decimal string": "SCALAR",
            "boolean": "SCALAR",
            "enum": "SCALAR",
            "int": "SCALAR",
            "list[Decimal string]": "SEQUENCE",
            "list[record]": "SEQUENCE",
        }
        try:
            shape = shape_by_exact_type[row.input_type]
        except KeyError as exc:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "formula binding has an unclassified exact input type",
            ) from exc
        return {
            "math_spec_id": row.math_spec_id,
            "input_name": row.input_name,
            "packet_type": row.accepted_packet_or_snapshot_type,
            "source_path": row.exact_field_path,
            "input_type": row.input_type,
            "shape": shape,
            "unit": row.unit_or_basis,
            "transform": row.canonical_typed_value_extraction,
            "required_clock_fields": tuple(row.required_clock_fields),
        }
    if type(row) is ST12DMath39RawInputBindingV1:
        return {
            "math_spec_id": "MATH-39",
            "input_name": row.input_name,
            "packet_type": row.accepted_packet_or_snapshot_type,
            "source_path": row.exact_field_path,
            "input_type": "SequencedBookEventsPacketV1",
            "shape": "SEQUENCE",
            "unit": row.unit_or_basis,
            "transform": row.point_in_time_rule,
            "required_clock_fields": (
                "qtt_received_at_utc",
                "qtt_parse_completed_at_utc",
                "durable_commit_completed_at_utc",
                "strategy_available_at_utc",
            ),
        }
    raise AssertionError("unreachable exact formula binding type")


def _pit_validate_resolution_capability_metadata(
    capability: PITInputCapabilityV2,
) -> None:
    expected = _pit_resolution_binding_metadata(capability.binding_id)
    actual = {
        "math_spec_id": capability.math_spec_id,
        "input_name": capability.input_name,
        "packet_type": capability.accepted_packet_or_snapshot_type,
        "source_path": capability.source_field_path,
        "input_type": capability.declared_input_type,
        "shape": capability.declared_shape_or_none,
        "unit": capability.unit_or_basis,
        "transform": capability.transform,
        "required_clock_fields": capability.required_clock_fields,
    }
    if actual != expected:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
            "capability metadata differs from the canonical formula-input binding",
        )


def _pit_packet_value_matches_type(value: object, declared_type: str) -> bool:
    if declared_type == "boolean":
        return type(value) is bool
    if declared_type == "int":
        return type(value) is int
    if declared_type == "Decimal string":
        if type(value) is not str:
            return False
        try:
            exact_decimal(value, field_name="PIT formula input")
        except NumericDomainError:
            return False
        return True
    if declared_type == "list[Decimal string]":
        if type(value) is not tuple or not value:
            return False
        try:
            for item in value:
                if type(item) is not str:
                    return False
                exact_decimal(item, field_name="PIT formula input list")
        except NumericDomainError:
            return False
        return True
    if declared_type == "enum":
        return type(value) is str and bool(value)
    if declared_type in {"list[record]", "SequencedBookEventsPacketV1"}:
        return (
            type(value) is tuple
            and bool(value)
            and all(isinstance(item, Mapping) for item in value)
        )
    return False


def resolve_pit_formula_inputs_v2(
    capabilities: tuple[PITInputCapabilityV2, ...],
    packets: tuple[PITFormulaInputPacketV2, ...],
    *,
    resolution_id: str,
    context_id: str,
    source_epoch_id: str,
    input_version: str,
) -> PITFormulaInputResolutionV2:
    """Resolve available capabilities without synthesizing missing truth."""

    _pit_input_text(resolution_id, "resolution_id")
    for name, value in (
        ("context_id", context_id),
        ("source_epoch_id", source_epoch_id),
        ("input_version", input_version),
    ):
        _pit_input_text(value, name)
    if type(capabilities) is not tuple or any(
        type(value) is not PITInputCapabilityV2 for value in capabilities
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "capabilities must be an exact PITInputCapabilityV2 tuple",
        )
    if type(packets) is not tuple or any(
        type(value) is not PITFormulaInputPacketV2 for value in packets
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "packets must be an exact PITFormulaInputPacketV2 tuple",
        )
    capability_by_key: dict[
        tuple[Stage1VenueProfileIdV1, str], PITInputCapabilityV2
    ] = {}
    for capability in capabilities:
        _pit_validate_resolution_capability_metadata(capability)
        if capability.key in capability_by_key:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "duplicate PIT capability key",
            )
        capability_by_key[capability.key] = capability
    packet_by_key: dict[
        tuple[Stage1VenueProfileIdV1, str], PITFormulaInputPacketV2
    ] = {}
    for packet in packets:
        if packet.key in packet_by_key:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "duplicate PIT formula-input packet key",
            )
        packet_by_key[packet.key] = packet
    available_keys = {
        key
        for key, capability in capability_by_key.items()
        if capability.availability is PITInputAvailabilityV2.AVAILABLE
    }
    if set(packet_by_key) != available_keys:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
            "packet keys must equal available capability keys exactly",
        )
    resolved: list[PITResolvedFormulaInputV2] = []
    unavailable: list[PITInputCapabilityV2] = []
    for capability in capabilities:
        if (
            capability.context_id != context_id
            or capability.source_epoch_id != source_epoch_id
            or capability.input_version != input_version
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "capability context/source epoch/input version mismatch",
            )
        if capability.availability is not PITInputAvailabilityV2.AVAILABLE:
            unavailable.append(capability)
            continue
        packet = packet_by_key[capability.key]
        equality_pairs = (
            (packet.context_id, capability.context_id),
            (packet.source_epoch_id, capability.source_epoch_id),
            (packet.input_version, capability.input_version),
            (packet.declared_input_type, capability.declared_input_type),
            (packet.declared_shape_or_none, capability.declared_shape_or_none),
            (packet.unit_or_basis, capability.unit_or_basis),
            (packet.source_field_path, capability.source_field_path),
            (packet.event_or_snapshot_ref, capability.event_or_snapshot_ref_or_none),
            (packet.freshness_receipt_ref, capability.freshness_receipt_ref_or_none),
        )
        if any(left != right for left, right in equality_pairs):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "packet metadata does not exactly equal the capability binding",
            )
        if not _pit_packet_value_matches_type(
            packet.value, capability.declared_input_type
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
                "packet value does not match the exact declared input type",
            )
        resolved.append(
            PITResolvedFormulaInputV2(
                profile_id=capability.profile_id,
                binding_id=capability.binding_id,
                math_spec_id=capability.math_spec_id,
                input_name=capability.input_name,
                value=packet.value,
                declared_input_type=capability.declared_input_type,
                declared_shape_or_none=capability.declared_shape_or_none,
                unit_or_basis=capability.unit_or_basis,
                source_field_path=capability.source_field_path,
                context_id=context_id,
                source_epoch_id=source_epoch_id,
                input_version=input_version,
                packet_ref=packet.packet_id,
                event_or_snapshot_ref=packet.event_or_snapshot_ref,
                freshness_receipt_ref=packet.freshness_receipt_ref,
            )
        )
    required_keys = frozenset(capability_by_key)
    actual_keys = {
        (value.profile_id, value.binding_id) for value in resolved
    } | {value.key for value in unavailable}
    return PITFormulaInputResolutionV2(
        resolution_id=resolution_id,
        context_id=context_id,
        source_epoch_id=source_epoch_id,
        input_version=input_version,
        resolved_inputs=tuple(resolved),
        unavailable_capabilities=tuple(unavailable),
        required_keys=required_keys,
        exact_key_set_equal=actual_keys == set(required_keys),
    )


# F14 pending references are separate from the closed formula input registry.
from _thread import RLock
from .context import _f14_freeze_v1, _f14_plain_v1
from .source_policy import RetailPrivateSourceRegistryV1, _f14_ingress_require_v1


class PrivateObservationPublisherV1:
    def __init__(self, *, source_registry):
        _f14_ingress_require_v1(type(source_registry) is RetailPrivateSourceRegistryV1,
            'F14_INGRESS_SOURCE')
        self.source_registry = source_registry
        self._lock = RLock()
        self._slots = {}
        self._requests = {}

    def _capture_v1(self, observed):
        entry = self.source_registry._captures.get(id(observed))
        _f14_ingress_require_v1(entry is not None and entry[0] is observed and entry[3] is True,
            'F14_INGRESS_CAPTURE_ASSOCIATION')
        return entry

    def publish_private_reference_v1(self, observed, raw_record_ref, capture_commit_ref):
        with self.source_registry._lock:
            entry = self._capture_v1(observed)
            request, attempt = entry[2], entry[4]
            with self.source_registry.fenced(request.grant, request.operation):
                _f14_ingress_require_v1(raw_record_ref == attempt + ':raw'
                    and capture_commit_ref == attempt + ':capture', 'F14_INGRESS_PUBLICATION_BINDING')
                key = (observed.session_binding.source_snapshot_ref, attempt)
                with self._lock:
                    existing = self._slots.get(key)
                    if existing is not None:
                        _f14_ingress_require_v1(existing['observed'] is observed
                            and existing['raw_record_ref'] == raw_record_ref
                            and existing['capture_commit_ref'] == capture_commit_ref
                            and existing['state'] in ('PENDING', 'RESOLVED')
                            and existing['published_clock'] is not None,
                            'F14_INGRESS_PUBLICATION_OUTCOME_UNKNOWN')
                        return existing['published_clock']
                    slot = dict(observed=observed, raw_record_ref=raw_record_ref,
                        capture_commit_ref=capture_commit_ref, state='OUTCOME_UNKNOWN',
                        published_clock=None, resolution=None, result=None)
                    self._slots[key] = slot
                    slot['state'] = 'PENDING'
                    try:
                        published = self.source_registry._observe_v1(request.grant)
                    except Exception:
                        slot['state'] = 'OUTCOME_UNKNOWN'
                        raise
                    slot['published_clock'] = published
                    return published

    def _bind_resolution_v1(self, observed, snapshot, observation, decision_time, recorded_cutoff):
        entry = self._capture_v1(observed)
        key = (observed.session_binding.source_snapshot_ref, entry[4])
        with self._lock:
            slot = self._slots.get(key)
            _f14_ingress_require_v1(slot is not None and slot['state'] == 'PENDING',
                'F14_INGRESS_PUBLICATION_OUTCOME_UNKNOWN')
            slot['resolution'] = (snapshot, observation, observed.session_binding, decision_time, recorded_cutoff)

    def resolve_committed_private_observation_v1(self, snapshot, observation, source_binding,
            decision_time, recorded_cutoff):
        from .persistence import PrivateEvidenceReadSnapshotV1
        _f14_ingress_require_v1(type(snapshot) is PrivateEvidenceReadSnapshotV1,
            'F14_INGRESS_COMMITTED_SNAPSHOT')
        with self.source_registry._lock:
            with self._lock:
                matches = [slot for slot in self._slots.values() if slot['resolution'] is not None
                    and slot['resolution'][0] is snapshot and slot['resolution'][1] is observation
                    and slot['resolution'][2] is source_binding
                    and slot['resolution'][3:] == (decision_time, recorded_cutoff)]
                _f14_ingress_require_v1(len(matches) == 1, 'F14_INGRESS_COMMITTED_SNAPSHOT')
                slot = matches[0]
                entry = self._capture_v1(slot['observed'])
                self.source_registry._validate_grant_v1(entry[2].grant, entry[2].operation)
                _f14_ingress_require_v1(slot['state'] in ('PENDING', 'RESOLVED')
                    and observation.get('state') == 'PRIVATE_EVIDENCE_CHAIN_CONFORMANCE_ONLY'
                    and all(value is False for value in observation.values() if type(value) is bool),
                    'F14_INGRESS_PUBLICATION_OUTCOME_UNKNOWN')
                if slot['state'] == 'PENDING':
                    slot['result'] = _f14_freeze_v1(_f14_plain_v1(observation))
                    slot['state'] = 'RESOLVED'
                return _f14_freeze_v1(_f14_plain_v1(slot['result']))
