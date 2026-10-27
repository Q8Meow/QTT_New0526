"""Centralized point-in-time field-class laws for ST12-B."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from .context import (
    ComputationContextKeyV1,
    parse_utc,
    _native_require,
    _native_reference_reason,
    _native_obj,
    _native_ident,
    _native_scalar,
    _native_utc_nanoseconds,
    _native_utc_receipt_pair,
    _public_counter_v1, _public_refs_v1,
)
from .errors import ContractValidationError, PointInTimeError, ReasonCode
from .models import ComputationExecutionContextV1


class PointInTimeFieldClassV1(StrEnum):
    OBSERVATION = "OBSERVATION"
    SCHEDULED_EFFECTIVE_FACT = "SCHEDULED_EFFECTIVE_FACT"
    REVISION = "REVISION"
    EVENT_OUTCOME = "EVENT_OUTCOME"
    SETTLEMENT = "SETTLEMENT"


class PointInTimeViolationV1(StrEnum):
    CONTEXT_AS_OF_MISMATCH = "CONTEXT_AS_OF_MISMATCH"
    OBSERVED_AFTER_DECISION = "OBSERVED_AFTER_DECISION"
    AVAILABLE_AFTER_DECISION = "AVAILABLE_AFTER_DECISION"
    RECEIVED_AFTER_DECISION = "RECEIVED_AFTER_DECISION"
    PROCESSED_AFTER_DECISION = "PROCESSED_AFTER_DECISION"
    EFFECTIVE_AFTER_DECISION = "EFFECTIVE_AFTER_DECISION"
    CLOCK_ORDER_INVALID = "CLOCK_ORDER_INVALID"
    REVISION_LEAKAGE = "REVISION_LEAKAGE"


@dataclass(frozen=True, slots=True)
class PointInTimeClocksV1:
    """The six clocks required by every frozen formula-input interface."""

    observed_time: datetime
    effective_time: datetime
    available_time: datetime
    received_time: datetime
    processed_time: datetime
    as_of_time: datetime

    def __post_init__(self) -> None:
        for name in (
            "observed_time",
            "effective_time",
            "available_time",
            "received_time",
            "processed_time",
            "as_of_time",
        ):
            object.__setattr__(
                self,
                name,
                parse_utc(getattr(self, name), field_name=name),
            )


@dataclass(frozen=True, slots=True)
class PointInTimeReceiptV1:
    receipt_id: str
    field_class: PointInTimeFieldClassV1
    context_id: str
    as_of_time: datetime
    admitted: bool
    checked_clocks: tuple[str, ...]
    violation: PointInTimeViolationV1 | None = None

    def __post_init__(self) -> None:
        if not self.receipt_id or not self.context_id:
            raise PointInTimeError(
                ReasonCode.POINT_IN_TIME_VIOLATION,
                "point-in-time receipt identity and context are required",
            )
        if type(self.admitted) is not bool:
            raise PointInTimeError(
                ReasonCode.POINT_IN_TIME_VIOLATION,
                "point-in-time admission must be an exact boolean",
            )
        if self.admitted == (self.violation is not None):
            raise PointInTimeError(
                ReasonCode.POINT_IN_TIME_VIOLATION,
                "point-in-time receipt admission and violation disagree",
            )


class PointInTimePolicyV1:
    """Apply deterministic violation precedence once, outside formula code."""

    CHECKED_CLOCKS = (
        "observed_time",
        "effective_time",
        "available_time",
        "received_time",
        "processed_time",
        "as_of_time",
    )

    @classmethod
    def validate(
        cls,
        *,
        receipt_id: str,
        field_class: PointInTimeFieldClassV1,
        clocks: PointInTimeClocksV1,
        context: ComputationContextKeyV1,
        prior_revision_available_time: datetime | None = None,
    ) -> PointInTimeReceiptV1:
        if not isinstance(field_class, PointInTimeFieldClassV1):
            raise PointInTimeError(
                ReasonCode.POINT_IN_TIME_VIOLATION,
                "field_class must be a frozen PointInTimeFieldClassV1",
            )
        if not isinstance(clocks, PointInTimeClocksV1) or not isinstance(
            context, ComputationContextKeyV1
        ):
            raise PointInTimeError(
                ReasonCode.POINT_IN_TIME_VIOLATION,
                "typed clocks and computation context are required",
            )

        violation: PointInTimeViolationV1 | None = None
        if clocks.as_of_time != context.as_of:
            violation = PointInTimeViolationV1.CONTEXT_AS_OF_MISMATCH
        elif clocks.observed_time > context.as_of:
            violation = PointInTimeViolationV1.OBSERVED_AFTER_DECISION
        elif clocks.available_time > context.as_of:
            violation = PointInTimeViolationV1.AVAILABLE_AFTER_DECISION
        elif clocks.received_time > context.as_of:
            violation = PointInTimeViolationV1.RECEIVED_AFTER_DECISION
        elif clocks.processed_time > context.as_of:
            violation = PointInTimeViolationV1.PROCESSED_AFTER_DECISION
        elif not (
            clocks.observed_time
            <= clocks.available_time
            <= clocks.received_time
            <= clocks.processed_time
        ):
            violation = PointInTimeViolationV1.CLOCK_ORDER_INVALID
        elif (
            field_class
            in {
                PointInTimeFieldClassV1.EVENT_OUTCOME,
                PointInTimeFieldClassV1.SETTLEMENT,
            }
            and clocks.effective_time > context.as_of
        ):
            violation = PointInTimeViolationV1.EFFECTIVE_AFTER_DECISION
        elif field_class is PointInTimeFieldClassV1.REVISION:
            if prior_revision_available_time is not None:
                prior = parse_utc(
                    prior_revision_available_time,
                    field_name="prior_revision_available_time",
                )
                if prior > context.as_of or clocks.available_time < prior:
                    violation = PointInTimeViolationV1.REVISION_LEAKAGE

        if violation is not None:
            raise PointInTimeError(
                ReasonCode.POINT_IN_TIME_VIOLATION,
                f"{field_class.value} rejected by {violation.value}",
            )
        return PointInTimeReceiptV1(
            receipt_id=receipt_id,
            field_class=field_class,
            context_id=context.context_id,
            as_of_time=context.as_of.astimezone(UTC),
            admitted=True,
            checked_clocks=cls.CHECKED_CLOCKS,
        )


def classify_point_in_time_semantics(text: str) -> PointInTimeFieldClassV1:
    """Map the frozen semantic text to one of the five centralized classes."""

    token = text.upper()
    if "SETTLEMENT" in token:
        return PointInTimeFieldClassV1.SETTLEMENT
    if "EVENT_OUTCOME" in token or "OUTCOME" in token and "EFFECTIVE" in token:
        return PointInTimeFieldClassV1.EVENT_OUTCOME
    if "REVISION" in token:
        return PointInTimeFieldClassV1.REVISION
    if "EFFECTIVE TIME MAY BE LATER" in token or "SCHEDULED" in token:
        return PointInTimeFieldClassV1.SCHEDULED_EFFECTIVE_FACT
    return PointInTimeFieldClassV1.OBSERVATION


# S1-PIT-DATA-PHASE-A-01 contracts.  The V1 contracts above remain the exact
# compatibility surface for the existing computation-control-plane callers.
class PITReasonCodeV1(StrEnum):
    PIT_SCOPE_NOT_SELECTED = "PIT_SCOPE_NOT_SELECTED"
    PIT_RIGHTS_NOT_ADMITTED = "PIT_RIGHTS_NOT_ADMITTED"
    PIT_SOURCE_CURRENTIZATION_STALE = "PIT_SOURCE_CURRENTIZATION_STALE"
    PIT_ENDPOINT_NOT_ALLOWLISTED = "PIT_ENDPOINT_NOT_ALLOWLISTED"
    PIT_PRIVATE_FIELD_CLASS_REJECTED = "PIT_PRIVATE_FIELD_CLASS_REJECTED"
    PIT_SCHEMA_OR_WIRE_DIALECT_INVALID = "PIT_SCHEMA_OR_WIRE_DIALECT_INVALID"
    PIT_DECIMAL_OR_SCALE_INVALID = "PIT_DECIMAL_OR_SCALE_INVALID"
    PIT_TICK_GRID_INVALID = "PIT_TICK_GRID_INVALID"
    PIT_QUANTITY_GRID_INVALID = "PIT_QUANTITY_GRID_INVALID"
    PIT_BOOK_CROSSED_INVALID = "PIT_BOOK_CROSSED_INVALID"
    PIT_PROVIDER_SEQUENCE_UNAVAILABLE = "PIT_PROVIDER_SEQUENCE_UNAVAILABLE"
    PIT_SEQUENCE_GAP = "PIT_SEQUENCE_GAP"
    PIT_CONFLICTING_DUPLICATE = "PIT_CONFLICTING_DUPLICATE"
    PIT_ANCHOR_REQUIRED = "PIT_ANCHOR_REQUIRED"
    PIT_CLOCK_DOMAIN_MISMATCH = "PIT_CLOCK_DOMAIN_MISMATCH"
    PIT_WALL_CLOCK_UNCERTAIN = "PIT_WALL_CLOCK_UNCERTAIN"
    PIT_PROVIDER_PUBLICATION_TIME_UNAVAILABLE = (
        "PIT_PROVIDER_PUBLICATION_TIME_UNAVAILABLE"
    )
    PIT_TOP_LEVEL_DEPTH_ONLY = "PIT_TOP_LEVEL_DEPTH_ONLY"
    PIT_CURRENT_STATE_PARITY_FAILED = "PIT_CURRENT_STATE_PARITY_FAILED"
    PIT_SOURCE_MAINTENANCE = "PIT_SOURCE_MAINTENANCE"
    PIT_SOURCE_UNAVAILABLE = "PIT_SOURCE_UNAVAILABLE"
    PIT_DURABLE_COMMIT_INCOMPLETE = "PIT_DURABLE_COMMIT_INCOMPLETE"
    PIT_RECONSTRUCTION_DIVERGENCE = "PIT_RECONSTRUCTION_DIVERGENCE"
    PIT_CAPABILITY_UNAVAILABLE = "PIT_CAPABILITY_UNAVAILABLE"
    PIT_LIFECYCLE_BLOCKED = "PIT_LIFECYCLE_BLOCKED"
    PIT_FRESHNESS_EXPIRED = "PIT_FRESHNESS_EXPIRED"
    PIT_EFFECT_AUTHORITY_FORBIDDEN = "PIT_EFFECT_AUTHORITY_FORBIDDEN"


class PITEventKindV2(StrEnum):
    CATALOG = "CATALOG"
    LIFECYCLE = "LIFECYCLE"
    BOOK_SNAPSHOT = "BOOK_SNAPSHOT"
    BOOK_DELTA = "BOOK_DELTA"
    BOOK_REPLACEMENT = "BOOK_REPLACEMENT"
    BBO = "BBO"
    TRADE = "TRADE"
    SETTLEMENT = "SETTLEMENT"
    REFERENCE_PRICE = "REFERENCE_PRICE"
    HEARTBEAT = "HEARTBEAT"
    SOURCE_STATUS = "SOURCE_STATUS"


class PITTransportStateV1(StrEnum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED_HEALTHY = "CONNECTED_HEALTHY"
    HEARTBEAT_OVERDUE = "HEARTBEAT_OVERDUE"
    SOURCE_MAINTENANCE = "SOURCE_MAINTENANCE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


class PITAnchorStateV1(StrEnum):
    ANCHOR_REQUIRED = "ANCHOR_REQUIRED"
    ANCHOR_ACCEPTED = "ANCHOR_ACCEPTED"
    REANCHOR_REQUIRED = "REANCHOR_REQUIRED"


class PITContinuityStateV3(StrEnum):
    NOT_APPLICABLE_CURRENT_STATE_FRAME = "NOT_APPLICABLE_CURRENT_STATE_FRAME"
    SEQUENCE_UNAVAILABLE = "SEQUENCE_UNAVAILABLE"
    CONTIGUOUS = "CONTIGUOUS"
    GAP_DETECTED = "GAP_DETECTED"
    RECOVERY_IN_PROGRESS = "RECOVERY_IN_PROGRESS"


class PITIntegrityStateV1(StrEnum):
    UNVALIDATED = "UNVALIDATED"
    VALID = "VALID"
    CORRUPT = "CORRUPT"
    CURRENT_STATE_PARITY_FAILED = "CURRENT_STATE_PARITY_FAILED"


class PITAvailabilityStateV2(StrEnum):
    UNAVAILABLE = "UNAVAILABLE"
    AVAILABLE_CURRENT_STATE = "AVAILABLE_CURRENT_STATE"
    AVAILABLE_CHANGE_LEVEL = "AVAILABLE_CHANGE_LEVEL"
    STALE = "STALE"
    RIGHTS_BLOCKED = "RIGHTS_BLOCKED"
    LIFECYCLE_BLOCKED = "LIFECYCLE_BLOCKED"
    CLOCK_BLOCKED = "CLOCK_BLOCKED"


class PITEventDispositionV1(StrEnum):
    COMMITTED = "COMMITTED"
    DUPLICATE_IGNORED = "DUPLICATE_IGNORED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"


class PITDepthClassV2(StrEnum):
    COMPLETE_PROVIDER_SNAPSHOT = "COMPLETE_PROVIDER_SNAPSHOT"
    INCREMENTAL_FROM_COMPLETE_ANCHOR = "INCREMENTAL_FROM_COMPLETE_ANCHOR"
    PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME = (
        "PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME"
    )
    BBO_ONLY = "BBO_ONLY"


class PITInputAvailabilityV2(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE_SOURCE_FIELD = "UNAVAILABLE_SOURCE_FIELD"
    UNAVAILABLE_PROVIDER_SEQUENCE = "UNAVAILABLE_PROVIDER_SEQUENCE"
    UNAVAILABLE_PROVIDER_PUBLICATION_TIME = (
        "UNAVAILABLE_PROVIDER_PUBLICATION_TIME"
    )
    UNAVAILABLE_EXACT_TRADE_IDENTITY = "UNAVAILABLE_EXACT_TRADE_IDENTITY"
    UNAVAILABLE_CHANGE_LEVEL_HISTORY = "UNAVAILABLE_CHANGE_LEVEL_HISTORY"
    UNAVAILABLE_FULL_DEPTH = "UNAVAILABLE_FULL_DEPTH"
    UNAVAILABLE_RIGHTS = "UNAVAILABLE_RIGHTS"
    UNAVAILABLE_FRESHNESS = "UNAVAILABLE_FRESHNESS"
    UNAVAILABLE_CONTINUITY = "UNAVAILABLE_CONTINUITY"
    UNAVAILABLE_LIFECYCLE = "UNAVAILABLE_LIFECYCLE"
    UNAVAILABLE_PRECISION = "UNAVAILABLE_PRECISION"
    UNAVAILABLE_CLOCK = "UNAVAILABLE_CLOCK"
    UNAVAILABLE_SCOPE = "UNAVAILABLE_SCOPE"


_PIT_REASON_TO_COARSE_REASON_V1: Mapping[PITReasonCodeV1, ReasonCode] = (
    MappingProxyType(
        {
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED: ReasonCode.CAPABILITY_DENIED,
            PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED: ReasonCode.SOURCE_RIGHTS_BLOCKED,
            PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE: ReasonCode.SOURCE_EPOCH_STALE,
            PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED: ReasonCode.CAPABILITY_DENIED,
            PITReasonCodeV1.PIT_PRIVATE_FIELD_CLASS_REJECTED: ReasonCode.PRIVATE_STATE_FORBIDDEN,
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID: ReasonCode.SCHEMA_MISMATCH,
            PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID: ReasonCode.INVALID_NUMERIC_INPUT,
            PITReasonCodeV1.PIT_TICK_GRID_INVALID: ReasonCode.UNIT_BASIS_OR_PRECISION_INVALID,
            PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID: ReasonCode.UNIT_BASIS_OR_PRECISION_INVALID,
            PITReasonCodeV1.PIT_BOOK_CROSSED_INVALID: ReasonCode.INVALID_CONTRACT,
            PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE: ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID,
            PITReasonCodeV1.PIT_SEQUENCE_GAP: ReasonCode.SEQUENCE_GAP,
            PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE: ReasonCode.DUPLICATE_EVENT_CONFLICT,
            PITReasonCodeV1.PIT_ANCHOR_REQUIRED: ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID,
            PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH: ReasonCode.CLOCK_DOMAIN_MISMATCH,
            PITReasonCodeV1.PIT_WALL_CLOCK_UNCERTAIN: ReasonCode.POINT_IN_TIME_VIOLATION,
            PITReasonCodeV1.PIT_PROVIDER_PUBLICATION_TIME_UNAVAILABLE: ReasonCode.POINT_IN_TIME_VIOLATION,
            PITReasonCodeV1.PIT_TOP_LEVEL_DEPTH_ONLY: ReasonCode.CAPABILITY_DENIED,
            PITReasonCodeV1.PIT_CURRENT_STATE_PARITY_FAILED: ReasonCode.SOURCE_CONFLICT,
            PITReasonCodeV1.PIT_SOURCE_MAINTENANCE: ReasonCode.SOURCE_EPOCH_STALE,
            PITReasonCodeV1.PIT_SOURCE_UNAVAILABLE: ReasonCode.PERSISTENCE_UNAVAILABLE,
            PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE: ReasonCode.PERSISTENCE_UNAVAILABLE,
            PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE: ReasonCode.PERSISTENCE_CONFLICT,
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE: ReasonCode.CAPABILITY_DENIED,
            PITReasonCodeV1.PIT_LIFECYCLE_BLOCKED: ReasonCode.UNKNOWN_LIFECYCLE_STATE,
            PITReasonCodeV1.PIT_FRESHNESS_EXPIRED: ReasonCode.FRESHNESS_VIOLATION,
            PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN: ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
        }
    )
)
if set(_PIT_REASON_TO_COARSE_REASON_V1) != set(PITReasonCodeV1):
    raise RuntimeError("PIT reason/coarse-reason mapping is not total")


class PITDataContractErrorV1(PointInTimeError):
    """One typed PIT failure carrying exact and existing coarse reason classes."""

    def __init__(self, pit_reason_code: PITReasonCodeV1, message: str) -> None:
        if type(pit_reason_code) is not PITReasonCodeV1:
            raise TypeError("pit_reason_code must be an exact PITReasonCodeV1")
        if type(message) is not str or not message or message != message.strip():
            raise TypeError("PIT error message must be canonical nonempty text")
        self.pit_reason_code = pit_reason_code
        self.coarse_reason_code = _PIT_REASON_TO_COARSE_REASON_V1[pit_reason_code]
        super().__init__(
            self.coarse_reason_code,
            f"{pit_reason_code.value}: {message}",
        )


@dataclass(frozen=True, slots=True)
class PublicStreamContinuityWitnessV1:
    profile_id: object
    capture_session_id: str
    connection_epoch: int
    subscription_id_or_none: int | None
    observation_ref: str
    previous_stream_observation_ref_or_none: str | None
    sequence_start_or_none: int | None
    sequence_end_or_none: int | None
    covered_from_or_none: int | None
    covered_through_or_none: int | None
    generation: int
    disposition: str
    affected_instrument_ids: tuple[str, ...]
    original_observation_refs: tuple[str, ...]

    def __post_init__(self):
        from .receipts import _public_profile_v1

        _public_profile_v1(self.profile_id)
        for value in (self.capture_session_id, self.observation_ref):
            _native_ident(value)
        if self.previous_stream_observation_ref_or_none is not None:
            _native_ident(self.previous_stream_observation_ref_or_none)
        _public_counter_v1(self.connection_epoch, allow_zero=True)
        _public_counter_v1(self.generation, allow_zero=True)
        if self.subscription_id_or_none is not None:
            _public_counter_v1(self.subscription_id_or_none)
        _public_refs_v1(self.affected_instrument_ids, allow_empty=True)
        _public_refs_v1(self.original_observation_refs)
        _native_require(self.observation_ref in self.original_observation_refs
                        and (self.previous_stream_observation_ref_or_none is None
                             or self.previous_stream_observation_ref_or_none in self.original_observation_refs),
                        "continuity witness references an absent original")
        _native_require(type(self.disposition) is str and self.disposition in {
            "ANCHOR", "CONTIGUOUS", "DUPLICATE", "CONTROL", "SEQUENCE_UNAVAILABLE"},
            "invalid stream disposition")
        values = (self.sequence_start_or_none, self.sequence_end_or_none,
                  self.covered_from_or_none, self.covered_through_or_none)
        if self.disposition == "SEQUENCE_UNAVAILABLE" or (self.disposition == "CONTROL" and self.sequence_start_or_none is None):
            _native_require(all(value is None for value in values), "unavailable sequence cannot be invented")
        else:
            for value in values:
                _public_counter_v1(value, allow_zero=True)
            _native_require(self.covered_from_or_none <= self.sequence_start_or_none
                            <= self.sequence_end_or_none <= self.covered_through_or_none,
                            "invalid covered stream interval")


_PUBLIC_STREAM_WITNESSES_V1 = {}


def _build_public_stream_continuity_v1(*, session) -> PublicStreamContinuityWitnessV1:
    """Receiving-session issuance from its retained original prefix, never a flag."""
    import base64
    from dataclasses import replace
    from ..selected_venues.market_data import PublicMarketDataSessionV1, _PUBLIC_SESSIONS_V1
    from ..market_data_ingest.adapter import _public_native_tree_v1, translate_public_observation_v1, PublicDataReadRequestV1
    from ..market_data_ingest.binding import PublicMetadataSnapshotV1, SelectedPITPublicDataContractV2
    from .source_policy import PublicDataSourceBindingV1
    from .stage1_launch_graph import Stage1VenueProfileIdV1

    _native_require(type(session) is PublicMarketDataSessionV1
                    and _PUBLIC_SESSIONS_V1.get(id(session)) is session and session._observations,
                    "continuity requires its receiving session")
    facts, _, _ = session._guard_v1()
    for name, cls in (("requests", PublicDataReadRequestV1), ("metadata", PublicMetadataSnapshotV1),
                      ("contracts", SelectedPITPublicDataContractV2), ("source_bindings", PublicDataSourceBindingV1)):
        rows = session._inputs.get(name)
        _native_require(type(rows) is tuple and rows and all(type(row) is cls for row in rows),
                        "missing exact stream input selection: " + name)
    _native_ident(session._inputs.get("wall_clock_source_id"))
    current = session._observations[-1]
    _native_require(current.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT
                    and current.operation_id == "K_WS", "selected continuity algorithm unavailable")

    def original_tree(observation):
        encoded = observation.raw_body_b64
        return _public_native_tree_v1(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)),
                                     maximum_bytes=session._budget.max_message_bytes)

    def stream_number(tree, name):
        message = tree.get("msg")
        _native_require(type(message) is dict, "native stream msg required")
        if name in tree and name in message:
            _native_require(type(tree[name]) is type(message[name]) and tree[name] == message[name],
                            "conflicting native stream aliases")
        value = tree.get(name, message.get(name))
        if value is not None:
            _public_counter_v1(value, allow_zero=name == "seq")
        return value

    sid = stream_number(original_tree(current), "sid")
    _native_require(sid is not None, "native stream member has no subscription identity")
    last_sequence = first_sequence = None
    previous_ref = last_ref = None
    seen, instruments, originals = {}, set(), []
    subscribed = False
    acknowledgement_ordinal = None
    subscription_request = None
    clocks = {}
    disposition = "CONTROL"
    sequence = None
    for observation in session._observations:
        if observation.operation_id != "K_WS" or observation.connection_epoch != current.connection_epoch:
            continue
        _native_require(observation.profile_id is current.profile_id
                        and observation.capture_session_id == current.capture_session_id
                        and observation.scope_generation == facts["scope_generation"], "mixed original stream custody")
        tree = original_tree(observation)
        if stream_number(tree, "sid") != sid:
            continue
        requests = [row for row in session._inputs["requests"] if row.request_id == observation.request_ref]
        _native_require(len(requests) == 1, "original stream member has no unique admitted request")
        request = requests[0]
        sources = [row for row in session._inputs["source_bindings"] if row.binding_id == request.source_binding_ref]
        _native_require(len(sources) == 1, "stream source association is ambiguous")
        contracts = [row for row in session._inputs["contracts"] if row.profile_id is current.profile_id
                     and row.source_contract_version == request.native_contract_version
                     and (row.source_contract_version, row.source_currentization_receipt_ref, row.rights_receipt_ref)
                     in set(zip(sources[0].source_contract_versions, sources[0].source_receipt_refs,
                                sources[0].rights_receipt_refs))]
        _native_require(len(contracts) == 1, "stream contract association is ambiguous")
        selected_metadata = []
        for ref in request.metadata_refs:
            matches = [row for row in session._inputs["metadata"] if row.metadata_id == ref]
            _native_require(len(matches) == 1, "stream metadata association is missing or ambiguous")
            selected_metadata.append(matches[0])
        retained = session._observation_plans.get(observation.observation_id)
        if retained is not None:
            _native_require(type(retained) is tuple and len(retained) == 4
                and retained[1] is sources[0] and retained[3] is contracts[0]
                and type(retained[2]) is tuple and all(type(row) is PublicMetadataSnapshotV1 for row in retained[2])
                and retained[0] == replace(request,metadata_refs=tuple(row.metadata_id for row in retained[2]))
                and {row.instrument_id for row in retained[2]} == set(request.instrument_ids),
                "stream observation metadata plan differs from its admitted request")
            request, _, selected_metadata, _ = retained
        else:
            _native_require(not facts["native_qualified"], "native stream observation has no received metadata plan")
        translated = translate_public_observation_v1(observation=observation, metadata=tuple(selected_metadata),
            source_binding=sources[0], translation_context=dict(request=request, contract=contracts[0],
                wall_clock_source_id=session._inputs["wall_clock_source_id"]))
        originals.append(observation)
        kind = tree.get("type")
        _native_require(kind in {"subscribed", "ok", "unsubscribed", "orderbook_snapshot", "orderbook_delta",
                                 "trade", "market_lifecycle_v2", "event_lifecycle", "event_fee_update"},
                        "invalid member of retained stream prefix")
        sequence = stream_number(tree, "seq")
        if kind == "subscribed":
            if acknowledgement_ordinal is not None:
                _native_require(subscribed and observation.request_ref == subscription_request
                                and sequence is not None and sequence in seen
                                and seen[sequence] == observation.raw_body_b64,
                                "subscription identity reused without an identical original sequenced acknowledgement")
            else:
                subscribed, subscription_request = True, observation.request_ref
                acknowledgement_ordinal = observation.receive_ordinal
        else:
            _native_require(subscribed and observation.request_ref == subscription_request,
                            "stream member has no matching acknowledged subscription")
        if sequence is None:
            _native_require(kind == "subscribed", "sequenced stream member has no native seq")
            continue
        previous_ref = last_ref
        if sequence in seen:
            _native_require(seen[sequence] == observation.raw_body_b64, "conflicting original stream sequence reuse")
            disposition = "DUPLICATE"
        else:
            if last_sequence is not None and sequence != last_sequence + 1:
                raise PITDataContractErrorV1(PITReasonCodeV1.PIT_SEQUENCE_GAP, "missing original subscription stream member")
            seen[sequence] = observation.raw_body_b64
            disposition = "ANCHOR" if last_sequence is None else "CONTIGUOUS"
            first_sequence = sequence if first_sequence is None else first_sequence
            last_sequence, last_ref = sequence, observation.observation_id
        if kind in {"orderbook_snapshot", "orderbook_delta", "trade", "market_lifecycle_v2"}:
            instrument = tree["msg"].get("market_ticker")
            _native_require(type(instrument) is str and (instrument in session._scope.instrument_ids
                            or kind == "market_lifecycle_v2" and "GLOBAL_PUBLIC_LIFECYCLE" in session._scope.receive_scope_classes),
                            "stream event is outside the selected instruments")
            if instrument in session._scope.instrument_ids:
                instruments.add(instrument)
            if "clock" in tree["msg"]:
                clock = tree["msg"]["clock"]
                _public_counter_v1(clock, allow_zero=True)
                _native_require(instrument not in clocks or clock >= clocks[instrument], "market clock regressed")
                clocks[instrument] = clock
        elif kind in {"event_lifecycle","event_fee_update"}:
            _native_require("GLOBAL_PUBLIC_LIFECYCLE" in session._scope.receive_scope_classes,
                            "global Event notification is outside the received-data scope")
            instruments.update(translated.stream_disposition["instrument_ids"])
        if kind == "unsubscribed":
            subscribed = False
    _native_require((sequence is not None and first_sequence is not None)
                    or (kind == "subscribed" and first_sequence is last_sequence is None and len(originals) == 1),
                    "current member has no covered sequence or isolated subscription acknowledgement")
    witness = PublicStreamContinuityWitnessV1(current.profile_id, current.capture_session_id, current.connection_epoch,
        sid, current.observation_id, previous_ref, sequence, sequence, first_sequence, last_sequence,
        acknowledgement_ordinal, disposition, tuple(sorted(instruments)), tuple(row.observation_id for row in originals))
    _PUBLIC_STREAM_WITNESSES_V1[id(witness)] = (witness, session, tuple(originals),
        tuple(row.raw_body_b64 for row in originals), facts["scope_generation"], acknowledgement_ordinal)
    return witness


def _issue_public_stream_continuity_v1(*, session) -> PublicStreamContinuityWitnessV1:
    try:
        return _build_public_stream_continuity_v1(session=session)
    except BaseException:
        from ..selected_venues.market_data import PublicMarketDataSessionV1, _PUBLIC_SESSIONS_V1

        if type(session) is PublicMarketDataSessionV1 and _PUBLIC_SESSIONS_V1.get(id(session)) is session:
            authority = session._binding._authority
            if authority is None:
                session._binding._failed = True
            else:
                with authority._lock:
                    session._binding._failed = True
        raise


def _require_public_stream_witness_custody_v1(witness):
    """Verify the original private witness before interpreting any disposition."""
    issued = _PUBLIC_STREAM_WITNESSES_V1.get(id(witness))
    _native_require(type(witness) is PublicStreamContinuityWitnessV1 and issued is not None and issued[0] is witness,
                    "manufactured continuity witness cannot promote a stream")
    from .source_policy import _public_binding_facts_v1
    from ..selected_venues.market_data import _PUBLIC_SESSIONS_V1

    _, session, originals, raw, source_generation, stream_generation = issued
    facts = _public_binding_facts_v1(session._binding)
    _native_require(_PUBLIC_SESSIONS_V1.get(id(session)) is session and session._binding._owner is session,
                    "continuity receiving-session custody changed")
    _native_require(tuple(row.raw_body_b64 for row in originals) == raw
                    and all(any(saved is row for saved in session._observations) for row in originals),
                    "original stream prefix custody changed")
    _native_require(originals and witness.observation_ref == originals[-1].observation_id
        and witness.profile_id is originals[-1].profile_id
        and witness.capture_session_id == originals[-1].capture_session_id
        and witness.connection_epoch == originals[-1].connection_epoch
        and source_generation == facts["scope_generation"] and witness.generation == stream_generation,
        "continuity witness differs from its original stream generation")
    return issued


def _require_public_stream_continuity_v1(witness, *, candidate, previous_sequence: int | None) -> None:
    """Validate private issuance and original prefix custody at the reducer seam."""
    from .receipts import _public_canonical_frame_ref_v1
    from .source_policy import _public_binding_facts_v1

    _, session, originals, raw, source_generation, stream_generation = _require_public_stream_witness_custody_v1(witness)
    facts = _public_binding_facts_v1(session._binding)
    frame_ref = _public_canonical_frame_ref_v1(witness.observation_ref)
    book_event = candidate.event_kind in {PITEventKindV2.BOOK_SNAPSHOT, PITEventKindV2.BOOK_DELTA}
    if not book_event:
        import base64
        from ..market_data_ingest.adapter import _public_native_tree_v1

        current = originals[-1]
        tree = _public_native_tree_v1(base64.urlsafe_b64decode(current.raw_body_b64 + "=" * (-len(current.raw_body_b64) % 4)),
                                     maximum_bytes=session._budget.max_message_bytes)
        _native_require((candidate.event_kind, tree.get("type")) in {
            (PITEventKindV2.TRADE, "trade"), (PITEventKindV2.LIFECYCLE, "market_lifecycle_v2")}
            and candidate.provider_sequence_start_or_none is candidate.provider_sequence_end_or_none is None,
            "non-book stream evidence cannot claim provider book-sequence identity")
    _native_require(witness.disposition in {"ANCHOR", "CONTIGUOUS"}
                    and witness.profile_id is candidate.profile_id
                    and witness.capture_session_id == candidate.capture_session_id
                    and str(witness.connection_epoch) == candidate.connection_epoch
                    and str(witness.subscription_id_or_none) == candidate.provider_subscription_id_or_none
                    and source_generation == facts["scope_generation"] and witness.generation == stream_generation
                    and candidate.event_record_id == frame_ref + "::CANONICAL-EVENT-V2"
                    and candidate.instrument_id in witness.affected_instrument_ids
                    and witness.sequence_start_or_none == witness.sequence_end_or_none
                    and (not book_event or (witness.sequence_end_or_none == candidate.provider_sequence_start_or_none
                         == candidate.provider_sequence_end_or_none and (previous_sequence is None
                         or witness.covered_from_or_none <= previous_sequence + 1 <= witness.sequence_end_or_none)))
                    and witness.sequence_end_or_none <= witness.covered_through_or_none,
                    "continuity witness does not cover this market transition")


def _pit_text(value: object, name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


def _pit_utc(value: object, name: str) -> datetime:
    if (
        type(value) is not datetime
        or value.tzinfo is None
        or value.utcoffset() is None
        or value.utcoffset().total_seconds() != 0
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
            f"{name} must be an aware UTC datetime",
        )
    return value.astimezone(UTC)


def _pit_optional_utc(value: object, name: str) -> datetime | None:
    if value is None:
        return None
    return _pit_utc(value, name)


def _pit_nonnegative_int(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
            f"{name} must be a nonnegative exact integer",
        )
    return value


@dataclass(frozen=True, slots=True)
class PITClockSetV3:
    provider_event_time_utc_or_none: datetime | None
    provider_publication_time_utc_or_none: datetime | None
    qtt_received_at_utc: datetime
    qtt_received_monotonic_ns: int
    qtt_parse_completed_at_utc: datetime
    qtt_parse_completed_monotonic_ns: int
    durable_commit_completed_at_utc: datetime
    durable_commit_completed_monotonic_ns: int
    strategy_available_at_utc: datetime
    strategy_available_monotonic_ns: int
    revision_effective_time_utc_or_none: datetime | None
    settlement_finality_time_utc_or_none: datetime | None
    process_epoch_id: str
    monotonic_clock_id: str
    wall_clock_source_id: str
    clock_quality_receipt_ref: str
    wall_clock_uncertainty_ns: int

    def __post_init__(self) -> None:
        for name in (
            "provider_event_time_utc_or_none",
            "provider_publication_time_utc_or_none",
            "revision_effective_time_utc_or_none",
            "settlement_finality_time_utc_or_none",
        ):
            object.__setattr__(self, name, _pit_optional_utc(getattr(self, name), name))
        for name in (
            "qtt_received_at_utc",
            "qtt_parse_completed_at_utc",
            "durable_commit_completed_at_utc",
            "strategy_available_at_utc",
        ):
            object.__setattr__(self, name, _pit_utc(getattr(self, name), name))
        for name in (
            "qtt_received_monotonic_ns",
            "qtt_parse_completed_monotonic_ns",
            "durable_commit_completed_monotonic_ns",
            "strategy_available_monotonic_ns",
            "wall_clock_uncertainty_ns",
        ):
            _pit_nonnegative_int(getattr(self, name), name)
        for name in (
            "process_epoch_id",
            "monotonic_clock_id",
            "wall_clock_source_id",
            "clock_quality_receipt_ref",
        ):
            _pit_text(getattr(self, name), name)


@dataclass(frozen=True, slots=True)
class PITClockAdmissionReceiptV3:
    receipt_id: str
    process_epoch_id: str
    monotonic_clock_id: str
    admitted: bool
    cross_clock_comparison_performed: bool
    provider_event_time_present: bool
    provider_publication_time_present: bool
    checked_relations: tuple[str, ...]
    wall_clock_uncertainty_ns: int
    decision_time_utc_or_none: datetime | None
    reason_code_or_none: PITReasonCodeV1 | None = None

    def __post_init__(self) -> None:
        _pit_text(self.receipt_id, "receipt_id")
        _pit_text(self.process_epoch_id, "process_epoch_id")
        _pit_text(self.monotonic_clock_id, "monotonic_clock_id")
        for name in (
            "admitted",
            "cross_clock_comparison_performed",
            "provider_event_time_present",
            "provider_publication_time_present",
        ):
            if type(getattr(self, name)) is not bool:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact boolean",
                )
        if type(self.checked_relations) is not tuple or any(
            type(value) is not str or not value for value in self.checked_relations
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "checked_relations must be an exact text tuple",
            )
        _pit_nonnegative_int(self.wall_clock_uncertainty_ns, "wall_clock_uncertainty_ns")
        object.__setattr__(
            self,
            "decision_time_utc_or_none",
            _pit_optional_utc(self.decision_time_utc_or_none, "decision_time_utc_or_none"),
        )
        if self.admitted is not True or self.reason_code_or_none is not None:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
                "only an admitted clock receipt may be constructed",
            )


def validate_pit_clock_set_v3(
    clocks: PITClockSetV3,
    *,
    receipt_id: str,
    decision_time_utc_or_none: datetime | None = None,
    requires_cross_clock_comparison: bool = False,
    requires_provider_event_time: bool = False,
    requires_provider_publication_time: bool = False,
    requires_revision_at_decision: bool = False,
    requires_finality_at_decision: bool = False,
    provider_publication_time_is_source_proven: bool = False,
    maximum_wall_clock_uncertainty_ns_or_none: int | None = None,
    required_process_epoch_id_or_none: str | None = None,
    required_monotonic_clock_id_or_none: str | None = None,
) -> PITClockAdmissionReceiptV3:
    """Validate one supplied clock set without consulting a process clock."""

    if type(clocks) is not PITClockSetV3:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
            "clocks must be an exact PITClockSetV3",
        )
    _pit_text(receipt_id, "receipt_id")
    for name, value in (
        ("requires_cross_clock_comparison", requires_cross_clock_comparison),
        ("requires_provider_event_time", requires_provider_event_time),
        ("requires_provider_publication_time", requires_provider_publication_time),
        ("requires_revision_at_decision", requires_revision_at_decision),
        ("requires_finality_at_decision", requires_finality_at_decision),
        (
            "provider_publication_time_is_source_proven",
            provider_publication_time_is_source_proven,
        ),
    ):
        if type(value) is not bool:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                f"{name} must be an exact boolean",
            )
    monotonic_values = (
        clocks.qtt_received_monotonic_ns,
        clocks.qtt_parse_completed_monotonic_ns,
        clocks.durable_commit_completed_monotonic_ns,
        clocks.strategy_available_monotonic_ns,
    )
    if monotonic_values != tuple(sorted(monotonic_values)):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
            "same-process monotonic clock order is invalid",
        )
    for name, actual, required in (
        (
            "required_process_epoch_id_or_none",
            clocks.process_epoch_id,
            required_process_epoch_id_or_none,
        ),
        (
            "required_monotonic_clock_id_or_none",
            clocks.monotonic_clock_id,
            required_monotonic_clock_id_or_none,
        ),
    ):
        if required is not None:
            _pit_text(required, name)
            if actual != required:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
                    "clock set does not match the required process/clock domain",
                )
    if requires_provider_event_time and clocks.provider_event_time_utc_or_none is None:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
            "the requested capability requires provider event time",
        )
    if (
        clocks.provider_publication_time_utc_or_none is not None
        and provider_publication_time_is_source_proven is not True
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_PROVIDER_PUBLICATION_TIME_UNAVAILABLE,
            "provider publication time lacks distinct source-field proof",
        )
    if (
        requires_provider_publication_time
        and clocks.provider_publication_time_utc_or_none is None
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_PROVIDER_PUBLICATION_TIME_UNAVAILABLE,
            "the requested capability requires a distinct provider publication time",
        )
    checked = [
        "receive_monotonic<=parse_monotonic",
        "parse_monotonic<=commit_complete_monotonic",
        "commit_complete_monotonic<=strategy_available_monotonic",
    ]
    if requires_cross_clock_comparison:
        if (
            maximum_wall_clock_uncertainty_ns_or_none is None
            or type(maximum_wall_clock_uncertainty_ns_or_none) is not int
            or maximum_wall_clock_uncertainty_ns_or_none < 0
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_WALL_CLOCK_UNCERTAIN,
                "cross-clock comparison requires an exact uncertainty ceiling",
            )
        if clocks.wall_clock_uncertainty_ns > maximum_wall_clock_uncertainty_ns_or_none:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_WALL_CLOCK_UNCERTAIN,
                "wall-clock uncertainty exceeds the requested capability ceiling",
            )
        checked.append("wall_clock_uncertainty<=capability_ceiling")
    elif maximum_wall_clock_uncertainty_ns_or_none is not None:
        _pit_nonnegative_int(
            maximum_wall_clock_uncertainty_ns_or_none,
            "maximum_wall_clock_uncertainty_ns_or_none",
        )
    decision = _pit_optional_utc(decision_time_utc_or_none, "decision_time_utc_or_none")
    if decision is None and (requires_revision_at_decision or requires_finality_at_decision):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
            "PIT_V3_DECISION_REQUIRED",
        )
    if decision is not None:
        if clocks.strategy_available_at_utc > decision:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "strategy availability occurs after the decision cutoff",
            )
        checked.append("strategy_available_at<=decision_time")
        if (
            requires_revision_at_decision
            and (
                clocks.revision_effective_time_utc_or_none is None
                or clocks.revision_effective_time_utc_or_none > decision
            )
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "the requested revision was not effective by the decision cutoff",
            )
        if (
            requires_finality_at_decision
            and (
                clocks.settlement_finality_time_utc_or_none is None
                or clocks.settlement_finality_time_utc_or_none > decision
            )
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_LIFECYCLE_BLOCKED,
                "settlement finality was not available by the decision cutoff",
            )
    return PITClockAdmissionReceiptV3(
        receipt_id=receipt_id,
        process_epoch_id=clocks.process_epoch_id,
        monotonic_clock_id=clocks.monotonic_clock_id,
        admitted=True,
        cross_clock_comparison_performed=requires_cross_clock_comparison,
        provider_event_time_present=clocks.provider_event_time_utc_or_none is not None,
        provider_publication_time_present=(
            clocks.provider_publication_time_utc_or_none is not None
        ),
        checked_relations=tuple(checked),
        wall_clock_uncertainty_ns=clocks.wall_clock_uncertainty_ns,
        decision_time_utc_or_none=decision,
    )


# F12 exact-input composition; typed projections confer no effect authority.
_F12_V1_REFERENCE_REASONS = frozenset(
    (
        'NATIVE_FIELDS',
        'PIT_AVAILABLE_AFTER_DECISION',
        'PIT_CLOCK_ORDER_INVALID',
        'PIT_CONTEXT_AS_OF_MISMATCH',
        'PIT_EFFECTIVE_AFTER_DECISION',
        'PIT_FIELD_CLASS',
        'PIT_OBSERVED_AFTER_DECISION',
        'PIT_PROCESSED_AFTER_DECISION',
        'PIT_RECEIVED_AFTER_DECISION',
        'PIT_REVISION_LEAKAGE',
        'PIT_TIME_PROJECTION_MISMATCH',
        'PIT_UNUSED_PRIOR_REVISION',
        'UTC_NANOSECONDS'
    )
)

_F12_V3_ERROR_CODES = {
    'NATIVE_FIELDS': PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    'BOOLEAN': PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    'TEXT': PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    'IDENTITY': PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    'UTC_NANOSECONDS': PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
    'PIT_TIME_PROJECTION_MISMATCH': PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
    'PIT_V3_INTEGER': PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
    'PIT_V3_UNCERTAINTY_CEILING': PITReasonCodeV1.PIT_WALL_CLOCK_UNCERTAIN,
    'PIT_V3_DECISION_REQUIRED': PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
    'PIT_V3_MONOTONIC_ORDER': PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
    'PIT_V3_CLOCK_DOMAIN': PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
    'PIT_V3_EVENT_TIME_UNAVAILABLE': PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
    'PIT_V3_PUBLICATION_NOT_PROVEN': PITReasonCodeV1.PIT_PROVIDER_PUBLICATION_TIME_UNAVAILABLE,
    'PIT_V3_PUBLICATION_UNAVAILABLE': PITReasonCodeV1.PIT_PROVIDER_PUBLICATION_TIME_UNAVAILABLE,
    'PIT_V3_WALL_CLOCK_UNCERTAIN': PITReasonCodeV1.PIT_WALL_CLOCK_UNCERTAIN,
    'PIT_V3_AVAILABLE_AFTER_DECISION': PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
    'PIT_V3_REVISION_UNAVAILABLE': PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
    'PIT_V3_FINALITY_UNAVAILABLE': PITReasonCodeV1.PIT_LIFECYCLE_BLOCKED,
}

def _native_retail_pit_receipt_bridge(
    clocks,
    *,
    field_class,
    context_as_of,
    prior_revision_available_time=None
):
    """Exact V1 clock relations and lossless receipt companions; no admission.

    UTC integers remain authoritative. A microsecond datetime is a compatibility
    projection only. The existing V3 monotonic, source-proof and clock-quality
    gates must still run; this function neither simulates nor replaces them.
    """
    try:
        names = (
            'observed_time',
            'effective_time',
            'available_time',
            'received_time',
            'processed_time',
            'as_of_time'
        )
        _native_obj(clocks, names)
        _native_require(
            type(field_class) is str and field_class in (
                'OBSERVATION',
                'SCHEDULED_EFFECTIVE_FACT',
                'REVISION',
                'EVENT_OUTCOME',
                'SETTLEMENT'
            ),
            'PIT_FIELD_CLASS'
        )
        values = {name: _native_utc_nanoseconds(clocks[name]) for name in names}
        decision = _native_utc_nanoseconds(context_as_of)
        prior = None
        if prior_revision_available_time is not None:
            _native_require(field_class == 'REVISION', 'PIT_UNUSED_PRIOR_REVISION')
            prior = _native_utc_nanoseconds(prior_revision_available_time)
        _native_require(values['as_of_time'] == decision, 'PIT_CONTEXT_AS_OF_MISMATCH')
        for name, reason in (
            ('observed_time', 'OBSERVED_AFTER_DECISION'),
            ('available_time', 'AVAILABLE_AFTER_DECISION'),
            ('received_time', 'RECEIVED_AFTER_DECISION'),
            ('processed_time', 'PROCESSED_AFTER_DECISION')
        ):
            _native_require(values[name] <= decision, 'PIT_' + reason)
        _native_require(
            values['observed_time'] <= values['available_time'] <= values['received_time'] <= values['processed_time'],
            'PIT_CLOCK_ORDER_INVALID'
        )
        if field_class in ('EVENT_OUTCOME', 'SETTLEMENT'):
            _native_require(values['effective_time'] <= decision, 'PIT_EFFECTIVE_AFTER_DECISION')
        if field_class == 'REVISION' and prior is not None:
            _native_require(
                prior <= decision and values['available_time'] >= prior,
                'PIT_REVISION_LEAKAGE'
            )
        pairs = {name: _native_utc_receipt_pair(clocks[name]) for name in names}
        context_pair = _native_utc_receipt_pair(context_as_of)
        prior_pair = None if prior is None else _native_utc_receipt_pair(prior_revision_available_time)
        all_pairs = list(pairs.values()) + [context_pair] + ([] if prior_pair is None else [prior_pair])
        return {
            'state': 'EXACT_CLOCK_RELATIONS_CHECKED_NOT_ADMISSION',
            'field_class': field_class,
            'clock_pairs': pairs,
            'context_pair': context_pair,
            'prior_revision_pair': prior_pair,
            'datetime_only_is_lossless': all((p['nanosecond_remainder'] == 0 for p in all_pairs)),
            'exact_ns_consumer_required': any((p['nanosecond_remainder'] != 0 for p in all_pairs)),
            'source_accepted': False,
            'runtime_effect_authorized': False,
            'receipt_emitted': False,
            'full_pit_v3_admitted': False
        }
    except ContractValidationError as error:
        detail = _native_reference_reason(error, _F12_V1_REFERENCE_REASONS)
        if detail is None:
            raise
        raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, detail) from error

def _native_retail_pit_v3_bridge(clocks, requirements, *, decision_time):
    """Validate selected exact V3 relations, not source or storage authority.

    All nine requirement keys are explicit. The existing V3 constructor and
    validator must still consume the projected values. Exact companion checks
    occur first and must survive persistence/reconstruction; datetime alone
    cannot justify a decision when precision was lost.
    """
    try:
        optional = (
            'provider_event_time_utc_or_none',
            'provider_publication_time_utc_or_none',
            'revision_effective_time_utc_or_none',
            'settlement_finality_time_utc_or_none'
        )
        wall = (
            'qtt_received_at_utc',
            'qtt_parse_completed_at_utc',
            'durable_commit_completed_at_utc',
            'strategy_available_at_utc'
        )
        mono = (
            'qtt_received_monotonic_ns',
            'qtt_parse_completed_monotonic_ns',
            'durable_commit_completed_monotonic_ns',
            'strategy_available_monotonic_ns'
        )
        ids = (
            'process_epoch_id',
            'monotonic_clock_id',
            'wall_clock_source_id',
            'clock_quality_receipt_ref'
        )
        flags = (
            'requires_cross_clock_comparison',
            'requires_provider_event_time',
            'requires_provider_publication_time',
            'requires_revision_at_decision',
            'requires_finality_at_decision',
            'provider_publication_time_is_source_proven'
        )
        limits = (
            'maximum_wall_clock_uncertainty_ns_or_none',
            'required_process_epoch_id_or_none',
            'required_monotonic_clock_id_or_none'
        )
        _native_obj(clocks, optional + wall + mono + ids + ('wall_clock_uncertainty_ns',))
        _native_obj(requirements, flags + limits)
        for name in flags:
            _native_scalar(requirements[name], 'bool')
        for name in mono + ('wall_clock_uncertainty_ns',):
            _native_require(type(clocks[name]) is int and clocks[name] >= 0, 'PIT_V3_INTEGER')
        for name in ids:
            _native_ident(clocks[name])
        for name in limits[1:]:
            if requirements[name] is not None:
                _native_ident(requirements[name])
        ceiling = requirements[limits[0]]
        _native_require(
            ceiling is None or (type(ceiling) is int and ceiling >= 0),
            'PIT_V3_UNCERTAINTY_CEILING'
        )
        pairs = {
            name: None if clocks[name] is None else _native_utc_receipt_pair(clocks[name]) for name in optional
        }
        pairs.update({name: _native_utc_receipt_pair(clocks[name]) for name in wall})
        decision = None if decision_time is None else _native_utc_receipt_pair(decision_time)
        _native_require(
            decision is not None or not (
                requirements['requires_revision_at_decision'] or requirements['requires_finality_at_decision']
            ),
            'PIT_V3_DECISION_REQUIRED'
        )
        sequence = tuple((clocks[name] for name in mono))
        _native_require(
            all((a <= b for a, b in zip(sequence, sequence[1:]))),
            'PIT_V3_MONOTONIC_ORDER'
        )
        for actual, required in (
            ('process_epoch_id', limits[1]),
            ('monotonic_clock_id', limits[2])
        ):
            _native_require(
                requirements[required] is None or clocks[actual] == requirements[required],
                'PIT_V3_CLOCK_DOMAIN'
            )
        _native_require(
            not requirements['requires_provider_event_time'] or pairs[optional[0]] is not None,
            'PIT_V3_EVENT_TIME_UNAVAILABLE'
        )
        publication = pairs[optional[1]]
        _native_require(
            publication is None or requirements['provider_publication_time_is_source_proven'],
            'PIT_V3_PUBLICATION_NOT_PROVEN'
        )
        _native_require(
            not requirements['requires_provider_publication_time'] or publication is not None,
            'PIT_V3_PUBLICATION_UNAVAILABLE'
        )
        checked = [
            'receive_monotonic<=parse_monotonic',
            'parse_monotonic<=commit_complete_monotonic',
            'commit_complete_monotonic<=strategy_available_monotonic'
        ]
        if requirements['requires_cross_clock_comparison']:
            _native_require(
                ceiling is not None and clocks['wall_clock_uncertainty_ns'] <= ceiling,
                'PIT_V3_WALL_CLOCK_UNCERTAIN'
            )
            checked.append('wall_clock_uncertainty<=capability_ceiling')
        if decision is not None:
            cutoff = int(decision['utc_ns_text'])
            _native_require(
                int(pairs['strategy_available_at_utc']['utc_ns_text']) <= cutoff,
                'PIT_V3_AVAILABLE_AFTER_DECISION'
            )
            checked.append('strategy_available_at_exact_ns<=decision_exact_ns')
            for flag, name, reason in (
                ('requires_revision_at_decision', optional[2], 'PIT_V3_REVISION_UNAVAILABLE'),
                ('requires_finality_at_decision', optional[3], 'PIT_V3_FINALITY_UNAVAILABLE')
            ):
                if requirements[flag]:
                    _native_require(
                        pairs[name] is not None and int(pairs[name]['utc_ns_text']) <= cutoff,
                        reason
                    )
                    checked.append(name + '<=decision_exact_ns')
        projected = copy.deepcopy(clocks)
        for name, pair in pairs.items():
            projected[name] = None if pair is None else pair['receipt_utc_floor']
        all_pairs = [p for p in pairs.values() if p is not None] + ([] if decision is None else [decision])
        lossless = all((p['nanosecond_remainder'] == 0 for p in all_pairs))
        return {
            'state': 'EXACT_V3_RELATIONS_CHECKED_NOT_ADMISSION' if decision is not None else 'INGESTION_CLOCK_SHAPE_CHECKED_NO_DECISION_CUTOFF',
            'clock_pairs': pairs,
            'decision_pair': decision,
            'requirements': copy.deepcopy(requirements),
            'datetime_constructor_text_kwargs': projected,
            'checked_relations': checked,
            'datetime_only_is_lossless': lossless,
            'exact_ns_consumer_required': not lossless,
            'source_accepted': False,
            'publication_proof_authenticated': False,
            'durable_commit_proven': False,
            'strategy_availability_proven': False,
            'full_pit_v3_admitted': False,
            'receipt_emitted': False,
            'posts_cash': False,
            'releases_reservation': False,
            'runtime_effect_authorized': False
        }
    except ContractValidationError as error:
        detail = _native_reference_reason(error, frozenset(_F12_V3_ERROR_CODES))
        if detail is None:
            raise
        raise PITDataContractErrorV1(_F12_V3_ERROR_CODES[detail], detail) from error

def _f12_strict_equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return all((type(k) is str for k in a)) and all((type(k) is str for k in b)) and (a.keys() == b.keys()) and all((_f12_strict_equal(a[k], b[k]) for k in a))
    if type(a) is list:
        return len(a) == len(b) and all((_f12_strict_equal(x, y) for x, y in zip(a, b)))
    return a == b

def _f12_frozen(x):
    if type(x) is dict:
        if any((type(k) is not str for k in x)):
            _f12_schema_stop('F12_WIRE_FIELDS')
        return MappingProxyType({k: _f12_frozen(v) for k, v in x.items()})
    if type(x) is list:
        return tuple((_f12_frozen(v) for v in x))
    if x is None or type(x) in (str, int, bool):
        return x
    _f12_schema_stop('F12_JSON_DOMAIN')

def _f12_thaw(x):
    if isinstance(x, Mapping):
        return {k: _f12_thaw(v) for k, v in x.items()}
    if type(x) is tuple:
        return [_f12_thaw(v) for v in x]
    return x

def _f12_schema_stop(reason):
    raise ContractValidationError(ReasonCode.INVALID_CONTRACT, reason)

def _f12_utc_projection(pair):
    return datetime.fromisoformat(pair['receipt_utc_floor'].replace('Z', '+00:00'))

def _f12_duration_us(value):
    if type(value) is not timedelta:
        _f12_schema_stop('F12_CONTEXT_DURATION_TYPE')
    return (value.days * 86400 + value.seconds) * 1000000 + value.microseconds

def _f12_context_binding(context):
    if type(context) not in (ComputationContextKeyV1, ComputationExecutionContextV1):
        _f12_schema_stop('F12_CONTEXT_TYPE')
    out = {
        'context_type': type(context).__name__,
        'context_id': context.context_id,
        'source_epoch_id': context.source_epoch_id,
        'input_version': context.input_version,
        'as_of_projection': context.as_of.isoformat(timespec='microseconds'),
        'observed_at_projection': context.observed_at.isoformat(timespec='microseconds'),
        'maximum_age_us_text': str(_f12_duration_us(context.maximum_age))
    }
    if type(context) is ComputationExecutionContextV1:
        out.update(
            scope={
                k: getattr(context.scope, k) for k in (
                    'market_scope_id',
                    'venue_scope_id',
                    'event_scope_id',
                    'instrument_or_contract_scope_id',
                    'mode_context_id',
                    'input_snapshot_id'
                )
            },
            binding_profile_version=context.binding_profile_version,
            parameter_policy_version=context.parameter_policy_version,
            implementation_versions=[
                {
                    'math_spec_id': p.math_spec_id,
                    'implementation_id': p.implementation_id
                } for p in context.implementation_versions
            ],
            dependency_graph_id=context.dependency_graph_id,
            dependency_graph_version=context.dependency_graph_version
        )
    return out

@dataclass(frozen=True, slots=True, init=False)
class ExactPITCompositionV1:
    kind: str
    receipt_id: str
    request: Mapping[str, object]
    companion: Mapping[str, object]
    context_binding: Mapping[str, object] | None
    clock_projection: PointInTimeClocksV1 | PITClockSetV3
    typed_check_receipt: PointInTimeReceiptV1 | PITClockAdmissionReceiptV3

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "F12_FACTORY_REQUIRED")

    @classmethod
    def _from_checked(cls, kind, receipt_id, request, companion, ctx, clocks, receipt):
        obj = object.__new__(cls)
        for name, value in zip(
            cls.__dataclass_fields__,
            (
                kind,
                receipt_id,
                _f12_frozen(request),
                _f12_frozen(companion),
                None if ctx is None else _f12_frozen(ctx),
                clocks,
                receipt
            )
        ):
            object.__setattr__(obj, name, value)
        return obj

    def to_payload(self):
        return {
            'format': 'QTT_F12_EXACT_COMPOSITION_V1',
            'kind': self.kind,
            'receipt_id': self.receipt_id,
            'request': _f12_thaw(self.request),
            'companion': _f12_thaw(self.companion),
            'context_binding': None if self.context_binding is None else _f12_thaw(self.context_binding)
        }

def compose_exact_pit_v1(
    clocks: dict[str, str],
    *,
    field_class: PointInTimeFieldClassV1,
    context: ComputationContextKeyV1,
    context_as_of: str,
    context_observed_at: str,
    receipt_id: str,
    prior_revision_available_time: str | None = None
) -> ExactPITCompositionV1:
    ctx = _f12_context_binding(context)
    if type(field_class) is not PointInTimeFieldClassV1:
        _f12_schema_stop('F12_FIELD_CLASS_TYPE')
    if type(receipt_id) is not str or not receipt_id or receipt_id != receipt_id.strip() or any((ord(c) < 32 for c in receipt_id)):
        raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, 'F12_RECEIPT_ID_INVALID')
    try:
        bridge = _native_retail_pit_receipt_bridge(
            clocks,
            field_class=field_class.value,
            context_as_of=context_as_of,
            prior_revision_available_time=prior_revision_available_time
        )
        observed = _native_utc_receipt_pair(context_observed_at)
    except ContractValidationError as error:
        detail = _native_reference_reason(error, _F12_V1_REFERENCE_REASONS)
        if detail is None:
            raise
        raise PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, detail) from error
    decision = bridge['context_pair']
    if _f12_utc_projection(decision) != context.as_of or _f12_utc_projection(observed) != context.observed_at:
        _f12_schema_stop('F12_CONTEXT_PROJECTION_MISMATCH')
    if int(observed['utc_ns_text']) > int(decision['utc_ns_text']):
        raise ContractValidationError(
            ReasonCode.FUTURE_CONTEXT,
            'F12_CONTEXT_OBSERVED_AFTER_CUTOFF'
        )
    if int(decision['utc_ns_text']) - int(observed['utc_ns_text']) > _f12_duration_us(context.maximum_age) * 1000:
        raise ContractValidationError(ReasonCode.STALE_CONTEXT, 'F12_EXACT_CONTEXT_STALE')
    projected = PointInTimeClocksV1(
        **{k: _f12_utc_projection(v) for k, v in bridge['clock_pairs'].items()}
    )
    prior = None if bridge['prior_revision_pair'] is None else _f12_utc_projection(bridge['prior_revision_pair'])
    receipt = PointInTimePolicyV1.validate(
        receipt_id=receipt_id,
        field_class=field_class,
        clocks=projected,
        context=context,
        prior_revision_available_time=prior
    )
    request = {
        'clocks': dict(clocks),
        'field_class': field_class.value,
        'context_as_of': context_as_of,
        'context_observed_at': context_observed_at,
        'prior_revision_available_time': prior_revision_available_time
    }
    companion = {'bridge': bridge, 'context_observed_pair': observed}
    return ExactPITCompositionV1._from_checked(
        'V1',
        receipt_id,
        request,
        companion,
        ctx,
        projected,
        receipt
    )

def compose_exact_pit_v3(
    clocks: dict[str, object],
    requirements: dict[str, object],
    *,
    decision_time: str | None,
    receipt_id: str
) -> ExactPITCompositionV1:
    _pit_text(receipt_id, 'receipt_id')
    bridge = _native_retail_pit_v3_bridge(clocks, requirements, decision_time=decision_time)
    projected = dict(bridge['datetime_constructor_text_kwargs'])
    for name, pair in bridge['clock_pairs'].items():
        projected[name] = None if pair is None else _f12_utc_projection(pair)
    typed_clocks = PITClockSetV3(**projected)
    decision = None if bridge['decision_pair'] is None else _f12_utc_projection(bridge['decision_pair'])
    receipt = validate_pit_clock_set_v3(
        typed_clocks,
        receipt_id=receipt_id,
        decision_time_utc_or_none=decision,
        **dict(requirements)
    )
    request = {
        'clocks': dict(clocks),
        'requirements': dict(requirements),
        'decision_time': decision_time
    }
    return ExactPITCompositionV1._from_checked(
        'V3',
        receipt_id,
        request,
        bridge,
        None,
        typed_clocks,
        receipt
    )

def restore_exact_pit_composition_v1(
    payload: dict[str, object],
    *,
    context: ComputationContextKeyV1 | None = None
) -> ExactPITCompositionV1:
    keys = {'format', 'kind', 'receipt_id', 'request', 'companion', 'context_binding'}
    if type(payload) is not dict or set(payload) != keys or payload['format'] != 'QTT_F12_EXACT_COMPOSITION_V1':
        _f12_schema_stop('F12_WIRE_FIELDS')
    request = payload['request']
    if type(request) is not dict:
        _f12_schema_stop('F12_WIRE_FIELDS')
    if payload['kind'] == 'V1':
        if set(request) != {
            'clocks',
            'field_class',
            'context_as_of',
            'context_observed_at',
            'prior_revision_available_time'
        }:
            _f12_schema_stop('F12_WIRE_FIELDS')
        if not _f12_strict_equal(_f12_context_binding(context), payload['context_binding']):
            _f12_schema_stop('F12_CONTEXT_BINDING_MISMATCH')
        if type(request['field_class']) is not str:
            _f12_schema_stop('F12_FIELD_CLASS_TYPE')
        try:
            field_class = PointInTimeFieldClassV1(request['field_class'])
        except ValueError as e:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, 'F12_FIELD_CLASS_TYPE') from e
        obj = compose_exact_pit_v1(
            request['clocks'],
            field_class=field_class,
            context=context,
            context_as_of=request['context_as_of'],
            context_observed_at=request['context_observed_at'],
            prior_revision_available_time=request['prior_revision_available_time'],
            receipt_id=payload['receipt_id']
        )
    elif payload['kind'] == 'V3':
        if context is not None or payload['context_binding'] is not None or set(request) != {'clocks', 'requirements', 'decision_time'}:
            _f12_schema_stop('F12_WIRE_FIELDS')
        obj = compose_exact_pit_v3(
            request['clocks'],
            request['requirements'],
            decision_time=request['decision_time'],
            receipt_id=payload['receipt_id']
        )
    else:
        _f12_schema_stop('F12_WIRE_KIND')
    if not _f12_strict_equal(obj.to_payload(), payload):
        _f12_schema_stop('F12_COMPANION_MISMATCH')
    return obj
