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
    _EvidenceBoundStoreV1, _evidence_deny_legacy_store_access_v1,
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
            retained = getattr(self, "_evidence_store_binding_v1", None)
            connect = sqlite3.connect
            if retained is not None:
                import _sqlite3
                from types import BuiltinFunctionType
                connect = _sqlite3.connect
                _native_require(type(connect) is BuiltinFunctionType and connect.__module__ == "_sqlite3"
                                and connect.__name__ == "connect", "LP03_NATIVE_SQLITE_FACTORY_REQUIRED")
            self._connection = connect(
                path_text,
                isolation_level=None,
                check_same_thread=True,
                timeout=busy_timeout_ms / 1000,
            )
            if retained is not None:
                _EvidenceBoundStoreV1._assert_opened_database_v1(retained, self)
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

    @classmethod
    def open_evidence_store_v1(cls, *, host_binding, store_binding, owned_role_root,
                               busy_timeout_ms: int, max_transaction_attempts: int):
        """Explicit configured setup; the role file must already have an identity.

        Opening this store does not create a grant or permit generic access.
        The separate setup owner creates/observes the eight files first, avoiding
        a dependency on the not-yet-created assembly grant or store binding.
        """
        _native_require(cls is SQLiteReferenceAdapterV1, "LP03_EXACT_SQLITE_ADAPTER_REQUIRED")
        retained = _EvidenceBoundStoreV1(host_binding=host_binding, binding=store_binding,
                                         owned_role_root=owned_role_root)
        result = None
        try:
            _native_require(store_binding.expected_schema_version == REFERENCE_SCHEMA_VERSION_V1,
                            "LP03_STORE_SCHEMA_VERSION")
            database = _EvidenceBoundStoreV1._database_path_for_open_v1(retained)
            # Retain the exact object before __init__, including its native
            # connection if initialization is interrupted after connect.
            result = object.__new__(cls)
            result._evidence_store_binding_v1 = retained
            cls.__init__(result, database, busy_timeout_ms=busy_timeout_ms,
                         max_transaction_attempts=max_transaction_attempts)
            _EvidenceBoundStoreV1._attach_original_adapter_v1(retained, result)
        except BaseException as original:
            try:
                if result is not None:
                    SQLiteReferenceAdapterV1.close(result)
                else:
                    _EvidenceBoundStoreV1._close_original_objects_v1(retained)
            except BaseException as cleanup:
                raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE,
                    "LP03_STORE_INITIALIZATION_CLEANUP_UNPROVEN:" + type(cleanup).__name__) from original
            raise
        return result

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
        if getattr(self, "_active_transaction", None) is not None and self._active_transaction.is_active:
            self._active_transaction.rollback()
        connection = getattr(self, "_connection", None)
        retained = getattr(self, "_evidence_store_binding_v1", None)
        if retained is not None:
            _EvidenceBoundStoreV1._close_original_database_v1(retained, self)
        elif connection is not None:
            connection.close()
        self._availability = PersistenceAvailabilityV1.UNAVAILABLE

    def _evidence_bootstrap_assembly_v1(self, operation):
        """Closed CONTROL transaction. It cannot accept caller SQL or members."""
        from dataclasses import fields
        from .models import (EvidenceAbsenceV1, EvidenceAssemblyStateV1, EvidenceAssemblyStateRecordV1,
                             EvidencePreparationConsumptionV1, EvidenceRecordHeaderV1)
        from .persistence import _EvidenceControlBootstrapV1
        from .receipts import _lp03_spine_for_record_v1
        from .latency_policy import _EvidenceLocalClockV1
        from ...agents.pr169_agent_orch1_resolvers import _EvidenceIssuerStateV1

        _native_require(type(self) is SQLiteReferenceAdapterV1 and type(operation) is _EvidenceControlBootstrapV1
                        and operation.issuer.control_store is self, "LP03_CONTROL_BOOTSTRAP_ADAPTER")
        _native_require({policy.rights_ref for _, rows in operation.policies for policy in rows}
                        == {ref for selection in operation.envelope_entry[3].assembly_scope.source_selections
                            for ref in selection.required_original_rights_refs}, "LP03_ORIGINAL_SOURCE_RIGHTS_INCOMPLETE")
        _EvidenceControlBootstrapV1._check_current_v1(operation)
        connection = self._connection
        _native_require(type(connection) is sqlite3.Connection and not connection.in_transaction
                        and self._active_transaction is None, "LP03_CONTROL_TRANSACTION_CONFLICT")
        # The final native effects have no Python SQL callback between the
        # retained currentness check and SQLite's original COMMIT implementation.
        sqlite3.Connection.set_trace_callback(connection, None)
        sqlite3.Connection.set_authorizer(connection, None)
        sqlite3.Connection.set_progress_handler(connection, None, 0)
        grant = operation.grant_record
        scope = operation.envelope_entry[3].assembly_scope
        request_json = deterministic_json({"owner_envelope_ref": operation.envelope_entry[0],
                                            "assembly_request": operation.request})
        key_bodies = (
            ("LP03-ASSEMBLY-REQUEST::" + deterministic_json((grant.preparation_natural_key[0],
                operation.envelope_entry[0], operation.request.idempotency_key)), request_json),
            ("LP03-PREPARATION::" + deterministic_json(grant.preparation_natural_key),
                deterministic_json({"preparation_natural_key": grant.preparation_natural_key})),
            ("LP03-PREPARATION-BUDGET::" + deterministic_json((grant.preparation_natural_key[0],
                grant.origin.value, grant.aggregate_budget_ref)), deterministic_json(grant.reserved_preparation_limits)),
        )
        def query(sql, parameters, bound, byte_bound):
            _EvidenceControlBootstrapV1._room_v1(operation, owner_queries=1, record_reads=bound,
                                                query_result_records=bound, read_bytes=byte_bound)
            _EvidenceControlBootstrapV1._check_current_v1(operation)
            _EvidenceControlBootstrapV1._charge_v1(operation, owner_queries=1)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            try:
                rows = sqlite3.Cursor.fetchmany(cursor, bound + 1)
            finally:
                sqlite3.Cursor.close(cursor)
            _EvidenceControlBootstrapV1._charge_v1(operation, record_reads=len(rows), query_result_records=len(rows),
                read_bytes=sum(len(value) if type(value) is bytes else len(deterministic_json(value).encode("utf-8"))
                               for row in rows for value in row))
            _native_require(len(rows) <= bound, "LP03_CONTROL_QUERY_RESULT_BOUND")
            return rows
        def effect(sql, parameters=()):
            _EvidenceControlBootstrapV1._check_current_v1(operation)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            sqlite3.Cursor.close(cursor)
        try:
            _EvidenceControlBootstrapV1._room_v1(operation, control_writes=2)
            _EvidenceControlBootstrapV1._charge_v1(operation, control_writes=1)
            effect("BEGIN IMMEDIATE")
            operation.commit_state = "TRANSACTION_OPEN"
            # The fixed key belongs to this CONTROL file, independently of
            # any new experiment, principal, generation or budget labels.
            lifecycle_key = "LP03-CONTROL-LIFECYCLE:ROOT"
            root_exists = query("SELECT 1 FROM idempotency_claims WHERE idempotency_key=? OR claim_record_id IN (?,?) LIMIT 3",
                (lifecycle_key, lifecycle_key, lifecycle_key + "::RESULT"), 3, 3)
            first_lifecycle = operation.issuer.lifecycle_original is None
            if first_lifecycle:
                if root_exists:
                    raise ContractValidationError(ReasonCode.EVIDENCE_RUN_UNRESOLVED, "LP03_CONTROL_LIFECYCLE_RECOVERY_REQUIRED")
                for table in APPEND_ONLY_TABLES_V1:
                    if query("SELECT 1 FROM " + table + " LIMIT 1", (), 1, 1):
                        raise ContractValidationError(ReasonCode.EVIDENCE_RUN_UNRESOLVED,
                                                      "LP03_CONTROL_UNANCHORED_HISTORY_REQUIRES_RECOVERY")
            else:
                lifecycle = _EvidenceIssuerStateV1._require_lifecycle_original_v1(operation.issuer)
                _native_require(len(root_exists) == 2, "LP03_CONTROL_LIFECYCLE_ROOT_MISSING")
                lifecycle_rows = lifecycle[1].lifecycle_rows
                for row in lifecycle_rows:
                    found = query("SELECT 1 FROM idempotency_claims WHERE claim_record_id=? AND parent_claim_id IS ? "
                        "AND idempotency_key IS ? AND canonical_request_json IS ? AND result_record_ref IS ? "
                        "AND created_at=? AND payload_json=?", row, 1, 1)
                    _native_require(found == [(1,)], "LP03_CONTROL_LIFECYCLE_ROOT_CHANGED")
            rows = query("SELECT 1 FROM idempotency_claims "
                         "WHERE idempotency_key IN (?,?,?)", tuple(key for key, _ in key_bodies), 3, 3)
            # A restarted owner cannot revive an original local deadline. A
            # same-process replay is read back by the issuer before this path.
            _native_require(not rows, "LP03_PREPARATION_ALREADY_RESERVED_OR_UNRESOLVED")
            plan_bound = min(1048576, grant.reserved_preparation_limits.max_read_bytes - operation.consumed["read_bytes"] - 20)
            _native_require(plan_bound > 0, "LP03_PREPARATION_RESOURCE_EXHAUSTED")
            plan_rows = query("SELECT length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) "
                              "FROM receipt_records WHERE record_id=?", (plan_bound, operation.plan.record_id), 1, plan_bound + 20)
            from datetime import UTC, timedelta
            wall = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=grant.created_wall_ns // 1000)
            plan_spine = _lp03_spine_for_record_v1(operation.plan, sequence=0, trace_ref=operation.trace_ref)
            plan_wire = deterministic_json(plan_spine)
            if plan_rows:
                from .receipts import _lp03_spine_from_storage_v1
                _native_require(plan_rows[0][0] <= plan_bound, "LP03_CONTROL_RECORD_BYTE_BOUND")
                original_plan = _lp03_spine_from_storage_v1(plan_rows[0][1],
                                                           expected_record_id=operation.plan.record_id)
                if original_plan.typed_payload.record != operation.plan:
                    raise PersistenceContractError(ReasonCode.EVIDENCE_SCENARIO_MISMATCH, "LP03_FROZEN_PLAN_CONFLICT")
                metadata_rows = query("SELECT 1 FROM receipt_records WHERE record_id=? AND effective_at=? "
                    "AND recorded_at=? AND aggregate_id=?", (original_plan.record_id, original_plan.effective_at.isoformat(),
                    original_plan.recorded_at.isoformat(), original_plan.aggregate_id), 1, 1)
                _native_require(metadata_rows == [(1,)], "LP03_FROZEN_PLAN_STORAGE_JOIN")
                plan_spine, plan_wire = original_plan, plan_rows[0][1].decode("utf-8")
            claims = []
            for index, (key, canonical_body) in enumerate(key_bodies):
                claim_id = grant.record_id + "::CLAIM:" + str(index)
                claim = IdempotencyClaimReceiptV1(claim_id, key, "LP03_ASSEMBLY_BOOTSTRAP", canonical_body,
                    IdempotencyClaimStateV1.ACQUIRED, None, wall, None, None)
                claims.append((claim_id, None, key, canonical_body, None, wall.isoformat(), deterministic_json(claim)))
                result_id = claim_id + "::RESULT"
                binding = deterministic_json(dict(binding_id=result_id, claim_ref=claim_id,
                    result_record_ref=grant.record_id, created_at=wall))
                claims.append((result_id, claim_id, None, None, grant.record_id, wall.isoformat(), binding))
            if first_lifecycle:
                identity = operation.lifecycle_identity_original
                config = operation.issuer.host.public_configuration
                root_body = deterministic_json(dict(schema_version="1.0", operation="LP03_CONTROL_LIFECYCLE_V1",
                    deployment_id=config.deployment_id, control_store_id=scope.control_store_id, origin=config.origin,
                    native_host_identity=config.host_identity, issuer_principal=config.service_principal,
                    supervisor_owner="SVC1", generation=identity[5], issuer_instance_ref=identity[3],
                    supervisor_instance_ref=identity[4], first_grant_ref=grant.record_id,
                    first_deadline_historical=grant.deadline_clock_and_process))
                _native_require(len(root_body.encode("utf-8")) <= 16384, "LP03_CONTROL_LIFECYCLE_BODY_CAPACITY")
                root_claim = IdempotencyClaimReceiptV1(lifecycle_key, lifecycle_key, "LP03_CONTROL_LIFECYCLE",
                    root_body, IdempotencyClaimStateV1.ACQUIRED, None, wall, None, None)
                root_result = dict(binding_id=lifecycle_key + "::RESULT", claim_ref=lifecycle_key,
                                   result_record_ref=grant.record_id, created_at=wall)
                lifecycle_rows = (
                    (lifecycle_key, None, lifecycle_key, root_body, None, wall.isoformat(), deterministic_json(root_claim)),
                    (lifecycle_key + "::RESULT", lifecycle_key, None, None, grant.record_id, wall.isoformat(),
                     deterministic_json(root_result)))
                claims.extend(lifecycle_rows)
            readback_claims = tuple(claims) if first_lifecycle else (*claims, *lifecycle_rows)
            exact_ids = (operation.plan.record_id, grant.record_id, grant.record_id + "::STATE:1",
                         *(row[0] for row in claims))
            _native_require(len(set(exact_ids)) == len(exact_ids), "LP03_CONTROL_MEMBER_IDENTITY_CONFLICT")
            placeholders = ",".join("?" for _ in exact_ids)
            for table, column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items():
                # Table/column identifiers come only from the accepted schema
                # owner. Every queried member is in this one exact roster.
                conflicts = query("SELECT " + column + " FROM " + table + " WHERE " + column
                    + " IN (" + placeholders + ")", exact_ids, len(exact_ids),
                    sum(len(deterministic_json(ref).encode("utf-8")) for ref in exact_ids))
                _native_require(all(table == "receipt_records" and row[0] == operation.plan.record_id and plan_rows
                                    for row in conflicts), "LP03_CONTROL_CROSS_TABLE_IDENTITY_CONFLICT")
            grant_spine = _lp03_spine_for_record_v1(grant, sequence=1, trace_ref=operation.trace_ref)
            header = {field.name: getattr(grant, field.name) for field in fields(EvidenceRecordHeaderV1) if field.name != "kind"}
            header.update(record_id=grant.record_id + "::STATE:1", causation_ref=grant.record_id)
            write_count = len(claims) + 2 + (not plan_rows) + 1  # rows plus original COMMIT
            _EvidenceControlBootstrapV1._room_v1(operation, control_writes=write_count + 1)
            _EvidenceControlBootstrapV1._charge_v1(operation, control_writes=write_count)
            prefix_bytes = operation.consumed["control_bytes"]
            # The count includes this state's own canonical bytes. Only the
            # decimal digit width can change; this finite fixed point is data
            # sizing, not recursive acquisition or a second store read.
            for _ in range(32):
                consumed = EvidencePreparationConsumptionV1(**operation.consumed, aggregate_budget_ref=grant.aggregate_budget_ref)
                admitted = EvidenceAssemblyStateRecordV1(**header, assembly_grant_ref=grant.record_id,
                    preparation_ordinal=grant.preparation_ordinal,
                    predecessor_state_ref_or_absence=EvidenceAbsenceV1("INITIAL_PREPARATION_STATE"),
                    state=EvidenceAssemblyStateV1.ADMITTED, consumed_preparation_budget=consumed,
                    currentness_observation_ref=grant.preparation_fence_ref,
                    input_assembly_ref_or_absence=EvidenceAbsenceV1("NOT_YET_ASSEMBLED"), all_reason_codes=())
                state_spine = _lp03_spine_for_record_v1(admitted, sequence=2, trace_ref=operation.trace_ref)
                spines = (plan_spine, grant_spine, state_spine)
                wires = (plan_wire, deterministic_json(grant_spine), deterministic_json(state_spine))
                total = prefix_bytes + sum(len(row[6].encode("utf-8")) for row in claims)
                if first_lifecycle:
                    total += sum(len(deterministic_json(value).encode("utf-8"))
                                 for row in lifecycle_rows for value in row[:-1])
                total += sum(len(wire.encode("utf-8")) for wire in wires[1 if plan_rows else 0:])
                if operation.consumed["control_bytes"] == total:
                    break
                operation.consumed["control_bytes"] = total
            else:
                raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "LP03_CONTROL_BYTE_SIZING_UNPROVEN")
            _EvidenceControlBootstrapV1._charge_v1(operation)
            operation.readback_refs = tuple(("receipt_records", row.record_id) for row in spines)
            operation.readback_refs += tuple(("idempotency_claims", row[0]) for row in readback_claims)
            operation.readback_bodies = wires + tuple(row[6] for row in readback_claims)
            record_rows = tuple((spine.record_id, spine.effective_at.isoformat(), spine.recorded_at.isoformat(),
                                 spine.aggregate_id, wire) for spine, wire in zip(spines, wires))
            operation.readback_rows = record_rows + readback_claims
            operation.roster_original = (operation.readback_refs, operation.readback_rows, operation.readback_bodies,
                deterministic_json((operation.readback_refs, operation.readback_rows, operation.readback_bodies)))
            operation.bootstrap_original = operation.roster_original
            operation.lifecycle_rows = lifecycle_rows
            written = (operation, operation.lifecycle_identity_original, lifecycle_rows, operation.bootstrap_original)
            operation.bootstrap_write_witness = written
            for row in record_rows[1 if plan_rows else 0:]:
                effect("INSERT INTO receipt_records VALUES(?,?,?,?,?)", row)
            for row in claims:
                effect("INSERT INTO idempotency_claims VALUES(?,?,?,?,?,?,?)", row)
            operation.commit_state = "COMMIT_ATTEMPTED"
            effect("COMMIT")
            operation.commit_state = "COMMITTED_PENDING_READBACK"
            committed = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
            _EvidenceControlBootstrapV1._assert_lifecycle_witnesses_v1(operation)
            _native_require(operation.bootstrap_write_witness is written,
                            "LP03_CONTROL_LIFECYCLE_WRITE_WITNESS_CHANGED")
            operation.bootstrap_commit_observation = committed
            operation.bootstrap_commit_witness = (written, committed)
        except BaseException as error:
            operation.failure_root = error
            try:
                in_transaction = sqlite3.Connection.in_transaction.__get__(connection)
            except BaseException as cleanup_error:
                operation.rollback_state = "UNPROVEN"
                operation.commit_state = "TRANSACTION_STATE_UNPROVEN"
                self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
                operation.failure_unretained = cleanup_error
                try:
                    _EvidenceControlBootstrapV1._retain_failure_secondary_v1(operation, "TRANSACTION_STATE", cleanup_error)
                except BaseException:
                    operation.failure_capture_failed = True
                in_transaction = None
            if in_transaction:
                try:
                    operation.consumed["control_writes"] += 1
                    operation.rollback_state = "ATTEMPTED"
                    cursor = sqlite3.Connection.execute(connection, "ROLLBACK")
                    sqlite3.Cursor.close(cursor)
                    operation.rollback_state = "RETURNED"
                    operation.commit_state = "ROLLED_BACK"
                except BaseException as cleanup_error:
                    operation.rollback_state = "UNPROVEN"
                    operation.commit_state = "ROLLBACK_UNPROVEN"
                    self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
                    operation.failure_unretained = cleanup_error
                    try:
                        _EvidenceControlBootstrapV1._retain_failure_secondary_v1(operation, "ROLLBACK", cleanup_error)
                    except BaseException:
                        operation.failure_capture_failed = True
            elif operation.commit_state in ("COMMIT_ATTEMPTED", "COMMITTED_PENDING_READBACK"):
                operation.commit_state = "COMMIT_OR_OBSERVATION_UNRESOLVED"
            raise
        SQLiteReferenceAdapterV1._evidence_bootstrap_readback_v1(self, operation)
        operation.commit_state = "COMMITTED_AND_READBACK"
        operation.current_state, operation.state_ordinal = admitted, 1
        return grant.record_id

    def _evidence_bootstrap_readback_v1(self, operation):
        return SQLiteReferenceAdapterV1._evidence_read_control_members_v1(self, operation, stage="BOOTSTRAP")

    def _evidence_registration_readback_v1(self, operation, *, parent_assembly=False):
        _native_require(type(parent_assembly) is bool, "LP03_REGISTRATION_READ_STAGE")
        return SQLiteReferenceAdapterV1._evidence_read_control_members_v1(self, operation,
            stage="SEALED_ASSEMBLY" if parent_assembly else "REGISTERED_EXPERIMENT")

    def _evidence_register_experiment_v1(self, operation):
        """One exact preregistration/reservation transaction, with original readback."""
        from dataclasses import fields, replace
        from datetime import UTC, timedelta
        from .models import EvidenceExperimentRecordV1, EvidenceRecordHeaderV1
        from .persistence import _EvidenceRegistrationOperationV1
        from .receipts import _lp03_spine_for_record_v1
        from .latency_policy import _EvidenceLocalClockV1

        owner = _EvidenceRegistrationOperationV1
        _native_require(type(operation) is owner and operation.issuer.control_store is self
                        and operation.commit_state == "POLICIES_RESOLVED" and operation.protocol is not None
                        and operation.parent_readback_observation is not None and not operation.records,
                        "LP03_ORIGINAL_REGISTRATION_POLICIES_REQUIRED")
        owner._check_current_v1(operation)
        original_policy = operation.resolved_policy_original
        _native_require(deterministic_json(operation.protocol) == original_policy[2]
                        and deterministic_json(operation.registration_policy) == original_policy[3],
                        "LP03_REGISTRATION_ORIGINAL_POLICY_CHANGED")
        connection = self._connection
        _native_require(not connection.in_transaction, "LP03_REGISTRATION_TRANSACTION_REENTRY")
        envelope, preparation = operation.envelope_entry[3], operation.preparation
        policy, proposed_claim = operation.registration_policy
        assembly = preparation.input_assembly_members[3]
        experiment_id, claim_id = assembly.record_id + "::EXPERIMENT:1", proposed_claim.record_id
        # The original family and aggregate reservations prevent a new request
        # key, preparation, or experiment label from erasing this work/history.
        request_key = "LP03-REGISTRATION-REQUEST::" + deterministic_json((envelope.envelope_ref, operation.request.idempotency_key))
        natural_key = "LP03-REGISTRATION::" + deterministic_json((envelope.deployment_id, envelope.experiment_id, envelope.experiment_revision))
        family_key = "LP03-CLAIM-FAMILY::" + deterministic_json((envelope.deployment_id, envelope.claim_policy_ref, proposed_claim.immutable_claim_ordinal))
        budget_key = "LP03-EXECUTION-BUDGET::" + deterministic_json((envelope.deployment_id, assembly.origin.value,
                                                                    envelope.aggregate_execution_limits.aggregate_budget_ref))
        keys = (request_key, natural_key, family_key, budget_key)
        claim_ids = tuple(experiment_id + "::RESERVATION:" + str(index) for index in range(len(keys)))
        exact_ids = (experiment_id, claim_id, *(ref for base in claim_ids for ref in (base, base + "::RESULT")))
        _native_require(len(set(exact_ids)) == len(exact_ids), "LP03_REGISTRATION_MEMBER_IDENTITY_CONFLICT")

        def query(sql, parameters, bound, byte_bound):
            owner._room_v1(operation, owner_queries=1, record_reads=bound, query_result_records=bound, read_bytes=byte_bound)
            owner._check_current_v1(operation)
            owner._charge_v1(operation, owner_queries=1)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            try:
                rows = sqlite3.Cursor.fetchmany(cursor, bound + 1)
            finally:
                sqlite3.Cursor.close(cursor)
            owner._charge_v1(operation, record_reads=len(rows), query_result_records=len(rows),
                             read_bytes=sum(len(deterministic_json(value).encode("utf-8")) for row in rows for value in row))
            _native_require(len(rows) <= bound, "LP03_REGISTRATION_QUERY_RESULT_BOUND")
            return rows

        def effect(sql, parameters=()):
            owner._check_current_v1(operation)
            owner._charge_v1(operation, control_writes=1)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            sqlite3.Cursor.close(cursor)

        try:
            # Reserve the whole finite write roster before opening a transaction.
            owner._room_v1(operation, control_writes=len(exact_ids) + 3)
            effect("BEGIN IMMEDIATE")
            operation.commit_state = "TRANSACTION_OPEN"
            _native_require(not query("SELECT 1 FROM idempotency_claims WHERE idempotency_key IN (?,?,?,?)", keys, 4, 4),
                            "LP03_REGISTRATION_ALREADY_RESERVED_OR_UNRESOLVED")
            placeholders = ",".join("?" for _ in exact_ids)
            for table, column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items():
                _native_require(not query("SELECT " + column + " FROM " + table + " WHERE " + column
                    + " IN (" + placeholders + ")", exact_ids, len(exact_ids),
                    sum(len(deterministic_json(ref).encode("utf-8")) for ref in exact_ids)),
                    "LP03_CONTROL_CROSS_TABLE_IDENTITY_CONFLICT")
            wall, mono, cpu = owner._check_current_v1(operation)
            _native_require(operation.protocol.valid_from_wall_ns <= wall < operation.protocol.exclusive_expiry_wall_ns,
                            "LP03_PARAMETER_PROTOCOL_EXPIRED")
            header = {member.name: getattr(proposed_claim, member.name) for member in fields(EvidenceRecordHeaderV1)
                      if member.name != "kind"}
            header.update(record_id=experiment_id, created_wall_ns=wall)
            snapshot = preparation.input_assembly_members[2]
            experiment = EvidenceExperimentRecordV1(**header, owner_envelope_ref=envelope.envelope_ref,
                registration_ordinal=policy["registration_ordinal"], semantic_variant_ref=policy["semantic_variant_ref"],
                selection_history_ref=policy["selection_history"]["history_ref"], input_assembly_ref=assembly.record_id,
                component_closure=envelope.component_closure, callbacks=envelope.callback_pins,
                scopes={name: getattr(snapshot, name) for name in ("market_scope", "venue_scope", "instrument_scope")},
                observation_plan=policy["observation_plan"], comparator_plan=policy["comparator_plan"],
                accounting_policy_ref=policy["accounting_policy_ref"], source_purposes=("EVIDENCE_EXPERIMENT_REGISTRATION_V1",),
                parameter_protocol_ref=operation.protocol.parameter_protocol_ref,
                required_metric_ids=operation.protocol.selected_metric_ids, required_receiver_ids=envelope.required_receiver_ids,
                expiry_wall_ns=min(envelope.exclusive_expiry_wall_ns, operation.protocol.exclusive_expiry_wall_ns))
            claim = replace(proposed_claim, created_wall_ns=wall, preregistered_at_ns=wall, causation_ref=experiment.record_id)
            records = (experiment, claim)
            spines = tuple(_lp03_spine_for_record_v1(record, sequence=preparation.state_ordinal + 5 + index,
                                                   trace_ref=preparation.trace_ref) for index, record in enumerate(records))
            wires = tuple(deterministic_json(spine) for spine in spines)
            created_at = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=wall // 1000)
            canonical_bodies = (
                deterministic_json(dict(owner_envelope_ref=envelope.envelope_ref, registration_request=operation.request)),
                deterministic_json(dict(experiment_id=envelope.experiment_id, experiment_revision=envelope.experiment_revision,
                                        assembly_ref=assembly.record_id, registration_ordinal=experiment.registration_ordinal)),
                deterministic_json(dict(family_ref=claim.family_ref, immutable_claim_ordinal=claim.immutable_claim_ordinal,
                                        candidate_ref=claim.candidate_ref, first_unrevealed_group_ordinal=claim.first_unrevealed_group_ordinal)),
                deterministic_json(dict(aggregate_limits=envelope.aggregate_execution_limits,
                    parameter_protocol=operation.protocol, preparation_audit_ref=preparation.current_state.record_id,
                    registration_consumed_prefix=dict(operation.consumed), observed_wall_ns=wall,
                    observed_monotonic_ns=mono, observed_cpu_ns=cpu, deadline=operation.deadline,
                    parent_readback_observation=operation.parent_readback_observation,
                    accounting_state="RESERVED_WITH_REGISTRATION_TAIL_PENDING")),
            )
            reservations = []
            for ref, key, body in zip(claim_ids, keys, canonical_bodies):
                reservation = IdempotencyClaimReceiptV1(ref, key, "LP03_EXPERIMENT_REGISTRATION", body,
                    IdempotencyClaimStateV1.ACQUIRED, None, created_at, None, None)
                reservations.append((ref, None, key, body, None, created_at.isoformat(), deterministic_json(reservation)))
                result_id = ref + "::RESULT"
                binding = deterministic_json(dict(binding_id=result_id, claim_ref=ref,
                    result_record_ref=experiment.record_id, created_at=created_at))
                reservations.append((result_id, ref, None, None, experiment.record_id, created_at.isoformat(), binding))
            record_rows = tuple((spine.record_id, spine.effective_at.isoformat(), spine.recorded_at.isoformat(),
                                 spine.aggregate_id, wire) for spine, wire in zip(spines, wires))
            total_bytes = sum(len(row[-1].encode("utf-8")) for row in (*record_rows, *reservations))
            owner._room_v1(operation, control_bytes=total_bytes)
            operation.records = records
            operation.readback_refs = tuple(("receipt_records", row[0]) for row in record_rows)
            operation.readback_refs += tuple(("idempotency_claims", row[0]) for row in reservations)
            operation.readback_rows = (*record_rows, *reservations)
            operation.readback_bodies = tuple(row[-1] for row in operation.readback_rows)
            operation.roster_original = (operation.readback_refs, operation.readback_rows, operation.readback_bodies,
                deterministic_json((operation.readback_refs, operation.readback_rows, operation.readback_bodies)))
            for row in record_rows:
                owner._charge_v1(operation, control_bytes=len(row[-1].encode("utf-8")))
                effect("INSERT INTO receipt_records VALUES(?,?,?,?,?)", row)
            for row in reservations:
                owner._charge_v1(operation, control_bytes=len(row[-1].encode("utf-8")))
                effect("INSERT INTO idempotency_claims VALUES(?,?,?,?,?,?,?)", row)
            operation.commit_state = "COMMIT_ATTEMPTED"
            effect("COMMIT")
            operation.commit_state = "COMMITTED_PENDING_READBACK"
            operation.commit_observation = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
        except BaseException:
            if sqlite3.Connection.in_transaction.__get__(connection):
                try:
                    # Cleanup is an observed effect even after the positive
                    # admission expired; it cannot create a usable reference.
                    operation.consumed["control_writes"] += 1
                    cursor = sqlite3.Connection.execute(connection, "ROLLBACK")
                    sqlite3.Cursor.close(cursor)
                    operation.commit_state = "ROLLED_BACK"
                except BaseException:
                    operation.commit_state = "ROLLBACK_UNPROVEN"
                    self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            elif operation.commit_state in ("COMMIT_ATTEMPTED", "COMMITTED_PENDING_READBACK"):
                operation.commit_state = "COMMIT_OR_OBSERVATION_UNRESOLVED"
            raise
        SQLiteReferenceAdapterV1._evidence_registration_readback_v1(self, operation)
        operation.commit_state = "COMMITTED_AND_READBACK"

    def _evidence_bind_registered_compilation_v1(self, operation):
        """Append the original immutable contracts and exact EXPERIMENT successor."""
        from dataclasses import replace
        from datetime import UTC, timedelta
        from .persistence import _EvidenceRegistrationOperationV1
        from .receipts import _lp03_spine_for_record_v1
        from .latency_policy import _EvidenceLocalClockV1
        owner = _EvidenceRegistrationOperationV1
        _native_require(type(operation) is owner and operation.issuer.control_store is self
                        and operation.commit_state == "COMMITTED_AND_READBACK" and operation.binding_state == "ADMITTED"
                        and operation.readback_observation is not None and operation.binding_original is not None,
                        "LP03_COMPILATION_BINDING_ADMISSION")
        owner._check_current_v1(operation)
        original = operation.binding_original
        _native_require(operation.compiler is original[0] and operation.compilation_request is original[1]
                        and operation.compilation is original[2] and operation.binding_spines is original[3]
                        and deterministic_json(operation.compilation_request) == original[4]
                        and deterministic_json(operation.compilation) == original[5]
                        and tuple(deterministic_json(row) for row in operation.binding_spines) == original[6],
                        "LP03_ORIGINAL_COMPILATION_CHANGED")
        connection = self._connection
        _native_require(not connection.in_transaction, "LP03_COMPILATION_TRANSACTION_REENTRY")
        experiment = operation.records[0]
        binding_id = experiment.record_id + "::BOUND:1"
        reservation_id = binding_id + "::RESERVATION"
        exact_ids = (*(spine.record_id for spine in operation.binding_spines), binding_id, reservation_id, reservation_id + "::RESULT")
        _native_require(len(set(exact_ids)) == 5, "LP03_COMPILATION_MEMBER_IDENTITY_CONFLICT")
        natural_key = "LP03-IMMUTABLE-BINDING::" + deterministic_json((experiment.experiment_id, experiment.experiment_revision,
                                                                     experiment.input_assembly_ref))

        def query(sql, parameters, bound, byte_bound):
            owner._room_v1(operation, owner_queries=1, record_reads=bound, query_result_records=bound, read_bytes=byte_bound)
            owner._check_current_v1(operation)
            owner._charge_v1(operation, owner_queries=1)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            try:
                rows = sqlite3.Cursor.fetchmany(cursor, bound + 1)
            finally:
                sqlite3.Cursor.close(cursor)
            owner._charge_v1(operation, record_reads=len(rows), query_result_records=len(rows),
                read_bytes=sum(len(deterministic_json(value).encode("utf-8")) for row in rows for value in row))
            _native_require(len(rows) <= bound, "LP03_COMPILATION_QUERY_BOUND")
            return rows

        def effect(sql, parameters=()):
            owner._check_current_v1(operation)
            owner._charge_v1(operation, control_writes=1)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            sqlite3.Cursor.close(cursor)

        try:
            owner._room_v1(operation, control_writes=8)
            effect("BEGIN IMMEDIATE")
            operation.binding_state = "TRANSACTION_OPEN"
            _native_require(not query("SELECT 1 FROM idempotency_claims WHERE idempotency_key=?", (natural_key,), 1, 1),
                            "LP03_COMPILATION_ALREADY_RESERVED_OR_UNRESOLVED")
            placeholders = ",".join("?" for _ in exact_ids)
            for table, column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items():
                _native_require(not query("SELECT " + column + " FROM " + table + " WHERE " + column
                    + " IN (" + placeholders + ")", exact_ids, 5,
                    sum(len(deterministic_json(ref).encode("utf-8")) for ref in exact_ids)),
                    "LP03_CONTROL_CROSS_TABLE_IDENTITY_CONFLICT")
            wall, mono, cpu = owner._check_current_v1(operation)
            # The immutable legacy lock retains its actual snapshot creation
            # time. Only this native successor observes the later binding.
            binding = replace(experiment, record_id=binding_id, input_lock_ref=operation.compilation.input_lock_id,
                created_wall_ns=wall, causation_ref=experiment.record_id,
                source_lineage_refs=(experiment.record_id, operation.records[1].record_id, experiment.input_assembly_ref,
                                     *(spine.record_id for spine in operation.binding_spines)))
            binding_spine = _lp03_spine_for_record_v1(binding, sequence=operation.preparation.state_ordinal + 7,
                                                     trace_ref=operation.preparation.trace_ref)
            all_spines = (*operation.binding_spines, binding_spine)
            record_rows = tuple((spine.record_id, spine.effective_at.isoformat(), spine.recorded_at.isoformat(),
                                 spine.aggregate_id, deterministic_json(spine)) for spine in all_spines)
            created_at = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=wall // 1000)
            request_body = deterministic_json(dict(request=operation.compilation_request,
                registration_ref=experiment.record_id, binding_ref=binding_id,
                original_aggregate_budget_ref=operation.envelope_entry[3].aggregate_execution_limits.aggregate_budget_ref,
                registration_and_binding_consumed_prefix=dict(operation.consumed),
                original_deadline=operation.deadline, native_observation=(wall, mono, cpu),
                registration_commit_observation=operation.commit_observation,
                registration_readback_observation=operation.readback_observation,
                accounting_state="RESERVED_WITH_BINDING_TAIL_PENDING"))
            reservation = IdempotencyClaimReceiptV1(reservation_id, natural_key, "LP03_IMMUTABLE_EXPERIMENT_BINDING", request_body,
                IdempotencyClaimStateV1.ACQUIRED, None, created_at, None, None)
            reservations = (
                (reservation_id, None, natural_key, request_body, None, created_at.isoformat(), deterministic_json(reservation)),
                (reservation_id + "::RESULT", reservation_id, None, None, binding_id, created_at.isoformat(),
                 deterministic_json(dict(binding_id=reservation_id + "::RESULT", claim_ref=reservation_id,
                                         result_record_ref=binding_id, created_at=created_at))),
            )
            total_bytes = sum(len(row[-1].encode("utf-8")) for row in (*record_rows, *reservations))
            owner._room_v1(operation, control_bytes=total_bytes)
            operation.binding_record = binding
            operation.binding_readback_refs = tuple(("receipt_records", row[0]) for row in record_rows)
            operation.binding_readback_refs += tuple(("idempotency_claims", row[0]) for row in reservations)
            operation.binding_readback_rows = (*record_rows, *reservations)
            operation.binding_readback_bodies = tuple(row[-1] for row in operation.binding_readback_rows)
            operation.binding_roster_original = (operation.binding_readback_refs, operation.binding_readback_rows, operation.binding_readback_bodies,
                deterministic_json((operation.binding_readback_refs, operation.binding_readback_rows, operation.binding_readback_bodies)))
            for row in record_rows:
                owner._charge_v1(operation, control_bytes=len(row[-1].encode("utf-8")))
                effect("INSERT INTO receipt_records VALUES(?,?,?,?,?)", row)
            for row in reservations:
                owner._charge_v1(operation, control_bytes=len(row[-1].encode("utf-8")))
                effect("INSERT INTO idempotency_claims VALUES(?,?,?,?,?,?,?)", row)
            operation.binding_state = "COMMIT_ATTEMPTED"
            effect("COMMIT")
            operation.binding_state = "COMMITTED_PENDING_READBACK"
            operation.binding_commit_observation = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
        except BaseException:
            if sqlite3.Connection.in_transaction.__get__(connection):
                try:
                    operation.consumed["control_writes"] += 1
                    cursor = sqlite3.Connection.execute(connection, "ROLLBACK")
                    sqlite3.Cursor.close(cursor)
                    operation.binding_state = "ROLLED_BACK"
                except BaseException:
                    operation.binding_state = "ROLLBACK_UNPROVEN"
                    self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            elif operation.binding_state in ("COMMIT_ATTEMPTED", "COMMITTED_PENDING_READBACK"):
                operation.binding_state = "COMMIT_OR_OBSERVATION_UNRESOLVED"
            raise
        SQLiteReferenceAdapterV1._evidence_read_control_members_v1(self, operation, stage="BOUND_EXPERIMENT")
        operation.binding_state = "COMMITTED_AND_READBACK"

    def _evidence_read_control_members_v1(self, operation, *, stage):
        from .persistence import _EvidenceControlBootstrapV1
        from .persistence import _EvidenceRegistrationOperationV1, _evidence_control_operation_owner_v1
        from .receipts import _lp03_spine_from_storage_v1
        operation_owner = _evidence_control_operation_owner_v1(operation)
        _native_require(type(self) is SQLiteReferenceAdapterV1 and operation.issuer.control_store is self,
                        "LP03_ORIGINAL_READBACK_OPERATION_REQUIRED")
        if stage == "BOOTSTRAP":
            bootstrap_commit = operation.bootstrap_commit_witness
            _EvidenceControlBootstrapV1._assert_lifecycle_witnesses_v1(operation)
            _native_require(type(operation) is _EvidenceControlBootstrapV1
                            and operation.commit_state in ("COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK")
                            and len(operation.readback_refs) in (11, 12, 13), "LP03_BOOTSTRAP_READBACK_SCOPE")
            refs, bodies, original_rows = operation.readback_refs, operation.readback_bodies, operation.readback_rows
        elif stage == "SEALED_ASSEMBLY":
            from .input_lock import _original_input_assembly_members_v1, _require_original_input_assembly_outcome_v1
            _native_require(type(operation) is _EvidenceRegistrationOperationV1 and operation.commit_state == "NOT_STARTED",
                            "LP03_REGISTRATION_PARENT_READ_SCOPE")
            preparation = operation.preparation
            assembly = _original_input_assembly_members_v1(preparation, preparation.input_assembly_outcome)[3]
            audit, audit_row, commit_observation = preparation.seal_audit_original
            _native_require(preparation.commit_state == "SEALED_AUDIT_COMMITTED_PENDING_READBACK"
                            and commit_observation is not None and len(preparation.readback_refs) == 13
                            and audit is preparation.current_state and audit.input_assembly_ref_or_absence == assembly.record_id
                            and audit.predecessor_state_ref_or_absence == preparation.seal_readback_observation[4],
                            "LP03_REGISTRATION_FINAL_AUDIT_JOIN")
            refs = (*preparation.readback_refs, ("receipt_records", audit.record_id))
            bodies = (*preparation.readback_bodies, audit_row[-1])
            original_rows = (*preparation.readback_rows, audit_row)
        elif stage == "BOUND_EXPERIMENT":
            _native_require(type(operation) is _EvidenceRegistrationOperationV1
                            and operation.binding_state in ("COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK")
                            and operation.binding_record is not None and len(operation.binding_readback_refs) == 5,
                            "LP03_COMPILATION_READBACK_SCOPE")
            refs, bodies, original_rows = operation.binding_readback_refs, operation.binding_readback_bodies, operation.binding_readback_rows
        else:
            _native_require(stage == "REGISTERED_EXPERIMENT" and type(operation) is _EvidenceRegistrationOperationV1
                            and operation.commit_state in ("COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK")
                            and bool(operation.records) and bool(operation.readback_refs), "LP03_REGISTRATION_READBACK_SCOPE")
            refs, bodies, original_rows = operation.readback_refs, operation.readback_bodies, operation.readback_rows
        _native_require(len(refs) == len(bodies) == len(original_rows), "LP03_CONTROL_READBACK_ROSTER")
        operation_owner._check_current_v1(operation)
        reader = _EvidenceBoundStoreV1._open_independent_readback_v1(
            self._evidence_store_binding_v1, operation.issuer.host, self, operation)
        try:
            for (table, ref), expected, original_row in zip(refs, bodies, original_rows):
                expected_bytes = expected.encode("utf-8")
                operation_owner._room_v1(operation, owner_queries=1, record_reads=1,
                    query_result_records=1, read_bytes=len(expected_bytes) + 21)
                operation_owner._check_current_v1(operation)
                operation_owner._charge_v1(operation, owner_queries=1)
                if table == "receipt_records":
                    sql = ("SELECT length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) "
                           "FROM receipt_records WHERE record_id=? AND effective_at=? AND recorded_at=? AND aggregate_id=?")
                else:
                    _native_require(table == "idempotency_claims", "LP03_BOOTSTRAP_READBACK_MEMBER")
                    sql = ("SELECT length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) "
                           "FROM idempotency_claims WHERE claim_record_id=? AND parent_claim_id IS ? "
                           "AND idempotency_key IS ? AND canonical_request_json IS ? AND result_record_ref IS ? AND created_at=?")
                _native_require(original_row[0] == ref and original_row[-1] == expected, "LP03_BOOTSTRAP_EXACT_MEMBER_JOIN")
                cursor = sqlite3.Connection.execute(reader, sql, (len(expected_bytes) + 1, *original_row[:-1]))
                try:
                    rows = sqlite3.Cursor.fetchmany(cursor, 2)
                finally:
                    sqlite3.Cursor.close(cursor)
                operation_owner._charge_v1(operation, record_reads=len(rows), query_result_records=len(rows),
                    read_bytes=sum(len(row[1]) + len(str(row[0])) for row in rows))
                _native_require(len(rows) == 1 and rows[0][0] == len(expected_bytes) and rows[0][1] == expected_bytes,
                                "LP03_BOOTSTRAP_READBACK_MISMATCH")
                if table == "receipt_records":
                    if stage == "BOUND_EXPERIMENT" and ref in tuple(row.record_id for row in operation.binding_spines):
                        from .cohort_compiler import _read_original_compilation_member_v1
                        _read_original_compilation_member_v1(rows[0][1], operation=operation, record_ref=ref)
                    else:
                        _lp03_spine_from_storage_v1(rows[0][1], expected_record_id=ref)
        finally:
            sqlite3.Connection.close(reader)
        if stage == "SEALED_ASSEMBLY":
            _require_original_input_assembly_outcome_v1(preparation, preparation.input_assembly_outcome)
        observed = operation_owner._check_current_v1(operation)
        if stage == "BOOTSTRAP" and operation.bootstrap_readback_observation is None:
            _native_require(operation.bootstrap_commit_observation is not None
                            and operation.bootstrap_commit_witness is bootstrap_commit
                            and operation.roster_original is operation.bootstrap_original,
                            "LP03_CONTROL_LIFECYCLE_FIRST_READBACK_SCOPE")
            operation.bootstrap_readback_observation = (*observed, tuple(operation.consumed.items()))
            operation.bootstrap_readback_witness = (bootstrap_commit, operation.bootstrap_readback_observation)
        elif stage == "SEALED_ASSEMBLY":
            operation.parent_readback_observation = (*observed, tuple(operation.consumed.items()), audit.record_id)
            operation.commit_state = "PARENT_READBACK_CONFIRMED"
        elif stage == "REGISTERED_EXPERIMENT":
            operation.readback_observation = (*observed, tuple(operation.consumed.items()))
        elif stage == "BOUND_EXPERIMENT":
            operation.binding_readback_observation = (*observed, tuple(operation.consumed.items()))

    def _evidence_read_attempt_members_v1(self, attempt, *, parents_in_transaction=False):
        """Only original sealed/registered/bound parents or this attempt's exact rows."""
        from .persistence import _EvidenceAttemptOperationV1, _EvidenceRegistrationOperationV1, _EvidenceBoundStoreV1
        from .receipts import _lp03_spine_from_storage_v1
        from .input_lock import _require_original_input_assembly_outcome_v1
        from .cohort_compiler import _read_original_compilation_member_v1
        _native_require(type(attempt) is _EvidenceAttemptOperationV1 and type(parents_in_transaction) is bool,
                        "LP03_ATTEMPT_READBACK_SCOPE")
        operation, owner = attempt.registration, _EvidenceRegistrationOperationV1
        _native_require(operation.issuer.control_store is self and operation.active_attempt is attempt,
                        "LP03_ATTEMPT_READBACK_OWNER")
        owner._check_current_v1(operation)
        if parents_in_transaction:
            _native_require(attempt.phase == "TRANSACTION_OPEN" and self._connection.in_transaction,
                            "LP03_ATTEMPT_PARENT_TRANSACTION_REQUIRED")
            preparation = operation.preparation
            audit, audit_row, observation = preparation.seal_audit_original
            _native_require(observation is not None and audit is preparation.current_state
                            and len(preparation.readback_refs) == 13 and len(operation.readback_refs) == 10
                            and len(operation.binding_readback_refs) == 5, "LP03_ATTEMPT_PARENT_ROSTER")
            refs = (*preparation.readback_refs, ("receipt_records", audit.record_id),
                    *operation.readback_refs, *operation.binding_readback_refs)
            rows = (*preparation.readback_rows, audit_row, *operation.readback_rows, *operation.binding_readback_rows)
            reader = self._connection
        else:
            _native_require(attempt.phase in ("COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK")
                            and len(attempt.readback_refs) == 6, "LP03_ATTEMPT_READBACK_ROSTER")
            refs, rows = attempt.readback_refs, attempt.readback_rows
            reader = _EvidenceBoundStoreV1._open_independent_readback_v1(
                self._evidence_store_binding_v1, operation.issuer.host, self, operation)
        try:
            _native_require(len(refs) == len(rows), "LP03_ATTEMPT_EXACT_MEMBER_JOIN")
            for (table, ref), original_row in zip(refs, rows):
                expected = original_row[-1].encode("utf-8")
                owner._room_v1(operation, owner_queries=1, record_reads=1, query_result_records=1, read_bytes=len(expected) + 21)
                owner._check_current_v1(operation)
                if table == "receipt_records":
                    sql = ("SELECT length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) "
                           "FROM receipt_records WHERE record_id=? AND effective_at=? AND recorded_at=? AND aggregate_id=?")
                else:
                    _native_require(table == "idempotency_claims", "LP03_ATTEMPT_EXACT_MEMBER_TABLE")
                    sql = ("SELECT length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) "
                           "FROM idempotency_claims WHERE claim_record_id=? AND parent_claim_id IS ? AND idempotency_key IS ? "
                           "AND canonical_request_json IS ? AND result_record_ref IS ? AND created_at=?")
                _native_require(original_row[0] == ref, "LP03_ATTEMPT_EXACT_MEMBER_JOIN")
                owner._charge_v1(operation, owner_queries=1)
                cursor = sqlite3.Connection.execute(reader, sql, (len(expected) + 1, *original_row[:-1]))
                try:
                    actual = sqlite3.Cursor.fetchmany(cursor, 2)
                finally:
                    sqlite3.Cursor.close(cursor)
                owner._charge_v1(operation, record_reads=len(actual), query_result_records=len(actual),
                    read_bytes=sum(len(row[1]) + len(str(row[0])) for row in actual))
                _native_require(len(actual) == 1 and actual[0] == (len(expected), expected), "LP03_ATTEMPT_PARENT_OR_READBACK_MISMATCH")
                if table == "receipt_records":
                    if parents_in_transaction and ref in tuple(row.record_id for row in operation.binding_spines):
                        _read_original_compilation_member_v1(expected, operation=operation, record_ref=ref)
                    else:
                        _lp03_spine_from_storage_v1(expected, expected_record_id=ref)
            if parents_in_transaction:
                _require_original_input_assembly_outcome_v1(preparation, preparation.input_assembly_outcome)
            observed = owner._check_current_v1(operation)
        finally:
            if not parents_in_transaction:
                sqlite3.Connection.close(reader)
        if not parents_in_transaction:
            # Closing the independent reader is included before the last
            # observed currentness and cumulative charge snapshot.
            observed = owner._check_current_v1(operation)
            attempt.readback_observation = (*observed, tuple(operation.consumed.items()))

    def _evidence_issue_attempt_v1(self, attempt):
        from datetime import UTC, timedelta
        from .persistence import _EvidenceAttemptOperationV1, _EvidenceRegistrationOperationV1
        from .receipts import _lp03_spine_for_record_v1
        from .latency_policy import _EvidenceLocalClockV1
        _native_require(type(attempt) is _EvidenceAttemptOperationV1 and attempt.phase == "ADMITTED_FOR_CONTROL_TRANSACTION",
                        "LP03_ATTEMPT_CONTROL_ADMISSION")
        operation, owner, connection = attempt.registration, _EvidenceRegistrationOperationV1, self._connection
        _native_require(operation.issuer.control_store is self and operation.active_attempt is attempt
                        and not connection.in_transaction, "LP03_ATTEMPT_TRANSACTION_REENTRY")
        envelope = operation.envelope_entry[3]
        grant_id = operation.binding_record.record_id + "::" + attempt.request.lane.value + ":1::GRANT"
        request_key = "LP03-ATTEMPT-REQUEST::" + deterministic_json((envelope.envelope_ref, attempt.request.idempotency_key))
        natural_key = "LP03-ATTEMPT::" + deterministic_json((envelope.deployment_id, envelope.experiment_revision,
                    envelope.assembly_scope.generation, attempt.request.lane.value, attempt.request.attempt_ordinal))
        claim_ids = (grant_id + "::REQUEST", grant_id + "::RESERVATION")
        exact_ids = (grant_id, grant_id + "::STATE:0", *(ref for base in claim_ids for ref in (base, base + "::RESULT")))

        def query(sql, parameters, bound, byte_bound):
            owner._room_v1(operation, owner_queries=1, record_reads=bound, query_result_records=bound, read_bytes=byte_bound)
            owner._check_current_v1(operation)
            owner._charge_v1(operation, owner_queries=1)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            try:
                rows = sqlite3.Cursor.fetchmany(cursor, bound + 1)
            finally:
                sqlite3.Cursor.close(cursor)
            owner._charge_v1(operation, record_reads=len(rows), query_result_records=len(rows),
                read_bytes=sum(len(deterministic_json(value).encode("utf-8")) for row in rows for value in row))
            _native_require(len(rows) <= bound, "LP03_ATTEMPT_QUERY_BOUND")
            return rows

        def effect(sql, parameters=()):
            owner._check_current_v1(operation)
            owner._charge_v1(operation, control_writes=1)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            sqlite3.Cursor.close(cursor)

        try:
            owner._room_v1(operation, control_writes=len(exact_ids) + 3)
            effect("BEGIN IMMEDIATE")
            attempt.phase = "TRANSACTION_OPEN"
            SQLiteReferenceAdapterV1._evidence_read_attempt_members_v1(self, attempt, parents_in_transaction=True)
            _native_require(not query("SELECT 1 FROM idempotency_claims WHERE idempotency_key IN (?,?)",
                (request_key, natural_key), 2, 2), "LP03_ATTEMPT_ALREADY_RESERVED_OR_UNRESOLVED")
            placeholders = ",".join("?" for _ in exact_ids)
            for table, column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items():
                _native_require(not query("SELECT " + column + " FROM " + table + " WHERE " + column + " IN (" + placeholders + ")",
                    exact_ids, len(exact_ids), sum(len(deterministic_json(ref).encode("utf-8")) for ref in exact_ids)),
                    "LP03_CONTROL_CROSS_TABLE_IDENTITY_CONFLICT")
            _EvidenceAttemptOperationV1._build_records_v1(attempt)
            spines = tuple(_lp03_spine_for_record_v1(record, sequence=operation.preparation.state_ordinal + 8 + index,
                trace_ref=operation.preparation.trace_ref) for index, record in enumerate((attempt.grant_record, attempt.current_state)))
            record_rows = tuple((spine.record_id, spine.effective_at.isoformat(), spine.recorded_at.isoformat(), spine.aggregate_id,
                                 deterministic_json(spine)) for spine in spines)
            observed = owner._check_current_v1(operation)
            created_at = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=observed[0] // 1000)
            request_body = deterministic_json(dict(request=attempt.request, grant_ref=grant_id, reserved_limits=attempt.limits,
                aggregate_limits=envelope.aggregate_execution_limits, original_deadline=operation.deadline,
                original_binding_commit_observation=operation.binding_commit_observation,
                original_binding_readback_observation=operation.binding_readback_observation,
                cumulative_consumed_prefix=dict(operation.consumed), attempt_consumed_prefix=attempt.current_state.consumed_budget,
                native_observation=observed, accounting_state="RESERVED_WITH_ATTEMPT_TAIL_PENDING"))
            claims = tuple(IdempotencyClaimReceiptV1(ref, key, "LP03_POST_LOCK_ATTEMPT", request_body,
                IdempotencyClaimStateV1.ACQUIRED, None, created_at, None, None) for ref, key in zip(claim_ids, (request_key, natural_key)))
            reservations = tuple(row for claim in claims for row in (
                (claim.claim_id, None, claim.idempotency_key, request_body, None, created_at.isoformat(), deterministic_json(claim)),
                (claim.claim_id + "::RESULT", claim.claim_id, None, None, grant_id, created_at.isoformat(),
                 deterministic_json(dict(binding_id=claim.claim_id + "::RESULT", claim_ref=claim.claim_id,
                                         result_record_ref=grant_id, created_at=created_at)))))
            all_rows = (*record_rows, *reservations)
            owner._room_v1(operation, control_bytes=sum(len(row[-1].encode("utf-8")) for row in all_rows))
            attempt.readback_refs = tuple(("receipt_records", row[0]) for row in record_rows) + tuple(("idempotency_claims", row[0]) for row in reservations)
            attempt.readback_rows, attempt.readback_bodies = all_rows, tuple(row[-1] for row in all_rows)
            attempt.roster_original = (attempt.readback_refs, attempt.readback_rows, attempt.readback_bodies)
            for row in record_rows:
                owner._charge_v1(operation, control_bytes=len(row[-1].encode("utf-8")))
                effect("INSERT INTO receipt_records VALUES(?,?,?,?,?)", row)
            for row in reservations:
                owner._charge_v1(operation, control_bytes=len(row[-1].encode("utf-8")))
                effect("INSERT INTO idempotency_claims VALUES(?,?,?,?,?,?,?)", row)
            attempt.phase = "COMMIT_ATTEMPTED"
            effect("COMMIT")
            attempt.phase = "COMMITTED_PENDING_READBACK"
            attempt.commit_observation = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
        except BaseException:
            if sqlite3.Connection.in_transaction.__get__(connection):
                try:
                    operation.consumed["control_writes"] += 1
                    cursor = sqlite3.Connection.execute(connection, "ROLLBACK")
                    sqlite3.Cursor.close(cursor)
                    attempt.phase = "ROLLED_BACK"
                except BaseException:
                    attempt.phase = "ROLLBACK_UNPROVEN"
                    self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            elif attempt.phase in ("COMMIT_ATTEMPTED", "COMMITTED_PENDING_READBACK"):
                attempt.phase = "COMMIT_OR_OBSERVATION_UNRESOLVED"
            raise
        SQLiteReferenceAdapterV1._evidence_read_attempt_members_v1(self, attempt)
        attempt.phase = "COMMITTED_AND_READBACK"

    def _evidence_prepare_lane_rows_v1(self, operation):
        from .persistence import _EvidenceLaneOperationV1
        _native_require(type(operation) is _EvidenceLaneOperationV1 and operation.platform._store is self
                        and operation.phase == "PREPARED" and self._connection.in_transaction,
                        "LP03_LANE_ROWS_ORIGINAL_TRANSACTION")
        records = operation.records
        rows = []
        def retain(table, values, original):
            rows.append((table, (*values, deterministic_json(original)), original))
        claim = records.idempotency_claim
        retain("idempotency_claims", (claim.claim_id, None, claim.idempotency_key, claim.canonical_request_json,
                                     None, claim.created_at.isoformat()), claim)
        for record in records.receipt_records:
            retain("receipt_records", (record.record_id, record.effective_at.isoformat(), record.recorded_at.isoformat(), record.aggregate_id), record)
        for event in records.economic_events:
            retain("economic_events", (event.economic_event_id, event.aggregate_id, event.event_sequence,
                                        event.effective_at.isoformat(), event.recorded_at.isoformat()), event)
        journal = records.journal_transaction
        retain("journal_transactions", (journal.journal_transaction_id, journal.effective_at.isoformat(), journal.recorded_at.isoformat()), journal)
        for posting in records.journal_postings:
            retain("journal_postings", (posting.posting_id, posting.journal_transaction_id,
                                        posting.effective_at.isoformat(), posting.recorded_at.isoformat()), posting)
        transition = records.state_transition
        retain("state_transitions", (transition.transition_id, transition.aggregate_id, transition.aggregate_version_after,
                                      transition.effective_at.isoformat(), transition.recorded_at.isoformat()), transition)
        binding = dict(binding_id=claim.claim_id + "::RESULT", claim_ref=claim.claim_id,
                       result_record_ref=records.result_record_ref, created_at=claim.created_at)
        retain("idempotency_claims", (binding["binding_id"], claim.claim_id, None, None, records.result_record_ref,
                                     claim.created_at.isoformat()), binding)
        operation.rows = tuple(rows)
        operation.row_original = (operation.rows, deterministic_json(operation.rows))
        exact_ids = tuple(row[0] for _table, row, _record in operation.rows)
        edge = operation.attempt.payload.component_closure == ("MATH-01","MATH-02")
        if edge:
            from .models import EvidenceDependencyExecutionRecordV1, EvidenceValueProjectionRecordV1, EvidenceEventSegmentRecordV1
            from .receipts import DurableComputationExecutionReceiptRecordV1, LP03EvidenceControlReceiptRecordV1
            spines = records.receipt_records
            _native_require(len(spines) == 5 and spines[0].typed_payload is operation.raw
                and type(spines[0].typed_payload) is DurableComputationExecutionReceiptRecordV1
                and type(spines[3].typed_payload) is DurableComputationExecutionReceiptRecordV1
                and all(type(spines[index].typed_payload) is LP03EvidenceControlReceiptRecordV1 for index in (1,2,4))
                and tuple(type(spines[index].typed_payload.record) for index in (1,2,4))
                    == (EvidenceValueProjectionRecordV1,EvidenceEventSegmentRecordV1,EvidenceDependencyExecutionRecordV1)
                and spines[0].typed_payload.existing_receipt.specification_id == "MATH-02"
                and spines[3].typed_payload.existing_receipt.specification_id == "MATH-01"
                and spines[4].typed_payload.record.producer_raw_receipt_ref == spines[3].record_id
                and spines[4].typed_payload.record.consumer_raw_receipt_ref == spines[0].record_id
                and spines[4].record_id == operation.attempt.grant_record.record_id + "::CONVERSION"
                and spines[4].typed_payload.record.publication_ref is operation.publication_ref
                and tuple(spines[index].record_id for index in (3,4))
                    == spines[2].typed_payload.record.aggregate_refs[-2:],
                "LP03_LANE_EXACT_EDGE_ATOMIC_ROSTER")
        selected = operation.heldout_score_records
        if selected is not None:
            from .models import (EvidenceEventSegmentRecordV1, EvidenceHeldOutCpcvPathScoreRecordV1,
                                 EvidenceHeldOutFoldScoreRecordV1, EvidenceValueProjectionRecordV1)
            from .receipts import DurableComputationExecutionReceiptRecordV1, LP03EvidenceControlReceiptRecordV1

            originals, folds, paths = selected
            spines = records.receipt_records
            scorer_count, path_count = len(folds), len(paths)
            supplemental = (*originals, *folds, *paths)
            _native_require(operation.exchange[1].math_id in ("MATH-20", "MATH-21")
                and 2 <= len(originals) == scorer_count <= 6 and 0 <= path_count <= 3
                and len(spines) == 3 + len(supplemental)
                and spines[0].typed_payload is operation.raw
                and type(spines[1].typed_payload) is type(spines[2].typed_payload) is LP03EvidenceControlReceiptRecordV1
                and type(spines[1].typed_payload.record) is EvidenceValueProjectionRecordV1
                and type(spines[2].typed_payload.record) is EvidenceEventSegmentRecordV1
                and all(type(row) is DurableComputationExecutionReceiptRecordV1 for row in originals)
                and all(type(row) is EvidenceHeldOutFoldScoreRecordV1 for row in folds)
                and all(type(row) is EvidenceHeldOutCpcvPathScoreRecordV1 for row in paths),
                "LP03_LANE_EXACT_HELD_OUT_ATOMIC_ROSTER")
            _native_require(all(spine.typed_payload is raw for spine, raw in
                    zip(spines[3:3+scorer_count], originals, strict=True))
                and all(type(spine.typed_payload) is LP03EvidenceControlReceiptRecordV1
                    and spine.typed_payload.record is row for spine, row in
                    zip(spines[3+scorer_count:], (*folds,*paths), strict=True))
                and tuple(row.record_id for row in supplemental) == spines[2].typed_payload.record.aggregate_refs[4:]
                and tuple(row.record_id for row in (*folds,*paths)) == spines[1].typed_payload.record.supplementary_measurement_refs
                and all(fold.scorer_raw_receipt_ref == raw.record_id for fold,raw in zip(folds,originals,strict=True)),
                "LP03_LANE_EXACT_HELD_OUT_ATOMIC_ASSOCIATION")
        recorded_dr = operation.recorded_dr_records
        if recorded_dr is not None:
            from .models import (EvidenceEventSegmentRecordV1, EvidenceRecordedDrGroupMeasurementRecordV1,
                                 EvidenceRecordedDrUncertaintyRecordV1, EvidenceValueProjectionRecordV1)
            from .receipts import LP03EvidenceControlReceiptRecordV1

            spines = records.receipt_records
            uncertainty = recorded_dr[-1]
            _native_require(1 <= len(recorded_dr) <= 2 and operation.exchange[1].math_id == "MATH-22"
                and type(uncertainty) is EvidenceRecordedDrUncertaintyRecordV1
                and uncertainty.original_estimator_ref == operation.raw.record_id
                and (len(recorded_dr) == 2) == (uncertainty.availability_disposition == "ORIGINAL_CONDITIONAL_RECORDED_SCORE_INTERVAL")
                and len(spines) == 3 + len(recorded_dr) and spines[0].typed_payload is operation.raw
                and all(type(spine.typed_payload) is LP03EvidenceControlReceiptRecordV1 for spine in spines[1:])
                and type(spines[1].typed_payload.record) is EvidenceValueProjectionRecordV1
                and type(spines[2].typed_payload.record) is EvidenceEventSegmentRecordV1
                and all(spine.typed_payload.record is row for spine,row in zip(spines[3:],recorded_dr,strict=True)),
                "LP03_LANE_EXACT_DR_UNCERTAINTY_ATOMIC_ROSTER")
            refs = tuple(row.record_id for row in recorded_dr)
            _native_require(refs == spines[1].typed_payload.record.supplementary_measurement_refs
                == spines[2].typed_payload.record.aggregate_refs[4:]
                and (len(recorded_dr)==1 or (type(recorded_dr[0]) is EvidenceRecordedDrGroupMeasurementRecordV1
                    and recorded_dr[0].record_id == uncertainty.group_measurement_ref)),
                "LP03_LANE_EXACT_DR_UNCERTAINTY_ASSOCIATION")
        conversion = operation.analytic_conversion_record
        analytic = operation.exchange[1].math_id in ("MATH-29", "MATH-30", "MATH-31", "MATH-37")
        _native_require(analytic == (conversion is not None), "LP03_LANE_ANALYTIC_ATOMIC_VARIANT")
        if analytic:
            from .models import (EvidenceAbsenceV1, EvidenceAnalyticBinary64ConversionRecordV1,
                                 EvidenceEventSegmentRecordV1, EvidenceValueProjectionRecordV1)
            from .receipts import LP03EvidenceControlReceiptRecordV1
            from .serialization import _native_strict_json

            spines = records.receipt_records
            _native_require(type(conversion) is EvidenceAnalyticBinary64ConversionRecordV1
                and len(spines) == 4 and spines[0].typed_payload is operation.raw
                and all(type(spine.typed_payload) is LP03EvidenceControlReceiptRecordV1 for spine in spines[1:])
                and type(spines[1].typed_payload.record) is EvidenceValueProjectionRecordV1
                and type(spines[2].typed_payload.record) is EvidenceEventSegmentRecordV1
                and spines[3].typed_payload.record is conversion, "LP03_LANE_ANALYTIC_ATOMIC_ROSTER")
            projection = spines[1].typed_payload.record
            segment = spines[2].typed_payload.record
            encoded = conversion.certificate_json_or_absence
            expected = (_native_strict_json(encoded.encode("utf-8"), max_bytes=65536, max_nodes=128,
                binary64_numbers=True)["analytic_value"] if type(encoded) is str else EvidenceAbsenceV1("NUMERICAL_CONVERSION_UNAVAILABLE"))
            _native_require(projection.original_raw_receipt_ref == conversion.original_raw_receipt_ref == operation.raw.record_id
                and projection.numerical_conversion_ref_or_absence == conversion.record_id
                and segment.aggregate_refs[4:] == (conversion.record_id,)
                and deterministic_json(projection.projected_value) == deterministic_json(expected),
                "LP03_LANE_ANALYTIC_ATOMIC_SOURCE_AND_CONVERSION_JOIN")
        quantum_trace = operation.exchange[1].math_id in ("MATH-50", "MATH-51")
        if quantum_trace:
            from .models import EvidenceEventSegmentRecordV1, EvidenceValueProjectionRecordV1
            from .receipts import ST12FEvidenceControlReceiptRecordV1, ST12FReceiptClassV1

            spines = records.receipt_records
            _native_require(len(spines) == 4 and spines[0].typed_payload is operation.raw,
                "LP03_QUANTUM_TRACE_ATOMIC_ROSTER")
            projection, segment = (spine.typed_payload.record for spine in spines[1:3])
            trace = spines[3].typed_payload
            _native_require(type(trace) is ST12FEvidenceControlReceiptRecordV1
                and trace.receipt_class is ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION
                and type(projection) is EvidenceValueProjectionRecordV1 and type(segment) is EvidenceEventSegmentRecordV1
                and trace.canonical_contract_json == operation.exchange[2]["quantum_constructor_receipt_json"]
                == deterministic_json(projection.projected_value)
                and (spines[3].record_id,) == projection.supplementary_measurement_refs == segment.aggregate_refs[4:],
                "LP03_QUANTUM_TRACE_ATOMIC_EXACT_ASSOCIATION")
        expected_count = 10 + len(supplemental) if selected is not None else 12 if edge else 10 + int(analytic) + int(quantum_trace)
        if recorded_dr is not None:
            expected_count += len(recorded_dr)
        _native_require(len(exact_ids) == len(set(exact_ids)) and len(exact_ids) == expected_count,
                        "LP03_LANE_EXACT_ATOMIC_ROSTER")
        _EvidenceLaneOperationV1._room_v1(operation, control_writes=len(exact_ids) + 2,
                       control_bytes=sum(len(row[-1].encode("utf-8")) for _table, row, _record in operation.rows))
        return exact_ids

    def _evidence_commit_lane_v1(self, operation):
        """One existing lane connection and one atomic UOW; no cross-file commit."""
        from .persistence import _EvidenceLaneOperationV1, _EvidenceRegistrationOperationV1
        from .transaction import TrancheCUnitOfWorkV1
        from .latency_policy import _EvidenceLocalClockV1
        owner = _EvidenceLaneOperationV1
        _native_require(type(operation) is owner and operation.platform._store is self
                        and type(operation.unit) is TrancheCUnitOfWorkV1 and operation.unit._adapter is self
                        and operation.phase == "RESERVED", "LP03_LANE_ORIGINAL_UNIT_OF_WORK")
        owner._check_current_v1(operation)
        connection = self._connection
        sqlite3.Connection.set_trace_callback(connection, None)
        sqlite3.Connection.set_authorizer(connection, None)
        sqlite3.Connection.set_progress_handler(connection, None, 0)
        owner._check_current_v1(operation)
        _native_require(not sqlite3.Connection.in_transaction.__get__(connection), "LP03_LANE_TRANSACTION_REENTRY")

        def effect(sql, parameters=(), byte_count=0):
            owner._room_v1(operation, control_writes=1, control_bytes=byte_count)
            owner._check_current_v1(operation)
            owner._charge_v1(operation, control_writes=1, control_bytes=byte_count)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            sqlite3.Cursor.close(cursor)

        def query(sql, parameters, bound, byte_bound):
            owner._room_v1(operation, owner_queries=1, record_reads=bound, query_result_records=bound, read_bytes=byte_bound)
            owner._check_current_v1(operation)
            owner._charge_v1(operation, owner_queries=1)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            try:
                actual = sqlite3.Cursor.fetchmany(cursor, bound + 1)
            finally:
                sqlite3.Cursor.close(cursor)
            owner._charge_v1(operation, record_reads=len(actual), query_result_records=len(actual),
                read_bytes=sum(len(deterministic_json(value).encode("utf-8")) for row in actual for value in row))
            _native_require(len(actual) <= bound, "LP03_LANE_QUERY_BOUND")
            return actual

        try:
            effect("BEGIN IMMEDIATE")
            operation.phase = "TRANSACTION_OPEN"
            operation.transaction_observation = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
            operation.transaction_original = (operation.unit, connection, operation.transaction_observation, operation.phase)
            owner._prepare_records_v1(operation)
            TrancheCUnitOfWorkV1._validate_evidence_records_v1(operation.unit, operation)
            exact_ids = SQLiteReferenceAdapterV1._evidence_prepare_lane_rows_v1(self, operation)
            claim = operation.records.idempotency_claim
            operation.phase = "TRANSACTION_OPEN"
            # The original current grant/fence is checked again under this
            # transaction before collision reads and each persistent effect.
            _native_require(not query("SELECT 1 FROM idempotency_claims WHERE idempotency_key=?",
                (claim.idempotency_key,), 1, 1), "LP03_LANE_ALREADY_COMMITTED_OR_UNRESOLVED")
            placeholders = ",".join("?" for _ in exact_ids)
            bound = sum(len(deterministic_json(ref).encode("utf-8")) for ref in exact_ids)
            for table, column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items():
                _native_require(not query("SELECT " + column + " FROM " + table + " WHERE " + column + " IN (" + placeholders + ")",
                    exact_ids, len(exact_ids), bound), "LP03_LANE_CROSS_TABLE_IDENTITY_CONFLICT")
            for table, row, _record in operation.rows:
                _native_require(len(row) == len(REFERENCE_SCHEMA_COLUMNS_V1[table]), "LP03_LANE_SCHEMA_COLUMN_JOIN")
                effect("INSERT INTO " + table + " VALUES(" + ",".join("?" for _ in row) + ")", row,
                       len(row[-1].encode("utf-8")))
            operation.phase = "COMMIT_ATTEMPTED"
            effect("COMMIT")
            operation.phase = "COMMITTED_PENDING_READBACK"
            operation.commit_observation = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
            operation.data_observations_original = (operation.commit_observation, None, operation.unit, operation.row_original)
        except BaseException:
            if sqlite3.Connection.in_transaction.__get__(connection):
                try:
                    operation.attempt.registration.consumed["control_writes"] += 1
                    cursor = sqlite3.Connection.execute(connection, "ROLLBACK")
                    sqlite3.Cursor.close(cursor)
                    operation.phase = "ROLLED_BACK"
                except BaseException:
                    operation.phase = "ROLLBACK_UNPROVEN"
                    self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            elif operation.phase in ("COMMIT_ATTEMPTED", "COMMITTED_PENDING_READBACK"):
                operation.phase = "COMMIT_OR_OBSERVATION_UNRESOLVED"
            _EvidenceRegistrationOperationV1._observe_accounting_v1(operation.attempt.registration)
            raise
        SQLiteReferenceAdapterV1._evidence_read_lane_batch_v1(self, operation)
        operation.phase = "COMMITTED_AND_READBACK"

    def _evidence_read_lane_batch_v1(self, operation, *, publication=False):
        from .persistence import _EvidenceLaneOperationV1, _EvidenceBoundStoreV1, _evidence_lane_member_from_storage_v1
        owner = _EvidenceLaneOperationV1
        _native_require(type(operation) is owner and operation.platform._store is self
                        and operation.phase in ("COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK")
                        and operation.commit_observation is not None and operation.row_original is not None,
                        "LP03_LANE_READBACK_SCOPE")
        _native_require(type(publication) is bool and (not publication or (
            operation.publication_phase in ("COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK")
            and operation.publication_commit_observation is not None)), "LP03_PUBLICATION_READBACK_SCOPE")
        owner._check_current_v1(operation)
        rows = (("receipt_records", operation.publication[2], operation.publication[1]), *operation.rows) if publication else operation.rows
        reader = _EvidenceBoundStoreV1._open_independent_readback_v1(self._evidence_store_binding_v1,
                                                                   operation.platform._host, self, operation)
        try:
            for table, row, original in rows:
                expected = row[-1].encode("utf-8")
                columns = REFERENCE_SCHEMA_COLUMNS_V1[table]
                owner._room_v1(operation, owner_queries=1, record_reads=1, query_result_records=1, read_bytes=len(expected) + 21)
                owner._check_current_v1(operation)
                owner._charge_v1(operation, owner_queries=1)
                cursor = sqlite3.Connection.execute(reader,
                    "SELECT length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) FROM " + table
                    + " WHERE " + " AND ".join(column + " IS ?" for column in columns[:-1]),
                    (len(expected) + 1, *row[:-1]))
                try:
                    actual = sqlite3.Cursor.fetchmany(cursor, 2)
                finally:
                    sqlite3.Cursor.close(cursor)
                owner._charge_v1(operation, record_reads=len(actual), query_result_records=len(actual),
                    read_bytes=sum(len(item[1]) + len(str(item[0])) for item in actual))
                _native_require(len(actual) == 1 and actual[0] == (len(expected), expected), "LP03_LANE_EXACT_READBACK_MISMATCH")
                _evidence_lane_member_from_storage_v1(expected, original)
        finally:
            sqlite3.Connection.close(reader)
        observed = owner._check_current_v1(operation)
        if publication:
            operation.publication_readback_observation = (*observed, tuple(operation.attempt.registration.consumed.items()))
            operation.publication_readback_original = (operation.publication_readback_observation, operation.publication_original, operation.row_original)
        else:
            _native_require(operation.readback_observation is None, "LP03_DATA_FIRST_READBACK_ALREADY_RETAINED")
            operation.readback_observation = (*observed, tuple(operation.attempt.registration.consumed.items()))
            operation.data_observations_original = (operation.commit_observation, operation.readback_observation, operation.unit, operation.row_original)

    def _evidence_append_lane_publication_v1(self, operation):
        from .persistence import _EvidenceLaneOperationV1, _EvidenceRegistrationOperationV1
        from .latency_policy import _EvidenceLocalClockV1
        owner = _EvidenceLaneOperationV1
        _native_require(type(operation) is owner and operation.platform._store is self
                        and operation.publication_phase == "NOT_STARTED", "LP03_PUBLICATION_ORIGINAL_APPEND")
        owner._prepare_publication_v1(operation)
        connection = self._connection
        sqlite3.Connection.set_trace_callback(connection, None)
        sqlite3.Connection.set_authorizer(connection, None)
        sqlite3.Connection.set_progress_handler(connection, None, 0)
        owner._check_current_v1(operation)
        _native_require(not sqlite3.Connection.in_transaction.__get__(connection), "LP03_PUBLICATION_TRANSACTION_REENTRY")
        row = operation.publication[2]
        owner._room_v1(operation, control_writes=3, control_bytes=len(row[-1].encode("utf-8")))

        def effect(sql, parameters=(), byte_count=0):
            owner._room_v1(operation, control_writes=1, control_bytes=byte_count)
            owner._require_publication_purpose_v1(operation, "EVIDENCE_LANE_REGISTRATION_V1", operation.attempt.handle, operation.issuer.clock)
            owner._check_current_v1(operation)
            owner._charge_v1(operation, control_writes=1, control_bytes=byte_count)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            sqlite3.Cursor.close(cursor)

        try:
            effect("BEGIN IMMEDIATE")
            operation.publication_phase = "TRANSACTION_OPEN"
            for table, column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items():
                owner._room_v1(operation, owner_queries=1, record_reads=1, query_result_records=1, read_bytes=1)
                owner._check_current_v1(operation)
                owner._charge_v1(operation, owner_queries=1)
                cursor = sqlite3.Connection.execute(connection, "SELECT 1 FROM " + table + " WHERE " + column + "=?", (row[0],))
                try:
                    actual = sqlite3.Cursor.fetchmany(cursor, 2)
                finally:
                    sqlite3.Cursor.close(cursor)
                owner._charge_v1(operation, record_reads=len(actual), query_result_records=len(actual), read_bytes=len(actual))
                _native_require(not actual, "LP03_PUBLICATION_ALREADY_PRESENT_OR_CONFLICT")
            effect("INSERT INTO receipt_records VALUES(?,?,?,?,?)", row, len(row[-1].encode("utf-8")))
            operation.publication_phase = "COMMIT_ATTEMPTED"
            effect("COMMIT")
            operation.publication_phase = "COMMITTED_PENDING_READBACK"
            operation.publication_commit_observation = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
            operation.publication_commit_original = (operation.publication_commit_observation, operation.publication_original, operation.row_original)
        except BaseException:
            if sqlite3.Connection.in_transaction.__get__(connection):
                try:
                    operation.attempt.registration.consumed["control_writes"] += 1
                    cursor = sqlite3.Connection.execute(connection, "ROLLBACK")
                    sqlite3.Cursor.close(cursor)
                    operation.publication_phase = "ROLLED_BACK"
                except BaseException:
                    operation.publication_phase = "ROLLBACK_UNPROVEN"
                    self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            elif operation.publication_phase in ("COMMIT_ATTEMPTED", "COMMITTED_PENDING_READBACK"):
                operation.publication_phase = "COMMIT_OR_OBSERVATION_UNRESOLVED"
            _EvidenceRegistrationOperationV1._observe_accounting_v1(operation.attempt.registration)
            raise

    def _evidence_read_publication_control_v1(self, operation):
        """Finite original CONTROL closure; no recursive availability acquisition."""
        from .persistence import _EvidenceLaneOperationV1, _EvidenceBoundStoreV1
        from .receipts import _lp03_spine_from_storage_v1
        from .cohort_compiler import _read_original_compilation_member_v1
        from .input_lock import _require_original_input_assembly_outcome_v1
        owner, registration = _EvidenceLaneOperationV1, operation.attempt.registration
        _native_require(type(operation) is owner and operation.issuer.control_store is self
                        and operation.dependency_original is not None, "LP03_PUBLICATION_CONTROL_OWNER")
        owner._check_current_v1(operation)
        reader = _EvidenceBoundStoreV1._open_independent_readback_v1(self._evidence_store_binding_v1,
            operation.issuer.host, self, registration)
        try:
            for table, row in operation.control_dependencies:
                expected = row[-1].encode("utf-8")
                columns = REFERENCE_SCHEMA_COLUMNS_V1[table]
                owner._room_v1(operation, owner_queries=1, record_reads=1, query_result_records=1, read_bytes=len(expected) + 21)
                owner._check_current_v1(operation)
                owner._charge_v1(operation, owner_queries=1)
                cursor = sqlite3.Connection.execute(reader,
                    "SELECT length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) FROM " + table
                    + " WHERE " + " AND ".join(column + " IS ?" for column in columns[:-1]), (len(expected) + 1, *row[:-1]))
                try:
                    actual = sqlite3.Cursor.fetchmany(cursor, 2)
                finally:
                    sqlite3.Cursor.close(cursor)
                owner._charge_v1(operation, record_reads=len(actual), query_result_records=len(actual),
                    read_bytes=sum(len(item[1]) + len(str(item[0])) for item in actual))
                _native_require(len(actual) == 1 and actual[0] == (len(expected), expected), "LP03_PUBLICATION_CONTROL_READBACK_MISMATCH")
                if table == "receipt_records":
                    if row[0] in tuple(member.record_id for member in registration.binding_spines):
                        _read_original_compilation_member_v1(expected, operation=registration, record_ref=row[0])
                    else:
                        _lp03_spine_from_storage_v1(expected, expected_record_id=row[0])
            _require_original_input_assembly_outcome_v1(registration.preparation, registration.preparation.input_assembly_outcome)
        finally:
            sqlite3.Connection.close(reader)
        owner._check_current_v1(operation)

    def _evidence_read_conformance_v1(self, operation, *, parents):
        from .persistence import (_EvidenceConformanceOperationV1, _EvidenceBoundStoreV1,
            _evidence_lane_member_from_storage_v1)
        from .receipts import _lp03_spine_from_storage_v1
        from .cohort_compiler import _read_original_compilation_member_v1
        from .serialization import _evidence_canonical_object_v1
        owner = _EvidenceConformanceOperationV1
        _native_require(type(operation) is owner and operation.issuer.control_store is self and type(parents) is bool,
                        "LP03_CONFORMANCE_ORIGINAL_READ_SCOPE")
        _native_require(operation.phase == "PARENTS_PENDING" if parents else operation.phase in (
            "COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK"), "LP03_CONFORMANCE_READ_PHASE")
        owner._assert_original_v1(operation, canonical=True)
        targets = operation.read_sets if parents else ((self, operation.issuer.host, operation.rows),)
        observations = []
        for target in targets:
            adapter, host, rows = target
            operation.read_target = target if parents else None
            reader = _EvidenceBoundStoreV1._open_independent_readback_v1(adapter._evidence_store_binding_v1, host, adapter, operation)
            try:
                for table, row, original in rows:
                    expected = row[-1].encode("utf-8")
                    columns = REFERENCE_SCHEMA_COLUMNS_V1[table]
                    owner._room_v1(operation, owner_queries=1, record_reads=1, query_result_records=1, read_bytes=len(expected) + 21)
                    owner._check_current_v1(operation)
                    owner._charge_v1(operation, owner_queries=1)
                    cursor = sqlite3.Connection.execute(reader,
                        "SELECT length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) FROM " + table
                        + " WHERE " + " AND ".join(column + " IS ?" for column in columns[:-1]), (len(expected) + 1, *row[:-1]))
                    try:
                        actual = sqlite3.Cursor.fetchmany(cursor, 2)
                    finally:
                        sqlite3.Cursor.close(cursor)
                    owner._charge_v1(operation, record_reads=len(actual), query_result_records=len(actual),
                        read_bytes=sum(len(item[1]) + len(str(item[0])) for item in actual))
                    _native_require(len(actual) == 1 and actual[0] == (len(expected), expected), "LP03_CONFORMANCE_EXACT_PARENT_READBACK_MISMATCH")
                    if original is not None:
                        _evidence_lane_member_from_storage_v1(expected, original)
                    elif table == "receipt_records":
                        if row[0] in tuple(member.record_id for member in operation.registration.binding_spines):
                            _read_original_compilation_member_v1(expected, operation=operation.registration, record_ref=row[0])
                        else:
                            _lp03_spine_from_storage_v1(expected, expected_record_id=row[0])
                    else:
                        _evidence_canonical_object_v1(expected, max_bytes=1048576)
            finally:
                sqlite3.Connection.close(reader)
                operation.read_target = None
            observed = owner._check_current_v1(operation)
            observations.append((adapter._evidence_store_binding_v1.binding.store_id,
                tuple((table, row[0]) for table, row, _ in rows), observed))
        owner._assert_original_v1(operation, canonical=True)
        observed = owner._check_current_v1(operation)
        if parents:
            operation.parent_readbacks = tuple(observations)
            operation.parent_original = (operation.parent_readbacks, operation.read_sets)
            operation.phase = "PARENTS_READBACK"
        elif operation.readback_observation is None:
            operation.readback_observation = (*observed, tuple(operation.registration.consumed.items()))
            operation.readback_original = (operation.readback_observation, operation.rows_original)
            operation.phase = "COMMITTED_AND_READBACK"

    def _evidence_read_review_v1(self, operation, *, stage):
        from .persistence import _EvidenceReviewOperationV1
        _native_require(type(operation) is _EvidenceReviewOperationV1, "LP03_REVIEW_ORIGINAL_READ_SCOPE")
        return SQLiteReferenceAdapterV1._evidence_read_measured_rows_v1(self, operation, stage=stage)

    def _evidence_commit_cold_revocation_v1(self, operation):
        """Append and independently verify the single new-generation archive reservation."""
        from .models import EvidenceMessageKindV1, EvidenceRevocationRecordV1
        from .persistence import _EvidenceBoundStoreV1, _EvidenceColdControlReadV1
        from .receipts import _lp03_spine_for_record_v1, _lp03_spine_from_storage_v1
        from .serialization import _evidence_canonical_object_v1
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1

        owner = _EvidenceColdControlReadV1
        _native_require(type(self) is SQLiteReferenceAdapterV1 and type(operation) is owner
            and operation.issuer.control_store is self and operation.phase == "ADMITTING"
            and type(operation.revocation) is EvidenceRevocationRecordV1
            and operation.revocation_commit is operation.revocation_readback is None,
            "LP03_COLD_CONTROL_ORIGINAL_ADMISSION_REQUIRED")
        owner._check_current_v1(operation)
        binding = self._evidence_store_binding_v1
        connection = self._connection
        _native_require(not sqlite3.Connection.in_transaction.__get__(connection) and self._active_transaction is None,
            "LP03_COLD_CONTROL_TRANSACTION_CONFLICT")
        sqlite3.Connection.set_trace_callback(connection, None)
        sqlite3.Connection.set_authorizer(connection, None)
        sqlite3.Connection.set_progress_handler(connection, None, 0)
        record = operation.revocation
        config = operation.issuer.host.public_configuration
        trace = EvidenceHostBindingV1._nonce_ref_v1(operation.issuer.host, "LP03-TRACE")
        spine = _lp03_spine_for_record_v1(record, sequence=record.new_generation, trace_ref=trace)
        stored = deterministic_json(spine).encode("utf-8")
        _native_require(len(stored) <= 16384, "LP03_COLD_CONTROL_REVOCATION_WIRE_BOUND")
        wall = spine.recorded_at.isoformat()
        original_envelope = operation.original_envelope
        key = operation.record_ref
        claim_ref = key+"::CLAIM"
        reserve_body = deterministic_json(dict(
            original_owner_ref=original_envelope.envelope_ref, current_owner_ref=operation.current_owner[0],
            deployment_id=config.deployment_id, control_store_id=binding.binding.store_id,
            target_generation=record.target_generation, new_generation=record.new_generation,
            current_process_identity_ref=operation.clock.process_identity_ref,
            current_clock_domain_id=operation.clock.clock_domain_id, current_boot_identity_ref=operation.clock.boot_identity_ref,
            reserved_preparation_limits=operation.limits))
        claim = IdempotencyClaimReceiptV1(claim_ref, key, "LP03_COLD_REVOCATION", reserve_body,
            IdempotencyClaimStateV1.ACQUIRED, None, spine.recorded_at, None, None)
        result_key = claim_ref+"::RESULT"
        result = deterministic_json(dict(binding_id=result_key, claim_ref=claim_ref, result_record_ref=record.record_id,
            created_at=spine.recorded_at))
        claim_rows = ((claim_ref, None, key, reserve_body, None, wall, deterministic_json(claim)),
            (result_key, claim_ref, None, None, record.record_id, wall, result))
        _native_require(sum(len(deterministic_json(row).encode("utf-8")) for row in claim_rows) <= 16384,
            "LP03_COLD_CONTROL_RESERVATION_WIRE_BOUND")

        def read(reader, query, args, *, maximum_bytes):
            owner._check_current_v1(operation)
            owner._room_v1(operation, owner_queries=1, record_reads=2, query_result_records=2, read_bytes=maximum_bytes)
            owner._charge_v1(operation, owner_queries=1)
            cursor = sqlite3.Connection.execute(reader, query, args)
            try:
                rows = sqlite3.Cursor.fetchmany(cursor, 2)
            finally:
                sqlite3.Cursor.close(cursor)
            owner._charge_v1(operation, record_reads=len(rows), query_result_records=len(rows),
                read_bytes=sum(len(value) if type(value) is bytes else len(deterministic_json(value).encode("utf-8"))
                    for row in rows for value in row))
            _native_require(len(rows) <= 1, "LP03_COLD_CONTROL_ORIGINAL_ADMISSION_CONFLICT")
            owner._check_current_v1(operation)
            return rows[0] if rows else None

        def effect(query, args=(), *, written_bytes=0):
            owner._check_current_v1(operation)
            owner._room_v1(operation, control_writes=1, control_bytes=written_bytes)
            owner._charge_v1(operation, control_writes=1, control_bytes=written_bytes)
            cursor = sqlite3.Connection.execute(connection, query, args)
            sqlite3.Cursor.close(cursor)

        attempted_commit = False
        root_ref = "LP03-CONTROL-LIFECYCLE:ROOT"
        try:
            effect("BEGIN IMMEDIATE")
            root = read(connection, "SELECT idempotency_key,length(CAST(canonical_request_json AS BLOB)),"
                "substr(CAST(canonical_request_json AS BLOB),1,16385) FROM idempotency_claims WHERE claim_record_id=?",
                (root_ref,), maximum_bytes=34000)
            _native_require(root is not None and root[0] == root_ref and type(root[1]) is int
                and type(root[2]) is bytes and 0 < root[1] == len(root[2]) <= 16384,
                "LP03_COLD_CONTROL_ORIGINAL_LIFECYCLE_REQUIRED")
            body = _evidence_canonical_object_v1(root[2], max_bytes=16384)
            _native_require(body["operation"] == "LP03_CONTROL_LIFECYCLE_V1"
                and (body["deployment_id"], body["control_store_id"], body["origin"], body["native_host_identity"],
                    body["issuer_principal"], body["generation"]) == (config.deployment_id, binding.binding.store_id,
                    config.origin.value, config.host_identity, config.service_principal, record.target_generation)
                and body["first_deadline_historical"]["process_identity_ref"] != operation.clock.process_identity_ref,
                "LP03_COLD_CONTROL_ORIGINAL_LIFECYCLE_GENERATION")
            root_result = read(connection, "SELECT parent_claim_id,result_record_ref FROM idempotency_claims "
                "WHERE claim_record_id=?", (root_ref+"::RESULT",), maximum_bytes=1024)
            _native_require(root_result == (root_ref,body["first_grant_ref"]), "LP03_COLD_CONTROL_ORIGINAL_LIFECYCLE_RESULT")
            for ref in (claim_ref, result_key):
                duplicate = read(connection, "SELECT 1 FROM idempotency_claims WHERE claim_record_id=?", (ref,), maximum_bytes=2)
                if duplicate is not None:
                    raise ContractValidationError(ReasonCode.EVIDENCE_RUN_UNRESOLVED, "LP03_COLD_CONTROL_ARCHIVE_ALREADY_RESERVED")
            for table,column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items():
                known = read(connection, "SELECT 1 FROM "+table+" WHERE "+column+"=?", (record.record_id,), maximum_bytes=2)
                _native_require(known is None, "LP03_COLD_CONTROL_REVOCATION_IDENTITY_CONFLICT")
            _, payload = EvidenceHostBindingV1._verify_message_v1(operation.issuer.host, record.issuer_signature,
                expected_kind=EvidenceMessageKindV1.REVOCATION, expected_issuer=config.service_principal,
                expected_subject=record.record_id, expected_audience="CP/sqlite_reference.py::recover_evidence_control_lifecycle_v1",
                expected_generation=config.generation)
            _native_require(payload == operation.recovery_authorization, "LP03_COLD_CONTROL_REVOCATION_SIGNATURE_JOIN")
            effect("INSERT INTO receipt_records VALUES(?,?,?,?,?)", (record.record_id, wall, wall, spine.aggregate_id,
                stored.decode("utf-8")), written_bytes=len(stored))
            for row in claim_rows:
                effect("INSERT INTO idempotency_claims VALUES(?,?,?,?,?,?,?)", row,
                    written_bytes=len(deterministic_json(row).encode("utf-8")))
            owner._room_v1(operation, control_writes=1)
            owner._charge_v1(operation, control_writes=1)
            owner._check_current_v1(operation)
            attempted_commit = True
            sqlite3.Connection.commit(connection)
            operation.revocation_commit = owner._check_current_v1(operation)
        except BaseException:
            if sqlite3.Connection.in_transaction.__get__(connection):
                sqlite3.Connection.rollback(connection)
            operation.phase = "COMMIT_UNPROVEN" if attempted_commit else "ADMISSION_DENIED"
            raise
        reader = _EvidenceBoundStoreV1._open_independent_readback_v1(binding, operation.issuer.host, self, operation)
        try:
            found = read(reader, "SELECT effective_at,recorded_at,aggregate_id,length(CAST(payload_json AS BLOB)),"
                "substr(CAST(payload_json AS BLOB),1,16385) FROM receipt_records WHERE record_id=?", (key,), maximum_bytes=34000)
            _native_require(found == (wall,wall,spine.aggregate_id,len(stored),stored)
                and _lp03_spine_from_storage_v1(found[-1], expected_record_id=key).typed_payload.record == record,
                "LP03_COLD_CONTROL_REVOCATION_READBACK")
            for row in claim_rows:
                exact = read(reader, "SELECT 1 FROM idempotency_claims WHERE claim_record_id=? AND parent_claim_id IS ? "
                    "AND idempotency_key IS ? AND canonical_request_json IS ? AND result_record_ref IS ? AND created_at=? AND payload_json=?",
                    row, maximum_bytes=2)
                _native_require(exact == (1,), "LP03_COLD_CONTROL_RESERVATION_READBACK")
            operation.revocation_readback = owner._check_current_v1(operation)
        finally:
            sqlite3.Connection.close(reader)

    def _evidence_read_cold_control_roster_v1(self, operation):
        """Resolve the selected historical control records without restoring a grant."""
        from .models import (
            EvidenceAssemblyGrantRecordV1, EvidenceAttemptGrantRecordV1, EvidenceAttemptStateRecordV1,
            EvidenceAssemblyStateRecordV1, EvidenceExecutionConsumptionV1, EvidenceExperimentRecordV1, EvidenceInputAssemblyRecordV1,
            EvidenceLaneRegistrationRecordV1, EvidencePipelineConformanceV1, EvidenceRecordRefV1, EvidenceScenarioPlanV1,
        )
        from .persistence import _EvidenceBoundStoreV1, _EvidenceColdControlReadV1
        from .latency_policy import _evidence_storage_observation_v1
        from .receipts import _lp03_spine_from_storage_v1
        from .serialization import _evidence_canonical_object_v1, deterministic_json

        owner = _EvidenceColdControlReadV1
        _native_require(type(self) is SQLiteReferenceAdapterV1 and type(operation) is owner
                        and operation.issuer.control_store is self, "LP03_COLD_CONTROL_ORIGINAL_STORE_REQUIRED")
        owner._check_current_v1(operation)
        binding = self._evidence_store_binding_v1
        reader = _EvidenceBoundStoreV1._open_independent_readback_v1(binding, operation.issuer.host, self, operation)
        body_cap = 1_048_576

        def query(sql, arguments):
            owner._check_current_v1(operation)
            owner._room_v1(operation, owner_queries=1, record_reads=1, query_result_records=1, read_bytes=2*body_cap+1024)
            owner._charge_v1(operation, owner_queries=1)
            cursor = sqlite3.Connection.execute(reader, sql, arguments)
            try:
                rows = sqlite3.Cursor.fetchmany(cursor, 2)
            finally:
                sqlite3.Cursor.close(cursor)
            owner._charge_v1(operation, record_reads=len(rows), query_result_records=len(rows),
                read_bytes=sum(len(item) if type(item) is bytes else len(deterministic_json(item).encode("utf-8"))
                               for row in rows for item in row))
            _native_require(len(rows) <= 1, "LP03_COLD_CONTROL_EXACT_ROW_CONFLICT")
            owner._check_current_v1(operation)
            return rows[0] if rows else None

        def claim(ref, *, by_unique_key=False):
            # Both selectors are fixed native SQLite indexes. A payload or request
            # never becomes an SQL identifier or search predicate.
            key = "idempotency_key" if by_unique_key else "claim_record_id"
            row = query("SELECT claim_record_id,parent_claim_id,idempotency_key,result_record_ref,created_at,"
                        "length(CAST(canonical_request_json AS BLOB)),substr(CAST(canonical_request_json AS BLOB),1,?),"
                        "length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) "
                        "FROM idempotency_claims WHERE " + key + "=?", (body_cap+1, body_cap+1, ref))
            if row is None:
                return None
            row_ref,parent,unique,result,created,request_bytes,request_raw,size,raw = row
            _native_require(type(size) is int and type(raw) is bytes and 0 < size == len(raw) <= body_cap,
                            "LP03_COLD_CONTROL_EXACT_ROW_BOUND")
            _native_require((unique if by_unique_key else row_ref)==ref, "LP03_COLD_CONTROL_EXACT_ROW_CONFLICT")
            body=_evidence_canonical_object_v1(raw,max_bytes=body_cap)
            if parent is None:
                _native_require(type(request_bytes) is int and type(request_raw) is bytes
                                and 0 < request_bytes == len(request_raw) <= body_cap
                                and body["claim_id"] == row_ref and body["idempotency_key"] == unique
                                and body["created_at"] == created and body["result_record_ref"] == result
                                and body["canonical_request_json"].encode("utf-8","strict")==request_raw,
                                "LP03_COLD_CONTROL_ORIGINAL_CLAIM_METADATA")
            else:
                _native_require(request_bytes is request_raw is None, "LP03_COLD_CONTROL_RESULT_REQUEST_UNEXPECTED")
            owner._retain_v1(operation, ("idempotency_claims",row_ref,raw))
            return row_ref,parent,unique,result,created,body

        def result_for(authority_claim, expected_ref=None):
            _native_require(authority_claim is not None and authority_claim[1] is authority_claim[3] is None,
                            "LP03_COLD_CONTROL_AUTHORITY_CLAIM_REQUIRED")
            root=authority_claim[0]
            row=claim(root+"::RESULT")
            _native_require(row is not None and row[0]==root+"::RESULT" and row[1]==root
                            and row[2] is None and (expected_ref is None or row[3] == expected_ref)
                            and row[5]["binding_id"] == row[0] and row[5]["claim_ref"] == root
                            and row[5]["result_record_ref"] == row[3] and row[5]["created_at"] == row[4],
                            "LP03_COLD_CONTROL_RESULT_BINDING_REQUIRED")
            return row[3]


        def record(ref, model, *, required=True):
            row = query("SELECT record_id,effective_at,recorded_at,aggregate_id,"
                        "length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) "
                        "FROM receipt_records WHERE record_id=?", (body_cap+1, ref))
            if row is None and not required:
                return None
            _native_require(row is not None and row[0] == ref and type(row[4]) is int
                            and type(row[5]) is bytes and 0 < row[4] == len(row[5]) <= body_cap,
                            "LP03_COLD_CONTROL_EXACT_RECORD_REQUIRED")
            spine = _lp03_spine_from_storage_v1(row[5], expected_record_id=ref)
            body = spine.typed_payload.record
            _native_require(type(body) is model and (spine.effective_at.isoformat(),spine.recorded_at.isoformat(),spine.aggregate_id)
                            == row[1:4], "LP03_COLD_CONTROL_EXACT_RECORD_SCHEMA_JOIN")
            owner._retain_v1(operation, ("receipt_records",ref,row[5]))
            return spine,body

        def pair(ref, *, expected_ref=None):
            selected = claim(ref)
            if selected is None:
                _native_require(claim(ref+"::RESULT") is None, "LP03_COLD_CONTROL_ORPHAN_RESULT")
                return None
            return selected, result_for(selected, expected_ref)

        def process_prefix(attempt, chain, prior_running_ref):
            """Verify the original native observations in the old clock domain."""
            from .serialization import _evidence_process_observation_body_v1

            phases = ("SUSPENDED", "RUNNING", "TERMINAL")
            _native_require(len(chain) == len(phases) and chain[0] is not None,
                "LP03_COLD_CONTROL_ORIGINAL_PROCESS_PREFIX")
            seen_missing = False
            original_identity = None
            previous_clock = None
            observations = []
            for phase, entry in zip(phases, chain, strict=True):
                if entry is None:
                    seen_missing = True
                    continue
                _native_require(not seen_missing, "LP03_COLD_CONTROL_ORIGINAL_PROCESS_PREFIX")
                claim_row, result_ref = entry
                wire = claim_row[5]["canonical_request_json"]
                durable_state = prior_running_ref if phase in ("RUNNING", "TERMINAL") else attempt.record_id+"::STATE:0"
                _native_require(type(wire) is str and result_ref == durable_state
                    and claim_row[2] == claim_row[0] == attempt.record_id+"::PROCESS:"+phase
                    and claim_row[5]["identity_class"] == "LP03_SVC_PROCESS_OBSERVATION_APPEND",
                    "LP03_COLD_CONTROL_ORIGINAL_PROCESS_CLAIM")
                body = _evidence_process_observation_body_v1(wire.encode("utf-8"))
                parent_ref = prior_running_ref if phase == "TERMINAL" else attempt.record_id+"::STATE:0"
                clock = body["observed_at"]
                native = body["native_observation"]
                _native_require((body["observation_ref"], body["grant_ref"], body["fence_ref"], body["stage"],
                    body["clock_domain_id"], body["boot_identity_ref"], body["predecessor_state_ref"],
                    body["supervisor_instance_ref"]) ==
                    (claim_row[0], attempt.record_id, attempt.fence_ref, phase, attempt.deadline.clock_domain_id,
                     attempt.deadline.boot_identity_ref, parent_ref, lifecycle["supervisor_instance_ref"])
                    and attempt.deadline.admitted_monotonic_ns <= clock[1]
                    and (previous_clock is None or all(a <= b for a,b in zip(previous_clock,clock,strict=True))),
                    "LP03_COLD_CONTROL_ORIGINAL_PROCESS_SCOPE_AND_CLOCK")
                if original_identity is None:
                    original_identity = native["process_identity"]
                _native_require(native["process_identity"] == original_identity, "LP03_COLD_CONTROL_ORIGINAL_PROCESS_IDENTITY")
                observations.append(body)
                previous_clock = clock
            return tuple(observations)

        try:
            historical = operation.original_envelope
            configuration = operation.issuer.host.public_configuration
            origin = historical.assembly_scope.origin
            original_generation = operation.recovery_authorization.target_generation
            root_ref = "LP03-CONTROL-LIFECYCLE:ROOT"
            root = claim(root_ref)
            first_ref = result_for(root)
            _native_require(root[2]==root_ref and root[5]["identity_class"]=="LP03_CONTROL_LIFECYCLE",
                            "LP03_COLD_CONTROL_FIXED_ROOT_REQUIRED")
            lifecycle = _evidence_canonical_object_v1(root[5]["canonical_request_json"].encode("utf-8"), max_bytes=16384)
            _native_require(lifecycle["operation"]=="LP03_CONTROL_LIFECYCLE_V1"
                            and (lifecycle["deployment_id"],lifecycle["control_store_id"],lifecycle["origin"],
                                 lifecycle["native_host_identity"],lifecycle["issuer_principal"],lifecycle["generation"],
                                 lifecycle["first_grant_ref"]) ==
                            (historical.deployment_id,binding.binding.store_id,origin.value,configuration.host_identity,
                             historical.issuer_principal,original_generation,first_ref),
                            "LP03_COLD_CONTROL_FIXED_ROOT_SCOPE_JOIN")
            _first_spine, first = record(first_ref, EvidenceAssemblyGrantRecordV1)
            _native_require(first.generation==original_generation and first.origin is origin
                            and first.deadline_clock_and_process.process_identity_ref != operation.clock.process_identity_ref
                            and deterministic_json(first.deadline_clock_and_process)==deterministic_json(lifecycle["first_deadline_historical"]),
                            "LP03_COLD_CONTROL_FIXED_ROOT_ANCHOR")

            key = (historical.deployment_id,origin.value,historical.experiment_id,historical.experiment_revision)
            preparation_claim = claim("LP03-PREPARATION::"+deterministic_json(key), by_unique_key=True)
            grant_ref = result_for(preparation_claim)
            _grant_spine, grant = record(grant_ref, EvidenceAssemblyGrantRecordV1)
            _native_require(grant.preparation_natural_key==key and grant.owner_envelope_ref==historical.envelope_ref
                            and grant.generation==original_generation and grant.origin is origin
                            and grant.exact_frozen_plan_ref.store_id==binding.binding.store_id
                            and preparation_claim[5]["canonical_request_json"]==deterministic_json({"preparation_natural_key":key}),
                            "LP03_COLD_CONTROL_SELECTED_PREPARATION_SCOPE")
            _plan_spine, plan = record(grant.exact_frozen_plan_ref.record_id, EvidenceScenarioPlanV1)
            _native_require(grant.scenario_plan_ref==plan.record_id and plan.protocol_ref==historical.protocol_ref
                            and plan.origin is origin and plan.generation==original_generation,
                            "LP03_COLD_CONTROL_ORIGINAL_SCENARIO_PLAN_JOIN")
            owner._verify_historical_grant_v1(operation, grant)
            assembled = record(grant_ref+"::INPUT_ASSEMBLY", EvidenceInputAssemblyRecordV1, required=False)
            if assembled is None:
                return owner._finish_read_v1(operation, lifecycle, grant, (), "ORIGINAL_ASSEMBLY_UNPROVEN")
            assembly_spine, assembly = assembled
            _native_require(assembly_spine.sequence>1 and assembly.assembly_grant_ref==grant_ref
                            and assembly.preparation_ordinal==grant.preparation_ordinal and assembly.generation==original_generation
                            and assembly.origin is origin, "LP03_COLD_CONTROL_ORIGINAL_ASSEMBLY_JOIN")
            seal_ref=grant_ref+"::STATE:"+str(assembly_spine.sequence-1)
            _seal_spine, seal=record(seal_ref,EvidenceAssemblyStateRecordV1)
            _native_require(seal.state.value=="SEALED" and seal.assembly_grant_ref==grant_ref
                            and seal.input_assembly_ref_or_absence==assembly.record_id,
                            "LP03_COLD_CONTROL_ORIGINAL_SEAL_REQUIRED")
            registered_key="LP03-REGISTRATION::"+deterministic_json((historical.deployment_id,
                historical.experiment_id,historical.experiment_revision))
            registration_claim=claim(registered_key, by_unique_key=True)
            if registration_claim is None:
                return owner._finish_read_v1(operation, lifecycle, grant, (), "ORIGINAL_REGISTRATION_UNPROVEN")
            experiment_ref=result_for(registration_claim, assembly.record_id+"::EXPERIMENT:1")
            _,experiment=record(experiment_ref,EvidenceExperimentRecordV1)
            _native_require(experiment.input_assembly_ref==assembly.record_id and experiment.owner_envelope_ref==historical.envelope_ref
                            and experiment.generation==original_generation and experiment.origin is origin,
                            "LP03_COLD_CONTROL_ORIGINAL_REGISTRATION_JOIN")
            bound_key="LP03-IMMUTABLE-BINDING::"+deterministic_json((experiment.experiment_id,experiment.experiment_revision,
                                                                   experiment.input_assembly_ref))
            bound_claim=claim(bound_key,by_unique_key=True)
            if bound_claim is None:
                return owner._finish_read_v1(operation, lifecycle, grant, (), "ORIGINAL_BINDING_UNPROVEN")
            bound_ref=result_for(bound_claim, experiment_ref+"::BOUND:1")
            _,bound=record(bound_ref,EvidenceExperimentRecordV1)
            _native_require(bound.causation_ref==experiment_ref and type(bound.input_lock_ref) is str
                            and (bound.input_assembly_ref,bound.generation,bound.origin,bound.scenario_plan_ref) ==
                                (assembly.record_id,original_generation,origin,plan.record_id),
                            "LP03_COLD_CONTROL_ORIGINAL_BINDING_JOIN")

            lanes = []
            for lane_name in ("REPLAY", "PAPER"):
                ref=bound_ref+"::"+lane_name+":1::GRANT"
                original_attempt=record(ref,EvidenceAttemptGrantRecordV1,required=False)
                if original_attempt is None:
                    _native_require(pair(ref+"::REQUEST") is None and pair(ref+"::RESERVATION") is None,
                                    "LP03_COLD_CONTROL_ORPHAN_ATTEMPT_RESERVATION")
                    lanes.append((lane_name,"ORIGINAL_ATTEMPT_UNAVAILABLE"))
                    continue
                _,attempt=original_attempt
                _native_require(attempt.original_owner_envelope_ref==historical.envelope_ref and attempt.generation==original_generation
                                and attempt.origin is origin and attempt.input_lock_ref==bound.input_lock_ref
                                and attempt.lane.value==lane_name and attempt.attempt_ordinal==1,
                                "LP03_COLD_CONTROL_ORIGINAL_ATTEMPT_JOIN")
                owner._verify_historical_grant_v1(operation,attempt)
                _,initial=record(ref+"::STATE:0",EvidenceAttemptStateRecordV1)
                _native_require(initial.state.value=="ADMITTED" and initial.grant_ref==ref
                                and initial.input_lock_ref==bound.input_lock_ref and initial.origin is origin,
                                "LP03_COLD_CONTROL_ORIGINAL_ATTEMPT_INITIAL_STATE")
                request=pair(ref+"::REQUEST",expected_ref=ref)
                reservation=pair(ref+"::RESERVATION",expected_ref=ref)
                _native_require(request is not None and reservation is not None
                    and request[0][5]["identity_class"]==reservation[0][5]["identity_class"]=="LP03_POST_LOCK_ATTEMPT"
                    and request[0][5]["canonical_request_json"]==reservation[0][5]["canonical_request_json"],
                    "LP03_COLD_CONTROL_ORIGINAL_ATTEMPT_RESERVATION_REQUIRED")
                original_request=_evidence_canonical_object_v1(request[0][5]["canonical_request_json"].encode("utf-8"),
                    max_bytes=body_cap)
                _native_require(original_request["grant_ref"]==ref and original_request["accounting_state"]==
                    "RESERVED_WITH_ATTEMPT_TAIL_PENDING" and (original_request["request"]["lane"],original_request["request"]["attempt_ordinal"])
                    ==(lane_name,1) and original_request["request"]["registration_binding_ref"]==
                        {"store_id":binding.binding.store_id,"record_id":bound_ref}
                    and deterministic_json(original_request["reserved_limits"])==deterministic_json(attempt.budgets)
                    and deterministic_json(original_request["aggregate_limits"])==deterministic_json(historical.aggregate_execution_limits)
                    and deterministic_json(original_request["attempt_consumed_prefix"])==deterministic_json(initial.consumed_budget),
                    "LP03_COLD_CONTROL_ORIGINAL_ATTEMPT_RESERVED_LIMITS")
                process=(pair(ref+"::PROCESS:SUSPENDED"),pair(ref+"::PROCESS:RUNNING"),pair(ref+"::PROCESS:TERMINAL"))
                failure=pair(ref+"::PROCESS:FAILURE")
                finalization=pair(ref+"::FINALIZATION")
                observations=process_prefix(attempt,process,ref+"::STATE:1") if any(entry is not None for entry in process) else ()
                if len(observations)==3 and failure is None and finalization is not None:
                    _,running=record(ref+"::STATE:1",EvidenceAttemptStateRecordV1)
                    _,final=record(ref+"::STATE:2",EvidenceAttemptStateRecordV1)
                    _native_require(running.state.value=="RUNNING" and running.prior_state_ref==initial.record_id
                        and running.grant_ref==ref and final.prior_state_ref==running.record_id
                        and final.process_observation_ref_or_absence==observations[2]["observation_ref"]
                        and observations[2]["native_observation"]["exit_code"]==0 and observations[2]["exchange_complete"] is True
                        and final.consumed_budget.active_workers==0 and final.consumed_budget.attempts==1,
                        "LP03_COLD_CONTROL_ORIGINAL_TERMINAL_OBSERVATION")
                    _,registration=record(finalization[1],EvidenceLaneRegistrationRecordV1)
                    _native_require(final.state.value=="COLLECTION_COMPLETE" and final.grant_ref==ref
                        and registration.attempt_ref==ref and registration.lane.value==lane_name
                        and registration.terminal_receipt_ref==final.record_id,
                        "LP03_COLD_CONTROL_ORIGINAL_FINALIZATION_JOIN")
                    final_claim = finalization[0][5]
                    final_data = _evidence_canonical_object_v1(final_claim["canonical_request_json"].encode("utf-8"),
                        max_bytes=body_cap)
                    _native_require(set(final_data) == {"operation", "original_grant_ref", "original_reservation_ref",
                        "terminal_state_ref", "lane_registration_ref", "publication_ref", "publication_readback_observation",
                        "available_at", "exact_dependency_refs", "consumed_prefix", "cumulative_consumed_prefix",
                        "retained_full_original_reservation", "reservation_state", "tail_accounting_state", "native_observation"}
                        and final_claim["identity_class"] == "LP03_LANE_FINALIZATION"
                        and final_claim["idempotency_key"] == "LP03-LANE-FINALIZATION::"+ref
                        and final_data["operation"] == "LP03_ORIGINAL_LANE_FINALIZATION_V1"
                        and (final_data["original_grant_ref"],final_data["original_reservation_ref"],
                            final_data["terminal_state_ref"],final_data["lane_registration_ref"])
                            == (ref,ref+"::RESERVATION",final.record_id,registration.record_id)
                        and deterministic_json(final_data["publication_ref"]) == deterministic_json(registration.accepted_publication_ref)
                        and deterministic_json(final_data["retained_full_original_reservation"]) == deterministic_json(attempt.budgets)
                        and final_data["reservation_state"] == "UNUSED_CAPACITY_RETAINED"
                        and final_data["tail_accounting_state"] == "OBSERVED_PREFIX_WITH_FULL_ORIGINAL_RESERVATION",
                        "LP03_COLD_CONTROL_ORIGINAL_FINALIZATION_EVIDENCE")
                    consumed = EvidenceExecutionConsumptionV1.from_canonical_mapping(final_data["consumed_prefix"])
                    earliest = final.consumed_budget
                    observed_wall, observed_mono, observed_cpu = final_data["native_observation"]
                    readback = final_data["publication_readback_observation"]
                    _native_require(len(readback) == 4 and all(type(value) is int and value >= 0 for value in readback[:3]),
                        "LP03_COLD_CONTROL_ORIGINAL_PUBLICATION_READBACK_SHAPE")
                    dependencies = tuple(EvidenceRecordRefV1.from_canonical_mapping(value) for value in final_data["exact_dependency_refs"])
                    same = set(final_data["consumed_prefix"]) - {"wall_ns", "cpu_ns"}
                    _native_require(all(getattr(consumed,name)==getattr(earliest,name) for name in same)
                        and earliest.wall_ns <= consumed.wall_ns <= attempt.budgets.max_wall_ns
                        and earliest.cpu_ns <= consumed.cpu_ns <= attempt.budgets.max_cpu_ns,
                        "LP03_COLD_CONTROL_ORIGINAL_FINAL_CONSUMED_PREFIX")
                    available = _evidence_storage_observation_v1(final_data["available_at"])
                    _native_require(available["process_identity_ref"] == attempt.deadline.process_identity_ref
                        and available["boot_identity_ref"] == attempt.deadline.boot_identity_ref
                        and available["clock_domain_id"] == attempt.deadline.clock_domain_id
                        and observed_wall >= final.created_wall_ns >= available["wall_ns"] >= observations[2]["observed_at"][0]
                        and all(pre <= use <= post for pre,use,post in zip(readback[:3],
                            (available["wall_ns"],available["monotonic_ns"],available["process_cpu_ns"]),
                            (observed_wall,observed_mono,observed_cpu),strict=True))
                        and 0 < len(dependencies) == len(set(dependencies)) <= 4096,
                        "LP03_COLD_CONTROL_ORIGINAL_FINALIZATION_OBSERVATION")
                    lanes.append((lane_name,"ORIGINAL_CONTROL_COLLECTED",attempt,initial,request,reservation,process,final,registration,final_data))
                else:
                    # Absence of original terminal proof keeps the reservation
                    # encumbered even if the old process is no longer reachable.
                    status = ("ORIGINAL_NATIVE_TERMINAL_FINALIZATION_UNPROVEN" if len(observations)==3
                        else "EVIDENCE_TERMINATION_UNKNOWN")
                    lanes.append((lane_name,status,attempt,initial,request,reservation,process,failure,finalization))
            results = tuple(record(bound_ref+"::CONFORMANCE:R"+str(version),EvidencePipelineConformanceV1,required=False)
                for version in (0,1,2))
            versions = tuple(row[1] if row is not None else None for row in results)
            seen_absence = False
            prior = None
            for version, expected_state in zip(versions,("READY_FOR_REVIEW","REVIEWED_FOR_DELIVERY","PASS_SOFTWARE_CONFORMANCE"),strict=True):
                if version is None:
                    seen_absence = True
                    continue
                _native_require(not seen_absence and len(lanes)==2 and all(lane[1]=="ORIGINAL_CONTROL_COLLECTED" for lane in lanes)
                    and (version.replay_attempt_ref,version.paper_attempt_ref)==tuple(lane[2].record_id for lane in lanes)
                    and (version.replay_registration_ref,version.paper_registration_ref)==tuple(lane[-2].record_id for lane in lanes)
                    and version.terminal_state==expected_state and version.origin is origin and version.generation==original_generation
                    and version.input_lock_ref==bound.input_lock_ref and (prior is None or version.causation_ref==prior.record_id),
                    "LP03_COLD_CONTROL_ORIGINAL_CONFORMANCE_SUCCESSION")
                prior = version
            operation.candidate_versions = versions
            return owner._finish_read_v1(operation,lifecycle,grant,tuple(lanes),"ORIGINAL_CONTROL_ROSTER_OBSERVED")
        finally:
            sqlite3.Connection.close(reader)

    def _evidence_read_cold_lane_publication_v1(self, operation, lane):
        """Read an original lane's pending pointer and exact typed DATA roster."""
        from .models import (EvidenceEventSegmentRecordV1, EvidencePublicationRecordV1,
            EvidenceRecordRefV1, EvidenceValueProjectionRecordV1)
        from .persistence import _EvidenceBoundStoreV1, _EvidenceColdControlReadV1
        from .receipts import _evidence_raw_spine_from_storage_v1, _lp03_spine_from_storage_v1
        from .serialization import _evidence_canonical_object_v1

        owner = _EvidenceColdControlReadV1
        _native_require(type(self) is SQLiteReferenceAdapterV1 and type(operation) is owner
            and operation.phase == "READING" and operation.result is not None
            and any(lane is retained for retained in operation.result[2])
            and len(lane) > 2 and operation.read_target is not None and self is operation.read_target[0],
            "LP03_COLD_LANE_ORIGINAL_READ_SCOPE")
        owner._check_current_v1(operation)
        adapter, host = operation.read_target
        binder = self._evidence_store_binding_v1
        store_id = binder.binding.store_id
        attempt = lane[2]
        _native_require(binder.binding.role.value == lane[0] and attempt.lane.value == lane[0]
            and store_id in attempt.allowed_writes and self is adapter,
            "LP03_COLD_LANE_ORIGINAL_ROLE_AND_STORE")
        reader = _EvidenceBoundStoreV1._open_independent_readback_v1(binder, host, self, operation)
        body_cap = 1_048_576

        def query(sql, args):
            owner._check_current_v1(operation)
            owner._room_v1(operation, owner_queries=1, record_reads=2, query_result_records=2, read_bytes=2*body_cap+1024)
            owner._charge_v1(operation, owner_queries=1)
            cursor = sqlite3.Connection.execute(reader, sql, args)
            try:
                rows = sqlite3.Cursor.fetchmany(cursor, 2)
            finally:
                sqlite3.Cursor.close(cursor)
            owner._charge_v1(operation, record_reads=len(rows), query_result_records=len(rows), read_bytes=sum(
                len(value) if type(value) is bytes else len(deterministic_json(value).encode("utf-8")) for row in rows for value in row))
            _native_require(len(rows) <= 1, "LP03_COLD_LANE_ORIGINAL_ROW_CONFLICT")
            owner._check_current_v1(operation)
            return rows[0] if rows else None

        def receipt(ref, cls, *, required=True):
            row = query("SELECT effective_at,recorded_at,aggregate_id,length(CAST(payload_json AS BLOB)),"
                "substr(CAST(payload_json AS BLOB),1,?) FROM receipt_records WHERE record_id=?", (body_cap+1,ref))
            if row is None and not required:
                return None
            _native_require(row is not None and type(row[-1]) is bytes and 0 < row[-2] == len(row[-1]) <= body_cap,
                "LP03_COLD_LANE_ORIGINAL_RECEIPT_REQUIRED")
            spine = _lp03_spine_from_storage_v1(row[-1],expected_record_id=ref)
            typed = spine.typed_payload.record
            _native_require(type(typed) is cls and (spine.effective_at.isoformat(),spine.recorded_at.isoformat(),spine.aggregate_id)==row[:3],
                "LP03_COLD_LANE_ORIGINAL_RECEIPT_METADATA")
            return typed,row[-1]

        try:
            data_ref = attempt.record_id+"::DATA"
            projected = receipt(data_ref+"::PROJECTION",EvidenceValueProjectionRecordV1,required=False)
            if projected is None:
                _native_require(lane[1] != "ORIGINAL_CONTROL_COLLECTED", "LP03_COLD_LANE_COLLECTED_PROJECTION_MISSING")
                return (lane[0],"EVIDENCE_PUBLICATION_UNPROVEN",None,())
            projection, projection_raw = projected
            pointer = projection.publication_ref
            _native_require((projection.attempt_ref,projection.lane,projection.input_lock_ref,projection.origin,projection.generation)
                == (attempt.record_id,attempt.lane,attempt.input_lock_ref,attempt.origin,attempt.generation)
                and pointer.store_id == store_id, "LP03_COLD_LANE_ORIGINAL_INERT_POINTER")
            published = receipt(pointer.publication_record_id,EvidencePublicationRecordV1,required=False)
            if published is None:
                _native_require(lane[1] != "ORIGINAL_CONTROL_COLLECTED", "LP03_COLD_LANE_COLLECTED_PUBLICATION_MISSING")
                return (lane[0],"EVIDENCE_PUBLICATION_UNPROVEN",pointer,((store_id,"receipt_records",projection.record_id,projection_raw),))
            publication, publication_raw = published
            refs = publication.underlying_record_refs
            _native_require((publication.lane,publication.origin,publication.generation,publication.input_lock_ref,
                publication.original_grant_ref,publication.fence_ref,publication.underlying_store_id,publication.underlying_transaction_ref)
                == (attempt.lane,attempt.origin,attempt.generation,attempt.input_lock_ref,attempt.record_id,attempt.fence_ref,store_id,data_ref)
                and publication.successful_commit_return_observation["process_identity_ref"]==attempt.deadline.process_identity_ref
                and publication.publication_observation["monotonic_ns"] < attempt.deadline.exclusive_deadline_monotonic_ns
                and 10 <= len(refs) <= 4096 and {projection.record_id,projection.original_raw_receipt_ref,data_ref+"::SEGMENT"} <= set(refs),
                "LP03_COLD_LANE_ORIGINAL_PUBLICATION_SCOPE")
            if lane[1] == "ORIGINAL_CONTROL_COLLECTED":
                registration, final = lane[-2:]
                dependency_refs = tuple(EvidenceRecordRefV1.from_canonical_mapping(value) for value in final["exact_dependency_refs"])
                _native_require(registration.accepted_publication_ref==pointer and registration.original_result_ref==projection.record_id
                    and set(refs) <= {ref.record_id for ref in dependency_refs if ref.store_id==store_id},
                    "LP03_COLD_LANE_ORIGINAL_FINALIZATION_POINTER")
            selected = tuple(REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items())
            joins = tuple("SELECT '"+table+"',length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) "
                "FROM "+table+" WHERE "+column+"=?" for table,column in selected)
            query_members = "SELECT * FROM ("+" UNION ALL ".join(joins)+") LIMIT 2"
            original_rows = [(store_id,"receipt_records",publication.record_id,publication_raw)]
            for ref in refs:
                row = query(query_members, (body_cap+1,ref)*len(selected))
                _native_require(row is not None and type(row[-1]) is bytes and 0 < row[-2] == len(row[-1]) <= body_cap,
                    "LP03_COLD_LANE_ORIGINAL_DATA_MEMBER_REQUIRED")
                table, _size, raw = row
                if ref==projection.record_id:
                    _native_require(table=="receipt_records" and raw==projection_raw,"LP03_COLD_LANE_PROJECTION_BODY_CHANGED")
                elif ref==projection.original_raw_receipt_ref:
                    _native_require(table=="receipt_records", "LP03_COLD_LANE_ORIGINAL_RAW_TABLE")
                    retained = _evidence_raw_spine_from_storage_v1(raw,expected_record_id=ref).typed_payload
                    _native_require(retained.existing_receipt.implementation_id==projection.original_implementation_ref
                        and (retained.output_unit,retained.output_basis)==(projection.output_unit,projection.output_basis),
                        "LP03_COLD_LANE_ORIGINAL_RAW_AND_PROJECTION")
                elif ref==data_ref+"::SEGMENT":
                    segment=_lp03_spine_from_storage_v1(raw,expected_record_id=ref).typed_payload.record
                    _native_require(table=="receipt_records" and type(segment) is EvidenceEventSegmentRecordV1
                        and segment.attempt_ref==attempt.record_id and segment.lane is attempt.lane,
                        "LP03_COLD_LANE_ORIGINAL_EVENT_SEGMENT")
                else:
                    _evidence_canonical_object_v1(raw,max_bytes=body_cap)
                original_rows.append((store_id,table,ref,raw))
            owner._check_current_v1(operation)
            # A durable address and the whole data batch are now visible. Old
            # review/right scopes are unresolved until separately checked.
            status = ("CURRENT_ORIGINAL_PUBLICATION_READBACK" if lane[1]=="ORIGINAL_CONTROL_COLLECTED"
                else "CURRENT_PUBLICATION_READBACK_FINALIZATION_UNPROVEN" if lane[1]=="ORIGINAL_NATIVE_TERMINAL_FINALIZATION_UNPROVEN"
                else "EVIDENCE_TERMINATION_UNKNOWN")
            return (lane[0],status,pointer,tuple(original_rows))
        finally:
            sqlite3.Connection.close(reader)

    def _evidence_commit_cold_reconstruction_v1(self, operation):
        """Retain the original current read observations under the parked revocation."""
        from datetime import UTC, datetime, timedelta
        from hashlib import sha256
        from .persistence import _EvidenceBoundStoreV1, _EvidenceColdControlReadV1
        from .serialization import _evidence_canonical_object_v1

        owner = _EvidenceColdControlReadV1
        _native_require(type(self) is SQLiteReferenceAdapterV1 and type(operation) is owner
            and self is operation.issuer.control_store and operation.phase=="RETURNING"
            and operation.archive_payload is not None and operation.archive_commit is operation.archive_readback is None,
            "LP03_COLD_ARCHIVE_ORIGINAL_RESULT_REQUIRED")
        now = owner._check_current_v1(operation)
        stored = deterministic_json(operation.archive_payload).encode("utf-8")
        _native_require(0 < len(stored) <= 131072, "LP03_COLD_ARCHIVE_RESULT_BOUND")
        ref = operation.record_ref+"::ARCHIVE:1"
        binding_ref = ref+"::RESULT"
        created = datetime(1970,1,1,tzinfo=UTC)+timedelta(microseconds=now[0]//1000)
        wall = created.isoformat()
        claim=IdempotencyClaimReceiptV1(ref,ref,"LP03_COLD_ARCHIVE_RECONSTRUCTION",stored.decode("utf-8"),
            IdempotencyClaimStateV1.ACQUIRED,None,created,None,None)
        binding_body=dict(binding_id=binding_ref,claim_ref=ref,result_record_ref=operation.record_ref,created_at=created)
        rows=((ref,None,ref,claim.canonical_request_json,None,wall,deterministic_json(claim)),
            (binding_ref,ref,None,None,operation.record_ref,wall,deterministic_json(binding_body)))
        write_bytes=tuple(len(deterministic_json(row).encode("utf-8")) for row in rows)
        owner._room_v1(operation,control_writes=5,control_bytes=sum(write_bytes))
        connection=self._connection
        _native_require(not sqlite3.Connection.in_transaction.__get__(connection) and self._active_transaction is None,
            "LP03_COLD_ARCHIVE_RESULT_TRANSACTION_STATE")
        sqlite3.Connection.set_trace_callback(connection,None)
        sqlite3.Connection.set_authorizer(connection,None)
        sqlite3.Connection.set_progress_handler(connection,None,0)

        def effect(sql,parameters=(),*,size=0):
            nonlocal attempted
            owner._check_current_v1(operation)
            owner._charge_v1(operation,control_writes=1,control_bytes=size)
            _native_require(self._connection is connection, "LP03_COLD_ARCHIVE_ORIGINAL_RESULT_CONNECTION")
            if sql=="COMMIT":
                _native_require(sqlite3.Connection.in_transaction.__get__(connection), "LP03_COLD_ARCHIVE_RESULT_TRANSACTION_STATE")
                attempted=True
            cursor=sqlite3.Connection.execute(connection,sql,parameters)
            sqlite3.Cursor.close(cursor)

        attempted=False
        try:
            effect("BEGIN IMMEDIATE")
            for row,size in zip(rows,write_bytes,strict=True):
                effect("INSERT INTO idempotency_claims VALUES(?,?,?,?,?,?,?)",row,size=size)
            effect("COMMIT")
            operation.archive_commit=owner._check_current_v1(operation)
        except BaseException:
            if sqlite3.Connection.in_transaction.__get__(connection):
                operation.consumed["control_writes"]+=1
                sqlite3.Connection.rollback(connection)
            operation.phase="ARCHIVE_RESULT_COMMIT_UNPROVEN" if attempted else "ARCHIVE_RESULT_WRITE_DENIED"
            raise
        retained=self._evidence_store_binding_v1
        reader=_EvidenceBoundStoreV1._open_independent_readback_v1(retained,operation.issuer.host,self,operation)
        try:
            for expected in rows:
                payload=expected[-1].encode("utf-8")
                owner._check_current_v1(operation)
                owner._room_v1(operation,owner_queries=1,record_reads=2,query_result_records=2,read_bytes=2*len(payload)+32)
                owner._charge_v1(operation,owner_queries=1)
                cursor=sqlite3.Connection.execute(reader,"SELECT length(CAST(payload_json AS BLOB)),"
                    "substr(CAST(payload_json AS BLOB),1,?) FROM idempotency_claims WHERE claim_record_id=? AND parent_claim_id IS ? "
                    "AND idempotency_key IS ? AND canonical_request_json IS ? AND result_record_ref IS ? AND created_at=?",
                    (len(payload)+1,*expected[:-1]))
                try:
                    returned=sqlite3.Cursor.fetchmany(cursor,2)
                finally:
                    sqlite3.Cursor.close(cursor)
                owner._charge_v1(operation,record_reads=len(returned),query_result_records=len(returned),
                    read_bytes=sum(len(str(size).encode("ascii"))+len(raw) for size,raw in returned))
                _native_require(returned==[(len(payload),payload)],"LP03_COLD_ARCHIVE_RESULT_READBACK")
                _evidence_canonical_object_v1(payload,max_bytes=262144)
            operation.archive_readback=owner._check_current_v1(operation)
            return ref,len(stored),sha256(stored).hexdigest()
        finally:
            sqlite3.Connection.close(reader)

    def _evidence_read_cold_review_v1(self, operation):
        """Resolve the original independently signed decision in its own role file."""
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceIndependentReviewRecordV1, EvidenceMessageKindV1, EvidenceStoreRoleV1
        from .persistence import _EvidenceBoundStoreV1, _EvidenceColdControlReadV1
        from .receipts import _lp03_spine_from_storage_v1

        owner = _EvidenceColdControlReadV1
        _native_require(type(self) is SQLiteReferenceAdapterV1 and type(operation) is owner
            and operation.phase == "READING" and type(operation.candidate_versions) is tuple
            and operation.candidate_versions[0] is not None and operation.read_target is not None and operation.read_target[0] is self,
            "LP03_COLD_REVIEW_ORIGINAL_OWNER_SCOPE")
        original, reviewed, _closed = operation.candidate_versions
        retained = self._evidence_store_binding_v1
        _native_require(retained.binding.role is EvidenceStoreRoleV1.REVIEW, "LP03_COLD_REVIEW_ORIGINAL_ROLE")
        host = operation.read_target[1]
        ref = original.record_id+"::REVIEW:1"
        if reviewed is not None:
            _native_require(reviewed.independent_conformance_review_ref == ref, "LP03_COLD_REVIEW_ORIGINAL_POINTER")
        reader = _EvidenceBoundStoreV1._open_independent_readback_v1(retained,host,self,operation)
        try:
            limit = 1_048_576
            owner._check_current_v1(operation)
            owner._room_v1(operation, owner_queries=1,record_reads=2,query_result_records=2,read_bytes=2*limit+1024)
            owner._charge_v1(operation,owner_queries=1)
            cursor=sqlite3.Connection.execute(reader,"SELECT effective_at,recorded_at,aggregate_id,"
                "length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) FROM receipt_records WHERE record_id=?",
                (limit+1,ref))
            try:
                rows=sqlite3.Cursor.fetchmany(cursor,2)
            finally:
                sqlite3.Cursor.close(cursor)
            owner._charge_v1(operation,record_reads=len(rows),query_result_records=len(rows),read_bytes=sum(
                len(value) if type(value) is bytes else len(deterministic_json(value).encode("utf-8")) for row in rows for value in row))
            if not rows:
                _native_require(reviewed is None, "LP03_COLD_REVIEW_ORIGINAL_REVIEWED_POINTER_UNPROVEN")
                return None
            _native_require(len(rows)==1 and type(rows[0][-1]) is bytes and 0 < rows[0][-2] == len(rows[0][-1]) <= limit,
                "LP03_COLD_REVIEW_ORIGINAL_ROW")
            raw=rows[0][-1]
            spine=_lp03_spine_from_storage_v1(raw,expected_record_id=ref)
            review=spine.typed_payload.record
            config=operation.issuer.host.public_configuration
            _native_require(type(review) is EvidenceIndependentReviewRecordV1
                and (spine.effective_at.isoformat(),spine.recorded_at.isoformat(),spine.aggregate_id)==rows[0][:3]
                and (review.generation,review.origin,review.input_lock_ref,review.original_candidate_ref,review.original_candidate_store,
                    review.original_candidate_version,review.reviewer_admission_ref,review.producing_principal,review.decision)
                == (original.generation,original.origin,original.input_lock_ref,original.record_id,
                    operation.issuer.control_store._evidence_store_binding_v1.binding.store_id,"R0",original.record_id+"::REVIEW_ADMISSION",
                    retained.binding.allowed_writer_principal,"PASS_SOFTWARE_CONFORMANCE"),
                "LP03_COLD_REVIEW_ORIGINAL_DECISION_SCOPE")
            _, payload=EvidenceHostBindingV1._verify_cold_historical_message_v1(operation.issuer.host,review.reviewer_decision_signature,
                archive=operation,kind=EvidenceMessageKindV1.REVIEW_DECISION,issuer=review.producing_principal,
                subject=ref,audience=config.service_principal,generation=original.generation,original_wall_ns=review.created_wall_ns)
            _native_require(payload.consumer_principal==config.service_principal
                and review.observed_metric_refs==tuple(lane[-2].original_result_ref for lane in operation.result[2]),
                "LP03_COLD_REVIEW_ORIGINAL_PAIRED_METRIC_REFS")
            owner._check_current_v1(operation)
            return review,raw
        finally:
            sqlite3.Connection.close(reader)

    def _evidence_read_measured_rows_v1(self, operation, *, stage):
        """Finite exact-reference joins; every returned record and byte is charged."""
        from .persistence import (_EvidenceReviewOperationV1, _EvidenceReviewedConformanceOperationV1, _EvidenceReceiverOperationV1,
            _EvidenceClosedConformanceOperationV1,
            _EvidenceBoundStoreV1, _evidence_lane_member_from_storage_v1)
        from .receipts import _lp03_spine_from_storage_v1
        from .cohort_compiler import _read_original_compilation_member_v1
        from .serialization import _evidence_canonical_object_v1
        owner = type(operation)
        _native_require(owner in (_EvidenceReviewOperationV1, _EvidenceReviewedConformanceOperationV1,
            _EvidenceReceiverOperationV1, _EvidenceClosedConformanceOperationV1), "LP03_MEASURED_READ_OWNER")
        successor = owner is _EvidenceReviewedConformanceOperationV1
        closeout = owner is _EvidenceClosedConformanceOperationV1
        receiver = owner is _EvidenceReceiverOperationV1
        _native_require(stage in (("ADMISSION", "PARENTS", "ACCEPTANCE", "ACK") if receiver else
                                 ("PARENTS", "CLOSEOUT") if closeout else ("PARENTS", "SUCCESSOR") if successor else ("ADMISSION", "PARENTS", "REVIEW")),
                        "LP03_REVIEW_READ_STAGE")
        parent_read = stage == "PARENTS"
        own_store = stage in ("REVIEW", "ACCEPTANCE", "ACK")
        expected_store = operation.store if own_store else operation.issuer.control_store
        phases = {"ADMISSION": ("ADMISSION_COMMITTED_PENDING_READBACK",),
                  "PARENTS": ("PARENTS_PENDING",) if successor or closeout else ("ADMITTED_AND_READBACK",),
                  "REVIEW": ("REVIEW_COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK"),
                  "SUCCESSOR": ("SUCCESSOR_COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK"),
                  "CLOSEOUT": ("CLOSEOUT_COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK"),
                  "ACCEPTANCE": ("ACCEPTANCE_COMMITTED_PENDING_READBACK",),
                  "ACK": ("ACK_COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK")}
        _native_require(self is expected_store and operation.phase in phases[stage], "LP03_REVIEW_ORIGINAL_READ_SCOPE")
        owner._assert_original_v1(operation, canonical=True)
        targets = operation.read_sets if parent_read else ((self, operation.host if own_store else operation.issuer.host,
            operation.admission_rows if stage == "ADMISSION" else operation.acceptance_rows if stage == "ACCEPTANCE" else operation.rows),)
        # Refuse an unaffordable replay before opening a reader or doing a partial
        # acquisition. Metadata uses the same exact original database path below.
        expected_reads = sum(len(target[2]) + 1 for target in targets)
        owner._room_v1(operation, record_reads=expected_reads, query_result_records=expected_reads,
            read_bytes=sum(len(row[-1].encode("utf-8")) + len(row[0].encode("utf-8")) + 21
                for _, _, rows in targets for _, row, _ in rows))
        observations = []
        for target in targets:
            adapter, host, rows = target
            operation.read_target = target
            reader = _EvidenceBoundStoreV1._open_independent_readback_v1(adapter._evidence_store_binding_v1, host, adapter, operation)
            try:
                for table in dict.fromkeys(table for table, _, _ in rows):
                    selected = tuple((row, original) for name, row, original in rows if name == table)
                    columns = REFERENCE_SCHEMA_COLUMNS_V1[table]
                    identities = tuple(row[0] for row, _ in selected)
                    _native_require(len(set(identities)) == len(identities), "LP03_REVIEW_DUPLICATE_READ_REFERENCE")
                    expected = {row[0]: (row[-1].encode("utf-8"), original) for row, original in selected}
                    parameters = tuple(value for row, _ in selected for value in (*row[:-1], len(expected[row[0]][0]) + 1))
                    requested_columns = (*columns[:-1], "payload_limit")
                    sql = ("WITH requested(" + ",".join(requested_columns) + ") AS (VALUES "
                        + ",".join("(" + ",".join("?" for _ in requested_columns) + ")" for _ in selected)
                        + ") SELECT stored." + columns[0] + ",length(CAST(stored.payload_json AS BLOB)),"
                        + "substr(CAST(stored.payload_json AS BLOB),1,requested.payload_limit) FROM " + table
                        + " AS stored JOIN requested ON "
                        + " AND ".join("stored." + column + " IS requested." + column for column in columns[:-1]))
                    owner._room_v1(operation, owner_queries=1, record_reads=len(selected), query_result_records=len(selected),
                        read_bytes=sum(len(raw) + len(ref.encode("utf-8")) + 21 for ref, (raw, _) in expected.items()))
                    owner._check_current_v1(operation)
                    owner._charge_v1(operation, owner_queries=1)
                    cursor = sqlite3.Connection.execute(reader, sql, parameters)
                    try:
                        actual = sqlite3.Cursor.fetchmany(cursor, len(selected) + 1)
                    finally:
                        sqlite3.Cursor.close(cursor)
                    owner._charge_v1(operation, record_reads=len(actual), query_result_records=len(actual),
                        read_bytes=sum(len(item[0].encode("utf-8")) + len(str(item[1])) + len(item[2]) for item in actual))
                    _native_require(len(actual) == len(selected) and len({item[0] for item in actual}) == len(selected)
                                    and {item[0] for item in actual} == set(expected), "LP03_REVIEW_EXACT_READ_ROSTER_MISMATCH")
                    for ref, size, raw in actual:
                        wanted, original = expected[ref]
                        if (size, raw) != (len(wanted), wanted):
                            if receiver and stage == "ACK" and table == "receipt_records" and ref == operation.record.record_id:
                                raise PersistenceContractError(ReasonCode.EVIDENCE_RECEIVER_CONFLICT,
                                    "LP03_RECEIVER_EXACT_ACK_BODY_CONFLICT")
                            _native_require(False, "LP03_REVIEW_EXACT_READBACK_MISMATCH")
                        if original is not None:
                            _evidence_lane_member_from_storage_v1(raw, original)
                        elif table == "receipt_records":
                            if ref in tuple(member.record_id for member in operation.registration.binding_spines):
                                _read_original_compilation_member_v1(raw, operation=operation.registration, record_ref=ref)
                            else:
                                _lp03_spine_from_storage_v1(raw, expected_record_id=ref)
                        else:
                            _evidence_canonical_object_v1(raw, max_bytes=1048576)
                    owner._check_current_v1(operation)
            finally:
                sqlite3.Connection.close(reader)
                operation.read_target = None
            observed = owner._check_current_v1(operation)
            observations.append((adapter._evidence_store_binding_v1.binding.store_id,
                tuple((table, row[0]) for table, row, _ in rows), observed))
        owner._assert_original_v1(operation, canonical=True)
        observed = owner._check_current_v1(operation)
        if parent_read:
            operation.parent_readbacks = tuple(observations)
            operation.parent_original = (operation.parent_readbacks, operation.read_sets)
            operation.phase = "PARENTS_READBACK"
        elif stage == "ADMISSION":
            operation.admission_readback = (*observed, tuple(operation.registration.consumed.items()))
            operation.admission_readback_original = (operation.admission_readback, operation.admission_rows_original)
            operation.phase = "ADMITTED_AND_READBACK"
        elif stage == "ACCEPTANCE":
            operation.acceptance_readback = (*observed, tuple(operation.registration.consumed.items()))
            operation.acceptance_readback_original = (operation.acceptance_readback, operation.acceptance_rows_original)
            operation.phase = "ACCEPTANCE_COMMITTED_AND_READBACK"
        elif operation.readback_observation is None:
            operation.readback_observation = (*observed, tuple(operation.registration.consumed.items()))
            operation.readback_original = (operation.readback_observation, operation.rows_original)
            operation.phase = "COMMITTED_AND_READBACK"

    def _evidence_commit_review_v1(self, operation, *, stage):
        from .persistence import _EvidenceReviewOperationV1
        _native_require(type(operation) is _EvidenceReviewOperationV1, "LP03_REVIEW_ORIGINAL_WRITE_SCOPE")
        return SQLiteReferenceAdapterV1._evidence_commit_measured_rows_v1(self, operation, stage=stage)

    def _evidence_commit_measured_rows_v1(self, operation, *, stage):
        from .persistence import (_EvidenceReviewOperationV1, _EvidenceReviewedConformanceOperationV1,
            _EvidenceReceiverOperationV1, _EvidenceClosedConformanceOperationV1, _EvidenceRegistrationOperationV1)
        from .latency_policy import _EvidenceLocalClockV1
        owner = type(operation)
        _native_require(owner in (_EvidenceReviewOperationV1, _EvidenceReviewedConformanceOperationV1,
            _EvidenceReceiverOperationV1, _EvidenceClosedConformanceOperationV1), "LP03_MEASURED_WRITE_OWNER")
        successor = owner is _EvidenceReviewedConformanceOperationV1
        closeout = owner is _EvidenceClosedConformanceOperationV1
        receiver = owner is _EvidenceReceiverOperationV1
        _native_require(stage in ("ADMISSION", "ACCEPTANCE", "ACK") if receiver else
                        stage == "CLOSEOUT" if closeout else stage == "SUCCESSOR" if successor else stage in ("ADMISSION", "REVIEW"), "LP03_REVIEW_WRITE_STAGE")
        admission = stage == "ADMISSION"
        _native_require(self is (operation.issuer.control_store if admission or successor or closeout else operation.store)
                        and operation.phase == ("PARENTS_READBACK" if successor or closeout else "ADMISSION_PENDING" if admission
                            else stage + "_PREPARED"),
                        "LP03_REVIEW_ORIGINAL_WRITE_SCOPE")
        if admission:
            owner._prepare_admission_v1(operation)
        elif successor or closeout:
            owner._prepare_records_v1(operation)
        owner._assert_original_v1(operation, canonical=True)
        rows = operation.admission_rows if admission else operation.acceptance_rows if stage == "ACCEPTANCE" else operation.rows
        ids = tuple(row[0] for _, row, _ in rows)
        _native_require(len(ids) == len(set(ids)) == (4 if receiver and admission else 2 if admission or stage == "ACCEPTANCE" else 3),
                        "LP03_REVIEW_EXACT_WRITE_ROSTER")
        # Include actual BEGIN/inserts/COMMIT, exact collisions, and one rollback
        # before the first write. Failed work stays on the original account.
        owner._room_v1(operation, owner_queries=1 + len(REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1),
            control_writes=len(rows) + 3, control_bytes=sum(len(row[-1].encode("utf-8")) for _, row, _ in rows))
        connection = self._connection
        sqlite3.Connection.set_trace_callback(connection, None)
        sqlite3.Connection.set_authorizer(connection, None)
        sqlite3.Connection.set_progress_handler(connection, None, 0)
        owner._check_current_v1(operation)
        _native_require(not sqlite3.Connection.in_transaction.__get__(connection), "LP03_REVIEW_TRANSACTION_REENTRY")

        def effect(sql, parameters=(), byte_count=0):
            owner._room_v1(operation, control_writes=1, control_bytes=byte_count)
            owner._check_current_v1(operation)
            owner._charge_v1(operation, control_writes=1, control_bytes=byte_count)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            sqlite3.Cursor.close(cursor)

        try:
            effect("BEGIN IMMEDIATE")
            operation.phase = stage + "_TRANSACTION_OPEN"
            queries = (("SELECT 1 FROM idempotency_claims WHERE idempotency_key=?", (rows[0][1][2],), 1),
                *(("SELECT 1 FROM " + table + " WHERE " + column + " IN (" + ",".join("?" for _ in ids) + ")", ids, len(ids))
                  for table, column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items()))
            for sql, parameters, bound in queries:
                owner._room_v1(operation, owner_queries=1, record_reads=bound, query_result_records=bound, read_bytes=bound)
                owner._check_current_v1(operation)
                owner._charge_v1(operation, owner_queries=1)
                cursor = sqlite3.Connection.execute(connection, sql, parameters)
                try:
                    actual = sqlite3.Cursor.fetchmany(cursor, bound + 1)
                finally:
                    sqlite3.Cursor.close(cursor)
                owner._charge_v1(operation, record_reads=len(actual), query_result_records=len(actual), read_bytes=len(actual))
                _native_require(not actual, "LP03_REVIEW_ALREADY_PRESENT_OR_CONFLICT")
            for table, row, _ in rows:
                effect("INSERT INTO " + table + " VALUES(" + ",".join("?" for _ in row) + ")", row, len(row[-1].encode("utf-8")))
            owner._assert_original_v1(operation, canonical=True)
            operation.phase = stage + "_COMMIT_ATTEMPTED"
            effect("COMMIT")
            operation.phase = stage + "_COMMITTED_PENDING_READBACK"
            observed = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
            if admission:
                operation.admission_commit = observed
                operation.admission_commit_original = (observed, operation.admission_rows_original)
            elif stage == "ACCEPTANCE":
                operation.acceptance_commit = observed
                operation.acceptance_commit_original = (observed, operation.acceptance_rows_original)
            else:
                operation.commit_observation = observed
                operation.commit_original = (observed, operation.rows_original)
        except BaseException:
            if sqlite3.Connection.in_transaction.__get__(connection):
                try:
                    operation.registration.consumed["control_writes"] += 1
                    if receiver:
                        operation.consumed["control_writes"] += 1
                        operation.consumed_original = tuple(operation.consumed.items())
                    cursor = sqlite3.Connection.execute(connection, "ROLLBACK")
                    sqlite3.Cursor.close(cursor)
                    operation.phase = stage + "_ROLLED_BACK"
                except BaseException:
                    operation.phase = stage + "_ROLLBACK_UNPROVEN"
                    self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            elif operation.phase in (stage + "_COMMIT_ATTEMPTED", stage + "_COMMITTED_PENDING_READBACK"):
                operation.phase = stage + "_COMMIT_OR_OBSERVATION_UNRESOLVED"
            _EvidenceRegistrationOperationV1._observe_accounting_v1(operation.registration)
            raise
        SQLiteReferenceAdapterV1._evidence_read_measured_rows_v1(self, operation, stage=stage)

    def _evidence_commit_conformance_v1(self, operation):
        from .persistence import _EvidenceConformanceOperationV1, _EvidenceRegistrationOperationV1
        from .latency_policy import _EvidenceLocalClockV1
        owner = _EvidenceConformanceOperationV1
        _native_require(type(operation) is owner and operation.issuer.control_store is self
                        and operation.phase == "PARENTS_READBACK", "LP03_CONFORMANCE_ORIGINAL_CONTROL")
        owner._prepare_records_v1(operation)
        connection = self._connection
        sqlite3.Connection.set_trace_callback(connection, None)
        sqlite3.Connection.set_authorizer(connection, None)
        sqlite3.Connection.set_progress_handler(connection, None, 0)
        owner._check_current_v1(operation)
        _native_require(not sqlite3.Connection.in_transaction.__get__(connection), "LP03_CONFORMANCE_TRANSACTION_REENTRY")

        def effect(sql, parameters=(), byte_count=0):
            owner._room_v1(operation, control_writes=1, control_bytes=byte_count)
            owner._check_current_v1(operation)
            owner._charge_v1(operation, control_writes=1, control_bytes=byte_count)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            sqlite3.Cursor.close(cursor)

        try:
            effect("BEGIN IMMEDIATE")
            operation.phase = "TRANSACTION_OPEN"
            ids = tuple(row[0] for _table, row, _ in operation.rows)
            _native_require(len(ids) == len(set(ids)) == 3, "LP03_CONFORMANCE_EXACT_ROW_ROSTER")
            queries = (("SELECT 1 FROM idempotency_claims WHERE idempotency_key=?", (operation.comparison.idempotency_key,), 1),
                *(("SELECT 1 FROM " + table + " WHERE " + column + " IN (?,?,?)", ids, 3)
                  for table, column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items()))
            for sql, parameters, bound in queries:
                owner._room_v1(operation, owner_queries=1, record_reads=bound, query_result_records=bound, read_bytes=bound)
                owner._check_current_v1(operation)
                owner._charge_v1(operation, owner_queries=1)
                cursor = sqlite3.Connection.execute(connection, sql, parameters)
                try:
                    actual = sqlite3.Cursor.fetchmany(cursor, bound + 1)
                finally:
                    sqlite3.Cursor.close(cursor)
                owner._charge_v1(operation, record_reads=len(actual), query_result_records=len(actual), read_bytes=len(actual))
                _native_require(not actual, "LP03_CONFORMANCE_ALREADY_PRESENT_OR_CONFLICT")
            for table, row, _ in operation.rows:
                effect("INSERT INTO " + table + " VALUES(" + ",".join("?" for _ in row) + ")", row, len(row[-1].encode("utf-8")))
            owner._assert_original_v1(operation, canonical=True)
            operation.phase = "COMMIT_ATTEMPTED"
            effect("COMMIT")
            operation.phase = "COMMITTED_PENDING_READBACK"
            operation.commit_observation = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
            operation.commit_original = (operation.commit_observation, operation.rows_original)
        except BaseException:
            if sqlite3.Connection.in_transaction.__get__(connection):
                try:
                    operation.registration.consumed["control_writes"] += 1
                    cursor = sqlite3.Connection.execute(connection, "ROLLBACK")
                    sqlite3.Cursor.close(cursor)
                    operation.phase = "ROLLED_BACK"
                except BaseException:
                    operation.phase = "ROLLBACK_UNPROVEN"
                    self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            elif operation.phase in ("COMMIT_ATTEMPTED", "COMMITTED_PENDING_READBACK"):
                operation.phase = "COMMIT_OR_OBSERVATION_UNRESOLVED"
            _EvidenceRegistrationOperationV1._observe_accounting_v1(operation.registration)
            raise
        SQLiteReferenceAdapterV1._evidence_read_conformance_v1(self, operation, parents=False)

    def _evidence_finalize_lane_v1(self, operation):
        """Original issuer transaction for collection and selected lane registration."""
        from .persistence import (_EvidenceLaneOperationV1, _EvidenceRegistrationOperationV1,
            _EvidenceBoundStoreV1, EvidenceAvailabilityHandleV1, _evidence_lane_member_from_storage_v1)
        from .latency_policy import _EvidenceLocalClockV1
        owner = _EvidenceLaneOperationV1
        _native_require(type(operation) is owner and operation.issuer.control_store is self
                        and operation.finalization_phase == "NOT_STARTED", "LP03_FINALIZATION_ORIGINAL_CONTROL")
        owner._prepare_finalization_v1(operation)
        connection = self._connection
        sqlite3.Connection.set_trace_callback(connection, None)
        sqlite3.Connection.set_authorizer(connection, None)
        sqlite3.Connection.set_progress_handler(connection, None, 0)

        def current():
            return EvidenceAvailabilityHandleV1._require_current_v1(operation.availability, operation=operation,
                purpose="EVIDENCE_LANE_REGISTRATION_V1", current_grant=operation.attempt.handle, clock=operation.issuer.clock)

        def effect(sql, parameters=(), byte_count=0):
            owner._room_v1(operation, control_writes=1, control_bytes=byte_count)
            current()
            owner._charge_v1(operation, control_writes=1, control_bytes=byte_count)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            sqlite3.Cursor.close(cursor)

        current()
        _native_require(not sqlite3.Connection.in_transaction.__get__(connection), "LP03_FINALIZATION_TRANSACTION_REENTRY")
        try:
            effect("BEGIN IMMEDIATE")
            operation.finalization_phase = "TRANSACTION_OPEN"
            ids = tuple(row[0] for _table, row, _record in operation.final_rows)
            _native_require(len(ids) == len(set(ids)) == 4, "LP03_FINALIZATION_EXACT_ROSTER")
            claim = operation.final_rows[2][2]
            queries = (("SELECT 1 FROM idempotency_claims WHERE idempotency_key=?", (claim.idempotency_key,), 1),
                *(("SELECT 1 FROM " + table + " WHERE " + column + " IN (?,?,?,?)", ids, 4)
                  for table, column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items()))
            for sql, parameters, bound in queries:
                owner._room_v1(operation, owner_queries=1, record_reads=bound, query_result_records=bound, read_bytes=bound)
                current()
                owner._charge_v1(operation, owner_queries=1)
                cursor = sqlite3.Connection.execute(connection, sql, parameters)
                try:
                    actual = sqlite3.Cursor.fetchmany(cursor, bound + 1)
                finally:
                    sqlite3.Cursor.close(cursor)
                owner._charge_v1(operation, record_reads=len(actual), query_result_records=len(actual), read_bytes=len(actual))
                _native_require(not actual, "LP03_FINALIZATION_ALREADY_PRESENT_OR_CONFLICT")
            for table, row, _record in operation.final_rows:
                effect("INSERT INTO " + table + " VALUES(" + ",".join("?" for _ in row) + ")", row, len(row[-1].encode("utf-8")))
            operation.finalization_phase = "COMMIT_ATTEMPTED"
            effect("COMMIT")
            operation.finalization_phase = "COMMITTED_PENDING_READBACK"
            operation.final_commit_observation = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
            operation.final_commit_original = (operation.final_commit_observation, operation.final_original)
        except BaseException:
            if sqlite3.Connection.in_transaction.__get__(connection):
                try:
                    operation.attempt.registration.consumed["control_writes"] += 1
                    cursor = sqlite3.Connection.execute(connection, "ROLLBACK")
                    sqlite3.Cursor.close(cursor)
                    operation.finalization_phase = "ROLLED_BACK"
                except BaseException:
                    operation.finalization_phase = "ROLLBACK_UNPROVEN"
                    self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            elif operation.finalization_phase in ("COMMIT_ATTEMPTED", "COMMITTED_PENDING_READBACK"):
                operation.finalization_phase = "COMMIT_OR_OBSERVATION_UNRESOLVED"
            _EvidenceRegistrationOperationV1._observe_accounting_v1(operation.attempt.registration)
            raise
        reader = _EvidenceBoundStoreV1._open_independent_readback_v1(self._evidence_store_binding_v1,
            operation.issuer.host, self, operation.attempt.registration)
        try:
            for table, row, record in operation.final_rows:
                expected = row[-1].encode("utf-8")
                columns = REFERENCE_SCHEMA_COLUMNS_V1[table]
                owner._room_v1(operation, owner_queries=1, record_reads=1, query_result_records=1, read_bytes=len(expected) + 21)
                current()
                owner._charge_v1(operation, owner_queries=1)
                cursor = sqlite3.Connection.execute(reader,
                    "SELECT length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) FROM " + table
                    + " WHERE " + " AND ".join(column + " IS ?" for column in columns[:-1]), (len(expected) + 1, *row[:-1]))
                try:
                    actual = sqlite3.Cursor.fetchmany(cursor, 2)
                finally:
                    sqlite3.Cursor.close(cursor)
                owner._charge_v1(operation, record_reads=len(actual), query_result_records=len(actual),
                    read_bytes=sum(len(item[1]) + len(str(item[0])) for item in actual))
                _native_require(len(actual) == 1 and actual[0] == (len(expected), expected), "LP03_FINALIZATION_READBACK_MISMATCH")
                _evidence_lane_member_from_storage_v1(expected, record)
        finally:
            sqlite3.Connection.close(reader)
        observed = current()
        operation.final_readback_observation = (*observed, tuple(operation.attempt.registration.consumed.items()))
        operation.final_readback_original = (operation.final_readback_observation, operation.final_original)
        operation.finalization_phase = "COMMITTED_AND_READBACK"

    def resolve_evidence_availability_v1(self, publication_ref, *, record_refs, purpose, current_grant, clock):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceAttemptGrantV1
        from .persistence import _EvidenceLaneOperationV1, EvidenceAvailabilityHandleV1
        from .latency_policy import _EvidenceLocalClockV1, _evidence_storage_observation_v1
        from .models import EvidenceRecordRefV1
        _native_require(type(current_grant) is EvidenceAttemptGrantV1, "LP03_AVAILABILITY_ORIGINAL_GRANT")
        operation = current_grant._attempt.lane_operation
        owner = _EvidenceLaneOperationV1
        diagnostic = "LP03_AVAILABILITY_EXACT_PUBLISHED_CLOSURE_REQUIRED"
        _native_require(type(operation) is owner and operation.platform._store is self
                        and publication_ref is operation.publication_ref and type(record_refs) is tuple
                        and all(type(ref) is EvidenceRecordRefV1 for ref in record_refs)
                        and operation.availability is None
                        and operation.publication_phase != "COMMITTED_AND_READBACK", diagnostic)
        expected_refs = operation.required_record_refs
        _native_require(record_refs == (() if expected_refs is None else expected_refs), diagnostic)
        owner._require_publication_purpose_v1(operation, purpose, current_grant, clock)
        owner._check_current_v1(operation)
        if expected_refs is None or operation.publication_phase != "COMMITTED_PENDING_READBACK":
            owner._require_publication_purpose_v1(operation, purpose, current_grant, clock)
            raise PersistenceContractError(ReasonCode.EVIDENCE_PUBLICATION_UNPROVEN, diagnostic)
        SQLiteReferenceAdapterV1._evidence_read_publication_control_v1(operation.issuer.control_store, operation)
        SQLiteReferenceAdapterV1._evidence_read_lane_batch_v1(self, operation, publication=True)
        # Allocate and populate before the final currentness observation. No
        # further I/O, caller callback or native close follows the final check.
        result = object.__new__(EvidenceAvailabilityHandleV1)
        result._operation, result._purpose = operation, purpose
        result._record_refs = operation.required_record_refs
        result._consumer_principal = operation.issuer.host.public_configuration.service_principal
        observation_body = dict(clock_domain_id=clock.clock_domain_id, process_identity_ref=clock.process_identity_ref,
            boot_identity_ref=clock.boot_identity_ref, clock_declarations=_EvidenceLocalClockV1.declaration_v1(clock))
        owner._require_publication_purpose_v1(operation, purpose, current_grant, clock)
        observed = owner._check_current_v1(operation)
        owner._require_publication_purpose_v1(operation, purpose, current_grant, clock)
        observation_body.update(wall_ns=observed[0], monotonic_ns=observed[1], process_cpu_ns=observed[2])
        result._available_at = _evidence_storage_observation_v1(observation_body)
        result._original = (purpose, result._record_refs, result._available_at, result._consumer_principal,
                            operation.publication_readback_original, current_grant, clock)
        operation.publication_phase = "COMMITTED_AND_READBACK"
        operation.availability = result
        return result

    def _evidence_read_process_append_v1(self, append, *, predecessor_in_transaction=False):
        from .persistence import _EvidenceAttemptObservationAppendV1, _EvidenceRegistrationOperationV1, _EvidenceBoundStoreV1
        from .receipts import _lp03_spine_from_storage_v1
        from .serialization import _evidence_process_observation_body_v1
        _native_require(type(append) is _EvidenceAttemptObservationAppendV1 and type(predecessor_in_transaction) is bool,
                        "LP03_PROCESS_APPEND_READ_SCOPE")
        _EvidenceAttemptObservationAppendV1._assert_original_v1(append)
        attempt, owner = append.attempt, _EvidenceRegistrationOperationV1
        operation = attempt.registration
        _native_require(operation.issuer.control_store is self and operation.active_attempt is attempt,
                        "LP03_PROCESS_APPEND_READ_OWNER")
        retained_appends = attempt.observation_appends
        owner._check_current_v1(operation)
        _native_require(attempt.observation_appends is retained_appends, "LP03_PROCESS_APPEND_LINEAGE_CHANGED")
        _EvidenceAttemptObservationAppendV1._assert_original_v1(append, canonical=False)
        previous = ()
        if predecessor_in_transaction:
            _native_require(append.phase == "TRANSACTION_OPEN" and self._connection.in_transaction,
                            "LP03_PROCESS_APPEND_TRANSACTION_REQUIRED")
            # Original admission plus every earlier observation is a finite
            # exact lineage, not a recursive acquisition of the current result.
            previous = tuple(entry for entry in attempt.observation_appends if entry is not append)
            _native_require(len(previous) <= 2 and all(entry.phase == "COMMITTED_AND_READBACK" for entry in previous),
                            "LP03_PROCESS_APPEND_PREDECESSOR_UNRESOLVED")
            for entry in previous:
                _EvidenceAttemptObservationAppendV1._assert_original_v1(entry)
            refs = (*attempt.readback_refs, *(ref for entry in previous for ref in entry.refs))
            rows = (*attempt.readback_rows, *(row for entry in previous for row in entry.rows))
            reader = self._connection
        else:
            _native_require(append.phase in ("COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK") and append.original is not None,
                            "LP03_PROCESS_APPEND_READBACK_UNRESOLVED")
            refs, rows = append.refs, append.rows
            reader = _EvidenceBoundStoreV1._open_independent_readback_v1(
                self._evidence_store_binding_v1, operation.issuer.host, self, operation)
        try:
            _native_require(len(refs) == len(rows), "LP03_PROCESS_APPEND_EXACT_ROSTER")
            for (table, ref), row in zip(refs, rows):
                expected = row[-1].encode("utf-8")
                owner._room_v1(operation, owner_queries=1, record_reads=1, query_result_records=1, read_bytes=len(expected) + 21)
                _EvidenceAttemptObservationAppendV1._assert_original_v1(append)
                owner._check_current_v1(operation)
                _native_require(attempt.observation_appends is retained_appends, "LP03_PROCESS_APPEND_LINEAGE_CHANGED")
                for entry in (*previous, append):
                    _EvidenceAttemptObservationAppendV1._assert_original_v1(entry, canonical=False)
                if table == "receipt_records":
                    sql = ("SELECT length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) "
                           "FROM receipt_records WHERE record_id=? AND effective_at=? AND recorded_at=? AND aggregate_id=?")
                else:
                    _native_require(table == "idempotency_claims", "LP03_PROCESS_APPEND_EXACT_TABLE")
                    sql = ("SELECT length(CAST(payload_json AS BLOB)),substr(CAST(payload_json AS BLOB),1,?) "
                           "FROM idempotency_claims WHERE claim_record_id=? AND parent_claim_id IS ? AND idempotency_key IS ? "
                           "AND canonical_request_json IS ? AND result_record_ref IS ? AND created_at=?")
                _native_require(row[0] == ref, "LP03_PROCESS_APPEND_EXACT_JOIN")
                owner._charge_v1(operation, owner_queries=1)
                cursor = sqlite3.Connection.execute(reader, sql, (len(expected) + 1, *row[:-1]))
                try:
                    actual = sqlite3.Cursor.fetchmany(cursor, 2)
                finally:
                    sqlite3.Cursor.close(cursor)
                owner._charge_v1(operation, record_reads=len(actual), query_result_records=len(actual),
                    read_bytes=sum(len(item[1]) + len(str(item[0])) for item in actual))
                _native_require(len(actual) == 1 and actual[0] == (len(expected), expected), "LP03_PROCESS_APPEND_READBACK_MISMATCH")
                if table == "receipt_records":
                    _lp03_spine_from_storage_v1(expected, expected_record_id=ref)
                elif row[0] == append.body["observation_ref"]:
                    _native_require(deterministic_json(_evidence_process_observation_body_v1(row[3].encode("utf-8"))) == append.body_json,
                                    "LP03_PROCESS_APPEND_BODY_READBACK_MISMATCH")
        finally:
            if not predecessor_in_transaction:
                sqlite3.Connection.close(reader)
        _EvidenceAttemptObservationAppendV1._assert_original_v1(append)
        observed = owner._check_current_v1(operation)
        _native_require(attempt.observation_appends is retained_appends, "LP03_PROCESS_APPEND_LINEAGE_CHANGED")
        for entry in (*previous, append):
            _EvidenceAttemptObservationAppendV1._assert_original_v1(entry, canonical=False)
        if not predecessor_in_transaction:
            append.readback_observation = (*observed, tuple(operation.consumed.items()))

    def _evidence_append_process_observation_v1(self, append):
        from datetime import UTC, timedelta
        from .persistence import _EvidenceAttemptObservationAppendV1, _EvidenceRegistrationOperationV1
        from .receipts import _lp03_spine_for_record_v1
        from .latency_policy import _EvidenceLocalClockV1
        _native_require(type(append) is _EvidenceAttemptObservationAppendV1 and append.phase == "RESERVED",
                        "LP03_PROCESS_APPEND_ORIGINAL_RESERVATION")
        attempt, owner, connection = append.attempt, _EvidenceRegistrationOperationV1, self._connection
        operation = attempt.registration
        _native_require(operation.issuer.control_store is self and operation.active_attempt is attempt
                        and not connection.in_transaction, "LP03_PROCESS_APPEND_TRANSACTION_REENTRY")

        def effect(sql, parameters=()):
            _EvidenceAttemptObservationAppendV1._assert_original_v1(append)
            owner._check_current_v1(operation)
            _EvidenceAttemptObservationAppendV1._assert_original_v1(append, canonical=False)
            owner._charge_v1(operation, control_writes=1)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            sqlite3.Cursor.close(cursor)

        try:
            owner._room_v1(operation, control_writes=6)
            effect("BEGIN IMMEDIATE")
            append.phase = "TRANSACTION_OPEN"
            SQLiteReferenceAdapterV1._evidence_read_process_append_v1(self, append, predecessor_in_transaction=True)
            claim_id = append.body["observation_ref"]
            state_id = attempt.grant_record.record_id + "::STATE:" + str(len(attempt.observation_appends) - 1)
            exact_ids = (*((state_id,) if append.stage == "RUNNING" else ()), claim_id, claim_id + "::RESULT")
            placeholders = ",".join("?" for _ in exact_ids)
            for table, column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items():
                owner._room_v1(operation, owner_queries=1, record_reads=len(exact_ids), query_result_records=len(exact_ids),
                    read_bytes=sum(len(deterministic_json(ref).encode("utf-8")) for ref in exact_ids))
                _EvidenceAttemptObservationAppendV1._assert_original_v1(append)
                owner._check_current_v1(operation)
                _EvidenceAttemptObservationAppendV1._assert_original_v1(append, canonical=False)
                owner._charge_v1(operation, owner_queries=1)
                cursor = sqlite3.Connection.execute(connection,
                    "SELECT " + column + " FROM " + table + " WHERE " + column + " IN (" + placeholders + ")", exact_ids)
                try:
                    rows = sqlite3.Cursor.fetchmany(cursor, len(exact_ids) + 1)
                finally:
                    sqlite3.Cursor.close(cursor)
                owner._charge_v1(operation, record_reads=len(rows), query_result_records=len(rows),
                    read_bytes=sum(len(deterministic_json(value).encode("utf-8")) for row in rows for value in row))
                _native_require(not rows, "LP03_CONTROL_CROSS_TABLE_IDENTITY_CONFLICT")
            # The state retains the actual post-query currentness observation;
            # its process reference separately retains the earlier native sample.
            record = _EvidenceAttemptObservationAppendV1._build_state_v1(append)
            observed = owner._check_current_v1(operation)
            _EvidenceAttemptObservationAppendV1._assert_original_v1(append, canonical=False)
            created_at = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=observed[0] // 1000)
            claim = IdempotencyClaimReceiptV1(claim_id, claim_id, "LP03_SVC_PROCESS_OBSERVATION_APPEND", append.body_json,
                IdempotencyClaimStateV1.ACQUIRED, None, created_at, None, None)
            result_ref = append.predecessor.record_id if record is None else record.record_id
            claim_rows = (
                (claim_id, None, claim_id, append.body_json, None, created_at.isoformat(), deterministic_json(claim)),
                (claim_id + "::RESULT", claim_id, None, None, result_ref, created_at.isoformat(),
                    deterministic_json(dict(binding_id=claim_id + "::RESULT", claim_ref=claim_id,
                                            result_record_ref=result_ref, created_at=created_at))))
            record_rows = ()
            if record is not None:
                spine = _lp03_spine_for_record_v1(record, sequence=operation.preparation.state_ordinal + 10 + len(attempt.observation_appends),
                                                trace_ref=operation.preparation.trace_ref)
                record_rows = ((spine.record_id, spine.effective_at.isoformat(), spine.recorded_at.isoformat(), spine.aggregate_id,
                                deterministic_json(spine)),)
            append.rows = (*record_rows, *claim_rows)
            append.refs = tuple(("receipt_records", row[0]) for row in record_rows) + tuple(("idempotency_claims", row[0]) for row in claim_rows)
            _native_require(tuple(ref for _table, ref in append.refs) == exact_ids, "LP03_PROCESS_APPEND_RESERVED_IDENTITIES_CHANGED")
            append.original = (record, append.rows, append.refs, None if record is None else deterministic_json(record))
            owner._room_v1(operation, control_bytes=sum(len(row[-1].encode("utf-8")) for row in append.rows))
            for (table, _ref), row in zip(append.refs, append.rows):
                owner._charge_v1(operation, control_bytes=len(row[-1].encode("utf-8")))
                effect("INSERT INTO " + table + " VALUES(" + ",".join("?" for _ in row) + ")", row)
            append.phase = "COMMIT_ATTEMPTED"
            effect("COMMIT")
            append.phase = "COMMITTED_PENDING_READBACK"
            append.commit_observation = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
        except BaseException:
            if sqlite3.Connection.in_transaction.__get__(connection):
                try:
                    operation.consumed["control_writes"] += 1
                    cursor = sqlite3.Connection.execute(connection, "ROLLBACK")
                    sqlite3.Cursor.close(cursor)
                    append.phase = "ROLLED_BACK"
                except BaseException:
                    append.phase = "ROLLBACK_UNPROVEN"
                    self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            elif append.phase in ("COMMIT_ATTEMPTED", "COMMITTED_PENDING_READBACK"):
                append.phase = "COMMIT_OR_OBSERVATION_UNRESOLVED"
            raise
        SQLiteReferenceAdapterV1._evidence_read_process_append_v1(self, append)
        append.phase = "COMMITTED_AND_READBACK"

    def _evidence_read_failure_audit_v1(self, audit, *, parents=False):
        """Read every original column through finite native BLOB projections."""
        from .persistence import _EvidenceAttemptFailureAuditV1, _EvidenceBoundStoreV1, _evidence_failure_row_bytes_v1
        from .receipts import _lp03_spine_from_storage_v1
        owner = _EvidenceAttemptFailureAuditV1
        _native_require(type(audit) is owner and type(parents) is bool and audit.issuer.control_store is self,
                        "LP03_FAILURE_READ_ORIGINAL_OWNER")
        owner._check_current_v1(audit)
        connection = self._connection
        if parents:
            _native_require(audit.phase == "TRANSACTION_OPEN" and sqlite3.Connection.in_transaction.__get__(connection),
                            "LP03_FAILURE_PARENT_TRANSACTION_REQUIRED")
            refs, rows, reader = audit.parent_refs, audit.parent_rows, connection
        else:
            _native_require(audit.phase == "COMMITTED_PENDING_READBACK" and audit.commit_original is not None,
                            "LP03_FAILURE_READBACK_COMMIT_REQUIRED")
            refs, rows = audit.refs, audit.rows
            reader = _EvidenceBoundStoreV1._open_independent_readback_v1(
                self._evidence_store_binding_v1, audit.issuer.host, self, audit)
        try:
            _native_require(len(refs) == len(rows), "LP03_FAILURE_READ_ROSTER")
            for (table, ref), row in zip(refs, rows, strict=True):
                _native_require(table in ("receipt_records", "idempotency_claims") and row[0] == ref,
                                "LP03_FAILURE_READ_EXACT_IDENTITY")
                columns = REFERENCE_SCHEMA_COLUMNS_V1[table]
                _native_require(len(row) == len(columns), "LP03_FAILURE_READ_EXACT_COLUMNS")
                expected = tuple(None if value is None else value.encode("utf-8") for value in row)
                projection = ",".join("length(CAST(" + column + " AS BLOB)),substr(CAST(" + column + " AS BLOB),1,?)"
                                      for column in columns)
                parameters = (*(1 if value is None else len(value) + 1 for value in expected), ref)
                owner._room_v1(audit, owner_queries=1, record_reads=1, query_result_records=1,
                              read_bytes=_evidence_failure_row_bytes_v1(row) + 20 * len(columns))
                owner._charge_v1(audit, owner_queries=1)
                sqlite3.Connection.set_trace_callback(reader, None)
                sqlite3.Connection.set_authorizer(reader, None)
                sqlite3.Connection.set_progress_handler(reader, None, 0)
                owner._check_current_v1(audit)
                _native_require(self._connection is connection and (not parents or sqlite3.Connection.in_transaction.__get__(connection)),
                                "LP03_FAILURE_READ_NATIVE_CONNECTION_CHANGED")
                cursor = sqlite3.Connection.execute(reader, "SELECT " + projection + " FROM " + table
                    + " WHERE " + columns[0] + "=?", parameters)
                try:
                    actual = sqlite3.Cursor.fetchmany(cursor, 2)
                finally:
                    sqlite3.Cursor.close(cursor)
                byte_count = sum(len(value) if type(value) is bytes else len(str(value)) if type(value) is int else 0
                                 for result in actual for value in result)
                owner._charge_v1(audit, record_reads=len(actual), query_result_records=len(actual), read_bytes=byte_count)
                target = tuple(part for value in expected for part in ((None, None) if value is None else (len(value), value)))
                _native_require(len(actual) == 1 and actual[0] == target, "LP03_FAILURE_ALL_COLUMN_READBACK_MISMATCH")
                if table == "receipt_records":
                    _lp03_spine_from_storage_v1(expected[-1], expected_record_id=ref)
        finally:
            if not parents:
                sqlite3.Connection.close(reader)
        observed = owner._check_current_v1(audit)
        if not parents:
            audit.readback_observation = (*observed, tuple(audit.registration.consumed.items()))
            audit.readback_original = (audit.readback_observation, audit.rows_original)

    def _evidence_commit_failure_audit_v1(self, audit):
        """One original integrity-only CONTROL batch, with no publication."""
        from .persistence import _EvidenceAttemptFailureAuditV1, _evidence_failure_row_bytes_v1
        from .latency_policy import _EvidenceLocalClockV1
        owner, connection = _EvidenceAttemptFailureAuditV1, self._connection
        _native_require(type(audit) is owner and audit.issuer.control_store is self and audit.phase == "PREPARED"
                        and type(connection) is sqlite3.Connection and not sqlite3.Connection.in_transaction.__get__(connection),
                        "LP03_FAILURE_COMMIT_ORIGINAL_OWNER")
        owner._check_current_v1(audit)
        _native_require(deterministic_json(audit.record) == audit.rows_original[7], "LP03_FAILURE_STATE_BODY_CHANGED")

        def effect(sql, parameters=(), *, byte_count=0):
            owner._charge_v1(audit, control_writes=1, control_bytes=byte_count)
            sqlite3.Connection.set_trace_callback(connection, None)
            sqlite3.Connection.set_authorizer(connection, None)
            sqlite3.Connection.set_progress_handler(connection, None, 0)
            owner._check_current_v1(audit)
            _native_require(self._connection is connection and audit.issuer.control_store is self,
                            "LP03_FAILURE_EFFECT_CONNECTION_CHANGED")
            if sql == "COMMIT":
                _native_require(audit.commit_attempt_original is None and audit.phase == "COMMIT_ATTEMPTED"
                                and sqlite3.Connection.in_transaction.__get__(connection), "LP03_FAILURE_COMMIT_ATTEMPT_WITNESS")
                audit.commit_attempt_original = (audit, audit.rows_original, connection)
            cursor = sqlite3.Connection.execute(connection, sql, parameters)
            sqlite3.Cursor.close(cursor)

        try:
            effect("BEGIN IMMEDIATE")
            audit.phase = "TRANSACTION_OPEN"
            SQLiteReferenceAdapterV1._evidence_read_failure_audit_v1(self, audit, parents=True)
            ids = tuple(ref for _table, ref in audit.refs)
            placeholders = ",".join("?" for _ in ids)
            for table, column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items():
                owner._room_v1(audit, owner_queries=1, record_reads=1, query_result_records=1, read_bytes=1)
                owner._charge_v1(audit, owner_queries=1)
                sqlite3.Connection.set_trace_callback(connection, None)
                sqlite3.Connection.set_authorizer(connection, None)
                sqlite3.Connection.set_progress_handler(connection, None, 0)
                owner._check_current_v1(audit)
                _native_require(self._connection is connection and sqlite3.Connection.in_transaction.__get__(connection),
                                "LP03_FAILURE_CONFLICT_CONNECTION_CHANGED")
                cursor = sqlite3.Connection.execute(connection,
                    "SELECT 1 FROM " + table + " WHERE " + column + " IN (" + placeholders + ") LIMIT 1", ids)
                try:
                    found = sqlite3.Cursor.fetchmany(cursor, 1)
                finally:
                    sqlite3.Cursor.close(cursor)
                owner._charge_v1(audit, record_reads=len(found), query_result_records=len(found), read_bytes=len(found))
                _native_require(not found, "LP03_CONTROL_CROSS_TABLE_IDENTITY_CONFLICT")
            for (table, _ref), row in zip(audit.refs, audit.rows, strict=True):
                effect("INSERT INTO " + table + " VALUES(" + ",".join("?" for _ in row) + ")", row,
                       byte_count=_evidence_failure_row_bytes_v1(row))
            _native_require(deterministic_json(audit.record) == audit.rows_original[7], "LP03_FAILURE_STATE_BODY_CHANGED")
            audit.phase = "COMMIT_ATTEMPTED"
            effect("COMMIT")
            audit.phase = "COMMITTED_PENDING_READBACK"
            audit.commit_observation = _EvidenceLocalClockV1.observe_v1(audit.issuer.clock)
            audit.commit_original = (audit.commit_observation, audit.rows_original)
        except BaseException:
            if sqlite3.Connection.in_transaction.__get__(connection):
                try:
                    # Rollback is containment of this original transaction,
                    # not another grant. Its actual attempted operation remains
                    # charged even if expiry/accounting caused the failure.
                    audit.registration.consumed["control_writes"] += 1
                    sqlite3.Connection.set_trace_callback(connection, None)
                    sqlite3.Connection.set_authorizer(connection, None)
                    sqlite3.Connection.set_progress_handler(connection, None, 0)
                    _native_require(audit.issuer.operation is audit and audit.issuer.lock._is_owned()
                                    and audit.identity_original[5] is self and self._connection is connection,
                                    "LP03_FAILURE_ROLLBACK_ORIGINAL_TRANSACTION_CHANGED")
                    cursor = sqlite3.Connection.execute(connection, "ROLLBACK")
                    sqlite3.Cursor.close(cursor)
                    audit.phase = "ROLLED_BACK"
                except BaseException:
                    audit.phase = "ROLLBACK_UNPROVEN"
                    self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            elif audit.phase in ("COMMIT_ATTEMPTED", "COMMITTED_PENDING_READBACK"):
                audit.phase = "COMMIT_OR_OBSERVATION_UNRESOLVED"
            raise
        SQLiteReferenceAdapterV1._evidence_read_failure_audit_v1(self, audit)
        audit.phase = "COMMITTED_AND_READBACK"

    def _evidence_append_reading_state_v1(self, operation):
        """Commit actual source-acquisition charges before returning any values."""
        return SQLiteReferenceAdapterV1._evidence_append_preparation_state_v1(self, operation)

    def _evidence_seal_assembly_v1(self, operation, assembly_outcome):
        from dataclasses import replace
        from .models import EvidenceAssemblyStateV1, EvidencePreparationConsumptionV1
        from .persistence import _EvidenceControlBootstrapV1
        from .receipts import _lp03_spine_for_record_v1
        from .input_lock import _require_original_input_assembly_outcome_v1
        assembly = _require_original_input_assembly_outcome_v1(operation, assembly_outcome)
        _native_require(not operation.seal_audit_reserve and operation.seal_audit_original is None,
                        "LP03_SEAL_AUDIT_ALREADY_RESERVED")
        limits = operation.grant_record.reserved_preparation_limits
        audit_id = operation.grant_record.record_id + "::STATE:" + str(operation.state_ordinal + 2)
        maximum = EvidencePreparationConsumptionV1(**{name: getattr(limits, "max_" + name) for name in operation.consumed},
                                                   aggregate_budget_ref=limits.aggregate_budget_ref)
        bound_record = replace(operation.current_state, record_id=audit_id, created_wall_ns=2**63 - 1,
            predecessor_state_ref_or_absence=operation.grant_record.record_id + "::STATE:" + str(operation.state_ordinal + 1),
            currentness_observation_ref=audit_id, state=EvidenceAssemblyStateV1.SEALED,
            input_assembly_ref_or_absence=assembly.record_id, consumed_preparation_budget=maximum)
        bound_spine = _lp03_spine_for_record_v1(bound_record, sequence=operation.state_ordinal + 4, trace_ref=operation.trace_ref)
        # Exact finite schema bound: maximum admitted counter widths, longest
        # possible 63-bit UTC projection and same original identities. The 32
        # bytes cover the changed predecessor/causation decimal ordinal widths.
        reserve = dict(owner_queries=len(REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1),
            record_reads=len(REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1), query_result_records=len(REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1),
            read_bytes=len(REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1), control_writes=4,
            control_bytes=len(deterministic_json(bound_spine).encode("utf-8")) + 32)
        _EvidenceControlBootstrapV1._room_v1(operation, **reserve)
        operation.seal_audit_reserve = reserve
        SQLiteReferenceAdapterV1._evidence_append_preparation_state_v1(self, operation, assembly_outcome=assembly_outcome)
        wall, mono, cpu = _EvidenceControlBootstrapV1._check_current_v1(operation)
        operation.seal_readback_observation = (wall, mono, cpu, tuple(operation.consumed.items()), operation.current_state.record_id)
        operation.in_seal_audit = True
        try:
            SQLiteReferenceAdapterV1._evidence_append_preparation_state_v1(self, operation, audit_tail=True)
        finally:
            operation.in_seal_audit = False

    def _evidence_append_preparation_state_v1(self, operation, *, assembly_outcome=None, audit_tail=False):
        """Closed READING or original assembly/SEALED transaction, no caller rows."""
        from dataclasses import replace
        from .models import EvidenceAssemblyStateV1
        from .input_lock import EvidenceInputAssemblyOutcomeV1, _require_original_input_assembly_outcome_v1
        from .persistence import _EvidenceControlBootstrapV1
        from .receipts import _lp03_spine_for_record_v1

        _native_require(type(operation) is _EvidenceControlBootstrapV1 and operation.issuer.control_store is self
                        and operation.commit_state == "COMMITTED_AND_READBACK" and operation.current_state is not None
                        and (operation.current_state.state is EvidenceAssemblyStateV1.SEALED if audit_tail else
                             operation.current_state.state in (EvidenceAssemblyStateV1.ADMITTED, EvidenceAssemblyStateV1.READING)),
                        "LP03_PREPARATION_NOT_READABLE")
        _native_require(type(audit_tail) is bool and (not audit_tail or (operation.in_seal_audit
                        and bool(operation.seal_audit_reserve) and operation.seal_readback_observation is not None
                        and operation.seal_audit_original is None and assembly_outcome is None)), "LP03_SEAL_AUDIT_SCOPE")
        sealing = assembly_outcome is not None
        if sealing:
            _native_require(type(assembly_outcome) is EvidenceInputAssemblyOutcomeV1
                            and operation.input_assembly_outcome is assembly_outcome
                            and assembly_outcome._operation is operation
                            and assembly_outcome._assembler is operation.issuer.assembler_context
                            and all(any(part is acquired for acquired in operation.acquired_slices)
                                    for part in assembly_outcome._slices), "LP03_ORIGINAL_ASSEMBLY_OUTCOME_REQUIRED")
            assembly = _require_original_input_assembly_outcome_v1(operation, assembly_outcome)
            _native_require(assembly.assembly_grant_ref == operation.grant_record.record_id
                            and assembly.preparation_ordinal == operation.grant_record.preparation_ordinal,
                            "LP03_ASSEMBLY_GRANT_JOIN")
        _EvidenceControlBootstrapV1._check_current_v1(operation)
        next_ordinal = operation.state_ordinal + 1
        record_id = operation.grant_record.record_id + "::STATE:" + str(next_ordinal)
        _EvidenceControlBootstrapV1._room_v1(operation, control_writes=4 if sealing else 3)
        _EvidenceControlBootstrapV1._charge_v1(operation, control_writes=4 if sealing else 3)
        prefix_bytes = operation.consumed["control_bytes"]
        if sealing:
            assembly_spine = _lp03_spine_for_record_v1(assembly, sequence=next_ordinal + 1, trace_ref=operation.trace_ref)
            assembly_wire = deterministic_json(assembly_spine)
            assembly_row = (assembly.record_id, assembly_spine.effective_at.isoformat(), assembly_spine.recorded_at.isoformat(),
                            assembly_spine.aggregate_id, assembly_wire)
        else:
            assembly_wire = ""
        connection = self._connection
        _native_require(not connection.in_transaction, "LP03_CONTROL_TRANSACTION_CONFLICT")
        sqlite3.Connection.set_trace_callback(connection, None)
        sqlite3.Connection.set_authorizer(connection, None)
        sqlite3.Connection.set_progress_handler(connection, None, 0)
        original_refs, original_bodies, original_rows = operation.readback_refs, operation.readback_bodies, operation.readback_rows
        try:
            _EvidenceControlBootstrapV1._check_current_v1(operation)
            cursor = sqlite3.Connection.execute(connection, "BEGIN IMMEDIATE")
            sqlite3.Cursor.close(cursor)
            new_ids = (record_id, assembly.record_id) if sealing else (record_id,)
            for table, column in REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1.items():
                _EvidenceControlBootstrapV1._room_v1(operation, owner_queries=1, record_reads=len(new_ids),
                                                    query_result_records=len(new_ids), read_bytes=len(new_ids))
                _EvidenceControlBootstrapV1._check_current_v1(operation)
                _EvidenceControlBootstrapV1._charge_v1(operation, owner_queries=1)
                cursor = sqlite3.Connection.execute(connection, "SELECT 1 FROM " + table + " WHERE " + column
                    + " IN (" + ",".join("?" for _ in new_ids) + ")", new_ids)
                try:
                    rows = sqlite3.Cursor.fetchmany(cursor, len(new_ids) + 1)
                finally:
                    sqlite3.Cursor.close(cursor)
                _EvidenceControlBootstrapV1._charge_v1(operation, record_reads=len(rows), query_result_records=len(rows), read_bytes=len(rows))
                _native_require(not rows, "LP03_CONTROL_CROSS_TABLE_IDENTITY_CONFLICT")
            # The persisted observation includes the actual collision queries.
            # It describes this native sample, never a future commit/readback.
            wall, _, _ = _EvidenceControlBootstrapV1._check_current_v1(operation)
            for _ in range(32):
                consumption = _EvidenceControlBootstrapV1._charge_v1(operation)
                record = replace(operation.current_state, record_id=record_id, created_wall_ns=wall,
                    causation_ref=operation.current_state.record_id, predecessor_state_ref_or_absence=operation.current_state.record_id,
                    currentness_observation_ref=record_id,
                    state=EvidenceAssemblyStateV1.SEALED if sealing or audit_tail else EvidenceAssemblyStateV1.READING,
                    input_assembly_ref_or_absence=assembly.record_id if sealing else operation.current_state.input_assembly_ref_or_absence,
                    consumed_preparation_budget=consumption)
                spine = _lp03_spine_for_record_v1(record, sequence=next_ordinal + (2 if sealing or audit_tail else 1), trace_ref=operation.trace_ref)
                wire = deterministic_json(spine)
                total = prefix_bytes + len(wire.encode("utf-8")) + len(assembly_wire.encode("utf-8"))
                if total == operation.consumed["control_bytes"]:
                    break
                operation.consumed["control_bytes"] = total
            else:
                raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "LP03_CONTROL_BYTE_SIZING_UNPROVEN")
            _EvidenceControlBootstrapV1._charge_v1(operation)
            if not audit_tail:
                _EvidenceControlBootstrapV1._room_v1(operation)
                _native_require(operation.consumed["control_bytes"] + operation.seal_audit_reserve.get("control_bytes", 0)
                                <= operation.grant_record.reserved_preparation_limits.max_control_bytes,
                                "LP03_PREPARATION_RESOURCE_EXHAUSTED")
            else:
                _native_require(len(wire.encode("utf-8")) <= operation.seal_audit_reserve["control_bytes"], "LP03_SEAL_AUDIT_SIZE_BOUND")
            row = (record_id, spine.effective_at.isoformat(), spine.recorded_at.isoformat(), spine.aggregate_id, wire)
            if sealing:
                _EvidenceControlBootstrapV1._check_current_v1(operation)
                cursor = sqlite3.Connection.execute(connection, "INSERT INTO receipt_records VALUES(?,?,?,?,?)", assembly_row)
                sqlite3.Cursor.close(cursor)
            _EvidenceControlBootstrapV1._check_current_v1(operation)
            cursor = sqlite3.Connection.execute(connection, "INSERT INTO receipt_records VALUES(?,?,?,?,?)", row)
            sqlite3.Cursor.close(cursor)
            _EvidenceControlBootstrapV1._check_current_v1(operation)
            operation.commit_state = "STATE_COMMIT_ATTEMPTED"
            cursor = sqlite3.Connection.execute(connection, "COMMIT")
            sqlite3.Cursor.close(cursor)
            if audit_tail:
                operation.commit_state = "SEALED_AUDIT_COMMITTED_PENDING_READBACK"
                operation.current_state, operation.state_ordinal = record, next_ordinal
                operation.seal_audit_original = (record, row, None)
                from .latency_policy import _EvidenceLocalClockV1
                committed_observation = _EvidenceLocalClockV1.observe_v1(operation.issuer.clock)
                operation.seal_audit_original = (record, row, committed_observation)
                # Deliberately no recursive audit read. The next separately
                # admitted phase must resolve this exact row and predecessors.
                _EvidenceControlBootstrapV1._check_current_v1(operation)
                return
            operation.commit_state = "COMMITTED_PENDING_READBACK"
            operation.readback_refs = (*original_refs[:11], ("receipt_records", record_id))
            operation.readback_bodies = (*original_bodies[:11], wire)
            operation.readback_rows = (*original_rows[:11], row)
            if sealing:
                operation.readback_refs = (*operation.readback_refs, ("receipt_records", assembly.record_id))
                operation.readback_bodies = (*operation.readback_bodies, assembly_wire)
                operation.readback_rows = (*operation.readback_rows, assembly_row)
            operation.roster_original = (operation.readback_refs, operation.readback_rows, operation.readback_bodies,
                deterministic_json((operation.readback_refs, operation.readback_rows, operation.readback_bodies)))
            SQLiteReferenceAdapterV1._evidence_bootstrap_readback_v1(self, operation)
            operation.current_state, operation.state_ordinal = record, next_ordinal
            operation.commit_state = "COMMITTED_AND_READBACK"
        except BaseException:
            if connection.in_transaction:
                operation.consumed["control_writes"] += 1
                try:
                    cursor = sqlite3.Connection.execute(connection, "ROLLBACK")
                    sqlite3.Cursor.close(cursor)
                except BaseException:
                    self._availability = PersistenceAvailabilityV1.INTEGRITY_FAILURE
            # Never restore positive currentness after a failed charge/state
            # publication, even if the earlier bootstrap remains immutable.
            operation.commit_state = "STATE_COMMIT_OR_READBACK_UNRESOLVED"
            raise

    def begin_transaction(self) -> PersistenceTransactionV1:
        _evidence_deny_legacy_store_access_v1(self)
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
        _evidence_deny_legacy_store_access_v1(self)
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
        _evidence_deny_legacy_store_access_v1(self)
        row = self._connection.execute(
            f"SELECT payload_json FROM {table} WHERE {identity_column}=?", (identity,)
        ).fetchone()
        if row is None:
            return False
        if row[0] == deterministic_json(payload):
            return True
        raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, f"conflicting duplicate {table} identity")

    def _record_exists(self, record_ref: str) -> bool:
        _evidence_deny_legacy_store_access_v1(self)
        for table in APPEND_ONLY_TABLES_V1:
            if table == "idempotency_claims":
                continue
            identity = REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1[table]
            if self._connection.execute(f"SELECT 1 FROM {table} WHERE {identity}=?", (record_ref,)).fetchone() is not None:
                return True
        return False

    def _assert_cross_table_identity_available(self, table: str, identity: str) -> None:
        _evidence_deny_legacy_store_access_v1(self)
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
        _evidence_deny_legacy_store_access_v1(self)
        if record.record_type is EconomicRecordTypeV1.LP03_EVIDENCE_CONTROL_V1:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE,
                                           "LP03_CONTROL_REQUIRES_ORIGINAL_ROLE_STORE")
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
        _evidence_deny_legacy_store_access_v1(self)
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
        _evidence_deny_legacy_store_access_v1(self)
        _source_use_record_ref_v1(record_ref)
        return self._source_use_read_v1(record_ref=record_ref, committed=True)

    def load_committed_source_use_head_v1(self, stream_id: str) -> EconomicReceiptEventSpineV1 | None:
        _evidence_deny_legacy_store_access_v1(self)
        _source_use_stream_id_v1(stream_id)
        return self._source_use_read_v1(stream_id=stream_id, committed=True)

    def load_source_use_head_for_update_v1(
        self, transaction: PersistenceTransactionV1, stream_id: str,
    ) -> EconomicReceiptEventSpineV1 | None:
        _evidence_deny_legacy_store_access_v1(self)
        _source_use_stream_id_v1(stream_id)
        tx = self._transaction(transaction)
        if type(tx) is not _SQLiteReferenceTransactionV1 or tx._adapter is not self:
            raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "source-use transaction ownership mismatch")
        return self._source_use_read_v1(stream_id=stream_id)

    def load_source_use_record_for_update_v1(
        self, transaction: PersistenceTransactionV1, record_ref: str,
    ) -> EconomicReceiptEventSpineV1 | None:
        _evidence_deny_legacy_store_access_v1(self)
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
        _evidence_deny_legacy_store_access_v1(self)
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
        _evidence_deny_legacy_store_access_v1(self)
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
        _evidence_deny_legacy_store_access_v1(self)
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
        _evidence_deny_legacy_store_access_v1(self)
        row = self._connection.execute("SELECT result.result_record_ref FROM idempotency_claims AS claim JOIN idempotency_claims AS result ON result.parent_claim_id=claim.claim_record_id WHERE claim.idempotency_key=?", (idempotency_key,)).fetchone()
        return None if row is None else row[0]

    def reconstruct_as_of(self, *, effective_cutoff: datetime, recorded_cutoff: datetime, aggregate_scope: tuple[str, ...]) -> tuple[object, ...]:
        _evidence_deny_legacy_store_access_v1(self)
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
