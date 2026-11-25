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
    FORMULA_INPUT_AUTHORITY_BINDINGS,
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
    ContractValidationError,
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


def _freeze(value: object, *, _packet_facts=None) -> object:
    if isinstance(value, dict):
        native = _packet_facts is not None and type(value) is dict and all(type(key) is str for key in value)
        result = MappingProxyType(
            {str(key): _freeze(item, _packet_facts=_packet_facts) for key, item in value.items()}
        )
    elif isinstance(value, list | tuple):
        native = type(value) in (list, tuple)
        result = tuple(_freeze(item, _packet_facts=_packet_facts) for item in value)
    else:
        return value
    if _packet_facts is not None:
        # Passive construction facts only. A large legacy packet retains its
        # legacy value but is unavailable to this bounded LP03 source profile.
        if len(_packet_facts) < 4097:
            _packet_facts.append((result, native))
    return result


def thaw_input(value: object) -> object:
    """Return a private mutable call value without changing authoritative state."""

    if isinstance(value, Mapping):
        return {str(key): thaw_input(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_input(item) for item in value]
    return value


class _OwnerPacketNativeFreezeV1:
    # An inherited runtime slot leaves the public dataclass field/signature and
    # canonical serialization rosters unchanged. There is no global registry.
    __slots__ = ("_evidence_native_freeze_v1",)


@dataclass(frozen=True, slots=True)
class OwnerValuePacketV1(_OwnerPacketNativeFreezeV1):
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
        native_root = type(self.values) is dict
        packet_facts = []
        original_values = _freeze(dict(self.values), _packet_facts=packet_facts)
        object.__setattr__(self, "values", original_values)
        object.__setattr__(self, "_evidence_native_freeze_v1",
                           (self, original_values, tuple(packet_facts), native_root))


@dataclass(frozen=True, slots=True)
class _EvidenceHistoricalInputReceiptV1:
    """M28 historical-input proof, distinct from unchanged V1 PIT semantics."""
    receipt_id: str
    context_id: str
    binding_id: str
    source_record_ref: tuple[str, str]
    source_context: ComputationExecutionContextV1
    source_native_clocks: tuple[tuple[str, int], ...]
    source_rights_refs: tuple[str, ...]
    consumer_decision_wall_ns: int
    consumer_cutoff_wall_ns: int
    published_producer_observations: tuple[tuple[str, tuple[object, ...]], ...]
    original_upstream_contexts: tuple[Mapping[str, object], ...]
    admitted: bool = True



@dataclass(frozen=True, slots=True)
class ResolvedFormulaInputV1:
    binding_id: str
    math_spec_id: str
    input_name: str
    value: object
    owner_id: str
    packet_id: str
    field_path: str
    point_in_time_receipt: PointInTimeReceiptV1 | _EvidenceHistoricalInputReceiptV1
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
        _deny_legacy_evidence_packet_access_v1(self)
        return self._packets

    def bind_evidence_conformance_source_v1(self, *, host_binding, original_rights):
        """Explicit synthetic-owner setup; no values enter through read requests."""
        _native_require(type(self) is CanonicalOwnerPacketRegistryV1
                        and getattr(self, "_evidence_source_custody_v1", None) is None,
                        "LP03_ORIGINAL_SOURCE_ALREADY_BOUND")
        custody = _EvidenceOwnerPacketCustodyV1(self, host_binding, original_rights)
        self._evidence_source_custody_v1 = custody
        return custody.owner_context

    def withdraw_evidence_source_rights_v1(self, rights_ref, *, owner_context) -> None:
        """The original owner's withdrawal cannot be undone by a read request."""
        custody = _require_evidence_packet_custody_v1(self)
        with custody.lock:
            _native_require(type(owner_context) is EvidenceSourceOwnerContextV1
                            and owner_context is custody.owner_context,
                            "LP03_ORIGINAL_SOURCE_OWNER_CONTEXT_REQUIRED")
            _EvidenceOwnerPacketCustodyV1._assert_original_v1(custody)
            _native_require(type(rights_ref) is str and rights_ref in custody.rights_by_id,
                            "LP03_ORIGINAL_RIGHTS_REFERENCE")
            custody.withdrawn.add(rights_ref)
            custody.generation += 1

    def read_evidence_source_slice_v1(self, read_grant):
        from ...agents.pr169_agent_orch1_resolvers import _EvidenceIssuerStateV1
        from .source_policy import _EvidenceHistoricalReadV1
        _native_require(type(read_grant) is _EvidenceHistoricalReadV1 and read_grant.registry is self,
                        "LP03_ORIGINAL_SOURCE_READ_CAPABILITY_REQUIRED")
        return _EvidenceIssuerStateV1._read_source_slice_v1(read_grant.issuer, read_grant)

    def packet_for(
        self,
        *,
        context: ComputationExecutionContextV1,
        binding_id: str,
    ) -> OwnerValuePacketV1:
        _deny_legacy_evidence_packet_access_v1(self)
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
        _deny_legacy_evidence_packet_access_v1(self)
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
        _deny_legacy_evidence_packet_access_v1(self)
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

    def __copy__(self):
        _deny_legacy_evidence_packet_access_v1(self)
        result = object.__new__(type(self))
        result.__dict__.update(self.__dict__)
        return result

    def __deepcopy__(self, memo):
        _deny_legacy_evidence_packet_access_v1(self)
        from copy import deepcopy
        result = object.__new__(type(self))
        result.__dict__.update(deepcopy(self.__dict__, memo))
        return result


def _deny_legacy_evidence_packet_access_v1(registry) -> None:
    if getattr(registry, "_evidence_source_custody_v1", None) is not None:
        raise InputAuthorityError(ReasonCode.CAPABILITY_DENIED,
                                  "LP03_CURRENT_ASSEMBLY_GRANT_REQUIRED")


def _require_evidence_packet_custody_v1(registry):
    custody = getattr(registry, "_evidence_source_custody_v1", None)
    if type(registry) is CanonicalOwnerPacketRegistryV1 and custody is None:
        raise ContractValidationError(ReasonCode.EVIDENCE_INPUT_UNAVAILABLE, "LP03_ORIGINAL_SOURCE_UNAVAILABLE")
    _native_require(type(registry) is CanonicalOwnerPacketRegistryV1
                    and type(custody) is _EvidenceOwnerPacketCustodyV1
                    and custody.registry is registry, "LP03_ORIGINAL_SOURCE_UNAVAILABLE")
    return custody


class EvidenceSourceOwnerContextV1:
    """Local original-owner setup context; never an assembly/read capability."""

    __slots__ = ("__owner",)

    def __init__(self, owner):
        _native_require(type(owner) is _EvidenceOwnerPacketCustodyV1, "LP03_ORIGINAL_SOURCE_CONTEXT_TYPE")
        self.__owner = owner

    def __copy__(self):
        raise TypeError("LP03 source owner context cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 source owner context cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 source owner context cannot be serialized")


from weakref import WeakKeyDictionary as _TrialLedgerWeakKeysV1, ref as _trial_ledger_weakref_v1

# Original constructor issuance only. Weak values cannot retain a registry
# through its guard closure; this catalog contains no source/read/rights cache.
_EVIDENCE_TRIAL_LEDGER_CONSTRUCTIONS_V1 = _TrialLedgerWeakKeysV1()


class _EvidenceCompleteMaterialTrialLedgerV1:
    """Original finite SOFTWARE roster; no empirical universe or p-value authority.

    The original empty packet pins context before any synthetic p input. Native
    completion visibility is separate from its six historical data clocks.
    Receipt names here identify owner-recorded synthetic inputs only.
    """

    __slots__ = ("original", "rows", "phase", "sealed", "guard", "_append", "_seal", "__weakref__")

    def __init__(self, *, packet_template, math_id, candidate_universe_id, evidence_window_id,
                 ordered_trial_ids, maximum_trials, maximum_ledger_bytes, benchmark_id=None,
                 ordered_time_ids=(), maximum_observations=0, sign_convention=None, sharpe_context=None,
                 cscv_context=None):
        if type(math_id) is str and math_id == "MATH-19":
            _native_require(benchmark_id is None and sign_convention is None and sharpe_context is None,
                "LP03_CSCV_LEDGER_PROFILE_ARGUMENTS")
            self._initialize_cscv_family_v1(packet_templates=packet_template, candidate_universe_id=candidate_universe_id,
                evidence_window_id=evidence_window_id, ordered_trial_ids=ordered_trial_ids, ordered_time_ids=ordered_time_ids,
                maximum_trials=maximum_trials, maximum_observations=maximum_observations,
                maximum_ledger_bytes=maximum_ledger_bytes, cscv_context=cscv_context)
            return
        _native_require(cscv_context is None, "LP03_TRIAL_LEDGER_LEGACY_PROFILE_ARGUMENTS")
        if type(math_id) is str and math_id in ("MATH-17", "MATH-18"):
            _native_require(benchmark_id is None and type(ordered_time_ids) is tuple and not ordered_time_ids
                and type(maximum_observations) is int and maximum_observations == 0 and sign_convention is None,
                "LP03_SHARPE_LEDGER_PROFILE_ARGUMENTS")
            self._initialize_sharpe_family_v1(packet_templates=packet_template, math_id=math_id,
                candidate_universe_id=candidate_universe_id, evidence_window_id=evidence_window_id,
                ordered_trial_ids=ordered_trial_ids, maximum_trials=maximum_trials,
                maximum_ledger_bytes=maximum_ledger_bytes, sharpe_context=sharpe_context)
            return
        _native_require(sharpe_context is None, "LP03_TRIAL_LEDGER_LEGACY_PROFILE_ARGUMENTS")
        if type(math_id) is str and math_id in ("MATH-15", "MATH-16"):
            self._initialize_reality_family_v1(packet_template=packet_template, math_id=math_id,
                candidate_universe_id=candidate_universe_id, evidence_window_id=evidence_window_id,
                ordered_trial_ids=ordered_trial_ids, maximum_trials=maximum_trials,
                maximum_ledger_bytes=maximum_ledger_bytes, benchmark_id=benchmark_id,
                ordered_time_ids=ordered_time_ids, maximum_observations=maximum_observations,
                sign_convention=sign_convention)
            return
        _native_require(benchmark_id is None and type(ordered_time_ids) is tuple and not ordered_time_ids
            and type(maximum_observations) is int and maximum_observations == 0 and sign_convention is None,
            "LP03_TRIAL_LEDGER_LEGACY_PROFILE_ARGUMENTS")
        from .context import _native_ident
        from time import time_ns
        from types import BuiltinFunctionType
        _native_require(type(time_ns) is BuiltinFunctionType, "LP03_TRIAL_LEDGER_NATIVE_VISIBILITY_CLOCK")
        _native_require(type(math_id) is str and math_id in ("MATH-12", "MATH-13")
                        and type(maximum_trials) is int and 0 < maximum_trials <= 32
                        and type(maximum_ledger_bytes) is int and 0 < maximum_ledger_bytes <= 32768,
                        "LP03_TRIAL_LEDGER_ORIGINAL_LIMITS")
        _native_require(type(ordered_trial_ids) is tuple and 0 < len(ordered_trial_ids) <= maximum_trials,
                        "LP03_TRIAL_LEDGER_ORIGINAL_ROSTER")
        for value in (candidate_universe_id, evidence_window_id, *ordered_trial_ids):
            _native_require(type(value) is str and 0 < len(value) <= 128, "LP03_TRIAL_LEDGER_ID_BOUND")
            _native_ident(value)
        _native_require(len(set(ordered_trial_ids)) == len(ordered_trial_ids), "LP03_TRIAL_LEDGER_DUPLICATE_TRIAL")
        _validate_evidence_packet_original_v1(packet_template, ("trial_p_values",))
        binding = FORMULA_INPUT_AUTHORITY_BINDINGS["FIVAB::" + math_id + "::p_values"]
        _native_require((packet_template.owner_id, packet_template.packet_type, packet_template.schema_id,
                         packet_template.schema_version, packet_template.producer_receipt_type,
                         packet_template.authorized_binding_ids)
                        == (binding.accepted_upstream_owner_id, binding.accepted_packet_or_snapshot_type,
                            binding.schema_id, binding.schema_version, binding.producer_receipt_type, (binding.binding_id,))
                        and set(packet_template.values) == {"trial_p_values"}
                        and packet_template.values["trial_p_values"] == () and not packet_template.source_conflict
                        and packet_template.source_state_and_claim_lineage == binding.source_state_and_claim_lineage,
                        "LP03_TRIAL_LEDGER_EMPTY_ORIGINAL_TEMPLATE")
        # Reserve the entire eventual roster, rows, end record and visibility
        # before any value is accepted. Identifiers are bounded native strings;
        # six escaped bytes per character safely bounds their future JSON.
        reserved = (2048 + 6 * (len(candidate_universe_id) + len(evidence_window_id)
                    + 3 * sum(map(len, ordered_trial_ids))) + 1152 * len(ordered_trial_ids))
        _native_require(reserved <= maximum_ledger_bytes, "LP03_TRIAL_LEDGER_COMPLETE_BYTE_CAPACITY")
        template_witness = _evidence_native_graph_witness_v1(packet_template,
            (OwnerValuePacketV1, ComputationScopeV1, PointInTimeClocksV1))
        self.original = (packet_template, template_witness, math_id, candidate_universe_id, evidence_window_id,
                         ordered_trial_ids, maximum_trials, maximum_ledger_bytes, reserved, time_ns)
        self.rows, self.phase, self.sealed = (), "OPEN", None
        original, rows, phase, sealed = self.original, self.rows, self.phase, self.sealed
        registry_members = None
        def retain(action, value=None):
            nonlocal rows, phase, sealed
            _native_require(self.guard is retain and self._append is append and self._seal is seal and self.original is original and self.rows is rows
                            and self.phase == phase and self.sealed is sealed, "LP03_TRIAL_LEDGER_ORIGINAL_CHANGED")
            _require_evidence_resolution_witness_v1(original[0], original[1], canonical=False)
            if sealed is not None:
                registry, packet, witness, visibility, canonical = sealed
                _native_require(getattr(registry, "_evidence_multiple_testing_ledger_v1", None) is self
                                and registry._packets is registry_members[0] and registry._by_id is registry_members[1]
                                and registry._by_binding is registry_members[2]
                                and registry._by_context_binding is registry_members[3]
                                and len(registry._packets) == 1 and registry._packets[0] is packet
                                and registry._by_id.get(packet.packet_id) is packet,
                                "LP03_TRIAL_LEDGER_SEALED_REGISTRY_CHANGED")
                _require_evidence_resolution_witness_v1(packet, witness, canonical=False)
            _native_require(action == "INSPECT" and value is None, "LP03_TRIAL_LEDGER_GUARD_OPERATION")
            return original, rows, phase, sealed
        def append(*, trial_id, synthetic_input_receipt_id, p_value):
            nonlocal rows
            from .context import _native_ident
            original, prefix, phase, sealed = retain("INSPECT")
            _native_require(phase == "OPEN" and len(prefix) < len(original[5]), "LP03_TRIAL_LEDGER_NOT_OPEN")
            _native_require(type(trial_id) is str and trial_id == original[5][len(prefix)], "LP03_TRIAL_LEDGER_APPEND_ORDER")
            _native_require(type(synthetic_input_receipt_id) is str and 0 < len(synthetic_input_receipt_id) <= 128,
                            "LP03_TRIAL_LEDGER_RECEIPT_BOUND")
            _native_ident(synthetic_input_receipt_id)
            _native_require(synthetic_input_receipt_id not in tuple(row[2] for row in prefix), "LP03_TRIAL_LEDGER_DUPLICATE_RECEIPT")
            _native_require(type(p_value) is float and math.isfinite(p_value) and 0.0 <= p_value <= 1.0,
                            "LP03_TRIAL_LEDGER_P_VALUE")
            rows = self.rows = (*prefix, (len(prefix), trial_id, synthetic_input_receipt_id, p_value))

        def seal():
            nonlocal phase, sealed, registry_members
            import struct
            from .serialization import deterministic_json
            original, prefix, current_phase, current_seal = retain("INSPECT")
            _native_require(current_phase == "OPEN" and len(prefix) == len(original[5]),
                            "LP03_TRIAL_LEDGER_INCOMPLETE_OR_NOT_OPEN")
            phase = self.phase = "SEALING"
            template, _, math_id, universe, window, roster, _, byte_limit, reserved, native_wall_ns = original
            body = dict(profile="DECLARED_FINITE_SOFTWARE_TRIAL_LEDGER_V1", math_id=math_id,
                implementation_id=math_id + "::1.1R1", candidate_universe_id=universe, evidence_window_id=window,
                origin="SOFTWARE_CONFORMANCE", p_value_provenance="SYNTHETIC_OWNER_RECORDED_INPUTS_ONLY",
                completeness_scope="EXACT_PROSPECTIVELY_DECLARED_SOFTWARE_ROSTER_ONLY", ordered_trial_ids=roster,
                rows=tuple(dict(original_index=index, trial_id=trial, synthetic_input_receipt_id=receipt,
                                p_value_binary64_bits=struct.pack(">d", value).hex()) for index, trial, receipt, value in prefix),
                end_record=dict(candidate_universe_id=universe, evidence_window_id=window, trial_count=len(roster),
                    last_trial_id=roster[-1], final_original_index=len(roster)-1, producer_receipt_id=template.producer_receipt_id))
            canonical = deterministic_json(body)
            _native_require(len(canonical.encode("utf-8")) + 128 <= reserved <= byte_limit,
                            "LP03_TRIAL_LEDGER_COMPLETE_BYTE_CAPACITY")
            packet = replace(template, values=dict(trial_p_values=tuple(row[3] for row in prefix), material_trial_ledger=body))
            _validate_evidence_packet_original_v1(packet, ("trial_p_values", "material_trial_ledger"))
            witness = _evidence_native_graph_witness_v1(packet,
                (OwnerValuePacketV1, ComputationScopeV1, PointInTimeClocksV1))
            registry = CanonicalOwnerPacketRegistryV1((packet,))
            registry._evidence_multiple_testing_ledger_v1 = self
            construction = (_trial_ledger_weakref_v1(self), _trial_ledger_weakref_v1(retain))
            _EVIDENCE_TRIAL_LEDGER_CONSTRUCTIONS_V1[registry] = construction
            registry_members = (registry._packets, registry._by_id, registry._by_binding, registry._by_context_binding)
            decision_ns = _native_utc_nanoseconds(template.clocks.as_of_time.isoformat())
            # Actual visibility follows construction of all packet/registry facts.
            # Historical source clocks are preserved without an invented seal time.
            visibility = native_wall_ns()
            _native_require(visibility <= decision_ns,
                            "LP03_TRIAL_LEDGER_MISSED_DECLARED_DECISION")
            retain("INSPECT")
            _native_require(_EVIDENCE_TRIAL_LEDGER_CONSTRUCTIONS_V1.get(registry) is construction
                            and construction[0]() is self and construction[1]() is retain
                            and registry._evidence_multiple_testing_ledger_v1 is self
                            and registry._packets is registry_members[0] and registry._by_id is registry_members[1]
                            and registry._by_binding is registry_members[2]
                            and registry._by_context_binding is registry_members[3]
                            and len(registry_members[0]) == 1 and registry_members[0][0] is packet
                            and registry._by_id.get(packet.packet_id) is packet,
                            "LP03_TRIAL_LEDGER_ORIGINAL_CONSTRUCTOR_REQUIRED")
            _require_evidence_resolution_witness_v1(packet, witness, canonical=False)
            sealed = self.sealed = (registry, packet, witness, visibility, canonical)
            phase = self.phase = "SEALED"
            return registry

        self._append, self._seal, self.guard = append, seal, retain

    def _initialize_cscv_family_v1(self, *, packet_templates, candidate_universe_id, evidence_window_id,
            ordered_trial_ids, ordered_time_ids, maximum_trials, maximum_observations, maximum_ledger_bytes, cscv_context):
        """Own a complete original synthetic strategy and chronological row roster."""
        import struct
        from time import time_ns
        from types import BuiltinFunctionType
        from .context import _native_ident
        from .serialization import deterministic_json

        _native_require(type(time_ns) is BuiltinFunctionType, "LP03_TRIAL_LEDGER_NATIVE_VISIBILITY_CLOCK")
        _native_require(type(maximum_trials) is int and 1 <= maximum_trials <= 4
            and type(maximum_observations) is int and 2 <= maximum_observations <= 8
            and type(maximum_ledger_bytes) is int and 0 < maximum_ledger_bytes <= 32768
            and type(ordered_trial_ids) is tuple and 1 <= len(ordered_trial_ids) <= maximum_trials
            and type(ordered_time_ids) is tuple and 2 <= len(ordered_time_ids) <= maximum_observations,
            "LP03_CSCV_LEDGER_ORIGINAL_LIMITS")
        _native_require(type(cscv_context) is dict and len(cscv_context) == 2 and all(type(key) is str for key in cscv_context)
            and set(cscv_context) == {"return_basis_id", "ordered_strategy_dispositions"}
            and type(cscv_context["ordered_strategy_dispositions"]) is tuple
            and len(cscv_context["ordered_strategy_dispositions"]) == len(ordered_trial_ids)
            and all(type(value) is str and value in ("ATTEMPTED", "PRUNED")
                for value in cscv_context["ordered_strategy_dispositions"]),
            "LP03_CSCV_LEDGER_STRATEGY_STATUS")
        for value in (candidate_universe_id, evidence_window_id,
                cscv_context["return_basis_id"], *ordered_trial_ids, *ordered_time_ids):
            _native_require(type(value) is str and 0 < len(value) <= 128, "LP03_CSCV_LEDGER_ID_DOMAIN")
            _native_ident(value)
        _native_require(len(set(ordered_trial_ids)) == len(ordered_trial_ids)
            and len(set(ordered_time_ids)) == len(ordered_time_ids), "LP03_CSCV_LEDGER_DUPLICATE_ORIGINAL_ID")
        bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-19"][:2]
        _native_require(tuple(row.input_name for row in bindings) == ("performance_matrix", "strategy_ids")
            and type(packet_templates) is tuple and len(packet_templates) == len(bindings),
            "LP03_CSCV_LEDGER_ORIGINAL_BINDINGS")
        witnesses = []
        for packet, binding in zip(packet_templates, bindings, strict=True):
            _validate_evidence_packet_original_v1(packet, ("cscv_ledger_pending",))
            _native_require((packet.owner_id, packet.packet_type, packet.schema_id, packet.schema_version,
                    packet.producer_receipt_type, packet.authorized_binding_ids, packet.source_state_and_claim_lineage)
                == (binding.accepted_upstream_owner_id, binding.accepted_packet_or_snapshot_type, binding.schema_id,
                    binding.schema_version, binding.producer_receipt_type, (binding.binding_id,), binding.source_state_and_claim_lineage)
                and tuple(packet.values) == ("cscv_ledger_pending",) and packet.values["cscv_ledger_pending"] == ()
                and packet.revision == evidence_window_id and not packet.source_conflict, "LP03_CSCV_LEDGER_OPEN_TEMPLATE")
            witnesses.append(_evidence_native_graph_witness_v1(packet, (OwnerValuePacketV1, ComputationScopeV1, PointInTimeClocksV1)))
        first, second = packet_templates
        _native_require(first.packet_id != second.packet_id and first.producer_receipt_id != second.producer_receipt_id
            and all(deterministic_json(getattr(first, name)) == deterministic_json(getattr(second, name))
                for name in ("context_id", "scope", "source_epoch_id", "input_version", "revision", "clocks", "ttl")),
            "LP03_CSCV_LEDGER_TEMPLATE_ASSOCIATION")
        return_basis = cscv_context["return_basis_id"]
        dispositions = cscv_context["ordered_strategy_dispositions"]
        def complete_body(matrix_rows):
            return dict(profile="DECLARED_CONTIGUOUS_SYNTHETIC_STRATEGY_PERFORMANCE_MATRIX_V1", math_id="MATH-19",
                implementation_id="MATH-19::2.0.0", origin="SOFTWARE_CONFORMANCE", candidate_universe_id=candidate_universe_id,
                evidence_window_id=evidence_window_id, return_basis_id=return_basis,
                ordered_strategy_ids=ordered_trial_ids, ordered_strategy_dispositions=dispositions,
                ordered_time_ids=ordered_time_ids, rows=matrix_rows,
                source_associations=tuple(dict(binding_id=binding.binding_id, packet_id=packet.packet_id,
                    producer_receipt_id=packet.producer_receipt_id) for packet, binding in zip(packet_templates, bindings, strict=True)),
                end_record=dict(candidate_universe_id=candidate_universe_id, evidence_window_id=evidence_window_id,
                    observation_count=len(ordered_time_ids), strategy_count=len(ordered_trial_ids),
                    cell_count=len(ordered_time_ids)*len(ordered_trial_ids), final_time_id=ordered_time_ids[-1]))

        # Compute the final UTF-8 envelope from the bounded declared graph.
        # Native identifiers exclude controls; each receipt scalar occupies
        # at most four UTF-8 bytes (or two bytes when escaped as JSON).
        cells = tuple(dict(strategy_id=trial, synthetic_input_receipt_id="", value_binary64_bits="0"*16)
            for trial in ordered_trial_ids)
        row_layout = tuple(dict(original_index=index, time_id=time_id, cells=cells)
            for index,time_id in enumerate(ordered_time_ids))
        cell_count = len(ordered_time_ids) * len(ordered_trial_ids)
        # JSON binary64 values in [-1,1] occupy at most 25 bytes plus a
        # delimiter. Account for both array layers and the repeated IDs.
        data_overhead = 128 + 26 * cell_count + 3 * len(ordered_time_ids) + 8
        repeated_ids = len(deterministic_json(ordered_trial_ids).encode("utf-8"))
        reserved = (len(deterministic_json(complete_body(row_layout)).encode("utf-8"))
            + 256 * cell_count + data_overhead + repeated_ids)
        _native_require(reserved <= maximum_ledger_bytes, "LP03_CSCV_LEDGER_COMPLETE_BYTE_CAPACITY")
        self.original = (packet_templates, tuple(witnesses), "MATH-19", candidate_universe_id, evidence_window_id,
            ordered_trial_ids, ordered_time_ids, return_basis, dispositions,
            maximum_ledger_bytes, reserved, time_ns)
        self.rows, self.phase, self.sealed = (), "OPEN", None
        original, rows, phase, sealed = self.original, self.rows, self.phase, self.sealed
        registry_members = None

        def retain(action, value=None):
            _native_require(self.guard is retain and self._append is append and self._seal is seal
                and self.original is original and self.rows is rows and type(self.phase) is str
                and self.phase == phase and self.sealed is sealed,
                "LP03_TRIAL_LEDGER_ORIGINAL_CHANGED")
            _native_require(type(action) is str and action == "INSPECT" and value is None, "LP03_TRIAL_LEDGER_GUARD_OPERATION")
            for packet, witness in zip(original[0], original[1], strict=True):
                _require_evidence_resolution_witness_v1(packet, witness, canonical=False)
            if sealed is not None:
                registry, packets, packet_witnesses, _, _ = sealed
                _native_require(getattr(registry, "_evidence_multiple_testing_ledger_v1", None) is self
                    and registry._packets is packets is registry_members[0] and registry._by_id is registry_members[1]
                    and registry._by_binding is registry_members[2] and registry._by_context_binding is registry_members[3]
                    and all(registry._by_id.get(packet.packet_id) is packet for packet in packets),
                    "LP03_CSCV_LEDGER_SEALED_REGISTRY_CHANGED")
                for packet, witness in zip(packets, packet_witnesses, strict=True):
                    _require_evidence_resolution_witness_v1(packet, witness, canonical=False)
            return original, rows, phase, sealed

        def append(*, time_id, synthetic_input_receipt_ids, performance_row):
            nonlocal rows
            _, prefix, current, _ = retain("INSPECT")
            _native_require(current == "OPEN" and len(prefix) < len(original[6]), "LP03_TRIAL_LEDGER_NOT_OPEN")
            _native_require(type(time_id) is str and time_id == original[6][len(prefix)], "LP03_CSCV_LEDGER_ROW_ORDER")
            count = len(original[5])
            _native_require(type(synthetic_input_receipt_ids) is tuple and len(synthetic_input_receipt_ids) == count
                and type(performance_row) is tuple and len(performance_row) == count,
                "LP03_CSCV_LEDGER_COMPLETE_ROW")
            for ref in synthetic_input_receipt_ids:
                _native_require(type(ref) is str and 0 < len(ref) <= 64, "LP03_CSCV_LEDGER_RECEIPT_BOUND")
                _native_ident(ref)
            _native_require(len(set(synthetic_input_receipt_ids)) == count
                and set(synthetic_input_receipt_ids).isdisjoint(ref for row in prefix for ref in row[2])
                and set(synthetic_input_receipt_ids).isdisjoint(packet.producer_receipt_id for packet in original[0]),
                "LP03_CSCV_LEDGER_DUPLICATE_RECEIPT")
            _native_require(all(type(value) is float and math.isfinite(value) and -1.0 <= value <= 1.0
                for value in performance_row), "LP03_CSCV_LEDGER_PERFORMANCE_DOMAIN")
            rows = self.rows = (*prefix, (len(prefix), time_id, synthetic_input_receipt_ids, performance_row))

        def seal():
            nonlocal phase, sealed, registry_members
            _, prefix, current, _ = retain("INSPECT")
            templates, _, _, universe, window, trials, times, basis, statuses, limit, reserved, native_clock = original
            _native_require(current == "OPEN" and len(prefix) == len(times), "LP03_TRIAL_LEDGER_INCOMPLETE_OR_NOT_OPEN")
            phase = self.phase = "SEALING"
            body = complete_body(tuple(dict(original_index=index, time_id=time_id, cells=tuple(
                dict(strategy_id=trial, synthetic_input_receipt_id=ref, value_binary64_bits=struct.pack(">d", value).hex())
                for trial, ref, value in zip(trials, refs, values, strict=True))) for index, time_id, refs, values in prefix))
            matrix = tuple(row[3] for row in prefix)
            canonical = deterministic_json(body)
            _native_require(len(canonical.encode("utf-8")) + len(deterministic_json((matrix,trials)).encode("utf-8")) + 128
                <= reserved <= limit, "LP03_CSCV_LEDGER_COMPLETE_BYTE_CAPACITY")
            packets = (replace(templates[0], values={bindings[0].exact_field_path: matrix, "material_trial_ledger": body}),
                replace(templates[1], values={bindings[1].exact_field_path: trials}))
            packet_witnesses = []
            for index, (packet, binding) in enumerate(zip(packets, bindings, strict=True)):
                _validate_evidence_packet_original_v1(packet, (binding.exact_field_path, "material_trial_ledger")
                    if index == 0 else (binding.exact_field_path,))
                packet_witnesses.append(_evidence_native_graph_witness_v1(packet, (OwnerValuePacketV1, ComputationScopeV1, PointInTimeClocksV1)))
            registry = CanonicalOwnerPacketRegistryV1(packets)
            registry._evidence_multiple_testing_ledger_v1 = self
            construction = (_trial_ledger_weakref_v1(self), _trial_ledger_weakref_v1(retain))
            _EVIDENCE_TRIAL_LEDGER_CONSTRUCTIONS_V1[registry] = construction
            registry_members = (registry._packets, registry._by_id, registry._by_binding, registry._by_context_binding)
            decision = _native_utc_nanoseconds(templates[0].clocks.as_of_time.isoformat())
            visibility = native_clock()
            _native_require(visibility <= decision, "LP03_TRIAL_LEDGER_MISSED_DECLARED_DECISION")
            retain("INSPECT")
            _native_require(_EVIDENCE_TRIAL_LEDGER_CONSTRUCTIONS_V1.get(registry) is construction
                and construction[0]() is self and construction[1]() is retain
                and registry._evidence_multiple_testing_ledger_v1 is self and registry._packets is packets
                and all(registry._by_id.get(packet.packet_id) is packet for packet in packets),
                "LP03_TRIAL_LEDGER_ORIGINAL_CONSTRUCTOR_REQUIRED")
            for packet, witness in zip(packets, packet_witnesses, strict=True):
                _require_evidence_resolution_witness_v1(packet, witness, canonical=False)
            sealed = self.sealed = (registry, packets, tuple(packet_witnesses), visibility, canonical)
            phase = self.phase = "SEALED"
            return registry

        self._append, self._seal, self.guard = append, seal, retain

    def append_synthetic_cscv_row_v1(self, *, time_id, synthetic_input_receipt_ids, performance_row):
        original, _, _, _ = self.guard("INSPECT")
        _native_require(original[2] == "MATH-19", "LP03_CSCV_LEDGER_METHOD_PROFILE")
        return self._append(time_id=time_id, synthetic_input_receipt_ids=synthetic_input_receipt_ids,
            performance_row=performance_row)

    def seal_synthetic_cscv_ledger_v1(self):
        original, _, _, _ = self.guard("INSPECT")
        _native_require(original[2] == "MATH-19", "LP03_CSCV_LEDGER_METHOD_PROFILE")
        return self._seal()


    def _initialize_sharpe_family_v1(self, *, packet_templates, math_id, candidate_universe_id,
            evidence_window_id, ordered_trial_ids, maximum_trials, maximum_ledger_bytes, sharpe_context):
        """Original SOFTWARE inputs only; never infer statistical support."""
        import struct
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .context import _native_ident
        from .serialization import deterministic_json
        from time import time_ns
        from types import BuiltinFunctionType
        _native_require(type(time_ns) is BuiltinFunctionType, "LP03_TRIAL_LEDGER_NATIVE_VISIBILITY_CLOCK")
        _native_require(type(math_id) is str and math_id in ("MATH-17", "MATH-18")
            and type(maximum_trials) is int and (1 if math_id == "MATH-17" else 2) <= maximum_trials <= 5
            and type(maximum_ledger_bytes) is int and 0 < maximum_ledger_bytes <= 32768,
            "LP03_SHARPE_LEDGER_ORIGINAL_LIMITS")
        _native_require(type(ordered_trial_ids) is tuple
            and (1 if math_id == "MATH-17" else 2) <= len(ordered_trial_ids) <= maximum_trials,
            "LP03_SHARPE_LEDGER_ORIGINAL_ROSTER")
        _native_require(type(sharpe_context) is dict and len(sharpe_context) == 5
            and all(type(key) is str for key in sharpe_context) and set(sharpe_context) == {
            "return_basis_id", "annualization_basis_id", "support_input_declaration_ref", "support_scope", "candidate_trial_id"}
            and type(sharpe_context["support_scope"]) is str
            and sharpe_context["support_scope"] == "SOFTWARE_INTEGER_INPUT_ONLY_NO_STATISTICAL_SUPPORT_CLAIM",
            "LP03_SHARPE_LEDGER_SUPPORT_SCOPE")
        for value in (candidate_universe_id, evidence_window_id, *ordered_trial_ids,
                *(sharpe_context[name] for name in ("return_basis_id", "annualization_basis_id",
                    "support_input_declaration_ref", "candidate_trial_id"))):
            _native_require(type(value) is str and 0 < len(value) <= 128, "LP03_SHARPE_LEDGER_ID_BOUND")
            _native_ident(value)
        _native_require(len(set(ordered_trial_ids)) == len(ordered_trial_ids)
            and sharpe_context["candidate_trial_id"] in ordered_trial_ids, "LP03_SHARPE_LEDGER_COMPLETE_CANDIDATE")
        bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
        _native_require(type(packet_templates) is tuple and len(packet_templates) == len(bindings)
            == (5 if math_id == "MATH-17" else 6), "LP03_SHARPE_LEDGER_TEMPLATE_ROSTER")
        witnesses = []
        for packet, binding in zip(packet_templates, bindings, strict=True):
            _validate_evidence_packet_original_v1(packet, ("sharpe_ledger_pending",))
            _native_require((packet.owner_id, packet.packet_type, packet.schema_id, packet.schema_version,
                    packet.producer_receipt_type, packet.authorized_binding_ids, packet.source_state_and_claim_lineage)
                == (binding.accepted_upstream_owner_id, binding.accepted_packet_or_snapshot_type,
                    binding.schema_id, binding.schema_version, binding.producer_receipt_type,
                    (binding.binding_id,), binding.source_state_and_claim_lineage)
                and tuple(packet.values) == ("sharpe_ledger_pending",) and packet.values["sharpe_ledger_pending"] == ()
                and not packet.source_conflict and type(packet.revision) is str and packet.revision == evidence_window_id,
                "LP03_SHARPE_LEDGER_EMPTY_ORIGINAL_TEMPLATE")
            witnesses.append(_evidence_native_graph_witness_v1(packet,
                (OwnerValuePacketV1, ComputationScopeV1, PointInTimeClocksV1)))
        _native_require(len({packet.packet_id for packet in packet_templates})
            == len({packet.producer_receipt_id for packet in packet_templates}) == len(bindings)
            and all(deterministic_json(getattr(packet, name)) == deterministic_json(getattr(packet_templates[0], name))
                for packet in packet_templates[1:] for name in
                ("context_id", "scope", "source_epoch_id", "input_version", "revision", "clocks", "ttl")),
            "LP03_SHARPE_LEDGER_TEMPLATE_ASSOCIATION")
        context = tuple((name, sharpe_context[name]) for name in sorted(sharpe_context))
        # Covers every escaped identifier, complete row/status roster, candidate
        # moment bits/integer, exact packet associations and duplicated values.
        reserved = (6144 + 6 * (3 * len(candidate_universe_id) + 3 * len(evidence_window_id)
            + 3 * sum(map(len, ordered_trial_ids)) + sum(len(name) + len(value) for name, value in context)
            + sum(len(packet.packet_id) + len(packet.producer_receipt_id) + len(binding.binding_id)
                for packet, binding in zip(packet_templates, bindings, strict=True))) + 1536 * len(ordered_trial_ids))
        _native_require(reserved <= maximum_ledger_bytes, "LP03_SHARPE_LEDGER_COMPLETE_BYTE_CAPACITY")
        self.original = (packet_templates, tuple(witnesses), math_id, candidate_universe_id, evidence_window_id,
            ordered_trial_ids, maximum_trials, maximum_ledger_bytes, reserved, time_ns, context)
        self.rows, self.phase, self.sealed = (), "OPEN", None
        original, rows, phase, sealed = self.original, self.rows, self.phase, self.sealed
        registry_members = None
        def retain(action, value=None):
            _native_require(self.guard is retain and self._append is append and self._seal is seal
                and self.original is original and self.rows is rows and type(self.phase) is str
                and self.phase == phase and self.sealed is sealed, "LP03_TRIAL_LEDGER_ORIGINAL_CHANGED")
            for packet, witness in zip(original[0], original[1], strict=True):
                _require_evidence_resolution_witness_v1(packet, witness, canonical=False)
            if sealed is not None:
                registry, packets, packet_witnesses, visibility, canonical = sealed
                _native_require(getattr(registry, "_evidence_multiple_testing_ledger_v1", None) is self
                    and registry._packets is packets is registry_members[0] and registry._by_id is registry_members[1]
                    and registry._by_binding is registry_members[2] and registry._by_context_binding is registry_members[3]
                    and len(packets) == len(original[0])
                    and all(registry._by_id.get(packet.packet_id) is packet for packet in packets),
                    "LP03_TRIAL_LEDGER_SEALED_REGISTRY_CHANGED")
                for packet, witness in zip(packets, packet_witnesses, strict=True):
                    _require_evidence_resolution_witness_v1(packet, witness, canonical=False)
            _native_require(type(action) is str and action == "INSPECT" and value is None,
                "LP03_TRIAL_LEDGER_GUARD_OPERATION")
            return original, rows, phase, sealed
        def append(*, trial_id, synthetic_input_receipt_id, disposition, sharpe):
            nonlocal rows
            original, prefix, current_phase, current_seal = retain("INSPECT")
            _native_require(current_phase == "OPEN" and len(prefix) < len(original[5]), "LP03_TRIAL_LEDGER_NOT_OPEN")
            _native_require(type(trial_id) is str and trial_id == original[5][len(prefix)], "LP03_TRIAL_LEDGER_APPEND_ORDER")
            _native_require(type(synthetic_input_receipt_id) is str and 0 < len(synthetic_input_receipt_id) <= 128,
                "LP03_SHARPE_LEDGER_RECEIPT_BOUND")
            _native_ident(synthetic_input_receipt_id)
            _native_require(synthetic_input_receipt_id not in tuple(row[2] for row in prefix)
                and synthetic_input_receipt_id not in tuple(packet.producer_receipt_id for packet in original[0]),
                "LP03_SHARPE_LEDGER_DUPLICATE_RECEIPT")
            _native_require(type(disposition) is str and disposition in ("ATTEMPTED", "PRUNED"),
                "LP03_SHARPE_LEDGER_TRIAL_DISPOSITION")
            _native_require(type(sharpe) is float and math.isfinite(sharpe) and -1.0 <= sharpe <= 1.0,
                "LP03_SHARPE_LEDGER_TRIAL_DOMAIN")
            rows = self.rows = (*prefix, (len(prefix), trial_id, synthetic_input_receipt_id, disposition, sharpe))
        def seal(*, candidate_values, synthetic_moment_receipt_id):
            nonlocal phase, sealed, registry_members
            original, prefix, current_phase, current_seal = retain("INSPECT")
            _native_require(current_phase == "OPEN" and len(prefix) == len(original[5]),
                "LP03_TRIAL_LEDGER_INCOMPLETE_OR_NOT_OPEN")
            templates, _, math_id, universe, window, roster, _, byte_limit, reserved, native_wall_ns, context = original
            context = dict(context)
            required = tuple(binding.input_name for binding in bindings if binding.input_name != "complete_material_trial_sharpes")
            _native_require(type(candidate_values) is dict and len(candidate_values) == len(required)
                and all(type(key) is str for key in candidate_values) and set(candidate_values) == set(required),
                "LP03_SHARPE_LEDGER_CANDIDATE_FIELDS")
            values = dict(candidate_values)
            count_name = "independent_equivalent_observations" if math_id == "MATH-17" else "candidate_independent_equivalent_observations"
            kurtosis_name = "sample_non_excess_kurtosis" if math_id == "MATH-17" else "candidate_sample_non_excess_kurtosis"
            estimate_name = "estimated_sharpe" if math_id == "MATH-17" else "candidate_estimated_sharpe"
            _native_require(type(values[count_name]) is int and 2 <= values[count_name] <= 2**53
                and all(type(value) is float and math.isfinite(value) for name, value in values.items() if name != count_name)
                and values[kurtosis_name] >= 1.0, "LP03_SHARPE_LEDGER_EXACT_SUPPORT_AND_MOMENTS")
            if math_id == "MATH-18":
                _native_require(1.0 < values["effective_independent_trial_count"] <= len(roster),
                    "LP03_SHARPE_LEDGER_EFFECTIVE_TRIALS")
                values["complete_material_trial_sharpes"] = tuple(row[4] for row in prefix)
            candidate_row = prefix[roster.index(context["candidate_trial_id"])]
            _native_require(candidate_row[3] == "ATTEMPTED"
                and struct.pack(">d", candidate_row[4]) == struct.pack(">d", values[estimate_name]),
                "LP03_SHARPE_LEDGER_CANDIDATE_VALUE_JOIN")
            _native_require(type(synthetic_moment_receipt_id) is str and 0 < len(synthetic_moment_receipt_id) <= 128,
                "LP03_SHARPE_LEDGER_RECEIPT_BOUND")
            _native_ident(synthetic_moment_receipt_id)
            _native_require(synthetic_moment_receipt_id not in tuple(row[2] for row in prefix)
                and synthetic_moment_receipt_id not in tuple(packet.producer_receipt_id for packet in templates),
                "LP03_SHARPE_LEDGER_DUPLICATE_RECEIPT")
            phase = self.phase = "SEALING"
            body = dict(profile="DECLARED_FINITE_SOFTWARE_SHARPE_LEDGER_V1", math_id=math_id,
                implementation_id=math_id + ("::1.1.0" if math_id == "MATH-17" else "::2.0.0"),
                origin="SOFTWARE_CONFORMANCE", candidate_universe_id=universe, evidence_window_id=window,
                completeness_scope="EXACT_PROSPECTIVELY_DECLARED_ATTEMPTED_AND_PRUNED_SOFTWARE_ROSTER_ONLY",
                value_provenance="SYNTHETIC_OWNER_RECORDED_SHARPES_AND_MOMENTS_ONLY", **context,
                ordered_trial_ids=roster,
                rows=tuple(dict(original_index=index, trial_id=trial, synthetic_input_receipt_id=receipt,
                    disposition=status, sharpe_binary64_bits=struct.pack(">d", value).hex())
                    for index, trial, receipt, status, value in prefix),
                candidate_moments=dict(synthetic_moment_receipt_id=synthetic_moment_receipt_id,
                    original_integer_support=values[count_name], integer_support_field=count_name,
                    binary64_fields={name: struct.pack(">d", value).hex()
                        for name, value in values.items() if name not in (count_name, "complete_material_trial_sharpes")}),
                source_associations=tuple(dict(binding_id=binding.binding_id, packet_id=packet.packet_id,
                    producer_receipt_id=packet.producer_receipt_id) for packet, binding in zip(templates, bindings, strict=True)),
                end_record=dict(candidate_universe_id=universe, evidence_window_id=window, trial_count=len(roster),
                    last_trial_id=roster[-1], final_original_index=len(roster)-1,
                    attempted_count=sum(row[3] == "ATTEMPTED" for row in prefix),
                    pruned_count=sum(row[3] == "PRUNED" for row in prefix)))
            canonical = deterministic_json(body)
            packets = tuple(replace(template, values={binding.exact_field_path: values[binding.input_name],
                **({"material_trial_ledger": body} if index == 0 else {})})
                for index, (template, binding) in enumerate(zip(templates, bindings, strict=True)))
            _native_require(len(canonical.encode("utf-8")) + len(deterministic_json(values).encode("utf-8")) + 128
                <= reserved <= byte_limit, "LP03_SHARPE_LEDGER_COMPLETE_BYTE_CAPACITY")
            packet_witnesses = []
            for index, (packet, binding) in enumerate(zip(packets, bindings, strict=True)):
                _validate_evidence_packet_original_v1(packet, (binding.exact_field_path, "material_trial_ledger")
                    if index == 0 else (binding.exact_field_path,))
                packet_witnesses.append(_evidence_native_graph_witness_v1(packet,
                    (OwnerValuePacketV1, ComputationScopeV1, PointInTimeClocksV1)))
            registry = CanonicalOwnerPacketRegistryV1(packets)
            registry._evidence_multiple_testing_ledger_v1 = self
            construction = (_trial_ledger_weakref_v1(self), _trial_ledger_weakref_v1(retain))
            _EVIDENCE_TRIAL_LEDGER_CONSTRUCTIONS_V1[registry] = construction
            registry_members = (registry._packets, registry._by_id, registry._by_binding, registry._by_context_binding)
            decision_ns = _native_utc_nanoseconds(templates[0].clocks.as_of_time.isoformat())
            visibility = native_wall_ns()
            _native_require(visibility <= decision_ns, "LP03_TRIAL_LEDGER_MISSED_DECLARED_DECISION")
            retain("INSPECT")
            _native_require(_EVIDENCE_TRIAL_LEDGER_CONSTRUCTIONS_V1.get(registry) is construction
                and construction[0]() is self and construction[1]() is retain
                and registry._evidence_multiple_testing_ledger_v1 is self
                and registry._packets is packets is registry_members[0] and registry._by_id is registry_members[1]
                and registry._by_binding is registry_members[2] and registry._by_context_binding is registry_members[3]
                and all(registry._by_id.get(packet.packet_id) is packet for packet in packets),
                "LP03_TRIAL_LEDGER_ORIGINAL_CONSTRUCTOR_REQUIRED")
            for packet, witness in zip(packets, packet_witnesses, strict=True):
                _require_evidence_resolution_witness_v1(packet, witness, canonical=False)
            sealed = self.sealed = (registry, packets, tuple(packet_witnesses), visibility, canonical)
            phase = self.phase = "SEALED"
            return registry
        self._append, self._seal, self.guard = append, seal, retain

    def append_synthetic_sharpe_trial_v1(self, *, trial_id, synthetic_input_receipt_id, disposition, sharpe):
        original, _, _, _ = self.guard("INSPECT")
        _native_require(original[2] in ("MATH-17", "MATH-18"), "LP03_SHARPE_LEDGER_METHOD_PROFILE")
        return self._append(trial_id=trial_id, synthetic_input_receipt_id=synthetic_input_receipt_id,
            disposition=disposition, sharpe=sharpe)

    def seal_synthetic_sharpe_ledger_v1(self, *, candidate_values, synthetic_moment_receipt_id):
        original, _, _, _ = self.guard("INSPECT")
        _native_require(original[2] in ("MATH-17", "MATH-18"), "LP03_SHARPE_LEDGER_METHOD_PROFILE")
        return self._seal(candidate_values=candidate_values, synthetic_moment_receipt_id=synthetic_moment_receipt_id)

    def _initialize_reality_family_v1(self, *, packet_template, math_id, candidate_universe_id, evidence_window_id,
            ordered_trial_ids, maximum_trials, maximum_ledger_bytes, benchmark_id, ordered_time_ids,
            maximum_observations, sign_convention):
        """Original finite synthetic candidate/time grid; no empirical claim."""
        from .context import _native_ident
        from time import time_ns
        from types import BuiltinFunctionType
        _native_require(type(time_ns) is BuiltinFunctionType, "LP03_TRIAL_LEDGER_NATIVE_VISIBILITY_CLOCK")
        _native_require(type(math_id) is str and math_id in ("MATH-15", "MATH-16")
            and type(maximum_trials) is int and 1 <= maximum_trials <= 2
            and type(maximum_observations) is int and (3 if math_id == "MATH-16" else 2) <= maximum_observations <= 4
            and type(maximum_ledger_bytes) is int and 0 < maximum_ledger_bytes <= 32768,
            "LP03_LOSS_FAMILY_ORIGINAL_LIMITS")
        _native_require(type(ordered_trial_ids) is tuple and 1 <= len(ordered_trial_ids) <= maximum_trials
            and type(ordered_time_ids) is tuple and (3 if math_id == "MATH-16" else 2) <= len(ordered_time_ids) <= maximum_observations
            and len(ordered_trial_ids) * len(ordered_time_ids) <= 8,
            "LP03_LOSS_FAMILY_ORIGINAL_GRID")
        _native_require(type(sign_convention) is str
            and sign_convention == "BENCHMARK_LOSS_MINUS_CANDIDATE_LOSS_POSITIVE_IS_BETTER",
            "LP03_LOSS_FAMILY_ORIGINAL_BINDING_ORIENTATION")
        for value in (candidate_universe_id, evidence_window_id, benchmark_id, *ordered_trial_ids, *ordered_time_ids):
            _native_require(type(value) is str and 0 < len(value) <= 128, "LP03_LOSS_FAMILY_ID_BOUND")
            _native_ident(value)
        _native_require(len(set(ordered_trial_ids)) == len(ordered_trial_ids)
            and len(set(ordered_time_ids)) == len(ordered_time_ids), "LP03_LOSS_FAMILY_DUPLICATE_ID")
        _validate_evidence_packet_original_v1(packet_template, ("candidate_loss_differentials",))
        binding = FORMULA_INPUT_AUTHORITY_BINDINGS["FIVAB::" + math_id + "::loss_differentials"]
        _native_require((packet_template.owner_id, packet_template.packet_type, packet_template.schema_id,
                packet_template.schema_version, packet_template.producer_receipt_type, packet_template.authorized_binding_ids)
            == (binding.accepted_upstream_owner_id, binding.accepted_packet_or_snapshot_type,
                binding.schema_id, binding.schema_version, binding.producer_receipt_type, (binding.binding_id,))
            and set(packet_template.values) == {"candidate_loss_differentials"}
            and packet_template.values["candidate_loss_differentials"] == () and not packet_template.source_conflict
            and packet_template.source_state_and_claim_lineage == binding.source_state_and_claim_lineage
            and type(packet_template.revision) is str and packet_template.revision == evidence_window_id,
            "LP03_LOSS_FAMILY_EMPTY_ORIGINAL_TEMPLATE")
        # Each cell reserves its bounded receipt/time identifiers, value bits,
        # ordinal fields and future matrix token. The additional header/end
        # reserve covers original rosters and their escaped repeated names.
        reserved = (2048 + 6 * (len(candidate_universe_id) + len(evidence_window_id) + len(benchmark_id)
            + len(sign_convention) + 3 * sum(map(len, ordered_trial_ids)) + 3 * sum(map(len, ordered_time_ids)))
            + 2048 * len(ordered_trial_ids) * len(ordered_time_ids))
        _native_require(reserved <= maximum_ledger_bytes, "LP03_LOSS_FAMILY_COMPLETE_BYTE_CAPACITY")
        witness = _evidence_native_graph_witness_v1(packet_template,
            (OwnerValuePacketV1, ComputationScopeV1, PointInTimeClocksV1))
        self.original = (packet_template, witness, math_id, candidate_universe_id, evidence_window_id,
            ordered_trial_ids, maximum_trials, maximum_ledger_bytes, reserved, time_ns,
            (benchmark_id, ordered_time_ids, maximum_observations, sign_convention))
        self.rows, self.phase, self.sealed = (), "OPEN", None
        original, rows, phase, sealed = self.original, self.rows, self.phase, self.sealed
        registry_members = None
        def retain(action, value=None):
            _native_require(self.guard is retain and self._append is append and self._seal is seal
                and self.original is original and self.rows is rows and type(self.phase) is str
                and self.phase == phase and self.sealed is sealed, "LP03_TRIAL_LEDGER_ORIGINAL_CHANGED")
            _require_evidence_resolution_witness_v1(original[0], original[1], canonical=False)
            if sealed is not None:
                registry, packet, packet_witness, visibility, canonical = sealed
                _native_require(getattr(registry, "_evidence_multiple_testing_ledger_v1", None) is self
                    and registry._packets is registry_members[0] and registry._by_id is registry_members[1]
                    and registry._by_binding is registry_members[2] and registry._by_context_binding is registry_members[3]
                    and len(registry._packets) == 1 and registry._packets[0] is packet
                    and registry._by_id.get(packet.packet_id) is packet, "LP03_TRIAL_LEDGER_SEALED_REGISTRY_CHANGED")
                _require_evidence_resolution_witness_v1(packet, packet_witness, canonical=False)
            _native_require(type(action) is str and action == "INSPECT" and value is None, "LP03_TRIAL_LEDGER_GUARD_OPERATION")
            return original, rows, phase, sealed
        def append(*, trial_id, time_ids, synthetic_input_receipt_ids, loss_differentials):
            nonlocal rows
            original, prefix, current_phase, current_seal = retain("INSPECT")
            _native_require(current_phase == "OPEN" and len(prefix) < len(original[5]), "LP03_TRIAL_LEDGER_NOT_OPEN")
            _native_require(type(trial_id) is str and trial_id == original[5][len(prefix)], "LP03_TRIAL_LEDGER_APPEND_ORDER")
            times = original[10][1]
            _native_require(type(time_ids) is tuple and len(time_ids) == len(times)
                and all(type(value) is str for value in time_ids)
                and time_ids == times and type(synthetic_input_receipt_ids) is tuple
                and type(loss_differentials) is tuple and len(synthetic_input_receipt_ids) == len(loss_differentials) == len(times),
                "LP03_LOSS_FAMILY_COMPLETE_COLUMN")
            prior = tuple(receipt for row in prefix for receipt in row[2])
            for receipt in synthetic_input_receipt_ids:
                _native_require(type(receipt) is str and 0 < len(receipt) <= 128, "LP03_LOSS_FAMILY_RECEIPT_BOUND")
                _native_ident(receipt)
                _native_require(receipt not in prior and receipt != original[0].producer_receipt_id,
                    "LP03_LOSS_FAMILY_DUPLICATE_RECEIPT")
            _native_require(len(set(synthetic_input_receipt_ids)) == len(synthetic_input_receipt_ids),
                "LP03_LOSS_FAMILY_DUPLICATE_RECEIPT")
            _native_require(all(type(value) is float and math.isfinite(value) and -1.0 <= value <= 1.0
                for value in loss_differentials), "LP03_LOSS_FAMILY_DIFFERENTIAL_DOMAIN")
            # Publish a complete immutable column only after every field passes.
            rows = self.rows = (*prefix, (len(prefix), trial_id, synthetic_input_receipt_ids, loss_differentials))
        def seal():
            nonlocal phase, sealed, registry_members
            import struct
            from .serialization import deterministic_json
            original, prefix, current_phase, current_seal = retain("INSPECT")
            _native_require(current_phase == "OPEN" and len(prefix) == len(original[5]),
                "LP03_TRIAL_LEDGER_INCOMPLETE_OR_NOT_OPEN")
            phase = self.phase = "SEALING"
            template, _, math_id, universe, window, roster, _, byte_limit, reserved, native_wall_ns, extra = original
            benchmark, times, _, orientation = extra
            body = dict(profile="DECLARED_FINITE_SOFTWARE_LOSS_FAMILY_LEDGER_V1", math_id=math_id,
                implementation_id=math_id + "::2.0.0", candidate_universe_id=universe, evidence_window_id=window,
                benchmark_id=benchmark, sign_convention=orientation, origin="SOFTWARE_CONFORMANCE",
                value_provenance="SYNTHETIC_OWNER_RECORDED_LOSS_DIFFERENTIALS_ONLY",
                completeness_scope="EXACT_PROSPECTIVELY_DECLARED_CANDIDATE_TIME_GRID_ONLY",
                ordered_trial_ids=roster, ordered_time_ids=times,
                rows=tuple(dict(original_candidate_index=index, trial_id=trial,
                    observations=tuple(dict(original_time_index=position, time_id=time_id,
                        synthetic_input_receipt_id=receipt, differential_binary64_bits=struct.pack(">d", value).hex())
                        for position, (time_id, receipt, value) in enumerate(zip(times, receipts, values, strict=True))))
                    for index, trial, receipts, values in prefix),
                end_record=dict(candidate_universe_id=universe, evidence_window_id=window, benchmark_id=benchmark,
                    trial_count=len(roster), observation_count=len(times), cell_count=len(roster)*len(times),
                    last_trial_id=roster[-1], final_original_candidate_index=len(roster)-1,
                    last_time_id=times[-1], final_original_time_index=len(times)-1, producer_receipt_id=template.producer_receipt_id))
            # Every original column contributes every declared time position.
            # This single transpose preserves the original float objects/bits.
            matrix = tuple(tuple(row[3][position] for row in prefix) for position in range(len(times)))
            canonical = deterministic_json(body)
            _native_require(len(canonical.encode("utf-8")) + len(deterministic_json(matrix).encode("utf-8")) + 128
                <= reserved <= byte_limit, "LP03_LOSS_FAMILY_COMPLETE_BYTE_CAPACITY")
            packet = replace(template, values=dict(candidate_loss_differentials=matrix, material_trial_ledger=body))
            _validate_evidence_packet_original_v1(packet, ("candidate_loss_differentials", "material_trial_ledger"))
            packet_witness = _evidence_native_graph_witness_v1(packet,
                (OwnerValuePacketV1, ComputationScopeV1, PointInTimeClocksV1))
            registry = CanonicalOwnerPacketRegistryV1((packet,))
            registry._evidence_multiple_testing_ledger_v1 = self
            construction = (_trial_ledger_weakref_v1(self), _trial_ledger_weakref_v1(retain))
            _EVIDENCE_TRIAL_LEDGER_CONSTRUCTIONS_V1[registry] = construction
            registry_members = (registry._packets, registry._by_id, registry._by_binding, registry._by_context_binding)
            decision_ns = _native_utc_nanoseconds(template.clocks.as_of_time.isoformat())
            visibility = native_wall_ns()
            _native_require(visibility <= decision_ns, "LP03_TRIAL_LEDGER_MISSED_DECLARED_DECISION")
            retain("INSPECT")
            _native_require(_EVIDENCE_TRIAL_LEDGER_CONSTRUCTIONS_V1.get(registry) is construction
                and construction[0]() is self and construction[1]() is retain
                and registry._evidence_multiple_testing_ledger_v1 is self
                and registry._packets is registry_members[0] and registry._by_id is registry_members[1]
                and registry._by_binding is registry_members[2] and registry._by_context_binding is registry_members[3]
                and len(registry_members[0]) == 1 and registry_members[0][0] is packet
                and registry._by_id.get(packet.packet_id) is packet, "LP03_TRIAL_LEDGER_ORIGINAL_CONSTRUCTOR_REQUIRED")
            _require_evidence_resolution_witness_v1(packet, packet_witness, canonical=False)
            sealed = self.sealed = (registry, packet, packet_witness, visibility, canonical)
            phase = self.phase = "SEALED"
            return registry
        self._append, self._seal, self.guard = append, seal, retain

    def append_synthetic_loss_candidate_v1(self, *, trial_id, time_ids, synthetic_input_receipt_ids, loss_differentials):
        original, _, _, _ = self.guard("INSPECT")
        _native_require(original[2] in ("MATH-15", "MATH-16"), "LP03_LOSS_FAMILY_METHOD_PROFILE")
        return self._append(trial_id=trial_id, time_ids=time_ids,
            synthetic_input_receipt_ids=synthetic_input_receipt_ids, loss_differentials=loss_differentials)

    def __copy__(self):
        raise TypeError("LP03 original trial ledger cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 original trial ledger cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 original trial ledger cannot be serialized")

    def append_synthetic_trial_v1(self, *, trial_id, synthetic_input_receipt_id, p_value):
        original, _, _, _ = self.guard("INSPECT")
        _native_require(original[2] in ("MATH-12", "MATH-13"), "LP03_TRIAL_LEDGER_METHOD_PROFILE")
        return self._append(trial_id=trial_id, synthetic_input_receipt_id=synthetic_input_receipt_id, p_value=p_value)

    def seal_synthetic_ledger_v1(self):
        original, _, _, _ = self.guard("INSPECT")
        _native_require(original[2] in ("MATH-12", "MATH-13", "MATH-15", "MATH-16"),
            "LP03_TRIAL_LEDGER_METHOD_PROFILE")
        return self._seal()



def _require_evidence_trial_ledger_registry_v1(registry, *, expected=None, scope=None):
    """Require this original owner construction, never a receipt-name alias."""
    _native_require(type(registry) is CanonicalOwnerPacketRegistryV1, "LP03_TRIAL_LEDGER_REGISTRY_TYPE")
    ledger = getattr(registry, "_evidence_multiple_testing_ledger_v1", None)
    packets = registry._packets
    _native_require(type(packets) is tuple and len(packets) <= 4096, "LP03_TRIAL_LEDGER_NATIVE_PACKET_ROSTER")
    for packet in packets:
        _native_require(type(packet) is OwnerValuePacketV1 and type(packet.packet_type) is str
                        and 0 < len(packet.packet_type) <= 256 and type(packet.authorized_binding_ids) is tuple
                        and 0 < len(packet.authorized_binding_ids) <= 4096,
                        "LP03_TRIAL_LEDGER_NATIVE_PACKET_ROSTER")
        _native_require(all(type(binding) is str and 0 < len(binding) <= 256 for binding in packet.authorized_binding_ids),
                        "LP03_TRIAL_LEDGER_NATIVE_PACKET_ROSTER")
    selected = tuple(packet for packet in packets if
        any(binding in ("FIVAB::MATH-12::p_values", "FIVAB::MATH-13::p_values", "FIVAB::MATH-15::loss_differentials", "FIVAB::MATH-16::loss_differentials")
            or binding in tuple(row.binding_id for selected_math in ("MATH-17", "MATH-18")
                for row in FORMULA_INPUT_AUTHORITY_BY_MATH_ID[selected_math])
            or binding in ("FIVAB::MATH-19::performance_matrix", "FIVAB::MATH-19::strategy_ids")
            for binding in packet.authorized_binding_ids)
        or packet.packet_type in ("MultipleTestingCandidatePValueLedgerV1", "PointInTimeLossDifferentialMatrixV1",
            "SharpeMomentAndTrialUniverseSnapshotV1", "PointInTimeStrategyPerformanceMatrixV1"))
    if ledger is None and not selected:
        _native_require(expected is None, "LP03_TRIAL_LEDGER_ORIGINAL_CHANGED")
        return None
    _native_require(type(ledger) is _EvidenceCompleteMaterialTrialLedgerV1 and len(selected) == len(registry._packets),
                    "LP03_TRIAL_LEDGER_ORIGINAL_OWNER_REQUIRED")
    construction = _EVIDENCE_TRIAL_LEDGER_CONSTRUCTIONS_V1.get(registry)
    _native_require(construction is not None and construction[0]() is ledger and construction[1]() is ledger.guard,
                    "LP03_TRIAL_LEDGER_ORIGINAL_CONSTRUCTOR_REQUIRED")
    if expected is not None:
        _native_require(type(expected) is tuple and len(expected) == 3 and expected[0] is ledger
                        and expected[1] is ledger.guard and expected[2] is ledger.sealed,
                        "LP03_TRIAL_LEDGER_ORIGINAL_CHANGED")
    original_guard = construction[1]()
    original, rows, phase, sealed = original_guard("INSPECT")
    _native_require(phase == "SEALED" and sealed is not None and sealed[0] is registry
                    and type(sealed[3]) is int and sealed[3] > 0,
                    "LP03_TRIAL_LEDGER_ORIGINAL_SEAL_REQUIRED")
    if original[2] == "MATH-19":
        _native_require(sealed[1] is registry._packets and len(selected) == 2
            and all(left is right for left, right in zip(selected, sealed[1], strict=True)),
            "LP03_CSCV_LEDGER_COMPLETE_PACKET_ROSTER")
    elif original[2] in ("MATH-17", "MATH-18"):
        _native_require(sealed[1] is registry._packets
            and len(selected) == (5 if original[2] == "MATH-17" else 6)
            and all(left is right for left, right in zip(selected, sealed[1], strict=True)),
            "LP03_SHARPE_LEDGER_COMPLETE_PACKET_ROSTER")
    else:
        _native_require(len(selected) == 1 and sealed[1] is selected[0],
            "LP03_TRIAL_LEDGER_ORIGINAL_SEAL_REQUIRED")
    if scope is not None:
        from .models import EvidenceAssemblyScopeV1, EvidenceOriginV1
        _native_require(type(scope) is EvidenceAssemblyScopeV1 and scope.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
                        and min(scope.snapshot_decision_wall_ns, scope.snapshot_pit_cutoff_wall_ns) >= sealed[3],
                        "LP03_TRIAL_LEDGER_NOT_VISIBLE_AT_CUTOFF")
    return (ledger, ledger.guard, sealed) if expected is None else expected


class _EvidencePublishedKelly27V1:
    """Prospective M27 result custody; never a current consumer grant.

    The association exists before execution. Completion comes only from the
    issuer's successful terminal tail. A later native visibility observation
    distinguishes the published result from its completed source handoff.
    """

    __slots__ = ("original", "prepared", "completion", "materialization", "materialized", "reads", "guard")

    def __init__(self, attempt):
        from .persistence import _EvidenceAttemptOperationV1
        from uuid import uuid4
        registration = attempt.registration
        _native_require(type(attempt) is _EvidenceAttemptOperationV1
                        and registration.issuer.lock._is_owned() and registration.issuer.operation is None
                        and registration.attempts.get((attempt.request.lane, attempt.request.attempt_ordinal)) is attempt
                        and attempt.phase == "ADMISSION_VALIDATING" and attempt.published_kelly27 is None
                        and attempt.request.lane.value == "REPLAY"
                        and registration.envelope_entry[3].component_closure == ("MATH-27",),
                        "LP03_KELLY27_PROSPECTIVE_ASSOCIATION_REQUIRED")
        self.original = (attempt, registration, attempt.request, "LP03-KELLY27-SOURCE::" + uuid4().hex,
                         "LP03_FIVAB::full_kelly_fraction::MATH-28")
        self.prepared = self.completion = self.materialized = None
        self.materialization, self.reads = "NOT_STARTED", ()
        original, prepared, materialized, reads, phase = self.original, None, None, (), "NOT_STARTED"
        read_originals = ()
        def retain(stage, value=None):
            nonlocal prepared, materialized, reads, phase, read_originals
            _native_require(self.original is original and self.prepared is prepared and self.materialized is materialized
                            and self.reads is reads and self.materialization == phase,
                            "LP03_KELLY27_SOURCE_ORIGINAL_ROSTER_CHANGED")
            if prepared is not None:
                _require_evidence_resolution_witness_v1(prepared[2], prepared[7], canonical=False)
            if materialized is not None:
                _require_evidence_resolution_witness_v1(materialized[1], materialized[6], canonical=False)
            for read, original_read, guard in read_originals:
                _native_require(read.original is original_read and read.guard is guard, "LP03_KELLY27_SOURCE_READ_CUSTODY_CHANGED")
                guard("INSPECT")
            if stage == "PREPARE":
                _native_require(prepared is None and phase == "NOT_STARTED", "LP03_KELLY27_SOURCE_PREPARATION_STATE")
                prepared = self.prepared = value
            elif stage == "BEGIN":
                _native_require(prepared is not None and phase == "NOT_STARTED", "LP03_KELLY27_SOURCE_ALREADY_MATERIALIZED_OR_UNRESOLVED")
                phase = self.materialization = "MATERIALIZING"
            elif stage == "MATERIALIZED":
                _native_require(phase == "MATERIALIZING" and materialized is None, "LP03_KELLY27_SOURCE_ALREADY_MATERIALIZED_OR_UNRESOLVED")
                materialized = self.materialized = value
                phase = self.materialization = "MATERIALIZED"
            elif stage == "READ":
                _native_require(phase == "MATERIALIZED" and type(value) is _EvidencePublishedSourceReadV1,
                                "LP03_KELLY27_SOURCE_READ_CUSTODY_CHANGED")
                reads = self.reads = (*reads, value)
                read_originals = (*read_originals, (value, value.original, value.guard))
            else:
                _native_require(stage == "INSPECT" and value is None, "LP03_KELLY27_SOURCE_GUARD_OPERATION")
            return prepared, materialized, reads, phase
        self.guard = retain

    def __copy__(self):
        raise TypeError("LP03 published source custody cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 published source custody cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 published source custody cannot be serialized")

    def _assert_original_v1(self, *, completed=False, canonical=False):
        from .persistence import _EvidenceLaneOperationV1, _EvidenceAttemptOperationV1
        _native_require(type(self) is _EvidencePublishedKelly27V1 and type(self.original) is tuple and len(self.original) == 5,
                        "LP03_KELLY27_SOURCE_ASSOCIATION_CHANGED")
        attempt, registration, request, _ref, binding = self.original
        _native_require(type(attempt) is _EvidenceAttemptOperationV1 and attempt.published_kelly27 is self
                        and type(attempt.original) is tuple and len(attempt.original) == 12 and attempt.original[10] is self
                        and attempt.original[11] is self.guard
                        and attempt.registration is registration and attempt.request is request
                        and request.lane.value == "REPLAY"
                        and registration.attempts.get((request.lane, request.attempt_ordinal)) is attempt
                        and registration.envelope_entry[3].component_closure == ("MATH-27",)
                        and binding == "LP03_FIVAB::full_kelly_fraction::MATH-28",
                        "LP03_KELLY27_SOURCE_ASSOCIATION_CHANGED")
        self.guard("INSPECT")
        if self.prepared is not None:
            lane, pins, _body, _context, _clocks, _targets, _upstream, _witness = self.prepared
            _native_require(lane is attempt.lane_operation and type(pins) is tuple and len(pins) == 9
                and all(left is right for left, right in zip(pins, (
                lane.original, lane.record_original, lane.row_original, lane.data_observations_original,
                lane.publication_original, lane.publication_readback_original, lane.dependency_original,
                lane.final_original, lane.final_readback_original))), "LP03_KELLY27_SOURCE_PRODUCER_CHANGED")
            if canonical:
                _EvidenceLaneOperationV1._assert_original_v1(lane)
        if completed:
            _native_require(self.prepared is not None and self.completion is not None
                            and attempt.terminal_original is self.completion is attempt.terminal_proof
                            and self.completion[0] is self.prepared[0]
                            and attempt.phase == "COLLECTION_COMPLETE_RESERVED"
                            and self.prepared[0].finalization_phase == "COMPLETED_RESERVED",
                            "LP03_KELLY27_SOURCE_COMPLETION_REQUIRED")
            if canonical:
                _EvidenceAttemptOperationV1._require_terminal_v1(attempt)

    def _prepare_v1(self, lane):
        from .persistence import _EvidenceLaneOperationV1
        from .serialization import deterministic_json, safe_json_loads
        from .models import _evidence_kelly27_source_slices_v1
        _EvidencePublishedKelly27V1._assert_original_v1(self)
        _native_require(self.prepared is None and self.completion is None and lane is self.original[0].lane_operation
                        and lane.finalization_phase == "COMMITTED_AND_READBACK",
                        "LP03_KELLY27_SOURCE_PREPARATION_STATE")
        _EvidenceLaneOperationV1._assert_original_v1(lane)
        segment = lane.records.receipt_records[-1].typed_payload.record
        source_payload = segment.exact_ordered_events[0]["payload"]
        sources = _evidence_kelly27_source_slices_v1(source_payload)
        source_events = tuple(part.reconstructed_canonical_events[0] for part in sources)
        raw = safe_json_loads(lane.raw.existing_receipt.output_json)
        _native_require(type(raw) is dict and set(raw) == {"raw_fraction", "sizing_candidate"}
                        and all(type(value) is str for value in raw.values())
                        and lane.raw.existing_receipt.specification_id == "MATH-27",
                        "LP03_KELLY27_SOURCE_ORIGINAL_RAW_REQUIRED")
        context = lane.exchange[0]._resolution.execution_context
        upstream = []
        for part in sources:
            matches = tuple(entry for entry in lane.attempt.registration.source_slice_originals
                if entry[0] is lane.attempt and entry[3].original_record_refs == part.original_record_refs)
            _native_require(len(matches) == 1, "LP03_KELLY27_SOURCE_UPSTREAM_CUSTODY_REQUIRED")
            entry = matches[0]
            upstream.append((entry[1], entry[2], tuple(entry[1].rights_by_id[ref] for ref in entry[2].required_original_rights_refs)))
        _native_require(upstream[0][0] is upstream[1][0], "LP03_KELLY27_SHARED_UPSTREAM_OWNER_PROFILE_REQUIRED")
        targets = ((lane.platform._store, lane.platform._host,
                    (*tuple((table, row) for table, row, _record in lane.rows), ("receipt_records", lane.publication[2]))),
                   (lane.issuer.control_store, lane.issuer.host,
                    (*lane.control_dependencies, *tuple((table, row) for table, row, _record in lane.final_rows))))
        _native_require(sum(len(rows) for _adapter, _host, rows in targets) <= 256,
                        "LP03_KELLY27_SOURCE_PARENT_ROSTER_BOUND")
        for _adapter, _host, rows in targets:
            _native_require(len({(table, row[0]) for table, row in rows}) == len(rows),
                            "LP03_KELLY27_SOURCE_DUPLICATE_PARENT")
        raw_rows = tuple(row for table, row, _record in lane.rows if table == "receipt_records" and row[0] == lane.raw.record_id)
        _native_require(len(raw_rows) == 1, "LP03_KELLY27_SOURCE_ORIGINAL_RAW_REQUIRED")
        values = MappingProxyType(dict(full_kelly_fraction=raw["raw_fraction"], published_source_context=MappingProxyType(dict(
            profile="LP03_PUBLISHED_MATH27_RAW_SOURCE_V1", producer_role="MATH27_COMPUTATION",
            binding_id=self.original[4], producer_lane=lane.attempt.request.lane.value,
            original_raw_record_json=raw_rows[0][-1], original_raw_output_json=lane.raw.existing_receipt.output_json,
            original_input_json=deterministic_json(dict(win_probability=source_events[0]["values"]["win_probability"],
                net_odds=source_events[1]["values"]["net_odds"])),
            invocation_contract=lane.exchange[2]["invocation_contract"], input_lock_ref=lane.attempt.registration.compilation.input_lock.input_lock_id,
            original_source_payload=source_payload, original_grant_ref=lane.attempt.grant_record.record_id,
            original_fence_ref=lane.attempt.payload.fence_ref, publication_record_json=lane.publication[2][-1],
            publication_available_wall_ns=lane.availability.available_at["wall_ns"],
            publication_availability_observation=lane.availability.available_at,
            data_commit_observation=lane.commit_observation, data_readback_observation=lane.readback_observation,
            publication_commit_observation=lane.publication_commit_observation,
            publication_readback_observation=lane.publication_readback_observation,
            finalization_readback_observation=lane.final_readback_observation,
            collection_complete_ref=lane.final_state.record_id, lane_registration_ref=lane.lane_registration.record_id))))
        # The existing closed graph walker bounds nodes, depth, every token,
        # and aggregate escaped output BEFORE serialization. Its conservative
        # construction bound and the smaller wire bound are separate limits.
        _EvidenceLaneOperationV1._room_v1(lane, read_bytes=262144)
        witness = _evidence_native_graph_witness_v1(values, (), maximum_bytes=262144)
        _native_require(len(witness[2].encode("utf-8")) <= 65536, "LP03_KELLY27_SOURCE_BODY_BOUND")
        body = values
        observed = lane.exchange[2]["invocation_measurement"]["completed"][0]
        available, processed = lane.availability.available_at["wall_ns"], lane.final_readback_observation[0]
        clocks = tuple(zip(("observed_time", "effective_time", "available_time", "received_time", "processed_time", "as_of_time"),
                           (observed, observed, available, processed, processed, processed), strict=True))
        pins = (lane.original, lane.record_original, lane.row_original, lane.data_observations_original,
                lane.publication_original, lane.publication_readback_original, lane.dependency_original,
                lane.final_original, lane.final_readback_original)
        self.guard("PREPARE", (lane, pins, body, context, clocks, targets, tuple(upstream), witness))
        _EvidencePublishedKelly27V1._assert_original_v1(self, canonical=True)

    def _materialize_source_v1(self):
        """One original-owner setup; returned registry grants no reads."""
        from .latency_policy import _EvidenceLocalClockV1
        from .serialization import deterministic_json, safe_json_loads
        _EvidencePublishedKelly27V1._assert_original_v1(self, completed=True)
        _native_require(self.materialization == "NOT_STARTED" and self.materialized is None,
                        "LP03_KELLY27_SOURCE_ALREADY_MATERIALIZED_OR_UNRESOLVED")
        self.guard("BEGIN")
        _EvidencePublishedKelly27V1._assert_original_v1(self, completed=True, canonical=True)
        lane, _pins, body, context, clocks, _targets, _upstream, witness = self.prepared
        registry = object.__new__(CanonicalOwnerPacketRegistryV1)
        values = safe_json_loads(witness[2])
        values["published_source_context"].update(completion_observation=self.completion[5],
            clock_domain_id=lane.issuer.clock.clock_domain_id,
            boot_identity_ref=lane.issuer.clock.boot_identity_ref, process_identity_ref=lane.issuer.clock.process_identity_ref)
        packet = OwnerValuePacketV1(packet_id=self.original[3], owner_id="QKU_COMPUTATION_CONTROL_PLANE.MATH-27",
            packet_type="LP03PublishedKellySourceV1", schema_id="LP03::MATH-27::PUBLISHED_RAW_SOURCE_V1", schema_version="1.0",
            context_id=context.context_id, scope=context.scope, source_epoch_id=lane.publication[0].record_id,
            input_version="1", clocks=PointInTimeClocksV1(**{name: datetime(1970, 1, 1, tzinfo=UTC)
                + timedelta(microseconds=ns // 1000) for name, ns in clocks}), ttl=context.maximum_age,
            values=values, authorized_binding_ids=(self.original[4],), producer_receipt_id=lane.raw.record_id,
            producer_receipt_type="LP03_MATH27_PUBLISHED_RAW_RECEIPT_V1",
            source_state_and_claim_lineage="LP03::MATH-27::ORIGINAL_PUBLISHED_RAW_RESULT", revision=1)
        CanonicalOwnerPacketRegistryV1.__init__(registry, (packet,))
        registry._evidence_published_kelly27_v1 = self
        packet_witness = _evidence_native_graph_witness_v1(packet,
            (OwnerValuePacketV1, ComputationScopeV1, PointInTimeClocksV1), maximum_bytes=262144)
        # Visibility is sampled only AFTER the original immutable registry and
        # complete packet witness exist. The source projection carries this
        # additional witness separately from the historical packet clocks.
        observed = _EvidenceLocalClockV1.observe_v1(lane.issuer.clock)
        _EvidencePublishedKelly27V1._assert_original_v1(self, completed=True, canonical=True)
        _require_evidence_resolution_witness_v1(packet, packet_witness, canonical=False)
        _native_require(observed[0] >= self.completion[5][0] >= clocks[-1][1]
                        and observed[1] >= self.completion[5][1], "LP03_KELLY27_SOURCE_VISIBILITY_CLOCK_ORDER")
        materialized = (registry, packet, observed, self.prepared, self.completion, registry._packets, packet_witness)
        self.guard("MATERIALIZED", materialized)
        _EvidencePublishedKelly27V1._assert_original_v1(self, completed=True, canonical=True)
        _native_require(registry._packets is self.materialized[5] and registry._packets[0] is packet
                        and registry._by_id[packet.packet_id] is packet,
                        "LP03_KELLY27_SOURCE_REGISTRY_CHANGED")
        return registry

    def _assert_scope_v1(self, scope, *, observed_wall_ns, purpose=None, principals=()):
        """Current consumer/upstream rights; no SQL or producer grant checks."""
        _EvidencePublishedKelly27V1._assert_original_v1(self, completed=True)
        _native_require(self.materialization == "MATERIALIZED" and self.materialized is not None
                        and self.materialized[3] is self.prepared and self.materialized[4] is self.completion,
                        "LP03_KELLY27_SOURCE_MATERIALIZATION_REQUIRED")
        registry, packet, visible, _prepared, _completion, packets, _witness = self.materialized
        _native_require(registry._packets is packets and packets[0] is packet and registry._by_id.get(packet.packet_id) is packet
                        and getattr(registry, "_evidence_published_kelly27_v1", None) is self,
                        "LP03_KELLY27_SOURCE_REGISTRY_CHANGED")
        _native_require(scope.snapshot_pit_cutoff_wall_ns >= visible[0]
                        and scope.snapshot_decision_wall_ns >= visible[0]
                        and visible[0] >= self.completion[5][0] >= self.prepared[0].final_readback_observation[0]
                        >= self.prepared[0].availability.available_at["wall_ns"], "LP03_KELLY27_SOURCE_NOT_VISIBLE_AT_CUTOFF")
        purpose = scope.source_purpose if purpose is None else purpose
        principals = (scope.assembler_principal,) if not principals else principals
        for custody, selection, policies in self.prepared[6]:
            with custody.lock:
                _EvidenceOwnerPacketCustodyV1._assert_original_v1(custody)
                _native_require(all(custody.rights_by_id.get(policy.rights_ref) is policy
                    and policy.rights_ref not in custody.withdrawn and policy.generation == custody.generation
                    and policy.origin is scope.origin and policy.valid_from_wall_ns <= observed_wall_ns
                    < policy.exclusive_expiry_wall_ns and observed_wall_ns < policy.exclusive_retention_wall_ns
                    and purpose in policy.source_purposes and set(principals) <= set(policy.consumer_principals)
                    for policy in policies), "LP03_KELLY27_UPSTREAM_CURRENT_USE_DENIED")


def _evidence_original_edge_measurement_v1(lane):
    """Select the original successful MATH-02 call and its durable parents."""
    from fractions import Fraction
    from hashlib import sha256

    from .evidence import _require_evidence_probability_edge_lane_v1
    from .lifecycle import EvidenceAttemptStateV1
    from .models import EvidenceLaneV1, EvidenceOriginV1
    from .persistence import _EvidenceAttemptObservationAppendV1, _EvidenceAttemptOperationV1, _EvidenceLaneOperationV1
    from .serialization import _native_strict_json

    _native_require(type(lane) is _EvidenceLaneOperationV1 and lane.issuer.lock._is_owned()
        and lane.issuer.operation is None and lane.attempt.request.lane is EvidenceLaneV1.REPLAY
        and lane.attempt.grant_record.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
        and lane.attempt.payload.component_closure == ("MATH-01", "MATH-02"),
        "LP03_MEASURED_EDGE_ORIGINAL_PUBLISHED_REPLAY_REQUIRED")
    complete = _EvidenceAttemptOperationV1._require_terminal_v1(lane.attempt)
    _native_require(complete[0] is lane and lane.phase == lane.publication_phase == "COMMITTED_AND_READBACK"
        and lane.finalization_phase == "COMPLETED_RESERVED"
        and lane.final_state.state is EvidenceAttemptStateV1.COLLECTION_COMPLETE,
        "LP03_MEASURED_EDGE_ORIGINAL_PUBLISHED_REPLAY_REQUIRED")
    producer, dependency, artifact, contracts = _require_evidence_probability_edge_lane_v1(lane)
    raw = lane.raw
    append = lane.attempt.observation_appends[-1]
    _EvidenceAttemptObservationAppendV1._assert_original_v1(append)
    terminal, native = append.body, complete[3][0]
    result, publication = lane.exchange[2], lane.publication[0]
    edge_stage = artifact["measured_original_stages"][2]
    measured = edge_stage["measurement"]
    pid, created_tick, _executable = native["process_identity"]
    _native_require(append.phase == "COMMITTED_AND_READBACK" and terminal["stage"] == "TERMINAL"
        and terminal["exchange_complete"] is True and terminal["native_observation"] == native
        and native["exit_code"] == native["active_processes"] == 0 and native["total_processes"] == 1
        and terminal["grant_ref"] == publication.original_grant_ref == lane.attempt.payload.grant_ref
        and terminal["fence_ref"] == publication.fence_ref == lane.attempt.payload.fence_ref
        and terminal["observation_ref"] == lane.final_state.process_observation_ref_or_absence
        and raw.dependency_receipt_refs == (terminal["grant_ref"], terminal["observation_ref"], producer.record_id)
        and terminal["invocation_measurement_or_absence"] == result["invocation_measurement"]
        and contracts[1].math_id == edge_stage["stage"] == "MATH-02" and measured["outcome"] == "SUCCESS"
        and measured["clock_domain_id"] == terminal["clock_domain_id"]
        and measured["boot_identity_ref"] == terminal["boot_identity_ref"]
        and measured["process_identity_ref"] == f'LP03-PROCESS::{pid}:{created_tick}:{measured["boot_identity_ref"].removeprefix("LP03-BOOT::")}'
        and raw.latency_ns == measured["duration_ns"],
        "LP03_MEASURED_EDGE_ORIGINAL_PROCESS_AND_CALL")
    observed, visible = tuple(measured["completed"]), lane.availability.available_at
    _native_require(raw.record_id in publication.underlying_record_refs
        and dependency.record_id in publication.underlying_record_refs
        and lane.lane_registration.accepted_publication_ref is lane.publication_ref
        and lane.lane_registration.terminal_receipt_ref == lane.final_state.record_id
        and observed[0] <= terminal["observed_at"][0] <= append.readback_observation[0] <= lane.commit_observation[0]
        <= lane.readback_observation[0] <= lane.publication_commit_observation[0]
        <= lane.publication_readback_observation[0] <= visible["wall_ns"]
        <= lane.final_readback_observation[0] <= complete[5][0]
        and observed[1] <= terminal["observed_at"][1] <= visible["monotonic_ns"] <= complete[5][1],
        "LP03_MEASURED_EDGE_ORIGINAL_OBSERVATION_ORDER")
    data_targets = (*tuple((table, row) for table, row, _record in lane.rows),
                    ("receipt_records", lane.publication[2]))
    control_targets = (*lane.control_dependencies,
                       *tuple((table, row) for table, row, _record in lane.final_rows))
    targets = ((lane.platform._store, lane.platform._host, data_targets),
               (lane.issuer.control_store, lane.issuer.host, control_targets))
    _native_require(len(data_targets) + len(control_targets) <= 256 and all(
        len({(table, row[0]) for table, row in rows}) == len(rows) for _adapter, _host, rows in targets),
        "LP03_MEASURED_EDGE_ORIGINAL_PARENT_ROSTER")
    original_rows = {row[0]: row[-1] for table, row in data_targets if table == "receipt_records"
        and row[0] in (raw.record_id, dependency.record_id, publication.record_id)}
    _native_require(set(original_rows) == {raw.record_id, dependency.record_id, publication.record_id},
        "LP03_MEASURED_EDGE_ORIGINAL_PARENT_ROSTER")
    registered = lane.attempt.registration
    sources = []
    for part in lane.exchange[0]._source_slices:
        candidates = tuple(entry for entry in registered.source_slice_originals
            if entry[0] is lane.attempt and entry[3] is part)
        _native_require(len(candidates) == 1, "LP03_MEASURED_EDGE_ORIGINAL_UPSTREAM_CUSTODY")
        entry, = candidates
        sources.append((entry[1], entry[2], tuple(entry[1].rights_by_id[ref] for ref in entry[2].required_original_rights_refs)))
    source_context = lane.attempt.invocations[0]._resolution.execution_context
    _native_require(source_context.context_id == dependency.execution_context_ref == raw.execution_context_ref
        and raw.output_unit == "probability points" and raw.output_basis == "MODEL_MINUS_MARKET_SAME_SNAPSHOT",
        "LP03_MEASURED_EDGE_ORIGINAL_AMOUNT_CONTEXT")
    edge = _native_strict_json(raw.existing_receipt.output_json.encode("utf-8"), max_bytes=256,
        max_nodes=1, binary64_numbers=True)
    _native_require(type(edge) is float, "LP03_MEASURED_EDGE_ORIGINAL_AMOUNT")
    seconds = float(Fraction(measured["duration_ns"], 10**9))
    body = dict(profile="ORIGINAL_PUBLISHED_EDGE_AND_CALL_MEASUREMENT_V1", original_lane="REPLAY",
        original_context_ref=source_context.context_id, original_input_lock_ref=dependency.input_lock_ref,
        original_grant_ref=terminal["grant_ref"], original_fence_ref=terminal["fence_ref"],
        original_edge_ref=raw.record_id, original_edge_output_json=raw.existing_receipt.output_json,
        original_measurement_ref=dependency.record_id, original_process_observation_ref=terminal["observation_ref"],
        original_publication_ref=publication.record_id, original_collection_complete_ref=lane.final_state.record_id,
        original_data_store_id=lane.publication_ref.store_id,
        original_row_sha256={ref:sha256(wire.encode("utf-8")).hexdigest() for ref, wire in original_rows.items()},
        measured_original_edge_call=measured, measured_original_edge_unit=raw.output_unit,
        measured_original_edge_basis=raw.output_basis,
        publication_available_observation=dict(visible), collection_complete_observed=complete[5][:2])
    return edge, seconds, body, source_context, targets, tuple(sources), complete


class _EvidencePublishedEdgeLatencyV1:
    """One original REPLAY edge and timing closure owned by the publishing lane."""

    __slots__ = ("original", "prepared", "materialized", "reads", "guard")

    def __init__(self, lane):
        from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
        from .latency_policy import _EvidenceLocalClockV1
        from .persistence import _EvidenceLaneOperationV1
        from .serialization import _evidence_canonical_object_v1, deterministic_json

        _native_require(type(lane) is _EvidenceLaneOperationV1, "LP03_MEASURED_EDGE_ORIGINAL_PUBLISHED_REPLAY_REQUIRED")
        with lane.issuer.lock:
            _native_require(lane.published_edge_latency is None, "LP03_MEASURED_EDGE_ALREADY_MATERIALIZED")
            edge, seconds, body, context, targets, upstream, complete = _evidence_original_edge_measurement_v1(lane)
            bindings = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-41"].bindings[:2]
            clocks = tuple(zip(("observed_time", "effective_time", "available_time", "received_time", "processed_time", "as_of_time"),
                (body["measured_original_edge_call"]["completed"][0],) * 2
                + (body["publication_available_observation"]["wall_ns"],)
                + (lane.final_readback_observation[0],) * 3, strict=True))
            clock_values = PointInTimeClocksV1(**{name: datetime(1970, 1, 1, tzinfo=UTC)
                + timedelta(microseconds=tick // 1000) for name, tick in clocks})
            roles = ((bindings[0], edge, body["original_edge_ref"]),
                     (bindings[1], seconds, body["original_measurement_ref"]))
            # Keep native clock declarations in two bounded exact capsules
            # inside the recorded event, while preserving the original body.
            source_fact = dict(body,
                measured_original_edge_call=deterministic_json(body["measured_original_edge_call"]),
                publication_available_observation=deterministic_json(body["publication_available_observation"]))
            packets = []
            for binding, value, original_ref in roles:
                source_data = dict(quantity_scope_ref=context.scope.instrument_or_contract_scope_id,
                    horizon_ref=context.scope.event_scope_id, output_unit="PROBABILITY-POINT",
                    output_basis="REMAINING_EDGE_AMOUNT_AT_MEASURED_LATENCY",
                    ordered_coordinate_ids=(context.scope.instrument_or_contract_scope_id,),
                    original_time_unit="SECONDS", original_quantity_unit="PROBABILITY-POINT",
                    binding_id=binding.binding_id, producer_role=binding.producer_role,
                    basis_ref=binding.unit_or_basis_requirement,
                    original_fact=dict(original_receipt_ref=original_ref,
                        quantity_scope_ref=context.scope.instrument_or_contract_scope_id, horizon_ref=context.scope.event_scope_id,
                        basis_ref=binding.unit_or_basis_requirement, **source_fact))
                source_data = _evidence_canonical_object_v1(
                    deterministic_json(source_data).encode("utf-8", "strict"), max_bytes=65536)
                packets.append(OwnerValuePacketV1(packet_id=original_ref,
                    owner_id="QKU_COMPUTATION_CONTROL_PLANE.MATH-02",
                    packet_type="LP03OriginalBinary64ExecutionInputSourceV1",
                    schema_id="LP03::MATH-41::ORIGINAL_INPUT_SOURCE_V1", schema_version="1.0",
                    context_id=context.context_id, scope=context.scope, source_epoch_id=context.source_epoch_id,
                    input_version=context.input_version, clocks=clock_values, ttl=context.maximum_age,
                    values={binding.input_name:deterministic_json(value), "original_execution_context":source_data},
                    authorized_binding_ids=(binding.binding_id,), producer_receipt_id=original_ref,
                    producer_receipt_type="LP03::MATH-41::ORIGINAL_INPUT_RECEIPT_V1",
                    source_state_and_claim_lineage=f"LP03::MATH-41::ORIGINAL_EXECUTION_INPUT::{binding.producer_role}",
                    revision=body["original_publication_ref"]))
            registry = CanonicalOwnerPacketRegistryV1(tuple(packets))
            registry._evidence_published_edge_latency_v1 = self
            fingerprints = tuple(_evidence_native_graph_witness_v1(packet,
                (OwnerValuePacketV1, ComputationScopeV1, PointInTimeClocksV1), maximum_bytes=262144) for packet in registry._packets)
            observed = _EvidenceLocalClockV1.observe_v1(lane.issuer.clock)
            _native_require(observed[0] >= complete[5][0] >= clocks[-1][1] and observed[1] >= complete[5][1],
                "LP03_MEASURED_EDGE_ORIGINAL_VISIBILITY_ORDER")
            original = self.original = (lane, lane.original, lane.record_original, lane.row_original,
                lane.publication_original, lane.publication_readback_original, lane.dependency_original, lane.final_readback_original,
                lane.final_original, complete)
            prepared = self.prepared = (lane, original, body, context, clocks, targets, upstream)
            materialized = self.materialized = (registry, registry._packets, observed, fingerprints)
            reads = self.reads = ()
            read_witnesses = ()

            def retain(stage, value=None):
                nonlocal reads, read_witnesses
                _native_require(self.original is original and self.prepared is prepared and self.materialized is materialized
                    and self.reads is reads, "LP03_MEASURED_EDGE_SOURCE_ROSTER_CHANGED")
                for packet, witness in zip(materialized[1], materialized[3], strict=True):
                    _require_evidence_resolution_witness_v1(packet, witness, canonical=False)
                for read, read_original, guard in read_witnesses:
                    _native_require(read.original is read_original and read.guard is guard,
                        "LP03_MEASURED_EDGE_SOURCE_READ_CUSTODY_CHANGED")
                    guard("INSPECT")
                if stage == "READ":
                    _native_require(type(value) is _EvidencePublishedSourceReadV1,
                        "LP03_MEASURED_EDGE_SOURCE_READ_CUSTODY_CHANGED")
                    reads = self.reads = (*reads, value)
                    read_witnesses = (*read_witnesses, (value, value.original, value.guard))
                else:
                    _native_require(stage == "INSPECT" and value is None, "LP03_MEASURED_EDGE_SOURCE_GUARD_OPERATION")

            self.guard = retain
            lane.published_edge_latency = self
            _EvidencePublishedEdgeLatencyV1._assert_original_v1(self, completed=True, canonical=True)

    def __copy__(self):
        raise TypeError("LP03 published edge and latency custody cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 published edge and latency custody cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 published edge and latency custody cannot be serialized")

    def _assert_original_v1(self, *, completed=False, canonical=False):
        from .persistence import _EvidenceAttemptOperationV1, _EvidenceLaneOperationV1

        _native_require(type(self) is _EvidencePublishedEdgeLatencyV1 and type(self.original) is tuple
            and len(self.original) == 10 and self.prepared[1] is self.original,
            "LP03_MEASURED_EDGE_SOURCE_ROSTER_CHANGED")
        lane = self.original[0]
        _native_require(type(lane) is _EvidenceLaneOperationV1 and lane.published_edge_latency is self
            and lane.attempt.lane_operation is lane and lane.attempt.terminal_original is lane.attempt.terminal_proof
            and lane.phase == lane.publication_phase == "COMMITTED_AND_READBACK"
            and lane.finalization_phase == "COMPLETED_RESERVED" and all(prior is current for prior, current in zip(
                self.original[1:], (lane.original, lane.record_original, lane.row_original, lane.publication_original,
                    lane.publication_readback_original, lane.dependency_original, lane.final_readback_original,
                    lane.final_original, lane.attempt.terminal_original), strict=True)),
            "LP03_MEASURED_EDGE_ORIGINAL_PUBLISHED_REPLAY_REQUIRED")
        registry, packets, _visible, _pins = self.materialized
        _native_require(registry._packets is packets and all(registry._by_id.get(packet.packet_id) is packet for packet in packets)
            and getattr(registry, "_evidence_published_edge_latency_v1", None) is self,
            "LP03_MEASURED_EDGE_SOURCE_REGISTRY_CHANGED")
        self.guard("INSPECT")
        if canonical:
            _native_require(_EvidenceAttemptOperationV1._require_terminal_v1(lane.attempt) is self.original[-1],
                "LP03_MEASURED_EDGE_ORIGINAL_PUBLISHED_REPLAY_REQUIRED")

    def _assert_scope_v1(self, scope, *, observed_wall_ns, purpose=None, principals=()):
        """Recheck original source rights and the consumer's signed historical cutoff."""
        from .models import EvidenceOriginV1

        _EvidencePublishedEdgeLatencyV1._assert_original_v1(self, completed=True)
        visible = self.materialized[2][0]
        _native_require(scope.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
            and self.original[-1][5][0] <= visible <= scope.snapshot_pit_cutoff_wall_ns
            <= scope.snapshot_decision_wall_ns <= observed_wall_ns, "LP03_MEASURED_EDGE_NOT_VISIBLE_AT_CUTOFF")
        purpose = scope.source_purpose if purpose is None else purpose
        principals = (scope.assembler_principal,) if not principals else principals
        for custody, _selection, policies in self.prepared[6]:
            _native_require(custody.lock._is_owned(), "LP03_MEASURED_EDGE_ORIGINAL_UPSTREAM_LOCK_REQUIRED")
            _EvidenceOwnerPacketCustodyV1._assert_original_v1(custody)
            _native_require(all(custody.rights_by_id.get(policy.rights_ref) is policy
                and policy.rights_ref not in custody.withdrawn and policy.generation == custody.generation
                and policy.origin is scope.origin and policy.valid_from_wall_ns <= observed_wall_ns
                < min(policy.exclusive_expiry_wall_ns, policy.exclusive_retention_wall_ns)
                and purpose in policy.source_purposes and set(principals) <= set(policy.consumer_principals)
                for policy in policies), "LP03_MEASURED_EDGE_ORIGINAL_UPSTREAM_RIGHTS_DENIED")

class _EvidencePublishedSourceReadV1:
    """Finite consumer read of a selected original published source closure."""

    __slots__ = ("original", "issuer", "consumer", "read_target", "observations", "completed", "source_result", "phase", "guard")

    def __init__(self, consumer, custody, selection):
        from .persistence import _EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1
        association = _EvidenceOwnerPacketCustodyV1._published_source_v1(custody)
        owner = type(association)
        _native_require(owner in (_EvidencePublishedKelly27V1, _EvidencePublishedEdgeLatencyV1),
                        "LP03_ORIGINAL_PUBLISHED_SOURCE_REQUIRED")
        kelly = owner is _EvidencePublishedKelly27V1
        component = "MATH-28" if kelly else "MATH-41"
        _native_require(type(consumer) in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1)
                        and consumer.envelope_entry[3].component_closure == (component,)
                        and consumer.issuer.operation is consumer and consumer.issuer.lock._is_owned()
                        and custody.lock._is_owned() and any(custody is row for row in consumer.issuer.source_custodies)
                        and any(selection is row for row in consumer.envelope_entry[3].assembly_scope.source_selections),
                        "LP03_KELLY27_FRESH_CONSUMER_SCOPE_REQUIRED" if kelly else "LP03_MEASURED_EDGE_CONSUMER_SCOPE_REQUIRED")
        owner._assert_original_v1(association, completed=True, canonical=True)
        packets = (association.materialized[1],) if kelly else association.materialized[1]
        selected = tuple(packet for packet in packets if selection.selection.record_refs == (packet.packet_id,))
        _native_require(len(selected) == 1
                        and selection.original_store_id == association.prepared[0].publication_ref.store_id
                        and selection.allowed_fields == tuple(selected[0].values),
                        "LP03_KELLY27_EXACT_CONSUMER_SOURCE_REQUIRED" if kelly else "LP03_MEASURED_EDGE_EXACT_CONSUMER_SOURCE_REQUIRED")
        self.consumer, self.issuer = consumer, consumer.issuer
        self.original = (consumer, custody, selection, association, association.prepared, association.materialized,
                         association.prepared[5], tuple(consumer.consumed.items()))
        self.read_target, self.observations, self.completed, self.source_result = None, (), None, None
        self.phase = "RESERVED"
        original, observations, completed, result, phase = self.original, (), None, None, "RESERVED"
        def retain(stage, value=None):
            nonlocal observations, completed, result, phase
            _native_require(self.original is original and self.observations is observations and self.completed is completed
                            and self.source_result is result and self.phase == phase,
                            "LP03_KELLY27_SOURCE_READ_CUSTODY_CHANGED")
            if stage == "BEGIN":
                _native_require(phase == "RESERVED", "LP03_KELLY27_SOURCE_READ_ALREADY_STARTED")
                phase = self.phase = "READING"
            elif stage == "OBSERVE":
                _native_require(phase == "READING" and len(observations) < sum(len(row[2]) for row in original[6]),
                                "LP03_KELLY27_SOURCE_PARENT_ROSTER_BOUND")
                observations = self.observations = (*observations, value)
            elif stage == "COMPLETE":
                _native_require(phase == "READING" and len(observations) == sum(len(row[2]) for row in original[6]),
                                "LP03_KELLY27_SOURCE_READBACK_REQUIRED")
                completed = self.completed = (original, observations, value)
                phase = self.phase = "READBACK_CONFIRMED"
            elif stage == "RESULT":
                _native_require(phase == "READBACK_CONFIRMED" and result is None, "LP03_KELLY27_SOURCE_READBACK_REQUIRED")
                result = self.source_result = (value, completed)
            else:
                _native_require(stage == "INSPECT" and value is None, "LP03_KELLY27_SOURCE_GUARD_OPERATION")
        self.guard = retain
        _native_require(len(association.reads) < consumer.consumed["record_reads"] + 1,
                        "LP03_KELLY27_SOURCE_READ_ROSTER_BOUND")
        association.guard("READ", self)

    def _assert_original_v1(self):
        original = self.original
        _native_require(type(self) is _EvidencePublishedSourceReadV1 and type(original) is tuple and len(original) == 8
                        and self.consumer is original[0] and self.issuer is self.consumer.issuer
                        and _EvidenceOwnerPacketCustodyV1._published_source_v1(original[1]) is original[3]
                        and original[3].prepared is original[4] and original[3].materialized is original[5]
                        and original[4][5] is original[6] and any(row is self for row in original[3].reads)
                        and (self.read_target is None or any(self.read_target is row for row in original[6])),
                        "LP03_KELLY27_SOURCE_READ_CUSTODY_CHANGED")
        type(original[3])._assert_original_v1(original[3], completed=True)

    def _room_v1(self, **increments):
        type(self.consumer)._room_v1(self.consumer, **increments)

    def _charge_v1(self, **increments):
        type(self.consumer)._charge_v1(self.consumer, **increments)

    def _check_current_v1(self):
        from .persistence import _EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1
        _EvidencePublishedSourceReadV1._assert_original_v1(self)
        consumer, custody, _selection, association, _prepared, _materialized, _targets, _prefix = self.original
        _native_require(type(consumer) in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1)
                        and consumer.issuer.operation is consumer and consumer.issuer.lock._is_owned() and custody.lock._is_owned(),
                        "LP03_KELLY27_FRESH_CONSUMER_SCOPE_REQUIRED")
        observed = type(consumer)._check_current_v1(consumer)
        purpose = "EVIDENCE_INPUT_ASSEMBLY_V1"
        principals = (consumer.envelope_entry[3].assembly_scope.assembler_principal,)
        if type(consumer) is _EvidenceRegistrationOperationV1:
            attempt = consumer.active_attempt
            _native_require(attempt is not None and attempt.invocation_state == "READING_ORIGINAL_INPUTS"
                            and any(self.original[2] is row for row in attempt.allowed_reads),
                            "LP03_KELLY27_FRESH_CONSUMER_SCOPE_REQUIRED")
            purpose = "EVIDENCE_LANE_EXECUTION_V1"
            principals = (attempt.payload.producer_principal, attempt.payload.service_principal)
        type(association)._assert_scope_v1(association, consumer.envelope_entry[3].assembly_scope,
            observed_wall_ns=observed[0], purpose=purpose, principals=principals)
        for adapter, _host, _rows in self.original[6]:
            _native_require(purpose in adapter._evidence_store_binding_v1.binding.allowed_reader_purposes,
                            "LP03_KELLY27_PRODUCER_STORE_READ_PURPOSE_DENIED")
        _EvidencePublishedSourceReadV1._assert_original_v1(self)
        return observed

    def _read_v1(self):
        import sqlite3
        from .persistence import _EvidenceBoundStoreV1
        from .sqlite_reference import REFERENCE_SCHEMA_COLUMNS_V1
        _EvidencePublishedSourceReadV1._assert_original_v1(self)
        _native_require(self.phase == "RESERVED" and self.completed is None and self.observations == () and self.read_target is None,
                        "LP03_KELLY27_SOURCE_READ_ALREADY_STARTED")
        self.guard("BEGIN")
        targets = self.original[6]
        expected_reads = sum(len(rows) + 1 for _adapter, _host, rows in targets)
        _EvidencePublishedSourceReadV1._room_v1(self, owner_queries=expected_reads, record_reads=expected_reads,
            query_result_records=expected_reads,
            read_bytes=sum(len(row[-1].encode("utf-8")) + len(row[0].encode("utf-8")) + 21
                for _adapter, _host, rows in targets for _table, row in rows)
                + sum(len(adapter.database_path.encode("utf-8")) + 5 for adapter, _host, _rows in targets))
        for target in targets:
            adapter, host, rows = target
            self.read_target = target
            _EvidencePublishedSourceReadV1._check_current_v1(self)
            reader = _EvidenceBoundStoreV1._open_independent_readback_v1(adapter._evidence_store_binding_v1, host, adapter, self)
            try:
                for table, row in rows:
                    _native_require(table in REFERENCE_SCHEMA_COLUMNS_V1, "LP03_KELLY27_SOURCE_PARENT_TABLE")
                    columns, raw = REFERENCE_SCHEMA_COLUMNS_V1[table], row[-1].encode("utf-8")
                    sql = ("SELECT length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) FROM "
                        + table + " WHERE " + " AND ".join(column + " IS ?" for column in columns[:-1]))
                    _EvidencePublishedSourceReadV1._room_v1(self, owner_queries=1, record_reads=1,
                        query_result_records=1, read_bytes=len(raw) + 21)
                    _EvidencePublishedSourceReadV1._check_current_v1(self)
                    _EvidencePublishedSourceReadV1._charge_v1(self, owner_queries=1)
                    cursor = sqlite3.Connection.execute(reader, sql, (len(raw) + 1, *row[:-1]))
                    try:
                        actual = sqlite3.Cursor.fetchmany(cursor, 2)
                    finally:
                        sqlite3.Cursor.close(cursor)
                    _EvidencePublishedSourceReadV1._charge_v1(self, record_reads=len(actual), query_result_records=len(actual),
                        read_bytes=sum(len(str(size)) + len(body) for size, body in actual))
                    _native_require(actual == [(len(raw), raw)], "LP03_KELLY27_SOURCE_EXACT_READBACK_MISMATCH")
                    observed = _EvidencePublishedSourceReadV1._check_current_v1(self)
                    self.guard("OBSERVE", (adapter._evidence_store_binding_v1.binding.store_id, table, row[0], observed))
            finally:
                sqlite3.Connection.close(reader)
                self.read_target = None
        observed = _EvidencePublishedSourceReadV1._check_current_v1(self)
        self.guard("COMPLETE", observed)


class _EvidenceOwnerPacketCustodyV1:
    """Existing registry's original synthetic policy and packet identities."""

    __slots__ = ("registry", "host", "packets", "rights_by_id", "generation", "withdrawn",
                 "lock", "owner_context", "wall_ns", "metadata_byte_sizes", "projection_sizes", "native_freeze_originals",
                 "published_kelly27", "published_edge_latency", "multiple_testing_ledger")

    def __init__(self, registry, host, rights):
        from _thread import RLock
        from time import time_ns
        from types import BuiltinFunctionType
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceConformanceSourceRightsV1, EvidenceOriginV1, EvidenceAbsenceV1

        _native_require(type(host) is EvidenceHostBindingV1
                        and host.public_configuration.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE,
                        "LP03_CONFORMANCE_SOURCE_HOST_REQUIRED")
        EvidenceHostBindingV1._assert_local_binding_v1(host)
        _native_require(type(time_ns) is BuiltinFunctionType, "LP03_NATIVE_SOURCE_CLOCK_REQUIRED")
        _native_require(type(rights) is tuple and 0 < len(rights) <= 256
                        and all(type(item) is EvidenceConformanceSourceRightsV1 for item in rights),
                        "LP03_ORIGINAL_RIGHTS_ROSTER")
        _native_require(len({item.rights_ref for item in rights}) == len(rights)
                        and all(item.generation == host.public_configuration.generation for item in rights),
                        "LP03_ORIGINAL_RIGHTS_GENERATION")
        packets = registry._packets
        _native_require(0 < len(packets) <= 4096 and all(type(p) is OwnerValuePacketV1 for p in packets),
                        "LP03_ORIGINAL_PACKET_ROSTER")
        self.multiple_testing_ledger = _require_evidence_trial_ledger_registry_v1(registry)
        published = getattr(registry, "_evidence_published_kelly27_v1", None)
        produced = any("LP03_FIVAB::full_kelly_fraction::MATH-28" in packet.authorized_binding_ids
                       or packet.packet_type == "LP03PublishedKellySourceV1" for packet in packets)
        _native_require((published is None and not produced) or
            (type(published) is _EvidencePublishedKelly27V1 and published.materialization == "MATERIALIZED"
             and published.materialized[0] is registry and len(packets) == 1 and published.materialized[1] is packets[0]
             and published.prepared[0].platform._host is host), "LP03_KELLY27_ORIGINAL_PUBLISHED_SOURCE_REQUIRED")
        if published is not None:
            _EvidencePublishedKelly27V1._assert_original_v1(published, completed=True, canonical=True)
        self.published_kelly27 = published
        measured = getattr(registry, "_evidence_published_edge_latency_v1", None)
        binds_measured_role = any(binding in ("LP03_FIVAB::edge_now::MATH-41", "LP03_FIVAB::latency::MATH-41")
            for packet in packets for binding in packet.authorized_binding_ids)
        _native_require((measured is None and not binds_measured_role) or
            (published is None and binds_measured_role and type(measured) is _EvidencePublishedEdgeLatencyV1
             and measured.materialized[0] is registry and measured.materialized[1] is packets
             and measured.prepared[0].platform._host is host),
            "LP03_MEASURED_EDGE_ORIGINAL_PUBLISHED_SOURCE_REQUIRED")
        if measured is not None:
            _EvidencePublishedEdgeLatencyV1._assert_original_v1(measured, completed=True, canonical=True)
        self.published_edge_latency = measured
        published = _EvidenceOwnerPacketCustodyV1._published_source_v1(self)
        # Validate native identities before packet IDs/bindings are hashed or
        # used by the original registry/source-policy association below.
        for packet in packets:
            _validate_evidence_packet_original_v1(packet, ())
        _EvidenceOwnerPacketCustodyV1._deny_public_originals_v1(registry, packets)
        original_by_id = {p.packet_id: p for p in packets}
        covered = set()
        projection_sizes = {}
        for policy in rights:
            EvidenceConformanceSourceRightsV1.__post_init__(policy)
            selection = policy.source_selection
            _native_require(type(selection.profile_scope) is EvidenceAbsenceV1
                            and type(selection.account_scope) is EvidenceAbsenceV1,
                            "LP03_CONFORMANCE_PROFILE_ACCOUNT_METADATA_UNAVAILABLE")
            for ref, clocks in policy.native_clock_companions:
                packet = original_by_id.get(ref)
                _native_require(packet is not None and packet.owner_id == selection.original_owner_id
                                and packet.packet_type in selection.permitted_record_kinds
                                and packet.input_version == policy.source_version,
                                "LP03_ORIGINAL_PACKET_POLICY_JOIN")
                _native_require(type(selection.market_scope) is tuple
                                and packet.scope.market_scope_id in selection.market_scope
                                and type(selection.instrument_scope) is tuple
                                and packet.scope.instrument_or_contract_scope_id in selection.instrument_scope,
                                "LP03_ORIGINAL_PACKET_SCOPE_JOIN")
                if measured is not None:
                    _native_require(clocks == measured.prepared[4],
                                    "LP03_MEASURED_EDGE_EXACT_NATIVE_CLOCK_COMPANION")
                for name, ns in clocks:
                    _native_require(_native_utc_nanoseconds(getattr(packet.clocks, name).isoformat()) == ns // 1000 * 1000,
                                    "LP03_ORIGINAL_PACKET_NATIVE_CLOCK_JOIN")
                # Original synthetic data registration, before any request:
                # validate immutable native leaves and retain exact size facts,
                # never a whole-store read cache. Bootstrap uses only these
                # metadata facts and never serializes packet values.
                from .serialization import deterministic_json, _evidence_canonical_object_v1
                _validate_evidence_packet_original_v1(packet, selection.allowed_fields)
                _native_require(all(name in packet.values for name in selection.allowed_fields),
                                "LP03_SOURCE_REQUIRED_FIELD_MISSING")
                visibility = None if published is None else published.materialized[2]
                base = _evidence_packet_projection_body_v1(packet, (), clocks, policy.origin, published_visibility=visibility,
                    trial_ledger_visibility=None if self.multiple_testing_ledger is None else self.multiple_testing_ledger[2][3])
                full = _evidence_packet_projection_body_v1(packet, selection.allowed_fields, clocks, policy.origin,
                    published_visibility=visibility,
                    trial_ledger_visibility=None if self.multiple_testing_ledger is None else self.multiple_testing_ledger[2][3])
                from decimal import localcontext
                from .context import decimal_context_v1
                with localcontext(decimal_context_v1()):
                    base_bytes = len(deterministic_json(base).encode("utf-8"))
                    field_bytes = {name: len(deterministic_json({name: full["values"][name]}).encode("utf-8")) - 2
                                   for name in selection.allowed_fields}
                    original_wire = deterministic_json(full).encode("utf-8")
                _evidence_canonical_object_v1(original_wire, max_bytes=1048576)
                _native_require(len(original_wire) == base_bytes + sum(field_bytes.values()) + len(field_bytes) - 1,
                                "LP03_ORIGINAL_PROJECTION_SIZE_JOIN")
                projection_sizes[(policy.rights_ref, ref)] = (base_bytes, MappingProxyType(field_bytes))
                covered.add(ref)
        _native_require(covered == set(original_by_id), "LP03_ORIGINAL_PACKET_POLICY_CLOSURE")
        self.registry, self.host, self.packets = registry, host, packets
        self.native_freeze_originals = tuple((packet, packet._evidence_native_freeze_v1) for packet in packets)
        self.rights_by_id = MappingProxyType({item.rights_ref: item for item in rights})
        from .serialization import deterministic_json
        sizes = {item.rights_ref: len(deterministic_json(item).encode("utf-8")) for item in rights}
        _native_require(all(size <= 65536 for size in sizes.values()), "LP03_ORIGINAL_RIGHTS_BYTE_BOUND")
        self.metadata_byte_sizes = MappingProxyType(sizes)
        self.projection_sizes = MappingProxyType(projection_sizes)
        self.generation = host.public_configuration.generation
        self.withdrawn = set()
        # Kelly retains its original shared upstream lock. The measured-edge
        # registry also retains each original upstream lock at operation entry.
        self.lock = RLock() if self.published_kelly27 is None else self.published_kelly27.prepared[6][0][0].lock
        self.wall_ns = time_ns
        self.owner_context = EvidenceSourceOwnerContextV1(self)

    def __copy__(self):
        raise TypeError("LP03 source custody cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 source custody cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 source custody cannot be serialized")

    def _assert_original_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1

        if type(self) is _EvidenceOwnerPacketCustodyV1 and self.multiple_testing_ledger is not None:
            # This original ledger pins native registry maps before the shared
            # custody walk performs any registry lookup.
            _native_require(_require_evidence_trial_ledger_registry_v1(self.registry, expected=self.multiple_testing_ledger)
                            is self.multiple_testing_ledger, "LP03_TRIAL_LEDGER_ORIGINAL_CHANGED")
        _native_require(type(self) is _EvidenceOwnerPacketCustodyV1
                        and getattr(self.registry, "_evidence_source_custody_v1", None) is self
                        and self.registry._packets is self.packets
                        and type(self.native_freeze_originals) is tuple and len(self.native_freeze_originals) == len(self.packets)
                        and all(original is packet and getattr(packet, "_evidence_native_freeze_v1", None) is proof
                                and proof[0] is packet and packet.values is proof[1]
                                for packet, (original, proof) in zip(self.packets, self.native_freeze_originals, strict=True))
                        and all(self.registry._by_id.get(p.packet_id) is p for p in self.packets),
                        "LP03_ORIGINAL_SOURCE_CUSTODY_LOST")
        EvidenceHostBindingV1._assert_local_binding_v1(self.host)
        if self.multiple_testing_ledger is None:
            _native_require(_require_evidence_trial_ledger_registry_v1(self.registry) is None,
                            "LP03_TRIAL_LEDGER_ORIGINAL_CHANGED")
        _EvidenceOwnerPacketCustodyV1._deny_public_originals_v1(self.registry, self.packets)
        published = self.published_kelly27
        _native_require(getattr(self.registry, "_evidence_published_kelly27_v1", None) is published,
                        "LP03_KELLY27_SOURCE_REGISTRY_CHANGED")
        if published is not None:
            _native_require(published.materialized[0] is self.registry and published.materialized[1] is self.packets[0],
                            "LP03_KELLY27_SOURCE_REGISTRY_CHANGED")
            _EvidencePublishedKelly27V1._assert_original_v1(published, completed=True)
        measured = self.published_edge_latency
        _native_require(getattr(self.registry, "_evidence_published_edge_latency_v1", None) is measured,
                        "LP03_MEASURED_EDGE_SOURCE_REGISTRY_CHANGED")
        if measured is not None:
            _native_require(measured.materialized[0] is self.registry and measured.materialized[1] is self.packets,
                            "LP03_MEASURED_EDGE_SOURCE_REGISTRY_CHANGED")
            _EvidencePublishedEdgeLatencyV1._assert_original_v1(measured, completed=True)

    def _published_source_v1(self):
        return self.published_kelly27 or self.published_edge_latency

    @staticmethod
    def _original_operation_locks_v1(custodies):
        """Return the complete original source lock set in one identity order."""
        locks = {}
        for custody in custodies:
            _native_require(type(custody) is _EvidenceOwnerPacketCustodyV1, "LP03_ORIGINAL_SOURCE_LOCK_ROSTER")
            lock = custody.lock
            locks[id(lock)] = lock
            measured = custody.published_edge_latency
            if measured is not None:
                _EvidencePublishedEdgeLatencyV1._assert_original_v1(measured, completed=True)
                for upstream, _selection, _rights in measured.prepared[6]:
                    _native_require(type(upstream) is _EvidenceOwnerPacketCustodyV1
                        and upstream.published_edge_latency is None, "LP03_ORIGINAL_SOURCE_LOCK_ROSTER")
                    lock = upstream.lock
                    locks[id(lock)] = lock
        return tuple(locks[key] for key in sorted(locks))

    @staticmethod
    def _deny_public_originals_v1(registry, packets):
        # Direct synthetic composition cannot replace an existing LP02 fence
        # with a new synthetic policy, even through a same-context packet copy.
        _native_require(id(registry) not in _PUBLIC_OWNER_REGISTRIES_V1,
                        "LP03_PUBLIC_ORIGINAL_REQUIRES_EXISTING_CUSTODY")
        for packet in packets:
            keys = tuple(CanonicalOwnerPacketRegistryV1._packet_binding_key(packet, binding)
                         for binding in packet.authorized_binding_ids)
            _native_require(packet.packet_id not in _PUBLIC_OWNER_PACKET_ORIGINS_V1
                            and id(packet) not in _PUBLIC_DERIVED_PACKET_CUSTODY_V1
                            and keys[0][:-1] not in _PUBLIC_NATIVE_CONTEXTS_V1
                            and all(key not in _PUBLIC_NATIVE_CONTEXT_BINDINGS_V1 for key in keys),
                            "LP03_PUBLIC_ORIGINAL_REQUIRES_EXISTING_CUSTODY")

    def _assembly_metadata_v1(self, scope, *, operation=None):
        """Called under the retained owner lock; never traverses packet values."""
        from .source_policy import _intersect_conformance_assembly_rights_v1

        _native_require(self.lock._is_owned(), "LP03_ORIGINAL_SOURCE_LOCK_REQUIRED")
        _EvidenceOwnerPacketCustodyV1._assert_original_v1(self)
        if operation is not None:
            from .persistence import _EvidenceControlBootstrapV1
            _native_require(type(operation) is _EvidenceControlBootstrapV1
                            and operation.issuer.operation is operation
                            and any(self is item for item in operation.issuer.source_custodies)
                            and operation.envelope_entry[3].assembly_scope is scope,
                            "LP03_ORIGINAL_METADATA_OPERATION_REQUIRED")
        if self.multiple_testing_ledger is not None:
            _require_evidence_trial_ledger_registry_v1(self.registry, expected=self.multiple_testing_ledger, scope=scope)
        if self.published_kelly27 is not None:
            _native_require(operation is not None and operation.envelope_entry[3].component_closure == ("MATH-28",),
                            "LP03_KELLY27_FRESH_CONSUMER_SCOPE_REQUIRED")
            _EvidencePublishedKelly27V1._assert_scope_v1(self.published_kelly27, scope, observed_wall_ns=self.wall_ns())
        if self.published_edge_latency is not None:
            _native_require(operation is not None and operation.envelope_entry[3].component_closure == ("MATH-41",),
                            "LP03_MEASURED_EDGE_CONSUMER_SCOPE_REQUIRED")
            _EvidencePublishedEdgeLatencyV1._assert_scope_v1(self.published_edge_latency, scope, observed_wall_ns=self.wall_ns())
        result = []
        for selection in scope.source_selections:
            policies = []
            for ref in selection.required_original_rights_refs:
                policy = self.rights_by_id.get(ref)
                if operation is not None and policy is not None:
                    _EvidenceControlBootstrapV1._charge_v1(operation, record_reads=1, query_result_records=1,
                                                         read_bytes=self.metadata_byte_sizes[ref])
                policies.append(policy)
            # A registry contributes only its exact owner/store selections.
            if all(policy is None for policy in policies):
                continue
            _native_require(all(policy is not None for policy in policies), "LP03_ORIGINAL_RIGHTS_INCOMPLETE")
            for policy in policies:
                _native_require(policy.rights_ref not in self.withdrawn and policy.generation == self.generation,
                                "LP03_ORIGINAL_RIGHTS_WITHDRAWN_OR_STALE")
                result.append(_intersect_conformance_assembly_rights_v1(
                    policy, selection, scope=scope, observed_wall_ns=self.wall_ns()))
        return tuple(result)

    def _read_assembly_slice_v1(self, operation, selection):
        """Read selected original fields; the issuer withholds return until audit."""
        from .persistence import _EvidenceControlBootstrapV1
        _native_require(type(operation) is _EvidenceControlBootstrapV1, "LP03_ORIGINAL_SOURCE_READ_OPERATION")
        return _EvidenceOwnerPacketCustodyV1._read_admitted_slice_v1(self, operation, selection)

    def _read_registration_policy_v1(self, operation, selection):
        """Only the already selected claim/protocol policy, under fresh rights."""
        from .persistence import _EvidenceRegistrationOperationV1
        _native_require(type(operation) is _EvidenceRegistrationOperationV1
                        and operation.commit_state == "PARENT_READBACK_CONFIRMED"
                        and operation.parent_readback_observation is not None
                        and (selection.original_owner_id, selection.permitted_record_kinds) in (
                            ("QKU_COMPUTATION_CONTROL_PLANE", ("EvidenceClaimPolicyV1",)),
                            ("ComputationParameterPolicyV1", ("EvidenceProtocolParametersV1",))),
                        "LP03_REGISTRATION_POLICY_SOURCE_SCOPE")
        return _EvidenceOwnerPacketCustodyV1._read_admitted_slice_v1(self, operation, selection)

    def _read_lane_slice_v1(self, operation, selection):
        from .persistence import _EvidenceRegistrationOperationV1, _EvidenceAttemptOperationV1
        _native_require(type(operation) is _EvidenceRegistrationOperationV1
                        and type(operation.active_attempt) is _EvidenceAttemptOperationV1
                        and operation.active_attempt.invocation_state == "READING_ORIGINAL_INPUTS"
                        and any(selection is item for item in operation.active_attempt.allowed_reads),
                        "LP03_LANE_ORIGINAL_SOURCE_SCOPE")
        return _EvidenceOwnerPacketCustodyV1._read_admitted_slice_v1(self, operation, selection)

    def _read_admitted_slice_v1(self, operation, selection):
        """One bounded native acquisition body for closed original read purposes."""
        from .models import EvidenceAbsenceV1, EvidenceExactSelectionV1, EvidenceRecordRefV1, EvidenceSourceSliceV1
        from .persistence import _EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1, _EvidenceReviewOperationV1
        from .serialization import deterministic_json, _evidence_canonical_object_v1

        operation_owner = type(operation)
        _native_require(operation_owner in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1, _EvidenceReviewOperationV1)
                        and operation.issuer.operation is (operation.registration if operation_owner is _EvidenceReviewOperationV1 else operation)
                        and any(self is item for item in operation.issuer.source_custodies)
                        and self.lock._is_owned() and type(selection.selection) is EvidenceExactSelectionV1,
                        "LP03_ORIGINAL_SOURCE_READ_OPERATION")
        if operation_owner is _EvidenceRegistrationOperationV1:
            if operation.active_attempt is None:
                _native_require(operation.commit_state == "PARENT_READBACK_CONFIRMED"
                                and operation.parent_readback_observation is not None
                                and (selection.original_owner_id, selection.permitted_record_kinds) in (
                                    ("QKU_COMPUTATION_CONTROL_PLANE", ("EvidenceClaimPolicyV1",)),
                                    ("ComputationParameterPolicyV1", ("EvidenceProtocolParametersV1",))),
                                "LP03_REGISTRATION_POLICY_SOURCE_SCOPE")
            else:
                from .persistence import _EvidenceAttemptOperationV1
                attempt = operation.active_attempt
                _native_require(type(attempt) is _EvidenceAttemptOperationV1 and attempt.phase == "COMMITTED_AND_READBACK"
                                and attempt.invocation_state == "READING_ORIGINAL_INPUTS"
                                and any(selection is item for item in attempt.allowed_reads), "LP03_LANE_ORIGINAL_SOURCE_SCOPE")
        if operation_owner is _EvidenceReviewOperationV1:
            baseline_ref = operation.registration.preparation.input_assembly_members[2].portfolio_and_cash_context[
                "permanent_no_trade_baseline_ref"]
            _native_require(operation.registration.active_review_operation is operation
                            and operation.phase == "PARENTS_READBACK" and operation.admission_readback_original is not None
                            and operation.baseline_original is None
                            and selection.permitted_record_kinds == ("EvidenceSyntheticBaselineV1",)
                            and selection.selection.record_refs == (baseline_ref,) and selection.allowed_fields == ("baseline",),
                            "LP03_REVIEW_ORIGINAL_BASELINE_SCOPE")
        scope = (operation.registration if operation_owner is _EvidenceReviewOperationV1 else operation).envelope_entry[3].assembly_scope
        _native_require(any(selection is item for item in scope.source_selections), "LP03_SOURCE_SELECTION_NOT_ORIGINAL")
        acquisition_prefix, acquisition_minted = _require_evidence_source_acquisition_prefix_v1(operation)
        _EvidenceOwnerPacketCustodyV1._assert_original_v1(self)
        if self.multiple_testing_ledger is not None:
            _require_evidence_trial_ledger_registry_v1(self.registry, expected=self.multiple_testing_ledger, scope=scope)
        # A per-read identity index of the independently retained original
        # carriers avoids rescanning all packets for every selected record.
        # This is bounded metadata, not reconstructed values or a rights cache.
        original_freezes = {id(packet): proof for packet, proof in self.native_freeze_originals}
        byte_bounds = {}
        for ref in selection.selection.record_refs:
            sizes = tuple(self.projection_sizes.get((right, ref)) for right in selection.required_original_rights_refs)
            _native_require(len(sizes) == 1 and sizes[0] is not None, "LP03_ORIGINAL_SOURCE_SIZE_UNAVAILABLE")
            base, values = sizes[0]
            _native_require(all(name in values for name in selection.allowed_fields), "LP03_SOURCE_FIELD_OUTSIDE_ORIGINAL_POLICY")
            byte_bounds[ref] = base + sum(values[name] for name in selection.allowed_fields) + len(selection.allowed_fields) - 1
        operation_owner._room_v1(operation, owner_queries=1,
            record_reads=len(selection.selection.record_refs), query_result_records=len(selection.selection.record_refs),
            read_bytes=sum(byte_bounds.values()))
        operation_owner._check_current_v1(operation)
        operation_owner._charge_v1(operation, owner_queries=1)
        produced_read = None
        published = _EvidenceOwnerPacketCustodyV1._published_source_v1(self)
        if published is not None:
            produced_read = _EvidencePublishedSourceReadV1(operation, self, selection)
            _EvidencePublishedSourceReadV1._read_v1(produced_read)
        events, companions = [], []
        for ref in selection.selection.record_refs:
            operation_owner._room_v1(operation, record_reads=1, query_result_records=1, read_bytes=byte_bounds[ref])
            operation_owner._check_current_v1(operation)
            packet = self.registry._by_id.get(ref)
            _native_require(packet is not None and packet.owner_id == selection.original_owner_id
                            and packet.packet_type in selection.permitted_record_kinds
                            and (packet.schema_id, packet.schema_version) in scope.input_schema_and_version_pins,
                            "LP03_ORIGINAL_SOURCE_RECORD_SCHEMA_JOIN")
            operation_owner._charge_v1(operation, record_reads=1, query_result_records=1)
            _native_require(packet.source_conflict is False, "LP03_ORIGINAL_SOURCE_CONFLICT")
            original_freeze = original_freezes.get(id(packet))
            _native_require(original_freeze is not None
                            and getattr(packet, "_evidence_native_freeze_v1", None) is original_freeze
                            and packet.values is original_freeze[1], "LP03_ORIGINAL_SOURCE_CUSTODY_LOST")
            _native_require(all(name in packet.values for name in selection.allowed_fields), "LP03_SOURCE_REQUIRED_FIELD_MISSING")
            original_clocks = tuple(row for rights_ref in selection.required_original_rights_refs
                for row in self.rights_by_id[rights_ref].native_clock_companions if row[0] == ref)
            _native_require(len(original_clocks) == 1, "LP03_ORIGINAL_SOURCE_CLOCK_AMBIGUITY")
            prior = packet.prior_revision_available_time
            if prior is None:
                prior_ns = EvidenceAbsenceV1("NO_PRIOR_REVISION_CLOCK")
            else:
                _native_require(type(prior) is str, "LP03_ORIGINAL_PRIOR_REVISION_CLOCK_UNAVAILABLE")
                prior_ns = _native_utc_nanoseconds(prior)
                _native_require(prior_ns <= scope.snapshot_pit_cutoff_wall_ns,
                                "LP03_PRIOR_REVISION_NOT_KNOWN_AT_CUTOFF")
            body = _evidence_packet_projection_body_v1(packet, selection.allowed_fields, original_clocks[0][1], scope.origin,
                published_visibility=None if published is None else published.materialized[2],
                trial_ledger_visibility=None if self.multiple_testing_ledger is None else self.multiple_testing_ledger[2][3])
            from decimal import localcontext
            from .context import decimal_context_v1
            with localcontext(decimal_context_v1()):
                raw = deterministic_json(body).encode("utf-8")
            operation_owner._charge_v1(operation, read_bytes=len(raw))
            _native_require(len(raw) == byte_bounds[ref], "LP03_ORIGINAL_SOURCE_PROJECTION_CHANGED")
            # Bounded canonical data reconstruction strips no provenance and
            # grants no new native/public object custody to the returned view.
            events.append(_evidence_canonical_object_v1(raw, max_bytes=1048576))
            companions.append(original_clocks[0])
            operation_owner._check_current_v1(operation)
        access, _, _ = operation_owner._check_current_v1(operation)
        _native_require(operation.source_slice_originals is acquisition_prefix and operation.source_slice_minted is acquisition_minted,
                        "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
        _require_evidence_source_acquisition_prefix_v1(operation)
        result = EvidenceSourceSliceV1(original_record_refs=tuple(EvidenceRecordRefV1(selection.original_store_id, ref)
                for ref in selection.selection.record_refs), reconstructed_canonical_events=tuple(events),
            original_native_clock_companions=tuple(companions), access_wall_ns=access, origin=scope.origin,
            rights_refs=selection.required_original_rights_refs, revision_limitations=("SOFTWARE_CONFORMANCE_SOURCE_ONLY",))
        if produced_read is not None:
            _native_require(produced_read.phase == "READBACK_CONFIRMED" and produced_read.completed is not None,
                            "LP03_KELLY27_SOURCE_READBACK_REQUIRED")
            produced_read.guard("RESULT", result)
        # Mint custody at the original acquisition boundary, before the next
        # native observation. A later view cannot adopt changed metadata by
        # creating its own canonical copy of this detached source slice.
        subject = operation.active_attempt if operation_owner is _EvidenceRegistrationOperationV1 and operation.active_attempt is not None else operation
        accounting = operation.registration if operation_owner is _EvidenceReviewOperationV1 else operation
        prefix, minted = _require_evidence_source_acquisition_prefix_v1(operation)
        _native_require(len(prefix) < accounting.consumed["record_reads"],
                        "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_BOUND")
        # Even witness construction failure retains the actual acquired slice;
        # this pending entry can never satisfy a successful-return consumer.
        pending_entry = (subject, self, selection, result, None, None)
        pending = operation.source_slice_guard("PENDING", pending_entry)
        aggregate_limit = (operation.grant_record.reserved_preparation_limits.max_read_bytes
                      if operation_owner is _EvidenceControlBootstrapV1 else accounting.envelope_entry[3].aggregate_execution_limits.max_input_bytes)
        aggregate_prefix = prefix
        if operation_owner is _EvidenceReviewOperationV1:
            _require_evidence_source_acquisition_prefix_v1(accounting)
            aggregate_prefix = (*accounting.source_slice_originals, *prefix)
        elif operation_owner is _EvidenceRegistrationOperationV1 and accounting.review_operation is not None:
            _require_evidence_source_acquisition_prefix_v1(accounting.review_operation)
            aggregate_prefix = (*prefix, *accounting.review_operation.source_slice_originals)
        byte_limit = aggregate_limit
        if subject is not operation:
            byte_limit = min(byte_limit, subject.payload.budgets.max_input_bytes)
        elif operation_owner is _EvidenceReviewOperationV1:
            byte_limit = min(byte_limit, operation.limits["maximum_input_bytes"])
        _native_require(all(type(entry) is tuple and len(entry) == 6 and type(entry[5]) is bytes for entry in aggregate_prefix),
                        "LP03_ORIGINAL_SOURCE_SLICE_WITNESS_CAPACITY")
        remaining = min(1048576, byte_limit - sum(len(entry[5]) for entry in prefix if entry[0] is subject),
                        aggregate_limit - sum(len(entry[5]) for entry in aggregate_prefix))
        _native_require(remaining > 0, "LP03_ORIGINAL_SOURCE_SLICE_WITNESS_CAPACITY")
        witness = _evidence_native_graph_witness_v1(result, (EvidenceSourceSliceV1, EvidenceRecordRefV1),
                                                     maximum_bytes=remaining, source_only=True)
        canonical = witness[2].encode("utf-8")
        _native_require(operation.source_slice_originals is pending and operation.source_slice_minted is minted,
                        "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
        _require_evidence_source_acquisition_prefix_v1(operation)
        entry = (subject, self, selection, result, witness, canonical)
        retained = operation.source_slice_guard("COMPLETE", pending_entry, entry)
        operation_owner._check_current_v1(operation)
        _native_require(operation.source_slice_originals is retained and operation.source_slice_minted is minted
                        and (operation.active_attempt if operation_owner is _EvidenceRegistrationOperationV1
                             and operation.active_attempt is not None else operation) is subject,
                        "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
        _require_evidence_source_acquisition_prefix_v1(operation)
        for original in retained:
            _require_evidence_resolution_witness_v1(original[3], original[4])
            _native_require(original[4][2].encode("utf-8") == original[5], "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
        return result


def _evidence_source_binary64_binding_v1(*, owner_id, record_kind, schema_id, schema_version,
                                       producer_receipt_type, binding_ids, field_path):
    """Select numeric data shape from existing exact public input metadata.

    This is not source or producer admission. Only the original custody can
    wrap a selected field, and its signed rights/PIT checks still apply.
    Record-valued and private producer inputs require their own reconstruction.
    """
    from .implementation_registry import _LP03_PUBLIC_EVIDENCE_INVOCATION_IDS_V1
    shapes = {"float64": 0, "list[float64]": 1, "list[list[float64]]": 2}
    switch_grid_type = "ordered list[nonnegative or INF]"
    rows = []
    for binding_id in binding_ids:
        binding = FORMULA_INPUT_AUTHORITY_BINDINGS.get(binding_id)
        if binding is None or binding.math_spec_id not in _LP03_PUBLIC_EVIDENCE_INVOCATION_IDS_V1:
            continue
        switch_grid = (binding.math_spec_id, binding.input_name, binding.input_type) == (
            "MATH-25", "tau_grid", switch_grid_type)
        if (binding.exact_field_path == field_path and (binding.input_type in shapes or switch_grid)
                and (owner_id, record_kind, schema_id, schema_version, producer_receipt_type)
                == (binding.accepted_upstream_owner_id, binding.accepted_packet_or_snapshot_type,
                    binding.schema_id, binding.schema_version, binding.producer_receipt_type)):
            rows.append(binding)
    if not rows:
        return None
    _native_require(len(rows) <= 48 and all(row.input_type == rows[0].input_type for row in rows),
                    "LP03_SOURCE_BINARY64_BINDING_AMBIGUITY")
    return tuple(row.binding_id for row in rows), rows[0].input_type, shapes.get(rows[0].input_type)


def _evidence_packet_binary64_binding_v1(packet, name):
    return _evidence_source_binary64_binding_v1(owner_id=packet.owner_id, record_kind=packet.packet_type,
        schema_id=packet.schema_id, schema_version=packet.schema_version, producer_receipt_type=packet.producer_receipt_type,
        binding_ids=packet.authorized_binding_ids, field_path=name)


def _evidence_logged_ope_binding_ids_v1(*, owner_id, record_kind, schema_id, schema_version,
                                        producer_receipt_type, binding_ids, field_path):
    """Select only the original logged-bandit row owner and frozen bindings."""
    if field_path != "logged_rows":
        return ()
    selected = []
    for ref in binding_ids:
        binding = FORMULA_INPUT_AUTHORITY_BINDINGS.get(ref)
        if binding is None or binding.math_spec_id not in ("MATH-22", "MATH-23", "MATH-25"):
            continue
        if (binding.input_name, binding.input_type, binding.exact_field_path) == ("logged_rows", "list[record]", field_path) and (
            owner_id, record_kind, schema_id, schema_version, producer_receipt_type) == (
            binding.accepted_upstream_owner_id, binding.accepted_packet_or_snapshot_type, binding.schema_id,
            binding.schema_version, binding.producer_receipt_type):
            selected.append(ref)
    return tuple(selected)


def _evidence_packet_logged_ope_bindings_v1(packet, name):
    return _evidence_logged_ope_binding_ids_v1(owner_id=packet.owner_id, record_kind=packet.packet_type,
        schema_id=packet.schema_id, schema_version=packet.schema_version, producer_receipt_type=packet.producer_receipt_type,
        binding_ids=packet.authorized_binding_ids, field_path=name)


def _evidence_logged_ope_rows_v1(rows, *, native_owner):
    """Preserve a bounded original row roster, scalar types and binary64 spelling."""
    from math import isfinite
    from .context import _native_ident

    _native_require(type(rows) is (tuple if native_owner else list) and 0 < len(rows) <= 64,
        "LP03_LOGGED_OPE_SOURCE_ROSTER")
    text_fields = ("row_id",)
    integer_fields = ("logged_action_index", "fold_id")
    vector_fields = ("behavior_action_probabilities", "target_action_probabilities",
        "cross_fitted_reward_model_predictions")
    expected = {*text_fields, *integer_fields, *vector_fields, "reward", "cross_fitted_prediction"}
    enclosed, identities = [], set()
    for row in rows:
        _native_require(type(row) is (MappingProxyType if native_owner else dict)
            and set(row) == expected, "LP03_LOGGED_OPE_SOURCE_ROW_FIELDS")
        row_id = row["row_id"]
        _native_require(type(row_id) is str and 0 < len(row_id) <= 128 and row_id not in identities,
            "LP03_LOGGED_OPE_SOURCE_ROW_IDENTITY")
        _native_ident(row_id)
        identities.add(row_id)
        behavior, target, scores = (row[name] for name in vector_fields)
        _native_require(type(behavior) is type(target) is type(scores) is (tuple if native_owner else list)
            and 0 < len(behavior) == len(target) == len(scores) <= 16
            and all(type(value) is float and 0 <= value <= 1 for value in (*behavior, *target))
            and all(type(value) is float and isfinite(value) for value in scores)
            and type(row["reward"]) is float and isfinite(row["reward"]),
            "LP03_LOGGED_OPE_SOURCE_NUMERIC_DOMAIN")
        action, fold = (row[name] for name in integer_fields)
        _native_require(type(action) is type(fold) is int and 0 <= action < len(behavior) and 0 <= fold < 64
            and type(row["cross_fitted_prediction"]) is bool, "LP03_LOGGED_OPE_SOURCE_ACTION_FOLD_STATE")
        enclosed.append(dict(row))
    return enclosed


def _evidence_fold_interval_binding_ids_v1(*, owner_id, record_kind, schema_id, schema_version,
        producer_receipt_type, binding_ids, field_path):
    """Select only the original M20/M21 interval carrier by its full identity."""
    if field_path != "sample_intervals":
        return ()
    selected = []
    for ref in binding_ids:
        binding = FORMULA_INPUT_AUTHORITY_BINDINGS.get(ref)
        if binding is None or binding.math_spec_id not in ("MATH-20","MATH-21"):
            continue
        if (binding.input_name, binding.input_type, binding.exact_field_path) != ("sample_intervals","list[record]",field_path):
            continue
        if (owner_id,record_kind,schema_id,schema_version,producer_receipt_type) == (
                binding.accepted_upstream_owner_id,binding.accepted_packet_or_snapshot_type,
                binding.schema_id,binding.schema_version,binding.producer_receipt_type):
            selected.append(ref)
    return tuple(selected)


def _evidence_packet_fold_interval_binding_ids_v1(packet,name):
    return _evidence_fold_interval_binding_ids_v1(owner_id=packet.owner_id,record_kind=packet.packet_type,
        schema_id=packet.schema_id,schema_version=packet.schema_version,producer_receipt_type=packet.producer_receipt_type,
        binding_ids=packet.authorized_binding_ids,field_path=name)


def _evidence_fold_interval_values_v1(rows, *, native_owner):
    from .context import _native_ident
    container = tuple if native_owner else list
    record = MappingProxyType if native_owner else dict
    _native_require(type(rows) is container and 2 <= len(rows) <= 8, "LP03_FOLD_INTERVAL_COMPLETE_LAYOUT")
    rendered = []
    for row in rows:
        _native_require(type(row) is record and len(row)==3 and all(type(key) is str for key in row)
            and set(row)=={"sample_id","start","end"}, "LP03_FOLD_INTERVAL_FIELDS")
        identifier,start,end=(row[name] for name in ("sample_id","start","end"))
        _native_require(type(identifier) is str and 0 < len(identifier) <= 128
            and type(start) is type(end) is float and math.isfinite(start) and math.isfinite(end)
            and -1_000_000 <= start < end <= 1_000_000, "LP03_FOLD_INTERVAL_NATIVE_VALUES")
        _native_ident(identifier)
        rendered.append(dict(sample_id=identifier,start=start,end=end))
    _native_require(len({row["sample_id"] for row in rendered})==len(rendered),"LP03_FOLD_INTERVAL_DUPLICATE_SAMPLE")
    return tuple(rendered)



def _evidence_switch_tau_grid_v1(value, *, native_owner):
    """Validate the exact threshold order before any owner value is copied."""
    _native_require(type(value) is (tuple if native_owner else list) and 0 < len(value) <= 64,
        "LP03_SWITCH_ORIGINAL_TAU_GRID_ROSTER")
    for entry in value:
        _native_require(
            type(entry) is float and math.isfinite(entry) and entry >= 0
            or type(entry) is int and 0 <= entry < 2**256
            or type(entry) is str and entry == "INF",
            "LP03_SWITCH_ORIGINAL_TAU_GRID_VALUE")
    ordered = tuple(math.inf if entry == "INF" else entry for entry in value)
    _native_require(all(left < right for left, right in zip(ordered, ordered[1:])),
        "LP03_SWITCH_ORIGINAL_TAU_GRID_ORDER")
    return tuple(value)


def _evidence_source_field_wire_v1(packet, name):
    from .serialization import _encode_evidence_projection_json_v1
    descriptor = _evidence_packet_binary64_binding_v1(packet, name)
    value = packet.values[name]
    interval_bindings = _evidence_packet_fold_interval_binding_ids_v1(packet,name)
    if interval_bindings:
        rows=_evidence_fold_interval_values_v1(value,native_owner=True)
        raw=_encode_evidence_projection_json_v1(rows,maximum_bytes=65536,maximum_nodes=4096)
        return dict(encoding="LP03_FOLD_INTERVAL_RECORDS_JSON_V1",binding_ids=interval_bindings,
            input_type="list[record]",value_json=raw.decode("utf-8","strict"))
    logged_bindings = _evidence_packet_logged_ope_bindings_v1(packet, name)
    if logged_bindings:
        rows = _evidence_logged_ope_rows_v1(value, native_owner=True)
        raw = _encode_evidence_projection_json_v1(rows, maximum_bytes=65536, maximum_nodes=4096)
        return dict(encoding="LP03_LOGGED_OPE_ROWS_JSON_V1", binding_ids=logged_bindings,
            input_type="list[record]", value_json=raw.decode("utf-8", "strict"))
    if descriptor is None:
        return value
    if descriptor[2] is None:
        value = _evidence_switch_tau_grid_v1(value, native_owner=True)
    # Original native-container and exact numeric-position validation precedes
    # this conversion. Its bounded numeric-only text cannot hide another JSON
    # object, path, secret-bearing member, Decimal amount or producer receipt.
    raw = _encode_evidence_projection_json_v1(value, maximum_bytes=65536, maximum_nodes=4096)
    return dict(encoding="LP03_BINARY64_FIELD_JSON_V1", binding_ids=descriptor[0],
                input_type=descriptor[1], value_json=raw.decode("ascii", "strict"))


def _evidence_decode_source_values_v1(event):
    """Decode selected numeric leaves of an already original acquired event."""
    from .serialization import _native_strict_json, _encode_evidence_projection_json_v1
    values = {}
    for name, value in event["values"].items():
        intervals=_evidence_fold_interval_binding_ids_v1(owner_id=event["owner_id"],record_kind=event["record_kind"],
            schema_id=event["schema_id"],schema_version=event["schema_version"],producer_receipt_type=event["producer_receipt_type"],
            binding_ids=event["authorized_binding_ids"],field_path=name)
        if intervals:
            _native_require(type(value) is MappingProxyType and set(value)=={"encoding","binding_ids","input_type","value_json"}
                and value["encoding"]=="LP03_FOLD_INTERVAL_RECORDS_JSON_V1" and value["binding_ids"]==intervals
                and value["input_type"]=="list[record]" and type(value["value_json"]) is str
                and 0 < len(value["value_json"]) <= 65536,"LP03_FOLD_INTERVAL_SOURCE_ENCODING")
            raw=value["value_json"].encode("utf-8","strict")
            decoded=_native_strict_json(raw,max_bytes=65536,max_nodes=4096,binary64_numbers=True)
            rows=_evidence_fold_interval_values_v1(decoded,native_owner=False)
            _native_require(_encode_evidence_projection_json_v1(rows,maximum_bytes=65536,maximum_nodes=4096)==raw,
                "LP03_FOLD_INTERVAL_SOURCE_NONCANONICAL")
            values[name]=tuple(MappingProxyType(row) for row in rows)
            continue
        logged = _evidence_logged_ope_binding_ids_v1(owner_id=event["owner_id"], record_kind=event["record_kind"],
            schema_id=event["schema_id"], schema_version=event["schema_version"],
            producer_receipt_type=event["producer_receipt_type"],
            binding_ids=event["authorized_binding_ids"], field_path=name)
        if logged:
            _native_require(type(value) is MappingProxyType and set(value) == {"encoding", "binding_ids", "input_type", "value_json"}
                and (value["encoding"], value["binding_ids"], value["input_type"]) == (
                    "LP03_LOGGED_OPE_ROWS_JSON_V1", logged, "list[record]")
                and type(value["value_json"]) is str and 0 < len(value["value_json"]) <= 65536,
                "LP03_LOGGED_OPE_SOURCE_WIRE")
            raw = value["value_json"].encode("utf-8", "strict")
            rows = _evidence_logged_ope_rows_v1(_native_strict_json(raw,
                max_bytes=65536, max_nodes=4096, binary64_numbers=True), native_owner=False)
            _native_require(_encode_evidence_projection_json_v1(rows, maximum_bytes=65536, maximum_nodes=4096) == raw,
                "LP03_LOGGED_OPE_SOURCE_NONCANONICAL")
            values[name] = tuple(MappingProxyType({key: tuple(item) if type(item) is list else item
                for key, item in row.items()}) for row in rows)
            continue
        descriptor = _evidence_source_binary64_binding_v1(owner_id=event["owner_id"], record_kind=event["record_kind"],
            schema_id=event["schema_id"], schema_version=event["schema_version"],
            producer_receipt_type=event["producer_receipt_type"], binding_ids=event["authorized_binding_ids"], field_path=name)
        if descriptor is None:
            values[name] = value
            continue
        _native_require(type(value) is MappingProxyType and set(value) == {"encoding", "binding_ids", "input_type", "value_json"}
                        and value["encoding"] == "LP03_BINARY64_FIELD_JSON_V1" and value["binding_ids"] == descriptor[0]
                        and value["input_type"] == descriptor[1] and type(value["value_json"]) is str
                        and len(value["value_json"]) <= 65536 and value["value_json"].isascii(),
                        "LP03_SOURCE_BINARY64_ENVELOPE")
        raw = value["value_json"].encode("ascii", "strict")
        decoded = _native_strict_json(raw, max_bytes=65536, max_nodes=4096, binary64_numbers=True)
        def numeric(item, depth):
            if depth:
                _native_require(type(item) is list, "LP03_SOURCE_BINARY64_SHAPE")
                return tuple(numeric(child, depth - 1) for child in item)
            _native_require(type(item) in (int, float) and (item.bit_length() <= 256 if type(item) is int else math.isfinite(item)),
                            "LP03_SOURCE_BINARY64_SHAPE")
            return item
        restored = (_evidence_switch_tau_grid_v1(decoded, native_owner=False)
            if descriptor[2] is None else numeric(decoded, descriptor[2]))
        _native_require(_encode_evidence_projection_json_v1(decoded, maximum_bytes=65536, maximum_nodes=4096) == raw,
                        "LP03_SOURCE_BINARY64_NONCANONICAL")
        values[name] = restored
    return values


def _validate_evidence_packet_original_v1(packet, selected_fields):
    """LP03 registration requires actual immutable native source data leaves."""
    from dataclasses import fields
    from .context import _native_ident, _native_text, _public_counter_v1
    from .serialization import _evidence_native_decimal_json_upper_v1

    _native_require(type(packet) is OwnerValuePacketV1 and type(selected_fields) is tuple
                    and len(selected_fields) <= 4096, "LP03_ORIGINAL_PACKET_NATIVE_TYPE")
    def ident(value):
        _native_require(type(value) is str and len(value) <= 256, "LP03_ORIGINAL_PACKET_ID_BOUND")
        return _native_ident(value)

    for name in ("packet_id", "owner_id", "packet_type", "schema_id", "schema_version", "context_id",
                 "source_epoch_id", "input_version", "producer_receipt_id", "producer_receipt_type"):
        ident(getattr(packet, name))
    _native_require(type(packet.source_state_and_claim_lineage) is str and len(packet.source_state_and_claim_lineage) <= 4096
                    and type(packet.scope) is ComputationScopeV1 and type(packet.clocks) is PointInTimeClocksV1
                    and type(packet.ttl) is timedelta and type(packet.source_conflict) is bool,
                    "LP03_ORIGINAL_PACKET_NATIVE_METADATA")
    _native_text(packet.source_state_and_claim_lineage)
    for field in fields(packet.scope):
        ident(getattr(packet.scope, field.name))
    for field in fields(packet.clocks):
        value = getattr(packet.clocks, field.name)
        _native_require(type(value) is datetime and value.tzinfo is UTC, "LP03_ORIGINAL_PACKET_NATIVE_CLOCK")
    _native_require(type(packet.authorized_binding_ids) is tuple and 0 < len(packet.authorized_binding_ids) <= 4096,
                    "LP03_ORIGINAL_PACKET_BINDINGS")
    for ref in packet.authorized_binding_ids:
        ident(ref)
    for value in (packet.provider_sequence, packet.revision):
        if type(value) is str:
            ident(value)
        elif value is not None:
            _native_require(type(value) is int and value.bit_length() <= 256, "LP03_ORIGINAL_PACKET_COUNTER_BOUND")
            _public_counter_v1(value, allow_zero=True)
    _native_require(packet.prior_revision_available_time is None or type(packet.prior_revision_available_time) is str,
                    "LP03_ORIGINAL_PRIOR_REVISION_CLOCK_UNAVAILABLE")
    if packet.prior_revision_available_time is not None:
        _native_require(len(packet.prior_revision_available_time) <= 256, "LP03_ORIGINAL_PACKET_CLOCK_BOUND")
        _native_utc_nanoseconds(packet.prior_revision_available_time)
    proof = getattr(packet, "_evidence_native_freeze_v1", None)
    _native_require(type(proof) is tuple and len(proof) == 4 and proof[0] is packet
                    and proof[1] is packet.values and proof[3] is True
                    and type(proof[2]) is tuple and 0 < len(proof[2]) <= 4096,
                    "LP03_ORIGINAL_SOURCE_FREEZE_PROVENANCE")
    containers = {}
    for fact in proof[2]:
        _native_require(type(fact) is tuple and len(fact) == 2 and type(fact[1]) is bool
                        and type(fact[0]) in (tuple, MappingProxyType), "LP03_ORIGINAL_SOURCE_FREEZE_PROVENANCE")
        previous = containers.get(id(fact[0]))
        # Empty tuples may share their native singleton identity. A nonnative
        # ingress must not be hidden by a later native occurrence of that tuple.
        containers[id(fact[0])] = fact if previous is None else (fact[0], fact[1] and previous[1])
    def original_container(value):
        fact = containers.get(id(value))
        _native_require(fact is not None and fact[0] is value and fact[1] is True,
                        "LP03_ORIGINAL_SOURCE_FOREIGN_CONTAINER")
    _native_require(type(packet.values) is MappingProxyType, "LP03_ORIGINAL_SOURCE_VALUES_NOT_IMMUTABLE")
    original_container(packet.values)
    _native_require(len(packet.values) <= 4096, "LP03_ORIGINAL_SOURCE_VALUE_BOUND")
    # Bound the entire selected-value serialization before any Decimal text or
    # aggregate JSON graph is made. String escaping is counted exactly.
    # Metadata is separately native/bounded above; its final full-wire1MB check
    # remains mandatory and no positive source result exists before it passes.
    nodes, upper_bytes = 1, 2
    def charge(amount):
        nonlocal upper_bytes
        upper_bytes += amount
        _native_require(upper_bytes <= 1048576, "LP03_ORIGINAL_SOURCE_SERIALIZATION_BOUND")
    def visit(value, depth, binary_depth=None):
        nonlocal nodes
        nodes += 1
        _native_require(nodes <= 4096 and depth <= 16, "LP03_ORIGINAL_SOURCE_VALUE_BOUND")
        if binary_depth is not None:
            _native_require(type(value) is tuple if binary_depth else type(value) in (int, float),
                            "LP03_SOURCE_BINARY64_SHAPE")
        if value is None or type(value) is bool:
            charge(5)
            return
        if type(value) is int:
            _native_require(value.bit_length() <= 256, "LP03_ORIGINAL_SOURCE_INTEGER_BOUND")
            charge(79)
            return
        if type(value) is float:
            _native_require(binary_depth == 0 and math.isfinite(value), "LP03_SOURCE_BINARY64_POSITION_OR_NONFINITE")
            charge(32)
            return
        if type(value) is str:
            _native_require(len(value) <= 65536, "LP03_ORIGINAL_SOURCE_TEXT_BOUND")
            needed = 2
            for char in value:
                point = ord(char)
                _native_require(not 0xD800 <= point <= 0xDFFF, "LP03_ORIGINAL_SOURCE_SURROGATE")
                needed += (2 if char in ('"', '\\', '\b', '\f', '\n', '\r', '\t') else 6 if point < 0x20 else
                           1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4)
                _native_require(needed <= 1048576 - upper_bytes, "LP03_ORIGINAL_SOURCE_SERIALIZATION_BOUND")
            charge(needed)
            return
        if type(value) is Decimal:
            charge(_evidence_native_decimal_json_upper_v1(value, maximum_bytes=1048576 - upper_bytes))
            return
        if type(value) is tuple:
            original_container(value)
            _native_require(len(value) <= 4096 - nodes, "LP03_ORIGINAL_SOURCE_VALUE_BOUND")
            charge(2 + max(0, len(value) - 1))
            for child in value:
                visit(child, depth + 1, None if binary_depth is None else binary_depth - 1)
            return
        if type(value) is MappingProxyType:
            original_container(value)
            _native_require(2 * len(value) <= 4096 - nodes, "LP03_ORIGINAL_SOURCE_VALUE_BOUND")
            charge(2 + 2 * len(value))
            for name, child in value.items():
                ident(name)
                visit(name, depth + 1)
                visit(child, depth + 1)
            return
        _native_require(False, "LP03_SOURCE_VALUE_NOT_IMMUTABLE_NATIVE")
    for name in selected_fields:
        ident(name)
        _native_require(name in packet.values, "LP03_SOURCE_REQUIRED_FIELD_MISSING")
        charge(2)
        visit(name, 0)
        descriptor = _evidence_packet_binary64_binding_v1(packet, name)
        interval_bindings = _evidence_packet_fold_interval_binding_ids_v1(packet,name)
        if interval_bindings:
            original_rows=packet.values[name]
            _native_require(type(original_rows) is tuple and 2 <= len(original_rows) <= 8,"LP03_FOLD_INTERVAL_COMPLETE_LAYOUT")
            original_container(original_rows)
            for original_row in original_rows:
                _native_require(type(original_row) is MappingProxyType,"LP03_FOLD_INTERVAL_FIELDS")
                original_container(original_row)
            rows=_evidence_fold_interval_values_v1(original_rows,native_owner=True)
            nodes += 4 + len(rows)*8
            _native_require(nodes <= 4096,"LP03_ORIGINAL_SOURCE_VALUE_BOUND")
            for row in rows:
                visit(row["sample_id"],1)
                visit(row["start"],1,0)
                visit(row["end"],1,0)
            charge(1024 + sum(12*len(row["sample_id"])+256 for row in rows))
            continue
        logged = _evidence_packet_logged_ope_bindings_v1(packet, name)
        if logged:
            from .serialization import _encode_evidence_projection_json_v1
            original_rows = packet.values[name]
            _native_require(type(original_rows) is tuple and 0 < len(original_rows) <= 64,
                "LP03_LOGGED_OPE_SOURCE_ROSTER")
            original_container(original_rows)
            for row in original_rows:
                _native_require(type(row) is MappingProxyType, "LP03_LOGGED_OPE_SOURCE_ROW_FIELDS")
                original_container(row)
                for child in row.values():
                    if type(child) is tuple:
                        original_container(child)
            rows = _evidence_logged_ope_rows_v1(original_rows, native_owner=True)
            raw = _encode_evidence_projection_json_v1(rows, maximum_bytes=65536, maximum_nodes=4096)
            nodes += 14 + 2 * len(logged)
            _native_require(nodes <= 4096, "LP03_ORIGINAL_SOURCE_VALUE_BOUND")
            charge(512 + 6 * len(raw) + sum(6 * len(ref) + 3 for ref in logged))
            continue
        original_value = packet.values[name]
        if descriptor is not None and descriptor[2] is None:
            _evidence_switch_tau_grid_v1(original_value, native_owner=True)
            original_container(original_value)
            nodes += 1
            charge(2 + max(0, len(original_value) - 1))
            for threshold in original_value:
                visit(threshold, 1, None if type(threshold) is str else 0)
                if type(threshold) is str:
                    charge(2)
        else:
            visit(original_value, 0, None if descriptor is None else descriptor[2])
        if descriptor is not None:
            # Bound the exact typed JSON envelope and original field selection. Bound the complete
            # Account for the field/type/binding strings before constructing
            # either its inner text or the outer projection serialization.
            nodes += 12 + 2 * len(descriptor[0])
            _native_require(nodes <= 4096, "LP03_ORIGINAL_SOURCE_VALUE_BOUND")
            charge(512 + sum(6 * len(ref) + 3 for ref in descriptor[0]))


def _evidence_packet_projection_body_v1(packet, selected_fields, original_clocks, origin, *, published_visibility=None, trial_ledger_visibility=None):
    from dataclasses import fields
    from .models import EvidenceAbsenceV1

    prior = packet.prior_revision_available_time
    _native_require(prior is None or type(prior) is str, "LP03_ORIGINAL_PRIOR_REVISION_CLOCK_UNAVAILABLE")
    prior_ns = EvidenceAbsenceV1("NO_PRIOR_REVISION_CLOCK") if prior is None else _native_utc_nanoseconds(prior)
    delta = packet.ttl
    values = {name: _evidence_source_field_wire_v1(packet, name) for name in selected_fields}
    if trial_ledger_visibility is not None:
        _native_require(packet.packet_type in ("MultipleTestingCandidatePValueLedgerV1", "PointInTimeLossDifferentialMatrixV1", "SharpeMomentAndTrialUniverseSnapshotV1", "PointInTimeStrategyPerformanceMatrixV1")
                        and type(trial_ledger_visibility) is int and trial_ledger_visibility > 0,
                        "LP03_TRIAL_LEDGER_NATIVE_VISIBILITY_REQUIRED")
        if "material_trial_ledger" in values:
            values["material_trial_ledger"] = dict(values["material_trial_ledger"],
                publication_visibility_wall_ns=trial_ledger_visibility)
    if published_visibility is not None:
        _native_require(type(published_visibility) is tuple and len(published_visibility) == 3
                        and all(type(value) is int and value >= 0 for value in published_visibility),
                        "LP03_KELLY27_SOURCE_VISIBILITY_WITNESS")
        if packet.packet_type == "LP03PublishedKellySourceV1":
            if "published_source_context" in values:
                values["published_source_context"] = dict(values["published_source_context"],
                    bridge_visibility_observation=published_visibility)
        else:
            _native_require(packet.packet_type == "LP03OriginalBinary64ExecutionInputSourceV1"
                            and packet.owner_id == "QKU_COMPUTATION_CONTROL_PLANE.MATH-02"
                            and packet.schema_id == "LP03::MATH-41::ORIGINAL_INPUT_SOURCE_V1",
                            "LP03_MEASURED_EDGE_SOURCE_VISIBILITY_WITNESS")
            if "original_execution_context" in values:
                selected = values["original_execution_context"]
                values["original_execution_context"] = dict(selected, original_fact=dict(selected["original_fact"],
                    bridge_visibility_observation=published_visibility))
    return dict(representation="OWNER_PACKET_V1", origin=origin.value,
        record_ref=packet.packet_id, owner_id=packet.owner_id, record_kind=packet.packet_type,
        schema_id=packet.schema_id, schema_version=packet.schema_version, context_id=packet.context_id,
        scope={field.name: getattr(packet.scope, field.name) for field in fields(packet.scope)},
        source_epoch_id=packet.source_epoch_id, input_version=packet.input_version,
        native_clocks=dict(original_clocks), ttl_ns=(delta.days * 86400 + delta.seconds) * 1_000_000_000
            + delta.microseconds * 1000,
        values=values,
        authorized_binding_ids=packet.authorized_binding_ids, producer_receipt_id=packet.producer_receipt_id,
        producer_receipt_type=packet.producer_receipt_type, source_state_and_claim_lineage=packet.source_state_and_claim_lineage,
        provider_sequence=(EvidenceAbsenceV1("PROVIDER_SEQUENCE_UNAVAILABLE") if packet.provider_sequence is None else packet.provider_sequence),
        revision=(EvidenceAbsenceV1("SOURCE_REVISION_UNAVAILABLE") if packet.revision is None else packet.revision),
        prior_revision_available_wall_ns_or_absence=prior_ns, source_conflict=packet.source_conflict)


class _EvidenceAssemblyPacketViewV1:
    """Finite decoded original slices for the sole existing admission body."""

    __slots__ = ("operation", "packets", "_original_members", "_source_originals")

    def __init__(self, operation, slices):
        from .persistence import _EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1
        owner = type(operation)
        _native_require(owner in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1)
                        and operation.issuer.operation is operation, "LP03_ORIGINAL_INPUT_VIEW_OWNER")
        original_slices = (operation.acquired_slices if owner is _EvidenceControlBootstrapV1 else
                           operation.active_attempt.source_slices if operation.active_attempt is not None else ())
        _native_require(all(any(part is acquired for acquired in original_slices) for part in slices),
                        "LP03_ASSEMBLY_VIEW_ORIGINAL_SLICES_REQUIRED")
        self._source_originals = _require_evidence_source_slice_roster_v1(operation, slices)
        owner._check_current_v1(operation)
        _require_evidence_source_slice_roster_v1(operation, slices, originals=self._source_originals)
        packets = []
        def projected(ns):
            seconds, remainder = divmod(ns, 1_000_000_000)
            return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds, microseconds=remainder // 1000)
        for part in slices:
            for event in part.reconstructed_canonical_events:
                prior = event["prior_revision_available_wall_ns_or_absence"]
                # The assembly already validated original integer nanoseconds;
                # these UTC projections feed the unchanged legacy checks.
                packets.append(OwnerValuePacketV1(packet_id=event["record_ref"], owner_id=event["owner_id"],
                    packet_type=event["record_kind"], schema_id=event["schema_id"], schema_version=event["schema_version"],
                    context_id=event["context_id"], scope=ComputationScopeV1(**dict(event["scope"])),
                    source_epoch_id=event["source_epoch_id"], input_version=event["input_version"],
                    clocks=PointInTimeClocksV1(**{name: projected(ns) for name, ns in event["native_clocks"].items()}),
                    ttl=timedelta(microseconds=event["ttl_ns"] // 1000), values=_evidence_decode_source_values_v1(event),
                    authorized_binding_ids=event["authorized_binding_ids"], producer_receipt_id=event["producer_receipt_id"],
                    producer_receipt_type=event["producer_receipt_type"], source_state_and_claim_lineage=event["source_state_and_claim_lineage"],
                    provider_sequence=None if isinstance(event["provider_sequence"], Mapping) else event["provider_sequence"],
                    revision=None if isinstance(event["revision"], Mapping) else event["revision"],
                    prior_revision_available_time=None if isinstance(prior, Mapping) else projected(prior), source_conflict=False))
        self.operation, self.packets = operation, tuple(packets)
        # Pin the locally reconstructed roster before any subsequent native
        # observation can expose an earlier decoded packet to substitution.
        witness = _evidence_native_graph_witness_v1(self.packets,
            (OwnerValuePacketV1, ComputationScopeV1, PointInTimeClocksV1))
        self._original_members = (self, operation, self.packets, witness, self._source_originals)

    def _require_original_v1(self):
        root = self._original_members
        _native_require(type(root) is tuple and len(root) == 5 and root[0] is self
                        and root[1] is self.operation and root[2] is self.packets and root[4] is self._source_originals,
                        "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
        _require_evidence_source_slice_roster_v1(self.operation, tuple(item[3] for item in root[4]), originals=root[4])
        _require_evidence_resolution_witness_v1(self.packets, root[3])
        return root

    def packet_for(self, *, context, binding_id):
        from .persistence import _EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1
        original = _EvidenceAssemblyPacketViewV1._require_original_v1(self)
        owner = type(self.operation)
        _native_require(owner in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1), "LP03_ORIGINAL_INPUT_VIEW_OWNER")
        owner._check_current_v1(self.operation)
        _native_require(_EvidenceAssemblyPacketViewV1._require_original_v1(self) is original,
                        "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
        matches = tuple(packet for packet in self.packets if binding_id in packet.authorized_binding_ids)
        _native_require(len(matches) == 1, "LP03_ASSEMBLY_FORMULA_BINDING_MISSING_OR_AMBIGUOUS")
        return matches[0]


def _validate_evidence_assembly_inputs_v1(operation, slices):
    """Selected input validation only; never invokes mathematics or callbacks."""
    from .persistence import _EvidenceControlBootstrapV1
    _native_require(type(operation) is _EvidenceControlBootstrapV1, "LP03_ASSEMBLY_ORIGINAL_INPUT_OWNER")
    return _resolve_evidence_original_inputs_v1(operation, slices)


@dataclass(frozen=True, slots=True)
class _EvidencePendingProbabilityEdgeInputsV1:
    """Resolved external subset plus an unexecuted registered dependency.

    This is deliberately not FormulaInputResolutionV1 and has no
    authoritative_values or complete inputs property. Only the same attempt's
    later original M01 result/conversion can supply the missing market input.
    A constructor or decoded copy confers no original invocation custody.
    """

    math_spec_id: str
    execution_context: ComputationExecutionContextV1
    external_inputs: tuple[ResolvedFormulaInputV1, ...]
    model_input_json: str
    packet_refs: tuple[str, ...]
    receipt_refs: tuple[str, ...]
    pending_edge_id: str
    producer_invocation_ordinal: int
    pending_consumer_binding_id: str
    resolution_state: str

    @property
    def context_id(self):
        return self.execution_context.context_id

    def __post_init__(self):
        from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
        from .implementation_registry import _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1
        from .serialization import _native_strict_json, _encode_evidence_projection_json_v1
        bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-02"]
        _native_require(self.math_spec_id == "MATH-02"
            and self.pending_edge_id == "EDGE::MATH-01::MATH-02"
            and type(self.producer_invocation_ordinal) is int and self.producer_invocation_ordinal == 0
            and self.pending_consumer_binding_id == bindings[1].binding_id
            and self.resolution_state == "ORIGINAL_EXTERNAL_INPUTS_RESOLVED_MATH01_RESULT_AND_CONVERSION_PENDING",
            "LP03_EDGE_CHAIN_PENDING_DEPENDENCY")
        _native_require(type(self.execution_context) is ComputationExecutionContextV1
            and self.execution_context.dependency_graph_id == "STACK::MATH-01::MATH-02::V3_4"
            and self.execution_context.dependency_graph_version == "3.4"
            and tuple((pin.math_spec_id, pin.implementation_id) for pin in self.execution_context.implementation_versions)
                == tuple((name, _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1[name].implementation_id) for name in ("MATH-01", "MATH-02")),
            "LP03_EDGE_CHAIN_PENDING_CONTEXT")
        _native_require(type(self.external_inputs) is tuple and len(self.external_inputs) == 2
            and all(type(row) is ResolvedFormulaInputV1 for row in self.external_inputs)
            and tuple((row.binding_id, row.math_spec_id, row.input_name, row.field_path, row.owner_id)
                for row in self.external_inputs) == tuple((binding.binding_id, "MATH-02", binding.input_name,
                    binding.exact_field_path, binding.accepted_upstream_owner_id) for binding in (bindings[0], bindings[2])),
            "LP03_EDGE_CHAIN_PENDING_EXTERNAL_ROSTER")
        _native_require(all(type(row.point_in_time_receipt) is PointInTimeReceiptV1
            and type(row.freshness_receipt) is FreshnessReceiptV1
            and row.point_in_time_receipt.admitted is True and row.point_in_time_receipt.violation is None
            and row.point_in_time_receipt.context_id == row.freshness_receipt.context_id == self.execution_context.context_id
            and row.point_in_time_receipt.as_of_time == self.execution_context.as_of
            and row.freshness_receipt.source_epoch_id == self.execution_context.source_epoch_id
            and row.freshness_receipt.admitted is True for row in self.external_inputs),
            "LP03_EDGE_CHAIN_PENDING_ORIGINAL_PIT_FRESHNESS")
        _native_require(type(self.packet_refs) is tuple
            and self.packet_refs == tuple(row.packet_id for row in self.external_inputs)
            and len(set(self.packet_refs)) == 2
            and type(self.receipt_refs) is tuple and self.receipt_refs == tuple(ref for row in self.external_inputs
                for ref in (row.producer_receipt_id, row.point_in_time_receipt.receipt_id, row.freshness_receipt.receipt_id))
            and len(set(self.receipt_refs)) == 6, "LP03_EDGE_CHAIN_PENDING_ORIGINAL_REFERENCES")
        _native_require(type(self.model_input_json) is str and 0 < len(self.model_input_json) <= 65536,
                        "LP03_EDGE_CHAIN_PENDING_MODEL_WIRE")
        wire = self.model_input_json.encode("utf-8", "strict")
        model = _native_strict_json(wire, max_bytes=65536, max_nodes=4096, binary64_numbers=True)
        _native_require(type(model) is dict and set(model) == {"calibrated_model_probability", "calibration_state"}
            and type(model["calibrated_model_probability"]) is float
            and math.isfinite(model["calibrated_model_probability"])
            and 0.0 <= model["calibrated_model_probability"] <= 1.0
            and type(model["calibration_state"]) is str
            and model["calibration_state"] == "CALIBRATED_FOR_DECLARED_CONTEXT"
            and _encode_evidence_projection_json_v1(model, maximum_bytes=65536, maximum_nodes=4096) == wire,
            "LP03_EDGE_CHAIN_PENDING_MODEL_DATA")
        from struct import pack
        _native_require(type(self.external_inputs[0].value) is float
            and pack(">d", self.external_inputs[0].value) == pack(">d", model["calibrated_model_probability"])
            and type(self.external_inputs[1].value) is str
            and self.external_inputs[1].value == model["calibration_state"],
            "LP03_EDGE_CHAIN_PENDING_RESOLVED_VALUE_JOIN")


def _evidence_resolution_witness_v1(resolution):
    """Pin original resolver members before any next native observation.

    The closed dataclass/container graph was built by the original input
    resolver. This witness neither reacquires source data nor grants authority.
    """
    admitted_types = (FormulaInputResolutionV1, ResolvedFormulaInputV1, ComputationExecutionContextV1,
                      ComputationScopeV1, ImplementationVersionPinV1, PointInTimeReceiptV1, FreshnessReceiptV1,
                      _EvidenceHistoricalInputReceiptV1, _EvidencePendingProbabilityEdgeInputsV1)
    _native_require(type(resolution) in (FormulaInputResolutionV1, _EvidencePendingProbabilityEdgeInputsV1),
                    "LP03_ORIGINAL_RESOLUTION_TYPE")
    if resolution.math_spec_id == "MATH-37":
        from .economic_math import FillProbabilityModelArtifactV1
        admitted_types = (*admitted_types, FillProbabilityModelArtifactV1)
    elif resolution.math_spec_id == "MATH-35":
        from .context import QuantizationPolicyV1
        from .economic_math import FeeScheduleBindingV1
        admitted_types = (*admitted_types, FeeScheduleBindingV1, QuantizationPolicyV1)
    elif resolution.math_spec_id == "MATH-38":
        from .economic_math import FillQuantityDistributionArtifactV1
        admitted_types = (*admitted_types, FillQuantityDistributionArtifactV1)
    elif resolution.math_spec_id == "MATH-50":
        from .quantum_benchmark import (
            EconomicComparatorReceiptV1,
            QAOAPreexistingTraceV1,
            QAOATracePointV1,
            QuantumEconomicBasisV1,
        )
        admitted_types = (
            *admitted_types, QAOAPreexistingTraceV1, QAOATracePointV1,
            QuantumEconomicBasisV1, EconomicComparatorReceiptV1,
        )
    elif resolution.math_spec_id == "MATH-51":
        from .quantum_benchmark import (
            EconomicComparatorReceiptV1,
            QuantumEconomicBasisV1,
            VQEPreexistingTraceV1,
            VQETracePointV1,
        )
        admitted_types = (
            *admitted_types, VQEPreexistingTraceV1, VQETracePointV1,
            QuantumEconomicBasisV1, EconomicComparatorReceiptV1,
        )
    elif resolution.math_spec_id == "MATH-52":
        from .quantum_benchmark import (
            EconomicComparatorReceiptV1,
            QuantumEconomicBasisV1,
            QuantumTraceValidationReceiptV1,
        )
        admitted_types = (
            *admitted_types, QuantumTraceValidationReceiptV1,
            QuantumEconomicBasisV1, EconomicComparatorReceiptV1,
        )
    return _evidence_native_graph_witness_v1(resolution, admitted_types)


def _evidence_native_graph_witness_v1(resolution, admitted_types, *, maximum_bytes=1048576, source_only=False):
    """Retain a bounded graph built locally by the original resolver only."""
    from dataclasses import fields
    from .serialization import deterministic_json, _evidence_native_decimal_json_upper_v1
    from .context import QuantizationPolicyV1, QuantizationRoundingV1, decimal_context_v1
    from decimal import localcontext
    from .models import EvidenceOriginV1, EvidenceSourceSliceV1, EvidenceRecordRefV1
    _native_require(type(source_only) is bool and (not source_only
                    or type(resolution) is EvidenceSourceSliceV1
                    and admitted_types == (EvidenceSourceSliceV1, EvidenceRecordRefV1)),
                    "LP03_ORIGINAL_SOURCE_GRAPH_PROFILE")
    _native_require(type(maximum_bytes) is int and 0 < maximum_bytes <= 1048576,
                    "LP03_ORIGINAL_RESOLUTION_BYTE_BOUND")
    facts, seen, active = [], set(), set()
    nodes, upper_bytes = 0, 0
    def charge(size):
        nonlocal upper_bytes
        upper_bytes += size
        _native_require(upper_bytes <= maximum_bytes, "LP03_ORIGINAL_RESOLUTION_BYTE_BOUND")
    def text_size(text):
        _native_require(type(text) is str and len(text) <= 65536, "LP03_ORIGINAL_RESOLUTION_BYTE_BOUND")
        return 6 * len(text) + 2
    def visit(item, depth):
        nonlocal nodes
        nodes += 1
        _native_require(nodes <= 4096 and depth <= 16, "LP03_ORIGINAL_RESOLUTION_BOUND")
        kind = type(item)
        if source_only:
            # Only the acquired source schema may reuse its original canonical
            # bytes after an exact graph check. A future native leaf type must
            # not silently gain that exemption from serialization.
            _native_require(kind in (type(None), bool, str, int, EvidenceOriginV1,
                            EvidenceSourceSliceV1, EvidenceRecordRefV1, tuple, MappingProxyType),
                            "LP03_ORIGINAL_SOURCE_GRAPH_MEMBER_TYPE")
        if item is None or kind is bool:
            charge(5)
            return
        if kind is str:
            charge(text_size(item))
            return
        if kind is int:
            charge(max(1, item.bit_length()) + 2)
            return
        if kind in (float, datetime, timedelta):
            charge(128)
            return
        if kind is Decimal:
            charge(_evidence_native_decimal_json_upper_v1(item, maximum_bytes=maximum_bytes - upper_bytes))
            return
        if kind in (PointInTimeFieldClassV1, EvidenceOriginV1) or (
                kind is QuantizationRoundingV1 and QuantizationPolicyV1 in admitted_types):
            charge(text_size(item.value))
            if source_only or kind is QuantizationRoundingV1:
                facts.append((item, kind, "FIELDS", (("value", item.value),)))
            return
        _native_require(kind in (*admitted_types, tuple, MappingProxyType), "LP03_ORIGINAL_RESOLUTION_MEMBER_TYPE")
        _native_require(id(item) not in active, "LP03_ORIGINAL_RESOLUTION_CYCLE")
        active.add(id(item))
        first = id(item) not in seen
        seen.add(id(item))
        if kind in admitted_types:
            members = tuple((field.name, getattr(item, field.name)) for field in fields(kind))
            if first:
                facts.append((item, kind, "FIELDS", members))
            charge(2 + 2 * len(members))
            for name, _ in members:
                visit(name, depth + 1)
            children = tuple(value for _, value in members)
        elif kind is MappingProxyType:
            _native_require(len(item) <= 4096 - nodes and all(type(name) is str for name in item),
                            "LP03_ORIGINAL_RESOLUTION_BOUND")
            members = tuple(item.items())
            if first:
                facts.append((item, kind, "MAPPING", members))
            charge(2 + 2 * len(members))
            for name, _ in members:
                visit(name, depth + 1)
            children = tuple(value for _, value in members)
        else:
            _native_require(len(item) <= 4096 - nodes, "LP03_ORIGINAL_RESOLUTION_BOUND")
            charge(2 + len(item))
            children = item
        for child in children:
            visit(child, depth + 1)
        active.remove(id(item))
    visit(resolution, 0)
    with localcontext(decimal_context_v1()):
        canonical = deterministic_json(resolution)
    _native_require(len(canonical.encode("utf-8")) <= upper_bytes, "LP03_ORIGINAL_RESOLUTION_BYTE_BOUND")
    witness = (resolution, tuple(facts), canonical)
    _require_evidence_resolution_witness_v1(resolution, witness)
    return witness


def _bind_evidence_source_acquisition_guard_v1(operation):
    """Constructor-local acquisition history; no source or execution grant."""
    from .models import EvidenceSourceSliceV1, EvidenceSourceSelectionV1
    from .persistence import _EvidenceRegistrationOperationV1, _EvidenceReviewOperationV1, _EvidenceAttemptOperationV1
    root = operation.source_slice_minted
    prefix = operation.source_slice_originals
    owner, issuer = type(operation), operation.issuer
    accounting = operation.registration if owner is _EvidenceReviewOperationV1 else operation
    envelope_entry = accounting.envelope_entry
    scope = envelope_entry[3].assembly_scope
    custodies, selections = issuer.source_custodies, scope.source_selections
    _native_require(type(root) is tuple and len(root) == 2 and root[0] is operation and type(root[1]) is list
                    and type(prefix) is tuple and not prefix and not root[1]
                    and type(custodies) is tuple and type(selections) is tuple,
                    "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")

    def guard(action, pending=None, completed=None):
        nonlocal prefix
        _native_require(operation.source_slice_minted is root
                        and operation.source_slice_originals is prefix
                        and type(operation) is owner and operation.issuer is issuer
                        and (operation.registration if owner is _EvidenceReviewOperationV1 else operation) is accounting
                        and accounting.envelope_entry is envelope_entry and envelope_entry[3].assembly_scope is scope
                        and issuer.source_custodies is custodies and scope.source_selections is selections
                        and type(root[1]) is list and len(root[1]) == len(prefix)
                        and all(left is right for left, right in zip(root[1], prefix)),
                        "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
        if action == "INSPECT":
            _native_require(pending is None and completed is None, "LP03_ORIGINAL_SOURCE_SLICE_TRANSITION")
            return prefix
        if action == "PENDING":
            _native_require(type(pending) is tuple and len(pending) == 6 and pending[4:] == (None, None)
                            and completed is None and all(entry[4] is not None for entry in prefix),
                            "LP03_ORIGINAL_SOURCE_SLICE_TRANSITION")
            # Prove immutable entry facts once, when the actual acquisition
            # mints them. INSPECT retains the same original scope and tuples;
            # selected consumers still check current relationships and data.
            _native_require((pending[0] is operation or owner is _EvidenceRegistrationOperationV1
                             and type(pending[0]) is _EvidenceAttemptOperationV1 and pending[0].registration is operation)
                            and type(pending[1]) is _EvidenceOwnerPacketCustodyV1
                            and any(pending[1] is custody for custody in custodies)
                            and type(pending[2]) is EvidenceSourceSelectionV1
                            and any(pending[2] is selection for selection in selections)
                            and type(pending[3]) is EvidenceSourceSliceV1,
                            "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
            # Allocate the next immutable prefix first. It retains the actual
            # pending source even if growing the visible diagnostic list fails.
            retained = (*prefix, pending)
            prefix = retained
            root[1].append(pending)
            operation.source_slice_originals = retained
            return retained
        _native_require(action == "COMPLETE" and prefix and prefix[-1] is pending
                        and pending[4:] == (None, None) and type(completed) is tuple and len(completed) == 6
                        and all(left is right for left, right in zip(pending[:4], completed[:4]))
                        and type(completed[4]) is tuple and len(completed[4]) == 3
                        and completed[4][0] is completed[3] and type(completed[4][2]) is str
                        and type(completed[5]) is bytes,
                        "LP03_ORIGINAL_SOURCE_SLICE_TRANSITION")
        # Allocation failure here leaves the captured pending prefix intact.
        retained = (*prefix[:-1], completed)
        root[1][-1] = completed
        operation.source_slice_originals = retained
        prefix = retained
        return retained

    return guard


def _require_evidence_source_acquisition_prefix_v1(operation):
    """Independent original minted entries forbid omission or replacement."""
    from .persistence import (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1,
                              _EvidenceReviewOperationV1)
    owner = type(operation)
    _native_require(owner in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1, _EvidenceReviewOperationV1),
                    "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_REQUIRED")
    root, prefix = operation.source_slice_minted, operation.source_slice_originals
    if owner is _EvidenceControlBootstrapV1:
        association = operation.issuer.preparations.get(operation.grant_record.record_id)
        _native_require(type(association) is tuple and len(association) == 3 and association[0] is operation,
                        "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
        issued = association[2]
    elif owner is _EvidenceRegistrationOperationV1:
        association = operation.preparation.registration_source_original
        _native_require(type(association) is tuple and len(association) == 2 and association[0] is operation
                        and operation.issuer.registrations.get(operation.preparation.grant_record.record_id) is operation,
                        "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
        issued = association[1]
    else:
        _native_require(operation.registration.review_operation is operation
                        and type(operation.original) is tuple and len(operation.original) == 18,
                        "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
        issued = operation.original[17]
    _native_require(type(issued) is tuple and len(issued) == 2 and issued[0] is root
                    and issued[1] is operation.source_slice_guard,
                    "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
    # Verify constructor-issued identity before calling the captured inspector.
    _native_require(operation.source_slice_guard("INSPECT") is prefix,
                    "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
    accounting = operation.registration if owner is _EvidenceReviewOperationV1 else operation
    _native_require(len(prefix) <= accounting.consumed["record_reads"],
                    "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
    return prefix, root


def _require_evidence_source_slice_roster_v1(operation, slices, *, originals=None, canonical=True, subject=None):
    """Require the exact witnesses minted by this original read operation."""
    from .models import EvidenceSourceSliceV1, EvidenceSourceSelectionV1
    from .persistence import (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1,
                              _EvidenceReviewOperationV1, _EvidenceAttemptOperationV1)
    owner = type(operation)
    _native_require(owner in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1, _EvidenceReviewOperationV1),
                    "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_REQUIRED")
    accounting = operation.registration if owner is _EvidenceReviewOperationV1 else operation
    if subject is None:
        subject = operation.active_attempt if owner is _EvidenceRegistrationOperationV1 and operation.active_attempt is not None else operation
    _native_require(subject is operation or owner is _EvidenceRegistrationOperationV1
                    and type(subject) is _EvidenceAttemptOperationV1 and subject.registration is operation,
                    "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
    prefix, _ = _require_evidence_source_acquisition_prefix_v1(operation)
    _native_require(type(slices) is tuple and type(operation.source_slice_originals) is tuple
                    and len(slices) <= len(operation.source_slice_originals) <= accounting.consumed["record_reads"],
                    "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_REQUIRED")
    records = []
    for part in slices:
        _native_require(type(part) is EvidenceSourceSliceV1, "LP03_ORIGINAL_SOURCE_SLICE_REQUIRED")
        matches = tuple(entry for entry in prefix
                        if type(entry) is tuple and len(entry) == 6 and entry[0] is subject and entry[3] is part)
        _native_require(len(matches) == 1, "LP03_ORIGINAL_SOURCE_SLICE_REQUIRED")
        entry = matches[0]
        _native_require(type(entry[1]) is _EvidenceOwnerPacketCustodyV1
                        and any(entry[1] is custody for custody in operation.issuer.source_custodies)
                        and type(entry[2]) is EvidenceSourceSelectionV1
                        and any(entry[2] is selection for selection in accounting.envelope_entry[3].assembly_scope.source_selections)
                        and type(entry[5]) is bytes, "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
        published = _EvidenceOwnerPacketCustodyV1._published_source_v1(entry[1])
        if published is not None:
            reads = tuple(read for read in published.reads if read.consumer is operation
                and read.original[2] is entry[2] and read.source_result is not None and read.source_result[0] is part)
            _native_require(len(reads) == 1 and reads[0].phase == "READBACK_CONFIRMED"
                            and reads[0].completed is reads[0].source_result[1]
                            and reads[0].completed[0] is reads[0].original
                            and reads[0].completed[1] is reads[0].observations,
                            "LP03_KELLY27_ORIGINAL_SOURCE_READBACK_CHANGED")
            _EvidencePublishedSourceReadV1._assert_original_v1(reads[0])
        # Acquisition already serialized this closed source graph under the
        # bounded source-only witness. The captured guard pins that exact
        # witness and bytes; every mutable field/mapping (including the enum
        # value) is still checked on every use. Do not reconstruct identical
        # JSON at each native currentness boundary.
        _require_evidence_resolution_witness_v1(part, entry[4], canonical=False)
        if canonical:
            _native_require(entry[4][2].encode("utf-8") == entry[5], "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
        records.append(entry)
    retained = tuple(records)
    if originals is not None:
        _native_require(type(originals) is tuple and len(originals) == len(retained)
                        and all(left is right for left, right in zip(retained, originals)),
                        "LP03_ORIGINAL_SOURCE_SLICE_ROSTER_CHANGED")
        return originals
    return retained


def _require_evidence_resolution_witness_v1(resolution, witness, *, canonical=True):
    from .serialization import deterministic_json
    from .context import decimal_context_v1
    from decimal import localcontext
    _native_require(type(witness) is tuple and len(witness) == 3 and witness[0] is resolution,
                    "LP03_ORIGINAL_RESOLUTION_MEMBERS_CHANGED")
    for original, kind, shape, members in witness[1]:
        _native_require(type(original) is kind, "LP03_ORIGINAL_RESOLUTION_MEMBERS_CHANGED")
        if shape == "FIELDS":
            _native_require(all(getattr(original, name) is value for name, value in members),
                            "LP03_ORIGINAL_RESOLUTION_MEMBERS_CHANGED")
        else:
            _native_require(len(original) == len(members), "LP03_ORIGINAL_RESOLUTION_MEMBERS_CHANGED")
            try:
                same = all(actual[0] is retained[0] and actual[1] is retained[1]
                           for actual, retained in zip(original.items(), members, strict=True))
            except ValueError:
                same = False
            _native_require(same, "LP03_ORIGINAL_RESOLUTION_MEMBERS_CHANGED")
    if canonical:
        with localcontext(decimal_context_v1()):
            _native_require(deterministic_json(resolution) == witness[2], "LP03_ORIGINAL_RESOLUTION_MEMBERS_CHANGED")


def _resolve_evidence_private26_inputs_v1(operation, view, decision):
    """Resolve one original software-only research input roster, without math.

    The signed original source selections and retained registry establish the
    owners. Private semantic role labels do not create a research authority.
    Action/scenario identities and utility metadata remain original source
    data; none are added to the existing three-argument financial callable.
    """
    from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
    from .implementation_registry import _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1
    from .models import EvidenceOriginV1, EvidenceRecordRefV1, EvidenceAbsenceV1
    from .persistence import _EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1
    from .serialization import _encode_evidence_projection_json_v1, deterministic_json
    from .context import _native_ident
    owner = type(operation)
    _native_require(owner in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1)
                    and type(view) is _EvidenceAssemblyPacketViewV1 and view.operation is operation
                    and operation.envelope_entry[3].assembly_scope.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
                    and operation.envelope_entry[3].component_closure == ("MATH-26",),
                    "LP03_PRIVATE26_ORIGINAL_SOFTWARE_SCOPE")
    original_view = _EvidenceAssemblyPacketViewV1._require_original_v1(view)
    owner._check_current_v1(operation)
    _native_require(_EvidenceAssemblyPacketViewV1._require_original_v1(view) is original_view,
                    "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
    contract = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-26"]
    _native_require(tuple(binding.input_name for binding in contract.bindings)
                    == ("current_action_values", "new_information_scenarios", "acquisition_cost"),
                    "LP03_PRIVATE26_ORIGINAL_BINDING_ROSTER")
    packets = tuple(view.packet_for(context=None, binding_id=binding.binding_id) for binding in contract.bindings)
    first = packets[0]
    scope = operation.envelope_entry[3].assembly_scope
    _native_require(len({packet.packet_id for packet in packets}) == 3
                    and len({packet.producer_receipt_id for packet in packets}) == 3
                    and all(packet.owner_id in scope.input_owner_roster
                        and packet.context_id == first.context_id and packet.scope == first.scope
                        and packet.source_epoch_id == first.source_epoch_id and packet.input_version == first.input_version
                        and type(packet.revision) is type(first.revision) and packet.revision == first.revision
                        and type(packet.revision) in (int, str) for packet in packets),
                    "LP03_PRIVATE26_ORIGINAL_CONTEXT_JOIN")
    selections = scope.source_selections
    refs = []
    for packet in packets:
        selected = tuple(selection for selection in selections if packet.packet_id in selection.selection.record_refs)
        _native_require(len(selected) == 1, "LP03_PRIVATE26_ORIGINAL_SOURCE_SELECTION")
        refs.append(EvidenceRecordRefV1(selected[0].original_store_id, packet.packet_id))
    contexts, native_inputs = [], {}
    common_fields = {"profile", "binding_id", "producer_role", "research_decision_ref", "action_roster_source_ref",
                     "ordered_action_ids", "utility_unit", "utility_currency_or_absence", "utility_basis_ref", "horizon_ref"}
    for packet, binding in zip(packets, contract.bindings):
        _native_require((packet.packet_type, packet.schema_id, packet.schema_version, packet.producer_receipt_type)
                        == ("LP03OriginalPrivateInputSourceV1", "LP03::MATH-26::ORIGINAL_INPUT_SOURCE_V1", "1.0",
                            "LP03_MATH26_ORIGINAL_INPUT_RECEIPT_V1")
                        and packet.source_state_and_claim_lineage == "LP03::MATH-26::ORIGINAL_INPUT::" + binding.producer_role
                        and packet.authorized_binding_ids == (binding.binding_id,)
                        and set(packet.values) == {binding.input_name, "private_source_context"}
                        and packet.source_conflict is False, "LP03_PRIVATE26_ORIGINAL_PRODUCER_SCHEMA")
        metadata = packet.values["private_source_context"]
        additional = ({"ordered_scenario_ids", "probability_resolution_receipt_ref"} if binding.input_name == "new_information_scenarios"
                      else {"acquisition_target_ref"} if binding.input_name == "acquisition_cost" else set())
        _native_require(type(metadata) is MappingProxyType and set(metadata) == common_fields | additional,
                        "LP03_PRIVATE26_SOURCE_CONTEXT_FIELDS")
        for name in common_fields - {"action_roster_source_ref", "ordered_action_ids", "utility_currency_or_absence"}:
            _native_ident(metadata[name])
        _native_require(metadata["profile"] == "LP03_MATH26_ORIGINAL_UTILITY_INPUT_V1"
                        and metadata["binding_id"] == binding.binding_id and metadata["producer_role"] == binding.producer_role,
                        "LP03_PRIVATE26_SOURCE_CONTEXT_PROFILE")
        roster_ref = metadata["action_roster_source_ref"]
        _native_require(type(roster_ref) is MappingProxyType and set(roster_ref) == {"store_id", "record_id"}
                        and EvidenceRecordRefV1(roster_ref["store_id"], roster_ref["record_id"]) == refs[0],
                        "LP03_PRIVATE26_ORIGINAL_ACTION_ROSTER_REF")
        actions = metadata["ordered_action_ids"]
        _native_require(type(actions) is tuple and 0 < len(actions) <= 4096, "LP03_PRIVATE26_ORIGINAL_ACTION_ROSTER")
        for action in actions:
            _native_ident(action)
        _native_require(len(set(actions)) == len(actions), "LP03_PRIVATE26_ORIGINAL_ACTION_ROSTER")
        currency = metadata["utility_currency_or_absence"]
        if type(currency) is MappingProxyType:
            _native_require(EvidenceAbsenceV1.from_canonical_mapping(dict(currency)).reason == "NOT_CURRENCY_DENOMINATED",
                            "LP03_PRIVATE26_UTILITY_CURRENCY_ABSENCE")
        else:
            _native_ident(currency)
            _native_require(type(currency) is str and len(currency) == 3 and currency.isascii() and currency.isalpha()
                            and currency.isupper() and metadata["utility_unit"] == currency,
                            "LP03_PRIVATE26_UTILITY_CURRENCY_BASIS")
        if binding.input_name == "new_information_scenarios":
            scenarios = metadata["ordered_scenario_ids"]
            _native_require(type(scenarios) is tuple and 0 < len(scenarios) <= 4096,
                            "LP03_PRIVATE26_ORIGINAL_SCENARIO_ROSTER")
            for scenario in scenarios:
                _native_ident(scenario)
            _native_ident(metadata["probability_resolution_receipt_ref"])
            _native_require(len(set(scenarios)) == len(scenarios)
                            and metadata["probability_resolution_receipt_ref"] == packet.producer_receipt_id,
                            "LP03_PRIVATE26_ORIGINAL_PROBABILITY_RECEIPT")
        elif binding.input_name == "acquisition_cost":
            _native_ident(metadata["acquisition_target_ref"])
            _native_require(metadata["acquisition_target_ref"] == metadata["research_decision_ref"],
                            "LP03_PRIVATE26_ORIGINAL_COST_SCOPE")
        contexts.append(metadata)
        native_inputs[binding.input_name] = packet.values[binding.input_name]
    shared = common_fields - {"binding_id", "producer_role"}
    _native_require(all(all(type(context[name]) is type(contexts[0][name])
                            and deterministic_json(context[name]) == deterministic_json(contexts[0][name]) for name in shared)
                        for context in contexts[1:]), "LP03_PRIVATE26_ORIGINAL_ACTION_UTILITY_JOIN")
    # The exact native string/tuple inputs are sized before JSON formatting.
    # Private decoding reconstructs the original Decimal arguments, with no
    # formula, normalization, fitted model or synthetic output computation.
    wire = _encode_evidence_projection_json_v1(native_inputs, maximum_bytes=65536, maximum_nodes=4096)
    values = decode_evidence_private_inputs_v1("MATH-26", wire, maximum_bytes=65536, maximum_nodes=4096)
    _native_require(len(values["current_action_values"]) == len(contexts[0]["ordered_action_ids"])
                    and len(values["new_information_scenarios"]) == len(contexts[1]["ordered_scenario_ids"])
                    and all(len(row[1]) == len(contexts[0]["ordered_action_ids"]) for row in values["new_information_scenarios"]),
                    "LP03_PRIVATE26_ORIGINAL_VALUE_ROSTER")
    context = ComputationExecutionContextV1(context_id=first.context_id, as_of=decision, observed_at=decision,
        source_epoch_id=first.source_epoch_id, input_version=first.input_version, maximum_age=min(packet.ttl for packet in packets),
        scope=first.scope, binding_profile_version="LP03::MATH-26::INPUT_V1",
        parameter_policy_version="ST12F_PARAMETER_RESOURCE_ROW_V1", implementation_versions=(ImplementationVersionPinV1(
            "MATH-26", _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1["MATH-26"].implementation_id),))
    FreshnessResolverV1.assert_context_current(context)
    resolved = []
    for packet, binding in zip(packets, contract.bindings):
        pit = PointInTimePolicyV1.validate(receipt_id=f"PIT::{packet.packet_id}::{binding.binding_id}",
            field_class=PointInTimeFieldClassV1.OBSERVATION, clocks=packet.clocks, context=context,
            prior_revision_available_time=packet.prior_revision_available_time)
        freshness = FreshnessResolverV1.validate(receipt_id=f"FRESHNESS::{packet.packet_id}::{binding.binding_id}",
            clocks=packet.clocks, context=context, packet_source_epoch_id=packet.source_epoch_id,
            policy=FreshnessPolicyV1(ttl=packet.ttl, require_provider_sequence=False, require_revision=True),
            provider_sequence=packet.provider_sequence, revision=packet.revision)
        resolved.append(ResolvedFormulaInputV1(binding.binding_id, "MATH-26", binding.input_name, values[binding.input_name],
            packet.owner_id, packet.packet_id, binding.exact_field_path, pit, freshness, packet.producer_receipt_id))
    resolution = FormulaInputResolutionV1("MATH-26", context, tuple(resolved), values, tuple(packet.packet_id for packet in packets),
        tuple(ref for row in resolved for ref in (row.producer_receipt_id, row.point_in_time_receipt.receipt_id, row.freshness_receipt.receipt_id)))
    _native_require(_EvidenceAssemblyPacketViewV1._require_original_v1(view) is original_view,
                    "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
    # The caller pins this exact resolution before its next native observation.
    return resolution


def _resolve_evidence_private27_inputs_v1(operation, view, decision):
    """Resolve original synthetic probability/payoff inputs, without sizing.

    Original signed selections and producer custody establish the owners.
    Calibration/payoff metadata describes those sources; it cannot create a
    calibrated model, private account observation or permission to use capital.
    """
    from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
    from .implementation_registry import _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1
    from .models import EvidenceOriginV1, EvidenceRecordRefV1, _evidence_kelly27_context_v1
    from .persistence import _EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1
    from .serialization import _encode_evidence_projection_json_v1, deterministic_json
    owner = type(operation)
    _native_require(owner in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1)
                    and type(view) is _EvidenceAssemblyPacketViewV1 and view.operation is operation
                    and operation.envelope_entry[3].assembly_scope.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
                    and operation.envelope_entry[3].component_closure == ("MATH-27",),
                    "LP03_PRIVATE27_ORIGINAL_SOFTWARE_SCOPE")
    original_view = _EvidenceAssemblyPacketViewV1._require_original_v1(view)
    owner._check_current_v1(operation)
    _native_require(_EvidenceAssemblyPacketViewV1._require_original_v1(view) is original_view,
                    "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
    contract = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-27"]
    _native_require(tuple(binding.input_name for binding in contract.bindings) == ("win_probability", "net_odds"),
                    "LP03_PRIVATE27_ORIGINAL_BINDING_ROSTER")
    packets = tuple(view.packet_for(context=None, binding_id=binding.binding_id) for binding in contract.bindings)
    first, scope = packets[0], operation.envelope_entry[3].assembly_scope
    _native_require(len({packet.packet_id for packet in packets}) == len({packet.producer_receipt_id for packet in packets}) == 2
                    and all(packet.owner_id in scope.input_owner_roster
                        and packet.context_id == first.context_id and packet.scope == first.scope
                        and packet.source_epoch_id == first.source_epoch_id and packet.input_version == first.input_version
                        and type(packet.revision) is type(first.revision) and packet.revision == first.revision
                        and type(packet.revision) in (int, str) for packet in packets),
                    "LP03_PRIVATE27_ORIGINAL_CONTEXT_JOIN")
    refs = []
    for packet in packets:
        selected = tuple(selection for selection in scope.source_selections if packet.packet_id in selection.selection.record_refs)
        _native_require(len(selected) == 1, "LP03_PRIVATE27_ORIGINAL_SOURCE_SELECTION")
        refs.append(EvidenceRecordRefV1(selected[0].original_store_id, packet.packet_id))
    contexts, native_inputs = [], {}
    for packet, binding in zip(packets, contract.bindings, strict=True):
        _native_require((packet.packet_type, packet.schema_id, packet.schema_version, packet.producer_receipt_type)
                        == ("LP03OriginalPrivateInputSourceV1", "LP03::MATH-27::ORIGINAL_INPUT_SOURCE_V1", "1.0",
                            "LP03_MATH27_ORIGINAL_INPUT_RECEIPT_V1")
                        and packet.source_state_and_claim_lineage == "LP03::MATH-27::ORIGINAL_INPUT::" + binding.producer_role
                        and packet.authorized_binding_ids == (binding.binding_id,)
                        and set(packet.values) == {binding.input_name, "private_source_context"}
                        and packet.source_conflict is False, "LP03_PRIVATE27_ORIGINAL_PRODUCER_SCHEMA")
        text = packet.values[binding.input_name]
        _native_require(type(text) is str and 0 < len(text) <= 4096, "LP03_KELLY27_ORIGINAL_FINANCIAL_TEXT")
        contexts.append(_evidence_kelly27_context_v1(packet.values["private_source_context"], binding=binding,
            original_refs=tuple(refs), producer_receipt_id=packet.producer_receipt_id,
            instrument_ref=packet.scope.instrument_or_contract_scope_id, event_ref=packet.scope.event_scope_id))
        native_inputs[binding.input_name] = text
    shared = set(contexts[0]) - {"binding_id", "producer_role", "original_resolution_receipt_ref"}
    _native_require(all(all(type(context[name]) is type(contexts[0][name])
                            and deterministic_json(context[name]) == deterministic_json(contexts[0][name]) for name in shared)
                        for context in contexts[1:]), "LP03_KELLY27_ORIGINAL_CONTEXT_JOIN")
    wire = _encode_evidence_projection_json_v1(native_inputs, maximum_bytes=65536, maximum_nodes=4096)
    values = decode_evidence_private_inputs_v1("MATH-27", wire, maximum_bytes=65536, maximum_nodes=4096)
    context = ComputationExecutionContextV1(context_id=first.context_id, as_of=decision, observed_at=decision,
        source_epoch_id=first.source_epoch_id, input_version=first.input_version, maximum_age=min(packet.ttl for packet in packets),
        scope=first.scope, binding_profile_version="LP03::MATH-27::INPUT_V1",
        parameter_policy_version="ST12F_PARAMETER_RESOURCE_ROW_V1", implementation_versions=(ImplementationVersionPinV1(
            "MATH-27", _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1["MATH-27"].implementation_id),))
    FreshnessResolverV1.assert_context_current(context)
    resolved = []
    for packet, binding in zip(packets, contract.bindings, strict=True):
        pit = PointInTimePolicyV1.validate(receipt_id=f"PIT::{packet.packet_id}::{binding.binding_id}",
            field_class=PointInTimeFieldClassV1.OBSERVATION, clocks=packet.clocks, context=context,
            prior_revision_available_time=packet.prior_revision_available_time)
        freshness = FreshnessResolverV1.validate(receipt_id=f"FRESHNESS::{packet.packet_id}::{binding.binding_id}",
            clocks=packet.clocks, context=context, packet_source_epoch_id=packet.source_epoch_id,
            policy=FreshnessPolicyV1(ttl=packet.ttl, require_provider_sequence=False, require_revision=True),
            provider_sequence=packet.provider_sequence, revision=packet.revision)
        resolved.append(ResolvedFormulaInputV1(binding.binding_id, "MATH-27", binding.input_name, values[binding.input_name],
            packet.owner_id, packet.packet_id, binding.exact_field_path, pit, freshness, packet.producer_receipt_id))
    resolution = FormulaInputResolutionV1("MATH-27", context, tuple(resolved), values, tuple(packet.packet_id for packet in packets),
        tuple(ref for row in resolved for ref in (row.producer_receipt_id, row.point_in_time_receipt.receipt_id, row.freshness_receipt.receipt_id)))
    _native_require(_EvidenceAssemblyPacketViewV1._require_original_v1(view) is original_view,
                    "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
    return resolution


def _resolve_evidence_private28_inputs_v1(operation, view, decision):
    """Resolve fresh M28 use of the original M27 publication and constraints."""
    from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
    from .implementation_registry import _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1
    from .models import EvidenceOriginV1, _evidence_kelly28_source_slices_v1, _evidence_kelly27_source_slices_v1
    from .persistence import _EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1
    from .serialization import _encode_evidence_projection_json_v1, deterministic_json, _evidence_frozen_data_v1
    owner = type(operation)
    _native_require(owner in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1)
        and type(view) is _EvidenceAssemblyPacketViewV1 and view.operation is operation
        and operation.envelope_entry[3].assembly_scope.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
        and operation.envelope_entry[3].component_closure == ("MATH-28",), "LP03_PRIVATE28_ORIGINAL_SOFTWARE_SCOPE")
    original_view = _EvidenceAssemblyPacketViewV1._require_original_v1(view)
    owner._check_current_v1(operation)
    _native_require(_EvidenceAssemblyPacketViewV1._require_original_v1(view) is original_view,
                    "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
    bindings = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-28"].bindings
    packets = tuple(view.packet_for(context=None, binding_id=binding.binding_id) for binding in bindings)
    sources, entries = [], []
    for packet in packets:
        selected = tuple(entry for entry in view._source_originals if len(entry[3].original_record_refs) == 1
            and entry[3].original_record_refs[0].record_id == packet.packet_id)
        _native_require(len(selected) == 1, "LP03_PRIVATE28_ORIGINAL_SOURCE_SELECTION")
        entries.append(selected[0])
        sources.append(selected[0][3])
    produced = entries[0][1].published_kelly27
    _native_require(type(produced) is _EvidencePublishedKelly27V1
        and entries[0][1].registry is produced.materialized[0]
        and entries[0][3].original_record_refs[0].record_id == produced.materialized[1].packet_id,
        "LP03_PRIVATE28_ORIGINAL_PUBLISHED_CUSTODY")
    scope = operation.envelope_entry[3].assembly_scope
    observed = owner._check_current_v1(operation)
    _native_require(_EvidenceAssemblyPacketViewV1._require_original_v1(view) is original_view,
                    "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
    _EvidencePublishedKelly27V1._assert_scope_v1(produced, scope, observed_wall_ns=observed[0])
    _evidence_kelly28_source_slices_v1(dict(association_profile="ORIGINAL_PUBLISHED_KELLY_AND_CURRENT_CONSTRAINTS",
        source_slice_jsons=tuple(entry[5].decode("utf-8", "strict") for entry in entries),
        consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
        consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns))
    first = packets[0]
    context = ComputationExecutionContextV1(context_id=first.context_id, as_of=decision, observed_at=decision,
        source_epoch_id=first.source_epoch_id, input_version=first.input_version, maximum_age=min(packet.ttl for packet in packets),
        scope=first.scope, binding_profile_version="LP03::MATH-28::INPUT_V1",
        parameter_policy_version="ST12F_PARAMETER_RESOURCE_ROW_V1", implementation_versions=(ImplementationVersionPinV1(
            "MATH-28", _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1["MATH-28"].implementation_id),))
    FreshnessResolverV1.assert_context_current(context)
    native = {binding.input_name: packet.values[binding.input_name] for binding, packet in zip(bindings, packets, strict=True)}
    wire = _encode_evidence_projection_json_v1(native, maximum_bytes=65536, maximum_nodes=4096)
    values = decode_evidence_private_inputs_v1("MATH-28", wire, maximum_bytes=65536, maximum_nodes=4096)
    resolved = []
    delta = context.maximum_age
    maximum_age_ns = (delta.days * 86400 + delta.seconds) * 1_000_000_000 + delta.microseconds * 1000
    for packet, part, binding in zip(packets, sources, bindings, strict=True):
        event = part.reconstructed_canonical_events[0]
        # Preserve each original epoch and all six clocks. The existing
        # freshness owner sees that source's epoch at the new consumer decision.
        source_context = replace(context, source_epoch_id=packet.source_epoch_id, input_version=packet.input_version)
        _native_require(0 <= scope.snapshot_decision_wall_ns - event["native_clocks"]["observed_time"]
            <= min(event["ttl_ns"], maximum_age_ns), "LP03_KELLY28_ORIGINAL_HISTORICAL_PIT_OR_TTL")
        published_observations, upstream_contexts = (), ()
        if binding.input_name == "full_kelly_fraction":
            provenance = event["values"]["published_source_context"]
            published_observations = tuple((name, provenance[name]) for name in (
                "data_commit_observation", "data_readback_observation", "publication_commit_observation",
                "publication_readback_observation", "finalization_readback_observation", "completion_observation",
                "bridge_visibility_observation"))
            upstream = _evidence_kelly27_source_slices_v1(provenance["original_source_payload"])
            retained = []
            for original in upstream:
                source_event = original.reconstructed_canonical_events[0]
                _native_require(0 <= scope.snapshot_decision_wall_ns - source_event["native_clocks"]["observed_time"]
                    <= min(source_event["ttl_ns"], maximum_age_ns), "LP03_KELLY28_UPSTREAM_INPUT_TTL")
                retained.append(dict(source_record_ref=(original.original_record_refs[0].store_id,
                    original.original_record_refs[0].record_id), source_epoch_id=source_event["source_epoch_id"],
                    input_version=source_event["input_version"], native_clocks=source_event["native_clocks"],
                    ttl_ns=source_event["ttl_ns"], original_rights_refs=original.rights_refs))
            upstream_contexts = tuple(_evidence_frozen_data_v1(item) for item in retained)
        pit = _EvidenceHistoricalInputReceiptV1(receipt_id=f"LP03-HISTORICAL-PIT::{scope.snapshot_decision_wall_ns}::{packet.packet_id}::{binding.binding_id}",
            context_id=context.context_id, binding_id=binding.binding_id,
            source_record_ref=(part.original_record_refs[0].store_id, part.original_record_refs[0].record_id),
            source_context=source_context, source_native_clocks=tuple(event["native_clocks"].items()), source_rights_refs=part.rights_refs,
            consumer_decision_wall_ns=scope.snapshot_decision_wall_ns, consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns,
            published_producer_observations=published_observations, original_upstream_contexts=upstream_contexts)
        freshness = FreshnessResolverV1.validate(receipt_id=f"LP03-HISTORICAL-FRESHNESS::{scope.snapshot_decision_wall_ns}::{packet.packet_id}::{binding.binding_id}",
            clocks=packet.clocks, context=source_context, packet_source_epoch_id=packet.source_epoch_id,
            policy=FreshnessPolicyV1(ttl=packet.ttl, require_provider_sequence=False, require_revision=True),
            provider_sequence=packet.provider_sequence, revision=packet.revision)
        resolved.append(ResolvedFormulaInputV1(binding.binding_id, "MATH-28", binding.input_name, values[binding.input_name],
            packet.owner_id, packet.packet_id, binding.exact_field_path, pit, freshness, packet.producer_receipt_id))
    resolution = FormulaInputResolutionV1("MATH-28", context, tuple(resolved), values, tuple(packet.packet_id for packet in packets),
        tuple(ref for row in resolved for ref in (row.producer_receipt_id, row.point_in_time_receipt.receipt_id, row.freshness_receipt.receipt_id)))
    _native_require(_EvidenceAssemblyPacketViewV1._require_original_v1(view) is original_view,
                    "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
    return resolution



def _resolve_evidence_original_private_inputs_v1(operation, view, decision, *, math_id):
    """Bind the selected private analytic arguments to acquired original source slices."""
    from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1, FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .implementation_registry import _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1
    from .models import (EvidenceOriginV1, _evidence_original_private_input_profile_v1,
        _evidence_original_private_inputs_v1)
    from .persistence import _EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1
    from .serialization import _evidence_canonical_object_v1, deterministic_json

    owner = type(operation)
    envelope = operation.envelope_entry[3]
    scope = envelope.assembly_scope
    _native_require(owner in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1)
        and type(view) is _EvidenceAssemblyPacketViewV1 and view.operation is operation
        and scope.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE and envelope.component_closure == (math_id,),
        "LP03_ANALYTIC_PRIVATE_ORIGINAL_SOFTWARE_SCOPE")
    view_original = _EvidenceAssemblyPacketViewV1._require_original_v1(view)
    owner._check_current_v1(operation)
    if math_id == "MATH-36":
        bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
        binding_profile = "3.4"
    else:
        binding_contract = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1[math_id]
        bindings = binding_contract.bindings
        binding_profile = binding_contract.schema_id
    packets = tuple(view.packet_for(context=None, binding_id=binding.binding_id) for binding in bindings)
    _native_require(all(packet.owner_id in scope.input_owner_roster for packet in packets),
        "LP03_ANALYTIC_PRIVATE_SIGNED_OWNER_ROSTER")
    source_parts = []
    for packet in packets:
        selected = tuple(entry[3] for entry in view_original[4]
            if len(entry[3].original_record_refs) == 1 and entry[3].original_record_refs[0].record_id == packet.packet_id)
        _native_require(len(selected) == 1, "LP03_ANALYTIC_PRIVATE_ORIGINAL_SLICE_REQUIRED")
        source_parts.append(selected[0])
    source_profile, _, _ = _evidence_original_private_input_profile_v1(math_id)
    source_payload = _evidence_canonical_object_v1(deterministic_json(dict(
        profile=source_profile, math_id=math_id,
        decision_wall_ns=scope.snapshot_decision_wall_ns, cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns,
        source_slices=source_parts)).encode("utf-8"))
    _, values, original_scope = _evidence_original_private_inputs_v1(source_payload, math_id=math_id)
    _native_require(tuple(packet.owner_id for packet in packets) == original_scope["original_owner_ids"],
        "LP03_ANALYTIC_PRIVATE_ORIGINAL_OWNER_ASSOCIATION")
    first = packets[0]
    context = ComputationExecutionContextV1(context_id=first.context_id, as_of=decision, observed_at=decision,
        source_epoch_id=first.source_epoch_id, input_version=first.input_version,
        maximum_age=min(packet.ttl for packet in packets), scope=first.scope,
        binding_profile_version=binding_profile, parameter_policy_version="ST12F_PARAMETER_RESOURCE_ROW_V1",
        implementation_versions=(ImplementationVersionPinV1(math_id, _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1[math_id].implementation_id),))
    FreshnessResolverV1.assert_context_current(context)
    resolved = []
    for packet, binding, part in zip(packets, bindings, source_parts, strict=True):
        source = part.reconstructed_canonical_events[0]
        exact_ref = part.original_record_refs[0]
        pit = _EvidenceHistoricalInputReceiptV1(
            receipt_id=f"LP03-ANALYTIC-PIT::{scope.snapshot_decision_wall_ns}::{packet.packet_id}::{binding.binding_id}",
            context_id=context.context_id, binding_id=binding.binding_id,
            source_record_ref=(exact_ref.store_id, exact_ref.record_id), source_context=context,
            source_native_clocks=tuple(source["native_clocks"].items()), source_rights_refs=part.rights_refs,
            consumer_decision_wall_ns=scope.snapshot_decision_wall_ns, consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns,
            published_producer_observations=(), original_upstream_contexts=())
        freshness = FreshnessResolverV1.validate(receipt_id=f"FRESHNESS::{packet.packet_id}::{binding.binding_id}",
            clocks=packet.clocks, context=context, packet_source_epoch_id=packet.source_epoch_id,
            policy=FreshnessPolicyV1(ttl=packet.ttl, require_provider_sequence=math_id == "MATH-36"
                and binding.input_name not in ("payout", "price_ranges"), require_revision=True),
            provider_sequence=packet.provider_sequence, revision=packet.revision)
        resolved.append(ResolvedFormulaInputV1(binding.binding_id, math_id, binding.input_name, values[binding.input_name],
            packet.owner_id, packet.packet_id, binding.exact_field_path, pit, freshness, packet.producer_receipt_id))
    receipt_refs = tuple(ref for row in resolved for ref in (
        row.producer_receipt_id, row.point_in_time_receipt.receipt_id, row.freshness_receipt.receipt_id))
    if math_id == "MATH-36":
        # Multiple book or grid fields share the same original producer receipt.
        receipt_refs = tuple(dict.fromkeys(receipt_refs))
    resolution = FormulaInputResolutionV1(math_id, context, tuple(resolved), values,
        tuple(row.packet_id for row in packets), receipt_refs)
    owner._check_current_v1(operation)
    _native_require(_EvidenceAssemblyPacketViewV1._require_original_v1(view) is view_original,
        "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
    return resolution


def _resolve_evidence_probability_edge_component_v1(operation, view, decision, math_id, prior):
    """Resolve external originals without inventing the pending M01 result."""
    from .models import EvidenceOriginV1, _evidence_probability_edge_chain_sources_v1
    from .implementation_registry import _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1
    from .persistence import _EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1
    from .serialization import deterministic_json, _native_strict_json, _encode_evidence_projection_json_v1
    owner = type(operation)
    _native_require(owner in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1)
        and type(view) is _EvidenceAssemblyPacketViewV1 and view.operation is operation
        and operation.envelope_entry[3].assembly_scope.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
        and operation.envelope_entry[3].component_closure == ("MATH-01", "MATH-02")
        and math_id in ("MATH-01", "MATH-02") and type(prior) is tuple
        and len(prior) == (0 if math_id == "MATH-01" else 1), "LP03_EDGE_CHAIN_ORIGINAL_COMPONENT_SCOPE")
    original_view = _EvidenceAssemblyPacketViewV1._require_original_v1(view)
    owner._check_current_v1(operation)
    _native_require(_EvidenceAssemblyPacketViewV1._require_original_v1(view) is original_view,
                    "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
    market_bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-01"]
    edge_bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-02"]
    external_bindings = (*market_bindings, edge_bindings[0], edge_bindings[2])
    packets = tuple(view.packet_for(context=None, binding_id=binding.binding_id) for binding in external_bindings)
    selected = []
    for packet in packets:
        entries = tuple(entry for entry in view._source_originals if len(entry[3].original_record_refs) == 1
            and entry[3].original_record_refs[0].record_id == packet.packet_id)
        _native_require(len(entries) == 1, "LP03_EDGE_CHAIN_ORIGINAL_EXTERNAL_SELECTION")
        selected.append(_native_strict_json(entries[0][5], max_bytes=65536, max_nodes=4096))
    sources = _evidence_probability_edge_chain_sources_v1(dict(
        association_profile="ORIGINAL_SOFTWARE_MARKET_PREDICTION_AND_INDEPENDENT_CALIBRATION_CONTEXT",
        stack_id="STACK::MATH-01::MATH-02::V3_4", edge_id="EDGE::MATH-01::MATH-02", source_slices=selected))
    decision_ns = operation.envelope_entry[3].assembly_scope.snapshot_decision_wall_ns
    _native_require(all(part.reconstructed_canonical_events[0]["native_clocks"]["as_of_time"] == decision_ns
        for part in sources) and _native_utc_nanoseconds(decision.isoformat()) == decision_ns // 1000 * 1000,
        "LP03_EDGE_CHAIN_EXACT_SNAPSHOT_NANOSECOND_JOIN")
    _native_require(decision_ns
        < sources[0].reconstructed_canonical_events[0]["values"]["contract_context"]["horizon_end_wall_ns"],
        "LP03_EDGE_CHAIN_ORIGINAL_DECISION_HORIZON")
    first = packets[0]
    _native_require(all(packet.context_id == first.context_id and packet.scope == first.scope
        and packet.source_epoch_id == first.source_epoch_id and packet.input_version == first.input_version
        for packet in packets[1:]), "LP03_EDGE_CHAIN_ORIGINAL_SNAPSHOT_CONTEXT")
    if math_id == "MATH-01":
        context = ComputationExecutionContextV1(context_id=first.context_id, as_of=decision, observed_at=decision,
            source_epoch_id=first.source_epoch_id, input_version=first.input_version,
            maximum_age=min(packet.ttl for packet in packets), scope=first.scope,
            binding_profile_version="3.4", parameter_policy_version="ST12F_PARAMETER_RESOURCE_ROW_V1",
            implementation_versions=tuple(ImplementationVersionPinV1(name, _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1[name].implementation_id)
                for name in ("MATH-01", "MATH-02")), dependency_graph_id="STACK::MATH-01::MATH-02::V3_4",
            dependency_graph_version="3.4")
        resolved = FormulaInputResolverV1.resolve("MATH-01", context=context, owner_registry=view)
    else:
        producer = prior[0]
        _native_require(type(producer) is FormulaInputResolutionV1 and producer.math_spec_id == "MATH-01",
                        "LP03_EDGE_CHAIN_ORIGINAL_PRODUCER_RESOLUTION")
        context = producer.execution_context
        _native_require(context.context_id == first.context_id and context.scope == first.scope
            and context.as_of == decision and context.source_epoch_id == first.source_epoch_id
            and context.input_version == first.input_version and context.maximum_age == min(packet.ttl for packet in packets),
            "LP03_EDGE_CHAIN_ORIGINAL_SHARED_CONTEXT")
        _validate_formula_input_context(context)
        external, external_witnesses = [], []
        for binding in (edge_bindings[0], edge_bindings[2]):
            for row, witness in zip(external, external_witnesses, strict=True):
                _require_evidence_resolution_witness_v1(row, witness)
            value = _resolve_formula_input_binding("MATH-02", binding=binding, context=context,
                owner_registry=view, caller_assertions=MappingProxyType({}))
            witness = _evidence_native_graph_witness_v1(value, (ResolvedFormulaInputV1, PointInTimeReceiptV1, FreshnessReceiptV1))
            external.append(value)
            external_witnesses.append(witness)
            owner._check_current_v1(operation)
            for row, original_witness in zip(external, external_witnesses, strict=True):
                _require_evidence_resolution_witness_v1(row, original_witness)
            _native_require(_EvidenceAssemblyPacketViewV1._require_original_v1(view) is original_view,
                            "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
        model_wire = _encode_evidence_projection_json_v1({row.input_name: row.value for row in external},
            maximum_bytes=65536, maximum_nodes=4096)
        resolved = _EvidencePendingProbabilityEdgeInputsV1(math_spec_id="MATH-02", execution_context=context,
            external_inputs=tuple(external), model_input_json=model_wire.decode("utf-8", "strict"),
            packet_refs=tuple(row.packet_id for row in external), receipt_refs=tuple(ref for row in external for ref in (
                row.producer_receipt_id, row.point_in_time_receipt.receipt_id, row.freshness_receipt.receipt_id)),
            pending_edge_id="EDGE::MATH-01::MATH-02", producer_invocation_ordinal=0,
            pending_consumer_binding_id=edge_bindings[1].binding_id,
            resolution_state="ORIGINAL_EXTERNAL_INPUTS_RESOLVED_MATH01_RESULT_AND_CONVERSION_PENDING")
        for row, witness in zip(external, external_witnesses, strict=True):
            _require_evidence_resolution_witness_v1(row, witness)
    resolved_witness = _evidence_resolution_witness_v1(resolved)
    owner._check_current_v1(operation)
    _require_evidence_resolution_witness_v1(resolved, resolved_witness)
    _native_require(_EvidenceAssemblyPacketViewV1._require_original_v1(view) is original_view,
                    "LP03_ORIGINAL_INPUT_VIEW_CHANGED")
    return resolved


def _evidence_math39_original_source_resolution_v1(source_slices, *, decision_ns, cutoff_ns):
    """Reconstruct the queue inputs from their two exact original source slices.

    This data function belongs after parent source custody and inside native
    worker validation. It supplies neither a source grant nor an invocation.
    """
    from dataclasses import fields
    from .context import _native_ident, _native_utc_receipt_pair
    from .implementation_registry import _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1
    from .models import EvidenceOriginV1, EvidenceSourceSliceV1

    bindings = CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-39"]
    _native_require(type(decision_ns) is type(cutoff_ns) is int and 0 < cutoff_ns <= decision_ns,
                    "LP03_QUEUE_EXACT_SNAPSHOT_CLOCKS")
    _native_require(type(source_slices) is tuple and len(source_slices) == len(bindings) == 2
        and all(type(part) is EvidenceSourceSliceV1 and part.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
                and len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
                for part in source_slices), "LP03_QUEUE_TWO_ORIGINAL_SOURCE_SLICES")
    events = tuple(part.reconstructed_canonical_events[0] for part in source_slices)
    _native_require(len({part.original_record_refs[0] for part in source_slices}) == 2
        and len({event["producer_receipt_id"] for event in events}) == 2,
        "LP03_QUEUE_DISTINCT_ORIGINAL_RECORDS_AND_RECEIPTS")
    book_event, ack_event = events
    _native_require(all(book_event[name] == ack_event[name]
        for name in ("context_id", "scope", "source_epoch_id", "input_version")),
        "LP03_QUEUE_SHARED_ORIGINAL_CONTEXT")
    _native_require(all(event["ttl_ns"] % 1000 == 0 for event in events), "LP03_QUEUE_ORIGINAL_TTL_REPRESENTABLE")
    shared_ttl = min(event["ttl_ns"] for event in events)
    packets = []

    def projected(ns):
        seconds, remainder = divmod(ns, 1_000_000_000)
        return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds, microseconds=remainder // 1000)

    def read_member(record, schema, times, decimals, source):
        _native_require(type(record) is MappingProxyType
            and set(record) == {member.name for member in fields(schema)}
            and record["producer_receipt_ref"] == source["producer_receipt_id"],
            "LP03_QUEUE_EXACT_TYPED_SOURCE_FIELDS_AND_RECEIPT")
        read = dict(record)
        exact = []
        for field, outer in zip(times, ("observed_time", "available_time"), strict=True):
            wall = _native_utc_receipt_pair(record[field])
            value = int(wall["utc_ns_text"])
            _native_require(0 < value <= source["native_clocks"][outer],
                            "LP03_QUEUE_MEMBER_CLOCK_AFTER_ORIGINAL_OWNER_CLOCK")
            read[field] = projected(value)
            exact.append(value)
        _native_require(exact[0] <= exact[1], "LP03_QUEUE_EXACT_EVENT_AVAILABILITY")
        for field in decimals:
            text = record[field]
            _native_require(type(text) is str and 0 < len(text) <= 64, "LP03_QUEUE_ORIGINAL_DECIMAL_TEXT")
            amount = exact_decimal(text, field_name=field)
            digits = amount.as_tuple()
            _native_require(str(amount) == text and len(digits.digits) <= 34 and -34 <= digits.exponent <= 34,
                            "LP03_QUEUE_ORIGINAL_DECIMAL_BOUND")
            read[field] = amount
        if schema is Math39SequencedBookEventV1:
            _native_require(type(record["sequence"]) is int and 0 <= record["sequence"] < 2**63
                and type(record["event_kind"]) is str and record["event_kind"] in Math39BookEventKindV1._value2member_map_,
                "LP03_QUEUE_ORIGINAL_EVENT_KIND_SEQUENCE")
            read["event_kind"] = Math39BookEventKindV1(record["event_kind"])
        for field, value in read.items():
            if field not in (*times, *decimals, "sequence", "event_kind", "ahead_of_order"):
                _native_ident(value)
        return schema(**read), tuple(exact)

    ack_clock = None
    row_clocks = ()
    books = ()
    for event, binding in zip(events, bindings, strict=True):
        _native_require((event["owner_id"], event["record_kind"], event["schema_id"], event["schema_version"],
            event["producer_receipt_type"], event["source_state_and_claim_lineage"], event["authorized_binding_ids"]) ==
            (binding.accepted_upstream_owner_id, binding.accepted_packet_or_snapshot_type, binding.schema_id,
            binding.schema_version, binding.producer_receipt_type, binding.source_state_and_claim_lineage, (binding.binding_id,))
            and set(event["values"]) == {binding.exact_field_path}, "LP03_QUEUE_ORIGINAL_OWNER_SCHEMA_BINDING")
        clocks = event["native_clocks"]
        _native_require(clocks["as_of_time"] == decision_ns
            and 0 < clocks["effective_time"] <= clocks["observed_time"] <= clocks["available_time"]
            <= clocks["received_time"] <= clocks["processed_time"] <= cutoff_ns
            and 0 <= decision_ns - clocks["observed_time"] <= shared_ttl, "LP03_QUEUE_ORIGINAL_SNAPSHOT_MEMBERS")
        value = event["values"][binding.exact_field_path]
        if binding.input_name == "sequenced_book_events":
            _native_require(type(value) is tuple and 0 < len(value) <= 32, "LP03_QUEUE_ORIGINAL_BOUNDED_EVENT_ROSTER")
            rows = tuple(read_member(row, Math39SequencedBookEventV1,
                ("event_time", "available_at"), ("price", "quantity"), event) for row in value)
            books, row_clocks = zip(*rows, strict=True)
            _native_require(len({row.event_id for row in books}) == len(books)
                and type(event["provider_sequence"]) is int and event["provider_sequence"] == books[-1].sequence,
                "LP03_QUEUE_ORIGINAL_COVERED_SEQUENCE")
            typed = books
        else:
            typed, ack_clock = read_member(value, Math39OrderAcknowledgementV1,
                ("acknowledged_at", "available_at"), ("price",), event)
            _native_require(type(event["revision"]) in (int, str), "LP03_QUEUE_ORIGINAL_ACK_REVISION")
        prior = event["prior_revision_available_wall_ns_or_absence"]
        _native_require(type(prior) is not int or prior <= cutoff_ns, "LP03_QUEUE_ORIGINAL_PRIOR_REVISION_AT_CUTOFF")
        packets.append(OwnerValuePacketV1(packet_id=event["record_ref"], owner_id=event["owner_id"],
            packet_type=event["record_kind"], schema_id=event["schema_id"], schema_version=event["schema_version"],
            context_id=event["context_id"], scope=ComputationScopeV1(**dict(event["scope"])),
            source_epoch_id=event["source_epoch_id"], input_version=event["input_version"],
            clocks=PointInTimeClocksV1(**{name: projected(ns) for name, ns in clocks.items()}),
            ttl=timedelta(microseconds=event["ttl_ns"] // 1000), values={binding.exact_field_path: typed},
            authorized_binding_ids=event["authorized_binding_ids"], producer_receipt_id=event["producer_receipt_id"],
            producer_receipt_type=event["producer_receipt_type"], source_state_and_claim_lineage=event["source_state_and_claim_lineage"],
            provider_sequence=event["provider_sequence"] if type(event["provider_sequence"]) in (int, str) else None,
            revision=event["revision"] if type(event["revision"]) in (int, str) else None,
            prior_revision_available_time=projected(prior) if type(prior) is int else None, source_conflict=False))
    # Check original event/ack order before the public resolver receives the
    # microsecond projections. A one-nanosecond inversion stays observable.
    _native_require(ack_clock is not None and all((clock[0] <= ack_clock[0]
        if row.event_kind is Math39BookEventKindV1.DISPLAYED_BEFORE_ORDER else clock[0] >= ack_clock[0])
        for row, clock in zip(books, row_clocks, strict=True)), "LP03_QUEUE_EXACT_ACK_INSERTION_ORDER")
    first = packets[0]
    context = ComputationExecutionContextV1(context_id=first.context_id, as_of=projected(decision_ns),
        observed_at=projected(decision_ns), source_epoch_id=first.source_epoch_id, input_version=first.input_version,
        maximum_age=min(packet.ttl for packet in packets), scope=first.scope, binding_profile_version="3.4",
        parameter_policy_version="ST12F_PARAMETER_RESOURCE_ROW_V1", implementation_versions=(ImplementationVersionPinV1(
            "MATH-39", _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1["MATH-39"].implementation_id),))
    return resolve_math39_formula_inputs(context=context, owner_registry=CanonicalOwnerPacketRegistryV1(tuple(packets)))


def _evidence_original_timeline_inputs_v1(scope, slices):
    """Reconstruct the signed event roster from the original acquired slices."""
    from hashlib import sha256
    from .models import EvidenceCausalTimelineScopeV1, EvidenceTimelineEventV1, _LP03_PUBLIC_TIMELINE_KINDS_V1
    from .serialization import deterministic_json

    _native_require(type(scope) is EvidenceCausalTimelineScopeV1, "LP03_TIMELINE_ORIGINAL_SCOPE")
    originals = {}
    for part in slices:
        for ref, record in zip(part.original_record_refs, part.reconstructed_canonical_events, strict=True):
            _native_require(ref not in originals and record["record_ref"] == ref.record_id,
                            "LP03_TIMELINE_ORIGINAL_SOURCE_IDENTITY")
            originals[ref] = record
    events = []
    revisions = {}
    for pin in scope.event_pins:
        original = originals.get(pin.source_record_ref)
        _native_require(original is not None and original["record_kind"] == "EvidenceCausalTimelineEventV1"
                        and set(original["values"]) == {"timeline_event"} and original["source_conflict"] is False,
                        "LP03_TIMELINE_ORIGINAL_SOURCE_RECORD")
        event = EvidenceTimelineEventV1.from_canonical_mapping(original["values"]["timeline_event"])
        if event.kind in _LP03_PUBLIC_TIMELINE_KINDS_V1:
            from .evidence_execution import _evidence_timeline_public_candidate_v1

            _native_require(original["owner_id"] == "SelectedVenuePublicMarketDataOwnerV1",
                            "LP03_TIMELINE_ORIGINAL_PUBLIC_OWNER")
            _evidence_timeline_public_candidate_v1(event)
        clocks = original["native_clocks"]
        sequence = original["provider_sequence"]
        order = event.provider_order_or_absence
        _native_require(event.source_record_ref == pin.source_record_ref and event.event_id == pin.event_id
                        and event.local_ordinal == pin.local_ordinal and event.origin is scope.scenario_plan.origin
                        and original["origin"] == event.origin.value and event.connection_epoch == original["source_epoch_id"]
                        and event.source_revision == original["revision"]
                        and (event.availability_wall_ns, event.effective_wall_ns) == (clocks["available_time"], clocks["effective_time"])
                        and (sequence == order[1] if type(order) is tuple else
                             sequence == {"state": "ABSENT_WITH_REASON", "reason": "PROVIDER_SEQUENCE_UNAVAILABLE"})
                        and sha256(deterministic_json(event).encode("utf-8")).hexdigest() == pin.canonical_event_sha256,
                        "LP03_TIMELINE_ORIGINAL_SOURCE_CLOCK_OR_REVISION")
        lineage = (original["owner_id"], original["source_state_and_claim_lineage"], original["context_id"])
        prior = revisions.get(lineage)
        previous_availability = original["prior_revision_available_wall_ns_or_absence"]
        if prior is not None:
            _native_require(event.source_revision > prior.source_revision
                            and prior.availability_wall_ns == previous_availability < event.availability_wall_ns,
                            "LP03_TIMELINE_APPEND_ONLY_SOURCE_REVISION")
        else:
            _native_require(isinstance(previous_availability, Mapping), "LP03_TIMELINE_MISSING_ORIGINAL_PRIOR_REVISION")
        revisions[lineage] = event
        events.append(event)
    for pin in scope.component_input_pins:
        source = originals.get(pin.source_record_ref)
        _native_require(source is not None and source["origin"] == scope.scenario_plan.origin.value
                        and source["source_conflict"] is False
                        and source["native_clocks"]["available_time"] == pin.availability_wall_ns,
                        "LP03_TIMELINE_ORIGINAL_COMPONENT_AVAILABILITY")
    cash_basis = scope.accepted_cash_basis_or_none
    if cash_basis is not None:
        source = originals.get(cash_basis.source_record_ref)
        _native_require(source is not None and source["record_kind"] == "EvidenceSyntheticBaselineV1"
                        and source["owner_id"] == "QKU_COMPUTATION_CONTROL_PLANE" and source["source_conflict"] is False
                        and source["native_clocks"]["available_time"] <= scope.decision_wall_ns[0],
                        "LP03_TIMELINE_ORIGINAL_ACCEPTED_CASH_SOURCE")
        baseline = source["values"]["baseline"]
        _native_require(baseline["cash"] == cash_basis.amount["amount_text"]
                        and baseline["currency"] == cash_basis.amount["currency_or_asset"]
                        and baseline["origin"] == scope.scenario_plan.origin.value,
                        "LP03_TIMELINE_ORIGINAL_ACCEPTED_CASH_BASIS")
    _native_require(all(event.availability_wall_ns <= scope.decision_wall_ns[-1] for event in events),
                    "LP03_TIMELINE_INCOMPLETE_DECISION_SCHEDULE")
    return tuple(events)


def _resolve_evidence_original_inputs_v1(operation, slices):
    """Resolve the ordered original input roster without invoking any formula.

    Route-specific protocol admission remains with the original parameter and
    snapshot owners. A resolved data roster is never execution permission.
    """
    from .implementation_registry import _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1, _LP03_PUBLIC_EVIDENCE_INVOCATION_IDS_V1
    from .persistence import _EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1
    owner = type(operation)
    _native_require(owner in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1), "LP03_ORIGINAL_INPUT_VIEW_OWNER")
    owner._check_current_v1(operation)
    closure = operation.envelope_entry[3].component_closure
    _native_require(type(closure) is tuple and 0 < len(closure) <= 48
                    and len(set(closure)) == len(closure), "LP03_ASSEMBLY_COMPONENT_CLOSURE")
    view = _EvidenceAssemblyPacketViewV1(operation, slices)
    scope = operation.envelope_entry[3].assembly_scope
    seconds, remainder = divmod(scope.snapshot_decision_wall_ns, 1_000_000_000)
    decision = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds, microseconds=remainder // 1000)
    results, witnesses = [], []
    def require_prefix():
        if owner is _EvidenceRegistrationOperationV1:
            attempt = operation.active_attempt
            _native_require(attempt is not None and attempt.invocation_state == "READING_ORIGINAL_INPUTS"
                            and len(attempt.resolution_progress) == len(results)
                            and len(attempt.resolution_witnesses) == len(witnesses)
                            and all(left is right for left, right in zip(attempt.resolution_progress, results))
                            and all(left is right for left, right in zip(attempt.resolution_witnesses, witnesses)),
                            "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
        for resolved, witness in zip(results, witnesses):
            _require_evidence_resolution_witness_v1(resolved, witness)
    for math_id in closure:
        if closure == ("MATH-01", "MATH-02"):
            resolved = _resolve_evidence_probability_edge_component_v1(operation, view, decision, math_id, tuple(results))
        elif math_id == "MATH-39":
            parts = []
            for binding in CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]:
                selected = tuple(part for part in slices
                    if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
                    and binding.binding_id in part.reconstructed_canonical_events[0]["authorized_binding_ids"])
                _native_require(len(selected) == 1, "LP03_QUEUE_ORIGINAL_ASSEMBLY_SOURCE_ROSTER")
                parts.append(selected[0])
            resolved = _evidence_math39_original_source_resolution_v1(tuple(parts),
                decision_ns=scope.snapshot_decision_wall_ns, cutoff_ns=scope.snapshot_pit_cutoff_wall_ns)
            _EvidenceAssemblyPacketViewV1._require_original_v1(view)
        elif math_id == "MATH-26":
            resolved = _resolve_evidence_private26_inputs_v1(operation, view, decision)
        elif math_id == "MATH-27":
            resolved = _resolve_evidence_private27_inputs_v1(operation, view, decision)
        elif math_id == "MATH-28":
            resolved = _resolve_evidence_private28_inputs_v1(operation, view, decision)
        elif math_id in ("MATH-29", "MATH-30", "MATH-31", "MATH-37", "MATH-32", "MATH-33", "MATH-35", "MATH-36", "MATH-38", "MATH-40", "MATH-41", "MATH-42", "MATH-43", "MATH-44", "MATH-45", "MATH-50", "MATH-51", "MATH-52"):
            resolved = _resolve_evidence_original_private_inputs_v1(operation, view, decision, math_id=math_id)
        else:
            if math_id not in _LP03_PUBLIC_EVIDENCE_INVOCATION_IDS_V1 or math_id not in FORMULA_INPUT_AUTHORITY_BY_MATH_ID:
                raise ContractValidationError(ReasonCode.EVIDENCE_INPUT_UNAVAILABLE,
                                              "LP03_ASSEMBLY_ORIGINAL_TYPED_PRODUCER_UNAVAILABLE")
            bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
            selected = tuple(view.packet_for(context=None, binding_id=binding.binding_id) for binding in bindings)
            first = selected[0]
            _native_require(all(packet.source_epoch_id == first.source_epoch_id and packet.input_version == first.input_version
                                and packet.scope == first.scope and packet.context_id == first.context_id for packet in selected),
                            "LP03_ASSEMBLY_FORMULA_CONTEXT_JOIN")
            context = ComputationExecutionContextV1(context_id=first.context_id, as_of=decision, observed_at=decision,
                source_epoch_id=first.source_epoch_id, input_version=first.input_version,
                maximum_age=min(packet.ttl for packet in selected), scope=first.scope,
                binding_profile_version="3.4", parameter_policy_version="ST12F_PARAMETER_RESOURCE_ROW_V1",
                implementation_versions=(ImplementationVersionPinV1(math_id,
                    _LP03_COMPLETE_IMPLEMENTATION_CONTRACTS_V1[math_id].implementation_id),))
            resolved = FormulaInputResolverV1.resolve(math_id, context=context, owner_registry=view)
        witness = _evidence_resolution_witness_v1(resolved)
        require_prefix()
        results.append(resolved)
        witnesses.append(witness)
        if owner is _EvidenceRegistrationOperationV1:
            attempt = operation.active_attempt
            _native_require(attempt is not None and attempt.invocation_state == "READING_ORIGINAL_INPUTS"
                            and len(attempt.resolution_progress) == len(results) - 1
                            and all(left is right for left, right in zip(attempt.resolution_progress, results[:-1])),
                            "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
            # Retain an incomplete prefix on failure. It cannot be reused as
            # a completed input capability or replaced by a retry.
            attempt.resolution_progress = (*attempt.resolution_progress, resolved)
            attempt.resolution_witnesses = (*attempt.resolution_witnesses, witness)
        owner._check_current_v1(operation)
        require_prefix()
    result = tuple(results)
    _native_require(tuple(row.math_spec_id for row in result) == closure,
                    "LP03_ASSEMBLY_RESOLUTION_ROSTER_CHANGED")
    owner._check_current_v1(operation)
    require_prefix()
    return result, tuple(witnesses)


def _evidence_probability_edge_worker_payload_v1(packets, attempt, contracts, *, original_record_refs, frame_byte_limit):
    """Bind a closed pending stack frame to this attempt's original inputs."""
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import EvidenceOriginV1, _evidence_normalized_event_v1, _evidence_probability_edge_chain_sources_v1
    from .serialization import deterministic_json, _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1
    _native_require(type(packets) is tuple and len(packets) == 2
        and all(type(packet) is EvidenceInvocationInputsV1 for packet in packets)
        and type(contracts) is tuple and len(contracts) == 2
        and all(type(contract) is EvidencePrivateInvocationContractV1 for contract in contracts),
        "LP03_EDGE_CHAIN_ORIGINAL_INPUT_AND_CONTRACT_ROSTER")
    resolutions = tuple(EvidenceInvocationInputsV1._require_original_v1(packet, attempt) for packet in packets)
    producer, pending = resolutions
    grant = attempt.payload
    _native_require(type(producer) is FormulaInputResolutionV1 and type(pending) is _EvidencePendingProbabilityEdgeInputsV1
        and producer.math_spec_id == "MATH-01" and pending.math_spec_id == "MATH-02"
        and pending.execution_context is producer.execution_context
        and packets[0]._roster_original is packets[1]._roster_original
        and packets[0]._roster_original[0] is attempt.invocations
        and attempt.invocations == packets and attempt.invocation_state == "EXTERNAL_INPUTS_RESOLVED"
        and grant.component_closure == ("MATH-01", "MATH-02") and not grant.callback_pins
        and attempt.grant_record.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
        and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
        "LP03_EDGE_CHAIN_ORIGINAL_PENDING_STACK")
    pins = grant.component_and_callback_pins["components"]
    _native_require(len(pins) == 2 and tuple(pin[0] for pin in pins) == ("MATH-01", "MATH-02"),
                    "LP03_EDGE_CHAIN_ORIGINAL_CONTRACT_PINS")
    for contract,pin in zip(contracts,pins,strict=True):
        expected = resolve_evidence_invocation_v1(pin[0], implementation_pin=pin[1], specification_pin=pin[2],
            resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
        _native_require(contract == expected, "LP03_EDGE_CHAIN_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs),
                    "LP03_EDGE_CHAIN_ORIGINAL_READ_ROSTER")
    original = packets[0]._roster_original
    canonical = original[3]
    _native_require(type(canonical) is str and 0 < len(canonical) <= frame_byte_limit,
                    "LP03_EDGE_CHAIN_ORIGINAL_SOURCE_BYTE_BOUND")
    source_bytes = 0
    for char in canonical:
        point = ord(char)
        _native_require(not 0xD800 <= point <= 0xDFFF, "LP03_EDGE_CHAIN_SOURCE_UTF8")
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(source_bytes <= frame_byte_limit, "LP03_EDGE_CHAIN_ORIGINAL_SOURCE_BYTE_BOUND")
    slices = _native_strict_json(canonical.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(slices) is list and len(slices) == len(packets[0]._source_slices),
                    "LP03_EDGE_CHAIN_ORIGINAL_SLICE_ROSTER")
    bindings = (*FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-01"],
                FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-02"][0], FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-02"][2])
    resolved_rows = (*producer.inputs, *pending.external_inputs)
    _native_require(len(resolved_rows) == 4, "LP03_EDGE_CHAIN_ORIGINAL_EXTERNAL_ROSTER")
    selected = []
    for resolved,binding in zip(resolved_rows,bindings,strict=True):
        indices = tuple(index for index,part in enumerate(packets[0]._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_EDGE_CHAIN_ORIGINAL_SOURCE_SELECTION")
        index = indices[0];event = packets[0]._source_slices[index].reconstructed_canonical_events[0]
        _native_require((resolved.binding_id,resolved.input_name,resolved.field_path,resolved.owner_id)
            == (binding.binding_id,binding.input_name,binding.exact_field_path,binding.accepted_upstream_owner_id)
            and resolved.producer_receipt_id == event["producer_receipt_id"]
            and event["authorized_binding_ids"] == (binding.binding_id,)
            and event["context_id"] == producer.context_id,
            "LP03_EDGE_CHAIN_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(slices[index])
    source_payload = dict(association_profile="ORIGINAL_SOFTWARE_MARKET_PREDICTION_AND_INDEPENDENT_CALIBRATION_CONTEXT",
        stack_id="STACK::MATH-01::MATH-02::V3_4", edge_id="EDGE::MATH-01::MATH-02", source_slices=selected)
    _evidence_probability_edge_chain_sources_v1(source_payload)
    events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    _native_require(all(event["native_clocks"]["as_of_time"]
        == attempt.registration.envelope_entry[3].assembly_scope.snapshot_decision_wall_ns for event in events),
        "LP03_EDGE_CHAIN_PARENT_EXACT_SNAPSHOT_JOIN")
    market_values = {binding.input_name:_extract(event["values"],binding.exact_field_path)
        for binding,event in zip(bindings[:2],events[:2],strict=True)}
    market_wire = _encode_evidence_projection_json_v1(market_values, maximum_bytes=frame_byte_limit, maximum_nodes=4096)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-EDGE::" + anchor["record_id"], kind="SYNTHETIC_SAME_SNAPSHOT_PROBABILITY_EDGE",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=events[0]["revision"], connection_epoch=events[0]["source_epoch_id"], local_ordinal=0, payload=source_payload)
    normalized = _evidence_normalized_event_v1(event)
    contract_data = tuple(_evidence_canonical_object_v1(deterministic_json(contract).encode("utf-8")) for contract in contracts)
    payload = dict(segment_ordinal=0, final_segment=True,
        inputs=dict(market_input_json=market_wire.decode("utf-8"), model_input_json=pending.model_input_json,
                    execution_context_json=deterministic_json(producer.execution_context),
                    conversion_receipt_id=grant.grant_ref + "::CONVERSION"),
        original_record_refs=refs, event=event, producer_invocation_contract=contract_data[0], invocation_contract=contract_data[1])
    from .evidence_execution import WORKER_PROTOCOL_V1, encode_evidence_worker_frame_v1, _worker_probability_edge_inputs_v1
    _worker_probability_edge_inputs_v1(payload, normalized, attempt_ref=grant.grant_ref)
    # Exact bounded prospective frame, with this attempt's real identifiers.
    # Preparing it performs no write or numerical invocation.
    encode_evidence_worker_frame_v1(dict(protocol=WORKER_PROTOCOL_V1, kind="INPUT_SEGMENT",
        attempt_ref=grant.grant_ref, fence_ref=grant.fence_ref, ordinal=1, payload=payload),
        direction="PARENT_TO_WORKER", attempt_ref=grant.grant_ref, fence_ref=grant.fence_ref,
        ordinal=1, frame_byte_limit=frame_byte_limit)
    _native_require(packets[0]._roster_original is original and packets[1]._roster_original is original,
                    "LP03_EDGE_CHAIN_ORIGINAL_ROSTER_CHANGED")
    for packet in packets:EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized


def _require_evidence_probability_edge_result_v1(packets, attempt, contracts, result, *, original_record_refs, frame_byte_limit):
    """Join the original worker data to the admitted pending source graph."""
    from .evidence_execution import _worker_probability_edge_result_v1, _worker_probability_edge_clock_limits_v1
    from .serialization import deterministic_json, _native_strict_json, _evidence_canonical_object_v1
    from .models import EvidenceAuthorizationMessageV1
    # This reconstructs only the bounded external input frame. It invokes no
    # formula/converter and cannot fill the pending dependency by recomputation.
    expected, normalized = _evidence_probability_edge_worker_payload_v1(packets, attempt, contracts,
        original_record_refs=original_record_refs, frame_byte_limit=frame_byte_limit)
    _native_require(deterministic_json(result["producer_invocation_contract"])
        == deterministic_json(expected["producer_invocation_contract"])
        and deterministic_json(result["invocation_contract"]) == deterministic_json(expected["invocation_contract"])
        and deterministic_json(result["original_record_refs"]) == deterministic_json(original_record_refs)
        and result["event_ordinal"] == 0, "LP03_EDGE_CHAIN_PARENT_RESULT_CONTRACT_JOIN")
    artifact = _worker_probability_edge_result_v1(result, attempt_ref=attempt.payload.grant_ref)
    _native_require("execution_clock_limits" in artifact, "LP03_EDGE_CHAIN_PARENT_CLOCK_LIMITS_REQUIRED")
    message = EvidenceAuthorizationMessageV1.from_canonical_mapping(_evidence_canonical_object_v1(
        attempt.grant_record.signed_grant.canonical_message.encode("utf-8")))
    horizon = normalized["payload"]["source_slices"][0]["reconstructed_canonical_events"][0]["values"]["contract_context"]["horizon_end_wall_ns"]
    _native_require(message.exclusive_expiry_wall_ns <= horizon,
                    "LP03_EDGE_CHAIN_PARENT_GRANT_SOURCE_HORIZON")
    bounds = (message.valid_from_wall_ns, min(message.exclusive_expiry_wall_ns,horizon),
        attempt.payload.deadline.admitted_monotonic_ns, attempt.payload.deadline.exclusive_deadline_monotonic_ns)
    _native_require(_worker_probability_edge_clock_limits_v1(artifact["execution_clock_limits"]) == bounds
        and artifact["producer_input_json"] == expected["inputs"]["market_input_json"],
        "LP03_EDGE_CHAIN_PARENT_ORIGINAL_INPUT_LIMIT_JOIN")
    consumer = _native_strict_json(artifact["consumer_input_json"].encode("utf-8"), max_bytes=frame_byte_limit,
                                  max_nodes=4096, binary64_numbers=True)
    model = _native_strict_json(expected["inputs"]["model_input_json"].encode("utf-8"), max_bytes=frame_byte_limit,
                               max_nodes=4096, binary64_numbers=True)
    _native_require(deterministic_json({name:consumer[name] for name in model}) == deterministic_json(model),
                    "LP03_EDGE_CHAIN_PARENT_MODEL_BITS_JOIN")
    receipt = _native_strict_json(artifact["conversion_receipt_json"].encode("utf-8"), max_bytes=frame_byte_limit,
                                 max_nodes=4096, binary64_numbers=True)
    _native_require(receipt["receipt_id"] == expected["inputs"]["conversion_receipt_id"]
        and deterministic_json(receipt["execution_context"]) == expected["inputs"]["execution_context_json"],
        "LP03_EDGE_CHAIN_PARENT_ORIGINAL_CONTEXT_JOIN")
    for packet in packets:
        EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return artifact


def _evidence_cashflow_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Prepare the closed cashflow frame from original pinned source bytes only."""
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import deterministic_json, _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    math_id = resolution.math_spec_id
    _native_require(math_id in ("MATH-06", "MATH-07") and grant.component_closure == (math_id,)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_CASHFLOW_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected = resolve_evidence_invocation_v1(math_id, implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected), "LP03_CASHFLOW_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_CASHFLOW_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_CASHFLOW_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(source_bytes <= frame_byte_limit, "LP03_CASHFLOW_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_CASHFLOW_ORIGINAL_SLICE_ROSTER")
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_CASHFLOW_ORIGINAL_RESOLUTION_ORDER")
    selected, native_inputs = [], {}
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_CASHFLOW_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        event = packet._source_slices[index].reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"] and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_CASHFLOW_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
        native_inputs[binding.input_name] = _extract(wire_slices[index]["reconstructed_canonical_events"][0]["values"], binding.exact_field_path)
    input_bytes = _encode_evidence_projection_json_v1(native_inputs,
        maximum_bytes=frame_byte_limit, maximum_nodes=4096)
    typed = decode_evidence_public_invocation_inputs_v1(math_id, input_bytes, maximum_bytes=frame_byte_limit, maximum_nodes=4096)
    _native_require(deterministic_json(typed) == deterministic_json(resolution.authoritative_values),
                    "LP03_CASHFLOW_ORIGINAL_TYPED_VALUE_JOIN")
    contract_bytes = deterministic_json(contract).encode("utf-8")
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, native_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_CASHFLOW_FRAME_NODE_CAPACITY")
    events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-CASHFLOW::" + anchor["record_id"], kind="SYNTHETIC_SIGNED_TOTAL_CASHFLOW_CONTEXT",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=events[0]["revision"], connection_epoch=events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="ORIGINAL_SOFTWARE_SIGNED_TOTAL_CASHFLOW_CONTEXT", math_id=math_id, source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=native_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    from .evidence_execution import WORKER_PROTOCOL_V1,_worker_cashflow_inputs_v1,encode_evidence_worker_frame_v1
    _worker_cashflow_inputs_v1(payload, normalized)
    # Preflight the complete actual frame under the unchanged byte/node limit.
    # Every source field is retained; no native invocation or write occurs here.
    bounded_frame = encode_evidence_worker_frame_v1(dict(protocol=WORKER_PROTOCOL_V1,kind="INPUT_SEGMENT",
        attempt_ref=grant.grant_ref,fence_ref=grant.fence_ref,ordinal=1,payload=payload),
        direction="PARENT_TO_WORKER",attempt_ref=grant.grant_ref,fence_ref=grant.fence_ref,ordinal=1,
        frame_byte_limit=frame_byte_limit)
    _native_require(len(bounded_frame) <= frame_byte_limit + 4,"LP03_CASHFLOW_FRAME_CAPACITY")
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized


def _evidence_market_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Prepare the closed market frame from original pinned source bytes only."""
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import deterministic_json, _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    math_id = resolution.math_spec_id
    _native_require(math_id in ("MATH-01", "MATH-04", "MATH-05") and grant.component_closure == (math_id,)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_MARKET_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected = resolve_evidence_invocation_v1(math_id, implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected), "LP03_MARKET_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_MARKET_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_MARKET_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(2 * source_bytes + 4096 <= frame_byte_limit, "LP03_MARKET_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_MARKET_ORIGINAL_SLICE_ROSTER")
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_MARKET_ORIGINAL_RESOLUTION_ORDER")
    selected, native_inputs = [], {}
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_MARKET_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        event = packet._source_slices[index].reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"] and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_MARKET_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
        native_inputs[binding.input_name] = _extract(wire_slices[index]["reconstructed_canonical_events"][0]["values"], binding.exact_field_path)
    input_bytes = _encode_evidence_projection_json_v1(native_inputs,
        maximum_bytes=frame_byte_limit - 2 * source_bytes - 4096, maximum_nodes=4096)
    typed = decode_evidence_public_invocation_inputs_v1(math_id, input_bytes, maximum_bytes=frame_byte_limit, maximum_nodes=4096)
    _native_require(deterministic_json(typed) == deterministic_json(resolution.authoritative_values),
                    "LP03_MARKET_ORIGINAL_TYPED_VALUE_JOIN")
    contract_bytes = deterministic_json(contract).encode("utf-8")
    _native_require(2 * source_bytes + len(input_bytes) + len(contract_bytes) + 4096 <= frame_byte_limit,
                    "LP03_MARKET_FRAME_CAPACITY")
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, native_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_MARKET_FRAME_NODE_CAPACITY")
    events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-MARKET::" + anchor["record_id"], kind="SYNTHETIC_MARKET_PRICE_CONTEXT",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=events[0]["revision"], connection_epoch=events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="SHARED_ORIGINAL_MARKET_AND_PAYOUT_CONTEXT", math_id=math_id, source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=native_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    from .evidence_execution import _worker_market_inputs_v1
    _worker_market_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized


def _evidence_kelly27_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Prepare the closed M27 frame from original pinned source bytes only."""
    from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import deterministic_json, _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    _native_require(resolution.math_spec_id == "MATH-27" and grant.component_closure == ("MATH-27",)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_KELLY27_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected = resolve_evidence_invocation_v1("MATH-27", implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected), "LP03_KELLY27_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_KELLY27_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_KELLY27_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(2 * source_bytes + 4096 <= frame_byte_limit, "LP03_KELLY27_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_KELLY27_ORIGINAL_SLICE_ROSTER")
    bindings = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-27"].bindings
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_KELLY27_ORIGINAL_RESOLUTION_ORDER")
    selected, native_inputs = [], {}
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_KELLY27_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        event = packet._source_slices[index].reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"] and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_KELLY27_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
        native_inputs[binding.input_name] = wire_slices[index]["reconstructed_canonical_events"][0]["values"][binding.input_name]
    input_bytes = _encode_evidence_projection_json_v1(native_inputs,
        maximum_bytes=frame_byte_limit - 2 * source_bytes - 4096, maximum_nodes=4096)
    typed = decode_evidence_private_inputs_v1("MATH-27", input_bytes, maximum_bytes=frame_byte_limit, maximum_nodes=4096)
    _native_require(deterministic_json(typed) == deterministic_json(resolution.authoritative_values),
                    "LP03_KELLY27_ORIGINAL_TYPED_VALUE_JOIN")
    contract_bytes = deterministic_json(contract).encode("utf-8")
    _native_require(2 * source_bytes + len(input_bytes) + len(contract_bytes) + 4096 <= frame_byte_limit,
                    "LP03_KELLY27_FRAME_CAPACITY")
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, native_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_KELLY27_FRAME_NODE_CAPACITY")
    events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-KELLY27::" + anchor["record_id"], kind="SYNTHETIC_KELLY_PROBABILITY_PAYOFF_CONTEXT",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=events[0]["revision"], connection_epoch=events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="SHARED_ORIGINAL_KELLY_PROBABILITY_PAYOFF_CONTEXT", source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=native_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    from .evidence_execution import _worker_kelly27_inputs_v1
    _worker_kelly27_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized



def _evidence_kelly28_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Frame only the three original selected slices, within the admitted bound."""
    from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import deterministic_json, _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    _native_require(resolution.math_spec_id == "MATH-28" and grant.component_closure == ("MATH-28",)
        and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
        and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
        "LP03_KELLY28_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected = resolve_evidence_invocation_v1("MATH-28", implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected), "LP03_KELLY28_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
        for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_KELLY28_ORIGINAL_READ_ROSTER")
    bindings = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-28"].bindings
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_KELLY28_ORIGINAL_RESOLUTION_ORDER")
    selected_entries = []
    for resolved, binding in zip(resolution.inputs, bindings, strict=True):
        entries = tuple(entry for entry in packet._roster_original[7]
            if len(entry[3].original_record_refs) == len(entry[3].reconstructed_canonical_events) == 1
            and entry[3].original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(entries) == 1, "LP03_KELLY28_ORIGINAL_SOURCE_SLICE")
        entry = entries[0]
        event = entry[3].reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
            and resolved.producer_receipt_id == event["producer_receipt_id"] and resolved.owner_id == event["owner_id"]
            and event["context_id"] == resolution.context_id and event["authorized_binding_ids"] == (binding.binding_id,)
            and type(resolved.point_in_time_receipt) is _EvidenceHistoricalInputReceiptV1,
            "LP03_KELLY28_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected_entries.append(entry)
    # Acquisition already retained exact bounded canonical bytes. Check their
    # aggregate before decoding; unrelated policy slices are not worker inputs.
    _native_require(all(type(entry[5]) is bytes for entry in selected_entries)
        and sum(len(entry[5]) for entry in selected_entries) + 4096 <= frame_byte_limit,
        "LP03_KELLY28_FRAME_CAPACITY")
    source_texts = tuple(entry[5].decode("utf-8", "strict") for entry in selected_entries)
    source_events = tuple(entry[3].reconstructed_canonical_events[0] for entry in selected_entries)
    native = {binding.input_name: event["values"][binding.input_name]
        for binding, event in zip(bindings, source_events, strict=True)}
    input_bytes = _encode_evidence_projection_json_v1(native, maximum_bytes=frame_byte_limit, maximum_nodes=4096)
    typed = decode_evidence_private_inputs_v1("MATH-28", input_bytes, maximum_bytes=frame_byte_limit, maximum_nodes=4096)
    _native_require(deterministic_json(typed) == deterministic_json(resolution.authoritative_values),
                    "LP03_KELLY28_ORIGINAL_TYPED_VALUE_JOIN")
    scope = attempt.registration.envelope_entry[3].assembly_scope
    for resolved in resolution.inputs:
        proof = resolved.point_in_time_receipt
        _native_require(proof.consumer_decision_wall_ns == scope.snapshot_decision_wall_ns
            and proof.consumer_cutoff_wall_ns == scope.snapshot_pit_cutoff_wall_ns,
            "LP03_KELLY28_ORIGINAL_CONSUMER_CLOCK_JOIN")
    anchor_ref = selected_entries[0][3].original_record_refs[0]
    anchor = dict(store_id=anchor_ref.store_id, record_id=anchor_ref.record_id)
    event = dict(event_id="LP03-KELLY28::" + anchor["record_id"], kind="SYNTHETIC_FRACTIONAL_KELLY_CONTEXT",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in source_events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in source_events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=source_events[0]["revision"], connection_epoch=source_events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="ORIGINAL_PUBLISHED_KELLY_AND_CURRENT_CONSTRAINTS", source_slice_jsons=source_texts,
            consumer_decision_wall_ns=scope.snapshot_decision_wall_ns, consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns))
    payload = dict(segment_ordinal=0, final_segment=True, inputs=native, original_record_refs=refs,
        event=event, invocation_contract=_evidence_canonical_object_v1(deterministic_json(contract).encode("utf-8")))
    # The existing bounded encoder counts the entire selected payload, including
    # all nested historical provenance, before producing its wire representation.
    _encode_evidence_projection_json_v1(payload, maximum_bytes=frame_byte_limit - 4096, maximum_nodes=4096 - 128)
    normalized = _evidence_normalized_event_v1(event)
    from .evidence_execution import _worker_kelly28_inputs_v1
    _worker_kelly28_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized



def _evidence_research_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Prepare the closed M26 frame from original pinned source bytes only."""
    from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import deterministic_json, _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    _native_require(resolution.math_spec_id == "MATH-26" and grant.component_closure == ("MATH-26",)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_RESEARCH_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected = resolve_evidence_invocation_v1("MATH-26", implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected), "LP03_RESEARCH_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_RESEARCH_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_RESEARCH_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(2 * source_bytes + 4096 <= frame_byte_limit, "LP03_RESEARCH_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_RESEARCH_ORIGINAL_SLICE_ROSTER")
    bindings = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1["MATH-26"].bindings
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_RESEARCH_ORIGINAL_RESOLUTION_ORDER")
    selected, native_inputs = [], {}
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_RESEARCH_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        event = packet._source_slices[index].reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"] and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_RESEARCH_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
        native_inputs[binding.input_name] = wire_slices[index]["reconstructed_canonical_events"][0]["values"][binding.input_name]
    input_bytes = _encode_evidence_projection_json_v1(native_inputs,
        maximum_bytes=frame_byte_limit - 2 * source_bytes - 4096, maximum_nodes=4096)
    typed = decode_evidence_private_inputs_v1("MATH-26", input_bytes, maximum_bytes=frame_byte_limit, maximum_nodes=4096)
    _native_require(deterministic_json(typed) == deterministic_json(resolution.authoritative_values),
                    "LP03_RESEARCH_ORIGINAL_TYPED_VALUE_JOIN")
    contract_bytes = deterministic_json(contract).encode("utf-8")
    _native_require(2 * source_bytes + len(input_bytes) + len(contract_bytes) + 4096 <= frame_byte_limit,
                    "LP03_RESEARCH_FRAME_CAPACITY")
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, native_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_RESEARCH_FRAME_NODE_CAPACITY")
    events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-RESEARCH::" + anchor["record_id"], kind="SYNTHETIC_RESEARCH_DECISION",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=events[0]["revision"], connection_epoch=events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="SHARED_ORIGINAL_RESEARCH_DECISION_CONTEXT", source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=native_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    from .evidence_execution import _worker_research_inputs_v1
    _worker_research_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized


def _evidence_forecast_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Build one bounded native-data frame from the retained original roster.

    Canonical slice bytes were pinned by original resolution. Reconstructing
    their data here cannot mint source custody: both original witness checks
    and the exact source-to-resolution association are required independently.
    """
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1, deterministic_json
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    _native_require(resolution.math_spec_id == "MATH-08" and grant.component_closure == ("MATH-08",)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_FORECAST_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected_contract = resolve_evidence_invocation_v1("MATH-08", implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected_contract), "LP03_FORECAST_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_FORECAST_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    # The complete already-pinned roster is a conservative byte bound for the
    # two selected slices and the separately repeated original-reference list.
    # Count UTF-8 bytes before allocating its encoded copy or parsed data.
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_FORECAST_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(2 * source_bytes + 4096 <= frame_byte_limit, "LP03_FORECAST_FRAME_CAPACITY")
    input_body = dict(resolution.authoritative_values)
    input_bytes = _encode_evidence_projection_json_v1(input_body,
        maximum_bytes=frame_byte_limit - 2 * source_bytes - 4096, maximum_nodes=4096)
    contract_bytes = deterministic_json(contract).encode("utf-8")
    _native_require(2 * source_bytes + len(input_bytes) + len(contract_bytes) + 4096 <= frame_byte_limit,
                    "LP03_FORECAST_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_FORECAST_ORIGINAL_SLICE_ROSTER")
    selected = []
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-08"]
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_FORECAST_ORIGINAL_RESOLUTION_ORDER")
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_FORECAST_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        part = packet._source_slices[index]
        event = part.reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"]
                        and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id
                        and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_FORECAST_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
    wire_inputs = _native_strict_json(input_bytes, max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=True)
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, wire_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_FORECAST_FRAME_NODE_CAPACITY")
    source_events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-FORECAST::" + anchor["record_id"], kind="SYNTHETIC_FORECAST_EVALUATION_BATCH",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in source_events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in source_events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=source_events[0]["revision"], connection_epoch=source_events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="SHARED_ORIGINAL_DATASET_CONTEXT",
            row_identity_profile="ORDERED_SYNTHETIC_ROWS_NO_SAMPLE_IDS", source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=wire_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    # Pure protocol validation includes the typed source/value join. This does
    # not launch or dispatch the frame; SVC still owns currentness and effects.
    from .evidence_execution import _worker_brier_inputs_v1
    _worker_brier_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized

def _evidence_log_loss_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Build one bounded native-data frame from the retained original roster.

    Canonical slice bytes were pinned by original resolution. Reconstructing
    their data here cannot mint source custody: both original witness checks
    and the exact source-to-resolution association are required independently.
    """
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1, deterministic_json
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    _native_require(resolution.math_spec_id == "MATH-09" and grant.component_closure == ("MATH-09",)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_LOG_LOSS_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected_contract = resolve_evidence_invocation_v1("MATH-09", implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected_contract), "LP03_LOG_LOSS_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_LOG_LOSS_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    # The complete already-pinned roster is a conservative byte bound for the
    # three selected slices and the separately repeated original-reference list.
    # Count UTF-8 bytes before allocating its encoded copy or parsed data.
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_LOG_LOSS_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(2 * source_bytes + 4096 <= frame_byte_limit, "LP03_LOG_LOSS_FRAME_CAPACITY")
    input_body = dict(resolution.authoritative_values)
    input_bytes = _encode_evidence_projection_json_v1(input_body,
        maximum_bytes=frame_byte_limit - 2 * source_bytes - 4096, maximum_nodes=4096)
    contract_bytes = deterministic_json(contract).encode("utf-8")
    _native_require(2 * source_bytes + len(input_bytes) + len(contract_bytes) + 4096 <= frame_byte_limit,
                    "LP03_LOG_LOSS_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_LOG_LOSS_ORIGINAL_SLICE_ROSTER")
    selected = []
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-09"]
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_LOG_LOSS_ORIGINAL_RESOLUTION_ORDER")
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_LOG_LOSS_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        part = packet._source_slices[index]
        event = part.reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"]
                        and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id
                        and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_LOG_LOSS_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
    wire_inputs = _native_strict_json(input_bytes, max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=True)
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, wire_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_LOG_LOSS_FRAME_NODE_CAPACITY")
    source_events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-LOG-LOSS::" + anchor["record_id"], kind="SYNTHETIC_LOG_LOSS_EVALUATION_BATCH",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in source_events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in source_events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=source_events[0]["revision"], connection_epoch=source_events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="SHARED_ORIGINAL_DATASET_AND_CLIP_POLICY_CONTEXT",
            row_identity_profile="ORDERED_SYNTHETIC_ROWS_NO_SAMPLE_IDS", source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=wire_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    # Pure protocol validation includes the typed source/value join. This does
    # not launch or dispatch the frame; SVC still owns currentness and effects.
    from .evidence_execution import _worker_log_loss_inputs_v1
    _worker_log_loss_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized


def _evidence_math39_queue_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Join exact frozen original reads, public contract, and resolved queue terms."""
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_math39_queue_source_data_v1, _evidence_normalized_event_v1
    from .serialization import _encode_evidence_projection_json_v1, _native_strict_json, deterministic_json

    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    registration, grant = attempt.registration, attempt.payload
    _native_require(type(resolution) is FormulaInputResolutionV1 and resolution.math_spec_id == "MATH-39"
        and type(contract) is EvidencePrivateInvocationContractV1 and grant.component_closure == ("MATH-39",)
        and not grant.callback_pins and registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_PRIVATE_DECIMAL_EXECUTION_CONFORMANCE_V1"
        and type(frame_byte_limit) is int and 4096 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
        "LP03_QUEUE_ORIGINAL_ATTEMPT_PROFILE")
    pin, = grant.component_and_callback_pins["components"]
    expected = resolve_evidence_invocation_v1("MATH-39", implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(pin[0] == "MATH-39" and contract == expected,
                    "LP03_QUEUE_ORIGINAL_ATTEMPT_PUBLIC_CONTRACT")
    refs = tuple(dict(store_id=ref.store_id, record_id=ref.record_id)
        for part in packet._source_slices for ref in part.original_record_refs)
    _native_require(deterministic_json(refs) == deterministic_json(original_record_refs)
        and resolution.packet_refs == registration.protocol.coverage_eligibility["source_record_refs"],
        "LP03_QUEUE_ORIGINAL_READ_ROSTER")
    selected = []
    bindings = CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-39"]
    for source_ref, binding in zip(resolution.packet_refs, bindings, strict=True):
        matches = tuple(row for row in packet._roster_original[7]
            if len(row[3].original_record_refs) == len(row[3].reconstructed_canonical_events) == 1
            and row[3].original_record_refs[0].record_id == source_ref)
        _native_require(len(matches) == 1, "LP03_QUEUE_ORIGINAL_ATTEMPT_SOURCE_SLICE")
        row, = matches
        part = row[3]
        ref, = part.original_record_refs
        event, = part.reconstructed_canonical_events
        permissions = tuple(item for item in grant.allowed_reads if item.original_store_id == ref.store_id
            and item.selection.record_refs == (ref.record_id,))
        _native_require(len(permissions) == 1 and permissions[0].original_owner_id == event["owner_id"]
            == binding.accepted_upstream_owner_id and permissions[0].allowed_fields == (binding.exact_field_path,)
            and permissions[0].required_original_rights_refs == part.rights_refs,
            "LP03_QUEUE_ORIGINAL_ATTEMPT_SOURCE_RIGHTS")
        selected.append(row)
    _native_require(all(type(row[5]) is bytes for row in selected)
        and sum(len(row[5]) for row in selected) <= frame_byte_limit-4096,
        "LP03_QUEUE_ORIGINAL_FRAME_SOURCE_CAPACITY")
    scope = registration.envelope_entry[3].assembly_scope
    source = dict(profile="ORIGINAL_SOFTWARE_ACKNOWLEDGED_QUEUE_INPUTS_V1", math_id="MATH-39",
        decision_wall_ns=scope.snapshot_decision_wall_ns, cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns,
        source_slices=tuple(_native_strict_json(row[5], max_bytes=frame_byte_limit, max_nodes=4096) for row in selected))
    parts, rederived = _evidence_math39_queue_source_data_v1(source)
    _native_require(deterministic_json(rederived) == deterministic_json(resolution),
                    "LP03_QUEUE_ORIGINAL_WORKER_RESOLUTION_JOIN")
    events = tuple(part.reconstructed_canonical_events[0] for part in parts)
    anchor = parts[0].original_record_refs[0]
    event = dict(event_id="LP03-QUEUE::"+anchor.record_id, kind="SYNTHETIC_ACKNOWLEDGED_QUEUE", origin=scope.origin.value,
        source_record_ref=dict(store_id=anchor.store_id, record_id=anchor.record_id),
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=events[0]["revision"], connection_epoch=events[0]["source_epoch_id"], local_ordinal=0,
        payload=source)
    wire = _encode_evidence_projection_json_v1(dict(segment_ordinal=0, final_segment=True, event=event,
        original_record_refs=refs, inputs={key:str(value) for key,value in resolution.authoritative_values.items()},
        invocation_contract=_native_strict_json(deterministic_json(contract).encode("utf-8", "strict"),
            max_bytes=frame_byte_limit, max_nodes=128)), maximum_bytes=frame_byte_limit-1024, maximum_nodes=4016)
    frame = _native_strict_json(wire, max_bytes=frame_byte_limit, max_nodes=4096)
    normalized = _evidence_normalized_event_v1(frame["event"])
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return frame, normalized


def _evidence_original_private_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Frame the selected original private arguments and their owner slices."""
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import (_evidence_normalized_event_v1, _evidence_original_private_input_profile_v1,
        _evidence_original_private_inputs_v1)
    from .serialization import _encode_evidence_projection_json_v1, _native_strict_json, deterministic_json

    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    registration, grant = attempt.registration, attempt.payload
    math_id = resolution.math_spec_id
    source_profile, event_profile, registration_profile = _evidence_original_private_input_profile_v1(math_id)
    _native_require(math_id in ("MATH-29", "MATH-30", "MATH-31", "MATH-37", "MATH-32", "MATH-33", "MATH-35", "MATH-36", "MATH-38", "MATH-40", "MATH-41", "MATH-42", "MATH-43", "MATH-44", "MATH-45", "MATH-50", "MATH-51", "MATH-52")
        and type(contract) is EvidencePrivateInvocationContractV1
        and grant.component_closure == (math_id,) and not grant.callback_pins
        and registration.protocol.analysis_profile == registration_profile
        and type(frame_byte_limit) is int and 4096 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
        "LP03_ANALYTIC_PRIVATE_ORIGINAL_INVOCATION_PROFILE")
    pin, = grant.component_and_callback_pins["components"]
    expected = resolve_evidence_invocation_v1(math_id, implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected), "LP03_ANALYTIC_PRIVATE_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=ref.store_id, record_id=ref.record_id)
        for part in packet._source_slices for ref in part.original_record_refs)
    _native_require(deterministic_json(refs) == deterministic_json(original_record_refs),
        "LP03_ANALYTIC_PRIVATE_ORIGINAL_READ_ROSTER")
    source_ids = tuple(row.packet_id for row in resolution.inputs)
    _native_require(source_ids == registration.protocol.coverage_eligibility["source_record_refs"],
        "LP03_ANALYTIC_PRIVATE_ORIGINAL_REGISTERED_SOURCE_REFS")
    selected = []
    for row in resolution.inputs:
        matches = tuple(item for item in packet._roster_original[7]
            if len(item[3].original_record_refs) == len(item[3].reconstructed_canonical_events) == 1
            and item[3].original_record_refs[0].record_id == row.packet_id)
        _native_require(len(matches) == 1, "LP03_ANALYTIC_PRIVATE_ORIGINAL_SOURCE_SLICE")
        match, = matches
        part = match[3]
        event, = part.reconstructed_canonical_events
        ref, = part.original_record_refs
        permissions = tuple(read for read in grant.allowed_reads if read.original_store_id == ref.store_id
            and read.selection.record_refs == (ref.record_id,))
        _native_require(len(permissions) == 1 and permissions[0].original_owner_id == row.owner_id == event["owner_id"]
            and row.producer_receipt_id == event["producer_receipt_id"]
            and event["authorized_binding_ids"] == (row.binding_id,)
            and permissions[0].required_original_rights_refs == part.rights_refs
            and set(permissions[0].allowed_fields) == set(event["values"]),
            "LP03_ANALYTIC_PRIVATE_ORIGINAL_SCOPED_RIGHTS")
        selected.append(match)
    _native_require(all(type(item[5]) is bytes for item in selected)
        and sum(len(item[5]) for item in selected) <= frame_byte_limit - 4096,
        "LP03_ANALYTIC_PRIVATE_FRAME_SOURCE_CAPACITY")
    events = tuple(item[3].reconstructed_canonical_events[0] for item in selected)
    scope = registration.envelope_entry[3].assembly_scope
    source_payload = dict(profile=source_profile, math_id=math_id,
        decision_wall_ns=scope.snapshot_decision_wall_ns, cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns,
        source_slices=tuple(_native_strict_json(item[5], max_bytes=frame_byte_limit, max_nodes=4096) for item in selected))
    parts, inputs, source_scope = _evidence_original_private_inputs_v1(source_payload, math_id=math_id)
    _native_require(deterministic_json(inputs) == deterministic_json(resolution.authoritative_values)
        and (source_scope["unit"], source_scope["basis"]) == (
            registration.protocol.numeric_profile["output_unit"], registration.protocol.numeric_profile["output_basis"]),
        "LP03_ANALYTIC_PRIVATE_ORIGINAL_INPUT_ASSOCIATION")
    available = max(row["native_clocks"]["available_time"] for row in events)
    if math_id == "MATH-41":
        fact = events[0]["values"]["original_execution_context"]["original_fact"]
        available = max(available, fact["bridge_visibility_observation"][0])
    quantum = math_id in ("MATH-50", "MATH-51", "MATH-52")
    if quantum:
        from .models import _evidence_quantum_original_lock_pins_v1

        lock = registration.compilation.input_lock
        pins = _evidence_quantum_original_lock_pins_v1(grant.component_and_callback_pins["quantum_original_lock"],
            basis=source_scope["original_economic_basis"])
        _native_require(source_scope["original_lock_id"] == grant.input_lock_ref == lock.input_lock_id
            and pins["scenario_set_ref"] == lock.scenario_set_id
            and pins["source_epoch_pairs"] == tuple(sorted(lock.source_epochs.items())),
            "LP03_QUANTUM_ORIGINAL_BOUND_LOCK")
    anchor = parts[0].original_record_refs[0]
    event = dict(event_id=("LP03-PRIVATE-ANALYTIC::" if event_profile == "SYNTHETIC_PRIVATE_ANALYTIC_INPUT"
        else "LP03-PRIVATE-EXECUTION::") + anchor.record_id, kind=event_profile,
        origin=scope.origin.value, source_record_ref=dict(store_id=anchor.store_id, record_id=anchor.record_id),
        availability_wall_ns=available,
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=events[0]["revision"], connection_epoch=events[0]["source_epoch_id"], local_ordinal=0,
        payload=source_payload)
    binary64 = math_id in ("MATH-41", "MATH-42", "MATH-43", "MATH-44")
    original_inputs = inputs if binary64 or quantum else {
        row.input_name: record["values"][row.field_path if math_id == "MATH-36" else row.input_name]
        for row, record in zip(resolution.inputs, events, strict=True)}
    input_wire = _native_strict_json(deterministic_json(original_inputs).encode("utf-8"),
        max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=binary64)
    contract_wire = _native_strict_json(deterministic_json(contract).encode("utf-8"),
        max_bytes=frame_byte_limit, max_nodes=128)
    frames = dict(segment_ordinal=0, final_segment=True, event=event, original_record_refs=refs,
        inputs=input_wire, invocation_contract=contract_wire)
    wire = _encode_evidence_projection_json_v1(frames, maximum_bytes=frame_byte_limit - 1024, maximum_nodes=4016)
    frames = _native_strict_json(wire, max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=binary64)
    normalized = _evidence_normalized_event_v1(frames["event"])
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return frames, normalized


def _evidence_recorded_ope_point_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Build one native input frame over the original selected point sources."""
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1, _evidence_recorded_ope_source_data_v1
    from .serialization import _evidence_canonical_object_v1, _encode_evidence_projection_json_v1, _native_strict_json, deterministic_json

    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    registration, grant = attempt.registration, attempt.payload
    math_id = resolution.math_spec_id
    _native_require(math_id in ("MATH-23", "MATH-24", "MATH-25")
        and type(contract) is EvidencePrivateInvocationContractV1
        and grant.component_closure == (math_id,) and not grant.callback_pins
        and registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_RECORDED_OPE_POINT_CONFORMANCE_V1"
        and type(frame_byte_limit) is int and 1024 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
        "LP03_OPE_POINT_ORIGINAL_INVOCATION_PROFILE")
    pin, = grant.component_and_callback_pins["components"]
    expected = resolve_evidence_invocation_v1(math_id, implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(expected) == deterministic_json(contract), "LP03_OPE_POINT_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=part.store_id, record_id=part.record_id) for item in packet._source_slices
        for part in item.original_record_refs)
    _native_require(deterministic_json(refs) == deterministic_json(original_record_refs),
        "LP03_OPE_POINT_ORIGINAL_READ_ROSTER")
    source_ids = tuple(item.packet_id for item in resolution.inputs)
    _native_require(source_ids == registration.protocol.coverage_eligibility["source_record_refs"],
        "LP03_OPE_POINT_ORIGINAL_REGISTERED_SOURCE_REFS")
    parts, events = [], []
    for ref in source_ids:
        matches = tuple(item for item in packet._source_slices if len(item.original_record_refs) == 1
            and item.original_record_refs[0].record_id == ref)
        _native_require(len(matches) == 1, "LP03_OPE_POINT_ORIGINAL_SOURCE_SLICE")
        part, = matches
        event, = part.reconstructed_canonical_events
        exact, = part.original_record_refs
        binds = tuple(read for read in grant.allowed_reads if read.original_store_id == exact.store_id
            and read.selection.record_refs == (exact.record_id,))
        _native_require(len(binds) == 1 and binds[0].original_owner_id == event["owner_id"]
            and binds[0].required_original_rights_refs == part.rights_refs
            and set(binds[0].allowed_fields) == set(event["values"]), "LP03_OPE_POINT_ORIGINAL_SCOPED_RIGHTS")
        parts.append(_evidence_canonical_object_v1(deterministic_json(part).encode("utf-8"), max_bytes=frame_byte_limit))
        events.append(event)
    scope = registration.envelope_entry[3].assembly_scope
    source_payload = dict(profile="ORIGINAL_SOFTWARE_OPE_POINT_ESTIMATION", selected_math_id=math_id,
        consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
        consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, source_slices=tuple(parts))
    _, inputs, row_ids, _ = _evidence_recorded_ope_source_data_v1(source_payload, math_id=math_id)
    input_wire = deterministic_json(inputs).encode("utf-8")
    _native_require(input_wire == deterministic_json(resolution.authoritative_values).encode("utf-8")
        and row_ids == registration.protocol.numeric_profile["ordered_original_row_ids"],
        "LP03_OPE_POINT_ORIGINAL_INPUT_ASSOCIATION")
    event = dict(event_id="LP03-OPE-POINT::"+source_ids[0], kind="SYNTHETIC_RECORDED_OPE_POINT",
        origin=scope.origin.value, source_record_ref=parts[0]["original_record_refs"][0],
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=events[0]["revision"], connection_epoch=events[0]["source_epoch_id"], local_ordinal=0,
        payload=source_payload)
    frames = dict(segment_ordinal=0, final_segment=True, event=event, original_record_refs=refs,
        inputs=_native_strict_json(input_wire, max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=True),
        invocation_contract=_evidence_canonical_object_v1(deterministic_json(contract).encode("utf-8")))
    _encode_evidence_projection_json_v1(frames, maximum_bytes=frame_byte_limit-1024, maximum_nodes=4016)
    normalized = _evidence_normalized_event_v1(event)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return frames, normalized


def _evidence_recorded_dr_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Assemble the exact signed M22 source roster for its original worker."""
    from .models import _evidence_dr_original_source_data_v1, _evidence_normalized_event_v1
    from .serialization import _encode_evidence_projection_json_v1, _evidence_canonical_object_v1, _native_strict_json, deterministic_json

    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    registration, grant = attempt.registration, attempt.payload
    profile = registration.protocol.numeric_profile
    _native_require(resolution.math_spec_id == contract.math_id == "MATH-22"
        and grant.component_closure == ("MATH-22",)
        and registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_RECORDED_DR_UNCERTAINTY_CONFORMANCE_V1"
        and contract.resource_policy_ref == grant.protocol_ref == registration.binding_record.protocol_ref,
        "LP03_DR_ORIGINAL_WORKER_INVOCATION_PROFILE")
    protected = grant.component_and_callback_pins.get("supplementary_uncertainty_policy")
    _native_require(protected == dict(parameter_protocol_ref=registration.protocol.parameter_protocol_ref,
        uncertainty_source_ref=profile["uncertainty_source_ref"], numerical_work_limits=registration.protocol.numerical_work_limits),
        "LP03_DR_ORIGINAL_SIGNED_POLICY_JOIN")
    refs = tuple(dict(store_id=ref.store_id, record_id=ref.record_id)
        for part in packet._source_slices for ref in part.original_record_refs)
    _native_require(deterministic_json(refs) == deterministic_json(original_record_refs),
        "LP03_DR_ORIGINAL_READ_ROSTER")
    selected = (profile["logged_row_source_ref"], profile["uncertainty_source_ref"], *profile["assumption_source_refs"])
    _native_require(tuple(row.packet_id for row in resolution.inputs) == selected[:1],
        "LP03_DR_ORIGINAL_SOURCE_RESOLUTION_JOIN")
    parts = []
    for ref in selected:
        candidates = tuple(part for part in packet._source_slices if len(part.original_record_refs) == 1
            and part.original_record_refs[0].record_id == ref)
        _native_require(len(candidates) == 1, "LP03_DR_ORIGINAL_PART_REQUIRED")
        part = candidates[0]
        exact = part.original_record_refs[0]
        matches = tuple(row for row in grant.allowed_reads if row.original_store_id == exact.store_id
            and row.selection.record_refs == (exact.record_id,))
        event = part.reconstructed_canonical_events[0]
        _native_require(len(matches) == 1 and matches[0].original_owner_id == event["owner_id"]
            and matches[0].required_original_rights_refs == part.rights_refs
            and matches[0].allowed_fields == tuple(event["values"]),
            "LP03_DR_ORIGINAL_SCOPED_SOURCE_RIGHTS")
        parts.append(part)
    events = tuple(part.reconstructed_canonical_events[0] for part in parts)
    _native_require((events[0]["producer_receipt_id"],events[1]["producer_receipt_id"]) ==
        (profile["logged_row_receipt_ref"],profile["uncertainty_policy_receipt_ref"]),
        "LP03_DR_ORIGINAL_REGISTERED_RECEIPTS")
    slices = tuple(_evidence_canonical_object_v1(deterministic_json(part).encode("utf-8"),max_bytes=frame_byte_limit) for part in parts)
    scope = registration.envelope_entry[3].assembly_scope
    raw_ref = grant.grant_ref+"::DATA::RAW"
    source_payload = dict(profile="ORIGINAL_SOFTWARE_MATH22_RECORDED_DR_UNCERTAINTY",
        decision_wall_ns=scope.snapshot_decision_wall_ns, cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns,
        estimator_original_raw_ref=raw_ref, original_logged_input_slice=slices[0], original_policy_slice=slices[1],
        original_assumption_slices=slices[2:])
    _, native, policy, _, _ = _evidence_dr_original_source_data_v1(source_payload, original_raw_ref=raw_ref)
    _native_require(policy["protocol_ref"] == registration.protocol.parameter_protocol_ref
        and policy["basis"] == profile["output_basis"] and policy["unit"] == profile["output_unit"]
        and deterministic_json(native) == deterministic_json(resolution.authoritative_values),
        "LP03_DR_ORIGINAL_REGISTERED_UNCERTAINTY_ASSOCIATION")
    event = dict(event_id="LP03-RECORDED-DR::"+selected[0], kind="SYNTHETIC_RECORDED_DR_UNCERTAINTY",
        origin=scope.origin.value, source_record_ref=slices[0]["original_record_refs"][0],
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON",reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=events[0]["revision"], connection_epoch=events[0]["source_epoch_id"], local_ordinal=0,
        payload=source_payload)
    input_bytes = deterministic_json(native).encode("utf-8", "strict")
    frames = dict(segment_ordinal=0, final_segment=True, event=event,
        inputs=_native_strict_json(input_bytes,max_bytes=frame_byte_limit,max_nodes=4096,binary64_numbers=True),
        original_record_refs=refs, invocation_contract=_evidence_canonical_object_v1(deterministic_json(contract).encode("utf-8")))
    _native_require(frame_byte_limit > 1024, "LP03_DR_ORIGINAL_FRAME_CAPACITY")
    _encode_evidence_projection_json_v1(frames, maximum_bytes=frame_byte_limit-1024, maximum_nodes=4016)
    normalized = _evidence_normalized_event_v1(event)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return frames, normalized


def _evidence_heldout_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Build the held-out frame from the original sealed source and grant joins."""
    from .bindings import FORMULA_INPUT_AUTHORITY_BY_MATH_ID
    from .implementation_registry import resolve_evidence_invocation_v1
    from .models import _evidence_heldout_source_data_v1, _evidence_normalized_event_v1
    from .parameter_policy import _LP03_HELDOUT_ANALYSIS_PROFILE_V1
    from .serialization import (
        _encode_evidence_projection_json_v1,
        _evidence_canonical_object_v1,
        _native_strict_json,
        deterministic_json,
    )

    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    registration, grant = attempt.registration, attempt.payload
    protocol = registration.protocol
    profile = protocol.numeric_profile
    math_id = resolution.math_spec_id
    _native_require(math_id in ("MATH-20", "MATH-21")
        and grant.component_closure == (math_id,)
        and protocol.analysis_profile == _LP03_HELDOUT_ANALYSIS_PROFILE_V1
        and profile["topology_math_id"] == math_id
        and registration.binding_record.protocol_ref == grant.protocol_ref
        and profile["scorer_resource_policy_ref"] == protocol.parameter_protocol_ref,
        "LP03_HELD_OUT_ORIGINAL_INVOCATION_PROFILE")
    scope = registration.envelope_entry[3].assembly_scope
    pin = grant.component_and_callback_pins["components"][0]
    original_contract = resolve_evidence_invocation_v1(math_id, implementation_pin=pin[1],
        specification_pin=pin[2], resource_policy_ref=grant.protocol_ref, origin=scope.origin)
    scorer_pin = (profile["scorer_math_id"], profile["scorer_implementation_id"],
        profile["scorer_specification_id"], protocol.parameter_protocol_ref)
    _native_require(deterministic_json(original_contract) == deterministic_json(contract)
        and grant.component_and_callback_pins.get("supplementary_scorers") == (scorer_pin,),
        "LP03_HELD_OUT_ORIGINAL_SIGNED_PINS")
    scorer_contract = resolve_evidence_invocation_v1(scorer_pin[0], implementation_pin=scorer_pin[1],
        specification_pin=scorer_pin[2], resource_policy_ref=scorer_pin[3], origin=scope.origin)

    refs = tuple(dict(store_id=ref.store_id, record_id=ref.record_id)
        for part in packet._source_slices for ref in part.original_record_refs)
    _native_require(deterministic_json(refs) == deterministic_json(original_record_refs),
        "LP03_HELD_OUT_ORIGINAL_READ_ROSTER")
    parts_by_id = {}
    for part in packet._source_slices:
        for ref in part.original_record_refs:
            _native_require(ref.record_id not in parts_by_id, "LP03_HELD_OUT_ORIGINAL_SOURCE_IDENTITY")
            parts_by_id[ref.record_id] = part
    source_ids = profile["topology_source_refs"]
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
    _native_require(tuple(row.packet_id for row in resolution.inputs) == source_ids
        and tuple(row.binding_id for row in resolution.inputs) == tuple(binding.binding_id for binding in bindings)
        and all(source in parts_by_id for source in source_ids),
        "LP03_HELD_OUT_ORIGINAL_TOPOLOGY_SOURCE_ORDER")
    trace_id = profile["prediction_trace_source_ref"]
    label_id = profile["outcome_label_source_ref"]
    _native_require(trace_id in parts_by_id, "LP03_MISSING_PREDICTION_PRODUCER")
    _native_require(label_id in parts_by_id, "LP03_HELD_OUT_ORIGINAL_LABELS_REQUIRED")
    topology = tuple(parts_by_id[source_id] for source_id in source_ids)
    trace, labels = (parts_by_id[source_id] for source_id in (trace_id, label_id))
    originals = (*topology, trace, labels)

    for part in originals:
        _native_require(len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1,
            "LP03_HELD_OUT_ORIGINAL_SINGLE_SOURCE_RECORD")
        actual, event = part.original_record_refs[0], part.reconstructed_canonical_events[0]
        selections = tuple(read for read in grant.allowed_reads if read.original_store_id == actual.store_id
            and read.selection.record_refs == (actual.record_id,))
        _native_require(len(selections) == 1 and part.rights_refs == selections[0].required_original_rights_refs
            and event["owner_id"] == selections[0].original_owner_id
            and tuple(event["values"]) == selections[0].allowed_fields
            and event["context_id"] == resolution.context_id,
            "LP03_HELD_OUT_ORIGINAL_SCOPED_SOURCE_RIGHTS")
    for part, row in zip(topology, resolution.inputs, strict=True):
        event = part.reconstructed_canonical_events[0]
        _native_require(event["producer_receipt_id"] == row.producer_receipt_id
            and event["owner_id"] == row.owner_id, "LP03_HELD_OUT_ORIGINAL_TOPOLOGY_RECEIPT")
    _native_require(trace.reconstructed_canonical_events[0]["producer_receipt_id"] == profile["prediction_trace_receipt_ref"]
        and labels.reconstructed_canonical_events[0]["producer_receipt_id"] == profile["outcome_label_receipt_ref"],
        "LP03_HELD_OUT_ORIGINAL_SUPPLEMENTARY_RECEIPTS")

    wire_parts = tuple(_evidence_canonical_object_v1(deterministic_json(part).encode("utf-8"),
        max_bytes=frame_byte_limit) for part in originals)
    data = dict(association_profile="ORIGINAL_SOFTWARE_HELD_OUT_TOPOLOGY_TRACE_AND_LABELS",
        topology_math_id=math_id, scorer_math_id=scorer_contract.math_id,
        consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
        consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns,
        topology_source_slices=wire_parts[:-2], prediction_trace_slice=wire_parts[-2],
        outcome_label_slice=wire_parts[-1],
        clip_epsilon_json_or_absence=_evidence_canonical_object_v1(
            deterministic_json(profile["clip_epsilon_json_or_absence"]).encode("utf-8"))
            if scorer_contract.math_id == "MATH-08" else profile["clip_epsilon_json_or_absence"])
    _, original_inputs, scored_trace = _evidence_heldout_source_data_v1(data)
    _native_require(scored_trace["prediction_model_id"] == profile["prediction_model_id"]
        and scored_trace["prediction_model_version"] == profile["prediction_model_version"]
        and deterministic_json(original_inputs) == deterministic_json(resolution.authoritative_values),
        "LP03_HELD_OUT_ORIGINAL_REGISTERED_TRACE_AND_TOPOLOGY")
    events = tuple(part.reconstructed_canonical_events[0] for part in originals)
    anchor = wire_parts[0]["original_record_refs"][0]
    event = dict(event_id="LP03-HELD-OUT::" + anchor["record_id"], kind="SYNTHETIC_HELD_OUT_FOLD_SCORING",
        origin=scope.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=events[0]["revision"], connection_epoch=events[0]["source_epoch_id"],
        local_ordinal=0, payload=data)
    value_bytes = deterministic_json(resolution.authoritative_values).encode("utf-8")
    wire_inputs = _native_strict_json(value_bytes, max_bytes=frame_byte_limit, max_nodes=4096,
        binary64_numbers=True)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=wire_inputs, original_record_refs=refs,
        event=event, invocation_contract=_evidence_canonical_object_v1(deterministic_json(contract).encode("utf-8")),
        scorer_invocation_contract=_evidence_canonical_object_v1(deterministic_json(scorer_contract).encode("utf-8")))
    _native_require(frame_byte_limit > 1024, "LP03_HELD_OUT_FRAME_CAPACITY")
    _encode_evidence_projection_json_v1(payload, maximum_bytes=frame_byte_limit - 1024, maximum_nodes=4016)
    normalized = _evidence_normalized_event_v1(event)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized, scorer_contract


def _evidence_cscv_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Build one bounded native-data frame from the retained original roster.

    Canonical slice bytes were pinned by original resolution. Reconstructing
    their data here cannot mint source custody: both original witness checks
    and the exact source-to-resolution association are required independently.
    """
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1, deterministic_json
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    math_id = resolution.math_spec_id
    grant = attempt.payload
    scope = attempt.registration.envelope_entry[3].assembly_scope
    _native_require(math_id == "MATH-19" and grant.component_closure == (math_id,)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_CSCV_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected_contract = resolve_evidence_invocation_v1(math_id, implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected_contract), "LP03_CSCV_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_CSCV_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    # Bound decoding of all original slices before selecting the three
    # invocation sources. Aggregate policy and accounting sources retain
    # access associations through the complete original grant references.
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_CSCV_FRAME_CAPACITY")
    roster_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        roster_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(roster_bytes <= frame_byte_limit, "LP03_CSCV_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_CSCV_ORIGINAL_SLICE_ROSTER")
    selected = []
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_CSCV_ORIGINAL_RESOLUTION_ORDER")
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_CSCV_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        part = packet._source_slices[index]
        event = part.reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"]
                        and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id
                        and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_CSCV_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
    headroom = frame_byte_limit - 4096
    _native_require(headroom >= 2, "LP03_CSCV_FRAME_CAPACITY")
    selected_bytes = len(_encode_evidence_projection_json_v1(selected,
        maximum_bytes=headroom // 2, maximum_nodes=4096))
    ref_bytes = len(_encode_evidence_projection_json_v1(refs, maximum_bytes=frame_byte_limit, maximum_nodes=4096))
    contract_bytes = deterministic_json(contract).encode("utf-8")
    remaining = headroom - 2 * selected_bytes - ref_bytes - len(contract_bytes)
    _native_require(remaining > 0, "LP03_CSCV_FRAME_CAPACITY")
    input_bytes = _encode_evidence_projection_json_v1(dict(resolution.authoritative_values),
        maximum_bytes=remaining, maximum_nodes=4096)
    wire_inputs = _native_strict_json(input_bytes, max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=True)
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, wire_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_CSCV_FRAME_NODE_CAPACITY")
    source_events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-CSCV::" + anchor["record_id"], kind="SYNTHETIC_CSCV_MATRIX_AND_GROUP_POLICY",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(max(row["native_clocks"]["available_time"] for row in source_events),
            source_events[0]["values"]["material_trial_ledger"]["publication_visibility_wall_ns"]),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in source_events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=source_events[0]["revision"], connection_epoch=source_events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="ORIGINAL_DECLARED_SOFTWARE_CSCV_MATRIX_AND_GROUP_POLICY",
            row_identity_profile="COMPLETE_DECLARED_CHRONOLOGICAL_MATRIX_AND_STRATEGY_ROSTER",
            consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
            consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=wire_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    # Pure protocol validation includes the typed source/value join. This does
    # not launch or dispatch the frame; SVC still owns currentness and effects.
    from .evidence_execution import _worker_cscv_inputs_v1
    _worker_cscv_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized



def _evidence_sharpe_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Build one bounded native-data frame from the retained original roster.

    Canonical slice bytes were pinned by original resolution. Reconstructing
    their data here cannot mint source custody: both original witness checks
    and the exact source-to-resolution association are required independently.
    """
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1, deterministic_json
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    math_id = resolution.math_spec_id
    grant = attempt.payload
    scope = attempt.registration.envelope_entry[3].assembly_scope
    _native_require(math_id in ("MATH-17", "MATH-18") and grant.component_closure == (math_id,)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_SHARPE_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected_contract = resolve_evidence_invocation_v1(math_id, implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected_contract), "LP03_SHARPE_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_SHARPE_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    # The complete already-pinned roster is a conservative byte bound for the
    # five or six selected slices and the separately repeated original-reference list.
    # Count UTF-8 bytes before allocating its encoded copy or parsed data.
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_SHARPE_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(2 * source_bytes + 4096 <= frame_byte_limit, "LP03_SHARPE_FRAME_CAPACITY")
    input_body = dict(resolution.authoritative_values)
    input_bytes = _encode_evidence_projection_json_v1(input_body,
        maximum_bytes=frame_byte_limit - 2 * source_bytes - 4096, maximum_nodes=4096)
    contract_bytes = deterministic_json(contract).encode("utf-8")
    _native_require(2 * source_bytes + len(input_bytes) + len(contract_bytes) + 4096 <= frame_byte_limit,
                    "LP03_SHARPE_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_SHARPE_ORIGINAL_SLICE_ROSTER")
    selected = []
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_SHARPE_ORIGINAL_RESOLUTION_ORDER")
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_SHARPE_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        part = packet._source_slices[index]
        event = part.reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"]
                        and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id
                        and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_SHARPE_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
    wire_inputs = _native_strict_json(input_bytes, max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=True)
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, wire_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_SHARPE_FRAME_NODE_CAPACITY")
    source_events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-SHARPE::" + anchor["record_id"], kind="SYNTHETIC_SHARPE_LEDGER_AND_MOMENTS",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(max(row["native_clocks"]["available_time"] for row in source_events),
            source_events[0]["values"]["material_trial_ledger"]["publication_visibility_wall_ns"]),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in source_events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=source_events[0]["revision"], connection_epoch=source_events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="ORIGINAL_DECLARED_SOFTWARE_SHARPE_LEDGER_AND_MOMENTS", math_id=math_id,
            row_identity_profile="COMPLETE_DECLARED_ATTEMPTED_AND_PRUNED_ROSTER_NO_STATISTICAL_SUPPORT_CLAIM",
            consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
            consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=wire_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    # Pure protocol validation includes the typed source/value join. This does
    # not launch or dispatch the frame; SVC still owns currentness and effects.
    from .evidence_execution import _worker_sharpe_inputs_v1
    _worker_sharpe_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized


def _evidence_spa_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Build one bounded native-data frame from the retained original roster.

    Canonical slice bytes were pinned by original resolution. Reconstructing
    their data here cannot mint source custody: both original witness checks
    and the exact source-to-resolution association are required independently.
    """
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1, deterministic_json
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    scope = attempt.registration.envelope_entry[3].assembly_scope
    _native_require(resolution.math_spec_id == "MATH-16" and grant.component_closure == ("MATH-16",)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_SPA_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected_contract = resolve_evidence_invocation_v1("MATH-16", implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected_contract), "LP03_SPA_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_SPA_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    # The complete already-pinned roster is a conservative byte bound for the
    # seven selected slices and the separately repeated original-reference list.
    # Count UTF-8 bytes before allocating its encoded copy or parsed data.
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_SPA_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(2 * source_bytes + 4096 <= frame_byte_limit, "LP03_SPA_FRAME_CAPACITY")
    input_body = dict(resolution.authoritative_values)
    input_bytes = _encode_evidence_projection_json_v1(input_body,
        maximum_bytes=frame_byte_limit - 2 * source_bytes - 4096, maximum_nodes=4096)
    contract_bytes = deterministic_json(contract).encode("utf-8")
    _native_require(2 * source_bytes + len(input_bytes) + len(contract_bytes) + 4096 <= frame_byte_limit,
                    "LP03_SPA_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_SPA_ORIGINAL_SLICE_ROSTER")
    selected = []
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-16"]
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_SPA_ORIGINAL_RESOLUTION_ORDER")
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_SPA_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        part = packet._source_slices[index]
        event = part.reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"]
                        and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id
                        and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_SPA_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
    wire_inputs = _native_strict_json(input_bytes, max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=True)
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, wire_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_SPA_FRAME_NODE_CAPACITY")
    source_events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-SPA::" + anchor["record_id"], kind="SYNTHETIC_SPA_BATCH",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(max(row["native_clocks"]["available_time"] for row in source_events),
            source_events[0]["values"]["material_trial_ledger"]["publication_visibility_wall_ns"]),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in source_events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=source_events[0]["revision"], connection_epoch=source_events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="ORIGINAL_DECLARED_SOFTWARE_LOSS_FAMILY_AND_SPA_POLICY",
            row_identity_profile="COMPLETE_DECLARED_CANDIDATE_TIME_GRID_NO_EMPIRICAL_UNIVERSE_CLAIM",
            consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
            consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=wire_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    # Pure protocol validation includes the typed source/value join. This does
    # not launch or dispatch the frame; SVC still owns currentness and effects.
    from .evidence_execution import _worker_spa_inputs_v1
    _worker_spa_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized


def _evidence_reality_check_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Build one bounded native-data frame from the retained original roster.

    Canonical slice bytes were pinned by original resolution. Reconstructing
    their data here cannot mint source custody: both original witness checks
    and the exact source-to-resolution association are required independently.
    """
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1, deterministic_json
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    scope = attempt.registration.envelope_entry[3].assembly_scope
    _native_require(resolution.math_spec_id == "MATH-15" and grant.component_closure == ("MATH-15",)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_REALITY_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected_contract = resolve_evidence_invocation_v1("MATH-15", implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected_contract), "LP03_REALITY_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_REALITY_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    # The complete already-pinned roster is a conservative byte bound for the
    # six selected slices and the separately repeated original-reference list.
    # Count UTF-8 bytes before allocating its encoded copy or parsed data.
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_REALITY_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(2 * source_bytes + 4096 <= frame_byte_limit, "LP03_REALITY_FRAME_CAPACITY")
    input_body = dict(resolution.authoritative_values)
    input_bytes = _encode_evidence_projection_json_v1(input_body,
        maximum_bytes=frame_byte_limit - 2 * source_bytes - 4096, maximum_nodes=4096)
    contract_bytes = deterministic_json(contract).encode("utf-8")
    _native_require(2 * source_bytes + len(input_bytes) + len(contract_bytes) + 4096 <= frame_byte_limit,
                    "LP03_REALITY_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_REALITY_ORIGINAL_SLICE_ROSTER")
    selected = []
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-15"]
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_REALITY_ORIGINAL_RESOLUTION_ORDER")
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_REALITY_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        part = packet._source_slices[index]
        event = part.reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"]
                        and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id
                        and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_REALITY_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
    wire_inputs = _native_strict_json(input_bytes, max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=True)
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, wire_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_REALITY_FRAME_NODE_CAPACITY")
    source_events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-REALITY::" + anchor["record_id"], kind="SYNTHETIC_REALITY_CHECK_BATCH",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(max(row["native_clocks"]["available_time"] for row in source_events),
            source_events[0]["values"]["material_trial_ledger"]["publication_visibility_wall_ns"]),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in source_events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=source_events[0]["revision"], connection_epoch=source_events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="ORIGINAL_DECLARED_SOFTWARE_LOSS_FAMILY_AND_REALITY_CHECK_POLICY",
            row_identity_profile="COMPLETE_DECLARED_CANDIDATE_TIME_GRID_NO_EMPIRICAL_UNIVERSE_CLAIM",
            consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
            consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=wire_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    # Pure protocol validation includes the typed source/value join. This does
    # not launch or dispatch the frame; SVC still owns currentness and effects.
    from .evidence_execution import _worker_reality_check_inputs_v1
    _worker_reality_check_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized


def _evidence_bootstrap_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Build one bounded native-data frame from the retained original roster.

    Canonical slice bytes were pinned by original resolution. Reconstructing
    their data here cannot mint source custody: both original witness checks
    and the exact source-to-resolution association are required independently.
    """
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1, deterministic_json
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    _native_require(resolution.math_spec_id == "MATH-14" and grant.component_closure == ("MATH-14",)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_BOOTSTRAP_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected_contract = resolve_evidence_invocation_v1("MATH-14", implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected_contract), "LP03_BOOTSTRAP_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_BOOTSTRAP_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    # The complete already-pinned roster is a conservative byte bound for the
    # six selected slices and the separately repeated original-reference list.
    # Count UTF-8 bytes before allocating its encoded copy or parsed data.
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_BOOTSTRAP_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(2 * source_bytes + 4096 <= frame_byte_limit, "LP03_BOOTSTRAP_FRAME_CAPACITY")
    input_body = dict(resolution.authoritative_values)
    input_bytes = _encode_evidence_projection_json_v1(input_body,
        maximum_bytes=frame_byte_limit - 2 * source_bytes - 4096, maximum_nodes=4096)
    contract_bytes = deterministic_json(contract).encode("utf-8")
    _native_require(2 * source_bytes + len(input_bytes) + len(contract_bytes) + 4096 <= frame_byte_limit,
                    "LP03_BOOTSTRAP_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_BOOTSTRAP_ORIGINAL_SLICE_ROSTER")
    selected = []
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-14"]
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_BOOTSTRAP_ORIGINAL_RESOLUTION_ORDER")
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_BOOTSTRAP_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        part = packet._source_slices[index]
        event = part.reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"]
                        and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id
                        and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_BOOTSTRAP_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
    wire_inputs = _native_strict_json(input_bytes, max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=True)
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, wire_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_BOOTSTRAP_FRAME_NODE_CAPACITY")
    source_events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-BOOTSTRAP::" + anchor["record_id"], kind="SYNTHETIC_STATIONARY_BOOTSTRAP_BATCH",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in source_events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in source_events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=source_events[0]["revision"], connection_epoch=source_events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="SHARED_ORIGINAL_ORDERED_SERIES_AND_BOOTSTRAP_POLICY_CONTEXT",
            row_identity_profile="ORDERED_SYNTHETIC_SERIES_NO_EMPIRICAL_DEPENDENCE_CLAIM", source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=wire_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    # Pure protocol validation includes the typed source/value join. This does
    # not launch or dispatch the frame; SVC still owns currentness and effects.
    from .evidence_execution import _worker_bootstrap_inputs_v1
    _worker_bootstrap_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized


def _evidence_wilson_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Build one bounded native-data frame from the retained original roster.

    Canonical slice bytes were pinned by original resolution. Reconstructing
    their data here cannot mint source custody: both original witness checks
    and the exact source-to-resolution association are required independently.
    """
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1, deterministic_json
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    _native_require(resolution.math_spec_id == "MATH-11" and grant.component_closure == ("MATH-11",)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_WILSON_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected_contract = resolve_evidence_invocation_v1("MATH-11", implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected_contract), "LP03_WILSON_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_WILSON_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    # The complete already-pinned roster is a conservative byte bound for the
    # three selected slices and the separately repeated original-reference list.
    # Count UTF-8 bytes before allocating its encoded copy or parsed data.
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_WILSON_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(2 * source_bytes + 4096 <= frame_byte_limit, "LP03_WILSON_FRAME_CAPACITY")
    input_body = dict(resolution.authoritative_values)
    input_bytes = _encode_evidence_projection_json_v1(input_body,
        maximum_bytes=frame_byte_limit - 2 * source_bytes - 4096, maximum_nodes=4096)
    contract_bytes = deterministic_json(contract).encode("utf-8")
    _native_require(2 * source_bytes + len(input_bytes) + len(contract_bytes) + 4096 <= frame_byte_limit,
                    "LP03_WILSON_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_WILSON_ORIGINAL_SLICE_ROSTER")
    selected = []
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-11"]
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_WILSON_ORIGINAL_RESOLUTION_ORDER")
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_WILSON_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        part = packet._source_slices[index]
        event = part.reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"]
                        and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id
                        and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_WILSON_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
    wire_inputs = _native_strict_json(input_bytes, max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=True)
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, wire_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_WILSON_FRAME_NODE_CAPACITY")
    source_events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-WILSON::" + anchor["record_id"], kind="SYNTHETIC_BERNOULLI_COUNT_BATCH",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in source_events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in source_events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=source_events[0]["revision"], connection_epoch=source_events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="SHARED_ORIGINAL_COUNTS_AND_CONFIDENCE_POLICY_CONTEXT",
            row_identity_profile="AGGREGATE_SYNTHETIC_BERNOULLI_COUNTS_NO_TRIAL_OBSERVATIONS", source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=wire_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    # Pure protocol validation includes the typed source/value join. This does
    # not launch or dispatch the frame; SVC still owns currentness and effects.
    from .evidence_execution import _worker_wilson_inputs_v1
    _worker_wilson_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized


def _evidence_calibration_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Build one bounded native-data frame from the retained original roster.

    Canonical slice bytes were pinned by original resolution. Reconstructing
    their data here cannot mint source custody: both original witness checks
    and the exact source-to-resolution association are required independently.
    """
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1, deterministic_json
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    _native_require(resolution.math_spec_id == "MATH-10" and grant.component_closure == ("MATH-10",)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_CALIBRATION_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected_contract = resolve_evidence_invocation_v1("MATH-10", implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected_contract), "LP03_CALIBRATION_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_CALIBRATION_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    # The complete already-pinned roster is a conservative byte bound for the
    # four selected slices and the separately repeated original-reference list.
    # Count UTF-8 bytes before allocating its encoded copy or parsed data.
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_CALIBRATION_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(2 * source_bytes + 4096 <= frame_byte_limit, "LP03_CALIBRATION_FRAME_CAPACITY")
    input_body = dict(resolution.authoritative_values)
    input_bytes = _encode_evidence_projection_json_v1(input_body,
        maximum_bytes=frame_byte_limit - 2 * source_bytes - 4096, maximum_nodes=4096)
    contract_bytes = deterministic_json(contract).encode("utf-8")
    _native_require(2 * source_bytes + len(input_bytes) + len(contract_bytes) + 4096 <= frame_byte_limit,
                    "LP03_CALIBRATION_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_CALIBRATION_ORIGINAL_SLICE_ROSTER")
    selected = []
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID["MATH-10"]
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_CALIBRATION_ORIGINAL_RESOLUTION_ORDER")
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_CALIBRATION_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        part = packet._source_slices[index]
        event = part.reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"]
                        and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id
                        and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_CALIBRATION_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
    wire_inputs = _native_strict_json(input_bytes, max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=True)
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, wire_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_CALIBRATION_FRAME_NODE_CAPACITY")
    source_events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-CALIBRATION::" + anchor["record_id"], kind="SYNTHETIC_CALIBRATION_EVALUATION_BATCH",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(row["native_clocks"]["available_time"] for row in source_events),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in source_events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=source_events[0]["revision"], connection_epoch=source_events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="SHARED_ORIGINAL_DATASET_AND_BIN_POLICY_CONTEXT",
            row_identity_profile="ORDERED_SYNTHETIC_ROWS_NO_SAMPLE_IDS", source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=wire_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    # Pure protocol validation includes the typed source/value join. This does
    # not launch or dispatch the frame; SVC still owns currentness and effects.
    from .evidence_execution import _worker_calibration_inputs_v1
    _worker_calibration_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized


def _evidence_multiple_testing_worker_payload_v1(packet, attempt, contract, *, original_record_refs, frame_byte_limit):
    """Build one bounded native-data frame from the retained original roster.

    Canonical slice bytes were pinned by original resolution. Reconstructing
    their data here cannot mint source custody: both original witness checks
    and the exact source-to-resolution association are required independently.
    """
    from .implementation_registry import EvidencePrivateInvocationContractV1, resolve_evidence_invocation_v1
    from .models import _evidence_normalized_event_v1
    from .serialization import _native_strict_json, _evidence_canonical_object_v1, _encode_evidence_projection_json_v1, deterministic_json
    resolution = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    grant = attempt.payload
    math_id = resolution.math_spec_id
    scope = attempt.registration.envelope_entry[3].assembly_scope
    _native_require(math_id in ("MATH-12", "MATH-13") and grant.component_closure == (math_id,)
                    and not grant.callback_pins and type(contract) is EvidencePrivateInvocationContractV1
                    and type(frame_byte_limit) is int and 0 < frame_byte_limit <= grant.budgets.frame_byte_limit <= 65536,
                    "LP03_MULTIPLE_ORIGINAL_INVOCATION_PROFILE")
    pin = grant.component_and_callback_pins["components"][0]
    expected_contract = resolve_evidence_invocation_v1(math_id, implementation_pin=pin[1], specification_pin=pin[2],
        resource_policy_ref=grant.protocol_ref, origin=attempt.grant_record.origin)
    _native_require(deterministic_json(contract) == deterministic_json(expected_contract), "LP03_MULTIPLE_ORIGINAL_CONTRACT_JOIN")
    refs = tuple(dict(store_id=selection.original_store_id, record_id=ref)
                 for selection in grant.allowed_reads for ref in selection.selection.record_refs)
    _native_require(deterministic_json(original_record_refs) == deterministic_json(refs), "LP03_MULTIPLE_ORIGINAL_READ_ROSTER")
    canonical_slices = packet._roster_original[3]
    # The complete already-pinned roster is a conservative byte bound for the
    # two selected slices and the separately repeated original-reference list.
    # Count UTF-8 bytes before allocating its encoded copy or parsed data.
    _native_require(type(canonical_slices) is str and len(canonical_slices) <= frame_byte_limit,
                    "LP03_MULTIPLE_FRAME_CAPACITY")
    source_bytes = 0
    for char in canonical_slices:
        point = ord(char)
        source_bytes += 1 if point < 0x80 else 2 if point < 0x800 else 3 if point < 0x10000 else 4
        _native_require(2 * source_bytes + 4096 <= frame_byte_limit, "LP03_MULTIPLE_FRAME_CAPACITY")
    input_body = dict(resolution.authoritative_values)
    input_bytes = _encode_evidence_projection_json_v1(input_body,
        maximum_bytes=frame_byte_limit - 2 * source_bytes - 4096, maximum_nodes=4096)
    contract_bytes = deterministic_json(contract).encode("utf-8")
    _native_require(2 * source_bytes + len(input_bytes) + len(contract_bytes) + 4096 <= frame_byte_limit,
                    "LP03_MULTIPLE_FRAME_CAPACITY")
    wire_slices = _native_strict_json(canonical_slices.encode("utf-8"), max_bytes=frame_byte_limit, max_nodes=4096)
    _native_require(type(wire_slices) is list and len(wire_slices) == len(packet._source_slices),
                    "LP03_MULTIPLE_ORIGINAL_SLICE_ROSTER")
    selected = []
    bindings = FORMULA_INPUT_AUTHORITY_BY_MATH_ID[math_id]
    _native_require(tuple(row.input_name for row in resolution.inputs) == tuple(row.input_name for row in bindings),
                    "LP03_MULTIPLE_ORIGINAL_RESOLUTION_ORDER")
    for resolved, binding in zip(resolution.inputs, bindings):
        indices = tuple(index for index, part in enumerate(packet._source_slices)
            if len(part.original_record_refs) == len(part.reconstructed_canonical_events) == 1
            and part.original_record_refs[0].record_id == resolved.packet_id)
        _native_require(len(indices) == 1, "LP03_MULTIPLE_ORIGINAL_SOURCE_SLICE")
        index = indices[0]
        part = packet._source_slices[index]
        event = part.reconstructed_canonical_events[0]
        _native_require(resolved.binding_id == binding.binding_id and resolved.field_path == binding.exact_field_path
                        and resolved.producer_receipt_id == event["producer_receipt_id"]
                        and resolved.owner_id == event["owner_id"]
                        and event["context_id"] == resolution.context_id
                        and event["authorized_binding_ids"] == (binding.binding_id,),
                        "LP03_MULTIPLE_ORIGINAL_RESOLUTION_SOURCE_JOIN")
        selected.append(wire_slices[index])
    wire_inputs = _native_strict_json(input_bytes, max_bytes=frame_byte_limit, max_nodes=4096, binary64_numbers=True)
    wire_contract = _evidence_canonical_object_v1(contract_bytes)
    def nodes(value):
        if type(value) is dict:
            return 1 + sum(1 + nodes(child) for child in value.values())
        if type(value) in (list, tuple):
            return 1 + sum(nodes(child) for child in value)
        return 1
    _native_require(sum(nodes(value) for value in (*selected, wire_inputs, wire_contract, refs)) + 128 <= 4096,
                    "LP03_MULTIPLE_FRAME_NODE_CAPACITY")
    source_events = tuple(part["reconstructed_canonical_events"][0] for part in selected)
    anchor = selected[0]["original_record_refs"][0]
    event = dict(event_id="LP03-MULTIPLE::" + anchor["record_id"], kind="SYNTHETIC_MULTIPLE_TESTING_BATCH",
        origin=attempt.grant_record.origin.value, source_record_ref=anchor,
        availability_wall_ns=max(max(row["native_clocks"]["available_time"] for row in source_events),
            source_events[0]["values"]["material_trial_ledger"]["publication_visibility_wall_ns"]),
        effective_wall_ns=max(row["native_clocks"]["effective_time"] for row in source_events),
        provider_order_or_absence=dict(state="ABSENT_WITH_REASON", reason="NO_AGGREGATE_PROVIDER_ORDER"),
        source_revision=source_events[0]["revision"], connection_epoch=source_events[0]["source_epoch_id"], local_ordinal=0,
        payload=dict(association_profile="ORIGINAL_DECLARED_SOFTWARE_TRIAL_LEDGER_AND_Q_POLICY", math_id=math_id,
            consumer_decision_wall_ns=scope.snapshot_decision_wall_ns,
            consumer_cutoff_wall_ns=scope.snapshot_pit_cutoff_wall_ns, source_slices=selected))
    normalized = _evidence_normalized_event_v1(event)
    payload = dict(segment_ordinal=0, final_segment=True, inputs=wire_inputs, original_record_refs=refs,
                   event=event, invocation_contract=wire_contract)
    # Pure protocol validation includes the typed source/value join. This does
    # not launch or dispatch the frame; SVC still owns currentness and effects.
    from .evidence_execution import _worker_multiple_testing_inputs_v1
    _worker_multiple_testing_inputs_v1(payload, normalized)
    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
    return payload, normalized


def decode_evidence_public_invocation_inputs_v1(math_spec_id, raw, *, maximum_bytes, maximum_nodes):
    """Bound public-formula argument data; mathematical checks stay original.

    For MATH-39 these are the four derived invocation arguments, not its two
    original owner inputs. This decoder supplies no queue/source provenance,
    policy readiness, EvidenceInvocationInputsV1 or formula-allocation bound.
    """
    from .specification import CURRENT_FORMULA_INPUT_CONTRACTS
    from .serialization import _native_strict_json, _encode_evidence_projection_json_v1
    _native_require(type(math_spec_id) is str and math_spec_id in (
        *tuple(f"MATH-{number:02d}" for number in range(1, 26)), "MATH-36", "MATH-39"),
        "LP03_PUBLIC_INVOCATION_INPUT_SCHEMA_UNAVAILABLE")
    wire = _native_strict_json(raw, max_bytes=maximum_bytes, max_nodes=maximum_nodes, binary64_numbers=True)
    contract = CURRENT_FORMULA_INPUT_CONTRACTS[math_spec_id]
    names = contract.derived_formula_input_keys if math_spec_id == "MATH-39" else contract.declared_input_keys
    _native_require(type(wire) is dict and set(wire) == set(names), "LP03_PUBLIC_INVOCATION_INPUT_FIELDS")
    _native_require(_encode_evidence_projection_json_v1(wire, maximum_bytes=maximum_bytes,
        maximum_nodes=maximum_nodes) == raw, "LP03_PUBLIC_INVOCATION_INPUT_NONCANONICAL")

    def freeze(item):
        # Every object here was created by the strict native JSON parser; no
        # caller-provided native mapping or coercion hook reaches this walk.
        if type(item) is dict:
            return MappingProxyType({name: freeze(value) for name, value in item.items()})
        if type(item) is list:
            return tuple(freeze(value) for value in item)
        return item
    if math_spec_id == "MATH-39":
        from decimal import InvalidOperation

        exact = {}
        for name in names:
            token = wire[name]
            _native_require((type(token) is str and 0 < len(token) <= 128 and token.isascii())
                            or (type(token) is int and token.bit_length() <= 256), "LP03_QUEUE_DERIVED_DECIMAL_TOKEN")
            try:
                value = Decimal(token)
            except InvalidOperation as error:
                raise InputAuthorityError(ReasonCode.INPUT_VALUE_CONFLICT, "LP03_QUEUE_DERIVED_DECIMAL_TOKEN") from error
            _native_require(value.is_finite() and value >= 0 and -34 <= value.as_tuple().exponent <= 69
                            and value.adjusted() <= 69 and (type(token) is int or str(value) == token),
                            "LP03_QUEUE_DERIVED_DECIMAL_BOUND")
            exact[name] = value
        return MappingProxyType(exact)
    return MappingProxyType({name: freeze(wire[name]) for name in names})


def decode_evidence_private_inputs_v1(math_spec_id, raw, *, maximum_bytes, maximum_nodes):
    """Bounded input data reconstruction, never canonical-owner admission.

    This does not issue EvidenceInvocationInputsV1. Original source rights,
    producer joins, policy readiness and attempt custody are separate required
    admissions. In particular a decoded model/fee/quantum record is only data.
    """
    from dataclasses import fields
    from decimal import localcontext
    from .bindings import EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1
    from .context import QuantizationPolicyV1, QuantizationRoundingV1, decimal_context_v1, parse_utc
    from .economic_math import FeeScheduleBindingV1, FillProbabilityModelArtifactV1, FillQuantityDistributionArtifactV1
    from .errors import ComputationControlPlaneError, ContractValidationError
    from .quantum_benchmark import (QuantumEconomicBasisV1, EconomicComparatorReceiptV1,
        QAOATracePointV1, VQETracePointV1, QAOAPreexistingTraceV1, VQEPreexistingTraceV1,
        QuantumTraceValidationReceiptV1)
    from .serialization import _native_strict_json, deterministic_json

    _native_require(type(math_spec_id) is str and math_spec_id in EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1,
                    "LP03_PRIVATE_INPUT_SCHEMA_UNAVAILABLE")
    wire = _native_strict_json(raw, max_bytes=maximum_bytes, max_nodes=maximum_nodes, binary64_numbers=True)
    _native_require(deterministic_json(wire).encode("utf-8") == raw, "LP03_PRIVATE_INPUT_NONCANONICAL")
    contract = EVIDENCE_PRIVATE_INPUT_CONTRACTS_V1[math_spec_id]
    _native_require(type(wire) is dict and set(wire) == {row.input_name for row in contract.bindings},
                    "LP03_PRIVATE_INPUT_FIELDS")

    # Closed adapter schemas preserve exact original dataclass member rosters.
    # Fields are explicit rather than inferred from a caller's object or class.
    records = {
        "FeeScheduleBindingV1": (FeeScheduleBindingV1, (
            ("binding_ref", "str"), ("venue_ref", "str"), ("market_or_category_ref", "str"),
            ("schedule_version", "str"), ("source_epoch_ref", "str"), ("valid_from", "datetime"),
            ("valid_until", "datetime_or_none"), ("evaluated_at", "datetime"),
            ("component_classes", "tuple[str]"), ("component_rate_bindings", "tuple[tuple[str,Decimal]]"))),
        "QuantizationPolicyV1": (QuantizationPolicyV1, (
            ("policy_id", "str"), ("field_id", "str"), ("increment", "Decimal"), ("rounding", "rounding"),
            ("unit", "str"), ("currency_or_asset", "str"), ("basis", "str"), ("scale", "int"), ("source_binding_ref", "str"))),
        "FillProbabilityModelArtifactV1": (FillProbabilityModelArtifactV1, (
            ("artifact_id", "str"), ("artifact_version", "str"), ("feature_schema_ref", "str"),
            ("calibration_receipt_ref", "str"), ("scope_ref", "str"), ("horizon_seconds", "int"),
            ("probability", "Decimal"), ("feature_snapshot_ref", "str"), ("feature_observed_at", "datetime"),
            ("evaluated_at", "datetime"), ("artifact_valid_until", "datetime"),
            ("maximum_feature_age", "timedelta"), ("calibration_state", "str"))),
        "FillQuantityDistributionArtifactV1": (FillQuantityDistributionArtifactV1, (
            ("artifact_id", "str"), ("artifact_version", "str"), ("source_binding_ref", "str"),
            ("scope_ref", "str"), ("horizon_seconds", "int"), ("evaluated_at", "datetime"),
            ("artifact_valid_until", "datetime"), ("order_quantity", "Decimal"),
            ("normalization_tolerance", "Decimal"), ("fill_quantity_distribution", "tuple[tuple[Decimal,Decimal]]"))),
        "QuantumEconomicBasisV1": (QuantumEconomicBasisV1, (
            ("input_lock_id", "str"), ("original_formulation_id", "str"), ("objective_sense", "str"),
            ("constraint_refs", "tuple[str]"), ("accounting_basis_ref", "str"), ("cost_basis_ref", "str"),
            ("capacity_basis_ref", "str"), ("scenario_set_ref", "str"), ("resource_budget_ref", "str"),
            ("ttl_policy_ref", "str"), ("version_epoch_pins", "tuple[str]"))),
        "EconomicComparatorReceiptV1": (EconomicComparatorReceiptV1, (
            ("receipt_id", "str"), ("comparator_class", "str"), ("comparison_basis", "QuantumEconomicBasisV1"),
            ("feasible", "bool"), ("hard_veto", "bool"), ("conservative_utility", "Decimal"),
            ("resource_use", "Decimal"), ("latency", "Decimal"), ("deterministic_tie_break", "str"))),
        "QAOATracePointV1": (QAOATracePointV1, (
            ("candidate_id", "str"), ("trace_weight", "Decimal"), ("locked_cost", "Decimal"),
            ("original_model_feasible", "bool"), ("original_economic_utility", "Decimal"),
            ("resource_use", "Decimal"), ("latency", "Decimal"))),
        "VQETracePointV1": (VQETracePointV1, (
            ("parameter_point_id", "str"), ("expectation", "Decimal"), ("variance", "Decimal"),
            ("locked_cost", "Decimal"), ("original_model_feasible", "bool"),
            ("original_economic_utility", "Decimal"), ("resource_use", "Decimal"), ("latency", "Decimal"))),
        "QAOAPreexistingTraceV1": (QAOAPreexistingTraceV1, (
            ("trace_id", "str"), ("input_lock_id", "str"), ("formulation_id", "str"), ("objective_id", "str"),
            ("objective_sense", "str"), ("parameter_order", "tuple[str]"), ("seed_policy_ref", "str"),
            ("bounds_ref", "str"), ("constraint_refs", "tuple[str]"), ("comparison_basis", "QuantumEconomicBasisV1"),
            ("points", "tuple[QAOATracePointV1]"), ("selected_candidate_id", "str"),
            ("strongest_classical_receipt_ref", "str"), ("no_trade_receipt_ref", "str"),
            ("strongest_classical_comparator", "EconomicComparatorReceiptV1"),
            ("no_trade_comparator", "EconomicComparatorReceiptV1"), ("trace_complete", "bool"),
            ("original_model_interpret_back_valid", "bool"))),
        "VQEPreexistingTraceV1": (VQEPreexistingTraceV1, (
            ("trace_id", "str"), ("input_lock_id", "str"), ("formulation_id", "str"), ("objective_sense", "str"),
            ("hamiltonian_id", "str"), ("ansatz_metadata_ref", "str"), ("parameter_order", "tuple[str]"),
            ("optimizer_metadata_ref", "str"), ("seed_policy_ref", "str"), ("bounds_ref", "str"),
            ("constraint_refs", "tuple[str]"), ("comparison_basis", "QuantumEconomicBasisV1"),
            ("points", "tuple[VQETracePointV1]"), ("selected_point_id", "str"),
            ("strongest_classical_receipt_ref", "str"), ("no_trade_receipt_ref", "str"),
            ("strongest_classical_comparator", "EconomicComparatorReceiptV1"),
            ("no_trade_comparator", "EconomicComparatorReceiptV1"), ("trace_complete", "bool"),
            ("original_model_interpret_back_valid", "bool"))),
        "QuantumTraceValidationReceiptV1": (QuantumTraceValidationReceiptV1, (
            ("receipt_id", "str"), ("schema_version", "str"), ("contract_version", "str"), ("math_spec_id", "str"),
            ("trace_id", "str"), ("input_lock_id", "str"), ("formulation_id", "str"),
            ("comparison_basis", "QuantumEconomicBasisV1"), ("selected_candidate_id", "str"),
            ("recomputed_objective", "Decimal"), ("recomputed_variance_or_explicit_absence", "Decimal_or_absence"),
            ("selected_original_model_feasible", "bool"), ("selected_hard_veto", "bool"),
            ("original_model_interpret_back_valid", "bool"), ("strongest_classical_receipt_ref", "str"),
            ("no_trade_receipt_ref", "str"), ("original_economic_utility", "Decimal"), ("resource_use", "Decimal"),
            ("latency", "Decimal"), ("deterministic_tie_break", "str"), ("effect_counts", "effect_counts"),
            ("terminal_state", "str"), ("quantum_advantage_claim_allowed", "bool"))),
    }
    sequences = {
        "tuple[Decimal]": "Decimal", "tuple[float]": "float", "tuple[str]": "str",
        "tuple[tuple[Decimal]]": "tuple[Decimal]", "tuple[tuple[float]]": "tuple[float]",
        "tuple[tuple[Decimal,tuple[Decimal]]]": ("Decimal", "tuple[Decimal]"),
        "tuple[tuple[Decimal,Decimal]]": ("Decimal", "Decimal"),
        "tuple[tuple[str,Decimal]]": ("str", "Decimal"),
        "tuple[QAOATracePointV1]": "QAOATracePointV1", "tuple[VQETracePointV1]": "VQETracePointV1",
    }
    remaining = maximum_nodes

    def value(item, kind):
        nonlocal remaining
        _native_require(remaining > 0, "LP03_PRIVATE_INPUT_NODES")
        remaining -= 1
        if type(kind) is tuple:
            _native_require(type(item) is list and len(item) == len(kind), "LP03_PRIVATE_INPUT_TUPLE")
            return tuple(value(child, child_kind) for child, child_kind in zip(item, kind, strict=True))
        if kind in sequences:
            _native_require(type(item) is list and len(item) <= remaining, "LP03_PRIVATE_INPUT_SEQUENCE")
            return tuple(value(child, sequences[kind]) for child in item)
        if kind == "Decimal_or_absence":
            if type(item) is str and item == "EXPLICIT_ABSENCE":
                return item
            kind = "Decimal"
        if kind == "Decimal":
            _native_require(type(item) is str and 0 < len(item) <= maximum_bytes, "LP03_PRIVATE_INPUT_DECIMAL_TEXT")
            result = Decimal(item)
            _native_require(result.is_finite() and str(result) == item, "LP03_PRIVATE_INPUT_DECIMAL_CANONICAL")
            return result
        if kind in ("str", "int", "bool", "float"):
            valid = (type(item) is str and bool(item) if kind == "str" else
                     type(item) is int if kind == "int" else type(item) is bool if kind == "bool" else
                     type(item) is float and math.isfinite(item))
            _native_require(valid, "LP03_PRIVATE_INPUT_SCALAR_TYPE")
            return item
        if kind in ("datetime", "datetime_or_none"):
            if item is None and kind == "datetime_or_none":
                return None
            _native_require(type(item) is str, "LP03_PRIVATE_INPUT_DATETIME")
            result = parse_utc(item, field_name=kind)
            _native_require(result.isoformat() == item, "LP03_PRIVATE_INPUT_DATETIME_CANONICAL")
            return result
        if kind == "rounding":
            _native_require(type(item) is str, "LP03_PRIVATE_INPUT_ROUNDING")
            return QuantizationRoundingV1(item)
        if kind == "timedelta":
            _native_require(type(item) is dict and set(item) == {"days", "seconds", "microseconds"},
                            "LP03_PRIVATE_INPUT_TIMEDELTA")
            parts = {name: value(item[name], "int") for name in ("days", "seconds", "microseconds")}
            _native_require(0 <= parts["days"] <= 999999999 and 0 <= parts["seconds"] < 86400
                            and 0 <= parts["microseconds"] < 1000000 and any(parts.values()),
                            "LP03_PRIVATE_INPUT_TIMEDELTA")
            return timedelta(**parts)
        if kind == "effect_counts":
            names = ("ansatz_construction", "optimizer", "estimator", "sampler", "transpiler", "simulator", "provider", "qpu")
            _native_require(type(item) is dict and set(item) == set(names), "LP03_PRIVATE_INPUT_EFFECT_COUNTS")
            return MappingProxyType({name: value(item[name], "int") for name in names})
        _native_require(kind in records, "LP03_PRIVATE_INPUT_TYPE_UNAVAILABLE")
        cls, members = records[kind]
        names = tuple(name for name, _ in members)
        _native_require(tuple(field.name for field in fields(cls)) == names
                        and type(item) is dict and set(item) == set(names), "LP03_PRIVATE_INPUT_RECORD_FIELDS")
        return cls(**{name: value(item[name], child_kind) for name, child_kind in members})

    def encoded(item, kind):
        # This encoder is local to the decoder and receives only its just-built
        # bounded originals. It is not an arbitrary native-value serializer.
        if type(kind) is tuple:
            return [encoded(child, child_kind) for child, child_kind in zip(item, kind, strict=True)]
        if kind in sequences:
            return [encoded(child, sequences[kind]) for child in item]
        if kind in ("Decimal", "Decimal_or_absence"):
            return str(item)
        if kind in ("datetime", "datetime_or_none"):
            return None if item is None else item.isoformat()
        if kind == "timedelta":
            return {"days": item.days, "seconds": item.seconds, "microseconds": item.microseconds}
        if kind == "rounding":
            return item.value
        if kind in records:
            return {name: encoded(getattr(item, name), child_kind) for name, child_kind in records[kind][1]}
        return item

    try:
        with localcontext(decimal_context_v1()):
            result = MappingProxyType({row.input_name: value(wire[row.input_name], row.native_input_type)
                                       for row in contract.bindings})
            body = {row.input_name: encoded(result[row.input_name], row.native_input_type) for row in contract.bindings}
            _native_require(deterministic_json(body).encode("utf-8") == raw, "LP03_PRIVATE_INPUT_RECONSTRUCTION_CHANGED")
            return result
    except ComputationControlPlaneError:
        raise
    except (ArithmeticError, ValueError, TypeError, MemoryError) as exc:
        raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "LP03_PRIVATE_INPUT_RECONSTRUCTION_FAILED") from exc


class EvidenceInvocationInputsV1:
    """Original canonical-owner packet; dictionaries never self-certify a lane input."""

    __slots__ = ("_attempt", "_resolution", "_natural_key", "_source_slices", "_roster_original")

    def __init__(self):
        raise TypeError("private invocation inputs require the original canonical resolver")

    def __copy__(self):
        raise TypeError("LP03 invocation input custody cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 invocation input custody cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 invocation input custody cannot be serialized")

    @property
    def natural_key(self):
        return self._natural_key

    @property
    def field_roster(self):
        _native_require(type(self._resolution) is FormulaInputResolutionV1, "LP03_EDGE_CHAIN_DEPENDENCY_NOT_EXECUTED")
        return self._resolution.inputs

    def _require_original_v1(self, attempt, *, canonical=True):
        from .serialization import deterministic_json
        root = attempt.invocation_original
        _native_require(type(self) is EvidenceInvocationInputsV1
                        and type(root) is tuple and len(root) == 8
                        and type(root[0]) is tuple and any(packet is self for packet in root[0])
                        and self._attempt is attempt and self._roster_original is root
                        and attempt.invocations is root[0] and attempt.source_slices is root[2]
                        and attempt.resolution_progress is root[4]
                        and attempt.resolution_witnesses is root[6]
                        and tuple(row.math_spec_id for row in root[4]) == root[5] == attempt.payload.component_closure
                        and len(root[0]) == len(root[1]) == len(root[4]) == len(root[5]) == len(root[6]),
                        "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
        if type(self._resolution) is _EvidencePendingProbabilityEdgeInputsV1:
            _native_require(root[5] == ("MATH-01", "MATH-02") and len(root[0]) == 2
                and root[0][1] is self and type(root[4][0]) is FormulaInputResolutionV1
                and self._resolution.execution_context is root[4][0].execution_context
                and attempt.invocation_state == "EXTERNAL_INPUTS_RESOLVED", "LP03_EDGE_CHAIN_ORIGINAL_PENDING_CUSTODY")
        key = self._natural_key
        _native_require(type(key) is tuple and len(key) == 5 and type(key[3]) is int
                        and 0 <= key[3] < len(root[0]), "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
        original = root[1][key[3]]
        _native_require(self is root[0][key[3]] is original[0] and self._resolution is original[1] is root[4][key[3]]
                        and key == original[2] == (attempt.registration.binding_record.experiment_revision,
                            attempt.payload.lane.value, attempt.payload.attempt_ordinal, key[3], root[5][key[3]])
                        and self._source_slices is root[2], "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
        _native_require(original[4] is root[6][key[3]], "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
        for resolution, witness in zip(root[4], root[6]):
            _require_evidence_resolution_witness_v1(resolution, witness, canonical=canonical)
        _require_evidence_source_slice_roster_v1(attempt.registration, self._source_slices,
            originals=root[7], subject=attempt, canonical=canonical)
        if canonical:
            _native_require(deterministic_json(self._resolution) == original[3]
                            and deterministic_json(self._source_slices) == root[3], "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
        return self._resolution


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
    def resolve_evidence_v1(math_spec_id, *, attempt_grant, invocation_ordinal, requester_context):
        from contextlib import ExitStack
        from ...agents.pr169_agent_orch1_resolvers import AgentOrchService, EvidenceAttemptGrantV1
        from .persistence import _EvidenceRegistrationOperationV1
        from .serialization import deterministic_json
        from .input_lock import _require_original_input_assembly_outcome_v1
        _native_require(type(attempt_grant) is EvidenceAttemptGrantV1 and type(math_spec_id) is str
                        and type(invocation_ordinal) is int and 0 <= invocation_ordinal < 48,
                        "LP03_PRIVATE_INPUT_PROFILE_UNAVAILABLE")
        state, attempt = attempt_grant._owner, attempt_grant._attempt
        AgentOrchService.resolve_evidence_attempt_v1(state.service, attempt_grant,
            purpose="EVIDENCE_LANE_EXECUTION_V1", requester_context=requester_context)
        closure = attempt.payload.component_closure
        _native_require(invocation_ordinal < len(closure) and closure[invocation_ordinal] == math_spec_id,
                        "LP03_PRIVATE_INPUT_PROFILE_UNAVAILABLE")
        operation = attempt.registration
        with state.lock, ExitStack() as locks:
            _native_require(state.operation is None and operation.active_attempt is None
                            and attempt.handle is attempt_grant and attempt.phase == "COMMITTED_AND_READBACK",
                            "LP03_PRIVATE_INPUT_ORIGINAL_ATTEMPT")
            state.operation, operation.active_attempt = operation, attempt
            try:
                state._lock_original_source_custodies_v1(locks)
                _EvidenceRegistrationOperationV1._check_current_v1(operation)
                if attempt.invocation_state == "RESOLVED" or (closure == ("MATH-01", "MATH-02")
                        and attempt.invocation_state == "EXTERNAL_INPUTS_RESOLVED"):
                    _native_require(type(attempt.invocations) is tuple and len(attempt.invocations) == len(closure),
                                    "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
                    packet = attempt.invocations[invocation_ordinal]
                    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
                    original = attempt.invocation_original
                    _EvidenceRegistrationOperationV1._check_current_v1(operation)
                    _native_require(attempt.invocation_original is original, "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
                    EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
                    return packet
                _native_require(attempt.invocation_state == "NOT_STARTED" and attempt.invocations == ()
                                and attempt.invocation_original is None and attempt.resolution_progress == ()
                                and attempt.resolution_witnesses == ()
                                and invocation_ordinal == 0,
                                "LP03_INVOCATION_ALREADY_RESERVED_OR_UNRESOLVED")
                attempt.invocation_state = "READING_ORIGINAL_INPUTS"
                preparation = operation.preparation
                _require_original_input_assembly_outcome_v1(preparation, preparation.input_assembly_outcome)
                sealed_events = {event["record_ref"]: event for part in preparation.input_assembly_members[1]
                                 for event in part.reconstructed_canonical_events}
                acquired, acquired_bodies, acquired_originals = (), (), ()
                for selection in attempt.allowed_reads:
                    matches = tuple(custody for custody, policies in operation.policies
                        if all(ref in {policy.rights_ref for policy in policies} for ref in selection.required_original_rights_refs))
                    _native_require(len(matches) == 1, "LP03_LANE_ORIGINAL_SOURCE_OWNER_AMBIGUOUS")
                    part = _EvidenceOwnerPacketCustodyV1._read_lane_slice_v1(matches[0], operation, selection)
                    _native_require(attempt.source_slices is acquired, "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
                    _require_evidence_source_slice_roster_v1(operation, acquired, originals=acquired_originals, subject=attempt)
                    original_part = _require_evidence_source_slice_roster_v1(operation, (part,), subject=attempt)
                    _native_require(all(event["record_ref"] in sealed_events and event == sealed_events[event["record_ref"]]
                                        for event in part.reconstructed_canonical_events), "LP03_LANE_SOURCE_DIFFERS_FROM_SEALED_INPUT")
                    acquired, acquired_bodies = (*acquired, part), (*acquired_bodies, deterministic_json(part))
                    acquired_originals = (*acquired_originals, *original_part)
                    attempt.source_slices = acquired
                slices = acquired
                resolutions, witnesses = _resolve_evidence_original_inputs_v1(operation, slices)
                _native_require(attempt.source_slices is slices, "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
                _require_evidence_source_slice_roster_v1(operation, slices, originals=acquired_originals, subject=attempt)
                _native_require(tuple(deterministic_json(part) for part in slices) == acquired_bodies,
                                "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
                sealed = preparation.input_assembly_members[4]
                _native_require(len(resolutions) == len(sealed) == len(closure)
                                and tuple(row.math_spec_id for row in resolutions) == tuple(row.math_spec_id for row in sealed) == closure
                                and all(type(row) is type(original) and (
                                        deterministic_json(row) == deterministic_json(original)
                                        if type(row) is _EvidencePendingProbabilityEdgeInputsV1 else
                                        tuple(row.authoritative_values) == tuple(original.authoritative_values)
                                        and deterministic_json(row.authoritative_values) == deterministic_json(original.authoritative_values)
                                        and row.packet_refs == original.packet_refs and row.receipt_refs == original.receipt_refs)
                                        for row, original in zip(resolutions, sealed)),
                                "LP03_LANE_RESOLUTION_DIFFERS_FROM_SEALED_INPUT")
                packets, originals = [], []
                for ordinal, resolution in enumerate(resolutions):
                    natural_key = (operation.binding_record.experiment_revision, attempt.payload.lane.value,
                                   attempt.payload.attempt_ordinal, ordinal, resolution.math_spec_id)
                    packet = object.__new__(EvidenceInvocationInputsV1)
                    packet._attempt, packet._resolution, packet._natural_key, packet._source_slices = attempt, resolution, natural_key, slices
                    packets.append(packet)
                    witness = witnesses[ordinal]
                    _require_evidence_resolution_witness_v1(resolution, witness)
                    originals.append((packet, resolution, natural_key, witness[2], witness))
                roster, originals = tuple(packets), tuple(originals)
                progress = attempt.resolution_progress
                original_witnesses = attempt.resolution_witnesses
                _native_require(len(progress) == len(resolutions) and all(left is right for left, right in zip(progress, resolutions))
                                and len(original_witnesses) == len(witnesses)
                                and all(left is right for left, right in zip(original_witnesses, witnesses)),
                                "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
                original = (roster, originals, slices, deterministic_json(slices), progress, closure, original_witnesses, acquired_originals)
                for packet in roster:
                    packet._roster_original = original
                _EvidenceRegistrationOperationV1._check_current_v1(operation)
                _native_require(attempt.source_slices is slices and attempt.resolution_progress is progress
                                and attempt.resolution_witnesses is original_witnesses
                                and attempt.invocations == () and attempt.invocation_original is None
                                and attempt.invocation_state == "READING_ORIGINAL_INPUTS",
                                "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
                _require_original_input_assembly_outcome_v1(preparation, preparation.input_assembly_outcome)
                _require_evidence_source_slice_roster_v1(operation, slices, originals=acquired_originals, subject=attempt)
                _native_require(deterministic_json(slices) == original[3]
                                and all(deterministic_json(row[1]) == row[3] for row in originals),
                                "LP03_ORIGINAL_INVOCATION_INPUTS_CHANGED")
                for resolution, witness in zip(progress, original_witnesses):
                    _require_evidence_resolution_witness_v1(resolution, witness)
                attempt.invocations, attempt.invocation_original, attempt.invocation_state = roster, original, (
                    "EXTERNAL_INPUTS_RESOLVED" if closure == ("MATH-01", "MATH-02") else "RESOLVED")
                return roster[invocation_ordinal]
            except BaseException:
                attempt.invocation_state = "INPUT_RESOLUTION_FAILED_REQUIRES_AUDIT"
                attempt.phase = "ATTEMPT_FAILED_REQUIRES_AUDIT"
                from .latency_policy import _EvidenceLocalClockV1
                try:
                    _native_require(_EvidenceRegistrationOperationV1._observe_accounting_v1(operation),
                                    "LP03_EXECUTION_ACCOUNTING_UNPROVEN")
                except BaseException:
                    attempt.phase = "ATTEMPT_CLOCK_CUSTODY_UNAVAILABLE"
                    raise
                raise
            finally:
                operation.active_attempt, state.operation = None, None

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
