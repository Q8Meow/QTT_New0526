"""Backend-neutral typed persistence hierarchy and deterministic memory reference."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from _thread import RLock
from typing import Mapping

from .accounting import JournalPostingV1, JournalTransactionV1, ReconciliationBreakReceiptV1
from .context import parse_utc
from .errors import PersistenceContractError, ReasonCode, TransactionContractError
from .idempotency import (
    IdempotencyClaimReceiptV1,
    IdempotencyClaimStateV1,
    IdempotencyOutcomeV1,
)
from .lifecycle import StateTransitionReceiptV1
from .migrations import APPEND_ONLY_TABLES_V1, PRODUCTION_PERSISTENCE_SELECTION_STATE_V1
from .outbox import OutboxIntentRecordV1
from .receipts import (
    DurableComputationExecutionReceiptRecordV1,
    EconomicEventRecordV1,
    EconomicReceiptEventSpineV1,
    ValueLineageEdgeV1,
)
from .rollback import (
    JournalReversalBundleV1,
    ReversalHistoryViewV1,
    ReversalReceiptV1,
)
from .serialization import deterministic_json


class PersistenceAvailabilityV1(StrEnum):
    AVAILABLE_REFERENCE = "AVAILABLE_REFERENCE"
    UNAVAILABLE = "UNAVAILABLE"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    READ_ONLY = "READ_ONLY"


@dataclass(frozen=True, slots=True)
class IdempotencyAcquireResultV1:
    outcome: IdempotencyOutcomeV1
    claim_ref: str
    original_result_ref: str | None = None


@dataclass(frozen=True, slots=True)
class _IdempotencyResultBindingV1:
    binding_id: str
    claim_ref: str
    result_record_ref: str
    created_at: datetime


class PersistenceTransactionV1(ABC):
    """Opaque transaction handle; it deliberately exposes no generic query/SQL API."""

    @property
    @abstractmethod
    def is_active(self) -> bool: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...


class PersistenceAdapterV1(ABC):
    """Typed append-only storage boundary; production technology remains unselected."""

    production_selection_state = PRODUCTION_PERSISTENCE_SELECTION_STATE_V1

    @property
    @abstractmethod
    def availability(self) -> PersistenceAvailabilityV1: ...

    @abstractmethod
    def begin_transaction(self) -> PersistenceTransactionV1: ...

    @abstractmethod
    def insert_receipt_record(self, transaction: PersistenceTransactionV1, record: EconomicReceiptEventSpineV1) -> None: ...

    @abstractmethod
    def insert_value_lineage_edge(self, transaction: PersistenceTransactionV1, edge: ValueLineageEdgeV1) -> None: ...

    @abstractmethod
    def insert_economic_event(self, transaction: PersistenceTransactionV1, event: EconomicEventRecordV1) -> None: ...

    @abstractmethod
    def insert_journal_transaction(self, transaction: PersistenceTransactionV1, journal: JournalTransactionV1) -> None: ...

    @abstractmethod
    def insert_journal_posting(self, transaction: PersistenceTransactionV1, posting: JournalPostingV1) -> None: ...

    @abstractmethod
    def insert_state_transition(self, transaction: PersistenceTransactionV1, transition: StateTransitionReceiptV1) -> None: ...

    @abstractmethod
    def acquire_idempotency_claim(self, transaction: PersistenceTransactionV1, claim: IdempotencyClaimReceiptV1) -> IdempotencyAcquireResultV1: ...

    @abstractmethod
    def bind_idempotency_result(self, transaction: PersistenceTransactionV1, claim_ref: str, result_record_ref: str, created_at: datetime) -> None: ...

    @abstractmethod
    def insert_outbox_intent(self, transaction: PersistenceTransactionV1, intent: OutboxIntentRecordV1) -> None: ...

    @abstractmethod
    def insert_reversal_link(self, transaction: PersistenceTransactionV1, reversal: ReversalReceiptV1) -> None: ...

    @abstractmethod
    def load_committed_reversal_history(
        self,
        transaction: PersistenceTransactionV1,
        original_transaction_id: str,
    ) -> ReversalHistoryViewV1: ...

    @abstractmethod
    def insert_reconciliation_break(self, transaction: PersistenceTransactionV1, reconciliation_break: ReconciliationBreakReceiptV1) -> None: ...

    @abstractmethod
    def get_record(self, record_ref: str) -> object | None: ...

    @abstractmethod
    def get_idempotency_result(self, idempotency_key: str) -> str | None: ...

    @abstractmethod
    def reconstruct_as_of(self, *, effective_cutoff: datetime, recorded_cutoff: datetime, aggregate_scope: tuple[str, ...]) -> tuple[object, ...]: ...


class _InMemoryTransactionV1(PersistenceTransactionV1):
    def __init__(
        self,
        adapter: "InMemoryPersistenceAdapterV1",
        committed_snapshot: dict[str, dict[str, object]],
        working: dict[str, dict[str, object]],
    ) -> None:
        self._adapter = adapter
        self._committed_snapshot = committed_snapshot
        self._working = working
        self._active = True

    @property
    def is_active(self) -> bool:
        return self._active

    def commit(self) -> None:
        if not self._active:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "transaction is no longer active")
        try:
            self._adapter._commit(self)
        finally:
            self._active = False
            self._adapter._release(self)

    def rollback(self) -> None:
        if not self._active:
            return
        self._working.clear()
        self._active = False
        self._adapter._release(self)


class InMemoryPersistenceAdapterV1(PersistenceAdapterV1):
    """Copy-on-write deterministic adapter with transaction-wide uniqueness lock."""

    def __init__(self) -> None:
        self._tables: dict[str, dict[str, object]] = {table: {} for table in APPEND_ONLY_TABLES_V1}
        self._lock = RLock()
        self._active_transaction: _InMemoryTransactionV1 | None = None

    @property
    def availability(self) -> PersistenceAvailabilityV1:
        return PersistenceAvailabilityV1.AVAILABLE_REFERENCE

    def begin_transaction(self) -> PersistenceTransactionV1:
        self._lock.acquire()
        try:
            if self._active_transaction is not None and self._active_transaction.is_active:
                raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "nested transactions are forbidden")
            committed_snapshot = {
                name: dict(rows) for name, rows in self._tables.items()
            }
            transaction = _InMemoryTransactionV1(
                self,
                committed_snapshot,
                {name: dict(rows) for name, rows in committed_snapshot.items()},
            )
            self._active_transaction = transaction
            return transaction
        except Exception:
            self._lock.release()
            raise

    def _transaction(self, transaction: PersistenceTransactionV1) -> _InMemoryTransactionV1:
        if transaction is not self._active_transaction or not isinstance(transaction, _InMemoryTransactionV1) or not transaction.is_active:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "transaction does not belong to adapter or is inactive")
        return transaction

    def _release(self, transaction: _InMemoryTransactionV1) -> None:
        if self._active_transaction is transaction:
            self._active_transaction = None
            self._lock.release()

    def _commit(self, transaction: _InMemoryTransactionV1) -> None:
        self._transaction(transaction)
        self._tables = {name: dict(rows) for name, rows in transaction._working.items()}

    def _insert(self, transaction: PersistenceTransactionV1, table: str, key: str, value: object) -> None:
        tx = self._transaction(transaction)
        if key in tx._working[table]:
            if deterministic_json(tx._working[table][key]) == deterministic_json(value):
                return
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, f"conflicting duplicate {table} identity")
        if any(key in rows for other_table, rows in tx._working.items() if other_table != table):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "record identity is already owned by another table")
        tx._working[table][key] = value

    @staticmethod
    def _record_exists(tables: Mapping[str, Mapping[str, object]], record_ref: str) -> bool:
        return any(record_ref in rows for table, rows in tables.items() if table != "idempotency_claims")

    def insert_receipt_record(self, transaction: PersistenceTransactionV1, record: EconomicReceiptEventSpineV1) -> None:
        tx = self._transaction(transaction)
        payload = record.typed_payload
        if isinstance(payload, DurableComputationExecutionReceiptRecordV1) and any(
            not self._record_exists(tx._working, ref) for ref in payload.dependency_receipt_refs
        ):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "durable receipt dependency is absent")
        self._insert(transaction, "receipt_records", record.record_id, record)

    def insert_value_lineage_edge(self, transaction: PersistenceTransactionV1, edge: ValueLineageEdgeV1) -> None:
        tx = self._transaction(transaction)
        if not self._record_exists(tx._working, edge.producer_record_id) or not self._record_exists(tx._working, edge.consumer_record_id):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "lineage producer/consumer record is absent")
        self._insert(transaction, "value_lineage_edges", edge.lineage_edge_id, edge)

    def insert_economic_event(self, transaction: PersistenceTransactionV1, event: EconomicEventRecordV1) -> None:
        tx = self._transaction(transaction)
        for existing in tx._working["economic_events"].values():
            if isinstance(existing, EconomicEventRecordV1) and existing.aggregate_id == event.aggregate_id and existing.event_sequence == event.event_sequence:
                if existing == event:
                    return
                raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "aggregate event sequence already exists")
        self._insert(transaction, "economic_events", event.economic_event_id, event)

    def insert_journal_transaction(self, transaction: PersistenceTransactionV1, journal: JournalTransactionV1) -> None:
        tx = self._transaction(transaction)
        if any(ref not in tx._working["economic_events"] for ref in journal.economic_event_refs):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "journal economic-event reference is absent")
        self._insert(transaction, "journal_transactions", journal.journal_transaction_id, journal)

    def insert_journal_posting(self, transaction: PersistenceTransactionV1, posting: JournalPostingV1) -> None:
        tx = self._transaction(transaction)
        if posting.journal_transaction_id not in tx._working["journal_transactions"] or posting.source_event_ref not in tx._working["economic_events"]:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "journal transaction is absent")
        self._insert(transaction, "journal_postings", posting.posting_id, posting)

    def insert_state_transition(self, transaction: PersistenceTransactionV1, transition: StateTransitionReceiptV1) -> None:
        tx = self._transaction(transaction)
        for existing in tx._working["state_transitions"].values():
            if isinstance(existing, StateTransitionReceiptV1) and existing.aggregate_id == transition.aggregate_id and existing.aggregate_version_after == transition.aggregate_version_after:
                if existing == transition:
                    return
                raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "aggregate version already exists")
        self._insert(transaction, "state_transitions", transition.transition_id, transition)

    def acquire_idempotency_claim(self, transaction: PersistenceTransactionV1, claim: IdempotencyClaimReceiptV1) -> IdempotencyAcquireResultV1:
        tx = self._transaction(transaction)
        if claim.claim_state is not IdempotencyClaimStateV1.ACQUIRED:
            raise PersistenceContractError(ReasonCode.INVALID_CONTRACT, "new idempotency claim must be in ACQUIRED state")
        claims = [row for row in tx._working["idempotency_claims"].values() if isinstance(row, IdempotencyClaimReceiptV1)]
        existing = next((row for row in claims if row.idempotency_key == claim.idempotency_key), None)
        if existing is None:
            self._insert(transaction, "idempotency_claims", claim.claim_id, claim)
            return IdempotencyAcquireResultV1(IdempotencyOutcomeV1.ACQUIRED, claim.claim_id)
        if existing.canonical_request_json != claim.canonical_request_json:
            return IdempotencyAcquireResultV1(IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD, existing.claim_id)
        binding = next((row for row in tx._working["idempotency_claims"].values() if isinstance(row, _IdempotencyResultBindingV1) and row.claim_ref == existing.claim_id), None)
        if binding is not None:
            return IdempotencyAcquireResultV1(IdempotencyOutcomeV1.REPLAYED_SAME_PAYLOAD, existing.claim_id, binding.result_record_ref)
        return IdempotencyAcquireResultV1(IdempotencyOutcomeV1.IN_PROGRESS, existing.claim_id)

    def bind_idempotency_result(self, transaction: PersistenceTransactionV1, claim_ref: str, result_record_ref: str, created_at: datetime) -> None:
        tx = self._transaction(transaction)
        if claim_ref not in tx._working["idempotency_claims"] or not self._record_exists(tx._working, result_record_ref):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "claim or result record is absent")
        if any(isinstance(row, _IdempotencyResultBindingV1) and row.claim_ref == claim_ref for row in tx._working["idempotency_claims"].values()):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "claim result is already bound")
        binding = _IdempotencyResultBindingV1(f"{claim_ref}::RESULT", claim_ref, result_record_ref, created_at)
        self._insert(transaction, "idempotency_claims", binding.binding_id, binding)

    def insert_outbox_intent(self, transaction: PersistenceTransactionV1, intent: OutboxIntentRecordV1) -> None:
        tx = self._transaction(transaction)
        if not self._record_exists(tx._working, intent.payload_record_ref):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "outbox payload record is absent")
        self._insert(transaction, "outbox_intents", intent.outbox_intent_id, intent)

    def insert_reversal_link(self, transaction: PersistenceTransactionV1, reversal: ReversalReceiptV1) -> None:
        if not isinstance(reversal, ReversalReceiptV1):
            raise PersistenceContractError(
                ReasonCode.REVERSAL_INVALID,
                "reversal linkage must be a typed receipt",
            )
        reversal_id = reversal.reversal_receipt_id
        original_ref = reversal.original_event_or_transaction_ref
        reversal_transaction_ref = reversal.reversal_transaction_ref
        tx = self._transaction(transaction)
        if not self._record_exists(tx._working, original_ref) or reversal_transaction_ref not in tx._working["journal_transactions"]:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "reversal linkage records are absent")
        self._insert(transaction, "reversal_links", reversal_id, reversal)

    def load_committed_reversal_history(
        self,
        transaction: PersistenceTransactionV1,
        original_transaction_id: str,
    ) -> ReversalHistoryViewV1:
        tx = self._transaction(transaction)
        snapshot = tx._committed_snapshot
        original = snapshot["journal_transactions"].get(original_transaction_id)
        if not isinstance(original, JournalTransactionV1):
            raise PersistenceContractError(
                ReasonCode.REVERSAL_INVALID,
                "original journal is absent from the committed transaction snapshot",
            )
        try:
            original_postings = tuple(
                snapshot["journal_postings"][posting_ref]
                for posting_ref in original.posting_refs
            )
        except KeyError as exc:
            raise PersistenceContractError(
                ReasonCode.REVERSAL_INVALID,
                "original committed journal has a missing posting",
            ) from exc
        if any(not isinstance(row, JournalPostingV1) for row in original_postings):
            raise PersistenceContractError(
                ReasonCode.REVERSAL_INVALID,
                "original committed posting is not typed",
            )
        links = sorted(
            (
                row
                for row in snapshot["reversal_links"].values()
                if isinstance(row, ReversalReceiptV1)
                and row.original_event_or_transaction_ref
                == original_transaction_id
            ),
            key=lambda row: (row.recorded_at, row.reversal_receipt_id),
        )
        bundles: list[JournalReversalBundleV1] = []
        for link in links:
            reversal_transaction = snapshot["journal_transactions"].get(
                link.reversal_transaction_ref
            )
            if not isinstance(reversal_transaction, JournalTransactionV1):
                raise PersistenceContractError(
                    ReasonCode.REVERSAL_INVALID,
                    "committed reversal link has no typed journal",
                )
            try:
                reversal_postings = tuple(
                    snapshot["journal_postings"][posting_ref]
                    for posting_ref in reversal_transaction.posting_refs
                )
            except KeyError as exc:
                raise PersistenceContractError(
                    ReasonCode.REVERSAL_INVALID,
                    "committed reversal journal has a missing posting",
                ) from exc
            if any(
                not isinstance(row, JournalPostingV1)
                for row in reversal_postings
            ):
                raise PersistenceContractError(
                    ReasonCode.REVERSAL_INVALID,
                    "committed reversal posting is not typed",
                )
            bundles.append(
                JournalReversalBundleV1(
                    reversal_transaction,
                    reversal_postings,
                    link,
                )
            )
        return ReversalHistoryViewV1(
            original,
            original_postings,
            tuple(bundles),
        )

    def insert_reconciliation_break(self, transaction: PersistenceTransactionV1, reconciliation_break: ReconciliationBreakReceiptV1) -> None:
        self._insert(transaction, "reconciliation_breaks", reconciliation_break.break_receipt_id, reconciliation_break)

    def get_record(self, record_ref: str) -> object | None:
        with self._lock:
            for rows in self._tables.values():
                if record_ref in rows:
                    return rows[record_ref]
        return None

    def get_idempotency_result(self, idempotency_key: str) -> str | None:
        with self._lock:
            claim = next((row for row in self._tables["idempotency_claims"].values() if isinstance(row, IdempotencyClaimReceiptV1) and row.idempotency_key == idempotency_key), None)
            if claim is None:
                return None
            binding = next((row for row in self._tables["idempotency_claims"].values() if isinstance(row, _IdempotencyResultBindingV1) and row.claim_ref == claim.claim_id), None)
            return None if binding is None else binding.result_record_ref

    def reconstruct_as_of(self, *, effective_cutoff: datetime, recorded_cutoff: datetime, aggregate_scope: tuple[str, ...]) -> tuple[object, ...]:
        effective_cutoff = parse_utc(effective_cutoff, field_name="effective_cutoff")
        recorded_cutoff = parse_utc(recorded_cutoff, field_name="recorded_cutoff")
        records: list[object] = []
        with self._lock:
            for table, rows in self._tables.items():
                if table == "idempotency_claims":
                    continue
                for record in rows.values():
                    effective = getattr(record, "effective_at", None)
                    recorded = getattr(record, "recorded_at", getattr(record, "created_at", None))
                    aggregate = getattr(record, "aggregate_id", None)
                    if isinstance(effective, datetime) and isinstance(recorded, datetime) and effective <= effective_cutoff and recorded <= recorded_cutoff and (not aggregate_scope or aggregate in aggregate_scope):
                        records.append(record)
        minimum = datetime.min.replace(tzinfo=UTC)
        return tuple(sorted(records, key=lambda row: (getattr(row, "aggregate_id", ""), getattr(row, "sequence", getattr(row, "event_sequence", 0)), getattr(row, "recorded_at", getattr(row, "created_at", minimum)), getattr(row, "record_id", getattr(row, "economic_event_id", getattr(row, "journal_transaction_id", getattr(row, "transition_id", "")))))))
