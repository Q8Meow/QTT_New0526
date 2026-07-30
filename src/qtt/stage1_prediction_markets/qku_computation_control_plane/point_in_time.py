"""Centralized point-in-time field-class laws for ST12-B."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

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
