"""Single freshness, TTL, source-epoch, sequence, and revision owner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from .context import ComputationContextKeyV1
from .errors import FreshnessError, ReasonCode
from .point_in_time import PointInTimeClocksV1
from .point_in_time import (
    PITAnchorStateV1,
    PITAvailabilityStateV2,
    PITContinuityStateV3,
    PITDataContractErrorV1,
    PITDepthClassV2,
    PITInputAvailabilityV2,
    PITIntegrityStateV1,
    PITReasonCodeV1,
    PITTransportStateV1,
)


@dataclass(frozen=True, slots=True)
class FreshnessPolicyV1:
    ttl: timedelta
    require_provider_sequence: bool = False
    require_revision: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.ttl, timedelta) or self.ttl <= timedelta(0):
            raise FreshnessError(
                ReasonCode.FRESHNESS_VIOLATION,
                "freshness TTL must be a positive timedelta",
            )
        if type(self.require_provider_sequence) is not bool or type(
            self.require_revision
        ) is not bool:
            raise FreshnessError(
                ReasonCode.FRESHNESS_VIOLATION,
                "freshness sequence/revision requirements must be exact booleans",
            )


@dataclass(frozen=True, slots=True)
class FreshnessReceiptV1:
    receipt_id: str
    context_id: str
    source_epoch_id: str
    age: timedelta
    ttl: timedelta
    provider_sequence: int | str | None
    revision: int | str | None
    admitted: bool = True

    def __post_init__(self) -> None:
        if not self.receipt_id or not self.context_id or not self.source_epoch_id:
            raise FreshnessError(
                ReasonCode.FRESHNESS_VIOLATION,
                "freshness receipt identity, context, and source epoch are required",
            )
        if self.age < timedelta(0) or self.age > self.ttl or not self.admitted:
            raise FreshnessError(
                ReasonCode.FRESHNESS_VIOLATION,
                "only an admitted, nonfuture, within-TTL receipt is valid",
            )


class FreshnessResolverV1:
    @staticmethod
    def assert_context_current(context: ComputationContextKeyV1) -> None:
        if not isinstance(context, ComputationContextKeyV1):
            raise FreshnessError(
                ReasonCode.FRESHNESS_VIOLATION,
                "freshness resolution requires a typed computation context",
            )
        if context.as_of - context.observed_at > context.maximum_age:
            raise FreshnessError(
                ReasonCode.FRESHNESS_VIOLATION,
                "computation context observation exceeds its maximum age",
            )

    @staticmethod
    def validate(
        *,
        receipt_id: str,
        clocks: PointInTimeClocksV1,
        context: ComputationContextKeyV1,
        packet_source_epoch_id: str,
        policy: FreshnessPolicyV1,
        provider_sequence: int | str | None,
        revision: int | str | None,
    ) -> FreshnessReceiptV1:
        if packet_source_epoch_id != context.source_epoch_id:
            raise FreshnessError(
                ReasonCode.SOURCE_EPOCH_STALE,
                "owner packet source epoch does not equal the exact context epoch",
            )
        age = context.as_of - clocks.observed_time
        if age < timedelta(0):
            raise FreshnessError(
                ReasonCode.FUTURE_CONTEXT,
                "future observations cannot satisfy freshness",
            )
        effective_ttl = min(policy.ttl, context.maximum_age)
        if age > effective_ttl:
            raise FreshnessError(
                ReasonCode.FRESHNESS_VIOLATION,
                "owner packet observation exceeds the stricter packet/context TTL",
            )
        if policy.require_provider_sequence and (
            provider_sequence is None or isinstance(provider_sequence, bool)
        ):
            raise FreshnessError(
                ReasonCode.FRESHNESS_VIOLATION,
                "provider-native sequence is required by the frozen interface",
            )
        if policy.require_revision and (
            revision is None or isinstance(revision, bool)
        ):
            raise FreshnessError(
                ReasonCode.FRESHNESS_VIOLATION,
                "provider-native revision is required by the frozen interface",
            )
        return FreshnessReceiptV1(
            receipt_id=receipt_id,
            context_id=context.context_id,
            source_epoch_id=context.source_epoch_id,
            age=age,
            ttl=effective_ttl,
            provider_sequence=provider_sequence,
            revision=revision,
        )


def _pit_freshness_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


def _pit_freshness_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be an exact boolean",
        )
    return value


def _pit_freshness_age(value: object, name: str, *, optional: bool) -> timedelta | None:
    if optional and value is None:
        return None
    if type(value) is not timedelta or value < timedelta(0):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_FRESHNESS_EXPIRED,
            f"{name} must be a nonnegative exact timedelta",
        )
    return value


@dataclass(frozen=True, slots=True)
class PITFreshnessRequirementV2:
    capability_key: str
    maximum_provider_event_age_or_none: timedelta | None
    maximum_local_receive_age: timedelta
    maximum_durable_commit_age: timedelta
    maximum_strategy_availability_age: timedelta
    economic_ttl: timedelta
    require_current_source: bool = True
    require_active_rights: bool = True
    require_healthy_transport: bool = True
    require_anchor: bool = True
    require_numeric_continuity: bool = False
    require_current_state_parity: bool = False
    require_provider_event_time: bool = False
    require_provider_publication_time: bool = False
    require_admissible_lifecycle: bool = True
    require_precision_and_tick: bool = True
    require_wall_clock_quality: bool = False
    required_depth_class: PITDepthClassV2 | None = None

    def __post_init__(self) -> None:
        _pit_freshness_text(self.capability_key, "capability_key")
        _pit_freshness_age(
            self.maximum_provider_event_age_or_none,
            "maximum_provider_event_age_or_none",
            optional=True,
        )
        for name in (
            "maximum_local_receive_age",
            "maximum_durable_commit_age",
            "maximum_strategy_availability_age",
            "economic_ttl",
        ):
            age = _pit_freshness_age(getattr(self, name), name, optional=False)
            if age == timedelta(0):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_FRESHNESS_EXPIRED,
                    f"{name} must be positive",
                )
        for name in (
            "require_current_source",
            "require_active_rights",
            "require_healthy_transport",
            "require_anchor",
            "require_numeric_continuity",
            "require_current_state_parity",
            "require_provider_event_time",
            "require_provider_publication_time",
            "require_admissible_lifecycle",
            "require_precision_and_tick",
            "require_wall_clock_quality",
        ):
            _pit_freshness_bool(getattr(self, name), name)
        if self.required_depth_class is not None and type(
            self.required_depth_class
        ) is not PITDepthClassV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TOP_LEVEL_DEPTH_ONLY,
                "required_depth_class must be an exact PITDepthClassV2 or absent",
            )


@dataclass(frozen=True, slots=True)
class PITFreshnessObservationV2:
    source_current: bool
    rights_active: bool
    transport_state: PITTransportStateV1
    anchor_state: PITAnchorStateV1
    continuity_state: PITContinuityStateV3
    integrity_state: PITIntegrityStateV1
    current_state_parity_passed: bool
    provider_event_age_or_none: timedelta | None
    provider_publication_time_present: bool
    local_receive_age: timedelta
    durable_commit_age: timedelta
    strategy_availability_age: timedelta
    lifecycle_admissible: bool
    precision_valid: bool
    tick_valid: bool
    wall_clock_quality_sufficient: bool
    source_conflict: bool
    depth_class: PITDepthClassV2
    economic_age: timedelta
    durable_commit_complete: bool

    def __post_init__(self) -> None:
        for name, enum_type in (
            ("transport_state", PITTransportStateV1),
            ("anchor_state", PITAnchorStateV1),
            ("continuity_state", PITContinuityStateV3),
            ("integrity_state", PITIntegrityStateV1),
            ("depth_class", PITDepthClassV2),
        ):
            if type(getattr(self, name)) is not enum_type:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} has the wrong exact enum type",
                )
        for name in (
            "source_current",
            "rights_active",
            "current_state_parity_passed",
            "provider_publication_time_present",
            "lifecycle_admissible",
            "precision_valid",
            "tick_valid",
            "wall_clock_quality_sufficient",
            "source_conflict",
            "durable_commit_complete",
        ):
            _pit_freshness_bool(getattr(self, name), name)
        _pit_freshness_age(
            self.provider_event_age_or_none,
            "provider_event_age_or_none",
            optional=True,
        )
        for name in (
            "local_receive_age",
            "durable_commit_age",
            "strategy_availability_age",
            "economic_age",
        ):
            _pit_freshness_age(getattr(self, name), name, optional=False)


@dataclass(frozen=True, slots=True)
class FreshnessAndDowngradePolicyV2:
    capability_key: str
    transport_decision: bool
    source_decision: bool
    continuity_and_parity_decision: bool
    rights_decision: bool
    lifecycle_decision: bool
    clock_decision: bool
    economic_ttl_decision: bool
    precision_and_tick_decision: bool
    depth_decision: bool
    durable_commit_decision: bool
    terminal_availability: PITInputAvailabilityV2
    state_availability: PITAvailabilityStateV2
    terminal_reason_or_none: PITReasonCodeV1 | None
    downgrade_route: str
    recovery_requirements: tuple[str, ...]

    def __post_init__(self) -> None:
        _pit_freshness_text(self.capability_key, "capability_key")
        for name in (
            "transport_decision",
            "source_decision",
            "continuity_and_parity_decision",
            "rights_decision",
            "lifecycle_decision",
            "clock_decision",
            "economic_ttl_decision",
            "precision_and_tick_decision",
            "depth_decision",
            "durable_commit_decision",
        ):
            _pit_freshness_bool(getattr(self, name), name)
        if type(self.terminal_availability) is not PITInputAvailabilityV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "terminal_availability must be exact PITInputAvailabilityV2",
            )
        if type(self.state_availability) is not PITAvailabilityStateV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "state_availability must be exact PITAvailabilityStateV2",
            )
        if self.terminal_reason_or_none is not None and type(
            self.terminal_reason_or_none
        ) is not PITReasonCodeV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "terminal_reason_or_none has the wrong exact type",
            )
        _pit_freshness_text(self.downgrade_route, "downgrade_route")
        if type(self.recovery_requirements) is not tuple or any(
            type(value) is not str or not value
            for value in self.recovery_requirements
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "recovery_requirements must be an exact text tuple",
            )
        if self.terminal_availability is PITInputAvailabilityV2.AVAILABLE:
            if self.terminal_reason_or_none is not None or self.recovery_requirements:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                    "available freshness cannot carry failure or recovery state",
                )
        elif self.terminal_reason_or_none is None:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "unavailable freshness requires a specific PIT reason",
            )


def evaluate_pit_freshness_v2(
    requirement: PITFreshnessRequirementV2,
    observation: PITFreshnessObservationV2,
) -> FreshnessAndDowngradePolicyV2:
    """Evaluate orthogonal PIT health with one deterministic fail-closed order."""

    if type(requirement) is not PITFreshnessRequirementV2 or type(
        observation
    ) is not PITFreshnessObservationV2:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "freshness evaluation requires exact typed arguments",
        )
    transport_ok = (
        not requirement.require_healthy_transport
        or observation.transport_state is PITTransportStateV1.CONNECTED_HEALTHY
    )
    source_ok = not requirement.require_current_source or (
        observation.source_current and not observation.source_conflict
    )
    rights_ok = not requirement.require_active_rights or observation.rights_active
    anchor_ok = not requirement.require_anchor or (
        observation.anchor_state is PITAnchorStateV1.ANCHOR_ACCEPTED
    )
    continuity_ok = not requirement.require_numeric_continuity or (
        observation.continuity_state is PITContinuityStateV3.CONTIGUOUS
    )
    integrity_ok = observation.integrity_state is PITIntegrityStateV1.VALID
    parity_ok = (
        not requirement.require_current_state_parity
        or observation.current_state_parity_passed
    )
    provider_time_ok = not requirement.require_provider_event_time or (
        observation.provider_event_age_or_none is not None
    )
    if (
        provider_time_ok
        and observation.provider_event_age_or_none is not None
        and requirement.maximum_provider_event_age_or_none is not None
    ):
        provider_time_ok = (
            observation.provider_event_age_or_none
            <= requirement.maximum_provider_event_age_or_none
        )
    publication_ok = not requirement.require_provider_publication_time or (
        observation.provider_publication_time_present
    )
    age_ok = (
        observation.local_receive_age <= requirement.maximum_local_receive_age
        and observation.durable_commit_age <= requirement.maximum_durable_commit_age
        and observation.strategy_availability_age
        <= requirement.maximum_strategy_availability_age
    )
    lifecycle_ok = (
        not requirement.require_admissible_lifecycle
        or observation.lifecycle_admissible
    )
    precision_ok = not requirement.require_precision_and_tick or (
        observation.precision_valid and observation.tick_valid
    )
    clock_ok = not requirement.require_wall_clock_quality or (
        observation.wall_clock_quality_sufficient
    )
    depth_ok = requirement.required_depth_class is None or (
        observation.depth_class is requirement.required_depth_class
    )
    ttl_ok = observation.economic_age <= requirement.economic_ttl
    durable_ok = observation.durable_commit_complete
    continuity_and_parity_ok = (
        anchor_ok and continuity_ok and integrity_ok and parity_ok
    )

    failures: tuple[
        tuple[bool, PITInputAvailabilityV2, PITAvailabilityStateV2, PITReasonCodeV1, str],
        ...,
    ] = (
        (
            source_ok,
            PITInputAvailabilityV2.UNAVAILABLE_FRESHNESS,
            PITAvailabilityStateV2.UNAVAILABLE,
            (
                PITReasonCodeV1.PIT_CURRENT_STATE_PARITY_FAILED
                if observation.source_conflict
                else PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE
            ),
            "CURRENTIZE_SOURCE",
        ),
        (
            rights_ok,
            PITInputAvailabilityV2.UNAVAILABLE_RIGHTS,
            PITAvailabilityStateV2.RIGHTS_BLOCKED,
            PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
            "READMIT_RIGHTS",
        ),
        (
            transport_ok,
            PITInputAvailabilityV2.UNAVAILABLE_FRESHNESS,
            PITAvailabilityStateV2.STALE,
            (
                PITReasonCodeV1.PIT_SOURCE_MAINTENANCE
                if observation.transport_state
                is PITTransportStateV1.SOURCE_MAINTENANCE
                else PITReasonCodeV1.PIT_SOURCE_UNAVAILABLE
            ),
            "RECOVER_TRANSPORT_NEW_EPOCH",
        ),
        (
            durable_ok,
            PITInputAvailabilityV2.UNAVAILABLE_FRESHNESS,
            PITAvailabilityStateV2.UNAVAILABLE,
            PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
            "COMPLETE_DURABLE_COMMIT",
        ),
        (
            anchor_ok,
            PITInputAvailabilityV2.UNAVAILABLE_CONTINUITY,
            PITAvailabilityStateV2.UNAVAILABLE,
            PITReasonCodeV1.PIT_ANCHOR_REQUIRED,
            "REANCHOR_NEW_EPOCH",
        ),
        (
            continuity_ok,
            PITInputAvailabilityV2.UNAVAILABLE_CONTINUITY,
            PITAvailabilityStateV2.UNAVAILABLE,
            (
                PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE
                if observation.continuity_state
                is PITContinuityStateV3.SEQUENCE_UNAVAILABLE
                else PITReasonCodeV1.PIT_SEQUENCE_GAP
            ),
            "RECOVER_SEQUENCE_AND_REANCHOR",
        ),
        (
            integrity_ok,
            PITInputAvailabilityV2.UNAVAILABLE_CONTINUITY,
            PITAvailabilityStateV2.UNAVAILABLE,
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "REJECT_CORRUPT_EVENT_AND_REANCHOR",
        ),
        (
            parity_ok,
            PITInputAvailabilityV2.UNAVAILABLE_CONTINUITY,
            PITAvailabilityStateV2.UNAVAILABLE,
            PITReasonCodeV1.PIT_CURRENT_STATE_PARITY_FAILED,
            "RECOVER_CURRENT_STATE_PARITY",
        ),
        (
            lifecycle_ok,
            PITInputAvailabilityV2.UNAVAILABLE_LIFECYCLE,
            PITAvailabilityStateV2.LIFECYCLE_BLOCKED,
            PITReasonCodeV1.PIT_LIFECYCLE_BLOCKED,
            "WAIT_FOR_ADMISSIBLE_LIFECYCLE_VERSION",
        ),
        (
            precision_ok,
            PITInputAvailabilityV2.UNAVAILABLE_PRECISION,
            PITAvailabilityStateV2.UNAVAILABLE,
            (
                PITReasonCodeV1.PIT_TICK_GRID_INVALID
                if not observation.tick_valid
                else PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID
            ),
            "REJECT_AND_REFRESH_PRECISION_BINDING",
        ),
        (
            clock_ok,
            PITInputAvailabilityV2.UNAVAILABLE_CLOCK,
            PITAvailabilityStateV2.CLOCK_BLOCKED,
            PITReasonCodeV1.PIT_WALL_CLOCK_UNCERTAIN,
            "REFRESH_CLOCK_QUALITY_RECEIPT",
        ),
        (
            provider_time_ok,
            PITInputAvailabilityV2.UNAVAILABLE_SOURCE_FIELD,
            PITAvailabilityStateV2.CLOCK_BLOCKED,
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
            "REQUIRE_PROVIDER_EVENT_TIME_FIELD",
        ),
        (
            publication_ok,
            PITInputAvailabilityV2.UNAVAILABLE_PROVIDER_PUBLICATION_TIME,
            PITAvailabilityStateV2.CLOCK_BLOCKED,
            PITReasonCodeV1.PIT_PROVIDER_PUBLICATION_TIME_UNAVAILABLE,
            "REQUIRE_PROVIDER_PUBLICATION_TIME_FIELD",
        ),
        (
            depth_ok,
            PITInputAvailabilityV2.UNAVAILABLE_FULL_DEPTH,
            PITAvailabilityStateV2.UNAVAILABLE,
            PITReasonCodeV1.PIT_TOP_LEVEL_DEPTH_ONLY,
            "OBTAIN_EXACT_REQUIRED_DEPTH_CLASS",
        ),
        (
            age_ok and ttl_ok,
            PITInputAvailabilityV2.UNAVAILABLE_FRESHNESS,
            PITAvailabilityStateV2.STALE,
            PITReasonCodeV1.PIT_FRESHNESS_EXPIRED,
            "REFRESH_CAPABILITY_INPUT",
        ),
    )
    terminal = next((row for row in failures if not row[0]), None)
    if terminal is None:
        available_state = (
            PITAvailabilityStateV2.AVAILABLE_CHANGE_LEVEL
            if observation.continuity_state is PITContinuityStateV3.CONTIGUOUS
            and observation.depth_class
            is PITDepthClassV2.INCREMENTAL_FROM_COMPLETE_ANCHOR
            else PITAvailabilityStateV2.AVAILABLE_CURRENT_STATE
        )
        terminal_availability = PITInputAvailabilityV2.AVAILABLE
        reason = None
        route = "NO_DOWNGRADE"
        recovery: tuple[str, ...] = ()
    else:
        _, terminal_availability, available_state, reason, route = terminal
        recovery = (route,)
    return FreshnessAndDowngradePolicyV2(
        capability_key=requirement.capability_key,
        transport_decision=transport_ok,
        source_decision=source_ok,
        continuity_and_parity_decision=continuity_and_parity_ok,
        rights_decision=rights_ok,
        lifecycle_decision=lifecycle_ok,
        clock_decision=clock_ok and provider_time_ok and publication_ok,
        economic_ttl_decision=age_ok and ttl_ok,
        precision_and_tick_decision=precision_ok,
        depth_decision=depth_ok,
        durable_commit_decision=durable_ok,
        terminal_availability=terminal_availability,
        state_availability=available_state,
        terminal_reason_or_none=reason,
        downgrade_route=route,
        recovery_requirements=recovery,
    )
