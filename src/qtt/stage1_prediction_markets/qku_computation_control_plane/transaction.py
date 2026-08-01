"""Atomic Tranche-C unit of work across typed semantic and persistence owners."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Mapping

from .accounting import AccountingAndTCAServiceV1, JournalAccountV1, JournalPostingV1, JournalTransactionV1, ReconciliationBreakReceiptV1
from .context import parse_utc
from .errors import ComputationControlPlaneError, ContractValidationError, PersistenceContractError, ReasonCode
from .idempotency import IdempotencyClaimReceiptV1, IdempotencyOutcomeV1
from .lifecycle import StateTransitionReceiptV1
from .outbox import OutboxIntentRecordV1
from .persistence import PersistenceAdapterV1, PersistenceAvailabilityV1, PersistenceTransactionV1
from .receipts import EconomicEventRecordV1, EconomicReceiptEventSpineV1, ValueLineageEdgeV1, validate_lineage_acyclic_v1
from .rollback import ReversalReceiptV1


class TransactionTerminalStateV1(StrEnum):
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    CONFLICT = "CONFLICT"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class TransactionRetryPolicyV1:
    max_transaction_attempts: int
    retryable_classes: frozenset[str] = frozenset({"REFERENCE_SQLITE_BUSY_BEFORE_SIDE_EFFECT"})

    def __post_init__(self) -> None:
        if isinstance(self.max_transaction_attempts, bool) or not isinstance(self.max_transaction_attempts, int) or self.max_transaction_attempts < 1:
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "explicit positive max_transaction_attempts is required")
        if not isinstance(self.retryable_classes, frozenset) or any(not value for value in self.retryable_classes):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "retryable_classes must be explicit")


@dataclass(frozen=True, slots=True)
class TransactionCommitReceiptV1:
    unit_of_work_id: str
    transaction_state: TransactionTerminalStateV1
    attempt_count: int
    committed_record_refs: tuple[str, ...]
    idempotency_claim_ref: str
    started_at: datetime | str
    completed_at: datetime | str
    failure_code: str | None
    retryable: bool

    def __post_init__(self) -> None:
        for name in ("unit_of_work_id", "idempotency_claim_ref"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{name} is required")
        if not isinstance(self.transaction_state, TransactionTerminalStateV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "transaction_state must be terminal and typed")
        if isinstance(self.attempt_count, bool) or not isinstance(self.attempt_count, int) or self.attempt_count < 1:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "attempt_count must be positive")
        if not isinstance(self.committed_record_refs, tuple) or any(not isinstance(ref, str) or not ref for ref in self.committed_record_refs):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "committed_record_refs must be a string tuple")
        if len(self.committed_record_refs) != len(set(self.committed_record_refs)):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "committed_record_refs must be unique")
        if type(self.retryable) is not bool:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "retryable must be bool")
        started = parse_utc(self.started_at, field_name="started_at")
        completed = parse_utc(self.completed_at, field_name="completed_at")
        if completed < started:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "completed_at precedes started_at")
        if self.transaction_state is TransactionTerminalStateV1.COMMITTED:
            if self.failure_code is not None or not self.committed_record_refs or self.retryable:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "committed receipt has contradictory failure fields")
        elif not self.failure_code or self.committed_record_refs:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "noncommitted receipt requires failure and no committed refs")
        object.__setattr__(self, "started_at", started)
        object.__setattr__(self, "completed_at", completed)


@dataclass(frozen=True, slots=True)
class TrancheCAtomicRecordSetV1:
    idempotency_claim: IdempotencyClaimReceiptV1
    receipt_records: tuple[EconomicReceiptEventSpineV1, ...]
    economic_events: tuple[EconomicEventRecordV1, ...]
    value_lineage_edges: tuple[ValueLineageEdgeV1, ...]
    journal_transaction: JournalTransactionV1 | None
    journal_postings: tuple[JournalPostingV1, ...]
    state_transition: StateTransitionReceiptV1
    result_record_ref: str
    optional_outbox_intent: OutboxIntentRecordV1 | None = None
    reversal_links: tuple[ReversalReceiptV1, ...] = ()
    reconciliation_breaks: tuple[ReconciliationBreakReceiptV1, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.idempotency_claim, IdempotencyClaimReceiptV1) or self.idempotency_claim.claim_state.value != "ACQUIRED":
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "atomic record set requires a newly ACQUIRED idempotency claim")
        if not self.receipt_records and not self.economic_events:
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "atomic record set requires at least one receipt or economic event")
        for name, rows, expected in (
            ("receipt_records", self.receipt_records, EconomicReceiptEventSpineV1),
            ("economic_events", self.economic_events, EconomicEventRecordV1),
            ("value_lineage_edges", self.value_lineage_edges, ValueLineageEdgeV1),
            ("journal_postings", self.journal_postings, JournalPostingV1),
            ("reversal_links", self.reversal_links, ReversalReceiptV1),
            ("reconciliation_breaks", self.reconciliation_breaks, ReconciliationBreakReceiptV1),
        ):
            if not isinstance(rows, tuple) or any(not isinstance(row, expected) for row in rows):
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be a typed tuple")
        if not isinstance(self.state_transition, StateTransitionReceiptV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "one typed legal state transition is required")
        if self.journal_transaction is not None and not isinstance(self.journal_transaction, JournalTransactionV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "journal_transaction must be typed when supplied")
        if not self.result_record_ref:
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "result_record_ref is required")
        identity_rows = [
            self.idempotency_claim.claim_id,
            *(record.record_id for record in self.receipt_records),
            *(event.economic_event_id for event in self.economic_events),
            *(edge.lineage_edge_id for edge in self.value_lineage_edges),
            *(posting.posting_id for posting in self.journal_postings),
            self.state_transition.transition_id,
            *(row.reversal_receipt_id for row in self.reversal_links),
            *(row.break_receipt_id for row in self.reconciliation_breaks),
        ]
        identities = set(identity_rows)
        event_by_id = {event.economic_event_id: event for event in self.economic_events}
        for record in self.receipt_records:
            if record.record_type.value == "ECONOMIC_EVENT":
                payload = record.typed_payload
                if not isinstance(payload, EconomicEventRecordV1) or event_by_id.get(payload.economic_event_id) != payload:
                    raise ContractValidationError(
                        ReasonCode.INVALID_CONTRACT,
                        "economic-event spine payload must close to the exact atomic economic event",
                    )
        if self.journal_transaction is None:
            if self.journal_postings:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "postings require one journal transaction")
            if any(event.event_class not in {"NO_FILL", "PREFLIGHT_BLOCKED", "NO_ECONOMIC_EFFECT"} for event in self.economic_events):
                raise ContractValidationError(ReasonCode.ACCOUNTING_IMBALANCE, "economic-effect events require a journal transaction")
        else:
            identities.add(self.journal_transaction.journal_transaction_id)
            identity_rows.append(self.journal_transaction.journal_transaction_id)
            if len(self.journal_postings) < 2:
                raise ContractValidationError(ReasonCode.ACCOUNTING_IMBALANCE, "journal transaction requires at least two postings")
            if any(event.event_class == "NO_FILL" for event in self.economic_events):
                raise ContractValidationError(ReasonCode.ACCOUNTING_IMBALANCE, "NO_FILL cannot create journal postings")
            event_ids = {event.economic_event_id for event in self.economic_events}
            if set(self.journal_transaction.economic_event_refs) != event_ids:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "journal must reference the atomic economic events exactly")
            if tuple(posting.posting_id for posting in self.journal_postings) != self.journal_transaction.posting_refs:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "journal posting identities do not match")
            if any(posting.source_event_ref not in event_ids for posting in self.journal_postings):
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "posting source event is outside the atomic record set")
        if self.optional_outbox_intent is not None:
            if not isinstance(self.optional_outbox_intent, OutboxIntentRecordV1):
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "optional outbox intent must be typed")
            if self.optional_outbox_intent.payload_record_ref not in identities:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "outbox payload must reference the atomic record set")
            identities.add(self.optional_outbox_intent.outbox_intent_id)
            identity_rows.append(self.optional_outbox_intent.outbox_intent_id)
        if len(identity_rows) != len(set(identity_rows)):
            raise ContractValidationError(ReasonCode.PERSISTENCE_CONFLICT, "atomic record identities must be globally unique")
        if self.result_record_ref not in identities:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "idempotency result must bind a record in the same atomic set")
        if self.reversal_links:
            if self.journal_transaction is None or any(row.reversal_transaction_ref != self.journal_transaction.journal_transaction_id for row in self.reversal_links):
                raise ContractValidationError(ReasonCode.REVERSAL_INVALID, "reversal links require their exact atomic reversal journal")
        validate_lineage_acyclic_v1(self.value_lineage_edges)


class TrancheCUnitOfWorkV1:
    """Compose writes only; economic meaning remains with accounting/lifecycle owners."""

    def __init__(self, adapter: PersistenceAdapterV1, retry_policy: TransactionRetryPolicyV1) -> None:
        if not isinstance(adapter, PersistenceAdapterV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "typed PersistenceAdapterV1 is required")
        if adapter.availability is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "durable operation requires available reference persistence")
        if not isinstance(retry_policy, TransactionRetryPolicyV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "typed transaction retry policy is required")
        adapter_attempts = getattr(adapter, "max_transaction_attempts", retry_policy.max_transaction_attempts)
        if adapter_attempts != retry_policy.max_transaction_attempts:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "adapter and unit-of-work retry limits must match")
        self._adapter = adapter
        self._retry_policy = retry_policy

    @staticmethod
    def _receipt(
        *, unit_of_work_id: str, state: TransactionTerminalStateV1, attempt: int,
        refs: tuple[str, ...], claim_ref: str, started_at: datetime | str,
        completed_at: datetime | str, failure_code: str | None, retryable: bool,
    ) -> TransactionCommitReceiptV1:
        return TransactionCommitReceiptV1(unit_of_work_id, state, attempt, refs, claim_ref, started_at, completed_at, failure_code, retryable)

    def execute(
        self,
        *,
        unit_of_work_id: str,
        records: TrancheCAtomicRecordSetV1,
        accounts: Mapping[str, JournalAccountV1],
        started_at: datetime | str,
        completed_at: datetime | str,
    ) -> TransactionCommitReceiptV1:
        for attempt in range(1, self._retry_policy.max_transaction_attempts + 1):
            transaction: PersistenceTransactionV1 | None = None
            try:
                transaction = self._adapter.begin_transaction()
            except PersistenceContractError as exc:
                retryable_begin = exc.reason_code.value in self._retry_policy.retryable_classes
                if retryable_begin and attempt < self._retry_policy.max_transaction_attempts:
                    continue
                return self._receipt(
                    unit_of_work_id=unit_of_work_id, state=TransactionTerminalStateV1.RETRY_EXHAUSTED,
                    attempt=attempt, refs=(), claim_ref=records.idempotency_claim.claim_id,
                    started_at=started_at, completed_at=completed_at,
                    failure_code=(ReasonCode.TRANSACTION_RETRY_EXHAUSTED.value if retryable_begin else exc.reason_code.value), retryable=False,
                )
            try:
                claim = self._adapter.acquire_idempotency_claim(transaction, records.idempotency_claim)
                if claim.outcome is IdempotencyOutcomeV1.REPLAYED_SAME_PAYLOAD:
                    transaction.rollback()
                    return self._receipt(
                        unit_of_work_id=unit_of_work_id, state=TransactionTerminalStateV1.COMMITTED,
                        attempt=attempt, refs=(claim.original_result_ref,), claim_ref=claim.claim_ref,
                        started_at=started_at, completed_at=completed_at, failure_code=None, retryable=False,
                    )
                if claim.outcome in {IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD, IdempotencyOutcomeV1.IN_PROGRESS}:
                    transaction.rollback()
                    reason = ReasonCode.IDEMPOTENCY_CONFLICT if claim.outcome is IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD else ReasonCode.IDEMPOTENCY_IN_PROGRESS
                    return self._receipt(
                        unit_of_work_id=unit_of_work_id, state=TransactionTerminalStateV1.CONFLICT,
                        attempt=attempt, refs=(), claim_ref=claim.claim_ref, started_at=started_at,
                        completed_at=completed_at, failure_code=reason.value, retryable=False,
                    )
                if records.journal_transaction is not None:
                    AccountingAndTCAServiceV1.validate_journal(records.journal_transaction, records.journal_postings, accounts)
                for record in records.receipt_records:
                    self._adapter.insert_receipt_record(transaction, record)
                for event in records.economic_events:
                    self._adapter.insert_economic_event(transaction, event)
                for edge in records.value_lineage_edges:
                    self._adapter.insert_value_lineage_edge(transaction, edge)
                if records.journal_transaction is not None:
                    self._adapter.insert_journal_transaction(transaction, records.journal_transaction)
                    for posting in records.journal_postings:
                        self._adapter.insert_journal_posting(transaction, posting)
                self._adapter.insert_state_transition(transaction, records.state_transition)
                if records.optional_outbox_intent is not None:
                    self._adapter.insert_outbox_intent(transaction, records.optional_outbox_intent)
                for reversal in records.reversal_links:
                    self._adapter.insert_reversal_link(transaction, reversal)
                for reconciliation_break in records.reconciliation_breaks:
                    self._adapter.insert_reconciliation_break(transaction, reconciliation_break)
                self._adapter.bind_idempotency_result(transaction, claim.claim_ref, records.result_record_ref, parse_utc(completed_at, field_name="completed_at"))
                transaction.commit()
                refs = (
                    *(record.record_id for record in records.receipt_records),
                    *(event.economic_event_id for event in records.economic_events),
                    *(edge.lineage_edge_id for edge in records.value_lineage_edges),
                    *((records.journal_transaction.journal_transaction_id,) if records.journal_transaction else ()),
                    *(posting.posting_id for posting in records.journal_postings),
                    records.state_transition.transition_id,
                    *((records.optional_outbox_intent.outbox_intent_id,) if records.optional_outbox_intent else ()),
                    *(row.reversal_receipt_id for row in records.reversal_links),
                    *(row.break_receipt_id for row in records.reconciliation_breaks),
                )
                return self._receipt(
                    unit_of_work_id=unit_of_work_id, state=TransactionTerminalStateV1.COMMITTED,
                    attempt=attempt, refs=tuple(refs), claim_ref=claim.claim_ref,
                    started_at=started_at, completed_at=completed_at, failure_code=None, retryable=False,
                )
            except ComputationControlPlaneError as exc:
                if transaction.is_active:
                    transaction.rollback()
                return self._receipt(
                    unit_of_work_id=unit_of_work_id, state=TransactionTerminalStateV1.ROLLED_BACK,
                    attempt=attempt, refs=(), claim_ref=records.idempotency_claim.claim_id,
                    started_at=started_at, completed_at=completed_at,
                    failure_code=exc.reason_code.value, retryable=False,
                )
            except Exception:
                if transaction.is_active:
                    transaction.rollback()
                raise
        raise AssertionError("bounded retry loop must terminate")
