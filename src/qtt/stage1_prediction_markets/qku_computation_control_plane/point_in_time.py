"""Centralized point-in-time field-class laws for ST12-B."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from .context import ComputationContextKeyV1, parse_utc
from .errors import PointInTimeError, ReasonCode


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
