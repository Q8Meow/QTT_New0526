"""Single Tranche-C owner for economic idempotency, duplicate, and replay laws."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .context import parse_utc
from .errors import ContractValidationError, IdempotencyContractError, ReasonCode
from .serialization import deterministic_json, safe_json_loads


def canonical_request_json_v1(value: object) -> str:
    """Canonical request equality is deterministic serialized text, never a digest."""

    return deterministic_json(value)


def validate_canonical_request_json_v1(text: str) -> str:
    value = safe_json_loads(text)
    if deterministic_json(value) != text:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "request JSON is not exact deterministic text")
    return text


class IdempotencyClaimStateV1(StrEnum):
    UNSEEN = "UNSEEN"
    ACQUIRED = "ACQUIRED"
    COMPLETED = "COMPLETED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"
    CONFLICT = "CONFLICT"


class IdempotencyOutcomeV1(StrEnum):
    ACQUIRED = "ACQUIRED"
    REPLAYED_SAME_PAYLOAD = "REPLAYED_SAME_PAYLOAD"
    CONFLICT_DIFFERENT_PAYLOAD = "CONFLICT_DIFFERENT_PAYLOAD"
    IN_PROGRESS = "IN_PROGRESS"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"


@dataclass(frozen=True, slots=True)
class IdempotencyClaimReceiptV1:
    claim_id: str
    idempotency_key: str
    identity_class: str
    canonical_request_json: str
    claim_state: IdempotencyClaimStateV1
    result_record_ref: str | None
    created_at: datetime | str
    completed_at: datetime | str | None
    failure_code: str | None

    def __post_init__(self) -> None:
        for name in ("claim_id", "idempotency_key", "identity_class"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{name} is required")
        validate_canonical_request_json_v1(self.canonical_request_json)
        if not isinstance(self.claim_state, IdempotencyClaimStateV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "claim_state must be typed")
        created = parse_utc(self.created_at, field_name="created_at")
        completed = None if self.completed_at is None else parse_utc(self.completed_at, field_name="completed_at")
        if completed is not None and completed < created:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "completed_at precedes created_at")
        if self.claim_state is IdempotencyClaimStateV1.COMPLETED:
            if not self.result_record_ref or completed is None or self.failure_code is not None:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "completed claim requires one result and no failure")
        else:
            if self.result_record_ref is not None:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "only completed claim may bind a result")
            failed = self.claim_state in {IdempotencyClaimStateV1.FAILED_RETRYABLE, IdempotencyClaimStateV1.FAILED_FINAL}
            if failed and (not self.failure_code or completed is None):
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "failed claim requires completion time and failure_code")
            if not failed and (self.failure_code is not None or completed is not None):
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "nonterminal claim cannot carry terminal fields")
        object.__setattr__(self, "created_at", created)
        object.__setattr__(self, "completed_at", completed)


@dataclass(frozen=True, slots=True)
class IdempotencyDecisionV1:
    outcome: IdempotencyOutcomeV1
    original_result_ref: str | None = None
    reconciliation_required: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, IdempotencyOutcomeV1) or type(self.reconciliation_required) is not bool:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "idempotency decision must be typed")
        if self.outcome is IdempotencyOutcomeV1.REPLAYED_SAME_PAYLOAD and not self.original_result_ref:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "replay requires original result")


def decide_existing_claim_v1(existing: IdempotencyClaimReceiptV1, canonical_request_json: str) -> IdempotencyDecisionV1:
    validate_canonical_request_json_v1(canonical_request_json)
    if existing.canonical_request_json != canonical_request_json:
        return IdempotencyDecisionV1(IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD)
    if existing.claim_state is IdempotencyClaimStateV1.COMPLETED:
        return IdempotencyDecisionV1(IdempotencyOutcomeV1.REPLAYED_SAME_PAYLOAD, existing.result_record_ref)
    if existing.claim_state is IdempotencyClaimStateV1.ACQUIRED:
        return IdempotencyDecisionV1(IdempotencyOutcomeV1.IN_PROGRESS)
    if existing.claim_state is IdempotencyClaimStateV1.FAILED_RETRYABLE:
        return IdempotencyDecisionV1(IdempotencyOutcomeV1.FAILED_RETRYABLE)
    if existing.claim_state is IdempotencyClaimStateV1.FAILED_FINAL:
        return IdempotencyDecisionV1(IdempotencyOutcomeV1.FAILED_FINAL)
    return IdempotencyDecisionV1(IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD)


class DuplicateEventDispositionV1(StrEnum):
    NEW = "NEW"
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    CONFLICT_QUARANTINED = "CONFLICT_QUARANTINED"


def decide_duplicate_event_v1(existing_payload_json: str | None, candidate_payload_json: str) -> DuplicateEventDispositionV1:
    validate_canonical_request_json_v1(candidate_payload_json)
    if existing_payload_json is None:
        return DuplicateEventDispositionV1.NEW
    validate_canonical_request_json_v1(existing_payload_json)
    if existing_payload_json == candidate_payload_json:
        return DuplicateEventDispositionV1.EXACT_DUPLICATE
    return DuplicateEventDispositionV1.CONFLICT_QUARANTINED


def require_acquired_v1(decision: IdempotencyDecisionV1) -> None:
    if not isinstance(decision, IdempotencyDecisionV1):
        raise IdempotencyContractError(ReasonCode.INVALID_CONTRACT, "typed idempotency decision is required")
    if decision.outcome is IdempotencyOutcomeV1.ACQUIRED:
        return
    if decision.outcome is IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD:
        raise IdempotencyContractError(ReasonCode.IDEMPOTENCY_CONFLICT, "same key has a different canonical request")
    if decision.outcome is IdempotencyOutcomeV1.IN_PROGRESS:
        raise IdempotencyContractError(ReasonCode.IDEMPOTENCY_IN_PROGRESS, "same canonical request is already in progress")
    raise IdempotencyContractError(ReasonCode.OPERATION_BLOCKED, f"claim outcome {decision.outcome.value} is not newly acquired")


IDEMPOTENCY_RETENTION_POLICY_V1 = "REFERENCE_STORE_LIFETIME_NO_TIME_BASED_PURGE_API"
PROVIDER_IDEMPOTENCY_BINDING_STATE_V1 = "FUTURE_CONNECTOR_BINDING_ONLY"
