"""Standard-library SQLite deterministic reference/test adapter (never production)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from _sqlite3 import (
    Error as _SQLiteError,
    IntegrityError as _SQLiteIntegrityError,
    OperationalError as _SQLiteOperationalError,
    connect as _open_reference_connection,
)

from .accounting import JournalPostingV1, JournalTransactionV1, ReconciliationBreakReceiptV1
from .context import parse_utc
from .errors import PersistenceContractError, ReasonCode, TransactionContractError
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
    PersistenceAdapterV1,
    PersistenceAvailabilityV1,
    PersistenceTransactionV1,
)
from .receipts import DurableComputationExecutionReceiptRecordV1, EconomicEventRecordV1, EconomicReceiptEventSpineV1, ValueLineageEdgeV1
from .serialization import deterministic_json, safe_json_loads


def _iso(value: datetime | str, name: str) -> str:
    return parse_utc(value, field_name=name).isoformat()


class _SQLiteReferenceTransactionV1(PersistenceTransactionV1):
    def __init__(self, adapter: "SQLiteReferenceAdapterV1") -> None:
        self._adapter = adapter
        self._active = True

    @property
    def is_active(self) -> bool:
        return self._active

    def commit(self) -> None:
        if not self._active:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "transaction is no longer active")
        try:
            self._adapter._connection.execute("COMMIT")
        except _SQLiteError as exc:
            try:
                self._adapter._connection.execute("ROLLBACK")
            except _SQLiteError:
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
        except _SQLiteError as exc:
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
            self._connection = _open_reference_connection(
                path_text,
                isolation_level=None,
                check_same_thread=True,
                timeout=busy_timeout_ms / 1000,
            )
            self._install_and_verify_schema()
            self._availability = PersistenceAvailabilityV1.AVAILABLE_REFERENCE
        except PersistenceContractError:
            if hasattr(self, "_connection"):
                self._connection.close()
            raise
        except _SQLiteError as exc:
            if hasattr(self, "_connection"):
                self._connection.close()
            raise PersistenceContractError(
                ReasonCode.PERSISTENCE_UNAVAILABLE,
                "SQLite reference initialization failed",
            ) from exc

    @property
    def availability(self) -> PersistenceAvailabilityV1:
        return self._availability

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
        if self._availability is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "reference persistence is unavailable")
        if self._active_transaction is not None and self._active_transaction.is_active:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "nested transactions are forbidden")
        try:
            self._connection.execute("BEGIN IMMEDIATE")
        except _SQLiteOperationalError as exc:
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
        except _SQLiteIntegrityError as exc:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, f"duplicate or invalid {kind}") from exc
        except _SQLiteError as exc:
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
        self._transaction(transaction)
        payload = record.typed_payload
        if isinstance(payload, DurableComputationExecutionReceiptRecordV1) and any(
            not self._record_exists(ref) for ref in payload.dependency_receipt_refs
        ):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "durable receipt dependency is absent")
        if self._exact_duplicate("receipt_records", "record_id", record.record_id, record):
            return
        self._assert_cross_table_identity_available("receipt_records", record.record_id)
        self._insert(transaction, "INSERT INTO receipt_records VALUES(?,?,?,?,?)", (record.record_id, _iso(record.effective_at, "effective_at"), _iso(record.recorded_at, "recorded_at"), record.aggregate_id, deterministic_json(record)), "receipt record")

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
        self._transaction(transaction)
        if any(self._connection.execute("SELECT 1 FROM economic_events WHERE economic_event_id=?", (ref,)).fetchone() is None for ref in journal.economic_event_refs):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "journal economic-event reference is absent")
        if self._exact_duplicate("journal_transactions", "journal_transaction_id", journal.journal_transaction_id, journal):
            return
        self._assert_cross_table_identity_available("journal_transactions", journal.journal_transaction_id)
        self._insert(transaction, "INSERT INTO journal_transactions VALUES(?,?,?,?)", (journal.journal_transaction_id, _iso(journal.effective_at, "effective_at"), _iso(journal.recorded_at, "recorded_at"), deterministic_json(journal)), "journal transaction")

    def insert_journal_posting(self, transaction: PersistenceTransactionV1, posting: JournalPostingV1) -> None:
        self._transaction(transaction)
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

    def insert_reversal_link(self, transaction: PersistenceTransactionV1, reversal: object) -> None:
        self._transaction(transaction)
        reversal_id = getattr(reversal, "reversal_receipt_id", None)
        original_ref = getattr(reversal, "original_event_or_transaction_ref", None)
        reversal_transaction_ref = getattr(reversal, "reversal_transaction_ref", None)
        if not isinstance(reversal_id, str) or not self._record_exists(original_ref) or not self._record_exists(reversal_transaction_ref):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "reversal linkage records are absent")
        if self._exact_duplicate("reversal_links", "reversal_receipt_id", reversal_id, reversal):
            return
        self._assert_cross_table_identity_available("reversal_links", reversal_id)
        self._insert(transaction, "INSERT INTO reversal_links VALUES(?,?,?,?,?,?)", (reversal_id, original_ref, reversal_transaction_ref, _iso(getattr(reversal, "effective_at"), "effective_at"), _iso(getattr(reversal, "recorded_at"), "recorded_at"), deterministic_json(reversal)), "reversal link")

    def insert_reconciliation_break(self, transaction: PersistenceTransactionV1, reconciliation_break: ReconciliationBreakReceiptV1) -> None:
        self._transaction(transaction)
        if self._exact_duplicate("reconciliation_breaks", "break_receipt_id", reconciliation_break.break_receipt_id, reconciliation_break):
            return
        self._assert_cross_table_identity_available("reconciliation_breaks", reconciliation_break.break_receipt_id)
        self._insert(transaction, "INSERT INTO reconciliation_breaks VALUES(?,?,?,?,?)", (reconciliation_break.break_receipt_id, reconciliation_break.reconciliation_run_id, _iso(reconciliation_break.effective_at, "effective_at"), _iso(reconciliation_break.recorded_at, "recorded_at"), deterministic_json(reconciliation_break)), "reconciliation break")

    def get_record(self, record_ref: str) -> object | None:
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
                payload = safe_json_loads(payload_text)
                sequence = int(payload.get("sequence", payload.get("event_sequence", payload.get("aggregate_version_after", 0)))) if isinstance(payload, dict) else 0
                results.append((aggregate, sequence, recorded, identity_value, payload))
        return tuple(payload for *_, payload in sorted(results, key=lambda row: row[:4]))
