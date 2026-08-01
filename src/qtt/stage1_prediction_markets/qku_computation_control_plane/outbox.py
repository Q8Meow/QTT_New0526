"""Atomic no-write outbox intent contract; dispatch is structurally unavailable."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .context import parse_utc
from .errors import ContractValidationError, LifecycleContractError, ReasonCode


class OutboxDispatchStateV1(StrEnum):
    RECORDED_NOT_DISPATCHABLE = "RECORDED_NOT_DISPATCHABLE"


@dataclass(frozen=True, slots=True)
class OutboxIntentRecordV1:
    outbox_intent_id: str
    topic_class: str
    aggregate_id: str
    payload_record_ref: str
    created_at: datetime | str
    dispatch_state: OutboxDispatchStateV1 = OutboxDispatchStateV1.RECORDED_NOT_DISPATCHABLE
    dispatch_attempt_count: int = 0
    next_eligible_at: datetime | None = None
    authority_class: str = "NO_WRITE_CONTRACT_ONLY"

    def __post_init__(self) -> None:
        for name in ("outbox_intent_id", "topic_class", "aggregate_id", "payload_record_ref", "authority_class"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{name} is required")
        if self.dispatch_state is not OutboxDispatchStateV1.RECORDED_NOT_DISPATCHABLE:
            raise LifecycleContractError(ReasonCode.OUTBOX_DISPATCH_FORBIDDEN, "Tranche-C outbox cannot become dispatchable")
        if self.dispatch_attempt_count != 0 or self.next_eligible_at is not None:
            raise LifecycleContractError(ReasonCode.OUTBOX_DISPATCH_FORBIDDEN, "Tranche-C outbox cannot record a dispatch attempt or schedule")
        if self.authority_class != "NO_WRITE_CONTRACT_ONLY":
            raise LifecycleContractError(ReasonCode.CAPABILITY_DENIED, "outbox intent has no external-write authority")
        object.__setattr__(self, "created_at", parse_utc(self.created_at, field_name="created_at"))


OUTBOX_RUNTIME_STATE_V1 = "RECORDED_NOT_DISPATCHABLE"
OUTBOX_DISPATCHER_IMPLEMENTED = False
