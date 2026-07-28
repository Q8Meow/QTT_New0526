"""Typed point-in-time availability and revision-leakage resolution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from hashlib import sha256

from .context import ComputationContextKeyV1, parse_utc
from .errors import PointInTimeError, ReasonCode


class PointInTimeFieldClassV1(StrEnum):
    """Time-field semantics whose ordering rules are intentionally distinct."""

    OBSERVATION = "OBSERVATION"
    SCHEDULED_EFFECTIVE_FACT = "SCHEDULED_EFFECTIVE_FACT"
    REVISION = "REVISION"
    EVENT_OUTCOME = "EVENT_OUTCOME"
    SETTLEMENT = "SETTLEMENT"


class PointInTimeStateV1(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE_AT_DECISION = "UNAVAILABLE_AT_DECISION"
    REVISION_LEAKAGE_BLOCKED = "REVISION_LEAKAGE_BLOCKED"
    EPOCH_MISMATCH_BLOCKED = "EPOCH_MISMATCH_BLOCKED"


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PointInTimeError(
            ReasonCode.INVALID_CONTRACT,
            f"{field_name} must be nonempty text",
        )
    return value


@dataclass(frozen=True, slots=True)
class PointInTimeEvidenceV1:
    """The original time domains for one contextual input value.

    ``observed_time`` and ``effective_time`` deliberately have no universal
    relative-order invariant. A scheduled fact may be observed before it
    becomes effective, while an ordinary observation may be effective first.
    Availability to the strategy is the controlling anti-leakage boundary.
    """

    evidence_id: str
    field_id: str
    field_class: PointInTimeFieldClassV1
    observed_time: datetime
    effective_time: datetime
    source_available_time: datetime
    strategy_available_time: datetime
    received_time: datetime
    processed_time: datetime
    as_of_time: datetime
    source_epoch_id: str
    source_revision_id: str

    def __post_init__(self) -> None:
        for name in (
            "evidence_id",
            "field_id",
            "source_epoch_id",
            "source_revision_id",
        ):
            _required_text(getattr(self, name), name)
        if not isinstance(self.field_class, PointInTimeFieldClassV1):
            raise PointInTimeError(
                ReasonCode.INVALID_CONTRACT,
                "field_class must be PointInTimeFieldClassV1",
            )
        for name in (
            "observed_time",
            "effective_time",
            "source_available_time",
            "strategy_available_time",
            "received_time",
            "processed_time",
            "as_of_time",
        ):
            object.__setattr__(
                self,
                name,
                parse_utc(getattr(self, name), field_name=name),
            )
        if self.received_time > self.processed_time:
            raise PointInTimeError(
                ReasonCode.POINT_IN_TIME_UNAVAILABLE,
                "received_time cannot be later than processed_time",
            )


@dataclass(frozen=True, slots=True)
class PointInTimeReceiptV1:
    receipt_id: str
    evidence_id: str
    field_id: str
    field_class: PointInTimeFieldClassV1
    state: PointInTimeStateV1
    as_of_time: datetime
    source_epoch_id: str
    source_revision_id: str
    blocker_codes: tuple[ReasonCode, ...]
    terminal_route: str
    no_authority_flag: bool = True

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "evidence_id",
            "field_id",
            "source_epoch_id",
            "source_revision_id",
            "terminal_route",
        ):
            _required_text(getattr(self, name), name)
        if not isinstance(self.field_class, PointInTimeFieldClassV1):
            raise PointInTimeError(
                ReasonCode.INVALID_CONTRACT,
                "receipt field_class must be typed",
            )
        if not isinstance(self.state, PointInTimeStateV1):
            raise PointInTimeError(
                ReasonCode.INVALID_CONTRACT,
                "receipt state must be typed",
            )
        object.__setattr__(
            self,
            "as_of_time",
            parse_utc(self.as_of_time, field_name="as_of_time"),
        )
        if (
            not isinstance(self.blocker_codes, tuple)
            or any(not isinstance(code, ReasonCode) for code in self.blocker_codes)
            or len(set(self.blocker_codes)) != len(self.blocker_codes)
        ):
            raise PointInTimeError(
                ReasonCode.INVALID_CONTRACT,
                "point-in-time blockers must be a unique typed tuple",
            )
        if (self.state is PointInTimeStateV1.AVAILABLE) == bool(
            self.blocker_codes
        ):
            raise PointInTimeError(
                ReasonCode.INVALID_CONTRACT,
                "available receipts have no blocker and blocked receipts require one",
            )
        if type(self.no_authority_flag) is not bool or not self.no_authority_flag:
            raise PointInTimeError(
                ReasonCode.CAPABILITY_DENIED,
                "point-in-time receipts cannot create authority",
            )

    @property
    def available(self) -> bool:
        return self.state is PointInTimeStateV1.AVAILABLE


class PointInTimeResolverV1:
    """Resolve strategy availability against the existing context key."""

    @staticmethod
    def resolve(
        evidence: PointInTimeEvidenceV1,
        context: ComputationContextKeyV1,
    ) -> PointInTimeReceiptV1:
        if not isinstance(evidence, PointInTimeEvidenceV1):
            raise PointInTimeError(
                ReasonCode.INVALID_CONTRACT,
                "point-in-time evidence must be typed",
            )
        if not isinstance(context, ComputationContextKeyV1):
            raise PointInTimeError(
                ReasonCode.INVALID_CONTRACT,
                "context must be ComputationContextKeyV1",
            )

        blockers: list[ReasonCode] = []
        state = PointInTimeStateV1.AVAILABLE
        if evidence.source_epoch_id != context.source_epoch_id:
            blockers.append(ReasonCode.SOURCE_EPOCH_MISSING)
            state = PointInTimeStateV1.EPOCH_MISMATCH_BLOCKED

        availability_times = (
            evidence.source_available_time,
            evidence.strategy_available_time,
            evidence.received_time,
            evidence.processed_time,
        )
        if (
            evidence.as_of_time != context.as_of
            or any(moment > context.as_of for moment in availability_times)
        ):
            blockers.append(ReasonCode.POINT_IN_TIME_UNAVAILABLE)
            state = PointInTimeStateV1.UNAVAILABLE_AT_DECISION

        if evidence.field_class in {
            PointInTimeFieldClassV1.REVISION,
            PointInTimeFieldClassV1.EVENT_OUTCOME,
            PointInTimeFieldClassV1.SETTLEMENT,
        } and (
            evidence.source_available_time > context.as_of
            or evidence.strategy_available_time > context.as_of
        ):
            blockers.append(ReasonCode.REVISION_LEAKAGE)
            state = PointInTimeStateV1.REVISION_LEAKAGE_BLOCKED

        blockers = list(dict.fromkeys(blockers))
        digest_material = "|".join(
            (
                evidence.evidence_id,
                context.stable_key,
                evidence.source_revision_id,
                state.value,
                *(code.value for code in blockers),
            )
        )
        return PointInTimeReceiptV1(
            receipt_id=f"PIT::{sha256(digest_material.encode('utf-8')).hexdigest()}",
            evidence_id=evidence.evidence_id,
            field_id=evidence.field_id,
            field_class=evidence.field_class,
            state=state,
            as_of_time=context.as_of,
            source_epoch_id=evidence.source_epoch_id,
            source_revision_id=evidence.source_revision_id,
            blocker_codes=tuple(blockers),
            terminal_route=(
                "QKUComputationControlPlaneV1"
                if not blockers
                else "research_agent::POINT_IN_TIME_REBINDING_WORK_ORDER"
            ),
        )

    @classmethod
    def require_available(
        cls,
        evidence: PointInTimeEvidenceV1,
        context: ComputationContextKeyV1,
    ) -> PointInTimeReceiptV1:
        receipt = cls.resolve(evidence, context)
        if not receipt.available:
            reason = receipt.blocker_codes[0]
            raise PointInTimeError(
                reason,
                f"{evidence.field_id} was unavailable at {context.as_of.isoformat()}",
            )
        return receipt
