"""Standard-library SQLite deterministic reference/test adapter (never production)."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import os
import sqlite3
import time
from types import MappingProxyType
from typing import Mapping

from .accounting import (
    AccountingAmountV1,
    EntrySideV1,
    JournalPostingV1,
    JournalTransactionV1,
    ReconciliationBreakReceiptV1,
)
from .context import _native_ident, _native_require, _public_counter_v1, _native_utc_nanoseconds, parse_utc
from .errors import ContractValidationError, PersistenceContractError, ReasonCode, SerializationSafetyError, TransactionContractError
from .idempotency import IdempotencyClaimReceiptV1, IdempotencyClaimStateV1, IdempotencyOutcomeV1
from .lifecycle import StateTransitionReceiptV1
from .migrations import (
    APPEND_ONLY_TABLES_V1,
    REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1,
    REFERENCE_SCHEMA_COLUMNS_V1,
    REFERENCE_SCHEMA_V1,
    REFERENCE_SCHEMA_VERSION_V1,
    append_only_trigger_statements_v1,
)
from .outbox import OutboxIntentRecordV1
from .persistence import (
    IdempotencyAcquireResultV1,
    PrivateEvidenceReadRequestV1, PrivateEvidenceReadSnapshotV1,
    _f14_requested_identities_v1, _f14_reconstruct_snapshot_v1,
    PersistenceAdapterV1,
    PersistenceAvailabilityV1,
    PersistenceTransactionV1,
    _source_action_reserved_v1, _public_record_reserved_v1,
)
from .receipts import (
    DurableComputationExecutionReceiptRecordV1, EconomicEventRecordV1,
    EconomicReceiptEventSpineV1, EconomicRecordTypeV1, PrivateObservationClockReceiptV1,
    ValueLineageEdgeV1, _private_clock_reconstruct_spine_v1,
    PrivateEvidenceWitnessV1, _f14_singleton_witness_v1,
    SourceUseControlRecordV1, _source_use_stream_id_v1, _source_use_record_ref_v1,
    _source_use_reconstruct_spine_v1, _source_use_from_storage_v1, _source_use_append_disposition_v1,
)
from .rollback import (
    JournalReversalBundleV1,
    ReversalHistoryViewV1,
    ReversalReceiptV1,
)
from .serialization import (deterministic_json, safe_json_loads,
    _f14_require_v1, _f14_validate_v1, _F14_ID)


def _iso(value: datetime | str, name: str) -> str:
    return parse_utc(value, field_name=name).isoformat()


def _payload_mapping(payload_json: str, kind: str) -> Mapping[str, object]:
    payload = safe_json_loads(payload_json)
    if not isinstance(payload, Mapping):
        raise PersistenceContractError(
            ReasonCode.REVERSAL_INVALID,
            f"committed {kind} payload is not an object",
        )
    return payload


def _journal_from_payload(payload_json: str) -> JournalTransactionV1:
    row = _payload_mapping(payload_json, "journal")
    try:
        return JournalTransactionV1(
            journal_transaction_id=str(row["journal_transaction_id"]),
            transaction_class=str(row["transaction_class"]),
            economic_event_refs=tuple(str(value) for value in row["economic_event_refs"]),
            posting_refs=tuple(str(value) for value in row["posting_refs"]),
            effective_at=str(row["effective_at"]),
            recorded_at=str(row["recorded_at"]),
            description_code=str(row["description_code"]),
            authority_class=str(row["authority_class"]),
            reversal_of_transaction_id=(
                None
                if row.get("reversal_of_transaction_id") is None
                else str(row["reversal_of_transaction_id"])
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PersistenceContractError(
            ReasonCode.REVERSAL_INVALID,
            "committed journal payload cannot be hydrated exactly",
        ) from exc


def _posting_from_payload(payload_json: str) -> JournalPostingV1:
    row = _payload_mapping(payload_json, "posting")
    try:
        return JournalPostingV1(
            posting_id=str(row["posting_id"]),
            journal_transaction_id=str(row["journal_transaction_id"]),
            account_id=str(row["account_id"]),
            entry_side=EntrySideV1(str(row["entry_side"])),
            amount_text=str(row["amount_text"]),
            ledger_unit=str(row["ledger_unit"]),
            currency_or_asset=str(row["currency_or_asset"]),
            basis=str(row["basis"]),
            scale=int(row["scale"]),
            effective_at=str(row["effective_at"]),
            recorded_at=str(row["recorded_at"]),
            source_event_ref=str(row["source_event_ref"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PersistenceContractError(
            ReasonCode.REVERSAL_INVALID,
            "committed posting payload cannot be hydrated exactly",
        ) from exc


def _reversal_from_payload(payload_json: str) -> ReversalReceiptV1:
    row = _payload_mapping(payload_json, "reversal receipt")
    try:
        remaining = tuple(
            AccountingAmountV1(
                amount_text=str(amount["amount_text"]),
                currency_or_asset=str(amount["currency_or_asset"]),
                ledger_unit=str(amount["ledger_unit"]),
                basis=str(amount["basis"]),
                scale=int(amount["scale"]),
                rounding_policy_ref=str(amount["rounding_policy_ref"]),
            )
            for amount in row["remaining_reversible_amounts"]
            if isinstance(amount, Mapping)
        )
        if len(remaining) != len(row["remaining_reversible_amounts"]):
            raise TypeError("remaining reversal amount is not an object")
        return ReversalReceiptV1(
            reversal_receipt_id=str(row["reversal_receipt_id"]),
            original_event_or_transaction_ref=str(
                row["original_event_or_transaction_ref"]
            ),
            reversal_event_ref=str(row["reversal_event_ref"]),
            reversal_transaction_ref=str(row["reversal_transaction_ref"]),
            reason_code=str(row["reason_code"]),
            authority_ref=str(row["authority_ref"]),
            effective_at=str(row["effective_at"]),
            recorded_at=str(row["recorded_at"]),
            replacement_ref=(
                None
                if row.get("replacement_ref") is None
                else str(row["replacement_ref"])
            ),
            remaining_reversible_amounts=remaining,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PersistenceContractError(
            ReasonCode.REVERSAL_INVALID,
            "committed reversal receipt payload cannot be hydrated exactly",
        ) from exc


class _SQLiteReferenceTransactionV1(PersistenceTransactionV1):
    def __init__(self, adapter: "SQLiteReferenceAdapterV1") -> None:
        self._adapter = adapter
        self._active = True
        self._reversal_snapshot_contaminated = False

    @property
    def is_active(self) -> bool:
        return self._active

    def commit(self) -> None:
        if not self._active:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "transaction is no longer active")
        try:
            self._adapter._connection.execute("COMMIT")
        except sqlite3.Error as exc:
            try:
                self._adapter._connection.execute("ROLLBACK")
            except sqlite3.Error:
                self._adapter._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "SQLite reference commit failed") from exc
        finally:
            self._active = False
            self._adapter._active_transaction = None

    def rollback(self) -> None:
        if not self._active:
            return
        try:
            self._adapter._connection.execute("ROLLBACK")
        except sqlite3.Error as exc:
            self._adapter._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            raise PersistenceContractError(
                ReasonCode.PERSISTENCE_UNAVAILABLE,
                "SQLite reference rollback failed; adapter integrity is unknown",
            ) from exc
        finally:
            self._active = False
            self._adapter._active_transaction = None


class SQLiteReferenceAdapterV1(PersistenceAdapterV1):
    """File-backed or in-memory SQLite reference profile with append-only schema."""

    is_production_adapter = False
    _ready_availability = PersistenceAvailabilityV1.AVAILABLE_REFERENCE

    def __init__(self, database_path: str | Path, *, busy_timeout_ms: int, max_transaction_attempts: int) -> None:
        if isinstance(busy_timeout_ms, bool) or not isinstance(busy_timeout_ms, int) or busy_timeout_ms < 0:
            raise PersistenceContractError(ReasonCode.INCOMPLETE_CONTRACT, "busy_timeout_ms must be explicit nonnegative integer")
        if isinstance(max_transaction_attempts, bool) or not isinstance(max_transaction_attempts, int) or max_transaction_attempts < 1:
            raise PersistenceContractError(ReasonCode.INCOMPLETE_CONTRACT, "max_transaction_attempts must be explicit positive integer")
        path_text = str(database_path)
        if not path_text:
            raise PersistenceContractError(ReasonCode.INCOMPLETE_CONTRACT, "database_path is required")
        self.database_path = path_text
        self.busy_timeout_ms = busy_timeout_ms
        self.max_transaction_attempts = max_transaction_attempts
        self._active_transaction: _SQLiteReferenceTransactionV1 | None = None
        self._availability = PersistenceAvailabilityV1.UNAVAILABLE
        try:
            self._connection = sqlite3.connect(
                path_text,
                isolation_level=None,
                check_same_thread=True,
                timeout=busy_timeout_ms / 1000,
            )
            self._install_and_verify_schema()
            self._availability = self._ready_availability
        except PersistenceContractError:
            if hasattr(self, "_connection"):
                self._connection.close()
            raise
        except sqlite3.Error as exc:
            if hasattr(self, "_connection"):
                self._connection.close()
            raise PersistenceContractError(
                ReasonCode.PERSISTENCE_UNAVAILABLE,
                "SQLite reference initialization failed",
            ) from exc

    @property
    def availability(self) -> PersistenceAvailabilityV1:
        return (PersistenceAvailabilityV1.INTEGRITY_FAILURE
                if self._source_use_integrity_failed_v1 else self._availability)

    def _install_and_verify_schema(self) -> None:
        connection = self._connection
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
        if self.database_path != ":memory:":
            mode = connection.execute("PRAGMA journal_mode=DELETE").fetchone()[0]
            if str(mode).lower() != "delete":
                self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
                raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "SQLite reference journal mode must be DELETE")
            connection.execute("PRAGMA synchronous=EXTRA")
        for statement in REFERENCE_SCHEMA_V1:
            connection.execute(statement)
        row = connection.execute("SELECT schema_version FROM qku_schema_version WHERE singleton=1").fetchone()
        if row is None:
            connection.execute("INSERT INTO qku_schema_version(singleton,schema_version) VALUES(1,?)", (REFERENCE_SCHEMA_VERSION_V1,))
        elif row[0] != REFERENCE_SCHEMA_VERSION_V1:
            self._availability = PersistenceAvailabilityV1.SCHEMA_MISMATCH
            raise PersistenceContractError(ReasonCode.SCHEMA_MISMATCH, "SQLite reference schema version mismatch")
        for statement in append_only_trigger_statements_v1():
            connection.execute(statement)
        for table, expected_columns in REFERENCE_SCHEMA_COLUMNS_V1.items():
            actual_columns = tuple(row[1] for row in connection.execute(f"PRAGMA table_info({table})").fetchall())
            if actual_columns != expected_columns:
                self._availability = PersistenceAvailabilityV1.SCHEMA_MISMATCH
                raise PersistenceContractError(ReasonCode.SCHEMA_MISMATCH, f"SQLite reference schema mismatch for {table}")
        expected_triggers = {
            f"{table}_reject_{operation}"
            for table in APPEND_ONLY_TABLES_V1
            for operation in ("update", "delete")
        }
        actual_triggers = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall()
        }
        if not expected_triggers <= actual_triggers:
            self._availability = PersistenceAvailabilityV1.SCHEMA_MISMATCH
            raise PersistenceContractError(ReasonCode.SCHEMA_MISMATCH, "SQLite append-only trigger set is incomplete")
        if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "foreign_keys pragma was not retained")
        if connection.execute("PRAGMA trusted_schema").fetchone()[0] != 0:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "trusted_schema pragma was not disabled")

    def close(self) -> None:
        if self._active_transaction is not None and self._active_transaction.is_active:
            self._active_transaction.rollback()
        self._connection.close()
        self._availability = PersistenceAvailabilityV1.UNAVAILABLE

    def begin_transaction(self) -> PersistenceTransactionV1:
        if self.availability is not self._ready_availability:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "reference persistence is unavailable")
        if self._active_transaction is not None and self._active_transaction.is_active:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "nested transactions are forbidden")
        try:
            self._connection.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as exc:
            reason = (
                ReasonCode.REFERENCE_SQLITE_BUSY_BEFORE_SIDE_EFFECT
                if getattr(exc, "sqlite_errorcode", None) in {5, 6}
                else ReasonCode.PERSISTENCE_UNAVAILABLE
            )
            raise PersistenceContractError(reason, "SQLite reference BEGIN IMMEDIATE failed") from exc
        transaction = _SQLiteReferenceTransactionV1(self)
        self._active_transaction = transaction
        return transaction

    def _transaction(self, transaction: PersistenceTransactionV1) -> _SQLiteReferenceTransactionV1:
        if transaction is not self._active_transaction or not isinstance(transaction, _SQLiteReferenceTransactionV1) or not transaction.is_active:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "transaction does not belong to adapter or is inactive")
        return transaction

    def _insert(self, transaction: PersistenceTransactionV1, sql: str, values: tuple[object, ...], kind: str) -> None:
        self._transaction(transaction)
        try:
            self._connection.execute(sql, values)
        except sqlite3.IntegrityError as exc:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, f"duplicate or invalid {kind}") from exc
        except sqlite3.Error as exc:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, f"SQLite reference write failed for {kind}") from exc

    def _exact_duplicate(self, table: str, identity_column: str, identity: str, payload: object) -> bool:
        row = self._connection.execute(
            f"SELECT payload_json FROM {table} WHERE {identity_column}=?", (identity,)
        ).fetchone()
        if row is None:
            return False
        if row[0] == deterministic_json(payload):
            return True
        raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, f"conflicting duplicate {table} identity")

    def _record_exists(self, record_ref: str) -> bool:
        for table in APPEND_ONLY_TABLES_V1:
            if table == "idempotency_claims":
                continue
            identity = REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1[table]
            if self._connection.execute(f"SELECT 1 FROM {table} WHERE {identity}=?", (record_ref,)).fetchone() is not None:
                return True
        return False

    def _assert_cross_table_identity_available(self, table: str, identity: str) -> None:
        for other_table, identity_column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items():
            if other_table == table:
                continue
            if self._connection.execute(
                f"SELECT 1 FROM {other_table} WHERE {identity_column}=?", (identity,)
            ).fetchone() is not None:
                raise PersistenceContractError(
                    ReasonCode.PERSISTENCE_CONFLICT,
                    "record identity is already owned by another table",
                )

    def insert_receipt_record(self, transaction: PersistenceTransactionV1, record: EconomicReceiptEventSpineV1) -> None:
        if _source_action_reserved_v1(record) or _public_record_reserved_v1(record):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "attributed actions are ephemeral only")
        self._transaction(transaction)
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
            not self._record_exists(ref) for ref in payload.dependency_receipt_refs
        ):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "durable receipt dependency is absent")
        if self._exact_duplicate("receipt_records", "record_id", record.record_id, record):
            return
        self._assert_cross_table_identity_available("receipt_records", record.record_id)
        self._insert(transaction, "INSERT INTO receipt_records VALUES(?,?,?,?,?)", (record.record_id, _iso(record.effective_at, "effective_at"), _iso(record.recorded_at, "recorded_at"), record.aggregate_id, deterministic_json(record)), "receipt record")

    def _source_use_read_v1(self, *, record_ref=None, stream_id=None, committed=False):
        if self.availability is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "source-use custody is unavailable")
        try:
            if committed and (self._active_transaction is not None or self._connection.in_transaction):
                raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "source-use read requires committed state")
            if stream_id is None:
                cursor = self._connection.execute(
                    "SELECT record_id,effective_at,recorded_at,aggregate_id,payload_json "
                    "FROM receipt_records WHERE record_id=?", (record_ref,),
                )
            else:
                cursor = self._connection.execute(
                    "SELECT record_id,effective_at,recorded_at,aggregate_id,payload_json "
                    "FROM receipt_records WHERE aggregate_id=? ORDER BY record_id DESC LIMIT 1",
                    ("SOURCE_USE::" + stream_id,),
                )
            try:
                row = cursor.fetchone()
            finally:
                cursor.close()
            if row is None:
                if record_ref is not None:
                    self._assert_cross_table_identity_available("receipt_records", record_ref)
                return None
        except sqlite3.Error as exc:
            # Native busy/connection errors remain available to the caller; never absence.
            if getattr(exc, "sqlite_errorcode", None) in {5, 6}:
                raise
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "SQLite source-use read failed") from exc
        try:
            record = _source_use_from_storage_v1(row[4], record_id=record_ref if stream_id is None else row[0], columns=row[:4])
            if stream_id is not None and record.typed_payload.stream_id != stream_id:
                raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "source-use stored head mismatch")
            return record
        except (PersistenceContractError, SerializationSafetyError):
            self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            raise

    def load_committed_source_use_record_v1(self, record_ref: str) -> EconomicReceiptEventSpineV1 | None:
        _source_use_record_ref_v1(record_ref)
        return self._source_use_read_v1(record_ref=record_ref, committed=True)

    def load_committed_source_use_head_v1(self, stream_id: str) -> EconomicReceiptEventSpineV1 | None:
        _source_use_stream_id_v1(stream_id)
        return self._source_use_read_v1(stream_id=stream_id, committed=True)

    def load_source_use_head_for_update_v1(
        self, transaction: PersistenceTransactionV1, stream_id: str,
    ) -> EconomicReceiptEventSpineV1 | None:
        _source_use_stream_id_v1(stream_id)
        tx = self._transaction(transaction)
        if type(tx) is not _SQLiteReferenceTransactionV1 or tx._adapter is not self:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "source-use transaction ownership mismatch")
        return self._source_use_read_v1(stream_id=stream_id)

    def load_source_use_record_for_update_v1(
        self, transaction: PersistenceTransactionV1, record_ref: str,
    ) -> EconomicReceiptEventSpineV1 | None:
        _source_use_record_ref_v1(record_ref)
        tx = self._transaction(transaction)
        if type(tx) is not _SQLiteReferenceTransactionV1 or tx._adapter is not self:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "source-use transaction ownership mismatch")
        return self._source_use_read_v1(record_ref=record_ref)

    def insert_value_lineage_edge(self, transaction: PersistenceTransactionV1, edge: ValueLineageEdgeV1) -> None:
        self._transaction(transaction)
        if not self._record_exists(edge.producer_record_id) or not self._record_exists(edge.consumer_record_id):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "lineage producer/consumer record is absent")
        if self._exact_duplicate("value_lineage_edges", "lineage_edge_id", edge.lineage_edge_id, edge):
            return
        self._assert_cross_table_identity_available("value_lineage_edges", edge.lineage_edge_id)
        self._insert(transaction, "INSERT INTO value_lineage_edges VALUES(?,?,?,?,?,?)", (edge.lineage_edge_id, edge.producer_record_id, edge.consumer_record_id, _iso(edge.effective_at, "effective_at"), _iso(edge.recorded_at, "recorded_at"), deterministic_json(edge)), "value-lineage edge")

    def insert_economic_event(self, transaction: PersistenceTransactionV1, event: EconomicEventRecordV1) -> None:
        self._transaction(transaction)
        existing = self._connection.execute(
            "SELECT economic_event_id,payload_json FROM economic_events WHERE aggregate_id=? AND event_sequence=?",
            (event.aggregate_id, event.event_sequence),
        ).fetchone()
        if existing is not None:
            if existing[0] == event.economic_event_id and existing[1] == deterministic_json(event):
                return
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "aggregate event sequence already exists with different payload")
        self._assert_cross_table_identity_available("economic_events", event.economic_event_id)
        self._insert(transaction, "INSERT INTO economic_events VALUES(?,?,?,?,?,?)", (event.economic_event_id, event.aggregate_id, event.event_sequence, _iso(event.effective_at, "effective_at"), _iso(event.recorded_at, "recorded_at"), deterministic_json(event)), "economic event")

    def insert_journal_transaction(self, transaction: PersistenceTransactionV1, journal: JournalTransactionV1) -> None:
        tx = self._transaction(transaction)
        tx._reversal_snapshot_contaminated = True
        if any(self._connection.execute("SELECT 1 FROM economic_events WHERE economic_event_id=?", (ref,)).fetchone() is None for ref in journal.economic_event_refs):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "journal economic-event reference is absent")
        if self._exact_duplicate("journal_transactions", "journal_transaction_id", journal.journal_transaction_id, journal):
            return
        self._assert_cross_table_identity_available("journal_transactions", journal.journal_transaction_id)
        self._insert(transaction, "INSERT INTO journal_transactions VALUES(?,?,?,?)", (journal.journal_transaction_id, _iso(journal.effective_at, "effective_at"), _iso(journal.recorded_at, "recorded_at"), deterministic_json(journal)), "journal transaction")

    def insert_journal_posting(self, transaction: PersistenceTransactionV1, posting: JournalPostingV1) -> None:
        tx = self._transaction(transaction)
        tx._reversal_snapshot_contaminated = True
        if self._connection.execute("SELECT 1 FROM economic_events WHERE economic_event_id=?", (posting.source_event_ref,)).fetchone() is None:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "posting source economic event is absent")
        if self._exact_duplicate("journal_postings", "posting_id", posting.posting_id, posting):
            return
        self._assert_cross_table_identity_available("journal_postings", posting.posting_id)
        self._insert(
            transaction,
            "INSERT INTO journal_postings VALUES(?,?,?,?,?)",
            (posting.posting_id, posting.journal_transaction_id, _iso(posting.effective_at, "effective_at"), _iso(posting.recorded_at, "recorded_at"), deterministic_json(posting)),
            "journal posting",
        )

    def insert_state_transition(self, transaction: PersistenceTransactionV1, transition: StateTransitionReceiptV1) -> None:
        self._transaction(transaction)
        existing = self._connection.execute(
            "SELECT transition_id,payload_json FROM state_transitions WHERE aggregate_id=? AND aggregate_version_after=?",
            (transition.aggregate_id, transition.aggregate_version_after),
        ).fetchone()
        if existing is not None:
            if existing[0] == transition.transition_id and existing[1] == deterministic_json(transition):
                return
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "aggregate version already exists with different payload")
        self._assert_cross_table_identity_available("state_transitions", transition.transition_id)
        self._insert(transaction, "INSERT INTO state_transitions VALUES(?,?,?,?,?,?)", (transition.transition_id, transition.aggregate_id, transition.aggregate_version_after, _iso(transition.effective_at, "effective_at"), _iso(transition.recorded_at, "recorded_at"), deterministic_json(transition)), "state transition")

    def acquire_idempotency_claim(self, transaction: PersistenceTransactionV1, claim: IdempotencyClaimReceiptV1) -> IdempotencyAcquireResultV1:
        self._transaction(transaction)
        if claim.claim_state is not IdempotencyClaimStateV1.ACQUIRED:
            raise PersistenceContractError(ReasonCode.INVALID_CONTRACT, "new idempotency claim must be in ACQUIRED state")
        row = self._connection.execute("SELECT claim_record_id,canonical_request_json FROM idempotency_claims WHERE idempotency_key=?", (claim.idempotency_key,)).fetchone()
        if row is None:
            self._assert_cross_table_identity_available("idempotency_claims", claim.claim_id)
            self._insert(transaction, "INSERT INTO idempotency_claims VALUES(?,?,?,?,?,?,?)", (claim.claim_id, None, claim.idempotency_key, claim.canonical_request_json, None, _iso(claim.created_at, "created_at"), deterministic_json(claim)), "idempotency claim")
            return IdempotencyAcquireResultV1(IdempotencyOutcomeV1.ACQUIRED, claim.claim_id)
        claim_ref, request_json = row
        if request_json != claim.canonical_request_json:
            return IdempotencyAcquireResultV1(IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD, claim_ref)
        binding = self._connection.execute("SELECT result_record_ref FROM idempotency_claims WHERE parent_claim_id=?", (claim_ref,)).fetchone()
        if binding is not None:
            return IdempotencyAcquireResultV1(IdempotencyOutcomeV1.REPLAYED_SAME_PAYLOAD, claim_ref, binding[0])
        return IdempotencyAcquireResultV1(IdempotencyOutcomeV1.IN_PROGRESS, claim_ref)

    def bind_idempotency_result(self, transaction: PersistenceTransactionV1, claim_ref: str, result_record_ref: str, created_at: datetime) -> None:
        self._transaction(transaction)
        if self._connection.execute("SELECT 1 FROM idempotency_claims WHERE claim_record_id=? AND parent_claim_id IS NULL", (claim_ref,)).fetchone() is None or not self._record_exists(result_record_ref):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "claim or result record is absent")
        payload = deterministic_json({"binding_id": f"{claim_ref}::RESULT", "claim_ref": claim_ref, "result_record_ref": result_record_ref, "created_at": created_at})
        self._assert_cross_table_identity_available("idempotency_claims", f"{claim_ref}::RESULT")
        self._insert(transaction, "INSERT INTO idempotency_claims VALUES(?,?,?,?,?,?,?)", (f"{claim_ref}::RESULT", claim_ref, None, None, result_record_ref, _iso(created_at, "created_at"), payload), "idempotency result binding")

    def insert_outbox_intent(self, transaction: PersistenceTransactionV1, intent: OutboxIntentRecordV1) -> None:
        self._transaction(transaction)
        if not self._record_exists(intent.payload_record_ref):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "outbox payload record is absent")
        if self._exact_duplicate("outbox_intents", "outbox_intent_id", intent.outbox_intent_id, intent):
            return
        self._assert_cross_table_identity_available("outbox_intents", intent.outbox_intent_id)
        self._insert(transaction, "INSERT INTO outbox_intents VALUES(?,?,?,?,?)", (intent.outbox_intent_id, intent.aggregate_id, intent.payload_record_ref, _iso(intent.created_at, "created_at"), deterministic_json(intent)), "outbox intent")

    def insert_reversal_link(self, transaction: PersistenceTransactionV1, reversal: ReversalReceiptV1) -> None:
        tx = self._transaction(transaction)
        tx._reversal_snapshot_contaminated = True
        if not isinstance(reversal, ReversalReceiptV1):
            raise PersistenceContractError(
                ReasonCode.REVERSAL_INVALID,
                "reversal linkage must be a typed receipt",
            )
        reversal_id = reversal.reversal_receipt_id
        original_ref = reversal.original_event_or_transaction_ref
        reversal_transaction_ref = reversal.reversal_transaction_ref
        if not self._record_exists(original_ref) or not self._record_exists(reversal_transaction_ref):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "reversal linkage records are absent")
        if self._exact_duplicate("reversal_links", "reversal_receipt_id", reversal_id, reversal):
            return
        self._assert_cross_table_identity_available("reversal_links", reversal_id)
        self._insert(transaction, "INSERT INTO reversal_links VALUES(?,?,?,?,?,?)", (reversal_id, original_ref, reversal_transaction_ref, _iso(getattr(reversal, "effective_at"), "effective_at"), _iso(getattr(reversal, "recorded_at"), "recorded_at"), deterministic_json(reversal)), "reversal link")

    def load_committed_reversal_history(
        self,
        transaction: PersistenceTransactionV1,
        original_transaction_id: str,
    ) -> ReversalHistoryViewV1:
        tx = self._transaction(transaction)
        if tx._reversal_snapshot_contaminated:
            raise PersistenceContractError(
                ReasonCode.REVERSAL_INVALID,
                "committed reversal history must be loaded before journal writes",
            )
        original_row = self._connection.execute(
            "SELECT payload_json FROM journal_transactions "
            "WHERE journal_transaction_id=?",
            (original_transaction_id,),
        ).fetchone()
        if original_row is None:
            raise PersistenceContractError(
                ReasonCode.REVERSAL_INVALID,
                "original journal is absent from the committed transaction snapshot",
            )
        original = _journal_from_payload(original_row[0])
        original_postings: list[JournalPostingV1] = []
        for posting_ref in original.posting_refs:
            posting_row = self._connection.execute(
                "SELECT payload_json FROM journal_postings WHERE posting_id=?",
                (posting_ref,),
            ).fetchone()
            if posting_row is None:
                raise PersistenceContractError(
                    ReasonCode.REVERSAL_INVALID,
                    "original committed journal has a missing posting",
                )
            original_postings.append(_posting_from_payload(posting_row[0]))
        link_rows = self._connection.execute(
            "SELECT payload_json FROM reversal_links "
            "WHERE original_ref=? "
            "ORDER BY recorded_at,reversal_receipt_id",
            (original_transaction_id,),
        ).fetchall()
        bundles: list[JournalReversalBundleV1] = []
        for (link_payload,) in link_rows:
            link = _reversal_from_payload(link_payload)
            transaction_row = self._connection.execute(
                "SELECT payload_json FROM journal_transactions "
                "WHERE journal_transaction_id=?",
                (link.reversal_transaction_ref,),
            ).fetchone()
            if transaction_row is None:
                raise PersistenceContractError(
                    ReasonCode.REVERSAL_INVALID,
                    "committed reversal link has no journal",
                )
            reversal_transaction = _journal_from_payload(transaction_row[0])
            reversal_postings: list[JournalPostingV1] = []
            for posting_ref in reversal_transaction.posting_refs:
                posting_row = self._connection.execute(
                    "SELECT payload_json FROM journal_postings WHERE posting_id=?",
                    (posting_ref,),
                ).fetchone()
                if posting_row is None:
                    raise PersistenceContractError(
                        ReasonCode.REVERSAL_INVALID,
                        "committed reversal journal has a missing posting",
                    )
                reversal_postings.append(_posting_from_payload(posting_row[0]))
            bundles.append(
                JournalReversalBundleV1(
                    reversal_transaction,
                    tuple(reversal_postings),
                    link,
                )
            )
        return ReversalHistoryViewV1(
            original,
            tuple(original_postings),
            tuple(bundles),
        )

    def insert_reconciliation_break(self, transaction: PersistenceTransactionV1, reconciliation_break: ReconciliationBreakReceiptV1) -> None:
        self._transaction(transaction)
        if self._exact_duplicate("reconciliation_breaks", "break_receipt_id", reconciliation_break.break_receipt_id, reconciliation_break):
            return
        self._assert_cross_table_identity_available("reconciliation_breaks", reconciliation_break.break_receipt_id)
        self._insert(transaction, "INSERT INTO reconciliation_breaks VALUES(?,?,?,?,?)", (reconciliation_break.break_receipt_id, reconciliation_break.reconciliation_run_id, _iso(reconciliation_break.effective_at, "effective_at"), _iso(reconciliation_break.recorded_at, "recorded_at"), deterministic_json(reconciliation_break)), "reconciliation break")

    def load_committed_private_clock_receipt_v1(
        self, record_ref: str,
    ) -> EconomicReceiptEventSpineV1 | None:
        if self._active_transaction is not None and self._active_transaction.is_active:
            raise TransactionContractError(
                ReasonCode.TRANSACTION_STATE_INVALID, "F13 committed read requires no active transaction",
            )
        try:
            if self._connection.in_transaction:
                raise TransactionContractError(
                    ReasonCode.TRANSACTION_STATE_INVALID, "F13 connection transaction remains active",
                )
            if self._availability is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE:
                raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "reference persistence is unavailable")
            _native_ident(record_ref)
            cursor = self._connection.execute(
                "SELECT record_id, effective_at, recorded_at, aggregate_id, payload_json "
                "FROM receipt_records WHERE record_id = ?", (record_ref,),
            )
            try:
                row = cursor.fetchone()
            finally:
                cursor.close()
        except sqlite3.Error as exc:
            raise PersistenceContractError(
                ReasonCode.PERSISTENCE_UNAVAILABLE, "SQLite reference private-clock read failed",
            ) from exc
        if row is None:
            return None
        if any(type(cell) is not str for cell in row):
            raise PersistenceContractError(ReasonCode.SCHEMA_MISMATCH, "F13_STORED_SQL_CELL_TYPE_INVALID")
        try:
            payload = safe_json_loads(row[4])
        except (RecursionError, UnicodeError) as exc:
            raise SerializationSafetyError(
                ReasonCode.SERIALIZATION_UNSAFE, "F13_STORED_ENVELOPE_INVALID",
            ) from exc
        record = _private_clock_reconstruct_spine_v1(payload, expected_record_id=record_ref)
        if row[:4] != (
            record.record_id, _iso(record.effective_at, "effective_at"),
            _iso(record.recorded_at, "recorded_at"), record.aggregate_id,
        ):
            raise PersistenceContractError(ReasonCode.SCHEMA_MISMATCH, "F13_STORED_SQL_METADATA_MISMATCH")
        if row[4] != deterministic_json(record):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "F13_STORED_SQL_CANONICAL_MISMATCH")
        return record

    @contextmanager
    def _f14_read_rows_v1(self, identities):
        """One read transaction, owned here; never end a caller's transaction."""
        if self._active_transaction is not None and self._active_transaction.is_active:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID,
                'F14 committed read requires no active transaction')
        if self._availability is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE,
                'F14 reference persistence is unavailable')
        owned = False
        cursor = None
        try:
            if self._connection.in_transaction:
                raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID,
                    'F14 connection transaction remains active')
            cursor = self._connection.cursor()
            cursor.execute('BEGIN')
            owned = True
            rows = {table: {} for table in APPEND_ONLY_TABLES_V1}
            mirrors = {}
            parameters = tuple(sorted(identities))
            placeholders = ','.join('?' for _ in parameters)
            for table in APPEND_ONLY_TABLES_V1:
                identity = REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1[table]
                columns = REFERENCE_SCHEMA_COLUMNS_V1[table]
                cursor.execute(f"SELECT {','.join(columns)} FROM {table} "
                    f"WHERE {identity} IN ({placeholders})", parameters)
                for values in cursor.fetchall():
                    _f14_require_v1(type(values[0]) is str and type(values[-1]) is str,
                        'F14_STORAGE_TEXT')
                    _f14_require_v1(values[0] not in rows[table], 'F14_STORAGE_VIEW_MEMBERSHIP')
                    rows[table][values[0]] = values[-1]
                    mirrors[(table, values[0])] = tuple(values)
            yield rows, mirrors
        except sqlite3.Error as exc:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE,
                'SQLite reference private-evidence read failed') from exc
        finally:
            if cursor is not None:
                try:
                    if owned:
                        cursor.execute('ROLLBACK')
                finally:
                    cursor.close()

    def load_committed_private_evidence_witness_v1(
        self, record_ref: str,
    ) -> EconomicReceiptEventSpineV1 | None:
        _f14_validate_v1(_F14_ID, record_ref)
        with self._f14_read_rows_v1(frozenset((record_ref,))) as (rows, mirrors):
            found = [(table, text) for table, values in rows.items() for text in values.values()]
            if not found:
                return None
            _f14_require_v1(len(found) == 1 and found[0][0] == 'receipt_records',
                'F14_STORAGE_VIEW_MEMBERSHIP')
            record = _f14_singleton_witness_v1(found[0][1], record_ref)
            _f14_verify_sql_mirror_v1('receipt_records', mirrors[('receipt_records', record_ref)], record)
            return record

    def load_committed_private_evidence_snapshot_v1(
        self, request: PrivateEvidenceReadRequestV1,
    ) -> PrivateEvidenceReadSnapshotV1:
        identities = _f14_requested_identities_v1(request)
        with self._f14_read_rows_v1(identities) as (rows, mirrors):
            snapshot = _f14_reconstruct_snapshot_v1(request, rows)
            values = dict(snapshot.records_by_ref)
            values.update(snapshot.control_records_by_ref)
            if snapshot.publication_intent_or_none is not None:
                intent = snapshot.publication_intent_or_none
                values[intent.outbox_intent_id] = intent
            for (table, rid), columns in mirrors.items():
                _f14_verify_sql_mirror_v1(table, columns, values[rid])
            return snapshot

    def get_record(self, record_ref: str) -> object | None:
        if type(record_ref) is not str:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "record_ref must be an exact string",
            )
        if record_ref.startswith("SOURCE_USE::"):
            return self.load_committed_source_use_record_v1(record_ref)
        if record_ref.startswith(("SOURCE_ACTION::", '["PUBLIC_')):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "attributed actions are ephemeral only")
        for table in APPEND_ONLY_TABLES_V1:
            identity = REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1[table]
            row = self._connection.execute(f"SELECT payload_json FROM {table} WHERE {identity}=?", (record_ref,)).fetchone()
            if row is not None:
                return safe_json_loads(row[0])
        return None

    def get_idempotency_result(self, idempotency_key: str) -> str | None:
        row = self._connection.execute("SELECT result.result_record_ref FROM idempotency_claims AS claim JOIN idempotency_claims AS result ON result.parent_claim_id=claim.claim_record_id WHERE claim.idempotency_key=?", (idempotency_key,)).fetchone()
        return None if row is None else row[0]

    def reconstruct_as_of(self, *, effective_cutoff: datetime, recorded_cutoff: datetime, aggregate_scope: tuple[str, ...]) -> tuple[object, ...]:
        results: list[tuple[str, int, str, str, object]] = []
        effective_text = parse_utc(effective_cutoff, field_name="effective_cutoff").isoformat()
        recorded_text = parse_utc(recorded_cutoff, field_name="recorded_cutoff").isoformat()
        table_specs = (
            ("receipt_records", "record_id", "aggregate_id"),
            ("value_lineage_edges", "lineage_edge_id", None),
            ("economic_events", "economic_event_id", "aggregate_id"),
            ("journal_transactions", "journal_transaction_id", None),
            ("journal_postings", "posting_id", None),
            ("state_transitions", "transition_id", "aggregate_id"),
            ("reversal_links", "reversal_receipt_id", None),
            ("reconciliation_breaks", "break_receipt_id", None),
        )
        for table, identity, aggregate_column in table_specs:
            if aggregate_scope and aggregate_column is None:
                continue
            aggregate_select = aggregate_column if aggregate_column is not None else "''"
            aggregate_clause = "" if not aggregate_scope else f" AND {aggregate_column} IN ({','.join('?' for _ in aggregate_scope)})"
            params: tuple[object, ...] = (effective_text, recorded_text, *aggregate_scope)
            rows = self._connection.execute(
                f"SELECT {aggregate_select},{identity},recorded_at,payload_json FROM {table} WHERE effective_at<=? AND recorded_at<=?{aggregate_clause}",
                params,
            ).fetchall()
            for aggregate, identity_value, recorded, payload_text in rows:
                if identity_value.startswith('["PUBLIC_'):
                    raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE,
                        "public records require their purpose-specific owner")
                if table == "receipt_records" and identity_value.startswith("SOURCE_USE::"):
                    original = self.load_committed_source_use_record_v1(identity_value)
                    results.append((aggregate, original.sequence, recorded, identity_value, original))
                    continue
                payload = safe_json_loads(payload_text)
                sequence = int(payload.get("sequence", payload.get("event_sequence", payload.get("aggregate_version_after", 0)))) if isinstance(payload, dict) else 0
                results.append((aggregate, sequence, recorded, identity_value, payload))
        return tuple(payload for *_, payload in sorted(results, key=lambda row: row[:4]))


_SYNTHETIC_PUBLIC_ROOTS_V1 = {}
_PUBLIC_COMMIT_WITNESSES_V1 = {}


class _SyntheticPublicStorageRootV1:
    def __init__(self):
        raise TypeError("synthetic public root requires its explicit test factory")

    def __reduce__(self):
        raise TypeError("storage capabilities cannot be serialized")

    def __copy__(self):
        raise TypeError("storage capabilities cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("storage capabilities cannot be copied")


def _public_file_identity_v1(path):
    for ancestor in (path, *path.parents):
        stat = ancestor.lstat()
        _native_require(not ancestor.is_symlink() and not getattr(stat, "st_file_attributes", 0) & 0x400,
                        "public storage path contains a link/reparse object")
    stat = path.stat()
    _native_require(path.is_file() and stat.st_nlink == 1, "public storage database must be a nonlinked regular file")
    return stat.st_dev, stat.st_ino


def _create_synthetic_public_storage_root_v1(*, database_path: Path, root_ref: str,
                                           expires_at_ns: int):
    """Read-only qualification of an explicit fixture file; never a native root."""
    _native_require(type(database_path) is type(Path()) and database_path.is_absolute(), "explicit fixture path required")
    _native_ident(root_ref)
    _public_counter_v1(expires_at_ns)
    result = object.__new__(_SyntheticPublicStorageRootV1)
    result.path, result.root_ref, result.expires_at_ns = database_path, root_ref, expires_at_ns
    result.identity, result.process_id = _public_file_identity_v1(database_path), os.getpid()
    _SYNTHETIC_PUBLIC_ROOTS_V1[id(result)] = result
    return result


def _public_root_facts_v1(root):
    if type(root) is _SyntheticPublicStorageRootV1:
        _native_require(_SYNTHETIC_PUBLIC_ROOTS_V1.get(id(root)) is root and root.process_id == os.getpid()
                        and time.time_ns() < root.expires_at_ns
                        and _public_file_identity_v1(root.path) == root.identity, "synthetic storage custody changed")
        return dict(root_ref=root.root_ref, database_path=str(root.path), expires_at_ns=root.expires_at_ns,
                    native_qualified=False, generation=0)
    from ...service.owner_source_use_windows import _public_storage_facts_v1

    return _public_storage_facts_v1(root)


class _PublicCommitWitnessV1:
    def __init__(self):
        raise TypeError("completion witness requires actual adapter commit/readback")

    def __reduce__(self):
        raise TypeError("completion witness is process-local")

    def __copy__(self):
        raise TypeError("completion witness cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("completion witness cannot be copied")


class _SQLitePhaseATransactionV1(_SQLiteReferenceTransactionV1):
    def __init__(self, adapter):
        super().__init__(adapter)
        self.public_records = {}
        self.completion_witness = None
        self.public_batch = None

    def commit(self):
        adapter = self._adapter
        adapter._check_public_store_v1()
        _native_require(self.is_active and adapter._active_transaction is self and self.public_records,
                        "public commit requires its owned nonempty transaction")
        if self.public_batch is not None:
            from ..orderbook_event_state_snapshot.handoff import _require_public_pit_batch_v1

            batch = _require_public_pit_batch_v1(batch=self.public_batch, adapter=adapter)
            _native_require(tuple(self.public_records) == tuple(record.record_id for record in batch[3])
                            and tuple(self.public_records.values()) == batch[4],
                            "public transaction is missing an exact prepared batch member")
        try:
            adapter._bound_public_busy_wait_v1()
            adapter._connection.execute("COMMIT")
            self._active = False
            adapter._active_transaction = None
            for identity, expected in self.public_records.items():
                adapter._bound_public_busy_wait_v1()
                row = adapter._connection.execute("SELECT payload_json FROM receipt_records WHERE record_id=?", (identity,)).fetchone()
                _native_require(row is not None and row[0] == expected, "public committed readback differs from appended bytes")
            adapter._check_public_store_v1()
            completed_wall, completed_mono = time.time_ns(), time.monotonic_ns()
            witness = object.__new__(_PublicCommitWitnessV1)
            witness.adapter, witness.transaction, witness.process_id = adapter, self, os.getpid()
            witness.records = MappingProxyType(dict(self.public_records))
            witness.evidence = MappingProxyType(dict(evidence_class="ADAPTER_CONFIRMED_SYNC_UPPER_BOUND",
                completed_wall_ns=completed_wall, completed_monotonic_ns=completed_mono,
                backend_assigned_commit_ns=None, original_record_refs=tuple(self.public_records),
                native_qualified=adapter._native_qualified))
            _PUBLIC_COMMIT_WITNESSES_V1[id(witness)] = witness
            self.completion_witness = witness
        except BaseException:
            # Even a returned COMMIT with failed readback is not positive completion evidence.
            adapter._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            if self._active:
                try:
                    adapter._connection.execute("PRAGMA busy_timeout=0")
                    adapter._connection.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
            self._active = False
            adapter._active_transaction = None
            raise

    def rollback(self):
        # Releasing this adapter's transaction must remain possible after expiry.
        self._adapter._connection.execute("PRAGMA busy_timeout=0")
        super().rollback()


class SQLitePhaseAAdapterV1(SQLiteReferenceAdapterV1):
    """Bounded file-backed Phase A store; it is never a production deployment claim."""

    is_production_adapter = False
    persistence_class = "PHASE_A_LOCAL_DURABLE"
    _ready_availability = PersistenceAvailabilityV1.AVAILABLE_PHASE_A_LOCAL_DURABLE

    def __init__(self, *, root_capability, source_use_binding, busy_timeout_ms: int):
        from .source_policy import _public_binding_facts_v1

        self._root_capability, self._public_binding = root_capability, source_use_binding
        facts = _public_root_facts_v1(root_capability)
        grant = _public_binding_facts_v1(source_use_binding)
        _native_require(grant["storage_root_ref"] == facts["root_ref"]
                        and grant["native_qualified"] == facts["native_qualified"]
                        and grant["source_inputs"].get("storage_root") is root_capability,
                        "storage root/grant origin mismatch")
        self._native_qualified = facts["native_qualified"]
        self._root_ref = facts["root_ref"]
        self._public_generation = grant["scope_generation"]
        self._retention_expires_ns = min(facts["expires_at_ns"], grant["retention_expires_at_ns"])
        _public_counter_v1(busy_timeout_ms, allow_zero=True)
        _native_require(busy_timeout_ms == grant["budget"].storage_busy_timeout_ms, "storage timeout differs from grant")
        self._public_transaction_serial = 0
        try:
            # Schema qualification cannot spend a caller's whole busy allowance
            # before the live grant can be rechecked. It performs no busy waits.
            super().__init__(facts["database_path"], busy_timeout_ms=0, max_transaction_attempts=1)
            self.busy_timeout_ms = busy_timeout_ms
            self._check_public_store_v1()
        except BaseException:
            if hasattr(self, "_connection"):
                self._connection.close()
            raise

    def __reduce__(self):
        raise TypeError("public data store is process-local")

    def __copy__(self):
        raise TypeError("public data store cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("public data store cannot be copied")

    def _install_and_verify_schema(self):
        objects = self._connection.execute("SELECT type,name,sql FROM sqlite_master").fetchall()
        tables = {name: sql for kind, name, sql in objects if kind == "table"}
        _native_require(tables or not self._native_qualified,
                        "native public storage requires a previously qualified schema")
        if objects:
            # A capture verifies an existing schema; CREATE IF NOT EXISTS must
            # never silently replace missing guards or accept changed constraints.
            expected_tables = {statement.split()[5]: statement.replace(" IF NOT EXISTS", "")
                               for statement in REFERENCE_SCHEMA_V1}
            expected_triggers = {statement.split()[5]: statement.replace(" IF NOT EXISTS", "")
                                 for statement in append_only_trigger_statements_v1()}
            triggers = {name: sql for kind, name, sql in objects if kind == "trigger"}
            _native_require(tables == expected_tables and triggers == expected_triggers
                            and all(kind in {"table", "trigger"} or
                                    (kind == "index" and name.startswith("sqlite_autoindex_") and sql is None)
                                    for kind, name, sql in objects), "unknown public storage schema or append guards")
            rows = self._connection.execute("SELECT singleton,schema_version FROM qku_schema_version").fetchall()
            _native_require(rows == [(1, REFERENCE_SCHEMA_VERSION_V1)], "public storage schema migration required")
            for table, columns in REFERENCE_SCHEMA_COLUMNS_V1.items():
                actual = tuple(row[1] for row in self._connection.execute("PRAGMA table_info(" + table + ")"))
                _native_require(actual == columns, "public storage columns differ from the qualified schema")
        super()._install_and_verify_schema()
        for pragma, expected in (("journal_mode", "delete"), ("synchronous", 3), ("foreign_keys", 1),
                                 ("trusted_schema", 0), ("busy_timeout", self.busy_timeout_ms)):
            actual = self._connection.execute("PRAGMA " + pragma).fetchone()
            _native_require(actual is not None and actual[0] == expected, "public storage pragma readback mismatch")
        self._connection.enable_load_extension(False)

    def _check_public_store_v1(self):
        from .source_policy import _public_binding_facts_v1

        root = _public_root_facts_v1(self._root_capability)
        grant = _public_binding_facts_v1(self._public_binding)
        _native_require(root["root_ref"] == self._root_ref and grant["storage_root_ref"] == self._root_ref
                        and grant["source_inputs"].get("storage_root") is self._root_capability
                        and grant["scope_generation"] == self._public_generation
                        and grant["native_qualified"] == self._native_qualified
                        and time.time_ns() < self._retention_expires_ns, "public storage scope/retention expired")
        return grant

    def begin_transaction(self):
        self._bound_public_busy_wait_v1()
        super().begin_transaction()
        try:
            self._check_public_store_v1()
        except BaseException:
            self._connection.execute("PRAGMA busy_timeout=0")
            self._active_transaction.rollback()
            raise
        transaction = _SQLitePhaseATransactionV1(self)
        self._active_transaction._active = False
        self._active_transaction = transaction
        return transaction

    def _bound_public_busy_wait_v1(self):
        grant = self._check_public_store_v1()
        remaining = min(grant["budget"].deadline_monotonic_ns,
                        self._public_binding._deadline) - time.monotonic_ns()
        _native_require(remaining > 0, "public storage deadline expired")
        # Floor to SQLite's millisecond unit: a sub-millisecond remainder means
        # no busy wait, rather than rounding beyond the original permission.
        effective = min(grant["budget"].storage_busy_timeout_ms, remaining // 1_000_000)
        self._connection.execute("PRAGMA busy_timeout=" + str(effective))
        return effective

    def insert_receipt_record(self, transaction, record):
        from .receipts import (_public_validate_spine_v1, _public_spine_from_json_v1,
                               PublicNativeObservationV1, PublicPublicationRecordV1)

        self._transaction(transaction)
        _native_require(type(transaction) is _SQLitePhaseATransactionV1, "wrong public transaction type")
        grant = self._check_public_store_v1()
        pit = record.record_type in {EconomicRecordTypeV1.PIT_COMMIT_INTENT,
            EconomicRecordTypeV1.PIT_CANONICAL_EVENT, EconomicRecordTypeV1.PIT_CAPTURE_AND_GAP}
        if transaction.public_batch is not None:
            from ..orderbook_event_state_snapshot.handoff import _require_public_pit_batch_v1

            batch = _require_public_pit_batch_v1(batch=transaction.public_batch, adapter=self)
            _native_require(any(item is record for item in batch[3]), "append is not an original prepared batch member")
        if pit:
            _native_require(transaction.public_batch is not None, "public PIT append requires its complete prepared batch")
            record.__post_init__()
            record.typed_payload.__post_init__()
            _native_require(record.schema_version == "PIT_RECEIPT_SPINE_V2"
                            and record.semantic_owner == "S1_PIT_DATA_PHASE_A_01"
                            and record.implementation_owner == "QKU_RECEIPT_SPINE_PHASE_A_COORDINATOR"
                            and record.context_ref == grant["scope_ref"]
                            and record.authority_class == "PUBLIC_DATA_CANDIDATE_NO_OPERATING_AUTHORITY",
                            "native PIT envelope differs from its owning branch")
        else:
            _public_validate_spine_v1(record)
        payload = record.typed_payload
        if pit:
            _native_require(payload.profile_id is grant["scope"].profile_id, "public PIT profile mismatch")
        elif type(payload) is PublicNativeObservationV1:
            _native_require(record.context_ref == grant["scope_ref"] and payload.profile_id is grant["scope"].profile_id
                            and payload.source_use_action_ref == grant["action_ref"]
                            and payload.scope_generation == self._public_generation
                            and payload.capture_session_id == grant["capture_session_id"]
                            and payload.operation_id in self._public_binding._capture.requested_operation_ids
                            and payload.native_contract_version == grant["scope"].source_contract_version
                            and set(payload.source_binding_refs) <= set(self._public_binding._capture.source_binding_refs),
                            "capture append scope mismatch")
            if self._native_qualified:
                owner = self._public_binding._owner
                _native_require(owner is not None and any(item is payload for item in owner._observations),
                                "native append is not an original owned receive")
                owner._guard_v1()
        elif type(payload) is PublicPublicationRecordV1:
            from ..orderbook_event_state_snapshot.handoff import _require_public_publication_append_v1

            _require_public_publication_append_v1(record=record, adapter=self)
            _native_require(record.context_ref == payload.scope_ref == grant["scope_ref"] and payload.profile_id is grant["scope"].profile_id
                            and payload.source_use_generation == self._public_generation
                            and payload.source_use_action_ref == grant["action_ref"]
                            and payload.capture_session_id == grant["capture_session_id"], "publication append scope mismatch")
        else:
            _native_require(any(row is record for row in grant["control_records"]), "control mirror is not the registered original")
        encoded = deterministic_json(record)
        _native_require(record.record_id not in transaction.public_records, "duplicate append in one public transaction")
        self._bound_public_busy_wait_v1()
        existing = self._connection.execute("SELECT payload_json FROM receipt_records WHERE record_id=?", (record.record_id,)).fetchone()
        _native_require(existing is None, "public append cannot retry an existing identity")
        self._bound_public_busy_wait_v1()
        previous = self._connection.execute("SELECT payload_json FROM receipt_records WHERE aggregate_id=? LIMIT ?",
            (record.aggregate_id, grant["budget"].max_retained_records + 1)).fetchall()
        _native_require(len(previous) <= grant["budget"].max_retained_records, "public retained record bound exceeded")
        previous = tuple(_public_spine_from_json_v1(row[0]) for row in previous)
        if pit:
            # PIT intent/event/capture share an event ordinal. The sealed batch
            # establishes those associations; no public receive ordinal is reused.
            _native_require(all(item.record_id in transaction.public_records for item in previous),
                            "native PIT partition already has a committed or unknown prefix")
        else:
            ordinals = sorted(item.sequence for item in previous)
            _native_require(ordinals == list(range(1, len(ordinals) + 1)) and record.sequence == len(ordinals) + 1,
                            "public append ordinal discontinuity")
        self._assert_cross_table_identity_available("receipt_records", record.record_id)
        self._bound_public_busy_wait_v1()
        self._insert(transaction, "INSERT INTO receipt_records VALUES(?,?,?,?,?)",
                     (record.record_id, _iso(record.effective_at, "effective_at"),
                      _iso(record.recorded_at, "recorded_at"), record.aggregate_id, encoded), "public receipt")
        transaction.public_records[record.record_id] = encoded

    def _commit_public_pit_batch_v1(self, *, batch):
        from ..orderbook_event_state_snapshot.handoff import _require_public_pit_batch_v1

        issued = _require_public_pit_batch_v1(batch=batch, adapter=self)
        transaction = self.begin_transaction()
        transaction.public_batch = batch
        try:
            for record in issued[3]:
                self.insert_receipt_record(transaction, record)
            transaction.commit()
            issued[1]._retained_records = len(issued[3])
            issued[1]._retained_bytes = sum(len(text.encode("utf-8")) for text in issued[4])
            return transaction.completion_witness
        except BaseException:
            try:
                if transaction.is_active:
                    transaction.rollback()
            finally:
                issued[1]._fail_v1()
            raise

    def _read_public_v1(self, request, root_capability, publication):
        from .persistence import PublicCaptureReadRequestV1, PublicPublicationReadRequestV1
        from .receipts import _public_spine_from_json_v1

        cls = PublicPublicationReadRequestV1 if publication else PublicCaptureReadRequestV1
        _native_require(type(request) is cls and root_capability is self._root_capability, "public read requires exact root capability")
        request.__post_init__()
        grant = self._check_public_store_v1()
        _native_require(self._active_transaction is None and self.availability is self._ready_availability,
                        "public reads require committed available storage")
        _native_require(request.read_purpose == "RESTORE_FOR_CURRENT_SESSION", "historical reconstruction requires its distinct evidence grant")
        _native_require(request.root_ref == self._root_ref and request.profile_id is grant["scope"].profile_id
                        and request.scope_ref == grant["scope_ref"]
                        and request.capture_session_id == grant["capture_session_id"]
                        and request.source_use_generation == self._public_generation, "public read scope mismatch")
        refs = request.publication_refs if publication else request.observation_refs
        expected = EconomicRecordTypeV1.PUBLIC_NATIVE_PUBLICATION if publication else EconomicRecordTypeV1.PUBLIC_NATIVE_CAPTURE
        result, total = [], 0
        for identity in refs:
            self._bound_public_busy_wait_v1()
            row = self._connection.execute("SELECT payload_json FROM receipt_records WHERE record_id=?", (identity,)).fetchone()
            _native_require(row is not None, "requested public original is missing")
            total += len(row[0].encode("utf-8"))
            _native_require(total <= request.maximum_bytes, "public read byte bound exceeded")
            record = _public_spine_from_json_v1(row[0])
            _native_require(record.record_type is expected, "requested public identity has the wrong receipt kind")
            payload = record.typed_payload
            generation = payload.source_use_generation if publication else payload.scope_generation
            observed_ns = (payload.issuance_observation_or_none["issued_wall_ns"]
                           if publication and payload.issuance_observation_or_none is not None
                           else payload.internal_publication_wall_ns if publication else payload.received_wall_ns)
            _native_require(record.record_id == identity and record.record_type is expected
                            and payload.profile_id is request.profile_id and payload.capture_session_id == request.capture_session_id
                            and record.context_ref == request.scope_ref
                            and generation == request.source_use_generation
                            and payload.source_use_action_ref == grant["action_ref"]
                            and (not publication or payload.scope_ref == request.scope_ref)
                            and observed_ns <= request.effective_cutoff_ns and observed_ns <= request.recorded_cutoff_ns
                            and _native_utc_nanoseconds(record.effective_at.isoformat()) <= request.effective_cutoff_ns
                            and _native_utc_nanoseconds(record.recorded_at.isoformat()) <= request.recorded_cutoff_ns,
                            "public stored identity/cutoff mismatch")
            result.append(record)
        self._check_public_store_v1()
        return tuple(result)

    def load_committed_public_capture_v1(self, request, *, root_capability=None):
        return self._read_public_v1(request, root_capability, False)

    def load_committed_public_publication_v1(self, request, *, root_capability=None):
        return self._read_public_v1(request, root_capability, True)

    def _require_public_commit_witness_v1(self, witness):
        _native_require(type(witness) is _PublicCommitWitnessV1
                        and _PUBLIC_COMMIT_WITNESSES_V1.get(id(witness)) is witness
                        and witness.adapter is self and witness.process_id == os.getpid()
                        and witness.transaction.completion_witness is witness
                        and not witness.transaction.is_active, "public commit witness has no issuing custody")
        self._check_public_store_v1()
        return witness.evidence

    def get_record(self, record_ref):
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "public store requires a bounded purpose-specific read")

    def reconstruct_as_of(self, **kwargs):
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "public store forbids wildcard history reads")


def _f14_verify_sql_mirror_v1(table, values, record):
    """Payloads have already passed bounded hydration before mirror comparison."""
    payload = deterministic_json(record)
    row = safe_json_loads(payload)
    if table == 'receipt_records':
        expected = (row['record_id'], row['effective_at'], row['recorded_at'], row['aggregate_id'], payload)
    elif table == 'state_transitions':
        expected = (row['transition_id'], row['aggregate_id'], row['aggregate_version_after'],
            row['effective_at'], row['recorded_at'], payload)
    elif table == 'idempotency_claims':
        if 'claim_id' in row:
            expected = (row['claim_id'], None, row['idempotency_key'], row['canonical_request_json'],
                None, row['created_at'], payload)
        else:
            expected = (row['binding_id'], row['claim_ref'], None, None, row['result_record_ref'],
                row['created_at'], payload)
    elif table == 'outbox_intents':
        expected = (row['outbox_intent_id'], row['aggregate_id'], row['payload_record_ref'], row['created_at'], payload)
    else:
        raise PersistenceContractError(ReasonCode.SCHEMA_MISMATCH, 'F14_STORAGE_VIEW_MEMBERSHIP')
    _f14_require_v1(len(values) == len(expected)
        and all(type(a) is type(b) and a == b for a, b in zip(values, expected, strict=True)),
        'F14_STORAGE_PLAN_ACTUAL_MISMATCH')
