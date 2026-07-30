"""Single freshness, TTL, source-epoch, sequence, and revision owner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from .context import ComputationContextKeyV1
from .errors import FreshnessError, ReasonCode
from .point_in_time import PointInTimeClocksV1


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
