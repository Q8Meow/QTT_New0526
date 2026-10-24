"""Backend-neutral typed persistence hierarchy and deterministic memory reference."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from _thread import RLock
from typing import Mapping

from .accounting import JournalPostingV1, JournalTransactionV1, ReconciliationBreakReceiptV1
from .context import _native_ident, parse_utc, _f14_freeze_v1, _f14_plain_v1
from .errors import ContractValidationError, PersistenceContractError, ReasonCode, SerializationSafetyError, TransactionContractError
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
    EconomicRecordTypeV1,
    PrivateObservationClockReceiptV1, PrivateEvidenceWitnessV1,
    _f14_singleton_witness_v1, _f14_typed_spine_v1,
    ValueLineageEdgeV1,
    _private_clock_reconstruct_spine_v1,
    SourceUseControlRecordV1, _source_use_stream_id_v1, _source_use_record_ref_v1,
    _source_use_reconstruct_spine_v1, _source_use_from_storage_v1, _source_use_append_disposition_v1,
    SourceUseAttributedActionV1, _source_action_ref_v1, _source_action_from_storage_v1,
    _source_action_reconstruct_spine_v1, _source_use_require_v1,
)
from .rollback import (
    JournalReversalBundleV1,
    ReversalHistoryViewV1,
    ReversalReceiptV1,
)
from .serialization import (deterministic_json, _f14_require_v1,
    _f14_validate_v1, _F14_ID, _F14_SCOPE, _F14_PHASES,
    _f14_load_canonical_v1, _f14_dumps_v1, _f14_phase_shapes_v1,
    _f14_hydrate_phase_storage_view_v1)


class PersistenceAvailabilityV1(StrEnum):
    AVAILABLE_REFERENCE = "AVAILABLE_REFERENCE"
    AVAILABLE_OWNER_CONTROL_EPHEMERAL = "AVAILABLE_OWNER_CONTROL_EPHEMERAL"
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
    _source_use_integrity_failed_v1 = False

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
    def load_committed_private_clock_receipt_v1(
        self, record_ref: str,
    ) -> EconomicReceiptEventSpineV1 | None: ...

    @abstractmethod
    def get_idempotency_result(self, idempotency_key: str) -> str | None: ...

    @abstractmethod
    def reconstruct_as_of(self, *, effective_cutoff: datetime, recorded_cutoff: datetime, aggregate_scope: tuple[str, ...]) -> tuple[object, ...]: ...


    @abstractmethod
    def load_committed_private_evidence_witness_v1(
        self, record_ref: str,
    ) -> EconomicReceiptEventSpineV1 | None: ...

    @abstractmethod
    def load_committed_private_evidence_snapshot_v1(
        self, request: PrivateEvidenceReadRequestV1,
    ) -> PrivateEvidenceReadSnapshotV1: ...

    def load_committed_source_use_record_v1(self, record_ref: str) -> EconomicReceiptEventSpineV1 | None:
        _source_use_record_ref_v1(record_ref)
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "source-use custody is unavailable")

    def load_committed_source_use_head_v1(self, stream_id: str) -> EconomicReceiptEventSpineV1 | None:
        _source_use_stream_id_v1(stream_id)
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "source-use custody is unavailable")

    def load_source_use_head_for_update_v1(
        self, transaction: PersistenceTransactionV1, stream_id: str,
    ) -> EconomicReceiptEventSpineV1 | None:
        _source_use_stream_id_v1(stream_id)
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "source-use custody is unavailable")

    def load_source_use_record_for_update_v1(
        self, transaction: PersistenceTransactionV1, record_ref: str,
    ) -> EconomicReceiptEventSpineV1 | None:
        _source_use_record_ref_v1(record_ref)
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "source-use custody is unavailable")

    def load_committed_source_action_v1(self, event_ref: str) -> EconomicReceiptEventSpineV1 | None:
        _source_action_ref_v1(event_ref)
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "source action storage is unavailable")

    def load_committed_source_action_head_v1(self, process_ref: str) -> EconomicReceiptEventSpineV1 | None:
        _source_use_stream_id_v1(process_ref)
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "source action storage is unavailable")

    def load_source_action_for_update_v1(self, transaction: PersistenceTransactionV1, event_ref: str) -> EconomicReceiptEventSpineV1 | None:
        _source_action_ref_v1(event_ref)
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "source action storage is unavailable")

    def load_source_action_head_for_update_v1(self, transaction: PersistenceTransactionV1, process_ref: str) -> EconomicReceiptEventSpineV1 | None:
        _source_use_stream_id_v1(process_ref)
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "source action storage is unavailable")


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
        self._availability = PersistenceAvailabilityV1.AVAILABLE_REFERENCE

    @property
    def availability(self) -> PersistenceAvailabilityV1:
        return (PersistenceAvailabilityV1.INTEGRITY_FAILURE
                if self._source_use_integrity_failed_v1 else self._availability)

    def _source_use_available_v1(self) -> bool:
        if type(self) is OwnerControlMemoryAdapterV1:
            return self._scope_valid_v1()
        return self.availability is PersistenceAvailabilityV1.AVAILABLE_REFERENCE

    def begin_transaction(self) -> PersistenceTransactionV1:
        self._lock.acquire()
        try:
            if not self._source_use_available_v1():
                raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "reference persistence is unavailable")
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
        if _source_action_reserved_v1(record):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "attributed actions require original owner composition")
        tx = self._transaction(transaction)
        payload = record.typed_payload
        if (record.record_type == EconomicRecordTypeV1.SOURCE_USE_CONTROL
                or isinstance(payload, SourceUseControlRecordV1)
                or (type(record.aggregate_id) is str and record.aggregate_id.startswith("SOURCE_USE::"))
                or (type(record.record_id) is str and record.record_id.startswith("SOURCE_USE::"))):
            record = _source_use_reconstruct_spine_v1(record)
            head = self.load_source_use_head_for_update_v1(transaction, record.typed_payload.stream_id)
            existing = self.load_source_use_record_for_update_v1(transaction, record.record_id)
            if _source_use_append_disposition_v1(record, head, existing) == "EXACT_DUPLICATE":
                return
        if (record.record_type == EconomicRecordTypeV1.PRIVATE_OBSERVATION_CLOCK
                or type(payload) is PrivateObservationClockReceiptV1):
            record = _private_clock_reconstruct_spine_v1(record, expected_record_id=record.record_id)
        if (record.record_type is EconomicRecordTypeV1.PRIVATE_EVIDENCE_WITNESS
                or type(payload) is PrivateEvidenceWitnessV1):
            record = _f14_singleton_witness_v1(record, record.record_id)
        if isinstance(payload, DurableComputationExecutionReceiptRecordV1) and any(
            not self._record_exists(tx._working, ref) for ref in payload.dependency_receipt_refs
        ):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "durable receipt dependency is absent")
        self._insert(transaction, "receipt_records", record.record_id, record)

    def _source_use_read_v1(self, tables, *, record_ref=None, stream_id=None):
        if not self._source_use_available_v1():
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "source-use custody is unavailable")
        try:
            if stream_id is not None:
                aggregate = "SOURCE_USE::" + stream_id
                record_ref = None
                for key, value in tables["receipt_records"].items():
                    if (getattr(value, "aggregate_id", None) == aggregate
                            or (type(key) is str and key.startswith(aggregate + "::"))):
                        _source_use_record_ref_v1(key)
                        if not key.startswith(aggregate + "::"):
                            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT,
                                "invalid stored source-use control identity")
                        if record_ref is None or key > record_ref:
                            record_ref = key
                if record_ref is None:
                    return None
            value = tables["receipt_records"].get(record_ref)
            if value is None and not any(record_ref in rows for rows in tables.values()):
                return None
            record = _source_use_from_storage_v1(value, record_id=record_ref)
            if stream_id is not None and record.typed_payload.stream_id != stream_id:
                raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "source-use stored head mismatch")
            return record
        except ContractValidationError as exc:
            self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT,
                "invalid stored source-use control identity") from exc
        except (PersistenceContractError, SerializationSafetyError):
            self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            raise

    def load_committed_source_use_record_v1(self, record_ref: str) -> EconomicReceiptEventSpineV1 | None:
        _source_use_record_ref_v1(record_ref)
        with self._lock:
            if self._active_transaction is not None:
                raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "source-use read requires committed state")
            return self._source_use_read_v1(self._tables, record_ref=record_ref)

    def load_committed_source_use_head_v1(self, stream_id: str) -> EconomicReceiptEventSpineV1 | None:
        _source_use_stream_id_v1(stream_id)
        with self._lock:
            if self._active_transaction is not None:
                raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "source-use read requires committed state")
            return self._source_use_read_v1(self._tables, stream_id=stream_id)

    def load_source_use_head_for_update_v1(
        self, transaction: PersistenceTransactionV1, stream_id: str,
    ) -> EconomicReceiptEventSpineV1 | None:
        _source_use_stream_id_v1(stream_id)
        tx = self._transaction(transaction)
        if type(tx) is not _InMemoryTransactionV1 or tx._adapter is not self:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "source-use transaction ownership mismatch")
        return self._source_use_read_v1(tx._working, stream_id=stream_id)

    def load_source_use_record_for_update_v1(
        self, transaction: PersistenceTransactionV1, record_ref: str,
    ) -> EconomicReceiptEventSpineV1 | None:
        _source_use_record_ref_v1(record_ref)
        tx = self._transaction(transaction)
        if type(tx) is not _InMemoryTransactionV1 or tx._adapter is not self:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "source-use transaction ownership mismatch")
        return self._source_use_read_v1(tx._working, record_ref=record_ref)

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

    def load_committed_private_clock_receipt_v1(
        self, record_ref: str,
    ) -> EconomicReceiptEventSpineV1 | None:
        with self._lock:
            if self._active_transaction is not None and self._active_transaction.is_active:
                raise TransactionContractError(
                    ReasonCode.TRANSACTION_STATE_INVALID, "F13 committed read requires no active transaction",
                )
            _native_ident(record_ref)
            committed = self._tables["receipt_records"]
            if record_ref not in committed:
                return None
            return _private_clock_reconstruct_spine_v1(committed[record_ref], expected_record_id=record_ref)

    def load_committed_private_evidence_witness_v1(
        self, record_ref: str,
    ) -> EconomicReceiptEventSpineV1 | None:
        with self._lock:
            self._f14_require_committed_v1()
            _f14_validate_v1(_F14_ID, record_ref)
            found = [(table, rows[record_ref]) for table, rows in self._tables.items()
                     if record_ref in rows]
            if not found:
                return None
            _f14_require_v1(len(found) == 1 and found[0][0] == 'receipt_records',
                'F14_STORAGE_VIEW_MEMBERSHIP')
            return _f14_singleton_witness_v1(found[0][1], record_ref)

    def _f14_require_committed_v1(self) -> None:
        if self._active_transaction is not None and self._active_transaction.is_active:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID,
                'F14 committed read requires no active transaction')
        if self.availability is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE,
                'F14 reference persistence is unavailable')

    def load_committed_private_evidence_snapshot_v1(
        self, request: PrivateEvidenceReadRequestV1,
    ) -> PrivateEvidenceReadSnapshotV1:
        with self._lock:
            self._f14_require_committed_v1()
            identities = _f14_requested_identities_v1(request)
            rows = {table: {rid: _f14_memory_payload_v1(request, rid, value) for rid, value in values.items()
                           if rid in identities} for table, values in self._tables.items()}
            return _f14_reconstruct_snapshot_v1(request, rows)

    def get_record(self, record_ref: str) -> object | None:
        if type(record_ref) is not str:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "record_ref must be an exact string",
            )
        if record_ref.startswith("SOURCE_USE::"):
            return self.load_committed_source_use_record_v1(record_ref)
        if record_ref.startswith("SOURCE_ACTION::"):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "attributed actions require specialized reads")
        with self._lock:
            for rows in self._tables.values():
                if record_ref in rows:
                    if _source_action_reserved_v1(rows[record_ref]):
                        raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "unexpected attributed action in reference storage")
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
                        if getattr(record, "record_type", None) is EconomicRecordTypeV1.SOURCE_USE_CONTROL:
                            record = self.load_committed_source_use_record_v1(record.record_id)
                        records.append(record)
        minimum = datetime.min.replace(tzinfo=UTC)
        return tuple(sorted(records, key=lambda row: (getattr(row, "aggregate_id", ""), getattr(row, "sequence", getattr(row, "event_sequence", 0)), getattr(row, "recorded_at", getattr(row, "created_at", minimum)), getattr(row, "record_id", getattr(row, "economic_event_id", getattr(row, "journal_transaction_id", getattr(row, "transition_id", "")))))))


def _source_action_reserved_v1(record: object) -> bool:
    return (getattr(record, "record_type", None) == EconomicRecordTypeV1.SOURCE_USE_ATTRIBUTED_ACTION
            or isinstance(getattr(record, "typed_payload", None), SourceUseAttributedActionV1)
            or any(type(value) is str and value.startswith("SOURCE_ACTION::")
                   for value in (getattr(record, "record_id", None), getattr(record, "aggregate_id", None))))


class OwnerControlMemoryAdapterV1(InMemoryPersistenceAdapterV1):
    """Process-owned source state, constructed only by the original policy factory.

    P never calls back into the authority or native verifier. Its registered batch
    already binds the original issuer, root, proof and exact prospective records.
    """

    def __init__(self) -> None:
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "owner composition requires original bootstrap")

    def _scope_valid_v1(self) -> bool:
        return (type(self) is OwnerControlMemoryAdapterV1
                and self.availability is PersistenceAvailabilityV1.AVAILABLE_OWNER_CONTROL_EPHEMERAL
                and self._control_scope is self._original_control_scope
                and self._control_scope[0] is not None and self._control_scope[1] is not None)

    def _deny_v1(self, *args, **kwargs):
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "operation is outside owner-control storage")

    get_record = _deny_v1
    get_idempotency_result = _deny_v1
    reconstruct_as_of = _deny_v1
    insert_value_lineage_edge = _deny_v1
    insert_economic_event = _deny_v1
    insert_journal_transaction = _deny_v1
    insert_journal_posting = _deny_v1
    insert_state_transition = _deny_v1
    acquire_idempotency_claim = _deny_v1
    bind_idempotency_result = _deny_v1
    insert_outbox_intent = _deny_v1
    insert_reversal_link = _deny_v1
    load_committed_reversal_history = _deny_v1
    insert_reconciliation_break = _deny_v1
    load_committed_private_clock_receipt_v1 = _deny_v1
    load_committed_private_evidence_witness_v1 = _deny_v1
    load_committed_private_evidence_snapshot_v1 = _deny_v1

    def _prepare_action_batch_v1(self, verified, originals, event, expected):
        _source_use_require_v1(self._scope_valid_v1() and self._pending_batch is None)
        batch = self._registered_batches.get(event.record_id)
        _source_use_require_v1(batch is not None and batch["verified"] is verified
                               and batch["scope"] is self._control_scope
                               and batch["event"] == event and batch["originals"] == originals
                               and batch["expected"] == expected)
        _source_use_require_v1(verified._attempted is True)
        self._pending_batch = batch

    def begin_transaction(self) -> PersistenceTransactionV1:
        _source_use_require_v1(self._scope_valid_v1() and self._pending_batch is not None)
        batch = self._pending_batch
        self._pending_batch = None
        tx = super().begin_transaction()
        tx._source_action_batch = batch
        return tx

    def _transaction(self, transaction: PersistenceTransactionV1) -> _InMemoryTransactionV1:
        tx = super()._transaction(transaction)
        batch = getattr(tx, "_source_action_batch", None)
        _source_use_require_v1(type(tx) is _InMemoryTransactionV1 and tx._adapter is self
                               and batch is not None and batch["scope"] is self._control_scope
                               and self._registered_batches.get(batch["event"].record_id) is batch)
        return tx

    def _action_read_v1(self, tables, *, event_ref=None, process_ref=None):
        _source_use_require_v1(self._scope_valid_v1())
        try:
            if process_ref is not None:
                _source_use_require_v1(process_ref == self._control_scope[2])
                aggregate = "SOURCE_ACTION::" + process_ref
                matches = []
                for key, value in tables["receipt_records"].items():
                    if (getattr(value, "aggregate_id", None) == aggregate
                            or (type(key) is str and key.startswith(aggregate + "::"))):
                        _source_action_ref_v1(key)
                        _source_use_require_v1(key.startswith(aggregate + "::"))
                        matches.append(key)
                if not matches:
                    return None
                event_ref = max(matches)
            _source_use_require_v1(event_ref.startswith("SOURCE_ACTION::" + self._control_scope[2] + "::"))
            value = tables["receipt_records"].get(event_ref)
            if value is None and not any(event_ref in rows for rows in tables.values()):
                return None
            return _source_action_from_storage_v1(value, record_id=event_ref)
        except (ContractValidationError, PersistenceContractError, SerializationSafetyError):
            self._source_use_integrity_failed_v1 = True
            raise

    def load_committed_source_action_v1(self, event_ref: str) -> EconomicReceiptEventSpineV1 | None:
        _source_action_ref_v1(event_ref)
        with self._lock:
            if self._active_transaction is not None:
                raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "source action read requires committed state")
            return self._action_read_v1(self._tables, event_ref=event_ref)

    def load_committed_source_action_head_v1(self, process_ref: str) -> EconomicReceiptEventSpineV1 | None:
        _source_use_stream_id_v1(process_ref)
        with self._lock:
            if self._active_transaction is not None:
                raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "source action read requires committed state")
            return self._action_read_v1(self._tables, process_ref=process_ref)

    def load_source_action_for_update_v1(self, transaction: PersistenceTransactionV1, event_ref: str) -> EconomicReceiptEventSpineV1 | None:
        _source_action_ref_v1(event_ref)
        return self._action_read_v1(self._transaction(transaction)._working, event_ref=event_ref)

    def load_source_action_head_for_update_v1(self, transaction: PersistenceTransactionV1, process_ref: str) -> EconomicReceiptEventSpineV1 | None:
        _source_use_stream_id_v1(process_ref)
        return self._action_read_v1(self._transaction(transaction)._working, process_ref=process_ref)

    def insert_receipt_record(self, transaction: PersistenceTransactionV1, record: EconomicReceiptEventSpineV1) -> None:
        tx = self._transaction(transaction)
        batch = tx._source_action_batch
        if _source_action_reserved_v1(record):
            record = _source_action_reconstruct_spine_v1(record)
            _source_use_require_v1(record == batch["event"])
        else:
            record = _source_use_reconstruct_spine_v1(record)
            _source_use_require_v1(record in batch["originals"])
            head = self.load_source_use_head_for_update_v1(tx, record.typed_payload.stream_id)
            existing = self.load_source_use_record_for_update_v1(tx, record.record_id)
            _source_use_append_disposition_v1(record, head, existing)
        self._insert(tx, "receipt_records", record.record_id, record)

    def _validate_action_batch_v1(self, transaction, *, complete):
        tx = self._transaction(transaction)
        batch = tx._source_action_batch
        event, originals = batch["event"], batch["originals"]
        p = event.typed_payload
        before = tx._committed_snapshot
        head = self._action_read_v1(before, process_ref=p.process_ref)
        expected_event, expected_declaration, expected_review = batch["expected"]
        _source_use_require_v1((None if head is None else head.record_id) == expected_event == p.predecessor_event_ref
                               and (expected_declaration, expected_review) == (p.expected_declaration_ref, p.expected_review_ref)
                               and p.sequence == (1 if head is None else head.sequence + 1)
                               and p.generation_before == (0 if head is None else head.typed_payload.generation_after))
        if head is not None:
            _source_use_require_v1(head.typed_payload.scope == p.scope and head.recorded_at <= event.recorded_at
                                   and (head.typed_payload.declaration_ref, head.typed_payload.review_ref)
                                   == (expected_declaration, expected_review))
        else:
            _source_use_require_v1(expected_declaration is expected_review is None)
        _source_use_require_v1(tuple(row.record_id for row in originals) == p.original_event_refs
                               and type(originals) is tuple and len(originals) <= 1)
        results = []
        for kind, expected, resulting in (("OWNER_DECLARATION", expected_declaration, p.declaration_ref),
                                          ("SOURCE_REVIEW", expected_review, p.review_ref)):
            old = None
            if expected is not None:
                old = self._source_use_read_v1(before, record_ref=expected)
                _source_use_require_v1(old is not None and old.typed_payload.subject_kind == kind
                                       and old.typed_payload.scope == p.scope
                                       and self._source_use_read_v1(before, stream_id=old.typed_payload.stream_id) == old)
            appended = next((row for row in originals if row.typed_payload.subject_kind == kind), None)
            if appended is None:
                _source_use_require_v1(resulting == expected)
                current = old
            else:
                a = appended.typed_payload
                _source_use_require_v1(resulting == appended.record_id and a.scope == p.scope
                                       and appended.recorded_at == event.recorded_at)
                original_head = self._source_use_read_v1(before, stream_id=a.stream_id)
                existing = self._source_use_read_v1(before, record_ref=appended.record_id)
                _source_use_require_v1(_source_use_append_disposition_v1(appended, original_head, existing) == "APPENDED")
                if old is not None and old.typed_payload.action != "WITHDRAW":
                    _source_use_require_v1(a.stream_id == old.typed_payload.stream_id)
                expected_kind = "SOURCE_REVIEW" if p.action in {"REVIEW_ACCEPT", "INVALIDATE_REVIEW"} else "OWNER_DECLARATION"
                _source_use_require_v1(kind == expected_kind and p.action != "OBSERVE_ONCE"
                                       and (a.action == "WITHDRAW") == (p.action in {"WITHDRAW_USE", "INVALIDATE_REVIEW"}))
                current = appended
            if current is not None:
                _source_use_require_v1(current.typed_payload.scope == p.scope)
            results.append(current)
        declaration, review = results
        review_parent = use_parent = None
        if head is not None:
            hp = head.typed_payload
            if hp.action != "INVALIDATE_REVIEW":
                review_parent = head.record_id if hp.action == "REVIEW_ACCEPT" else hp.review_event_ref
            if hp.action in {"USE_ADMIT", "OBSERVE_ONCE"}:
                use_parent = head.record_id if hp.action == "USE_ADMIT" else hp.use_event_ref
        if p.action == "REVIEW_ACCEPT":
            _source_use_require_v1(review is not None and review.typed_payload.content is not None)
            content, facts = review.typed_payload.content, p.review_facts
            _source_use_require_v1(content.reported_time_kind == "UTC_INSTANT"
                                   and datetime.fromisoformat(content.reported_time_text) == facts.factual_checked_at_utc
                                   and (content.reviewed_document_ref, content.reviewed_document_version,
                                        content.claimed_effective_at_utc, content.claimed_expires_at_utc)
                                   == (facts.document_ref, facts.document_version, facts.source_effective_at_utc, facts.source_expires_at_utc))
        else:
            _source_use_require_v1(p.review_event_ref == review_parent)
        if p.action in {"USE_ADMIT", "OBSERVE_ONCE"}:
            _source_use_require_v1(declaration is not None and review is not None
                                   and declaration.typed_payload.content is not None and review.typed_payload.content is not None)
            accepted_review = self._action_read_v1(before, event_ref=review_parent)
            _source_use_require_v1(accepted_review is not None and accepted_review.typed_payload.action == "REVIEW_ACCEPT"
                                   and accepted_review.typed_payload.review_ref == review.record_id
                                   and accepted_review.typed_payload.scope == p.scope
                                   and event.recorded_at < p.expires_at_utc <= accepted_review.typed_payload.expires_at_utc)
            content = declaration.typed_payload.content
            _source_use_require_v1(content.claimed_effective_at_utc is not None and content.claimed_expires_at_utc is not None
                                   and content.claimed_effective_at_utc <= event.recorded_at < p.expires_at_utc <= content.claimed_expires_at_utc)
        if p.action == "OBSERVE_ONCE":
            _source_use_require_v1(p.use_event_ref == use_parent)
            accepted_use = self._action_read_v1(before, event_ref=use_parent)
            _source_use_require_v1(accepted_use is not None and accepted_use.typed_payload.action == "USE_ADMIT"
                                   and accepted_use.typed_payload.generation_after == p.generation_after
                                   and (accepted_use.typed_payload.declaration_ref, accepted_use.typed_payload.review_ref,
                                        accepted_use.typed_payload.review_event_ref) == (p.declaration_ref, p.review_ref, p.review_event_ref)
                                   and p.expires_at_utc <= accepted_use.typed_payload.expires_at_utc)
        elif p.action in {"WITHDRAW_USE", "INVALIDATE_REVIEW"}:
            _source_use_require_v1(p.use_event_ref == use_parent)
        expected_tables = {name: dict(rows) for name, rows in before.items()}
        for record in (*originals, event):
            _source_use_require_v1(not any(record.record_id in rows for rows in before.values()))
            expected_tables["receipt_records"][record.record_id] = record
        rows = expected_tables["receipt_records"]
        _source_use_require_v1(len(rows) <= 256 and sum(len(deterministic_json(row).encode("utf-8")) for row in rows.values()) <= 16 * 1024 * 1024)
        if complete:
            _source_use_require_v1(tx._working == expected_tables)
            for original in originals:
                _source_use_require_v1(self._source_use_read_v1(tx._working, stream_id=original.typed_payload.stream_id) == original)
            _source_use_require_v1(self._action_read_v1(tx._working, process_ref=p.process_ref) == event)
        return declaration, review

    def _commit(self, transaction: _InMemoryTransactionV1) -> None:
        self._validate_action_batch_v1(transaction, complete=True)
        super()._commit(transaction)


_F14_RECORD_ROLES = ('raw', 'transport', 'capture_commit', 'publication',
    'companion', 'companion_commit', 'clock_proofs', 'publication_intent')
_F14_CONTROL_ROLES = ('unit_of_work_id', 'claim_ref', 'result_binding_ref', 'transition_ref')


@dataclass(frozen=True, slots=True)
class PrivateEvidenceReadRequestV1:
    scope: Mapping[str, str]
    record_refs: Mapping[str, object]
    phase_control_refs: Mapping[str, Mapping[str, str]]

    def __post_init__(self) -> None:
        from collections.abc import Mapping as MappingABC
        _f14_require_v1(all(isinstance(x, MappingABC) for x in
            (self.scope, self.record_refs, self.phase_control_refs)), 'F14_STORAGE_FIELDS')
        scope = dict(self.scope)
        _f14_validate_v1(_F14_SCOPE, scope)
        _f14_require_v1(scope['profile'] == 'POLYMARKET_US_RETAIL_DIRECT', 'F14_STORAGE_SCOPE')
        refs = dict(self.record_refs)
        supplied_controls = dict(self.phase_control_refs)
        _f14_require_v1(set(refs) == set(_F14_RECORD_ROLES)
            and set(supplied_controls) == {'A', 'B', 'C'}, 'F14_STORAGE_VIEW_REFS')
        _f14_require_v1(all(isinstance(value, MappingABC) for value in supplied_controls.values()),
            'F14_STORAGE_VIEW_REFS')
        controls = {key: dict(value) for key, value in supplied_controls.items()}
        proofs = refs['clock_proofs']
        _f14_require_v1(type(proofs) is tuple and len(proofs) <= 3, 'F14_PHYSICAL_PROOFS')
        identities = [value for key, value in refs.items() if key != 'clock_proofs'] + list(proofs)
        for values in controls.values():
            _f14_require_v1(set(values) == set(_F14_CONTROL_ROLES), 'F14_STORAGE_VIEW_REFS')
            for value in values.values():
                _f14_validate_v1(_F14_ID, value)
            _f14_require_v1(len(values['claim_ref']) <= 248
                and values['result_binding_ref'] == values['claim_ref'] + '::RESULT',
                'F14_CONTROL_RESULT_BINDING')
            identities.extend(values.values())
        for value in identities:
            _f14_validate_v1(_F14_ID, value)
        _f14_require_v1(len(identities) == len(set(identities)), 'F14_CONTROL_ID_ALIAS')
        object.__setattr__(self, 'scope', _f14_freeze_v1(scope))
        object.__setattr__(self, 'record_refs', _f14_freeze_v1(refs))
        object.__setattr__(self, 'phase_control_refs', _f14_freeze_v1(controls))


@dataclass(frozen=True, slots=True)
class PrivateEvidenceReadSnapshotV1:
    scope: Mapping[str, str]
    records_by_ref: Mapping[str, EconomicReceiptEventSpineV1]
    control_records_by_ref: Mapping[str, object]
    present_record_refs: frozenset[str]
    publication_intent_or_none: OutboxIntentRecordV1 | None

    def __post_init__(self) -> None:
        for name in ('scope', 'records_by_ref', 'control_records_by_ref'):
            object.__setattr__(self, name, _f14_freeze_v1(getattr(self, name)))
        _f14_require_v1(type(self.present_record_refs) is frozenset, 'F14_PHYSICAL_SET')


def _f14_requested_identities_v1(request):
    _f14_require_v1(type(request) is PrivateEvidenceReadRequestV1, 'F14_STORAGE_FIELDS')
    refs = request.record_refs
    identities = {value for key, value in refs.items() if key != 'clock_proofs'}
    identities.update(refs['clock_proofs'])
    for values in request.phase_control_refs.values():
        identities.update(values.values())
    return frozenset(identities)


def _f14_memory_payload_v1(request, rid, value):
    from .lifecycle import TransitionDispositionV1
    from .outbox import OutboxDispatchStateV1
    refs, controls = request.record_refs, request.phase_control_refs
    if rid == refs['publication_intent']:
        expected = OutboxIntentRecordV1
        _f14_require_v1(type(value) is expected and type(value.dispatch_state) is OutboxDispatchStateV1,
            'F14_STORAGE_FIELDS')
    elif any(rid == control['claim_ref'] for control in controls.values()):
        expected = IdempotencyClaimReceiptV1
        _f14_require_v1(type(value) is expected and type(value.claim_state) is IdempotencyClaimStateV1,
            'F14_STORAGE_FIELDS')
    elif any(rid == control['result_binding_ref'] for control in controls.values()):
        expected = _IdempotencyResultBindingV1
    elif any(rid == control['transition_ref'] for control in controls.values()):
        expected = StateTransitionReceiptV1
        _f14_require_v1(type(value) is expected and type(value.disposition) is TransitionDispositionV1,
            'F14_STORAGE_FIELDS')
    else:
        expected = EconomicReceiptEventSpineV1
        _f14_require_v1(type(value) is expected, 'F14_STORAGE_FIELDS')
        if rid == refs['companion']:
            _private_clock_reconstruct_spine_v1(value, expected_record_id=rid)
        else:
            _f14_singleton_witness_v1(value, rid)
    _f14_require_v1(type(value) is expected, 'F14_STORAGE_FIELDS')
    return deterministic_json(value)


def _f14_reconstruct_snapshot_v1(request, rows):
    """Validate all physical membership before hydrating actual committed rows."""
    from .transaction import _f14_physical_prefix_v1
    from .lifecycle import TransitionDispositionV1
    _f14_requested_identities_v1(request)
    _f14_require_v1(type(rows) is dict and set(rows) == set(APPEND_ONLY_TABLES_V1),
        'F14_STORAGE_VIEW_TABLES')
    refs, controls = request.record_refs, request.phase_control_refs
    phases = {'A': (refs['raw'], refs['transport']),
        'B': (refs['capture_commit'], refs['publication'], refs['companion'], *refs['clock_proofs']),
        'C': (refs['companion_commit'],)}
    roles = {refs['raw']: 'raw', refs['transport']: 'transport',
        refs['capture_commit']: 'capture', refs['publication']: 'publication',
        refs['companion']: 'companion', refs['companion_commit']: 'completion',
        refs['publication_intent']: 'intent'}
    roles.update({rid: f'proof{i}' for i, rid in enumerate(refs['clock_proofs'])})
    for phase, control in controls.items():
        roles.update({control['claim_ref']: phase + '.claim',
            control['result_binding_ref']: phase + '.result',
            control['transition_ref']: phase + '.transition'})
    present = [rid for values in rows.values() for rid in values]
    _f14_require_v1(len(present) == len(set(present)) and set(present) <= set(roles),
        'F14_STORAGE_VIEW_MEMBERSHIP')
    stage = _f14_physical_prefix_v1(len(refs['clock_proofs']), frozenset(roles[rid] for rid in present))
    records, technical = {}, {}
    intent = None
    kinds = {'A': ('RAW', 'TRANSPORT'),
        'B': ('CAPTURE_COMMIT', 'PUBLICATION', None, *('CLOCK_PROOF' for _ in refs['clock_proofs'])),
        'C': ('COMPANION_COMMIT',)}
    for phase in ('A', 'B', 'C')[:stage]:
        control = dict(controls[phase])
        phase_ids = set(phases[phase]) | set(control.values())
        if phase == 'A':
            phase_ids.add(refs['publication_intent'])
        selected = {table: {rid: text for rid, text in values.items() if rid in phase_ids}
                    for table, values in rows.items()}
        restored = _f14_hydrate_phase_storage_view_v1(selected, phase=phase,
            proof_count=len(refs['clock_proofs']), expected_scope=dict(request.scope),
            receipt_refs=phases[phase], **control,
            publication_intent_ref=refs['publication_intent'] if phase == 'A' else None)
        for rid, kind in zip(phases[phase], kinds[phase], strict=True):
            records[rid] = _f14_typed_spine_v1(selected['receipt_records'][rid], rid, kind, dict(request.scope))
        claim = dict(restored['claim'])
        claim['claim_state'] = IdempotencyClaimStateV1(claim['claim_state'])
        technical[control['claim_ref']] = IdempotencyClaimReceiptV1(**claim)
        binding = dict(restored['binding'])
        binding['created_at'] = parse_utc(binding['created_at'], field_name='created_at')
        technical[control['result_binding_ref']] = _IdempotencyResultBindingV1(**binding)
        transition = dict(restored['request']['state_transition'])
        transition['disposition'] = TransitionDispositionV1(transition['disposition'])
        technical[control['transition_ref']] = StateTransitionReceiptV1(**transition)
        if phase == 'A':
            from .outbox import OutboxDispatchStateV1
            data = dict(restored['request']['publication_intent_or_none'])
            data['dispatch_state'] = OutboxDispatchStateV1(data['dispatch_state'])
            intent = OutboxIntentRecordV1(**data)
        for rid in (control['claim_ref'], control['result_binding_ref'], control['transition_ref']):
            text = next(values[rid] for values in selected.values() if rid in values)
            _f14_require_v1(deterministic_json(technical[rid]) == text, 'F14_STORAGE_NONCANONICAL')
    return PrivateEvidenceReadSnapshotV1(dict(request.scope), records, technical, frozenset(present), intent)
