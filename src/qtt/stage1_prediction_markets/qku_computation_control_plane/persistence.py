"""Backend-neutral typed persistence hierarchy and deterministic memory reference."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from _thread import RLock
from typing import Mapping

from .accounting import JournalPostingV1, JournalTransactionV1, ReconciliationBreakReceiptV1
from .context import (
    _native_ident, _native_require, _public_counter_v1, _public_nanoseconds_v1, _public_refs_v1,
    parse_utc, _f14_freeze_v1, _f14_plain_v1,
)
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
    PublicDataSourceUseActionV1, PublicSourceUseOriginalV1, _public_identity_v1, _public_validate_spine_v1,
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
    AVAILABLE_PHASE_A_LOCAL_DURABLE = "AVAILABLE_PHASE_A_LOCAL_DURABLE"
    AVAILABLE_OWNER_CONTROL_EPHEMERAL = "AVAILABLE_OWNER_CONTROL_EPHEMERAL"
    UNAVAILABLE = "UNAVAILABLE"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    READ_ONLY = "READ_ONLY"


class _EvidenceBoundStoreV1:
    """Original role-file identity, not permission to read or mutate its data."""

    __control_leases_lock = RLock()
    __control_leases = {}
    __slots__ = ("__host", "__binding", "__root", "__database", "__adapter", "__native", "__handles", "__connection")

    def __init__(self, *, host_binding, binding, owned_role_root) -> None:
        from pathlib import Path
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceKeyPurposeV1, EvidenceStoreBindingV1, EvidenceStoreRoleV1

        _native_require(type(host_binding) is EvidenceHostBindingV1 and type(binding) is EvidenceStoreBindingV1,
                        "LP03_STORE_HOST_BINDING_REQUIRED")
        EvidenceHostBindingV1._assert_local_binding_v1(host_binding)
        config = host_binding.public_configuration
        _native_require(binding in config.store_bindings and binding.origin is config.origin
                        and binding.deployment_id == config.deployment_id
                        and binding.allowed_writer_principal == config.service_principal,
                        "LP03_STORE_ORIGINAL_WRITER_BINDING")
        role = binding.role
        expected = {
            EvidenceStoreRoleV1.CONTROL: ("AGENT_ORCH1", EvidenceKeyPurposeV1.EVIDENCE_ISSUER),
            EvidenceStoreRoleV1.REVIEW: ("INDEPENDENT_EVIDENCE_REVIEW", EvidenceKeyPurposeV1.INDEPENDENT_REVIEW),
            EvidenceStoreRoleV1.READINESS_ACK: ("READINESS1", EvidenceKeyPurposeV1.RECEIVER_ACCEPTANCE),
            EvidenceStoreRoleV1.PRETRADE_ACK: ("PRETRADE1", EvidenceKeyPurposeV1.RECEIVER_ACCEPTANCE),
            EvidenceStoreRoleV1.AGENT_ACK: ("AGENT_ORCH1", EvidenceKeyPurposeV1.RECEIVER_ACCEPTANCE),
            EvidenceStoreRoleV1.SVC_ACK: ("SVC1", EvidenceKeyPurposeV1.RECEIVER_ACCEPTANCE),
        }
        if role in (EvidenceStoreRoleV1.REPLAY, EvidenceStoreRoleV1.PAPER):
            _native_require(config.service_owner in ("QKU_COMPUTATION_CONTROL_PLANE", "SVC1")
                            and host_binding.signing_purpose is EvidenceKeyPurposeV1.EVIDENCE_PRODUCER,
                            "LP03_LANE_STORE_WRITER_ROLE")
        else:
            _native_require((config.service_owner, host_binding.signing_purpose) == expected[role],
                            "LP03_STORE_WRITER_ROLE")
        _native_require(type(owned_role_root) in (str, type(Path()))
                        and bool(str(owned_role_root)), "LP03_STORE_ROOT_TYPE")
        root = Path(owned_role_root)
        _native_require(root.is_absolute() and ".." not in root.parts and "." not in root.parts,
                        "LP03_STORE_ROOT_ABSOLUTE")
        self.__host = host_binding
        self.__binding = binding
        self.__root = root
        self.__database = root / (role.value.lower() + ".sqlite3")
        self.__adapter = None
        self.__connection = None
        self.__native = None
        self.__handles = []
        _EvidenceBoundStoreV1._assert_original_file_v1(self)
        try:
            _EvidenceBoundStoreV1._retain_original_objects_v1(self)
        except BaseException:
            _EvidenceBoundStoreV1._close_original_objects_v1(self)
            raise

    def __repr__(self) -> str:
        return "<LP03 original role store: access not granted>"

    def __copy__(self):
        raise TypeError("LP03 store binding cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 store binding cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 store binding cannot be serialized")

    @property
    def binding(self):
        return self.__binding

    def _database_path_for_open_v1(self):
        _native_require(self.__adapter is None, "LP03_STORE_ALREADY_ATTACHED")
        _EvidenceBoundStoreV1._assert_original_file_v1(self)
        return self.__database

    def _open_independent_readback_v1(self, host_binding, adapter, operation):
        """Separate native read-only connection while original file handles stay held."""
        import _sqlite3
        import sqlite3
        from types import BuiltinFunctionType
        from pathlib import Path

        operation_owner = _evidence_control_operation_owner_v1(operation)
        from .input_resolver import _EvidencePublishedSourceReadV1
        if type(operation) is _EvidencePublishedSourceReadV1:
            _native_require(operation.read_target is not None, "LP03_KELLY27_EXACT_CONSUMER_SOURCE_REQUIRED")
        expected_store = (operation.read_target[0] if type(operation) is _EvidencePublishedSourceReadV1 and operation.read_target is not None else
            operation.platform._store if type(operation) is _EvidenceLaneOperationV1 else
            operation.read_target[0] if type(operation) in (_EvidenceReviewOperationV1, _EvidenceReviewedConformanceOperationV1,
                _EvidenceReceiverOperationV1, _EvidenceClosedConformanceOperationV1)
                and operation.read_target is not None else
            operation.read_target[0] if type(operation) is _EvidenceConformanceOperationV1 and operation.read_target is not None
            else operation.read_target[0] if type(operation) is _EvidenceColdControlReadV1 and operation.read_target is not None
            else operation.issuer.control_store)
        _native_require(expected_store is adapter,
                        "LP03_ORIGINAL_READBACK_OPERATION_REQUIRED")
        _EvidenceBoundStoreV1._require_original_objects_v1(self, host_binding, adapter)
        _native_require(type(_sqlite3.connect) is BuiltinFunctionType, "LP03_NATIVE_SQLITE_FACTORY_REQUIRED")
        connection = _sqlite3.connect(self.__database.as_uri() + "?mode=ro", uri=True, timeout=0, isolation_level=None)
        try:
            _native_require(type(connection) is sqlite3.Connection, "LP03_NATIVE_SQLITE_READBACK_REQUIRED")
            expected_metadata_bytes = len(str(self.__database).encode("utf-8")) + 5
            operation_owner._room_v1(operation, owner_queries=1, record_reads=1,
                query_result_records=1, read_bytes=expected_metadata_bytes)
            operation_owner._check_current_v1(operation)
            operation_owner._charge_v1(operation, owner_queries=1)
            cursor = sqlite3.Connection.execute(connection, "PRAGMA database_list")
            try:
                rows = sqlite3.Cursor.fetchmany(cursor, 2)
            finally:
                sqlite3.Cursor.close(cursor)
            _native_require(len(rows) == 1 and rows[0][1] == "main" and Path(rows[0][2]) == self.__database,
                            "LP03_ORIGINAL_READBACK_DATABASE")
            operation_owner._charge_v1(operation, record_reads=1, query_result_records=1,
                read_bytes=sum(len(str(value).encode("utf-8")) for value in rows[0]))
            _EvidenceBoundStoreV1._require_original_objects_v1(self, host_binding, adapter)
        except BaseException:
            sqlite3.Connection.close(connection)
            raise
        return connection

    def _require_original_objects_v1(self, host_binding, adapter) -> None:
        """SQL-free original host/connection/file custody for final effect tails."""
        import sqlite3
        _native_require(host_binding is self.__host and adapter is self.__adapter,
                        "LP03_STORE_ORIGINAL_HOST_CUSTODY")
        _native_require(self.__connection is not None and adapter._connection is self.__connection
                        and len(self.__handles) == len(self.__root.parents) + 2
                        and adapter._availability is PersistenceAvailabilityV1.AVAILABLE_REFERENCE,
                        "LP03_STORE_CUSTODY_NOT_LIVE")
        if self.__binding.role.value == "CONTROL":
            _EvidenceBoundStoreV1._require_control_lease_v1(self)
        try:
            sqlite3.Connection.in_transaction.__get__(self.__connection)
        except sqlite3.Error as exc:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE,
                                           "LP03_STORE_NATIVE_CONNECTION_UNAVAILABLE") from exc
        _EvidenceBoundStoreV1._assert_original_file_v1(self)

    def _require_original_host_v1(self, host_binding, adapter) -> None:
        _EvidenceBoundStoreV1._require_original_objects_v1(self, host_binding, adapter)
        _EvidenceBoundStoreV1._assert_opened_database_v1(self, adapter)

    def _attach_original_adapter_v1(self, adapter) -> None:
        import sqlite3
        from .sqlite_reference import SQLiteReferenceAdapterV1

        _native_require(self.__adapter is None and type(adapter) is SQLiteReferenceAdapterV1
                        and type(adapter._connection) is sqlite3.Connection
                        and adapter.database_path == str(self.__database), "LP03_STORE_ADAPTER_IDENTITY")
        _EvidenceBoundStoreV1._assert_original_file_v1(self)
        self.__adapter = adapter

    def _assert_opened_database_v1(self, adapter) -> None:
        import sqlite3
        from pathlib import Path

        _native_require(type(adapter._connection) is sqlite3.Connection
                        and adapter.database_path == str(self.__database), "LP03_STORE_NATIVE_CONNECTION_REQUIRED")
        if self.__connection is None:
            self.__connection = adapter._connection
        _native_require(adapter._connection is self.__connection, "LP03_STORE_CONNECTION_REPLACED")
        _EvidenceBoundStoreV1._observe_original_objects_v1(self)
        try:
            cursor = sqlite3.Connection.execute(adapter._connection, "PRAGMA database_list")
            try:
                databases = sqlite3.Cursor.fetchall(cursor)
            finally:
                sqlite3.Cursor.close(cursor)
        except sqlite3.Error as exc:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE,
                                           "LP03_STORE_NATIVE_CONNECTION_UNAVAILABLE") from exc
        _native_require(len(databases) == 1 and databases[0][1] == "main"
                        and Path(databases[0][2]) == self.__database,
                        "LP03_STORE_OPENED_DATABASE_MISMATCH")

    def _close_original_database_v1(self, adapter) -> None:
        import sqlite3

        connection = self.__connection
        if connection is None:
            connection = getattr(adapter, "_connection", None)
        if connection is not None:
            _native_require(type(connection) is sqlite3.Connection, "LP03_ORIGINAL_CONNECTION_CLOSE_UNPROVEN")
            sqlite3.Connection.close(connection)
        self.__connection = None
        _EvidenceBoundStoreV1._close_original_objects_v1(self)

    def _assert_original_file_v1(self) -> None:
        import os
        import stat
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1

        EvidenceHostBindingV1._assert_local_binding_v1(self.__host)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        try:
            # Inspect every component before resolve/open. A same-ID alias is
            # still rejected when a symlink/junction or hardlink is involved.
            for component in (*reversed(self.__root.parents), self.__root):
                info = os.lstat(component)
                _native_require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode)
                                and not (getattr(info, "st_file_attributes", 0) & reparse_flag),
                                "LP03_STORE_ROOT_REDIRECTION")
            root_info = os.lstat(self.__root)
            file_info = os.lstat(self.__database)
            _native_require(stat.S_ISREG(file_info.st_mode) and not stat.S_ISLNK(file_info.st_mode)
                            and not (getattr(file_info, "st_file_attributes", 0) & reparse_flag)
                            and file_info.st_nlink == 1, "LP03_STORE_FILE_REDIRECTION")
            if (self.__root.resolve(strict=True) != self.__root
                    or (root_info.st_dev, root_info.st_ino) != self.__binding.resolved_root_identity
                    or (file_info.st_dev, file_info.st_ino) != self.__binding.database_file_identity):
                raise PersistenceContractError(ReasonCode.EVIDENCE_STORE_ISOLATION_INVALID,
                    "LP03_STORE_ORIGINAL_FILE_IDENTITY")
        except OSError as exc:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "LP03_STORE_ORIGINAL_FILE_UNAVAILABLE") from exc
        if self.__handles:
            _EvidenceBoundStoreV1._observe_original_objects_v1(self)

    def _retain_original_objects_v1(self) -> None:
        import ctypes
        import os
        import sys
        from types import SimpleNamespace

        _native_require(os.name == "nt" and sys.platform == "win32" and ctypes.sizeof(ctypes.c_void_p) == 8,
                        "LP03_NATIVE_STORE_CONTAINMENT_UNAVAILABLE")
        kernel = ctypes.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
        h, d, b = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int32
        kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, d, d, h, d, d, h]
        kernel.CreateFileW.restype = h
        kernel.CloseHandle.argtypes, kernel.CloseHandle.restype = [h], b
        kernel.GetFileType.argtypes, kernel.GetFileType.restype = [h], d
        kernel.GetFileInformationByHandleEx.argtypes = [h, b, h, d]
        kernel.GetFileInformationByHandleEx.restype = b
        kernel.GetFinalPathNameByHandleW.argtypes = [h, ctypes.c_wchar_p, d, d]
        kernel.GetFinalPathNameByHandleW.restype = d
        self.__native = SimpleNamespace(kernel=kernel, control_lease=None)
        paths = (*reversed(self.__root.parents), self.__root, self.__database)
        for path in paths:
            directory = path != self.__database
            # READ_DATA/LIST_DIRECTORY participates in sharing enforcement;
            # attributes-only opens do not prevent a rename on this host.
            # No contents are read. READ|WRITE sharing deliberately omits DELETE
            # so retained ancestors/file cannot redirect SQLite's later open.
            access = 0x80000000 if not directory and self.__binding.role.value == "CONTROL" else 0x80 | 1
            handle = kernel.CreateFileW(str(path), access, 3, None, 3,
                0x200000 | (0x2000000 if directory else 0), None)
            if handle in (None, ctypes.c_void_p(-1).value):
                raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE,
                                               "LP03_STORE_NATIVE_OBJECT_OPEN_FAILED:" + str(ctypes.get_last_error()))
            self.__handles.append((handle, path, directory))
        _EvidenceBoundStoreV1._observe_original_objects_v1(self)
        if self.__binding.role.value == "CONTROL":
            _EvidenceBoundStoreV1._lock_original_control_store_v1(self)

    def _lock_original_control_store_v1(self) -> None:
        """Hold one disjoint byte on the pinned original CONTROL file."""
        import ctypes

        _native_require(self.__binding.role.value == "CONTROL" and self.__native is not None
                        and self.__native.control_lease is None and self.__handles,
                        "LP03_CONTROL_ORIGINAL_LOCK_SCOPE")
        handle, path, directory = self.__handles[-1]
        _native_require(path == self.__database and directory is False, "LP03_CONTROL_ORIGINAL_LOCK_SCOPE")

        class Overlapped(ctypes.Structure):
            _fields_ = (("Internal", ctypes.c_size_t), ("InternalHigh", ctypes.c_size_t),
                        ("Offset", ctypes.c_uint32), ("OffsetHigh", ctypes.c_uint32), ("hEvent", ctypes.c_void_p))

        _native_require(ctypes.sizeof(Overlapped) == 32 and Overlapped.Offset.offset == 16
                        and Overlapped.OffsetHigh.offset == 20 and Overlapped.hEvent.offset == 24,
                        "LP03_CONTROL_NATIVE_LOCK_ABI")
        position = Overlapped()
        # Locking one byte at 2^60 does not extend the database. The offset
        # cannot overlap SQLite data or its own reserved locking region.
        position.OffsetHigh = 1 << 28
        native = self.__native
        identity = self.__binding.database_file_identity
        with _EvidenceBoundStoreV1.__control_leases_lock:
            lease = _EvidenceBoundStoreV1.__control_leases.get(identity)
            if lease is not None:
                _native_require(lease[2] == self.__database and self not in lease[3],
                    "LP03_CONTROL_ORIGINAL_LOCK_CUSTODY")
                lease[3].add(self)
                native.control_lease = lease
                return
            native.kernel.LockFileEx.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
                                               ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(Overlapped)]
            native.kernel.LockFileEx.restype = ctypes.c_int32
            if not native.kernel.LockFileEx(handle, 3, 0, 1, 0, ctypes.byref(position)):
                failure = ctypes.get_last_error()
                reason = ReasonCode.EVIDENCE_RUN_UNRESOLVED if failure == 33 else ReasonCode.PERSISTENCE_UNAVAILABLE
                raise PersistenceContractError(reason, "LP03_CONTROL_NATIVE_LOCK_UNAVAILABLE:" + str(failure))
            lease = (native.kernel, handle, self.__database, {self})
            _EvidenceBoundStoreV1.__control_leases[identity] = lease
            native.control_lease = lease

    def _require_control_lease_v1(self) -> None:
        with _EvidenceBoundStoreV1.__control_leases_lock:
            lease = _EvidenceBoundStoreV1.__control_leases.get(self.__binding.database_file_identity)
            _native_require(lease is not None and self.__native is not None and self.__native.control_lease is lease
                and lease[2] == self.__database and self in lease[3], "LP03_CONTROL_ORIGINAL_LOCK_CUSTODY")

    def _release_control_lease_v1(self):
        native = self.__native
        if native is None or native.control_lease is None:
            return None
        with _EvidenceBoundStoreV1.__control_leases_lock:
            _EvidenceBoundStoreV1._require_control_lease_v1(self)
            lease = native.control_lease
            if len(lease[3]) == 1:
                _native_require(lease[0].CloseHandle(lease[1]), "LP03_CONTROL_NATIVE_LOCK_CLOSE_UNPROVEN")
                del _EvidenceBoundStoreV1.__control_leases[self.__binding.database_file_identity]
            lease[3].remove(self)
            native.control_lease = None
            return lease[1]

    def _observe_original_objects_v1(self) -> None:
        # Reuse only the accepted pure native object-observation routine. No
        # source-capture root, credential, enrollment or permission is imported.
        from ...service.owner_source_use_windows import _object_state_v1

        _native_require(self.__native is not None and bool(self.__handles), "LP03_STORE_NATIVE_OBJECTS_REQUIRED")
        try:
            for handle, path, directory in self.__handles:
                observed = _object_state_v1(self.__native, handle, path, directory)
                identity = (observed[0], int.from_bytes(observed[1], "little"))
                if path == self.__root:
                    _native_require(identity == self.__binding.resolved_root_identity, "LP03_STORE_NATIVE_ROOT_IDENTITY")
                elif path == self.__database:
                    _native_require(identity == self.__binding.database_file_identity, "LP03_STORE_NATIVE_DATABASE_IDENTITY")
        except RuntimeError as exc:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "LP03_STORE_NATIVE_OBJECT_CHANGED") from exc

    def _close_original_objects_v1(self) -> None:
        if not self.__handles:
            return
        control_handle = _EvidenceBoundStoreV1._release_control_lease_v1(self)
        remaining = []
        for handle, path, directory in reversed(self.__handles):
            if handle != control_handle and not self.__native.kernel.CloseHandle(handle):
                remaining.append((handle, path, directory))
        self.__handles = list(reversed(remaining))
        _native_require(not remaining, "LP03_STORE_NATIVE_HANDLE_CLOSE_UNPROVEN")


def _evidence_assert_control_roster_v1(operation):
    """Identity of native-constructed immutable SQL rows, never a new acquisition."""
    sets = [((operation.readback_refs, operation.readback_rows, operation.readback_bodies), operation.roster_original)]
    if type(operation) is _EvidenceRegistrationOperationV1:
        sets.append(((operation.binding_readback_refs, operation.binding_readback_rows, operation.binding_readback_bodies),
                     operation.binding_roster_original))
    for values, pinned in sets:
        _native_require((pinned is None and values == ((), (), ())) or (pinned is not None
            and all(left is right for left, right in zip(values, pinned[:3]))), "LP03_ORIGINAL_CONTROL_ROSTER_CHANGED")


class _EvidenceColdControlReadV1:
    """A current issuer's exact historical read, with no grant reconstruction."""

    __slots__ = ("issuer", "current_owner", "historical_owner", "recovery_authorization",
        "record_ref", "started", "clock", "limits", "consumed", "phase", "rows", "original",
        "original_envelope", "revocation", "revocation_commit", "revocation_readback", "result", "role_stores", "read_target", "candidate_versions",
        "archive_payload", "archive_commit", "archive_readback")

    def __init__(self, *, issuer, current_owner, historical_owner):
        from ...agents.pr169_agent_orch1_resolvers import _EvidenceIssuerStateV1
        from .latency_policy import _EvidenceLocalClockV1
        from .models import EvidenceRevocationPayloadV1

        _native_require(type(issuer) is _EvidenceIssuerStateV1 and issuer.lock._is_owned()
            and issuer.operation is None and issuer.lifecycle_original is None
            and not issuer.preparations and not issuer.registrations and issuer.supervisor is None,
            "LP03_COLD_ARCHIVE_NEW_ORIGINAL_ISSUER_REQUIRED")
        config = issuer.host.public_configuration
        retained = issuer.control_store._evidence_store_binding_v1
        _native_require("EVIDENCE_COLD_CONTROL_RECONSTRUCTION_V1" in retained.binding.allowed_reader_purposes,
            "LP03_COLD_ARCHIVE_CONTROL_READER_PURPOSE")
        current = current_owner[3]
        historical = historical_owner[2]
        _native_require(any(current_owner is row for row in issuer.owner_envelopes)
            and any(historical_owner is row for row in issuer.historical_owner_envelopes)
            and (current.experiment_id, current.experiment_revision, current.protocol_ref, current.assembly_scope.generation)
                == (historical.experiment_id, historical.experiment_revision, historical.protocol_ref, config.generation)
            and current.envelope_ref != historical.envelope_ref and historical.assembly_scope.generation + 1 == config.generation,
            "LP03_COLD_ARCHIVE_ORIGINAL_OWNER_JOIN")
        self.issuer, self.current_owner, self.historical_owner = issuer, current_owner, historical_owner
        self.clock = _EvidenceLocalClockV1()
        self.started = _EvidenceLocalClockV1.observe_v1(self.clock)
        self.limits = current.assembly_scope.preparation_limits
        self.consumed = dict(record_reads=0, read_bytes=0, owner_queries=0, query_result_records=0,
            control_writes=0, control_bytes=0, cpu_ns=0, wall_ns=0)
        self.phase, self.rows = "ADMITTING", []
        self.role_stores, self.read_target = issuer.cold_role_stores, None
        self.candidate_versions = (None,None,None)
        self.archive_payload = self.archive_commit = self.archive_readback = None
        self.original_envelope = None
        self.recovery_authorization = EvidenceRevocationPayloadV1(
            target_envelope_ref=historical.envelope_ref, target_experiment_id=historical.experiment_id,
            target_generation=historical.assembly_scope.generation, new_generation=config.generation,
            exact_revocation_scope=("ASSEMBLY_GRANT", "ATTEMPT_GRANT", "REVIEW_ADMISSION", "RECEIVER_ADMISSION"),
            authenticated_reason="COLD_ORIGINAL_GENERATION_FENCED", observed_at_ns=self.started[0])
        from hashlib import sha256

        identity = deterministic_json((config.generation, historical.experiment_id, historical.experiment_revision,
            historical.envelope_ref)).encode("utf-8")
        self.record_ref = "LP03-COLD-REVOCATION::" + sha256(identity).hexdigest()
        self.revocation = self.revocation_commit = self.revocation_readback = self.result = None
        self.original = (self, issuer, issuer.lifecycle_identity, current_owner, historical_owner,
            self.clock, self.started, self.limits, self.consumed, self.rows, self.recovery_authorization,
            retained, self.record_ref)

    def _check_current_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .latency_policy import _EvidenceLocalClockV1

        issuer = self.issuer
        _native_require(type(self) is _EvidenceColdControlReadV1 and issuer.lock._is_owned()
            and issuer.operation is self and self.phase in ("ADMITTING", "READING", "RETURNING")
            and all(a is b for a,b in zip(self.original, (self, issuer, issuer.lifecycle_identity,
                self.current_owner, self.historical_owner, self.clock, self.started, self.limits,
                self.consumed, self.rows, self.recovery_authorization,
                issuer.control_store._evidence_store_binding_v1, self.record_ref), strict=True))
            and self.role_stores is issuer.cold_role_stores
            and issuer.generation == issuer.host.public_configuration.generation == self.recovery_authorization.new_generation,
            "LP03_COLD_ARCHIVE_ORIGINAL_CURRENTNESS")
        EvidenceHostBindingV1._assert_local_binding_v1(issuer.host)
        _EvidenceBoundStoreV1._require_original_objects_v1(self.original[-2], issuer.host, issuer.control_store)
        if self.read_target is not None:
            _native_require(any(self.read_target is item for item in self.role_stores), "LP03_COLD_ARCHIVE_ROLE_READ_TARGET")
            adapter, host = self.read_target
            EvidenceHostBindingV1._assert_local_binding_v1(host)
            _EvidenceBoundStoreV1._require_original_objects_v1(adapter._evidence_store_binding_v1,host,adapter)
        when = _EvidenceLocalClockV1.observe_v1(self.clock)
        current = self.current_owner[3]
        _native_require(current.envelope_ref not in issuer.cancelled_envelopes
            and self.started[0] <= when[0] < min(current.exclusive_expiry_wall_ns, current.assembly_scope.exclusive_expiry_wall_ns)
            and all(before <= after for before,after in zip(self.started,when,strict=True)),
            "LP03_COLD_ARCHIVE_CURRENT_OWNER_EXPIRY")
        self.consumed["wall_ns"] = when[1] - self.started[1]
        self.consumed["cpu_ns"] = when[2] - self.started[2]
        _EvidenceColdControlReadV1._room_v1(self)
        return when

    def _room_v1(self, **maximums):
        _native_require(all(key in self.consumed and type(value) is int and value >= 0 for key,value in maximums.items())
            and all(amount + maximums.get(key, 0) <= getattr(self.limits, "max_"+key)
                for key,amount in self.consumed.items()), "LP03_COLD_ARCHIVE_RESOURCE_EXHAUSTED")

    def _charge_v1(self, **increments):
        _native_require(all(key in self.consumed and type(value) is int and value >= 0 for key,value in increments.items()),
            "LP03_COLD_ARCHIVE_CHARGE_TYPE")
        for key, amount in increments.items():
            self.consumed[key] += amount
        _EvidenceColdControlReadV1._room_v1(self)

    def _retain_v1(self, row):
        _EvidenceColdControlReadV1._check_current_v1(self)
        table, record, raw = row
        _native_require(table in ("idempotency_claims", "receipt_records") and type(raw) is bytes
            and 0 < len(raw) <= 1_048_576, "LP03_COLD_ARCHIVE_ORIGINAL_ROW")
        existing = tuple(item for item in self.rows if item[:2] == (table,record))
        _native_require(not existing or existing == (row,), "LP03_COLD_ARCHIVE_ORIGINAL_ROW_CHANGED")
        if not existing:
            self.rows.append(row)

    def _verify_historical_grant_v1(self, grant):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import (EvidenceAssemblyGrantRecordV1, EvidenceAttemptGrantRecordV1,
            EvidenceAuthorizationMessageV1, EvidenceMessageKindV1)
        from .serialization import _evidence_canonical_object_v1

        envelope = self.original_envelope
        _native_require(type(grant) in (EvidenceAssemblyGrantRecordV1, EvidenceAttemptGrantRecordV1)
            and grant.generation == envelope.assembly_scope.generation and grant.producing_principal == envelope.issuer_principal,
            "LP03_COLD_ARCHIVE_ORIGINAL_GRANT_SCOPE")
        if type(grant) is EvidenceAssemblyGrantRecordV1:
            expected_kind = EvidenceMessageKindV1.ASSEMBLY_GRANT
            audience = envelope.assembly_scope.assembler_audience
        else:
            expected_kind = EvidenceMessageKindV1.ATTEMPT_GRANT
            signed_body = EvidenceAuthorizationMessageV1.from_canonical_mapping(
                _evidence_canonical_object_v1(grant.signed_grant.canonical_message.encode("utf-8")))
            audience = signed_body.audience
        _EvidenceColdControlReadV1._verify_original_envelope_v1(self, original_wall_ns=grant.created_wall_ns)
        return EvidenceHostBindingV1._verify_cold_historical_message_v1(self.issuer.host, grant.signed_grant,
            archive=self, kind=expected_kind, issuer=envelope.issuer_principal, subject=grant.record_id,
            audience=audience, generation=grant.generation, original_wall_ns=grant.created_wall_ns)

    def _verify_original_envelope_v1(self, *, original_wall_ns):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceMessageKindV1

        original_signed, original_message, original_envelope = self.historical_owner
        verified_message, verified_envelope = EvidenceHostBindingV1._verify_cold_historical_message_v1(
            self.issuer.host, original_signed, archive=self, kind=EvidenceMessageKindV1.OWNER_ENVELOPE,
            issuer=original_message.issuer, subject=original_envelope.envelope_ref,
            audience=self.issuer.host.public_configuration.service_principal,
            generation=original_message.generation, original_wall_ns=original_wall_ns)
        _native_require(verified_message == original_message and verified_envelope == original_envelope,
            "LP03_COLD_ARCHIVE_ORIGINAL_OWNER_SIGNATURE_CHANGED")
        return verified_envelope

    def _build_revocation_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceAbsenceV1, EvidenceKeyPurposeV1, EvidenceMessageKindV1, EvidenceRevocationRecordV1
        from .serialization import _evidence_canonical_object_v1

        _native_require(self.phase == "ADMITTING" and self.revocation is None and self.original_envelope is not None,
            "LP03_COLD_ARCHIVE_ADMISSION_PHASE")
        archive = self.recovery_authorization
        config = self.issuer.host.public_configuration
        current = self.current_owner[3]
        _EvidenceColdControlReadV1._check_current_v1(self)
        issuer_keys = tuple(key for key in config.verification_keys if key.principal == config.service_principal
            and key.purpose is EvidenceKeyPurposeV1.EVIDENCE_ISSUER and type(key.revocation_record_ref_or_absence) is EvidenceAbsenceV1
            and key.valid_from_wall_ns <= archive.observed_at_ns < key.exclusive_expiry_wall_ns)
        _native_require(len(issuer_keys) == 1, "LP03_COLD_ARCHIVE_CURRENT_ISSUER_KEY")
        expiry = min(current.exclusive_expiry_wall_ns, current.assembly_scope.exclusive_expiry_wall_ns,
            issuer_keys[0].exclusive_expiry_wall_ns)
        signed = EvidenceHostBindingV1._sign_message_v1(self.issuer.host, kind=EvidenceMessageKindV1.REVOCATION,
            subject=self.record_ref, audience="CP/sqlite_reference.py::recover_evidence_control_lifecycle_v1",
            generation=archive.new_generation,
            valid_from_wall_ns=archive.observed_at_ns, exclusive_expiry_wall_ns=expiry,
            payload=_evidence_canonical_object_v1(deterministic_json(archive).encode("utf-8")))
        return EvidenceRevocationRecordV1(record_id=self.record_ref, schema_version="1.0", origin=config.origin,
            experiment_id=current.experiment_id, experiment_revision=current.experiment_revision,
            protocol_ref=current.protocol_ref, input_lock_ref=EvidenceAbsenceV1("NOT_YET_BOUND_BEFORE_EXECUTION"),
            scenario_plan_ref="LP03-CONTROL-LIFECYCLE:ROOT", causation_ref=archive.target_envelope_ref,
            correlation_ref=self.issuer.lifecycle_identity[3], producing_owner="AGENT_ORCH1", producing_principal=config.service_principal,
            source_lineage_refs=(archive.target_envelope_ref, current.envelope_ref),
            created_wall_ns=archive.observed_at_ns, clock_domain_id=self.clock.clock_domain_id,
            generation=config.generation, no_order_authority=True, no_provider_effect=True, no_model_fit=True,
            no_llm_execution=True, no_qpu_execution=True, target_envelope_ref=archive.target_envelope_ref,
            target_experiment_id=archive.target_experiment_id, target_generation=archive.target_generation,
            new_generation=archive.new_generation, exact_revocation_scope=archive.exact_revocation_scope,
            authenticated_reason=archive.authenticated_reason, observed_at_ns=archive.observed_at_ns, issuer_signature=signed)

    def _run_v1(self):
        from hashlib import sha256
        from .models import EvidencePreparationConsumptionV1
        from .serialization import _evidence_frozen_data_v1, _evidence_canonical_object_v1
        from .sqlite_reference import SQLiteReferenceAdapterV1

        issuer = self.issuer
        _native_require(type(self) is _EvidenceColdControlReadV1 and issuer.lock._is_owned() and issuer.operation is None,
            "LP03_COLD_ARCHIVE_ORIGINAL_ISSUER_REQUIRED")
        issuer.operation = self
        try:
            _EvidenceColdControlReadV1._check_current_v1(self)
            self.original_envelope = _EvidenceColdControlReadV1._verify_original_envelope_v1(self,
                original_wall_ns=self.historical_owner[1].valid_from_wall_ns)
            self.revocation = _EvidenceColdControlReadV1._build_revocation_v1(self)
            SQLiteReferenceAdapterV1._evidence_commit_cold_revocation_v1(issuer.control_store,self)
            _native_require(self.revocation_commit is not None and self.revocation_readback is not None,
                "LP03_COLD_ARCHIVE_ORIGINAL_REVOCATION_READBACK")
            self.phase = "READING"
            _, grant, lanes, disposition, raw, _ = SQLiteReferenceAdapterV1._evidence_read_cold_control_roster_v1(
                issuer.control_store,self)
            publications = []
            for lane in lanes:
                for target in self.role_stores:
                    adapter, host = target
                    if len(lane) <= 2 or adapter._evidence_store_binding_v1.binding.role.value != lane[0]:
                        continue
                    self.read_target = target
                    try:
                        name, state, pointer, parents = SQLiteReferenceAdapterV1._evidence_read_cold_lane_publication_v1(adapter,self,lane)
                    finally:
                        self.read_target = None
                    publications.append(dict(lane=name, disposition=state, original_pointer=pointer,
                        original_parent_bytes=tuple((store,table,ref,len(wire),sha256(wire).hexdigest())
                            for store,table,ref,wire in parents)))
            review_proof = None
            if self.candidate_versions[0] is not None:
                for target in self.role_stores:
                    adapter, _host = target
                    if adapter._evidence_store_binding_v1.binding.role.value != "REVIEW":
                        continue
                    self.read_target = target
                    try:
                        returned = SQLiteReferenceAdapterV1._evidence_read_cold_review_v1(adapter,self)
                    finally:
                        self.read_target = None
                    if returned is not None:
                        record, wire = returned
                        review_proof = dict(original_signed_review_ref=record.record_id, exact_original_bytes=len(wire),
                            exact_original_sha256=sha256(wire).hexdigest(), original_review_decision=record.decision)
            self.phase = "RETURNING"
            observed = _EvidenceColdControlReadV1._check_current_v1(self)
            report = dict(disposition=disposition, original_assembly_grant_ref=grant.record_id,
                original_lanes=tuple(row[:2] for row in lanes), current_publication_readbacks=tuple(publications),
                original_conformance_roster=tuple(record.record_id for record in self.candidate_versions if record is not None),
                original_signed_review_readback=review_proof,
                revocation=self.revocation,
                revocation_commit_observation=self.revocation_commit, revocation_readback_observation=self.revocation_readback,
                archive_observation=observed, current_clock_domain=self.clock.clock_domain_id,
                selected_control_records=tuple((table,ref,len(wire),sha256(wire).hexdigest()) for table,ref,wire in raw),
                selected_consumed=EvidencePreparationConsumptionV1(**self.consumed, aggregate_budget_ref=self.limits.aggregate_budget_ref))
            report_bytes = deterministic_json(report).encode("utf-8")
            self.archive_payload = _evidence_frozen_data_v1(_evidence_canonical_object_v1(report_bytes, max_bytes=131072))
            ref, size, digest = SQLiteReferenceAdapterV1._evidence_commit_cold_reconstruction_v1(issuer.control_store,self)
            _native_require(self.archive_commit is not None and self.archive_readback is not None
                and len(report_bytes)==size and sha256(report_bytes).hexdigest()==digest,
                "LP03_COLD_ARCHIVE_ORIGINAL_DURABLE_RESULT")
            final = _EvidenceColdControlReadV1._check_current_v1(self)
            return dict(report, durable_archive_result=dict(record_ref=ref, bytes=size, sha256=digest),
                durable_archive_commit=self.archive_commit, durable_archive_readback=self.archive_readback,
                final_archive_observation=final, final_archive_consumed=EvidencePreparationConsumptionV1(
                    **self.consumed, aggregate_budget_ref=self.limits.aggregate_budget_ref))
        finally:
            issuer.operation = None
            if self.revocation_commit is not None or self.phase == "COMMIT_UNPROVEN":
                issuer.lifecycle_unresolved = True

    def _finish_read_v1(self, lifecycle, grant, lanes, disposition):
        # This remains internal historical custody, even when terminal and publication evidence exist.
        _native_require(self.phase == "READING" and self.revocation_readback is not None and self.result is None,
            "LP03_COLD_ARCHIVE_ORIGINAL_READ_PHASE")
        observation = _EvidenceColdControlReadV1._check_current_v1(self)
        self.result = (lifecycle, grant, lanes, disposition, tuple(self.rows), observation)
        return self.result


class _EvidenceControlBootstrapV1:
    """One exact issuer-owned bootstrap operation, never a generic SQL permit."""

    __slots__ = ("issuer", "envelope_entry", "request", "plan", "grant_record", "trace_ref",
                 "policies", "started_cpu_ns", "consumed", "commit_state", "readback_refs", "readback_bodies",
                 "readback_rows", "current_state", "state_ordinal", "source_read_capabilities", "acquired_slices",
                 "input_assembly_outcome", "input_assembly_members", "seal_audit_reserve", "in_seal_audit",
                 "seal_readback_observation", "seal_audit_original", "roster_original", "bootstrap_original",
                 "bootstrap_commit_observation", "bootstrap_readback_observation", "lifecycle_rows",
                 "lifecycle_identity_original", "bootstrap_write_witness", "bootstrap_commit_witness", "bootstrap_readback_witness",
                 "bootstrap_clock_original", "failure_root", "failure_secondary", "failure_observation", "rollback_state",
                 "failure_accounting_original", "failure_accounting_state", "failure_clock_observation",
                 "failure_capture_failed", "failure_unretained", "source_slice_originals", "source_slice_minted",
                 "source_slice_guard", "registration_source_original", "registration_numerical_original")

    def __init__(self, *, issuer, envelope_entry, request, plan, grant_record, trace_ref, policies, started_cpu_ns,
                 lifecycle_identity):
        from ...agents.pr169_agent_orch1_resolvers import _EvidenceIssuerStateV1
        from .models import EvidenceAssemblyRequestV1, EvidenceAssemblyGrantRecordV1, EvidenceScenarioPlanV1
        _native_require(type(issuer) is _EvidenceIssuerStateV1 and issuer.operation is None
                        and issuer.lock._is_owned() and type(request) is EvidenceAssemblyRequestV1
                        and type(plan) is EvidenceScenarioPlanV1 and type(grant_record) is EvidenceAssemblyGrantRecordV1,
                        "LP03_CONTROL_BOOTSTRAP_OWNER_REQUIRED")
        self.issuer, self.envelope_entry, self.request = issuer, envelope_entry, request
        _native_require(envelope_entry[3].assembly_scope.source_purpose
                        in issuer.control_store._evidence_store_binding_v1.binding.allowed_reader_purposes,
                        "LP03_CONTROL_READER_PURPOSE_DENIED")
        self.plan, self.grant_record, self.trace_ref, self.policies = plan, grant_record, trace_ref, policies
        self.started_cpu_ns = started_cpu_ns
        self.consumed = dict(record_reads=0, read_bytes=0, owner_queries=0,
                             query_result_records=0,
                             control_writes=0, control_bytes=0, cpu_ns=0, wall_ns=0)
        self.commit_state, self.readback_refs, self.readback_bodies = "NOT_STARTED", (), ()
        self.readback_rows = ()
        self.roster_original = None
        self.bootstrap_original = self.bootstrap_commit_observation = self.bootstrap_readback_observation = None
        self.lifecycle_rows = ()
        _native_require(lifecycle_identity is issuer.lifecycle_identity, "LP03_CONTROL_LIFECYCLE_IDENTITY_CHANGED")
        self.lifecycle_identity_original = lifecycle_identity
        self.bootstrap_write_witness = self.bootstrap_commit_witness = self.bootstrap_readback_witness = None
        self.bootstrap_clock_original = issuer.clock
        self.failure_root, self.failure_observation = None, None
        self.failure_secondary, self.rollback_state = [], "NOT_ENTERED"
        self.failure_accounting_original = (issuer.clock, grant_record.deadline_clock_and_process, started_cpu_ns, self.consumed)
        self.failure_accounting_state = "NOT_OBSERVED"
        self.failure_clock_observation = self.failure_unretained = None
        self.failure_capture_failed = False
        self.current_state, self.state_ordinal = None, 0
        self.source_read_capabilities, self.acquired_slices = (), ()
        self.source_slice_originals = ()
        self.source_slice_minted = (self, [])
        from .input_resolver import _bind_evidence_source_acquisition_guard_v1
        self.source_slice_guard = _bind_evidence_source_acquisition_guard_v1(self)
        self.registration_source_original = None
        self.registration_numerical_original = None
        self.input_assembly_outcome = None
        self.input_assembly_members = None
        self.seal_audit_reserve, self.in_seal_audit = {}, False
        self.seal_readback_observation, self.seal_audit_original = None, None

    def __copy__(self):
        raise TypeError("LP03 bootstrap operation cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 bootstrap operation cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 bootstrap operation cannot be serialized")

    def _charge_v1(self, **increments):
        from .models import EvidencePreparationConsumptionV1
        limits = self.grant_record.reserved_preparation_limits
        for name, amount in increments.items():
            _native_require(name in self.consumed and type(amount) is int and amount >= 0, "LP03_PREPARATION_CHARGE_TYPE")
            self.consumed[name] += amount
        # Consumed attempts remain retained even when a limit is exceeded.
        for name, value in self.consumed.items():
            _native_require(value <= getattr(limits, "max_" + name), "LP03_PREPARATION_RESOURCE_EXHAUSTED")
        return EvidencePreparationConsumptionV1(**self.consumed, aggregate_budget_ref=limits.aggregate_budget_ref)

    def _room_v1(self, **upper_bounds):
        """Check a finite acquisition before invoking its original owner."""
        limits = self.grant_record.reserved_preparation_limits
        for name, amount in upper_bounds.items():
            _native_require(name in self.consumed and type(amount) is int and amount >= 0,
                            "LP03_PREPARATION_CHARGE_TYPE")
            reserve = 0 if self.in_seal_audit else self.seal_audit_reserve.get(name, 0)
            _native_require(self.consumed[name] + amount + reserve <= getattr(limits, "max_" + name),
                            "LP03_PREPARATION_RESOURCE_EXHAUSTED")

    def _check_current_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import _EvidenceIssuerStateV1
        _native_require(type(self) is _EvidenceControlBootstrapV1 and self.issuer.operation is self
                        and self.issuer.lock._is_owned(), "LP03_CONTROL_OPERATION_NOT_ORIGINAL")
        _evidence_assert_control_roster_v1(self)
        _EvidenceControlBootstrapV1._assert_lifecycle_witnesses_v1(self)
        wall, mono, cpu = _EvidenceIssuerStateV1._bootstrap_current_v1(self.issuer, self)
        _evidence_assert_control_roster_v1(self)
        _EvidenceControlBootstrapV1._assert_lifecycle_witnesses_v1(self)
        self.consumed["wall_ns"] = mono - self.grant_record.deadline_clock_and_process.admitted_monotonic_ns
        self.consumed["cpu_ns"] = cpu - self.started_cpu_ns
        _EvidenceControlBootstrapV1._charge_v1(self)
        return wall, mono, cpu

    def _assert_lifecycle_witnesses_v1(self):
        """Each first boundary retains its predecessors before another observation."""
        _native_require(self.issuer.lifecycle_identity is self.lifecycle_identity_original,
                        "LP03_CONTROL_LIFECYCLE_IDENTITY_CHANGED")
        written, committed, readback = self.bootstrap_write_witness, self.bootstrap_commit_witness, self.bootstrap_readback_witness
        _native_require((written is None and self.bootstrap_original is None and self.lifecycle_rows == ())
                        or (type(written) is tuple and len(written) == 4 and written[0] is self
                            and written[1] is self.lifecycle_identity_original and written[2] is self.lifecycle_rows
                            and written[3] is self.bootstrap_original), "LP03_CONTROL_LIFECYCLE_WRITE_WITNESS_CHANGED")
        _native_require((committed is None and self.bootstrap_commit_observation is None)
                        or (type(committed) is tuple and len(committed) == 2 and committed[0] is written
                            and committed[1] is self.bootstrap_commit_observation),
                        "LP03_CONTROL_LIFECYCLE_COMMIT_WITNESS_CHANGED")
        _native_require((readback is None and self.bootstrap_readback_observation is None)
                        or (type(readback) is tuple and len(readback) == 2 and readback[0] is committed
                            and readback[1] is self.bootstrap_readback_observation),
                        "LP03_CONTROL_LIFECYCLE_READBACK_WITNESS_CHANGED")

    def _observe_failure_accounting_v1(self):
        """Nonpositive accounting uses the original clock, not renewed authority."""
        from .latency_policy import _EvidenceLocalClockV1
        self.failure_accounting_state = "OBSERVATION_UNRESOLVED"
        try:
            original = self.failure_accounting_original
            clock, deadline, started_cpu, consumed = original
            _native_require(clock is self.bootstrap_clock_original and deadline is self.grant_record.deadline_clock_and_process
                            and started_cpu == self.started_cpu_ns and consumed is self.consumed
                            and type(consumed) is dict and len(consumed) == 8
                            and all(type(value) is int and value >= 0 for value in consumed.values()),
                            "LP03_BOOTSTRAP_FAILURE_ACCOUNTING_CHANGED")
            before = tuple(consumed.items())
            observed = _EvidenceLocalClockV1.observe_v1(clock)
            self.failure_clock_observation = observed
            _native_require(self.failure_accounting_original is original and consumed is self.consumed
                            and clock is self.bootstrap_clock_original and deadline is self.grant_record.deadline_clock_and_process
                            and started_cpu == self.started_cpu_ns and tuple(consumed.items()) == before,
                            "LP03_BOOTSTRAP_FAILURE_ACCOUNTING_CHANGED")
            _native_require(observed[1] - deadline.admitted_monotonic_ns >= consumed["wall_ns"]
                            and observed[2] - started_cpu >= consumed["cpu_ns"],
                            "LP03_BOOTSTRAP_FAILURE_CLOCK_ORDER")
            consumed["wall_ns"] = observed[1] - deadline.admitted_monotonic_ns
            consumed["cpu_ns"] = observed[2] - started_cpu
            self.failure_observation = (*observed, tuple(consumed.items()))
        except BaseException as error:
            _EvidenceControlBootstrapV1._retain_failure_secondary_v1(self, "FINAL_ACCOUNTING", error)
            return
        self.failure_accounting_state = "OBSERVED_THROUGH_NATIVE_SAMPLE"
        try:
            _EvidenceControlBootstrapV1._charge_v1(self)
        except BaseException as error:
            self.failure_accounting_state = "OBSERVED_BUDGET_UNPROVEN"
            _EvidenceControlBootstrapV1._retain_failure_secondary_v1(self, "FINAL_BUDGET", error)

    def _retain_failure_secondary_v1(self, stage, error):
        # Retain the actual secondary before attempting diagnostic allocation.
        # Failure of that allocation cannot turn cleanup into a positive result.
        previous = self.failure_unretained
        if previous is None:
            self.failure_unretained = error
        try:
            list.append(self.failure_secondary, (stage, error))
        except BaseException:
            self.failure_capture_failed = True
        else:
            if previous is None or previous is error:
                self.failure_unretained = None


class _EvidenceRegistrationOperationV1:
    """Fresh original-envelope control admission, never an assembly-grant renewal."""

    __slots__ = ("issuer", "preparation", "envelope_entry", "request", "policies", "deadline", "started_cpu_ns",
                 "consumed", "commit_state", "readback_refs", "readback_bodies", "readback_rows", "records", "handle",
                 "parent_readback_observation", "protocol", "policy_slices", "registration_policy", "commit_observation",
                 "readback_observation", "resolved_policy_original", "compiler", "compilation_request", "compilation",
                 "binding_record", "binding_spines", "binding_state", "binding_readback_refs", "binding_readback_rows",
                 "binding_readback_bodies", "binding_commit_observation", "binding_readback_observation", "binding_original",
                 "attempts", "active_attempt", "accounting_observation_state", "active_lane_operation",
                 "roster_original", "binding_roster_original", "retained_reservations", "conformance_operation",
                 "review_operation", "active_review_operation", "reviewed_conformance_operation", "closed_conformance_operation",
                 "receiver_operations", "receiver_reservations", "active_receiver_operation", "source_slice_originals", "source_slice_minted",
                 "policy_source_originals", "source_slice_guard", "numerical_work", "numerical_original", "review_numerical_original")

    def __init__(self, *, issuer, preparation, request):
        from ...agents.pr169_agent_orch1_resolvers import _EvidenceIssuerStateV1
        from .latency_policy import _EvidenceLocalClockV1
        from .models import EvidenceProcessDeadlineV1, EvidenceRegistrationRequestV1
        _native_require(type(issuer) is _EvidenceIssuerStateV1
                        and type(preparation) is _EvidenceControlBootstrapV1 and preparation.issuer is issuer
                        and type(request) is EvidenceRegistrationRequestV1, "LP03_REGISTRATION_ORIGINAL_CONTEXT")
        _wall, mono, cpu = _EvidenceLocalClockV1.observe_v1(issuer.clock)
        with issuer.lock:
            _native_require(issuer.operation is None, "LP03_CONTROL_OPERATION_REENTRY")
            key = preparation.grant_record.record_id
            original = issuer.preparations.get(key)
            _native_require(original is not None and original[0] is preparation and key not in issuer.registrations,
                            "LP03_REGISTRATION_ALREADY_RESERVED_OR_UNRESOLVED")
            self.issuer, self.preparation, self.envelope_entry, self.request = issuer, preparation, preparation.envelope_entry, request
            self.policies = preparation.policies
            self.deadline = None
            self.started_cpu_ns = cpu
            self.consumed = dict(record_reads=0, read_bytes=0, owner_queries=0, query_result_records=0,
                                 control_writes=0, control_bytes=0, cpu_ns=0, wall_ns=0)
            self.commit_state = "ADMISSION_VALIDATING"
            self.readback_refs, self.readback_bodies, self.readback_rows, self.records = (), (), (), ()
            self.handle = None
            self.parent_readback_observation = self.protocol = self.registration_policy = None
            self.policy_slices = ()
            self.policy_source_originals = ()
            self.source_slice_originals = ()
            self.source_slice_minted = (self, [])
            from .input_resolver import _bind_evidence_source_acquisition_guard_v1
            self.source_slice_guard = _bind_evidence_source_acquisition_guard_v1(self)
            self.commit_observation = self.readback_observation = None
            self.resolved_policy_original = None
            self.numerical_work = None
            self.numerical_original = (self, "ABSENT", None)
            self.compiler = self.compilation_request = self.compilation = self.binding_record = None
            self.binding_spines = self.binding_readback_refs = self.binding_readback_rows = self.binding_readback_bodies = ()
            self.binding_state = "NOT_STARTED"
            self.binding_commit_observation = self.binding_readback_observation = self.binding_original = None
            self.attempts, self.active_attempt = {}, None
            self.active_lane_operation = None
            self.roster_original = self.binding_roster_original = None
            self.retained_reservations = ()
            self.conformance_operation = None
            self.review_operation = self.active_review_operation = self.reviewed_conformance_operation = None
            self.review_numerical_original = None
            self.receiver_operations, self.receiver_reservations, self.active_receiver_operation = {}, (), None
            self.closed_conformance_operation = None
            self.accounting_observation_state = "OBSERVED"
            # Latch the original attempt before any substantive original-body
            # validation. Construction failure cannot reset work through a new key.
            preparation.registration_source_original = (self, (self.source_slice_minted, self.source_slice_guard))
            preparation.registration_numerical_original = self.numerical_original
            issuer.registrations[key] = self
            try:
                envelope = preparation.envelope_entry[3]
                self.deadline = EvidenceProcessDeadlineV1(clock_domain_id=issuer.clock.clock_domain_id,
                    process_identity_ref=issuer.clock.process_identity_ref, boot_identity_ref=issuer.clock.boot_identity_ref,
                    admitted_monotonic_ns=mono, exclusive_deadline_monotonic_ns=mono + envelope.aggregate_execution_limits.max_wall_ns)
                _native_require(preparation.commit_state == "SEALED_AUDIT_COMMITTED_PENDING_READBACK"
                                and preparation.seal_audit_original is not None and preparation.seal_audit_original[2] is not None,
                                "LP03_REGISTRATION_SEAL_CUSTODY_UNRESOLVED")
                _native_require((request.input_assembly_ref.store_id, request.input_assembly_ref.record_id)
                                == (envelope.assembly_scope.control_store_id, preparation.input_assembly_members[3].record_id),
                                "LP03_REGISTRATION_ORIGINAL_ASSEMBLY_JOIN")
                _native_require("EVIDENCE_EXPERIMENT_REGISTRATION_V1"
                                in issuer.control_store._evidence_store_binding_v1.binding.allowed_reader_purposes,
                                "LP03_REGISTRATION_CONTROL_PURPOSE_DENIED")
                # Canonical proposal validation belongs after current registration
                # source/consumer admission and charged exact parent readback. This
                # constructor neither serializes nor exposes the old snapshot.
                self.commit_state = "NOT_STARTED"
            except BaseException:
                self.commit_state = "ADMISSION_FAILED_REQUIRES_AUDIT"
                raise
            finally:
                try:
                    _wall, observed_mono, observed_cpu = _EvidenceLocalClockV1.observe_v1(issuer.clock)
                except BaseException:
                    self.commit_state = "ADMISSION_CLOCK_CUSTODY_UNAVAILABLE"
                    raise
                self.consumed["wall_ns"], self.consumed["cpu_ns"] = observed_mono - mono, observed_cpu - cpu

    def __copy__(self):
        raise TypeError("LP03 registration operation cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 registration operation cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 registration operation cannot be serialized")

    def _room_v1(self, *, retained_attempt=None, **increments):
        totals = dict(self.consumed)
        reserved = _EvidenceRegistrationOperationV1._retained_capacity_v1(self, prospective=retained_attempt)
        for name, value in increments.items():
            _native_require(name in totals and type(value) is int and value >= 0, "LP03_REGISTRATION_CHARGE_TYPE")
            totals[name] += value
        limits = self.envelope_entry[3].aggregate_execution_limits
        _native_require(totals["record_reads"] + reserved["max_input_reads"] <= limits.max_input_reads
                        and totals["query_result_records"] + reserved["max_input_reads"] <= limits.max_input_reads
                        and totals["read_bytes"] + reserved["max_input_bytes"] <= limits.max_input_bytes
                        and totals["owner_queries"] + totals["control_writes"] + reserved["max_persistent_operations"] <= limits.max_persistent_operations
                        and totals["control_bytes"] + reserved["max_persistent_bytes"] <= limits.max_persistent_bytes
                        and totals["cpu_ns"] + reserved["max_cpu_ns"] <= limits.max_cpu_ns
                        and totals["wall_ns"] + reserved["max_wall_ns"] <= limits.max_wall_ns, "LP03_REGISTRATION_RESOURCE_EXHAUSTED")
        if self.active_attempt is not None:
            _EvidenceAttemptOperationV1._check_room_v1(self.active_attempt, totals)
        if self.active_review_operation is not None:
            _EvidenceReviewOperationV1._check_room_v1(self.active_review_operation, totals)
        if self.active_receiver_operation is not None:
            _EvidenceReceiverOperationV1._check_room_v1(self.active_receiver_operation, totals)
        if self.issuer.supervisor is not None:
            from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
            usage = EvidenceProcessSupervisorV1._execution_usage_v1(self.issuer.supervisor, self)
            _native_require(all(usage[name] + reserved.get(limit, 0) <= getattr(limits, limit) for name, limit in (
                ("process_memory_high_water_bytes", "max_process_memory_bytes"), ("job_memory_high_water_bytes", "max_job_memory_bytes"),
                ("events", "max_events"), ("callbacks", "max_callbacks"), ("coordinates", "max_coordinates"),
                ("computations", "max_computations"), ("output_bytes", "max_output_bytes"),
                ("active_workers", "max_concurrency"))), "LP03_REGISTRATION_EXECUTION_RESOURCE_EXHAUSTED")

    def _retained_capacity_v1(self, *, prospective=None):
        """Conservative encumbrances stay separate from actual measurements."""
        names = ("max_wall_ns", "max_cpu_ns", "max_input_reads", "max_input_bytes", "max_persistent_operations",
                 "max_persistent_bytes", "max_events", "max_callbacks", "max_coordinates", "max_computations", "max_output_bytes")
        result = dict.fromkeys(names, 0)
        completed = tuple(attempt for attempt in self.attempts.values()
                          if attempt.phase in ("COLLECTION_COMPLETE_RESERVED", "FAILURE_AUDITED_RESERVED"))
        _native_require(len(completed) == len(self.retained_reservations)
                        and len({id(attempt) for attempt in completed}) == len(completed)
                        and all(entry[0] is attempt for entry, attempt in zip(self.retained_reservations, completed)),
                        "LP03_RETAINED_RESERVATION_ROSTER_CHANGED")
        for attempt, limits, roster, proof in self.retained_reservations:
            _native_require(attempt.registration is self
                            and limits is attempt.original[5] is attempt.limits is attempt.payload.budgets
                            and roster is attempt.roster_original and len(roster[0]) == 6
                            and roster[0][4] == ("idempotency_claims", attempt.grant_record.record_id + "::RESERVATION")
                            and proof is attempt.terminal_original is attempt.terminal_proof,
                            "LP03_ORIGINAL_RETAINED_RESERVATION_CHANGED")
            if type(proof[0]) is _EvidenceAttemptFailureAuditV1:
                _native_require(proof[0].phase == "COMPLETED_RESERVED" and proof[0] is attempt.failure_audit
                                and proof[4] is proof[0].readback_original, "LP03_FAILURE_RETAINED_RESERVATION_CHANGED")
            else:
                _native_require(type(proof[0]) is _EvidenceLaneOperationV1
                                and proof[0].finalization_phase == "COMPLETED_RESERVED"
                                and proof[4] is proof[0].final_readback_original, "LP03_ORIGINAL_RETAINED_RESERVATION_CHANGED")
            for name in names:
                result[name] += getattr(limits, name)
        if prospective is not None:
            _native_require(type(prospective) is _EvidenceAttemptOperationV1 and prospective is self.active_attempt
                            and prospective.registration is self and prospective.phase == "NATIVE_TERMINAL_PENDING_LANE_FINALIZATION"
                            and not any(entry[0] is prospective for entry in self.retained_reservations)
                            and prospective.limits is prospective.original[5] is prospective.payload.budgets,
                            "LP03_PROSPECTIVE_RESERVATION_SCOPE")
            for name in names:
                result[name] += getattr(prospective.limits, name)
        if self.review_operation is not None:
            review = self.review_operation
            _native_require(type(review) is _EvidenceReviewOperationV1 and review.registration is self
                            and review.limits is review.original[11] and review.original[1] is self,
                            "LP03_REVIEW_ORIGINAL_RESERVATION_CHANGED")
            for target, source in (("max_wall_ns", "maximum_wall_ns"), ("max_input_reads", "maximum_input_reads"),
                ("max_input_bytes", "maximum_input_bytes"), ("max_persistent_operations", "maximum_persistent_operations"),
                ("max_persistent_bytes", "maximum_persistent_bytes")):
                result[target] += review.limits[source]
        _native_require(type(self.receiver_operations) is dict and type(self.receiver_reservations) is tuple
                        and len(self.receiver_operations) == len(self.receiver_reservations) <= 4
                        and set(self.receiver_operations) <= {"READINESS1", "PRETRADE1", "AGENT_ORCH1", "SVC1"}
                        and all(type(entry) is tuple and len(entry) == 4 for entry in self.receiver_reservations)
                        and len({entry[0] for entry in self.receiver_reservations}) == len(self.receiver_reservations)
                        and all(name == entry[0] and receiver is entry[1]
                            for (name, receiver), entry in zip(self.receiver_operations.items(), self.receiver_reservations)),
                        "LP03_RECEIVER_RESERVATION_ROSTER")
        for name, receiver, original, original_limits in self.receiver_reservations:
            _native_require(type(receiver) is _EvidenceReceiverOperationV1 and receiver.registration is self
                            and receiver.original is original and receiver.context._original[5] == name
                            and receiver.limits is original_limits is original[7]
                            and original[1] is self, "LP03_RECEIVER_ORIGINAL_RESERVATION_CHANGED")
            for target, source in (("max_wall_ns", "maximum_wall_ns"), ("max_input_reads", "maximum_input_reads"),
                ("max_input_bytes", "maximum_input_bytes"), ("max_persistent_operations", "maximum_persistent_operations"),
                ("max_persistent_bytes", "maximum_persistent_bytes")):
                result[target] += receiver.limits[source]
        return result

    def _charge_v1(self, **increments):
        for name, value in increments.items():
            _native_require(name in self.consumed and type(value) is int and value >= 0, "LP03_REGISTRATION_CHARGE_TYPE")
            self.consumed[name] += value
        _EvidenceRegistrationOperationV1._room_v1(self)

    def _assert_numerical_original_v1(self):
        """Original registration arithmetic is retained before any native gap."""
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .input_resolver import _require_evidence_source_slice_roster_v1
        from .serialization import deterministic_json
        original = self.preparation.registration_numerical_original
        _native_require(type(original) is tuple and self.numerical_original is original
                        and len(original) in (3, 11) and original[0] is self,
                        "LP03_REGISTRATION_ORIGINAL_NUMERICAL_WORK_CHANGED")
        if len(original) == 3 and original[1] == "ABSENT":
            _native_require(original[2] is self.numerical_work is None
                            and (self.protocol is None or self.protocol.analysis_profile not in (
                                "DETERMINISTIC_EXACT_DECIMAL_EVI_CONFORMANCE_V1", "DETERMINISTIC_EXACT_DECIMAL_MARKET_CONFORMANCE_V1", "DETERMINISTIC_EXACT_DECIMAL_CASHFLOW_CONFORMANCE_V1",
                                "DETERMINISTIC_EXACT_DECIMAL_KELLY_CONFORMANCE_V1", "DETERMINISTIC_CERTIFIED_BINARY64_LOG_LOSS_CONFORMANCE_V1", "DETERMINISTIC_EXACT_BINARY64_CALIBRATION_CONFORMANCE_V1", "DETERMINISTIC_AS241_BINARY64_WILSON_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_STATIONARY_BOOTSTRAP_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_COMPLETE_FAMILY_REALITY_CHECK_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_COMPLETE_FAMILY_SPA_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_BINARY64_SHARPE_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_RECORDED_DR_UNCERTAINTY_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_RECORDED_OPE_POINT_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_PRIVATE_ANALYTIC_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_PRIVATE_DECIMAL_EXECUTION_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_PRIVATE_BINARY64_EXECUTION_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_QUANTUM_CONSTRUCTOR_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_HELD_OUT_BOUNDED_SCORING_V1", "DETERMINISTIC_ORDERED_BINARY64_CSCV_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_BINARY64_MULTIPLE_TESTING_CONFORMANCE_V1", "DETERMINISTIC_SAME_SNAPSHOT_PROBABILITY_EDGE_CONFORMANCE_V1")),
                            "LP03_REGISTRATION_ORIGINAL_NUMERICAL_WORK_CHANGED")
            return original
        _native_require(len(original) == 11 and original[1] == "COMPLETE"
                        and type(self.numerical_work) is _EvidenceNumericalWorkV1
                        and self.numerical_work is original[2], "LP03_REGISTRATION_NUMERICAL_WORK_UNRESOLVED")
        work = self.numerical_work
        _native_require(work._original is original[3] and work.limits is original[4]
                        and work._decimal_admissions is original[5]
                        and type(work._decimal_inputs) is dict and len(work._decimal_inputs) == len(original[6])
                        and all(type(key) is int for key in work._decimal_inputs)
                        and all(key == held_key and record is held_record for (key, record), (held_key, held_record)
                                in zip(work._decimal_inputs.items(), original[6], strict=True))
                        and type(work._consumed) is dict and all(type(key) is str and type(value) is int
                            for key, value in work._consumed.items())
                        and tuple(work._consumed.items()) == original[7]
                        and work.state == "OPEN" and work.failure is None,
                        "LP03_REGISTRATION_ORIGINAL_NUMERICAL_WORK_CHANGED")
        work._open()
        work._assert_math26_context_custody_v1()
        protocol, protocol_body, policy, policy_body = original[10]
        _native_require((self.protocol is None or (self.protocol is protocol
                            and type(self.resolved_policy_original) is tuple and len(self.resolved_policy_original) == 6
                            and self.resolved_policy_original[5] is original))
                        and deterministic_json(protocol) == protocol_body and deterministic_json(policy) == policy_body,
                        "LP03_REGISTRATION_ORIGINAL_NUMERICAL_POLICY_CHANGED")
        _require_evidence_source_slice_roster_v1(self.preparation, tuple(entry[3] for entry in original[9]),
            originals=original[9], subject=self.preparation, canonical=False)
        return original

    def _check_current_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import _EvidenceIssuerStateV1
        from .input_resolver import _require_evidence_source_slice_roster_v1
        _native_require(self.accounting_observation_state == "OBSERVED", "LP03_EXECUTION_ACCOUNTING_UNPROVEN")
        numerical_original = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(self)
        _evidence_assert_control_roster_v1(self)
        _evidence_assert_control_roster_v1(self.preparation)
        _require_evidence_source_slice_roster_v1(self, self.policy_slices,
            originals=self.policy_source_originals, subject=self, canonical=False)
        if self.active_attempt is not None:
            from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
            _EvidenceAttemptOperationV1._assert_original_members_v1(self.active_attempt, canonical=True)
            EvidenceProcessSupervisorV1._assert_original_v1(self.active_attempt.supervisor)
        values = _EvidenceIssuerStateV1._registration_current_v1(self.issuer, self)
        _native_require(_EvidenceRegistrationOperationV1._assert_numerical_original_v1(self) is numerical_original,
                        "LP03_REGISTRATION_ORIGINAL_NUMERICAL_WORK_CHANGED")
        _require_evidence_source_slice_roster_v1(self, self.policy_slices,
            originals=self.policy_source_originals, subject=self, canonical=False)
        _evidence_assert_control_roster_v1(self)
        _evidence_assert_control_roster_v1(self.preparation)
        if self.active_attempt is not None:
            _EvidenceAttemptOperationV1._validate_current_v1(self.active_attempt, values)
        _EvidenceRegistrationOperationV1._room_v1(self)
        return values

    def _observe_accounting_v1(self):
        """Retain actual nonpositive work without extending any live authority."""
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        from .latency_policy import _EvidenceLocalClockV1
        _native_require(type(self) is _EvidenceRegistrationOperationV1
                        and self.issuer.registrations.get(self.preparation.grant_record.record_id) is self,
                        "LP03_ACCOUNTING_ORIGINAL_OPERATION")
        with self.issuer.lock:
            observed = True
            try:
                usage = (EvidenceProcessSupervisorV1._execution_usage_v1(self.issuer.supervisor, self, refresh=True)
                         if self.issuer.supervisor is not None else dict(cpu_ns=0))
            except BaseException:
                observed = False
                usage = None
            try:
                _wall, mono, cpu = _EvidenceLocalClockV1.observe_v1(self.issuer.clock)
                self.consumed["wall_ns"] = max(self.consumed["wall_ns"], mono - self.deadline.admitted_monotonic_ns)
                if usage is not None:
                    self.consumed["cpu_ns"] = max(self.consumed["cpu_ns"], cpu - self.started_cpu_ns + usage["cpu_ns"])
            except BaseException:
                observed = False
            if not observed:
                self.accounting_observation_state = "UNPROVEN_RETAINED_LAST_OBSERVATION"
            return observed


class _EvidenceConformanceOperationV1:
    """Original CONTROL-owned construction over completed, separately read lanes."""

    __slots__ = ("issuer", "registration", "service", "original", "lanes", "pins", "read_sets", "read_target",
                 "phase", "started", "parent_readbacks", "parent_original", "record", "comparison", "rows", "rows_original",
                 "commit_observation", "commit_original", "readback_observation", "readback_original")

    def __init__(self, *, service, registration):
        from .evidence import ComputationEvidenceServiceV1
        from .latency_policy import _EvidenceLocalClockV1
        from .models import EvidenceLaneV1
        ComputationEvidenceServiceV1._assert_measured_binding_v1(service)
        issuer = registration.issuer
        self.started = _EvidenceLocalClockV1.observe_v1(issuer.clock)
        with issuer.lock:
            _native_require(type(registration) is _EvidenceRegistrationOperationV1
                            and issuer is service._measured_original[0] and issuer.operation is None
                            and registration.conformance_operation is None, "LP03_CONFORMANCE_ALREADY_RESERVED_OR_UNRESOLVED")
            self.issuer, self.registration, self.service = issuer, registration, service
            self.phase, self.original, self.lanes, self.pins = "ADMISSION_VALIDATING", None, (), ()
            self.read_sets, self.read_target, self.parent_readbacks = (), None, ()
            self.parent_original = None
            self.record = self.comparison = self.rows_original = None
            self.rows = ()
            self.commit_observation = self.commit_original = self.readback_observation = self.readback_original = None
            registration.conformance_operation = self
            try:
                _native_require(registration.compiler is service._measured_original[2]
                                and registration.active_attempt is None and registration.active_lane_operation is None
                                and issuer.supervisor._active is None and not issuer.supervisor._unresolved,
                                "LP03_CONFORMANCE_ORIGINAL_COMPLETED_LANES_REQUIRED")
                attempts = tuple(registration.attempts.get((lane, 1)) for lane in (EvidenceLaneV1.REPLAY, EvidenceLaneV1.PAPER))
                _native_require(all(type(item) is _EvidenceAttemptOperationV1 for item in attempts)
                                and len(registration.attempts) == 2, "LP03_CONFORMANCE_EXACT_ATTEMPT_ROSTER")
                proofs = tuple(_EvidenceAttemptOperationV1._require_terminal_v1(item) for item in attempts)
                self.lanes = tuple(proof[0] for proof in proofs)
                _native_require(self.lanes[0].native is not self.lanes[1].native
                                and self.lanes[0].native._terminal_original[0]["process_identity"]
                                != self.lanes[1].native._terminal_original[0]["process_identity"]
                                and all(lane.platform._host is service._measured_original[1] for lane in self.lanes),
                                "LP03_CONFORMANCE_DISTINCT_ORIGINAL_PRODUCERS")
                self.pins = tuple((lane, lane.attempt.terminal_original, lane.original, lane.row_original,
                    lane.final_original, lane.publication_original, lane.dependency_original, lane.control_original,
                    lane.final_readback_original, deterministic_json((lane.native._terminal_original[0], lane.attempt.terminal_original[6])))
                    for lane in self.lanes)
                control = {}
                for lane in self.lanes:
                    for table, row in lane.control_dependencies:
                        key = (table, row[0])
                        _native_require(key not in control or control[key][1] == row, "LP03_CONFORMANCE_PARENT_CONFLICT")
                        control[key] = (table, row, None)
                    for table, row, record in lane.final_rows:
                        key = (table, row[0])
                        _native_require(key not in control, "LP03_CONFORMANCE_PARENT_CONFLICT")
                        control[key] = (table, row, record)
                self.read_sets = ((issuer.control_store, issuer.host, tuple(control.values())),
                    *((lane.platform._store, lane.platform._host,
                       (("receipt_records", lane.publication[2], lane.publication[1]), *lane.rows)) for lane in self.lanes))
                self.original = (issuer, registration, service, service._measured_original, self.lanes, self.pins,
                    self.read_sets, registration.binding_original, registration.resolved_policy_original,
                    registration.retained_reservations, registration.binding_roster_original,
                    deterministic_json(tuple(tuple((table, row) for table, row, _ in target[2]) for target in self.read_sets)))
                self.phase = "PARENTS_PENDING"
            except BaseException:
                self.phase = "ADMISSION_FAILED_REQUIRES_AUDIT"
                raise
            finally:
                _EvidenceRegistrationOperationV1._observe_accounting_v1(registration)

    def __copy__(self):
        raise TypeError("LP03 conformance operation cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 conformance operation cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 conformance operation cannot be serialized")

    def _assert_original_v1(self, *, canonical=False):
        from .evidence import ComputationEvidenceServiceV1
        original = self.original
        _native_require(type(self) is _EvidenceConformanceOperationV1 and original is not None
                        and self.registration.conformance_operation is self
                        and all(left is right for left, right in zip((self.issuer, self.registration, self.service,
                            self.service._measured_original, self.lanes, self.pins, self.read_sets,
                            self.registration.binding_original, self.registration.resolved_policy_original,
                            self.registration.retained_reservations, self.registration.binding_roster_original), original[:11])),
                        "LP03_CONFORMANCE_ORIGINAL_MEMBERS_CHANGED")
        ComputationEvidenceServiceV1._assert_measured_binding_v1(self.service)
        _native_require(self.registration.active_attempt is None and self.registration.active_lane_operation is None
                        and self.issuer.supervisor._active is None and not self.issuer.supervisor._unresolved
                        and (self.read_target is None or any(self.read_target is item for item in self.read_sets)),
                        "LP03_CONFORMANCE_ORIGINAL_SCOPE_CHANGED")
        for pinned in self.pins:
            lane = pinned[0]
            _native_require(all(left is right for left, right in zip((lane.attempt.terminal_original, lane.original,
                lane.row_original, lane.final_original, lane.publication_original, lane.dependency_original,
                lane.control_original, lane.final_readback_original), pinned[1:9]))
                and deterministic_json((lane.native._terminal_original[0], lane.attempt.terminal_original[6])) == pinned[9],
                "LP03_CONFORMANCE_ORIGINAL_PARENT_CHANGED")
            _EvidenceLaneOperationV1._assert_original_v1(lane, canonical=canonical)
        if canonical:
            _native_require(deterministic_json(tuple(tuple((table, row) for table, row, _ in target[2]) for target in self.read_sets))
                            == original[11], "LP03_CONFORMANCE_ORIGINAL_READ_ROSTER_CHANGED")
        if self.rows_original is not None:
            _native_require(self.rows is self.rows_original[0] and self.record is self.rows_original[1]
                            and self.comparison is self.rows_original[2]
                            and (not canonical or deterministic_json((self.rows, self.record, self.comparison)) == self.rows_original[3]),
                            "LP03_CONFORMANCE_ORIGINAL_ROWS_CHANGED")
        _native_require((self.parent_original is None and self.parent_readbacks == ()) or (
            self.parent_original is not None and self.parent_readbacks is self.parent_original[0]
            and self.read_sets is self.parent_original[1]), "LP03_CONFORMANCE_ORIGINAL_PARENT_OBSERVATIONS_CHANGED")
        for observed, pinned in ((self.commit_observation, self.commit_original), (self.readback_observation, self.readback_original)):
            _native_require((observed is None and pinned is None) or (pinned is not None and observed is pinned[0]
                            and self.rows_original is pinned[1]), "LP03_CONFORMANCE_ORIGINAL_OBSERVATION_CHANGED")

    def _room_v1(self, **increments):
        _EvidenceRegistrationOperationV1._room_v1(self.registration, **increments)

    def _charge_v1(self, **increments):
        _EvidenceRegistrationOperationV1._charge_v1(self.registration, **increments)

    def _check_current_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceAbsenceV1, EvidenceKeyPurposeV1
        _EvidenceConformanceOperationV1._assert_original_v1(self)
        purpose = "EVIDENCE_BUNDLE_CONSTRUCTION_V1"
        principal = self.service._measured_original[1].public_configuration.service_principal
        _native_require(self.issuer.operation is self.registration and self.issuer.lock._is_owned(),
                        "LP03_CONFORMANCE_OPERATION_SCOPE")
        for adapter, host, _rows in self.read_sets:
            _native_require(purpose in adapter._evidence_store_binding_v1.binding.allowed_reader_purposes,
                            "LP03_CONFORMANCE_STORE_PURPOSE_DENIED")
            _EvidenceBoundStoreV1._require_original_objects_v1(adapter._evidence_store_binding_v1, host, adapter)
        producer = self.service._measured_original[1]
        EvidenceHostBindingV1._assert_local_binding_v1(producer)
        keys = tuple(key for key in producer.public_configuration.verification_keys
                     if key.key_id == producer.public_configuration.signing_key_id and key.purpose is EvidenceKeyPurposeV1.EVIDENCE_PRODUCER)
        _native_require(len(keys) == 1 and keys[0].principal == principal
                        and type(keys[0].revocation_record_ref_or_absence) is EvidenceAbsenceV1,
                        "LP03_CONFORMANCE_PRODUCER_KEY_NOT_CURRENT")
        for custody, policies in self.registration.policies:
            _native_require(custody.lock._is_owned(), "LP03_CONFORMANCE_ORIGINAL_SOURCE_PURPOSE_DENIED")
            if not all(purpose in policy.source_purposes and principal in policy.consumer_principals for policy in policies):
                raise ContractValidationError(ReasonCode.EVIDENCE_SOURCE_PURPOSE_DENIED,
                                              "LP03_CONFORMANCE_ORIGINAL_SOURCE_PURPOSE_DENIED")
        observed = _EvidenceRegistrationOperationV1._check_current_v1(self.registration)
        _EvidenceConformanceOperationV1._assert_original_v1(self)
        _EvidenceConformanceOperationV1._require_producer_key_time_v1(keys[0], observed[0])
        return observed

    @staticmethod
    def _require_producer_key_time_v1(key, wall_ns):
        """Pure validity predicate; callers still prove original key custody."""
        _native_require(key.valid_from_wall_ns <= wall_ns < key.exclusive_expiry_wall_ns,
                        "LP03_CONFORMANCE_PRODUCER_KEY_NOT_CURRENT")

    def _prepare_records_v1(self):
        from datetime import timedelta
        from .evidence import _build_ready_conformance_v1
        from .receipts import _lp03_spine_for_record_v1
        _native_require(self.phase == "PARENTS_READBACK" and len(self.parent_readbacks) == 3,
                        "LP03_CONFORMANCE_PARENT_READBACK_REQUIRED")
        _EvidenceConformanceOperationV1._assert_original_v1(self, canonical=True)
        observed = _EvidenceConformanceOperationV1._check_current_v1(self)
        self.record, comparison_body = _build_ready_conformance_v1(operation=self, observed=observed)
        created = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=observed[0] // 1000)
        claim = IdempotencyClaimReceiptV1(self.record.comparison_ref, "LP03-CONFORMANCE::" + self.registration.binding_record.record_id,
            "LP03_CONFORMANCE_COMPARISON", deterministic_json(comparison_body), IdempotencyClaimStateV1.ACQUIRED,
            None, created, None, None)
        self.comparison = claim
        result = dict(binding_id=claim.claim_id + "::RESULT", claim_ref=claim.claim_id,
                      result_record_ref=self.record.record_id, created_at=created)
        spine = _lp03_spine_for_record_v1(self.record, sequence=0, trace_ref=self.registration.preparation.trace_ref)
        self.rows = (("idempotency_claims", (claim.claim_id, None, claim.idempotency_key, claim.canonical_request_json,
            None, created.isoformat(), deterministic_json(claim)), claim),
            ("receipt_records", (spine.record_id, spine.effective_at.isoformat(), spine.recorded_at.isoformat(),
                spine.aggregate_id, deterministic_json(spine)), spine),
            ("idempotency_claims", (result["binding_id"], claim.claim_id, None, None, self.record.record_id,
                created.isoformat(), deterministic_json(result)), result))
        self.rows_original = (self.rows, self.record, self.comparison, deterministic_json((self.rows, self.record, self.comparison)))
        size = sum(len(row[-1].encode("utf-8")) for _table, row, _ in self.rows)
        _EvidenceConformanceOperationV1._room_v1(self, owner_queries=15, control_writes=6, control_bytes=size,
            record_reads=36, query_result_records=36, read_bytes=size + 1024)
        self.phase = "PREPARED"
        _EvidenceConformanceOperationV1._check_current_v1(self)


class _EvidenceReviewOperationV1:
    """One separately admitted reviewer; original limits remain encumbered."""

    __slots__ = ("issuer", "registration", "parent", "reviewer", "host", "store", "limits", "deadline", "started", "prefix",
        "original", "phase", "read_sets", "read_target", "parent_readbacks", "parent_original", "admission_payload",
        "signed_admission", "admission_original", "admission_rows", "admission_rows_original", "admission_commit",
        "admission_commit_original", "admission_readback", "admission_readback_original", "record", "decision_payload",
        "rows", "rows_original", "commit_observation", "commit_original", "readback_observation", "readback_original",
        "baseline_slice", "baseline_original", "numerical_work", "source_slice_originals", "source_slice_minted", "source_slice_guard",
        "numerical_result_original")

    def __init__(self, *, reviewer, parent):
        from .evidence import IndependentEvidenceReviewV1
        from .latency_policy import _EvidenceLocalClockV1
        from .models import EvidenceProcessDeadlineV1
        IndependentEvidenceReviewV1._assert_measured_binding_v1(reviewer)
        issuer, registration = parent.issuer, parent.registration
        started = _EvidenceLocalClockV1.observe_v1(issuer.clock)
        with issuer.lock:
            _native_require(type(parent) is _EvidenceConformanceOperationV1 and parent.phase == "COMMITTED_AND_READBACK"
                            and parent.record.terminal_state == "READY_FOR_REVIEW" and issuer.operation is None
                            and registration.review_operation is None and reviewer._measured_original[0] is issuer,
                            "LP03_REVIEW_ALREADY_RESERVED_OR_PARENT_UNAVAILABLE")
            self.issuer, self.registration, self.parent, self.reviewer = issuer, registration, parent, reviewer
            self.host, self.store = reviewer._measured_original[2:4]
            self.limits, self.started, self.prefix = registration.protocol.review_ack_policy, started, dict(registration.consumed)
            self.deadline = EvidenceProcessDeadlineV1(clock_domain_id=issuer.clock.clock_domain_id,
                process_identity_ref=issuer.clock.process_identity_ref, boot_identity_ref=issuer.clock.boot_identity_ref,
                admitted_monotonic_ns=started[1], exclusive_deadline_monotonic_ns=min(
                    started[1] + self.limits["maximum_wall_ns"], registration.deadline.exclusive_deadline_monotonic_ns))
            self.read_sets = ((issuer.control_store, issuer.host, (*parent.read_sets[0][2], *parent.rows)), *parent.read_sets[1:])
            self.read_target, self.parent_readbacks, self.parent_original = None, (), None
            self.admission_payload = self.signed_admission = self.admission_original = self.admission_rows_original = None
            self.admission_rows, self.rows = (), ()
            self.admission_commit = self.admission_commit_original = self.admission_readback = self.admission_readback_original = None
            self.record = self.decision_payload = self.rows_original = None
            self.commit_observation = self.commit_original = self.readback_observation = self.readback_original = None
            self.baseline_slice = self.baseline_original = None
            self.source_slice_originals = ()
            self.source_slice_minted = (self, [])
            from .input_resolver import _bind_evidence_source_acquisition_guard_v1
            self.source_slice_guard = _bind_evidence_source_acquisition_guard_v1(self)
            self.numerical_work = None
            self.numerical_result_original = None
            self.original = (issuer, registration, parent, reviewer, reviewer._measured_original, self.host, self.store,
                parent.original, parent.rows_original, parent.readback_original, self.read_sets, self.limits, self.deadline,
                tuple(self.prefix.items()), started, self.numerical_work,
                None if self.numerical_work is None else self.numerical_work._original,
                (self.source_slice_minted, self.source_slice_guard))
            self.phase = "ADMISSION_PENDING"
            registration.review_operation = self
            registration.review_numerical_original = (self, None)
            try:
                if registration.protocol.analysis_profile in ("DETERMINISTIC_EXACT_BINARY64_BRIER_CONFORMANCE_V1",
                        "DETERMINISTIC_EXACT_DECIMAL_EVI_CONFORMANCE_V1", "DETERMINISTIC_EXACT_DECIMAL_MARKET_CONFORMANCE_V1", "DETERMINISTIC_EXACT_DECIMAL_CASHFLOW_CONFORMANCE_V1",
                        "DETERMINISTIC_EXACT_DECIMAL_KELLY_CONFORMANCE_V1", "DETERMINISTIC_CERTIFIED_BINARY64_LOG_LOSS_CONFORMANCE_V1", "DETERMINISTIC_EXACT_BINARY64_CALIBRATION_CONFORMANCE_V1", "DETERMINISTIC_AS241_BINARY64_WILSON_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_STATIONARY_BOOTSTRAP_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_COMPLETE_FAMILY_REALITY_CHECK_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_COMPLETE_FAMILY_SPA_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_BINARY64_SHARPE_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_RECORDED_DR_UNCERTAINTY_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_RECORDED_OPE_POINT_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_PRIVATE_ANALYTIC_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_PRIVATE_DECIMAL_EXECUTION_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_PRIVATE_BINARY64_EXECUTION_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_QUANTUM_CONSTRUCTOR_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_HELD_OUT_BOUNDED_SCORING_V1", "DETERMINISTIC_ORDERED_BINARY64_CSCV_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_BINARY64_MULTIPLE_TESTING_CONFORMANCE_V1", "DETERMINISTIC_SAME_SNAPSHOT_PROBABILITY_EDGE_CONFORMANCE_V1"):
                    from .parameter_policy import _EvidenceNumericalWorkV1
                    self.phase = "NUMERICAL_WORK_INITIALIZING"
                    numerical_limits = registration.protocol.numerical_work_limits
                    retained_capacity = 0
                    edge = registration.protocol.analysis_profile == "DETERMINISTIC_SAME_SNAPSHOT_PROBABILITY_EDGE_CONFORMANCE_V1"
                    cashflow = registration.protocol.analysis_profile == "DETERMINISTIC_EXACT_DECIMAL_CASHFLOW_CONFORMANCE_V1"
                    market = registration.protocol.analysis_profile == "DETERMINISTIC_EXACT_DECIMAL_MARKET_CONFORMANCE_V1"
                    multiple = registration.protocol.analysis_profile == "DETERMINISTIC_ORDERED_BINARY64_MULTIPLE_TESTING_CONFORMANCE_V1"
                    recorded_dr = registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_RECORDED_DR_UNCERTAINTY_CONFORMANCE_V1"
                    private_execution = registration.protocol.analysis_profile in ("DETERMINISTIC_ORIGINAL_PRIVATE_DECIMAL_EXECUTION_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_PRIVATE_BINARY64_EXECUTION_CONFORMANCE_V1")
                    quantum = registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_QUANTUM_CONSTRUCTOR_CONFORMANCE_V1"
                    analytic = registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_PRIVATE_ANALYTIC_CONFORMANCE_V1"
                    ope_point = registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_RECORDED_OPE_POINT_CONFORMANCE_V1"
                    heldout = registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_HELD_OUT_BOUNDED_SCORING_V1"
                    pbo = registration.protocol.analysis_profile == "DETERMINISTIC_ORDERED_BINARY64_CSCV_CONFORMANCE_V1"
                    sharpe = registration.protocol.analysis_profile == "DETERMINISTIC_ORDERED_BINARY64_SHARPE_CONFORMANCE_V1"
                    spa = registration.protocol.analysis_profile == "DETERMINISTIC_ORDERED_COMPLETE_FAMILY_SPA_CONFORMANCE_V1"
                    reality = registration.protocol.analysis_profile == "DETERMINISTIC_ORDERED_COMPLETE_FAMILY_REALITY_CHECK_CONFORMANCE_V1"
                    bootstrap = registration.protocol.analysis_profile == "DETERMINISTIC_ORDERED_STATIONARY_BOOTSTRAP_CONFORMANCE_V1"
                    wilson = registration.protocol.analysis_profile == "DETERMINISTIC_AS241_BINARY64_WILSON_CONFORMANCE_V1"
                    calibration = registration.protocol.analysis_profile == "DETERMINISTIC_EXACT_BINARY64_CALIBRATION_CONFORMANCE_V1"
                    log_loss = registration.protocol.analysis_profile == "DETERMINISTIC_CERTIFIED_BINARY64_LOG_LOSS_CONFORMANCE_V1"
                    kelly = registration.protocol.analysis_profile == "DETERMINISTIC_EXACT_DECIMAL_KELLY_CONFORMANCE_V1"
                    if cashflow or edge or market or kelly or log_loss or calibration or wilson or bootstrap or reality or spa or sharpe or pbo or heldout or recorded_dr or ope_point or analytic or private_execution or quantum or multiple or registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-26::evi",):
                        original_work = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)
                        proof = original_work[8]
                        # Independent review owns fresh arithmetic observations,
                        # but it cannot renew the original serialization budget.
                        remaining = numerical_limits["max_serialized_bytes"] - dict(original_work[7])["serialized_bytes"]
                        _native_require(remaining > 0, "LP03_CASHFLOW_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if cashflow else "LP03_EDGE_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if edge else "LP03_MULTIPLE_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if multiple else "LP03_DR_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if recorded_dr else "LP03_OPE_POINT_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if ope_point else "LP03_ANALYTIC_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if analytic else "LP03_PRIVATE_EXECUTION_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if private_execution else "LP03_QUANTUM_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if quantum else "LP03_HELD_OUT_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if heldout else "LP03_CSCV_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if pbo else "LP03_SHARPE_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if sharpe else "LP03_SPA_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if spa else "LP03_REALITY_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if reality else "LP03_BOOTSTRAP_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if bootstrap else "LP03_WILSON_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if wilson else "LP03_CALIBRATION_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if calibration else "LP03_LOG_LOSS_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if log_loss else
                                        "LP03_KELLY_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if kelly else
                                        "LP03_MARKET_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED" if market else
                                        "LP03_MATH26_REVIEW_NUMERICAL_ALLOWANCE_EXHAUSTED")
                        numerical_limits = dict(numerical_limits, max_serialized_bytes=remaining)
                        if analytic:
                            coordinate_count = len(proof["ordered_coordinate_ids"])
                            retained_capacity = (2 * (coordinate_count * coordinate_count + 2 * coordinate_count + 3)
                                if proof["math_id"] == "MATH-29" else 2 * (coordinate_count + 3))
                        elif quantum:
                            retained_capacity = 768
                        elif private_execution:
                            from .models import _evidence_private_execution_review_capacity_v1
                            retained_capacity = _evidence_private_execution_review_capacity_v1(proof["math_id"])
                        else:
                            retained_capacity = (2*(42 if proof["math_id"] == "MATH-06" else 6*len(proof["outcome_ids"])+33) if cashflow else 16 if edge else 2*(6+len(proof["ordered_original_row_ids"])) if recorded_dr else 6 if ope_point else 8 if heldout or log_loss or calibration or wilson or bootstrap or reality or spa or sharpe or pbo or multiple else 2 * (proof["financial_source_count"] + 2 + (4 if proof["math_id"] == "MATH-27" else 1) + 3) if kelly else
                                2 * (proof["financial_source_count"] + 2 + (5 if proof["math_id"] == "MATH-05" else 1) + 3)
                                if market else 2 * (proof["action_count"] + proof["scenario_count"] * (proof["action_count"] + 4) + 9))
                    # Retain even a partially initialized numerical object on
                    # this already-latched review. Failure cannot admit a new
                    # review or skip the original accounting finally block.
                    self.numerical_work = object.__new__(_EvidenceNumericalWorkV1)
                    _EvidenceNumericalWorkV1.__init__(self.numerical_work, numerical_limits, retained_input_capacity=retained_capacity)
                    self.original = (*self.original[:15], self.numerical_work, self.numerical_work._original, self.original[17])
                    self.phase = "ADMISSION_PENDING"
                _EvidenceConformanceOperationV1._assert_original_v1(parent, canonical=True)
                _native_require(self.host.public_configuration.service_principal != parent.record.producing_principal
                                and all(self.host.public_configuration.service_principal != lane.platform._host.public_configuration.service_principal
                                        for lane in parent.lanes), "LP03_REVIEW_SELF_REVIEW_FORBIDDEN")
                _EvidenceRegistrationOperationV1._room_v1(registration)
            except BaseException:
                self.phase = "ADMISSION_FAILED_REQUIRES_AUDIT"
                raise
            finally:
                _EvidenceRegistrationOperationV1._observe_accounting_v1(registration)

    def __copy__(self):
        raise TypeError("LP03 review operation cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 review operation cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 review operation cannot be serialized")

    def _assert_original_v1(self, *, canonical=False):
        _EvidenceReviewOperationV1._assert_reviewing_members_v1(self, canonical=canonical)
        _EvidenceConformanceOperationV1._assert_original_v1(self.parent, canonical=canonical)

    def _assert_reviewing_members_v1(self, *, canonical=False):
        # R1 owns the same original R0 parent as this review. Validate that
        # common closure once per R1 check, then these original review members.
        # No observation or authority is retained between validation calls.
        from .evidence import IndependentEvidenceReviewV1
        _native_require(type(self) is _EvidenceReviewOperationV1 and self.registration.review_operation is self
                        and all(left is right for left, right in zip((self.issuer, self.registration, self.parent, self.reviewer,
                            self.reviewer._measured_original, self.host, self.store, self.parent.original, self.parent.rows_original,
                            self.parent.readback_original, self.read_sets, self.limits, self.deadline), self.original[:13]))
                        and tuple(self.prefix.items()) == self.original[13] and self.started is self.original[14]
                        and self.numerical_work is self.original[15]
                        and (self.numerical_work is None or self.numerical_work._original is self.original[16]),
                        "LP03_REVIEW_ORIGINAL_MEMBERS_CHANGED")
        numerical = self.registration.review_numerical_original
        _native_require(type(numerical) is tuple and len(numerical) == 2 and numerical[0] is self
                        and numerical[1] is self.numerical_result_original, "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        if self.registration.protocol.analysis_profile in (
                "DETERMINISTIC_EXACT_DECIMAL_EVI_CONFORMANCE_V1", "DETERMINISTIC_EXACT_DECIMAL_MARKET_CONFORMANCE_V1", "DETERMINISTIC_EXACT_DECIMAL_CASHFLOW_CONFORMANCE_V1",
                "DETERMINISTIC_EXACT_DECIMAL_KELLY_CONFORMANCE_V1", "DETERMINISTIC_CERTIFIED_BINARY64_LOG_LOSS_CONFORMANCE_V1", "DETERMINISTIC_EXACT_BINARY64_CALIBRATION_CONFORMANCE_V1", "DETERMINISTIC_AS241_BINARY64_WILSON_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_STATIONARY_BOOTSTRAP_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_COMPLETE_FAMILY_REALITY_CHECK_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_COMPLETE_FAMILY_SPA_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_BINARY64_SHARPE_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_RECORDED_DR_UNCERTAINTY_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_RECORDED_OPE_POINT_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_PRIVATE_ANALYTIC_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_PRIVATE_DECIMAL_EXECUTION_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_PRIVATE_BINARY64_EXECUTION_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_QUANTUM_CONSTRUCTOR_CONFORMANCE_V1", "DETERMINISTIC_ORIGINAL_HELD_OUT_BOUNDED_SCORING_V1", "DETERMINISTIC_ORDERED_BINARY64_CSCV_CONFORMANCE_V1", "DETERMINISTIC_ORDERED_BINARY64_MULTIPLE_TESTING_CONFORMANCE_V1", "DETERMINISTIC_SAME_SNAPSHOT_PROBABILITY_EDGE_CONFORMANCE_V1"):
            work = self.numerical_work
            work._open()
            work._assert_math26_context_custody_v1()
            if self.numerical_result_original is None:
                _native_require(work._decimal_admissions == () and work._math26_context_steps == [],
                                "LP03_REVIEW_NUMERICAL_RESULT_UNRESOLVED")
            else:
                original = self.numerical_result_original
                _native_require(type(original) is tuple and len(original) == 8 and original[0] is work
                                and original[1] is work._original and original[2] is work.limits
                                and original[3] is work._decimal_admissions and original[4] is work._math26_context_prefix
                                and tuple(work.consumed.items()) == original[5]
                                and (not canonical or deterministic_json(original[6]) == original[7]),
                                "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        IndependentEvidenceReviewV1._assert_measured_binding_v1(self.reviewer)
        _native_require(self.read_target is None or any(self.read_target is target for target in self.read_sets)
                        or (self.read_target[0] is self.issuer.control_store and self.read_target[1] is self.issuer.host
                            and self.read_target[2] is self.admission_rows)
                        or (self.read_target[0] is self.store and self.read_target[1] is self.host and self.read_target[2] is self.rows),
                        "LP03_REVIEW_ORIGINAL_READ_TARGET_CHANGED")
        if self.admission_original is not None:
            _native_require(self.admission_payload is self.admission_original[0] and self.signed_admission is self.admission_original[1]
                            and (not canonical or deterministic_json((self.admission_payload, self.signed_admission)) == self.admission_original[2]),
                            "LP03_REVIEW_ORIGINAL_ADMISSION_CHANGED")
        for rows, pinned in ((self.admission_rows, self.admission_rows_original), (self.rows, self.rows_original)):
            _native_require((pinned is None and rows == ()) or (pinned is not None and rows is pinned[0]
                            and (not canonical or deterministic_json(rows) == pinned[1])), "LP03_REVIEW_ORIGINAL_ROWS_CHANGED")
        _native_require((self.rows_original is None and self.record is None and self.decision_payload is None)
                        or (self.rows_original is not None and self.record is self.rows_original[2]
                            and self.decision_payload is self.rows_original[3]), "LP03_REVIEW_ORIGINAL_DECISION_CHANGED")
        _native_require((self.baseline_original is None and self.baseline_slice is None)
                        or (type(self.baseline_original) is tuple and len(self.baseline_original) == 3
                            and self.baseline_slice is self.baseline_original[0]),
                        "LP03_REVIEW_ORIGINAL_BASELINE_CHANGED")
        if self.baseline_original is not None:
            from .input_resolver import _require_evidence_source_slice_roster_v1
            _require_evidence_source_slice_roster_v1(self, (self.baseline_slice,),
                originals=self.baseline_original[2], subject=self, canonical=canonical)
            _native_require(not canonical or deterministic_json(self.baseline_slice) == self.baseline_original[1],
                            "LP03_REVIEW_ORIGINAL_BASELINE_CHANGED")
        _native_require((self.parent_original is None and self.parent_readbacks == ()) or (
            self.parent_original is not None and self.parent_readbacks is self.parent_original[0]
            and self.read_sets is self.parent_original[1]), "LP03_REVIEW_ORIGINAL_PARENT_OBSERVATIONS_CHANGED")
        for observed, pinned, rows in ((self.admission_commit, self.admission_commit_original, self.admission_rows_original),
            (self.admission_readback, self.admission_readback_original, self.admission_rows_original),
            (self.commit_observation, self.commit_original, self.rows_original), (self.readback_observation, self.readback_original, self.rows_original)):
            _native_require((observed is None and pinned is None) or (pinned is not None and observed is pinned[0] and rows is pinned[1]),
                            "LP03_REVIEW_ORIGINAL_OBSERVATION_CHANGED")

    def _check_room_v1(self, totals):
        limits, prefix = self.limits, self.prefix
        _native_require(totals["record_reads"] - prefix["record_reads"] <= limits["maximum_input_reads"]
                        and totals["query_result_records"] - prefix["query_result_records"] <= limits["maximum_input_reads"]
                        and totals["read_bytes"] - prefix["read_bytes"] <= limits["maximum_input_bytes"]
                        and totals["owner_queries"] + totals["control_writes"] - prefix["owner_queries"] - prefix["control_writes"]
                            <= limits["maximum_persistent_operations"]
                        and totals["control_bytes"] - prefix["control_bytes"] <= limits["maximum_persistent_bytes"]
                        and totals["wall_ns"] - (self.started[1] - self.registration.deadline.admitted_monotonic_ns)
                            <= limits["maximum_wall_ns"], "LP03_REVIEW_RESOURCE_EXHAUSTED")

    def _room_v1(self, **increments):
        _EvidenceRegistrationOperationV1._room_v1(self.registration, **increments)

    def _charge_v1(self, **increments):
        _EvidenceRegistrationOperationV1._charge_v1(self.registration, **increments)

    def _scope_v1(self):
        from contextlib import contextmanager, ExitStack
        @contextmanager
        def entered():
            with self.issuer.lock, ExitStack() as locks:
                _native_require(self.issuer.operation is None and self.registration.active_review_operation is None,
                                "LP03_REVIEW_OPERATION_REENTRY")
                self.issuer.operation, self.registration.active_review_operation = self.registration, self
                try:
                    self.issuer._lock_original_source_custodies_v1(locks)
                    _EvidenceReviewOperationV1._check_current_v1(self)
                    yield self
                except BaseException:
                    _EvidenceRegistrationOperationV1._observe_accounting_v1(self.registration)
                    raise
                finally:
                    self.registration.active_review_operation = self.issuer.operation = None
        return entered()

    def _check_current_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceAbsenceV1, EvidenceKeyPurposeV1
        _EvidenceReviewOperationV1._assert_original_v1(self)
        numerical_original = self.registration.review_numerical_original
        _native_require(self.issuer.operation is self.registration and self.issuer.lock._is_owned()
                        and self.registration.active_review_operation is self and self.parent.phase == "COMMITTED_AND_READBACK",
                        "LP03_REVIEW_ORIGINAL_OPERATION_SCOPE")
        purpose, config = "EVIDENCE_INDEPENDENT_REVIEW_V1", self.host.public_configuration
        for adapter, host in ((target[0], target[1]) for target in (*self.read_sets, (self.store, self.host, ()))):
            _native_require(purpose in adapter._evidence_store_binding_v1.binding.allowed_reader_purposes,
                            "LP03_REVIEW_STORE_PURPOSE_DENIED")
            _EvidenceBoundStoreV1._require_original_objects_v1(adapter._evidence_store_binding_v1, host, adapter)
        EvidenceHostBindingV1._assert_local_binding_v1(self.host)
        keys = tuple(key for key in config.verification_keys if key.key_id == config.signing_key_id
                     and key.purpose is EvidenceKeyPurposeV1.INDEPENDENT_REVIEW and key.principal == config.service_principal)
        _native_require(len(keys) == 1 and type(keys[0].revocation_record_ref_or_absence) is EvidenceAbsenceV1,
                        "LP03_REVIEW_KEY_NOT_CURRENT")
        for custody, policies in self.registration.policies:
            _native_require(custody.lock._is_owned() and all(purpose in policy.source_purposes
                            and config.service_principal in policy.consumer_principals for policy in policies),
                            "LP03_REVIEW_ORIGINAL_SOURCE_USE_DENIED")
        observed = _EvidenceRegistrationOperationV1._check_current_v1(self.registration)
        _EvidenceReviewOperationV1._assert_original_v1(self)
        _native_require(self.registration.review_numerical_original is numerical_original,
                        "LP03_REVIEW_ORIGINAL_NUMERICAL_RESULT_CHANGED")
        _native_require(keys[0].valid_from_wall_ns <= observed[0] < keys[0].exclusive_expiry_wall_ns
                        and observed[0] < self.limits["exclusive_expiry_wall_ns"]
                        and self.deadline.admitted_monotonic_ns <= observed[1] < self.deadline.exclusive_deadline_monotonic_ns,
                        "LP03_REVIEW_EXPIRED_OR_KEY_NOT_CURRENT")
        if self.admission_payload is not None:
            _native_require(observed[0] < self.admission_payload.expiry, "LP03_REVIEW_ADMISSION_EXPIRED")
        return observed

    def _prepare_admission_v1(self):
        from datetime import timedelta
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceReviewAdmissionPayloadV1, EvidenceRecordRefV1, EvidenceMessageKindV1
        from .serialization import _evidence_canonical_object_v1
        _native_require(self.phase == "ADMISSION_PENDING", "LP03_REVIEW_ADMISSION_PHASE")
        observed = _EvidenceReviewOperationV1._check_current_v1(self)
        grant_id = self.parent.record.record_id + "::REVIEW_ADMISSION"
        config, issuer_config = self.host.public_configuration, self.issuer.host.public_configuration
        expiry = min(self.registration.envelope_entry[3].exclusive_expiry_wall_ns,
            self.limits["exclusive_expiry_wall_ns"], self.registration.protocol.exclusive_expiry_wall_ns,
            self.started[0] + self.deadline.exclusive_deadline_monotonic_ns - self.started[1],
            *(key.exclusive_expiry_wall_ns for key in config.verification_keys
              if key.key_id in (config.signing_key_id, issuer_config.signing_key_id)))
        self.admission_payload = EvidenceReviewAdmissionPayloadV1(grant_ref=grant_id,
            original_owner_envelope_ref=self.registration.envelope_entry[3].envelope_ref,
            candidate_ref=EvidenceRecordRefV1(self.issuer.control_store._evidence_store_binding_v1.binding.store_id, self.parent.record.record_id),
            candidate_version="R0", reviewer_principal=config.service_principal,
            review_store_id=self.store._evidence_store_binding_v1.binding.store_id, protocol_ref=self.parent.record.protocol_ref,
            input_lock_ref=self.parent.record.input_lock_ref, origin=self.parent.record.origin, generation=self.parent.record.generation,
            source_purpose="EVIDENCE_INDEPENDENT_REVIEW_V1", limits=self.limits, deadline=self.deadline, expiry=expiry)
        self.signed_admission = EvidenceHostBindingV1._sign_message_v1(self.issuer.host, kind=EvidenceMessageKindV1.REVIEW_ADMISSION,
            subject=grant_id, audience=config.service_principal, generation=self.parent.record.generation,
            valid_from_wall_ns=observed[0], exclusive_expiry_wall_ns=expiry,
            payload=_evidence_canonical_object_v1(deterministic_json(self.admission_payload).encode("utf-8")))
        self.admission_original = (self.admission_payload, self.signed_admission,
            deterministic_json((self.admission_payload, self.signed_admission)))
        _message, decoded = EvidenceHostBindingV1._verify_message_v1(self.host, self.signed_admission,
            expected_kind=EvidenceMessageKindV1.REVIEW_ADMISSION, expected_issuer=issuer_config.service_principal,
            expected_subject=grant_id, expected_audience=config.service_principal, expected_generation=self.parent.record.generation)
        _native_require(decoded == self.admission_payload, "LP03_REVIEW_ADMISSION_SIGNATURE_JOIN")
        created = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=observed[0] // 1000)
        claim = IdempotencyClaimReceiptV1(grant_id, grant_id, "LP03_REVIEW_ADMISSION",
            deterministic_json(dict(signed_admission=self.signed_admission, payload=self.admission_payload,
                reservation_state="FULL_ORIGINAL_REVIEW_LIMITS_RETAINED")), IdempotencyClaimStateV1.ACQUIRED, None, created, None, None)
        result = dict(binding_id=grant_id + "::RESULT", claim_ref=grant_id, result_record_ref=grant_id, created_at=created)
        self.admission_rows = (("idempotency_claims", (grant_id, None, grant_id, claim.canonical_request_json, None,
            created.isoformat(), deterministic_json(claim)), claim), ("idempotency_claims", (result["binding_id"], grant_id,
                None, None, grant_id, created.isoformat(), deterministic_json(result)), result))
        self.admission_rows_original = (self.admission_rows, deterministic_json(self.admission_rows))
        self.phase = "ADMISSION_PREPARED"
        _EvidenceReviewOperationV1._check_current_v1(self)

    def _storage_observation_v1(self, observed):
        from .latency_policy import _EvidenceLocalClockV1, _evidence_storage_observation_v1
        clock = self.issuer.clock
        return _evidence_storage_observation_v1(dict(wall_ns=observed[0], monotonic_ns=observed[1], process_cpu_ns=observed[2],
            clock_domain_id=clock.clock_domain_id, process_identity_ref=clock.process_identity_ref,
            boot_identity_ref=clock.boot_identity_ref, clock_declarations=_EvidenceLocalClockV1.declaration_v1(clock)))

    def _prepare_decision_v1(self):
        from dataclasses import fields
        from datetime import timedelta
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceIndependentReviewRecordV1, EvidenceReviewDecisionPayloadV1, EvidenceMessageKindV1, EvidenceRecordHeaderV1, _LP03_DR_REVIEW_LIMITATIONS_V1, _LP03_OPE_POINT_REVIEW_LIMITATIONS_V1, _LP03_ANALYTIC_REVIEW_LIMITATIONS_V1, _LP03_PRIVATE_EXECUTION_REVIEW_LIMITATIONS_V1, _LP03_PRIVATE_BINARY64_EXECUTION_REVIEW_LIMITATIONS_V1, _LP03_QUANTUM_REVIEW_LIMITATIONS_V1, _LP03_HELD_OUT_REVIEW_LIMITATIONS_V1, _LP03_CSCV_REVIEW_LIMITATIONS_V1, _LP03_SHARPE_REVIEW_LIMITATIONS_V1
        from .evidence import IndependentEvidenceReviewV1
        from .serialization import _evidence_canonical_object_v1
        from .receipts import _lp03_spine_for_record_v1
        _native_require(self.phase == "PARENTS_READBACK" and self.parent_original is not None
                        and self.admission_readback_original is not None, "LP03_REVIEW_ORIGINAL_PARENT_READBACK_REQUIRED")
        _EvidenceReviewOperationV1._assert_original_v1(self, canonical=True)
        calculation = IndependentEvidenceReviewV1._calculate_measured_conformance_v1(self.reviewer, self)
        observed = _EvidenceReviewOperationV1._check_current_v1(self)
        config, parent = self.host.public_configuration, self.parent.record
        record_id, method_id = parent.record_id + "::REVIEW:1", parent.record_id + "::REVIEW:METHOD:1"
        body = {member.name: getattr(parent, member.name) for member in fields(EvidenceRecordHeaderV1)}
        body.update(kind="REVIEW", record_id=record_id, causation_ref=parent.record_id,
            producing_owner="INDEPENDENT_EVIDENCE_REVIEW", producing_principal=config.service_principal,
            source_lineage_refs=(parent.record_id, self.admission_payload.grant_ref), created_wall_ns=observed[0],
            original_candidate_store=self.admission_payload.candidate_ref.store_id, original_candidate_ref=parent.record_id,
            original_candidate_version="R0", reviewer_admission_ref=self.admission_payload.grant_ref,
            producer_refs=(parent.producing_principal,), observed_metric_refs=tuple(lane.records.result_record_ref for lane in self.parent.lanes),
            independent_method_refs=(method_id,), decision="PASS_SOFTWARE_CONFORMANCE",
            limitations=(("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_MATH_01_MATH_02_CLOSURE_ONLY",
                          "NO_EMPIRICAL_PREDICTION_OR_CALIBRATION_CERTIFICATION", "EXACT_DECIMAL_AND_DERIVED_BINARY64_CELLS_ONLY",
                          "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED")
                         if self.registration.protocol.analysis_profile == "DETERMINISTIC_SAME_SNAPSHOT_PROBABILITY_EDGE_CONFORMANCE_V1" else
                         ("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_" + self.registration.envelope_entry[3].component_closure[0].replace("-", "_") + "_CLOSURE_ONLY",
                          "EXACT_DECIMAL_CONTEXT_INTERMEDIATES_ONLY", "NO_EMPIRICAL_MODEL_FEE_OR_ACCOUNT_CERTIFICATION", "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED")
                         if self.registration.protocol.analysis_profile == "DETERMINISTIC_EXACT_DECIMAL_CASHFLOW_CONFORMANCE_V1" else
                         ("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_" + self.registration.envelope_entry[3].component_closure[0].replace("-", "_") + "_CLOSURE_ONLY",
                          "EXACT_DECIMAL_CONTEXT_INTERMEDIATES_ONLY", "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED")
                         if self.registration.protocol.analysis_profile in ("DETERMINISTIC_EXACT_DECIMAL_MARKET_CONFORMANCE_V1", "DETERMINISTIC_EXACT_DECIMAL_CASHFLOW_CONFORMANCE_V1",
                            "DETERMINISTIC_EXACT_DECIMAL_KELLY_CONFORMANCE_V1") else
                         ("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_MATH_26_CLOSURE_ONLY", "EXACT_DECIMAL_CONTEXT_INTERMEDIATES_ONLY",
                          "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED") if self.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-26::evi",) else
                         ("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_" + self.registration.protocol.selected_metric_ids[0].split("::")[1].replace("-", "_") + "_CLOSURE_ONLY",
                          "DECLARED_SOFTWARE_TRIAL_UNIVERSE_ONLY_NO_EMPIRICAL_FDR", "ORDERED_BINARY64_NEAREST_EVEN_WITH_DERIVED_HARMONIC_FSUM", "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED")
                         if self.registration.protocol.analysis_profile == "DETERMINISTIC_ORDERED_BINARY64_MULTIPLE_TESTING_CONFORMANCE_V1" else
                          _LP03_PRIVATE_EXECUTION_REVIEW_LIMITATIONS_V1 if self.registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_PRIVATE_DECIMAL_EXECUTION_CONFORMANCE_V1" else
                          _LP03_PRIVATE_BINARY64_EXECUTION_REVIEW_LIMITATIONS_V1 if self.registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_PRIVATE_BINARY64_EXECUTION_CONFORMANCE_V1" else
                          _LP03_QUANTUM_REVIEW_LIMITATIONS_V1 if self.registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_QUANTUM_CONSTRUCTOR_CONFORMANCE_V1" else
                          _LP03_ANALYTIC_REVIEW_LIMITATIONS_V1 if self.registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_PRIVATE_ANALYTIC_CONFORMANCE_V1" else
                          _LP03_OPE_POINT_REVIEW_LIMITATIONS_V1 if self.registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_RECORDED_OPE_POINT_CONFORMANCE_V1" else
                          _LP03_DR_REVIEW_LIMITATIONS_V1 if self.registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_RECORDED_DR_UNCERTAINTY_CONFORMANCE_V1" else
                          _LP03_HELD_OUT_REVIEW_LIMITATIONS_V1 if self.registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_HELD_OUT_BOUNDED_SCORING_V1" else
                         _LP03_CSCV_REVIEW_LIMITATIONS_V1 if self.registration.protocol.analysis_profile == "DETERMINISTIC_ORDERED_BINARY64_CSCV_CONFORMANCE_V1" else
                         _LP03_SHARPE_REVIEW_LIMITATIONS_V1
                         if self.registration.protocol.analysis_profile == "DETERMINISTIC_ORDERED_BINARY64_SHARPE_CONFORMANCE_V1" else
                         ("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_MATH_16_CLOSURE_ONLY",
                          "COMPLETE_FAMILY_MODEL_ONLY_NO_EMPIRICAL_UNIVERSE_OR_SIGNIFICANCE_CERTIFICATION",
                          "FORMULA_INTERMEDIATES_DERIVED_REVIEW_REPLAY_RETURNS_ONLY", "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED")
                         if self.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-16::spa_receipt",) else
                         ("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_MATH_15_CLOSURE_ONLY",
                          "COMPLETE_FAMILY_MODEL_ONLY_NO_EMPIRICAL_UNIVERSE_OR_SIGNIFICANCE_CERTIFICATION",
                          "FORMULA_INTERMEDIATES_DERIVED_REVIEW_REPLAY_RETURNS_ONLY", "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED")
                         if self.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-15::reality_check_receipt",) else
                         ("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_MATH_14_CLOSURE_ONLY",
                          "BOOTSTRAP_MODEL_ONLY_NO_COVERAGE_OR_EMPIRICAL_CERTIFICATION",
                          "FORMULA_INTERMEDIATES_DERIVED_REVIEW_REPLAY_RETURNS_ONLY", "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED")
                         if self.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-14::bootstrap_distribution_and_interval",) else
                         ("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_MATH_11_CLOSURE_ONLY",
                          "AS241_MODEL_ONLY_NO_EXACT_QUANTILE_OR_COVERAGE_CERTIFICATION",
                          "ALL_INVERSE_NORMAL_AND_WILSON_STAGES_DERIVED_NOT_OBSERVED", "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED")
                         if self.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-11::interval",) else
                         ("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_MATH_10_CLOSURE_ONLY",
                          "EXACT_CALIBRATION_INTERMEDIATES_WITH_DERIVED_UNOBSERVED_SUMS", "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED")
                         if self.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-10::ece",) else
                         ("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_MATH_09_CLOSURE_ONLY",
                          "RATIONAL_LOG_ENCLOSURES_WITH_DERIVED_UNOBSERVED_SUMS", "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED")
                         if self.registration.protocol.selected_metric_ids == ("CONFORMANCE::MATH-09::log_loss",) else
                         ("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_MATH_08_CLOSURE_ONLY", "EXACT_BINARY64_INTERMEDIATES_ONLY",
                          "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED") if self.numerical_work is not None else
                         ("SOFTWARE_CONFORMANCE_ONLY", "SELECTED_MATH_03_CLOSURE_ONLY", "NATIVE_CLOCK_ACCURACY_NOT_QUALIFIED")),
            checked_at=_EvidenceReviewOperationV1._storage_observation_v1(self, observed), expiry=self.admission_payload.expiry,
            original_commit_observation=_EvidenceReviewOperationV1._storage_observation_v1(self, self.parent.commit_observation),
            original_readback_observation=_EvidenceReviewOperationV1._storage_observation_v1(self, self.parent.readback_observation))
        payload = EvidenceReviewDecisionPayloadV1(record_body=_evidence_canonical_object_v1(deterministic_json(body).encode("utf-8")),
            independent_calculation=calculation, consumer_principal=self.issuer.host.public_configuration.service_principal)
        signed = EvidenceHostBindingV1._sign_message_v1(self.host, kind=EvidenceMessageKindV1.REVIEW_DECISION,
            subject=record_id, audience=payload.consumer_principal, generation=parent.generation,
            valid_from_wall_ns=observed[0], exclusive_expiry_wall_ns=self.admission_payload.expiry,
            payload=_evidence_canonical_object_v1(deterministic_json(payload).encode("utf-8")))
        _message, decoded = EvidenceHostBindingV1._verify_message_v1(self.issuer.host, signed,
            expected_kind=EvidenceMessageKindV1.REVIEW_DECISION, expected_issuer=config.service_principal,
            expected_subject=record_id, expected_audience=payload.consumer_principal, expected_generation=parent.generation)
        _native_require(decoded == payload, "LP03_REVIEW_DECISION_SIGNATURE_JOIN")
        body.pop("kind")
        self.record = EvidenceIndependentReviewRecordV1(**body, reviewer_decision_signature=signed)
        self.decision_payload = payload
        created = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=observed[0] // 1000)
        claim = IdempotencyClaimReceiptV1(method_id, method_id, "LP03_INDEPENDENT_REVIEW_METHOD",
            deterministic_json(payload), IdempotencyClaimStateV1.ACQUIRED, None, created, None, None)
        result = dict(binding_id=method_id + "::RESULT", claim_ref=method_id, result_record_ref=record_id, created_at=created)
        spine = _lp03_spine_for_record_v1(self.record, sequence=1, trace_ref=self.registration.preparation.trace_ref)
        self.rows = (("idempotency_claims", (method_id, None, method_id, claim.canonical_request_json, None,
            created.isoformat(), deterministic_json(claim)), claim), ("receipt_records", (record_id, spine.effective_at.isoformat(),
                spine.recorded_at.isoformat(), spine.aggregate_id, deterministic_json(spine)), spine),
            ("idempotency_claims", (result["binding_id"], method_id, None, None, record_id, created.isoformat(), deterministic_json(result)), result))
        self.rows_original = (self.rows, deterministic_json(self.rows), self.record, payload)
        self.phase = "REVIEW_PREPARED"
        _EvidenceReviewOperationV1._check_current_v1(self)


class _EvidenceReviewedConformanceOperationV1:
    """Original builder's R1 successor; independent review grants are never reused."""

    __slots__ = ("issuer", "registration", "parent", "review", "service", "original", "phase", "read_sets", "read_target",
        "parent_readbacks", "parent_original", "record", "rows", "rows_original", "commit_observation", "commit_original",
        "readback_observation", "readback_original")

    def __init__(self, *, service, parent, review):
        from .evidence import ComputationEvidenceServiceV1
        ComputationEvidenceServiceV1._assert_measured_binding_v1(service)
        issuer, registration = parent.issuer, parent.registration
        with issuer.lock:
            _native_require(type(parent) is _EvidenceConformanceOperationV1 and type(review) is _EvidenceReviewOperationV1
                            and review.parent is parent and service is parent.service and issuer.operation is None
                            and registration.reviewed_conformance_operation is None,
                            "LP03_REVIEWED_CONFORMANCE_ALREADY_RESERVED_OR_UNRESOLVED")
            self.issuer, self.registration, self.parent, self.review, self.service = issuer, registration, parent, review, service
            self.read_sets = ((issuer.control_store, issuer.host, (*parent.rows, *review.admission_rows)),
                              (review.store, review.host, review.rows))
            self.read_target, self.parent_readbacks, self.parent_original = None, (), None
            self.record, self.rows, self.rows_original = None, (), None
            self.commit_observation = self.commit_original = self.readback_observation = self.readback_original = None
            self.original = (issuer, registration, parent, review, service, self.read_sets, parent.original, parent.rows_original,
                parent.readback_original, review.original, review.admission_rows_original, review.rows_original,
                review.commit_original, review.readback_original)
            self.phase = "PARENTS_PENDING"
            registration.reviewed_conformance_operation = self
            try:
                _EvidenceReviewedConformanceOperationV1._assert_original_v1(self, canonical=True)
                _native_require(parent.phase == review.phase == "COMMITTED_AND_READBACK"
                                and parent.record.terminal_state == "READY_FOR_REVIEW"
                                and review.record.decision == "PASS_SOFTWARE_CONFORMANCE",
                                "LP03_REVIEWED_CONFORMANCE_ORIGINAL_POSITIVE_REVIEW_REQUIRED")
            except BaseException:
                self.phase = "ADMISSION_FAILED_REQUIRES_AUDIT"
                raise
            finally:
                _EvidenceRegistrationOperationV1._observe_accounting_v1(registration)

    def __copy__(self):
        raise TypeError("LP03 reviewed successor operation cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 reviewed successor operation cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 reviewed successor operation cannot be serialized")

    def _assert_original_v1(self, *, canonical=False):
        _native_require(type(self) is _EvidenceReviewedConformanceOperationV1
            and self.registration.reviewed_conformance_operation is self
            and all(left is right for left, right in zip((self.issuer, self.registration, self.parent, self.review, self.service,
                self.read_sets, self.parent.original, self.parent.rows_original, self.parent.readback_original,
                self.review.original, self.review.admission_rows_original, self.review.rows_original,
                self.review.commit_original, self.review.readback_original), self.original))
            and self.review.parent is self.parent,
            "LP03_REVIEWED_CONFORMANCE_ORIGINAL_MEMBERS_CHANGED")
        _EvidenceConformanceOperationV1._assert_original_v1(self.parent, canonical=canonical)
        _EvidenceReviewOperationV1._assert_reviewing_members_v1(self.review, canonical=canonical)
        _native_require(self.read_target is None or any(self.read_target is target for target in self.read_sets)
                        or (self.read_target[0] is self.issuer.control_store and self.read_target[1] is self.issuer.host
                            and self.read_target[2] is self.rows), "LP03_REVIEWED_CONFORMANCE_READ_TARGET_CHANGED")
        _native_require((self.rows_original is None and self.rows == () and self.record is None) or (
            self.rows_original is not None and self.rows is self.rows_original[0] and self.record is self.rows_original[2]
            and (not canonical or deterministic_json(self.rows) == self.rows_original[1])),
            "LP03_REVIEWED_CONFORMANCE_ORIGINAL_ROWS_CHANGED")
        _native_require((self.parent_original is None and self.parent_readbacks == ()) or (
            self.parent_original is not None and self.parent_readbacks is self.parent_original[0]
            and self.read_sets is self.parent_original[1]), "LP03_REVIEWED_CONFORMANCE_ORIGINAL_PARENT_OBSERVATIONS_CHANGED")
        for observed, pinned in ((self.commit_observation, self.commit_original), (self.readback_observation, self.readback_original)):
            _native_require((observed is None and pinned is None) or (pinned is not None and observed is pinned[0]
                            and self.rows_original is pinned[1]), "LP03_REVIEWED_CONFORMANCE_ORIGINAL_OBSERVATION_CHANGED")

    def _room_v1(self, **increments):
        _EvidenceRegistrationOperationV1._room_v1(self.registration, **increments)

    def _charge_v1(self, **increments):
        _EvidenceRegistrationOperationV1._charge_v1(self.registration, **increments)

    def _check_current_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceAbsenceV1, EvidenceKeyPurposeV1
        _EvidenceReviewedConformanceOperationV1._assert_original_v1(self)
        _native_require(self.issuer.operation is self.registration and self.issuer.lock._is_owned()
                        and self.registration.active_review_operation is None
                        and self.parent.phase == self.review.phase == "COMMITTED_AND_READBACK",
                        "LP03_REVIEWED_CONFORMANCE_ORIGINAL_SCOPE")
        review = self.review
        _native_require("EVIDENCE_BUNDLE_CONSTRUCTION_V1" in review.store._evidence_store_binding_v1.binding.allowed_reader_purposes,
                        "LP03_REVIEWED_CONFORMANCE_REVIEW_STORE_PURPOSE")
        _EvidenceBoundStoreV1._require_original_objects_v1(review.store._evidence_store_binding_v1, review.host, review.store)
        EvidenceHostBindingV1._assert_local_binding_v1(review.host)
        config = review.host.public_configuration
        keys = tuple(key for key in config.verification_keys if key.key_id == config.signing_key_id
                     and key.principal == review.record.producing_principal and key.purpose is EvidenceKeyPurposeV1.INDEPENDENT_REVIEW)
        _native_require(len(keys) == 1 and type(keys[0].revocation_record_ref_or_absence) is EvidenceAbsenceV1,
                        "LP03_REVIEWED_CONFORMANCE_REVIEW_KEY_NOT_CURRENT")
        observed = _EvidenceConformanceOperationV1._check_current_v1(self.parent)
        _EvidenceReviewedConformanceOperationV1._assert_original_v1(self)
        _native_require(keys[0].valid_from_wall_ns <= observed[0] < keys[0].exclusive_expiry_wall_ns
                        and observed[0] < review.record.expiry
                        and observed[1] < review.deadline.exclusive_deadline_monotonic_ns,
                        "LP03_REVIEWED_CONFORMANCE_REVIEW_EXPIRED")
        return observed

    def _prepare_records_v1(self):
        from dataclasses import replace
        from datetime import timedelta
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceMessageKindV1
        from .receipts import _lp03_spine_for_record_v1
        _native_require(self.phase == "PARENTS_READBACK" and len(self.parent_readbacks) == 2,
                        "LP03_REVIEWED_CONFORMANCE_PARENT_READBACK_REQUIRED")
        _EvidenceReviewedConformanceOperationV1._assert_original_v1(self, canonical=True)
        review, parent = self.review, self.parent.record
        _, decision = EvidenceHostBindingV1._verify_message_v1(self.issuer.host, review.record.reviewer_decision_signature,
            expected_kind=EvidenceMessageKindV1.REVIEW_DECISION, expected_issuer=review.host.public_configuration.service_principal,
            expected_subject=review.record.record_id, expected_audience=self.issuer.host.public_configuration.service_principal,
            expected_generation=parent.generation)
        _native_require(decision == review.decision_payload and review.record.original_candidate_ref == parent.record_id
                        and review.record.original_candidate_version == "R0" and review.record.decision == "PASS_SOFTWARE_CONFORMANCE",
                        "LP03_REVIEWED_CONFORMANCE_EXACT_REVIEW_JOIN")
        observed = _EvidenceReviewedConformanceOperationV1._check_current_v1(self)
        record_id = parent.record_id.removesuffix("R0") + "R1"
        record = replace(parent, record_id=record_id, causation_ref=parent.record_id, created_wall_ns=observed[0],
            source_lineage_refs=(parent.record_id, review.record.record_id), terminal_state="REVIEWED_FOR_DELIVERY",
            independent_conformance_review_ref=review.record.record_id)
        created = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=observed[0] // 1000)
        claim_id = record_id + "::TRANSITION"
        claim = IdempotencyClaimReceiptV1(claim_id, claim_id, "LP03_REVIEWED_CONFORMANCE",
            deterministic_json(dict(parent_ref=parent.record_id, review_store=review.store._evidence_store_binding_v1.binding.store_id,
                review_ref=review.record.record_id, review_commit=review.commit_observation, review_readback=review.readback_observation,
                exact_parent_readbacks=self.parent_readbacks)), IdempotencyClaimStateV1.ACQUIRED, None, created, None, None)
        result = dict(binding_id=claim_id + "::RESULT", claim_ref=claim_id, result_record_ref=record_id, created_at=created)
        spine = _lp03_spine_for_record_v1(record, sequence=1, trace_ref=self.registration.preparation.trace_ref)
        self.rows = (("idempotency_claims", (claim_id, None, claim_id, claim.canonical_request_json, None,
            created.isoformat(), deterministic_json(claim)), claim), ("receipt_records", (record_id, spine.effective_at.isoformat(),
                spine.recorded_at.isoformat(), spine.aggregate_id, deterministic_json(spine)), spine),
            ("idempotency_claims", (result["binding_id"], claim_id, None, None, record_id, created.isoformat(), deterministic_json(result)), result))
        self.record = record
        self.rows_original = (self.rows, deterministic_json(self.rows), record)
        self.phase = "SUCCESSOR_PREPARED"
        _EvidenceReviewedConformanceOperationV1._check_current_v1(self)


class _EvidenceReceiverContextV1:
    """Exact receiving service custody; public view rows confer no authority."""

    __slots__ = ("_original",)

    def __init__(self):
        raise TypeError("use the receiving owner's explicit original binding")

    def __copy__(self):
        raise TypeError("LP03 receiver context cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 receiver context cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 receiver context cannot be serialized")

    @classmethod
    def _bind_v1(cls, *, owner_service, receiving_owner, parent_resolver, host_binding, persistence_adapter):
        from ...agents.pr169_agent_orch1_resolvers import AgentOrchService, EvidenceHostBindingV1
        from ...readiness.pr169_readiness1_resolvers import CandidateReadinessResolverV1
        from ...pretrade.pr169_pretrade1_resolvers import PreTradeRegistryView
        from ...service.pr169_svc1_resolvers import DashboardReadModelService
        from .evidence import ComputationEvidenceServiceV1
        from .models import EvidenceKeyPurposeV1, EvidenceStoreRoleV1
        from .sqlite_reference import SQLiteReferenceAdapterV1
        owners = {"READINESS1": (CandidateReadinessResolverV1, EvidenceStoreRoleV1.READINESS_ACK),
            "PRETRADE1": (PreTradeRegistryView, EvidenceStoreRoleV1.PRETRADE_ACK),
            "AGENT_ORCH1": (AgentOrchService, EvidenceStoreRoleV1.AGENT_ACK),
            "SVC1": (DashboardReadModelService, EvidenceStoreRoleV1.SVC_ACK)}
        _native_require(cls is _EvidenceReceiverContextV1 and receiving_owner in owners
                        and type(owner_service) is owners[receiving_owner][0]
                        and type(host_binding) is EvidenceHostBindingV1 and type(persistence_adapter) is SQLiteReferenceAdapterV1,
                        "LP03_RECEIVER_ORIGINAL_OWNER_REQUIRED")
        ComputationEvidenceServiceV1._assert_measured_binding_v1(parent_resolver)
        issuer = parent_resolver._measured_original[0]
        config, producer = host_binding.public_configuration, parent_resolver._measured_original[1].public_configuration
        retained = persistence_adapter._evidence_store_binding_v1
        _native_require(host_binding.signing_purpose is EvidenceKeyPurposeV1.RECEIVER_ACCEPTANCE
                        and config.service_owner == receiving_owner and retained.binding.role is owners[receiving_owner][1]
                        and config.service_principal == retained.binding.allowed_writer_principal
                        and config.service_principal not in (producer.service_principal, issuer.host.public_configuration.service_principal)
                        and owner_service is not issuer.service
                        and (issuer.supervisor is None or owner_service is not issuer.supervisor._service)
                        and getattr(owner_service, "_evidence_issuer_state_v1", None) is None
                        and getattr(owner_service, "_evidence_supervisor_v1", None) is None
                        and config.store_bindings == producer.store_bindings and config.verification_keys == producer.verification_keys
                        and config.deployment_id == producer.deployment_id and config.origin is producer.origin
                        and config.generation == producer.generation and config.environment_identity == producer.environment_identity
                        and config.package_identity_ref == producer.package_identity_ref, "LP03_RECEIVER_ORIGINAL_ROLE_SEPARATION")
        _EvidenceBoundStoreV1._require_original_objects_v1(retained, host_binding, persistence_adapter)
        with issuer.lock:
            _native_require(issuer.operation is None and getattr(owner_service, "_evidence_receiver_context_v1", None) is None
                            and len(issuer.measured_receiver_bindings) < 4
                            and not any(original[5] == receiving_owner for _, original in issuer.measured_receiver_bindings),
                            "LP03_RECEIVER_ALREADY_BOUND_OR_BUSY")
            result = object.__new__(cls)
            result._original = (issuer, owner_service, parent_resolver, host_binding, persistence_adapter, receiving_owner, retained, result,
                                type(owner_service))
            object.__setattr__(owner_service, "_evidence_receiver_context_v1", result)
            issuer.measured_receiver_bindings = (*issuer.measured_receiver_bindings, (result, result._original))
            return result

    def _assert_original_v1(self, *, owner_service=None):
        from .evidence import ComputationEvidenceServiceV1
        original = getattr(self, "_original", None)
        _native_require(type(self) is _EvidenceReceiverContextV1 and type(original) is tuple and len(original) == 9
                        and original[7] is self and (owner_service is None or owner_service is original[1])
                        and getattr(original[1], "_evidence_receiver_context_v1", None) is self
                        and original[4]._evidence_store_binding_v1 is original[6]
                        and type(original[1]) is original[8]
                        and getattr(original[1], "_evidence_issuer_state_v1", None) is None
                        and getattr(original[1], "_evidence_supervisor_v1", None) is None
                        and sum(context is self and pinned is original for context, pinned in original[0].measured_receiver_bindings) == 1,
                        "LP03_RECEIVER_ORIGINAL_CONTEXT_CHANGED")
        ComputationEvidenceServiceV1._assert_measured_binding_v1(original[2])
        _native_require(original[2]._measured_original[0] is original[0], "LP03_RECEIVER_ORIGINAL_ISSUER_CHANGED")

    def _receive_v1(self, delivery_ref, *, owner_service):
        from .models import EvidenceRecordRefV1
        from .latency_policy import _EvidenceLocalClockV1
        from .sqlite_reference import SQLiteReferenceAdapterV1
        _EvidenceReceiverContextV1._assert_original_v1(self, owner_service=owner_service)
        issuer = self._original[0]
        _native_require(type(delivery_ref) is EvidenceRecordRefV1
                        and delivery_ref.store_id == issuer.control_store._evidence_store_binding_v1.binding.store_id,
                        "LP03_RECEIVER_ORIGINAL_DELIVERY_REQUIRED")
        operations = tuple(operation for registration in issuer.registrations.values()
            for operation in registration.receiver_operations.values()
            if operation.context is self and operation.delivery is not None and operation.delivery.record_id == delivery_ref.record_id)
        _native_require(len(operations) == 1, "LP03_RECEIVER_ORIGINAL_DELIVERY_REQUIRED")
        operation = operations[0]
        with _EvidenceReceiverOperationV1._scope_v1(operation):
            _native_require(operation.phase in ("ADMITTED_AND_READBACK", "COMMITTED_AND_READBACK"),
                            "LP03_RECEIVER_ALREADY_STARTED_OR_UNRESOLVED")
            if operation.phase == "COMMITTED_AND_READBACK":
                SQLiteReferenceAdapterV1._evidence_read_measured_rows_v1(operation.store, operation, stage="ACK")
            else:
                received = _EvidenceLocalClockV1.observe_v1(issuer.clock)
                operation.received_observation = received
                operation.received_original = received
                SQLiteReferenceAdapterV1._evidence_read_measured_rows_v1(issuer.control_store, operation, stage="PARENTS")
                _EvidenceReceiverOperationV1._prepare_acceptance_v1(operation)
                SQLiteReferenceAdapterV1._evidence_commit_measured_rows_v1(operation.store, operation, stage="ACCEPTANCE")
                _EvidenceReceiverOperationV1._prepare_ack_v1(operation)
                SQLiteReferenceAdapterV1._evidence_commit_measured_rows_v1(operation.store, operation, stage="ACK")
            _EvidenceReceiverOperationV1._check_current_v1(operation)
            _EvidenceReceiverContextV1._assert_original_v1(self, owner_service=owner_service)
            return operation.record


class _EvidenceReceiverOperationV1:
    """One original receiver's issuance, acquisition, acceptance and ACK budget."""

    __slots__ = ("issuer", "registration", "parent", "context", "host", "store", "limits", "deadline", "started", "prefix",
        "original", "phase", "base_read_sets", "read_sets", "read_sets_original", "read_target", "parent_readbacks", "parent_original",
        "delivery_id", "delivery", "admission_payload", "signed_admission", "admission_original", "admission_rows", "admission_rows_original",
        "admission_commit", "admission_commit_original", "admission_readback", "admission_readback_original",
        "acceptance_rows", "acceptance_rows_original", "acceptance_commit", "acceptance_commit_original", "acceptance_readback",
        "acceptance_readback_original", "received_observation", "received_original", "record", "ack_payload", "rows", "rows_original",
        "commit_observation", "commit_original", "readback_observation", "readback_original", "consumed", "consumed_original")

    def __init__(self, *, context, parent):
        from .latency_policy import _EvidenceLocalClockV1
        from .models import EvidenceProcessDeadlineV1
        _EvidenceReceiverContextV1._assert_original_v1(context)
        issuer, registration = parent.issuer, parent.registration
        started = _EvidenceLocalClockV1.observe_v1(issuer.clock)
        name = context._original[5]
        with issuer.lock:
            _EvidenceRegistrationOperationV1._retained_capacity_v1(registration)
            _native_require(type(parent) is _EvidenceReviewedConformanceOperationV1 and parent.phase == "COMMITTED_AND_READBACK"
                            and parent.record.terminal_state == "REVIEWED_FOR_DELIVERY" and context._original[0] is issuer
                            and context._original[2] is parent.service and issuer.operation is None
                            and name not in registration.receiver_operations, "LP03_RECEIVER_ALREADY_RESERVED_OR_PARENT_UNAVAILABLE")
            self.issuer, self.registration, self.parent, self.context = issuer, registration, parent, context
            self.host, self.store = context._original[3:5]
            self.limits, self.started, self.prefix = registration.protocol.review_ack_policy, started, dict(registration.consumed)
            self.consumed = dict.fromkeys(("record_reads", "read_bytes", "owner_queries", "query_result_records", "control_writes", "control_bytes"), 0)
            self.consumed_original = tuple(self.consumed.items())
            self.deadline = EvidenceProcessDeadlineV1(clock_domain_id=issuer.clock.clock_domain_id,
                process_identity_ref=issuer.clock.process_identity_ref, boot_identity_ref=issuer.clock.boot_identity_ref,
                admitted_monotonic_ns=started[1], exclusive_deadline_monotonic_ns=min(started[1] + self.limits["maximum_wall_ns"],
                    registration.deadline.exclusive_deadline_monotonic_ns, parent.review.deadline.exclusive_deadline_monotonic_ns))
            required = set((*registration.readback_refs, *registration.binding_readback_refs))
            policy_rows = tuple(row for row in parent.parent.read_sets[0][2] if (row[0], row[1][0]) in required)
            self.base_read_sets = ((issuer.control_store, issuer.host,
                (*policy_rows, *parent.parent.rows, *parent.review.admission_rows, *parent.rows)),
                (parent.review.store, parent.review.host, parent.review.rows))
            self.delivery_id = parent.record.record_id + "::DELIVERY:" + name + ":1"
            self.read_sets, self.read_sets_original, self.read_target = (), None, None
            self.parent_readbacks, self.parent_original = (), None
            self.delivery = self.admission_payload = self.signed_admission = self.admission_original = None
            self.admission_rows, self.acceptance_rows, self.rows = (), (), ()
            self.admission_rows_original = self.acceptance_rows_original = self.rows_original = None
            self.admission_commit = self.admission_commit_original = self.admission_readback = self.admission_readback_original = None
            self.acceptance_commit = self.acceptance_commit_original = self.acceptance_readback = self.acceptance_readback_original = None
            self.commit_observation = self.commit_original = self.readback_observation = self.readback_original = None
            self.received_observation = self.received_original = self.record = self.ack_payload = None
            self.original = (issuer, registration, parent, context, context._original, self.host, self.store, self.limits,
                self.deadline, started, tuple(self.prefix.items()), parent.original, parent.rows_original, parent.readback_original,
                self.base_read_sets, self.delivery_id, self.consumed)
            self.phase = "ADMISSION_PENDING"
            registration.receiver_operations[name] = self
            registration.receiver_reservations = (*registration.receiver_reservations, (name, self, self.original, self.limits))
            try:
                _native_require(len(policy_rows) == len(required) == 15, "LP03_RECEIVER_ORIGINAL_PROTOCOL_AND_LOCK_ROSTER")
                _EvidenceReviewedConformanceOperationV1._assert_original_v1(parent, canonical=True)
                _EvidenceRegistrationOperationV1._room_v1(registration)
            except BaseException:
                self.phase = "ADMISSION_FAILED_REQUIRES_AUDIT"
                raise
            finally:
                _EvidenceRegistrationOperationV1._observe_accounting_v1(registration)

    def __copy__(self):
        raise TypeError("LP03 receiver operation cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 receiver operation cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 receiver operation cannot be serialized")

    def _assert_original_v1(self, *, canonical=False):
        _EvidenceReceiverOperationV1._assert_receiving_members_v1(self, canonical=canonical)
        _EvidenceReviewedConformanceOperationV1._assert_original_v1(self.parent, canonical=canonical)

    def _assert_receiving_members_v1(self, *, canonical=False):
        # A closeout has one common R1 parent. Its owner validates that common
        # closure once per check and each original receiver's own members here.
        _EvidenceRegistrationOperationV1._retained_capacity_v1(self.registration)
        _native_require(type(self) is _EvidenceReceiverOperationV1
                        and self.registration.receiver_operations.get(self.context._original[5]) is self
                        and all(left is right for left, right in zip((self.issuer, self.registration, self.parent, self.context,
                            self.context._original, self.host, self.store, self.limits, self.deadline, self.started), self.original[:10]))
                        and tuple(self.prefix.items()) == self.original[10]
                        and all(left is right for left, right in zip((self.parent.original, self.parent.rows_original,
                            self.parent.readback_original, self.base_read_sets), self.original[11:15]))
                        and self.delivery_id == self.original[15] and self.consumed is self.original[16]
                        and tuple(self.consumed.items()) == self.consumed_original, "LP03_RECEIVER_ORIGINAL_MEMBERS_CHANGED")
        _EvidenceReceiverContextV1._assert_original_v1(self.context)
        _native_require((self.read_sets_original is None and self.read_sets == ()) or (
            self.read_sets_original is not None and self.read_sets is self.read_sets_original[0]
            and (not canonical or deterministic_json(self.read_sets[0][2]) == self.read_sets_original[1])),
            "LP03_RECEIVER_ORIGINAL_READ_ROSTER_CHANGED")
        _native_require(self.read_target is None or any(self.read_target is target for target in self.read_sets)
                        or (self.read_target[0] is self.issuer.control_store and self.read_target[1] is self.issuer.host
                            and self.read_target[2] is self.admission_rows)
                        or (self.read_target[0] is self.store and self.read_target[1] is self.host
                            and (self.read_target[2] is self.acceptance_rows or self.read_target[2] is self.rows)),
                        "LP03_RECEIVER_ORIGINAL_READ_TARGET_CHANGED")
        if self.admission_original is not None:
            _native_require(self.delivery is self.admission_original[0] and self.admission_payload is self.admission_original[1]
                            and self.signed_admission is self.admission_original[2]
                            and (not canonical or deterministic_json((self.delivery, self.admission_payload, self.signed_admission))
                                == self.admission_original[3]), "LP03_RECEIVER_ORIGINAL_ADMISSION_CHANGED")
        for rows, pinned in ((self.admission_rows, self.admission_rows_original),
            (self.acceptance_rows, self.acceptance_rows_original), (self.rows, self.rows_original)):
            _native_require((pinned is None and rows == ()) or (pinned is not None and rows is pinned[0]
                            and (not canonical or deterministic_json(rows) == pinned[1])), "LP03_RECEIVER_ORIGINAL_ROWS_CHANGED")
        _native_require((self.rows_original is None and self.record is None and self.ack_payload is None) or (
            self.rows_original is not None and self.record is self.rows_original[2] and self.ack_payload is self.rows_original[3]),
            "LP03_RECEIVER_ORIGINAL_ACK_CHANGED")
        _native_require((self.parent_original is None and self.parent_readbacks == ()) or (
            self.parent_original is not None and self.parent_readbacks is self.parent_original[0]
            and self.read_sets is self.parent_original[1]), "LP03_RECEIVER_ORIGINAL_PARENT_OBSERVATIONS_CHANGED")
        _native_require(self.received_observation is self.received_original, "LP03_RECEIVER_ORIGINAL_RECEIPT_OBSERVATION_CHANGED")
        for observed, pinned, rows in ((self.admission_commit, self.admission_commit_original, self.admission_rows_original),
            (self.admission_readback, self.admission_readback_original, self.admission_rows_original),
            (self.acceptance_commit, self.acceptance_commit_original, self.acceptance_rows_original),
            (self.acceptance_readback, self.acceptance_readback_original, self.acceptance_rows_original),
            (self.commit_observation, self.commit_original, self.rows_original), (self.readback_observation, self.readback_original, self.rows_original)):
            _native_require((observed is None and pinned is None) or (pinned is not None and observed is pinned[0] and rows is pinned[1]),
                            "LP03_RECEIVER_ORIGINAL_OBSERVATION_CHANGED")

    def _check_room_v1(self, totals):
        _native_require(self.consumed is self.original[16] and tuple(self.consumed.items()) == self.consumed_original,
                        "LP03_RECEIVER_ORIGINAL_COUNTERS_CHANGED")
        usage = {name: value + totals[name] - self.registration.consumed[name] for name, value in self.consumed.items()}
        limits = self.limits
        _native_require(usage["record_reads"] <= limits["maximum_input_reads"]
                        and usage["query_result_records"] <= limits["maximum_input_reads"]
                        and usage["read_bytes"] <= limits["maximum_input_bytes"]
                        and usage["owner_queries"] + usage["control_writes"] <= limits["maximum_persistent_operations"]
                        and usage["control_bytes"] <= limits["maximum_persistent_bytes"]
                        and totals["wall_ns"] - (self.started[1] - self.registration.deadline.admitted_monotonic_ns)
                            <= limits["maximum_wall_ns"], "LP03_RECEIVER_RESOURCE_EXHAUSTED")

    def _room_v1(self, **increments):
        _EvidenceRegistrationOperationV1._room_v1(self.registration, **increments)

    def _charge_v1(self, **increments):
        _native_require(self.consumed is self.original[16] and tuple(self.consumed.items()) == self.consumed_original,
                        "LP03_RECEIVER_ORIGINAL_COUNTERS_CHANGED")
        for name, value in increments.items():
            _native_require(name in self.consumed and type(value) is int and value >= 0, "LP03_RECEIVER_CHARGE_TYPE")
            self.consumed[name] += value
        self.consumed_original = tuple(self.consumed.items())
        _EvidenceRegistrationOperationV1._charge_v1(self.registration, **increments)

    def _scope_v1(self):
        from contextlib import contextmanager, ExitStack
        @contextmanager
        def entered():
            with self.issuer.lock, ExitStack() as locks:
                _native_require(self.issuer.operation is None and self.registration.active_receiver_operation is None,
                                "LP03_RECEIVER_OPERATION_REENTRY")
                self.issuer.operation, self.registration.active_receiver_operation = self.registration, self
                try:
                    self.issuer._lock_original_source_custodies_v1(locks)
                    _EvidenceReceiverOperationV1._check_current_v1(self)
                    yield self
                except BaseException:
                    _EvidenceRegistrationOperationV1._observe_accounting_v1(self.registration)
                    raise
                finally:
                    self.registration.active_receiver_operation = self.issuer.operation = None
        return entered()

    def _check_current_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceAbsenceV1, EvidenceKeyPurposeV1
        _EvidenceReceiverOperationV1._assert_original_v1(self)
        _native_require(self.issuer.operation is self.registration and self.issuer.lock._is_owned()
                        and self.registration.active_receiver_operation is self and self.parent.phase == "COMMITTED_AND_READBACK",
                        "LP03_RECEIVER_ORIGINAL_OPERATION_SCOPE")
        purpose, config = "EVIDENCE_RECEIVER_ACCEPTANCE_V1", self.host.public_configuration
        for adapter, host in ((self.issuer.control_store, self.issuer.host),
                              (self.parent.review.store, self.parent.review.host), (self.store, self.host)):
            _native_require(purpose in adapter._evidence_store_binding_v1.binding.allowed_reader_purposes,
                            "LP03_RECEIVER_STORE_PURPOSE_DENIED")
            _EvidenceBoundStoreV1._require_original_objects_v1(adapter._evidence_store_binding_v1, host, adapter)
        EvidenceHostBindingV1._assert_local_binding_v1(self.host)
        keys = tuple(key for key in config.verification_keys if key.key_id == config.signing_key_id
                     and key.purpose is EvidenceKeyPurposeV1.RECEIVER_ACCEPTANCE and key.principal == config.service_principal)
        _native_require(len(keys) == 1 and type(keys[0].revocation_record_ref_or_absence) is EvidenceAbsenceV1,
                        "LP03_RECEIVER_KEY_NOT_CURRENT")
        for custody, policies in self.registration.policies:
            _native_require(custody.lock._is_owned() and all(purpose in policy.source_purposes
                            and config.service_principal in policy.consumer_principals for policy in policies),
                            "LP03_RECEIVER_ORIGINAL_SOURCE_USE_DENIED")
        observed = _EvidenceReviewedConformanceOperationV1._check_current_v1(self.parent)
        _EvidenceReceiverOperationV1._assert_original_v1(self)
        _native_require(keys[0].valid_from_wall_ns <= observed[0] < keys[0].exclusive_expiry_wall_ns
                        and observed[0] < self.limits["exclusive_expiry_wall_ns"]
                        and self.deadline.admitted_monotonic_ns <= observed[1] < self.deadline.exclusive_deadline_monotonic_ns,
                        "LP03_RECEIVER_EXPIRED_OR_KEY_NOT_CURRENT")
        if self.admission_payload is not None:
            _native_require(observed[0] < self.admission_payload.expiry, "LP03_RECEIVER_ADMISSION_EXPIRED")
        return observed

    def _prepare_admission_v1(self):
        from dataclasses import fields
        from datetime import timedelta
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import (EvidenceReceiverAdmissionPayloadV1, EvidenceDeliveryRecordV1, EvidenceRecordHeaderV1,
            EvidenceRecordRefV1, EvidenceMessageKindV1, EvidenceAbsenceV1)
        from .serialization import _evidence_canonical_object_v1
        from .receipts import _lp03_spine_for_record_v1
        from .outbox import OutboxIntentRecordV1
        _native_require(self.phase == "ADMISSION_PENDING", "LP03_RECEIVER_ADMISSION_PHASE")
        observed = _EvidenceReceiverOperationV1._check_current_v1(self)
        config, issuer_config, parent = self.host.public_configuration, self.issuer.host.public_configuration, self.parent.record
        grant_id, outbox_id = self.delivery_id + "::ADMISSION", self.delivery_id + "::OUTBOX"
        expiry = min(self.registration.envelope_entry[3].exclusive_expiry_wall_ns,
            self.limits["exclusive_expiry_wall_ns"], self.registration.protocol.exclusive_expiry_wall_ns, self.parent.review.record.expiry,
            self.started[0] + self.deadline.exclusive_deadline_monotonic_ns - self.started[1],
            *(key.exclusive_expiry_wall_ns for key in config.verification_keys
              if key.key_id in (config.signing_key_id, issuer_config.signing_key_id)))
        payload = EvidenceReceiverAdmissionPayloadV1(grant_ref=grant_id,
            original_owner_envelope_ref=self.registration.envelope_entry[3].envelope_ref,
            candidate_ref=EvidenceRecordRefV1(self.issuer.control_store._evidence_store_binding_v1.binding.store_id, parent.record_id),
            candidate_version="R1", delivery_ref=self.delivery_id, receiver_owner=self.context._original[5],
            receiver_principal=config.service_principal, receiver_store_id=self.store._evidence_store_binding_v1.binding.store_id,
            protocol_ref=parent.protocol_ref, input_lock_ref=parent.input_lock_ref, origin=parent.origin, generation=parent.generation,
            source_purpose="EVIDENCE_RECEIVER_ACCEPTANCE_V1", limits=self.limits, deadline=self.deadline, expiry=expiry)
        signed = EvidenceHostBindingV1._sign_message_v1(self.issuer.host, kind=EvidenceMessageKindV1.RECEIVER_ADMISSION,
            subject=grant_id, audience=config.service_principal, generation=parent.generation,
            valid_from_wall_ns=observed[0], exclusive_expiry_wall_ns=expiry,
            payload=_evidence_canonical_object_v1(deterministic_json(payload).encode("utf-8")))
        _, decoded = EvidenceHostBindingV1._verify_message_v1(self.host, signed,
            expected_kind=EvidenceMessageKindV1.RECEIVER_ADMISSION, expected_issuer=issuer_config.service_principal,
            expected_subject=grant_id, expected_audience=config.service_principal, expected_generation=parent.generation)
        _native_require(decoded == payload, "LP03_RECEIVER_ADMISSION_SIGNATURE_JOIN")
        header = {member.name: getattr(parent, member.name) for member in fields(EvidenceRecordHeaderV1) if member.name != "kind"}
        header.update(record_id=self.delivery_id, producing_owner="AGENT_ORCH1", producing_principal=issuer_config.service_principal,
            causation_ref=parent.record_id, created_wall_ns=observed[0], source_lineage_refs=(parent.record_id, self.parent.review.record.record_id, grant_id))
        delivery = EvidenceDeliveryRecordV1(**header, receiver_owner=self.context._original[5], receiver_purpose=payload.source_purpose,
            bundle_or_conformance_store=payload.candidate_ref.store_id, bundle_or_conformance_ref=parent.record_id,
            bundle_or_conformance_version="R1", payload_reference_roster=tuple(EvidenceRecordRefV1(
                adapter._evidence_store_binding_v1.binding.store_id, row[0]) for adapter, _, rows in self.base_read_sets for _, row, _ in rows),
            attempt_ordinal=1, expiry=expiry, previous_attempt_ref_or_absence=EvidenceAbsenceV1("FIRST_DELIVERY_ATTEMPT"), sender_outbox_ref=outbox_id)
        created = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=observed[0] // 1000)
        claim = IdempotencyClaimReceiptV1(grant_id, self.delivery_id, "LP03_RECEIVER_ADMISSION",
            deterministic_json(dict(signed_admission=signed, payload=payload, delivery=delivery,
                reservation_state="FULL_ORIGINAL_RECEIVER_LIMITS_RETAINED")), IdempotencyClaimStateV1.ACQUIRED, None, created, None, None)
        result = dict(binding_id=grant_id + "::RESULT", claim_ref=grant_id, result_record_ref=self.delivery_id, created_at=created)
        intent = OutboxIntentRecordV1(outbox_id, "LP03_SOFTWARE_CONFORMANCE_DELIVERY", parent.experiment_id, self.delivery_id, created)
        spine = _lp03_spine_for_record_v1(delivery, sequence=1, trace_ref=self.registration.preparation.trace_ref)
        self.delivery, self.admission_payload, self.signed_admission = delivery, payload, signed
        self.admission_original = (delivery, payload, signed, deterministic_json((delivery, payload, signed)))
        self.admission_rows = (("idempotency_claims", (grant_id, None, self.delivery_id, claim.canonical_request_json, None,
            created.isoformat(), deterministic_json(claim)), claim), ("receipt_records", (delivery.record_id, spine.effective_at.isoformat(),
                spine.recorded_at.isoformat(), spine.aggregate_id, deterministic_json(spine)), spine),
            ("outbox_intents", (outbox_id, intent.aggregate_id, intent.payload_record_ref, created.isoformat(), deterministic_json(intent)), intent),
            ("idempotency_claims", (result["binding_id"], grant_id, None, None, self.delivery_id, created.isoformat(), deterministic_json(result)), result))
        self.admission_rows_original = (self.admission_rows, deterministic_json(self.admission_rows))
        self.read_sets = ((self.issuer.control_store, self.issuer.host, (*self.base_read_sets[0][2], *self.admission_rows)), self.base_read_sets[1])
        self.read_sets_original = (self.read_sets, deterministic_json(self.read_sets[0][2]))
        self.phase = "ADMISSION_PREPARED"
        _EvidenceReceiverOperationV1._check_current_v1(self)

    def _prepare_acceptance_v1(self):
        from datetime import timedelta
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceMessageKindV1
        _native_require(self.phase == "PARENTS_READBACK" and self.parent_original is not None
                        and self.admission_readback_original is not None and self.received_original is not None,
                        "LP03_RECEIVER_ORIGINAL_PARENT_READBACK_REQUIRED")
        _EvidenceReceiverOperationV1._assert_original_v1(self, canonical=True)
        config, parent, review = self.host.public_configuration, self.parent.record, self.parent.review
        _, admission = EvidenceHostBindingV1._verify_message_v1(self.host, self.signed_admission,
            expected_kind=EvidenceMessageKindV1.RECEIVER_ADMISSION, expected_issuer=self.issuer.host.public_configuration.service_principal,
            expected_subject=self.admission_payload.grant_ref, expected_audience=config.service_principal, expected_generation=parent.generation)
        _, decision = EvidenceHostBindingV1._verify_message_v1(self.host, review.record.reviewer_decision_signature,
            expected_kind=EvidenceMessageKindV1.REVIEW_DECISION, expected_issuer=review.host.public_configuration.service_principal,
            expected_subject=review.record.record_id, expected_audience=self.issuer.host.public_configuration.service_principal,
            expected_generation=parent.generation)
        _native_require(admission == self.admission_payload and decision == review.decision_payload
                        and self.delivery.receiver_owner == config.service_owner == self.context._original[5]
                        and self.delivery.receiver_purpose == admission.source_purpose == "EVIDENCE_RECEIVER_ACCEPTANCE_V1"
                        and self.delivery.bundle_or_conformance_ref == parent.record_id == admission.candidate_ref.record_id
                        and self.delivery.bundle_or_conformance_version == admission.candidate_version == "R1"
                        and parent.terminal_state == "REVIEWED_FOR_DELIVERY"
                        and parent.independent_conformance_review_ref == review.record.record_id
                        and review.record.decision == "PASS_SOFTWARE_CONFORMANCE"
                        and self.delivery.attempt_ordinal <= self.limits["maximum_delivery_attempts"]
                        and self.context._original[5] in self.limits["required_receiver_ids"], "LP03_RECEIVER_EXACT_USE_AND_AUDIENCE_JOIN")
        observed = _EvidenceReceiverOperationV1._check_current_v1(self)
        created = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=observed[0] // 1000)
        claim_id = self.delivery_id + "::ACCEPTANCE"
        claim = IdempotencyClaimReceiptV1(claim_id, claim_id, "LP03_RECEIVER_ACCEPTANCE_PENDING_ACK",
            deterministic_json(dict(receiving_owner=config.service_owner, receiving_principal=config.service_principal,
                delivery_ref=self.delivery_id, candidate_ref=admission.candidate_ref, candidate_version="R1",
                receiver_admission_ref=admission.grant_ref, original_review_ref=review.record.record_id,
                receiver_purpose=admission.source_purpose, received=self.received_observation,
                original_parent_readbacks=self.parent_readbacks, checked_at=observed,
                outcome="SOFTWARE_CONFORMANCE_RECEIPT_VALIDATED_ACK_NOT_YET_PUBLISHED")),
            IdempotencyClaimStateV1.ACQUIRED, None, created, None, None)
        result = dict(binding_id=claim_id + "::RESULT", claim_ref=claim_id, result_record_ref=claim_id, created_at=created)
        self.acceptance_rows = (("idempotency_claims", (claim_id, None, claim_id, claim.canonical_request_json, None,
            created.isoformat(), deterministic_json(claim)), claim), ("idempotency_claims", (result["binding_id"], claim_id,
                None, None, claim_id, created.isoformat(), deterministic_json(result)), result))
        self.acceptance_rows_original = (self.acceptance_rows, deterministic_json(self.acceptance_rows))
        self.phase = "ACCEPTANCE_PREPARED"
        _EvidenceReceiverOperationV1._check_current_v1(self)

    def _prepare_ack_v1(self):
        from dataclasses import fields
        from datetime import timedelta
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceReceiverAckRecordV1, EvidenceReceiverAckPayloadV1, EvidenceMessageKindV1, EvidenceRecordHeaderV1
        from .serialization import _evidence_canonical_object_v1
        from .receipts import _lp03_spine_for_record_v1
        _native_require(self.phase == "ACCEPTANCE_COMMITTED_AND_READBACK" and self.acceptance_commit_original is not None
                        and self.acceptance_readback_original is not None, "LP03_RECEIVER_DURABLE_ACCEPTANCE_REQUIRED")
        _EvidenceReceiverOperationV1._assert_original_v1(self, canonical=True)
        observed = _EvidenceReceiverOperationV1._check_current_v1(self)
        config, parent = self.host.public_configuration, self.parent.record
        record_id, claim_id = self.delivery_id + "::ACK", self.delivery_id + "::ACK_PUBLICATION"
        body = {member.name: getattr(parent, member.name) for member in fields(EvidenceRecordHeaderV1)}
        body.update(kind="RECEIVER_ACK", record_id=record_id, producing_owner=config.service_owner, producing_principal=config.service_principal,
            causation_ref=self.delivery_id, created_wall_ns=observed[0], source_lineage_refs=(parent.record_id,
                self.parent.review.record.record_id, self.delivery_id, self.admission_payload.grant_ref, self.acceptance_rows[0][1][0]),
            delivery_ref=self.delivery_id, original_candidate_store=self.admission_payload.candidate_ref.store_id,
            original_candidate_ref=parent.record_id, original_candidate_version="R1", receiving_owner=config.service_owner,
            receiving_principal=config.service_principal, receiver_admission_ref=self.admission_payload.grant_ref,
            state="ACCEPTED", reason_codes=("SOFTWARE_CONFORMANCE_RECEIVED_NO_OPERATIONAL_AUTHORITY",),
            received_wall_ns=self.received_observation[0], original_readback_ref=self.acceptance_rows[0][1][0],
            durable_accept_observation=dict(successful_commit_return_observation=_EvidenceReviewOperationV1._storage_observation_v1(self, self.acceptance_commit),
                independent_readback_observation=_EvidenceReviewOperationV1._storage_observation_v1(self, self.acceptance_readback)),
            expiry=self.admission_payload.expiry)
        payload = EvidenceReceiverAckPayloadV1(record_body=_evidence_canonical_object_v1(deterministic_json(body).encode("utf-8")),
            consumer_principal=self.issuer.host.public_configuration.service_principal)
        signed = EvidenceHostBindingV1._sign_message_v1(self.host, kind=EvidenceMessageKindV1.RECEIVER_ACK,
            subject=record_id, audience=payload.consumer_principal, generation=parent.generation,
            valid_from_wall_ns=observed[0], exclusive_expiry_wall_ns=self.admission_payload.expiry,
            payload=_evidence_canonical_object_v1(deterministic_json(payload).encode("utf-8")))
        _, decoded = EvidenceHostBindingV1._verify_message_v1(self.issuer.host, signed,
            expected_kind=EvidenceMessageKindV1.RECEIVER_ACK, expected_issuer=config.service_principal,
            expected_subject=record_id, expected_audience=payload.consumer_principal, expected_generation=parent.generation)
        _native_require(decoded == payload, "LP03_RECEIVER_ACK_SIGNATURE_JOIN")
        body.pop("kind")
        record = EvidenceReceiverAckRecordV1(**body, signature=signed)
        created = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=observed[0] // 1000)
        claim = IdempotencyClaimReceiptV1(claim_id, claim_id, "LP03_RECEIVER_ACK_PUBLICATION", deterministic_json(payload),
            IdempotencyClaimStateV1.ACQUIRED, None, created, None, None)
        result = dict(binding_id=claim_id + "::RESULT", claim_ref=claim_id, result_record_ref=record_id, created_at=created)
        spine = _lp03_spine_for_record_v1(record, sequence=1, trace_ref=self.registration.preparation.trace_ref)
        self.record, self.ack_payload = record, payload
        self.rows = (("idempotency_claims", (claim_id, None, claim_id, claim.canonical_request_json, None,
            created.isoformat(), deterministic_json(claim)), claim), ("receipt_records", (record_id, spine.effective_at.isoformat(),
                spine.recorded_at.isoformat(), spine.aggregate_id, deterministic_json(spine)), spine),
            ("idempotency_claims", (result["binding_id"], claim_id, None, None, record_id, created.isoformat(), deterministic_json(result)), result))
        self.rows_original = (self.rows, deterministic_json(self.rows), record, payload)
        self.phase = "ACK_PREPARED"
        _EvidenceReceiverOperationV1._check_current_v1(self)


class _EvidenceClosedConformanceOperationV1:
    """Original builder's R2 closeout of four actual R1 receiver operations."""

    __slots__ = ("issuer", "registration", "parent", "receivers", "service", "original", "phase", "read_sets", "read_target",
        "parent_readbacks", "parent_original", "record", "rows", "rows_original", "commit_observation", "commit_original",
        "readback_observation", "readback_original")

    def __init__(self, *, service, parent, receivers):
        from .evidence import ComputationEvidenceServiceV1
        ComputationEvidenceServiceV1._assert_measured_binding_v1(service)
        issuer, registration = parent.issuer, parent.registration
        with issuer.lock:
            _EvidenceRegistrationOperationV1._retained_capacity_v1(registration)
            _native_require(type(parent) is _EvidenceReviewedConformanceOperationV1 and service is parent.service
                            and issuer.operation is None and registration.closed_conformance_operation is None
                            and type(receivers) is tuple and len(receivers) == 4
                            and tuple(receiver.context._original[5] for receiver in receivers)
                                == tuple(registration.protocol.review_ack_policy["required_receiver_ids"])
                            and all(receiver is registration.receiver_operations[receiver.context._original[5]]
                                    and receiver.parent is parent for receiver in receivers),
                            "LP03_CLOSEOUT_ORIGINAL_RECEIVERS_REQUIRED")
            self.issuer, self.registration, self.parent, self.receivers, self.service = issuer, registration, parent, receivers, service
            ready = parent.parent
            self.read_sets = ((issuer.control_store, issuer.host, (*ready.read_sets[0][2], *ready.rows,
                *parent.review.admission_rows, *parent.rows, *(row for receiver in receivers for row in receiver.admission_rows))),
                *ready.read_sets[1:], (parent.review.store, parent.review.host, parent.review.rows),
                *((receiver.store, receiver.host, (*receiver.acceptance_rows, *receiver.rows)) for receiver in receivers))
            self.read_target, self.parent_readbacks, self.parent_original = None, (), None
            self.record, self.rows, self.rows_original = None, (), None
            self.commit_observation = self.commit_original = self.readback_observation = self.readback_original = None
            self.original = (issuer, registration, parent, receivers, service, self.read_sets, parent.original,
                parent.rows_original, parent.readback_original, registration.receiver_reservations,
                tuple((receiver.original, receiver.admission_rows_original, receiver.acceptance_rows_original,
                    receiver.rows_original, receiver.admission_commit_original, receiver.admission_readback_original,
                    receiver.acceptance_commit_original, receiver.acceptance_readback_original, receiver.commit_original,
                    receiver.readback_original, receiver.parent_original, receiver.received_original) for receiver in receivers),
                deterministic_json(tuple(rows for _, _, rows in self.read_sets)))
            self.phase = "PARENTS_PENDING"
            registration.closed_conformance_operation = self
            try:
                _EvidenceClosedConformanceOperationV1._assert_original_v1(self, canonical=True)
                _native_require(parent.phase == "COMMITTED_AND_READBACK" and parent.record.terminal_state == "REVIEWED_FOR_DELIVERY"
                                and all(receiver.phase == "COMMITTED_AND_READBACK" and receiver.record.state == "ACCEPTED"
                                    and receiver.acceptance_readback_original is not None and receiver.readback_original is not None
                                    for receiver in receivers), "LP03_CLOSEOUT_ALL_ORIGINAL_ACCEPTED_ACKS_REQUIRED")
                closure = registration.envelope_entry[3].component_closure
                expected_parent_rows = 136 if closure == ("MATH-01", "MATH-02") else 132
                if closure in (("MATH-20",), ("MATH-21",)):
                    from .evidence_execution import _heldout_computation_count_v1
                    math_id = closure[0]
                    for lane in ready.lanes:
                        inputs = lane.exchange[0]._resolution.authoritative_values
                        expected_folds = _heldout_computation_count_v1(math_id, inputs) - 1
                        expected_paths = (3 if inputs["k_test_groups"] == 2 else 1) if math_id == "MATH-21" else 0
                        original_scores, folds, paths = lane.heldout_score_records
                        _native_require(len(original_scores) == len(folds) == expected_folds
                            and len(paths) == expected_paths, "LP03_CLOSEOUT_ORIGINAL_HELD_OUT_ROSTER")
                        expected_parent_rows += 2 * expected_folds + expected_paths
                if closure == ("MATH-22",):
                    _native_require(all(type(lane.recorded_dr_records) is tuple and len(lane.recorded_dr_records) == 2
                        for lane in ready.lanes), "LP03_CLOSEOUT_ORIGINAL_DR_UNCERTAINTY_REQUIRED")
                    expected_parent_rows += 4
                if closure in tuple((math_id,) for math_id in ("MATH-29", "MATH-30", "MATH-31", "MATH-37")):
                    _native_require(all(lane.analytic_conversion_record is not None for lane in ready.lanes),
                        "LP03_CLOSEOUT_ORIGINAL_ANALYTIC_CONVERSIONS_REQUIRED")
                    expected_parent_rows += 2
                if closure in (("MATH-50",), ("MATH-51",)):
                    from .receipts import ST12FEvidenceControlReceiptRecordV1, ST12FReceiptClassV1

                    for lane in ready.lanes:
                        spines = lane.records.receipt_records
                        _native_require(len(spines) == 4 and type(spines[3].typed_payload) is ST12FEvidenceControlReceiptRecordV1
                            and spines[3].typed_payload.receipt_class is ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION
                            and spines[3].typed_payload.canonical_contract_json == lane.exchange[2]["quantum_constructor_receipt_json"],
                            "LP03_CLOSEOUT_ORIGINAL_QUANTUM_TRACE_CONTROL_ROSTER")
                    expected_parent_rows += 2
                _native_require(len(self.read_sets) == 8 and sum(len(rows) for _, _, rows in self.read_sets) == expected_parent_rows,
                                "LP03_CLOSEOUT_SELECTED_CLOSURE_ROSTER")
            except BaseException:
                self.phase = "ADMISSION_FAILED_REQUIRES_AUDIT"
                raise
            finally:
                _EvidenceRegistrationOperationV1._observe_accounting_v1(registration)

    def __copy__(self):
        raise TypeError("LP03 closeout operation cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 closeout operation cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 closeout operation cannot be serialized")

    def _assert_original_v1(self, *, canonical=False):
        _native_require(type(self) is _EvidenceClosedConformanceOperationV1 and self.registration.closed_conformance_operation is self
                        and all(left is right for left, right in zip((self.issuer, self.registration, self.parent, self.receivers,
                            self.service, self.read_sets, self.parent.original, self.parent.rows_original,
                            self.parent.readback_original, self.registration.receiver_reservations), self.original[:10])),
                        "LP03_CLOSEOUT_ORIGINAL_MEMBERS_CHANGED")
        _EvidenceReviewedConformanceOperationV1._assert_original_v1(self.parent, canonical=canonical)
        for receiver, pinned in zip(self.receivers, self.original[10]):
            _EvidenceReceiverOperationV1._assert_receiving_members_v1(receiver, canonical=canonical)
            _native_require(receiver.parent is self.parent and all(left is right for left, right in zip((receiver.original,
                receiver.admission_rows_original, receiver.acceptance_rows_original, receiver.rows_original,
                receiver.admission_commit_original, receiver.admission_readback_original, receiver.acceptance_commit_original,
                receiver.acceptance_readback_original, receiver.commit_original, receiver.readback_original,
                receiver.parent_original, receiver.received_original), pinned)), "LP03_CLOSEOUT_ORIGINAL_RECEIVER_CUSTODY_CHANGED")
        _native_require(not canonical or deterministic_json(tuple(rows for _, _, rows in self.read_sets)) == self.original[11],
                        "LP03_CLOSEOUT_ORIGINAL_READ_ROSTER_CHANGED")
        _native_require(self.read_target is None or any(self.read_target is target for target in self.read_sets)
                        or (self.read_target[0] is self.issuer.control_store and self.read_target[1] is self.issuer.host
                            and self.read_target[2] is self.rows), "LP03_CLOSEOUT_READ_TARGET_CHANGED")
        _native_require((self.rows_original is None and self.rows == () and self.record is None) or (
            self.rows_original is not None and self.rows is self.rows_original[0] and self.record is self.rows_original[2]
            and (not canonical or deterministic_json(self.rows) == self.rows_original[1])), "LP03_CLOSEOUT_ORIGINAL_ROWS_CHANGED")
        _native_require((self.parent_original is None and self.parent_readbacks == ()) or (
            self.parent_original is not None and self.parent_readbacks is self.parent_original[0]
            and self.read_sets is self.parent_original[1]), "LP03_CLOSEOUT_ORIGINAL_PARENT_OBSERVATIONS_CHANGED")
        for observed, pinned in ((self.commit_observation, self.commit_original), (self.readback_observation, self.readback_original)):
            _native_require((observed is None and pinned is None) or (pinned is not None and observed is pinned[0]
                            and self.rows_original is pinned[1]), "LP03_CLOSEOUT_ORIGINAL_OBSERVATION_CHANGED")

    def _room_v1(self, **increments):
        _EvidenceRegistrationOperationV1._room_v1(self.registration, **increments)

    def _charge_v1(self, **increments):
        _EvidenceRegistrationOperationV1._charge_v1(self.registration, **increments)

    def _check_current_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceAbsenceV1, EvidenceKeyPurposeV1
        _EvidenceClosedConformanceOperationV1._assert_original_v1(self)
        _native_require(self.issuer.operation is self.registration and self.issuer.lock._is_owned()
                        and self.registration.active_receiver_operation is None and self.registration.active_review_operation is None
                        and self.registration.active_attempt is None, "LP03_CLOSEOUT_ORIGINAL_BUILDER_SCOPE")
        keys = []
        for receiver in self.receivers:
            _native_require(receiver.phase == "COMMITTED_AND_READBACK" and receiver.record.state == "ACCEPTED"
                            and "EVIDENCE_BUNDLE_CONSTRUCTION_V1" in receiver.store._evidence_store_binding_v1.binding.allowed_reader_purposes,
                            "LP03_CLOSEOUT_ACK_UNAVAILABLE_OR_PURPOSE_DENIED")
            _EvidenceBoundStoreV1._require_original_objects_v1(receiver.store._evidence_store_binding_v1, receiver.host, receiver.store)
            EvidenceHostBindingV1._assert_local_binding_v1(receiver.host)
            config = receiver.host.public_configuration
            selected = tuple(key for key in config.verification_keys if key.key_id == config.signing_key_id
                and key.principal == receiver.record.receiving_principal and key.purpose is EvidenceKeyPurposeV1.RECEIVER_ACCEPTANCE)
            _native_require(len(selected) == 1 and type(selected[0].revocation_record_ref_or_absence) is EvidenceAbsenceV1,
                            "LP03_CLOSEOUT_RECEIVER_KEY_NOT_CURRENT")
            keys.append(selected[0])
        # This common parent check samples after all ACK-store observations and
        # revalidates original producer/reviewer authority at that final time.
        observed = _EvidenceReviewedConformanceOperationV1._check_current_v1(self.parent)
        _EvidenceClosedConformanceOperationV1._assert_original_v1(self)
        _native_require(observed[0] < self.parent.review.record.expiry
                        and observed[1] < self.parent.review.deadline.exclusive_deadline_monotonic_ns
                        and all(key.valid_from_wall_ns <= observed[0] < key.exclusive_expiry_wall_ns
                            and observed[0] < receiver.record.expiry == receiver.admission_payload.expiry
                            and observed[1] < receiver.deadline.exclusive_deadline_monotonic_ns
                            for key, receiver in zip(keys, self.receivers)), "LP03_CLOSEOUT_ACK_OR_REVIEW_EXPIRED")
        return observed

    def _prepare_records_v1(self):
        from dataclasses import replace
        from datetime import timedelta
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import EvidenceMessageKindV1
        from .receipts import _lp03_spine_for_record_v1
        _native_require(self.phase == "PARENTS_READBACK" and len(self.parent_readbacks) == 8,
                        "LP03_CLOSEOUT_ORIGINAL_PARENT_READBACK_REQUIRED")
        _EvidenceClosedConformanceOperationV1._assert_original_v1(self, canonical=True)
        review = self.parent.review
        _, review_payload = EvidenceHostBindingV1._verify_message_v1(self.issuer.host, review.record.reviewer_decision_signature,
            expected_kind=EvidenceMessageKindV1.REVIEW_DECISION, expected_issuer=review.host.public_configuration.service_principal,
            expected_subject=review.record.record_id, expected_audience=self.issuer.host.public_configuration.service_principal,
            expected_generation=self.parent.record.generation)
        _native_require(review_payload == review.decision_payload and review.record.decision == "PASS_SOFTWARE_CONFORMANCE",
                        "LP03_CLOSEOUT_ORIGINAL_REVIEW_SIGNATURE_JOIN")
        for receiver in self.receivers:
            ack, admission, delivery = receiver.record, receiver.admission_payload, receiver.delivery
            _, admitted_payload = EvidenceHostBindingV1._verify_message_v1(receiver.host, receiver.signed_admission,
                expected_kind=EvidenceMessageKindV1.RECEIVER_ADMISSION, expected_issuer=self.issuer.host.public_configuration.service_principal,
                expected_subject=admission.grant_ref, expected_audience=receiver.host.public_configuration.service_principal,
                expected_generation=self.parent.record.generation)
            _, payload = EvidenceHostBindingV1._verify_message_v1(self.issuer.host, ack.signature,
                expected_kind=EvidenceMessageKindV1.RECEIVER_ACK, expected_issuer=receiver.host.public_configuration.service_principal,
                expected_subject=ack.record_id, expected_audience=self.issuer.host.public_configuration.service_principal,
                expected_generation=self.parent.record.generation)
            _native_require(admitted_payload == admission and payload == receiver.ack_payload and ack.state == "ACCEPTED"
                and ack.receiving_owner == admission.receiver_owner == delivery.receiver_owner == receiver.context._original[5]
                and ack.receiving_principal == admission.receiver_principal == receiver.host.public_configuration.service_principal
                and ack.original_candidate_store == admission.candidate_ref.store_id == delivery.bundle_or_conformance_store
                    == self.issuer.control_store._evidence_store_binding_v1.binding.store_id
                and ack.original_candidate_ref == admission.candidate_ref.record_id == delivery.bundle_or_conformance_ref == self.parent.record.record_id
                and ack.original_candidate_version == admission.candidate_version == delivery.bundle_or_conformance_version == "R1"
                and ack.delivery_ref == admission.delivery_ref == delivery.record_id
                and ack.receiver_admission_ref == admission.grant_ref
                and ack.original_readback_ref == receiver.acceptance_rows[0][1][0]
                and ack.durable_accept_observation["successful_commit_return_observation"]
                    == _EvidenceReviewOperationV1._storage_observation_v1(self, receiver.acceptance_commit)
                and ack.durable_accept_observation["independent_readback_observation"]
                    == _EvidenceReviewOperationV1._storage_observation_v1(self, receiver.acceptance_readback),
                "LP03_CLOSEOUT_EXACT_ACK_DELIVERY_ACCEPTANCE_JOIN")
        observed = _EvidenceClosedConformanceOperationV1._check_current_v1(self)
        parent = self.parent.record
        record_id = parent.record_id.removesuffix("R1") + "R2"
        record = replace(parent, record_id=record_id, causation_ref=parent.record_id, created_wall_ns=observed[0],
            source_lineage_refs=(parent.record_id, parent.independent_conformance_review_ref, *(receiver.record.record_id for receiver in self.receivers)),
            receiver_ack_refs=tuple(sorted((receiver.context._original[5], receiver.record.record_id) for receiver in self.receivers)),
            terminal_state="PASS_SOFTWARE_CONFORMANCE")
        created = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=observed[0] // 1000)
        claim_id = record_id + "::CLOSEOUT"
        claim = IdempotencyClaimReceiptV1(claim_id, claim_id, "LP03_SOFTWARE_CONFORMANCE_CLOSEOUT",
            deterministic_json(dict(parent_ref=parent.record_id, parent_version="R1", exact_parent_readbacks=self.parent_readbacks,
                receivers=tuple(dict(owner=receiver.context._original[5], store=receiver.store._evidence_store_binding_v1.binding.store_id,
                    ack_ref=receiver.record.record_id, delivery_ref=receiver.delivery_id, admission_ref=receiver.admission_payload.grant_ref,
                    acceptance_ref=receiver.acceptance_rows[0][1][0], acceptance_commit=receiver.acceptance_commit,
                    acceptance_readback=receiver.acceptance_readback, ack_commit=receiver.commit_observation,
                    ack_readback=receiver.readback_observation) for receiver in self.receivers))),
            IdempotencyClaimStateV1.ACQUIRED, None, created, None, None)
        result = dict(binding_id=claim_id + "::RESULT", claim_ref=claim_id, result_record_ref=record_id, created_at=created)
        spine = _lp03_spine_for_record_v1(record, sequence=1, trace_ref=self.registration.preparation.trace_ref)
        self.record = record
        self.rows = (("idempotency_claims", (claim_id, None, claim_id, claim.canonical_request_json, None,
            created.isoformat(), deterministic_json(claim)), claim), ("receipt_records", (record_id, spine.effective_at.isoformat(),
                spine.recorded_at.isoformat(), spine.aggregate_id, deterministic_json(spine)), spine),
            ("idempotency_claims", (result["binding_id"], claim_id, None, None, record_id, created.isoformat(), deterministic_json(result)), result))
        self.rows_original = (self.rows, deterministic_json(self.rows), record)
        self.phase = "CLOSEOUT_PREPARED"
        _EvidenceClosedConformanceOperationV1._check_current_v1(self)


class _EvidenceAttemptOperationV1:
    """One original post-lock reservation on the registration's cumulative account."""

    __slots__ = ("registration", "request", "supervisor", "started", "prefix", "limits", "deadline", "phase",
                 "payload", "grant_record", "current_state", "readback_refs", "readback_rows", "readback_bodies",
                 "commit_observation", "readback_observation", "handle", "original", "terminal_proof", "allowed_reads",
                 "record_original", "roster_original", "invocations", "invocation_original", "source_slices", "invocation_state",
                 "resolution_progress", "resolution_witnesses",
                 "current_state_original", "observation_appends", "terminal_original", "child_cpu_prefix", "lane_operation",
                 "failure_bounds", "failure_audit", "published_kelly27")

    def __init__(self, registration, request):
        from dataclasses import fields
        from .models import (EvidenceAttemptRequestV1, EvidenceExecutionLimitsV1, EvidenceProcessDeadlineV1,
                             _EVIDENCE_FAILURE_RESERVE_PAIRS_V1)
        from .latency_policy import _EvidenceLocalClockV1
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        _native_require(type(registration) is _EvidenceRegistrationOperationV1 and type(request) is EvidenceAttemptRequestV1,
                        "LP03_ATTEMPT_ORIGINAL_CONTEXT")
        issuer = registration.issuer
        started = _EvidenceLocalClockV1.observe_v1(issuer.clock)
        with issuer.lock:
            _native_require(issuer.operation is None and registration.active_attempt is None,
                            "LP03_CONTROL_OPERATION_REENTRY")
            key = (request.lane, request.attempt_ordinal)
            _native_require(key not in registration.attempts, "LP03_ATTEMPT_ALREADY_RESERVED_OR_UNRESOLVED")
            self.registration, self.request, self.supervisor = registration, request, issuer.supervisor
            self.started, self.prefix = started, dict(registration.consumed)
            self.limits = self.deadline = self.payload = self.grant_record = self.current_state = None
            self.commit_observation = self.readback_observation = self.handle = self.original = self.terminal_proof = None
            self.record_original = self.roster_original = None
            self.current_state_original = self.terminal_original = None
            self.lane_operation = None
            self.failure_bounds, self.failure_audit = None, None
            self.published_kelly27 = None
            self.observation_appends = ()
            self.child_cpu_prefix = 0
            self.invocations, self.invocation_original, self.resolution_progress = (), None, ()
            self.resolution_witnesses = ()
            self.source_slices, self.invocation_state = (), "NOT_STARTED"
            self.readback_refs = self.readback_rows = self.readback_bodies = self.allowed_reads = ()
            self.phase = "ADMISSION_VALIDATING"
            registration.attempts[key] = self
            try:
                _native_require(registration.commit_state == registration.binding_state == "COMMITTED_AND_READBACK"
                                and registration.binding_record is not None and registration.binding_readback_observation is not None,
                                "LP03_ATTEMPT_REQUIRES_ORIGINAL_BOUND_EXPERIMENT")
                _native_require(request.registration_binding_ref.store_id == issuer.control_store._evidence_store_binding_v1.binding.store_id
                                and request.registration_binding_ref.record_id == registration.binding_record.record_id,
                                "LP03_ATTEMPT_ORIGINAL_BINDING_JOIN")
                _native_require("EVIDENCE_ATTEMPT_ADMISSION_V1" in issuer.control_store._evidence_store_binding_v1.binding.allowed_reader_purposes,
                                "LP03_ATTEMPT_CONTROL_PURPOSE_DENIED")
                envelope = registration.envelope_entry[3]
                _native_require(request.lane in envelope.permitted_lanes and request.attempt_ordinal == 1,
                                "LP03_ATTEMPT_LANE_OR_PREDECESSOR_UNAVAILABLE")
                # Only the original committed/read-back state plus retained
                # native terminal custody can release a previous reservation.
                for old in registration.attempts.values():
                    if old is not self:
                        _EvidenceAttemptOperationV1._require_terminal_v1(old)
                _native_require(type(self.supervisor) is EvidenceProcessSupervisorV1, "LP03_ATTEMPT_SUPERVISOR_UNAVAILABLE")
                EvidenceProcessSupervisorV1._assert_original_v1(self.supervisor)
                _native_require(self.supervisor._active is None, "LP03_ATTEMPT_SUPERVISOR_BUSY")
                prior_usage = EvidenceProcessSupervisorV1._execution_usage_v1(self.supervisor, registration, refresh=True)
                self.child_cpu_prefix = prior_usage["cpu_ns"]
                # Claim/protocol packets contain independent expectations. They
                # are not readable by the worker or its lane broker.
                self.allowed_reads = tuple(selection for selection in envelope.assembly_scope.source_selections
                    if not set(selection.permitted_record_kinds) & {"EvidenceClaimPolicyV1", "EvidenceProtocolParametersV1"})
                aggregate, per = envelope.aggregate_execution_limits, envelope.per_attempt_limits
                used = dict(max_wall_ns=started[1] - registration.deadline.admitted_monotonic_ns,
                    max_cpu_ns=started[2] - registration.started_cpu_ns + self.child_cpu_prefix, max_input_reads=self.prefix["record_reads"],
                    max_input_bytes=self.prefix["read_bytes"],
                    max_persistent_operations=self.prefix["owner_queries"] + self.prefix["control_writes"],
                    max_persistent_bytes=self.prefix["control_bytes"], max_attempts=len(registration.attempts) - 1,
                    max_events=prior_usage["events"], max_callbacks=prior_usage["callbacks"],
                    max_coordinates=prior_usage["coordinates"], max_computations=prior_usage["computations"],
                    max_output_bytes=prior_usage["output_bytes"])
                retained = _EvidenceRegistrationOperationV1._retained_capacity_v1(registration)
                for name, value in retained.items():
                    used[name] = used.get(name, 0) + value
                reserve_names = {name for name, _total in _EVIDENCE_FAILURE_RESERVE_PAIRS_V1}
                values = {member.name: (aggregate.aggregate_budget_ref if member.name == "aggregate_budget_ref" else
                    min(getattr(per, member.name), max(0, getattr(aggregate, member.name) - used.get(member.name, 0))))
                    for member in fields(EvidenceExecutionLimitsV1) if member.name not in reserve_names}
                # Audit quotas are subdivisions, not measured expenditure.
                # Each prior full retained reservation encumbers its original
                # quota once; actual CPU/read/write counters are never
                # subtracted from a differently named reserve field.
                for reserve, total in _EVIDENCE_FAILURE_RESERVE_PAIRS_V1:
                    retained_quota = sum(getattr(limits, reserve)
                        for _old, limits, _roster, _proof in registration.retained_reservations)
                    values[reserve] = min(getattr(per, reserve),
                        max(0, getattr(aggregate, reserve) - retained_quota), values[total])
                self.limits = EvidenceExecutionLimitsV1(**values)
                _native_require(self.limits.max_attempts >= 1 and self.limits.max_concurrency >= 1,
                                "LP03_ATTEMPT_RESOURCE_EXHAUSTED")
                _native_require(all(getattr(self.limits, name) > 0 for name in reserve_names),
                                "LP03_ATTEMPT_FAILURE_RESERVE_UNAVAILABLE")
                positive_wall = self.limits.max_wall_ns - self.limits.stop_grace_ns - self.limits.reserved_failure_wall_ns
                expiry = min(envelope.exclusive_expiry_wall_ns, registration.protocol.exclusive_expiry_wall_ns)
                positive_end = min(started[1] + positive_wall,
                    registration.deadline.exclusive_deadline_monotonic_ns, started[1] + max(0, expiry - started[0]))
                _native_require(positive_wall > 0 and positive_end > started[1], "LP03_ATTEMPT_FAILURE_WINDOW_UNAVAILABLE")
                self.failure_bounds = (positive_end, positive_end + self.limits.stop_grace_ns,
                    positive_end + self.limits.stop_grace_ns + self.limits.reserved_failure_wall_ns)
                self.deadline = EvidenceProcessDeadlineV1(clock_domain_id=issuer.clock.clock_domain_id,
                    process_identity_ref=issuer.clock.process_identity_ref, boot_identity_ref=issuer.clock.boot_identity_ref,
                    admitted_monotonic_ns=started[1], exclusive_deadline_monotonic_ns=positive_end)
                if envelope.component_closure == ("MATH-27",) and request.lane.value == "REPLAY":
                    from .input_resolver import _EvidencePublishedKelly27V1
                    self.published_kelly27 = _EvidencePublishedKelly27V1(self)
                self.original = (registration, request, self.supervisor, self.started, tuple(self.prefix.items()),
                                 self.limits, self.deadline, self.allowed_reads, self.child_cpu_prefix, self.failure_bounds,
                                 self.published_kelly27, None if self.published_kelly27 is None else self.published_kelly27.guard)
                self.phase = "ADMITTED_FOR_CONTROL_TRANSACTION"
            except BaseException:
                self.phase = "ADMISSION_FAILED_REQUIRES_AUDIT"
                raise
            finally:
                _EvidenceRegistrationOperationV1._observe_accounting_v1(registration)

    def __copy__(self):
        raise TypeError("LP03 original attempt cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 original attempt cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 original attempt cannot be serialized")

    def _check_room_v1(self, totals):
        limits, prefix = self.limits, self.prefix
        _native_require(limits is not None, "LP03_ATTEMPT_RESERVATION_UNAVAILABLE")
        _native_require(totals["wall_ns"] - (self.started[1] - self.registration.deadline.admitted_monotonic_ns)
                            < self.failure_bounds[0] - self.started[1], "LP03_ATTEMPT_EXPIRED")
        _native_require(totals["record_reads"] - prefix["record_reads"] <= limits.max_input_reads - limits.reserved_failure_input_reads
                        and totals["read_bytes"] - prefix["read_bytes"] <= limits.max_input_bytes - limits.reserved_failure_input_bytes
                        and totals["owner_queries"] + totals["control_writes"] - prefix["owner_queries"] - prefix["control_writes"]
                            <= limits.max_persistent_operations - limits.reserved_failure_persistent_operations
                        and totals["control_bytes"] - prefix["control_bytes"] <= limits.max_persistent_bytes - limits.reserved_failure_persistent_bytes
                        and totals["cpu_ns"] - (self.started[2] - self.registration.started_cpu_ns + self.child_cpu_prefix)
                            <= limits.max_cpu_ns - limits.reserved_failure_cpu_ns,
                        "LP03_ATTEMPT_RESOURCE_EXHAUSTED")
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        usage = EvidenceProcessSupervisorV1._execution_usage_v1(self.supervisor, self.registration, selected_attempt=self)
        for name, limit in (
            ("process_memory_high_water_bytes", "max_process_memory_bytes"), ("job_memory_high_water_bytes", "max_job_memory_bytes"),
            ("events", "max_events"), ("callbacks", "max_callbacks"), ("coordinates", "max_coordinates"),
            ("computations", "max_computations"), ("output_bytes", "max_output_bytes"),
            ("active_workers", "max_concurrency")):
            if usage[name] > getattr(limits, limit):
                # Existing exact budget semantics; numeric native diagnostics
                # stay in the original args rather than defining a new code.
                raise ContractValidationError(ReasonCode.BUDGET_EXCEEDED,
                    "LP03_ATTEMPT_EXECUTION_RESOURCE_EXHAUSTED:" + name + ":" + str(usage[name]) + ":" + str(getattr(limits, limit)))

    def _validate_current_v1(self, observed):
        from .models import EvidenceAbsenceV1, EvidenceKeyPurposeV1, EvidenceStoreRoleV1
        registration, issuer = self.registration, self.registration.issuer
        _EvidenceAttemptOperationV1._assert_original_members_v1(self, canonical=False)
        _native_require(self.original is not None and registration is self.original[0] and self.request is self.original[1]
                        and self.supervisor is self.original[2] and self.started == self.original[3]
                        and tuple(self.prefix.items()) == self.original[4] and self.limits is self.original[5]
                        and self.deadline is self.original[6] and self.allowed_reads is self.original[7]
                        and self.child_cpu_prefix == self.original[8] and self.failure_bounds is self.original[9],
                        "LP03_ATTEMPT_ORIGINAL_ADMISSION_CHANGED")
        _native_require(registration.active_attempt is self and issuer.operation is registration
                        and registration.attempts.get((self.request.lane, self.request.attempt_ordinal)) is self
                        and issuer.supervisor is self.supervisor and not self.supervisor._unresolved,
                        "LP03_ATTEMPT_NOT_ORIGINAL_OR_UNRESOLVED")
        finalizing = (self.phase == "NATIVE_TERMINAL_PENDING_LANE_FINALIZATION"
                      and type(registration.active_lane_operation) is _EvidenceLaneOperationV1
                      and registration.active_lane_operation is self.lane_operation
                      and self.lane_operation.attempt is self)
        _native_require(finalizing or self.phase in ("ADMITTED_FOR_CONTROL_TRANSACTION", "TRANSACTION_OPEN", "COMMIT_ATTEMPTED",
                                       "COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK"),
                        "LP03_ATTEMPT_NONPOSITIVE_OR_UNRESOLVED")
        envelope = registration.envelope_entry[3]
        producer = next(binding.allowed_writer_principal for binding in envelope.store_bindings
                        if binding.role.value == self.request.lane.value)
        service = self.supervisor._host.public_configuration.service_principal
        required = {ref for selection in self.allowed_reads for ref in selection.required_original_rights_refs}
        policies = tuple(policy for _custody, rows in registration.policies for policy in rows if policy.rights_ref in required)
        _native_require({policy.rights_ref for policy in policies} == required, "LP03_ATTEMPT_SOURCE_PURPOSE_DENIED")
        if not all("EVIDENCE_LANE_EXECUTION_V1" in policy.source_purposes
                   and {producer, service} <= set(policy.consumer_principals) for policy in policies):
            raise ContractValidationError(ReasonCode.EVIDENCE_SOURCE_PURPOSE_DENIED, "LP03_ATTEMPT_SOURCE_PURPOSE_DENIED")
        keys = tuple(key for key in issuer.host.public_configuration.verification_keys
                     if key.principal in (producer, service) and key.purpose is EvidenceKeyPurposeV1.EVIDENCE_PRODUCER)
        wall, mono, _cpu = observed
        _native_require(len(keys) == 2 and all(type(key.revocation_record_ref_or_absence) is EvidenceAbsenceV1
            and key.valid_from_wall_ns <= wall < key.exclusive_expiry_wall_ns for key in keys), "LP03_ATTEMPT_ROLE_KEY_NOT_CURRENT")
        _native_require(self.started[1] <= mono, "LP03_ATTEMPT_CLOCK_REGRESSED")
        _native_require(mono < self.deadline.exclusive_deadline_monotonic_ns, "LP03_ATTEMPT_EXPIRED")

    def _assert_original_members_v1(self, *, canonical):
        if self.original is not None:
            _native_require(len(self.original) == 12 and self.published_kelly27 is self.original[10]
                            and (self.published_kelly27 is None and self.original[11] is None
                                 or self.published_kelly27 is not None and self.published_kelly27.guard is self.original[11]),
                            "LP03_ATTEMPT_PRODUCED_SOURCE_ASSOCIATION_CHANGED")
        original = self.record_original
        if original is None:
            _native_require(self.payload is None and self.grant_record is None and self.current_state is None,
                            "LP03_ATTEMPT_ORIGINAL_RECORD_CHANGED")
        else:
            state_original = self.current_state_original
            _native_require(self.payload is original[0] and self.grant_record is original[1]
                            and state_original is not None and self.current_state is state_original[0],
                            "LP03_ATTEMPT_ORIGINAL_RECORD_CHANGED")
            if canonical:
                _native_require(tuple(deterministic_json(value) for value in (self.payload, self.grant_record, original[2])) == original[3]
                                and deterministic_json(self.current_state) == state_original[1],
                                "LP03_ATTEMPT_ORIGINAL_RECORD_CHANGED")
        roster = self.roster_original
        if roster is None:
            _native_require(self.readback_refs == self.readback_rows == self.readback_bodies == (), "LP03_ATTEMPT_ORIGINAL_ROSTER_CHANGED")
        else:
            _native_require(self.readback_refs is roster[0] and self.readback_rows is roster[1] and self.readback_bodies is roster[2],
                            "LP03_ATTEMPT_ORIGINAL_ROSTER_CHANGED")

    def _build_records_v1(self):
        from dataclasses import fields
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from .models import (EvidenceAbsenceV1, EvidenceAttemptGrantPayloadV1, EvidenceAttemptGrantRecordV1,
                             EvidenceAttemptStateRecordV1, EvidenceRecordHeaderV1, EvidenceRecordRefV1, EvidenceMessageKindV1)
        from .lifecycle import EvidenceAttemptStateV1
        from .input_lock import _require_original_input_assembly_outcome_v1
        from .serialization import _evidence_canonical_object_v1
        registration, issuer = self.registration, self.registration.issuer
        _native_require(self.payload is None and self.grant_record is None and self.current_state is None,
                        "LP03_ATTEMPT_RECORDS_ALREADY_BUILT")
        _require_original_input_assembly_outcome_v1(registration.preparation, registration.preparation.input_assembly_outcome)
        original = registration.binding_original
        _native_require(original is not None and registration.compilation is original[2]
                        and deterministic_json(registration.compilation) == original[5], "LP03_ORIGINAL_COMPILATION_CHANGED")
        bound, envelope = registration.binding_record, registration.envelope_entry[3]
        locked = registration.compilation.input_lock
        pins = dict(components=tuple((name, locked.implementation_versions[name], locked.formula_specification_versions[name])
                                    for name in envelope.component_closure), callbacks=envelope.callback_pins)
        if envelope.callback_pins:
            from .models import EvidenceCausalTimelineScopeV1
            from ...agents.pr169_agent_orch1_resolvers import _EvidenceIssuerStateV1

            timeline = registration.records[0].observation_plan["causal_timeline"]
            scope = EvidenceCausalTimelineScopeV1.from_canonical_mapping(timeline)
            _native_require(timeline == registration.registration_policy[0]["observation_plan"]["causal_timeline"]
                            and scope.scenario_plan == registration.preparation.plan,
                            "LP03_ATTEMPT_ORIGINAL_TIMELINE_REGISTRATION")
            _EvidenceIssuerStateV1._require_original_callbacks_v1(issuer, registration.envelope_entry, scope.callbacks)
            pins["causal_timeline"] = timeline
        if registration.protocol.analysis_profile=="DETERMINISTIC_ORIGINAL_HELD_OUT_BOUNDED_SCORING_V1":
            scoring=registration.protocol.numeric_profile
            scorer=scoring["scorer_math_id"]
            _native_require(envelope.component_closure in (("MATH-20",),("MATH-21",))
                and scorer in ("MATH-08","MATH-09") and envelope.callback_pins==()
                and (locked.implementation_versions[scorer],locked.formula_specification_versions[scorer])==(
                    scoring["scorer_implementation_id"],scoring["scorer_specification_id"])
                and scoring["scorer_resource_policy_ref"] == registration.protocol.parameter_protocol_ref,
                "LP03_ATTEMPT_ORIGINAL_SCORER_LOCK_PIN")
            # The signed topology protocol and the original parameter owner
            # carry distinct record IDs. Retain both as original authority.
            pins["supplementary_scorers"] = ((scorer, locked.implementation_versions[scorer],
                locked.formula_specification_versions[scorer], registration.protocol.parameter_protocol_ref),)
        if registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_RECORDED_DR_UNCERTAINTY_CONFORMANCE_V1":
            _native_require(envelope.component_closure == ("MATH-22",) and envelope.callback_pins == (),
                "LP03_ATTEMPT_ORIGINAL_DR_CONTINUATION_CLOSURE")
            pins["supplementary_uncertainty_policy"] = dict(
                parameter_protocol_ref=registration.protocol.parameter_protocol_ref,
                uncertainty_source_ref=registration.protocol.numeric_profile["uncertainty_source_ref"],
                numerical_work_limits=registration.protocol.numerical_work_limits)
        if registration.protocol.analysis_profile == "DETERMINISTIC_ORIGINAL_QUANTUM_CONSTRUCTOR_CONFORMANCE_V1":
            quantum_lock = dict(scenario_set_ref=locked.scenario_set_id,
                source_epoch_pairs=tuple(sorted(locked.source_epochs.items())))
            proof = _EvidenceRegistrationOperationV1._assert_numerical_original_v1(registration)[8]
            _native_require(quantum_lock == proof["original_quantum_lock"] and locked.input_lock_id == proof["original_lock_id"],
                "LP03_ATTEMPT_QUANTUM_ORIGINAL_COMPILED_LOCK")
            pins["quantum_original_lock"] = quantum_lock
        producer = next(binding.allowed_writer_principal for binding in envelope.store_bindings if binding.role.value == self.request.lane.value)
        store_id = self.request.registration_binding_ref.store_id
        grant_id = bound.record_id + "::" + self.request.lane.value + ":1::GRANT"
        fence = EvidenceHostBindingV1._nonce_ref_v1(issuer.host, "LP03-ATTEMPT-FENCE")
        predecessor = EvidenceAbsenceV1("FIRST_ATTEMPT")
        allowed_writes = tuple(binding.store_id for binding in envelope.store_bindings if binding.role.value == self.request.lane.value)
        effects = dict(no_order_authority=True, no_provider_effect=True, no_model_fit=True, no_llm_execution=True, no_qpu_execution=True)
        payload = EvidenceAttemptGrantPayloadV1(grant_ref=grant_id, original_owner_envelope_ref=envelope.envelope_ref,
            experiment_id=bound.experiment_id, experiment_revision=bound.experiment_revision,
            input_assembly_ref=registration.request.input_assembly_ref, registration_ref=self.request.registration_binding_ref,
            input_lock_ref=locked.input_lock_id, scenario_plan_ref=EvidenceRecordRefV1(store_id, bound.scenario_plan_ref),
            protocol_ref=bound.protocol_ref, task_ref=registration.records[0].record_id, claim_family_ref=envelope.claim_policy_ref,
            component_closure=envelope.component_closure, callback_pins=envelope.callback_pins, component_and_callback_pins=pins,
            producer_principal=producer, service_principal=self.supervisor._host.public_configuration.service_principal,
            lane=self.request.lane, attempt_ordinal=self.request.attempt_ordinal, predecessor_attempt_ref=predecessor,
            original_source_grant_refs=tuple(dict.fromkeys(ref for selection in self.allowed_reads for ref in selection.required_original_rights_refs)),
            allowed_reads=self.allowed_reads, allowed_write_store_ids=allowed_writes, budgets=self.limits, deadline=self.deadline,
            fence_ref=fence, supervisor_binding_ref=self.supervisor.binding_ref, **effects)
        wall, _mono, _cpu = _EvidenceRegistrationOperationV1._check_current_v1(registration)
        expiry = min(envelope.exclusive_expiry_wall_ns, registration.protocol.exclusive_expiry_wall_ns)
        signed = EvidenceHostBindingV1._sign_message_v1(issuer.host, kind=EvidenceMessageKindV1.ATTEMPT_GRANT,
            subject=grant_id, audience=payload.service_principal, generation=bound.generation,
            valid_from_wall_ns=wall, exclusive_expiry_wall_ns=expiry,
            payload=_evidence_canonical_object_v1(deterministic_json(payload).encode("utf-8")))
        common = {member.name: getattr(bound, member.name) for member in fields(EvidenceRecordHeaderV1)
                  if member.name not in ("kind", "record_id", "created_wall_ns", "causation_ref", "source_lineage_refs")}
        grant = EvidenceAttemptGrantRecordV1(**common, record_id=grant_id, created_wall_ns=wall, causation_ref=bound.record_id,
            source_lineage_refs=(bound.record_id, bound.input_assembly_ref, locked.input_lock_id),
            original_owner_envelope_ref=envelope.envelope_ref, signed_grant=signed, lane=payload.lane,
            attempt_ordinal=payload.attempt_ordinal, predecessor_attempt_ref=predecessor,
            supervisor_binding_ref=payload.supervisor_binding_ref, component_and_callback_pins=pins,
            allowed_reads=payload.allowed_reads, allowed_writes=payload.allowed_write_store_ids,
            budgets=self.limits, deadline=self.deadline, exclusive_expiry=expiry, fence_ref=fence)
        observed = _EvidenceRegistrationOperationV1._check_current_v1(registration)
        state_id = grant_id + "::STATE:0"
        admitted = EvidenceAttemptStateRecordV1(**common, record_id=state_id, created_wall_ns=observed[0], causation_ref=grant_id,
            source_lineage_refs=(grant_id, bound.record_id), grant_ref=grant_id,
            prior_state_ref=EvidenceAbsenceV1("INITIAL_ATTEMPT_STATE"), state=EvidenceAttemptStateV1.ADMITTED,
            all_reason_codes=(), primary_reason=EvidenceAbsenceV1("NO_STOP_REASON"), event_ordinal=0,
            supervisor_instance_ref=self.supervisor.instance_ref, process_observation_ref_or_absence=EvidenceAbsenceV1("NOT_STARTED"),
            consumed_budget=_EvidenceAttemptOperationV1._consumption_v1(self), currentness_observation_ref=state_id)
        self.payload, self.grant_record, self.current_state = payload, grant, admitted
        self.record_original = (payload, grant, admitted, tuple(deterministic_json(value) for value in (payload, grant, admitted)))
        self.current_state_original = (admitted, deterministic_json(admitted))

    def _require_terminal_v1(self):
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        from .lifecycle import EvidenceAttemptStateV1
        original = self.terminal_original
        if type(original) is tuple and len(original) == 7 and type(original[0]) is _EvidenceAttemptFailureAuditV1:
            return _EvidenceAttemptFailureAuditV1._require_terminal_v1(original[0])
        audit = self.failure_audit
        if (original is None and type(audit) is _EvidenceAttemptFailureAuditV1
                and audit.phase == "COMMIT_OR_OBSERVATION_UNRESOLVED"):
            _EvidenceAttemptFailureAuditV1._assert_original_v1(audit, in_operation=False)
            attempted = audit.commit_attempt_original
            _native_require(audit.attempt is self and audit.rows_original is not None
                            and type(attempted) is tuple and len(attempted) == 3
                            and attempted[0] is audit and attempted[1] is audit.rows_original
                            and attempted[2] is audit.issuer.control_store._connection
                            and audit.commit_original is audit.readback_original is None,
                            "LP03_FAILURE_AUDIT_AMBIGUOUS_COMMIT_WITNESS")
            raise PersistenceContractError(ReasonCode.EVIDENCE_COMMIT_AMBIGUOUS,
                "LP03_ATTEMPT_PRIOR_CUSTODY_UNRESOLVED")
        _native_require(type(original) is tuple and len(original) == 7 and self.terminal_proof is original
                        and original[0] is self.lane_operation and type(original[0]) is _EvidenceLaneOperationV1
                        and original[0].finalization_phase == "COMPLETED_RESERVED"
                        and original[0].final_readback_original is original[4]
                        and self.current_state is original[1] and original[0].final_state is original[1]
                        and self.current_state.state is EvidenceAttemptStateV1.COLLECTION_COMPLETE
                        and original[2] in self.supervisor._retained and original[2]._terminal_original is original[3]
                        and original[2].original[1] is self and original[2].phase == "TERMINAL_RETAINED_AND_CLOSED",
                        "LP03_ATTEMPT_PRIOR_CUSTODY_UNRESOLVED")
        _EvidenceAttemptOperationV1._assert_original_members_v1(self, canonical=True)
        _EvidenceLaneOperationV1._assert_original_v1(original[0])
        _native_require(original[0].final_commit_original is not None and original[4] is not None
                        and original[5][1] >= original[4][0][1] and original[6].active_workers == 0
                        and original[6].cpu_ns <= self.limits.max_cpu_ns and original[6].wall_ns <= self.limits.max_wall_ns,
                        "LP03_ATTEMPT_TERMINAL_ACCOUNTING_UNRESOLVED")
        EvidenceProcessSupervisorV1._assert_original_v1(self.supervisor)
        return original

    def _consumption_v1(self):
        from .models import EvidenceExecutionConsumptionV1
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        registration, prefix = self.registration, self.prefix
        values = registration.consumed
        usage = EvidenceProcessSupervisorV1._execution_usage_v1(self.supervisor, registration, selected_attempt=self)
        return EvidenceExecutionConsumptionV1(
            wall_ns=values["wall_ns"] - (self.started[1] - registration.deadline.admitted_monotonic_ns),
            cpu_ns=values["cpu_ns"] - (self.started[2] - registration.started_cpu_ns + self.child_cpu_prefix),
            process_memory_high_water_bytes=usage["process_memory_high_water_bytes"], job_memory_high_water_bytes=usage["job_memory_high_water_bytes"],
            events=usage["events"], callbacks=usage["callbacks"], coordinates=usage["coordinates"],
            attempts=1, input_reads=values["record_reads"] - prefix["record_reads"], input_bytes=values["read_bytes"] - prefix["read_bytes"],
            computations=usage["computations"], output_bytes=usage["output_bytes"], persistent_operations=values["owner_queries"] + values["control_writes"]
                - prefix["owner_queries"] - prefix["control_writes"], persistent_bytes=values["control_bytes"] - prefix["control_bytes"],
            active_workers=usage["active_workers"], aggregate_budget_ref=self.limits.aggregate_budget_ref)


def _evidence_failure_claim_rows_v1(claim_ref, body_json, result_ref, created_at, *, operation):
    """Existing claim and result rows; neither creates a new record kind."""
    _native_require(operation in ("LP03_SVC_PROCESS_CAPTURE", "LP03_SVC_PROCESS_FAILURE_AUDIT",
                                  "LP03_SVC_PROCESS_OBSERVATION_APPEND"), "LP03_FAILURE_CLAIM_OPERATION")
    for ref in (claim_ref, claim_ref + "::RESULT", result_ref):
        _native_ident(ref)
    claim = IdempotencyClaimReceiptV1(claim_ref, claim_ref, operation, body_json,
        IdempotencyClaimStateV1.ACQUIRED, None, created_at, None, None)
    return ((claim_ref, None, claim_ref, body_json, None, created_at.isoformat(), deterministic_json(claim)),
        (claim_ref + "::RESULT", claim_ref, None, None, result_ref, created_at.isoformat(),
            deterministic_json(dict(binding_id=claim_ref + "::RESULT", claim_ref=claim_ref,
                                    result_record_ref=result_ref, created_at=created_at))))


def _evidence_failure_row_bytes_v1(row):
    """Every stored text column, including duplicate canonical request data."""
    _native_require(type(row) is tuple and all(value is None or type(value) is str for value in row),
                    "LP03_FAILURE_SQL_ROW_TYPES")
    return sum(len(value.encode("utf-8")) for value in row if value is not None)


class _EvidenceAttemptFailureAuditV1:
    """One original CONTROL integrity tail; never an execution renewal.

    Actual accounting remains cumulative. The audit may spend only its reserved
    subdivision and the remaining original total, before the fixed endpoint.
    A durable observation never grants process terminality or slot release.
    """

    __slots__ = ("attempt", "native", "registration", "issuer", "started", "prefix", "identity_original",
                 "phase", "snapshot", "capture_snapshot", "capture_manifest", "capture_bodies", "body", "body_json",
                 "predecessor", "record", "rows", "refs", "rows_original", "commit_attempt_original", "commit_observation", "commit_original",
                 "readback_observation", "readback_original", "failure_reason", "parent_refs", "parent_rows", "parent_original",
                 "entry_failure_observation", "trigger_original", "trigger_roster", "trigger_snapshot")

    def __init__(self, attempt, native, *, failure_reason, original_error, trigger_original, trigger_roster):
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1, _WindowsEvidenceProcessV1
        from .latency_policy import _EvidenceLocalClockV1
        from .lifecycle import _EVIDENCE_REASON_STATE_V1
        _native_require(type(attempt) is _EvidenceAttemptOperationV1 and type(native) is _WindowsEvidenceProcessV1
                        and native.original[1] is attempt and attempt.failure_audit is None
                        and attempt.record_original is not None and attempt.roster_original is not None
                        and type(failure_reason) is str and failure_reason in _EVIDENCE_REASON_STATE_V1
                        and failure_reason not in ("COLLECTION_COMPLETE", "FUTILITY"), "LP03_FAILURE_AUDIT_ORIGINAL_ATTEMPT")
        registration, issuer = attempt.registration, attempt.registration.issuer
        _native_require(issuer.operation is None and registration.active_attempt is None and registration.active_lane_operation is None
                        and issuer.supervisor is attempt.supervisor and any(item is native for item in issuer.supervisor._retained),
                        "LP03_FAILURE_AUDIT_REENTRY_OR_CUSTODY")
        self.attempt, self.native, self.registration, self.issuer = attempt, native, registration, issuer
        self.started = self.identity_original = self.entry_failure_observation = None
        self.prefix = None
        self.trigger_original, self.trigger_roster, self.trigger_snapshot = trigger_original, trigger_roster, None
        self.predecessor, self.failure_reason = attempt.current_state, failure_reason
        self.snapshot = self.capture_snapshot = self.capture_manifest = self.body = self.body_json = self.record = None
        self.capture_bodies, self.rows, self.refs = (), (), ()
        self.parent_refs, self.parent_rows, self.parent_original = (), (), None
        self.rows_original = self.commit_observation = self.commit_original = self.readback_observation = self.readback_original = None
        self.commit_attempt_original = None
        self.phase = "ENTRY_RETAINED"
        # Latch before the clock/lock/native accounting calls can fail. Even
        # an unobserved entry cannot be retried with a new audit allowance.
        attempt.failure_audit = self
        self.started = _EvidenceLocalClockV1.observe_v1(issuer.clock)
        self.prefix = dict(registration.consumed)
        current_triggers = tuple(entry for entry in attempt.supervisor._failure_trigger_originals if entry[0] is native)
        _native_require(type(trigger_roster) is tuple and len(current_triggers) == len(trigger_roster)
                        and all(left is right for left, right in zip(current_triggers, trigger_roster)),
                        "LP03_FAILURE_ORIGINAL_TRIGGER_ROSTER_CHANGED")
        roots = tuple(entry for entry in self.trigger_roster if entry[2] == "TRIGGER")
        _native_require(len(roots) == 1 and roots[0] is trigger_original
                        and roots[0][1] is native.original and roots[0][3] is original_error,
                        "LP03_FAILURE_ORIGINAL_TRIGGER_REQUIRED")
        # The CPU prefix remains the earlier actual settlement observation;
        # any unobserved settlement tail is conservatively charged to this
        # reserve as well. Never sample a later prefix after entry work.
        lanes = tuple(entry for entry in attempt.supervisor._lane_operation_originals if entry[0] is native)
        _native_require(len(lanes) <= 1 and ((not lanes and attempt.lane_operation is None) or
            (len(lanes) == 1 and lanes[0][1] is attempt and lanes[0][2] is attempt.lane_operation
             and lanes[0][2].original is lanes[0][3])), "LP03_FAILURE_ORIGINAL_LANE_ASSOCIATION_REQUIRED")
        self.identity_original = (attempt, native, registration, issuer, issuer.host, issuer.control_store,
            issuer.clock, registration.consumed, attempt.limits, attempt.failure_bounds, self.started,
            tuple(self.prefix.items()), self.predecessor, attempt.record_original, attempt.roster_original, failure_reason,
            lanes[0] if lanes else None, self.trigger_original, self.trigger_roster)
        self.phase = "RESERVED"

    def __copy__(self):
        raise TypeError("LP03 failure audit cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 failure audit cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 failure audit cannot be serialized")

    @staticmethod
    def _storage_capacity_v1(attempt):
        """Prelaunch schema bound, without allocating captured or base64 bytes.

        This reserves logical storage/readback work, not a prediction that CPU
        or wall time will suffice. Those original finite limits remain enforced.
        """
        from dataclasses import fields, replace
        from datetime import timedelta
        from types import MappingProxyType
        from .lifecycle import EvidenceAttemptStateV1, _EVIDENCE_REASON_STATE_V1
        from .models import EvidenceExecutionConsumptionV1
        from .migrations import REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1
        from .receipts import _lp03_spine_for_record_v1
        from .serialization import (_evidence_process_capture_metadata_v1, _encode_evidence_projection_json_v1,
                                    _evidence_canonical_object_v1, _evidence_failure_trigger_header_v1)
        from .latency_policy import _EvidenceLocalClockV1
        import sys
        from pathlib import Path
        _native_require(type(attempt) is _EvidenceAttemptOperationV1 and attempt.record_original is not None
                        and attempt.roster_original is not None, "LP03_FAILURE_CAPACITY_ORIGINAL_ATTEMPT")
        _EvidenceAttemptOperationV1._assert_original_members_v1(attempt, canonical=True)
        grant, limits, supervisor = attempt.payload, attempt.limits, attempt.supervisor
        _native_require(limits is grant.budgets is attempt.original[5] and 0 <= limits.max_output_bytes <= 1048576,
                        "LP03_FAILURE_CAPACITY_ORIGINAL_LIMITS")
        maximum = 2**63 - 1
        segment_limit = min(limits.segment_max_bytes, limits.frame_byte_limit)
        header = _evidence_process_capture_metadata_v1(grant_ref=grant.grant_ref, fence_ref=grant.fence_ref,
            supervisor_instance_ref=supervisor.instance_ref, stream="STDOUT", ordinal=maximum, count=maximum,
            first=maximum, size=maximum, captured=maximum, observed=maximum, discarded=maximum,
            eof=False, complete=False)
        header_json = deterministic_json(header)
        chunk = ((segment_limit - len(header_json.encode("utf-8"))) // 4) * 3
        _native_require(0 < segment_limit <= 65536 and chunk > 0, "LP03_FAILURE_CAPTURE_HEADER_CAPACITY")
        # Two streams can each have one final partial segment. Interior chunks
        # are multiples of three, so only their two final base64 pads remain.
        segments = ((limits.max_output_bytes + chunk - 1) // chunk + 1) if limits.max_output_bytes else 0
        encoded_bytes = 4 * ((limits.max_output_bytes + 2) // 3) + (4 if limits.max_output_bytes else 0)
        _native_require(segments <= min(limits.max_persistent_operations, 4096), "LP03_FAILURE_CAPTURE_ROSTER_CAPACITY")
        observation_ref = grant.grant_ref + "::PROCESS:FAILURE"
        state_ref = grant.grant_ref + "::STATE:FAILURE"
        created = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=maximum // 1000)
        longest_capture_ref = observation_ref + "::CAPTURE:STDOUT:" + str(max(0, segments - 1))
        for ref in (observation_ref, state_ref, grant.grant_ref + "::RESERVATION", longest_capture_ref,
                    longest_capture_ref + "::RESULT"):
            _native_ident(ref)
        sample_rows = _evidence_failure_claim_rows_v1(longest_capture_ref, header_json,
            observation_ref, created, operation="LP03_SVC_PROCESS_CAPTURE")
        # ASCII base64 is copied exactly twice: canonical_request_json and its
        # quoted appearance in payload_json. No base64 data is allocated here.
        capture_bytes = segments * sum(_evidence_failure_row_bytes_v1(row) for row in sample_rows) + 2 * encoded_bytes
        observation_rows = _evidence_failure_claim_rows_v1(observation_ref, "{}", state_ref, created,
            operation="LP03_SVC_PROCESS_FAILURE_AUDIT")
        # A canonical JSON byte needs at most two bytes when quoted inside the
        # claim payload. The direct canonical column is the third copy bound.
        observation_bytes = sum(_evidence_failure_row_bytes_v1(row) for row in observation_rows) + 3 * 16384
        reasons = tuple(reason for reason in _EVIDENCE_REASON_STATE_V1 if reason not in ("COLLECTION_COMPLETE", "FUTILITY"))
        consumption = EvidenceExecutionConsumptionV1(**{member.name:
            limits.aggregate_budget_ref if member.name == "aggregate_budget_ref" else maximum
            for member in fields(EvidenceExecutionConsumptionV1)})
        bound_state = replace(attempt.record_original[2], record_id=state_ref, created_wall_ns=maximum,
            causation_ref=state_ref, prior_state_ref=state_ref, state=EvidenceAttemptStateV1.TERMINATION_UNKNOWN,
            all_reason_codes=reasons, primary_reason="TERMINATION_UNKNOWN", event_ordinal=maximum,
            process_observation_ref_or_absence=observation_ref, consumed_budget=consumption,
            currentness_observation_ref=state_ref)
        spine = _lp03_spine_for_record_v1(bound_state, sequence=maximum, trace_ref=attempt.registration.preparation.trace_ref)
        state_row = (spine.record_id, spine.effective_at.isoformat(), spine.recorded_at.isoformat(), spine.aggregate_id,
                     deterministic_json(spine))
        state_bytes = _evidence_failure_row_bytes_v1(state_row)
        state_bytes += max(len(state.value) for state in EvidenceAttemptStateV1) - len("TERMINATION_UNKNOWN")
        state_bytes += max(len(reason) for reason in reasons) - len("TERMINATION_UNKNOWN")
        # Bound the entire maximum-capture manifest, not only its reference
        # array. This is virtual sizing data, never a factual observation.
        reference = longest_capture_ref
        manifest = dict(schema_version="1.0", operation="SVC_PROCESS_CAPTURE_MANIFEST_V1",
            observation_ref=observation_ref, grant_ref=grant.grant_ref, fence_ref=grant.fence_ref,
            supervisor_instance_ref=supervisor.instance_ref, capture_complete=False,
            streams=[dict(stream=stream, observed_byte_count=maximum, captured_byte_count=maximum,
                discarded_byte_count=maximum, eof=False, segment_refs=[]) for stream in ("STDOUT", "STDERR")])
        manifest_base = _encode_evidence_projection_json_v1(manifest, maximum_bytes=16384, maximum_nodes=4096)
        manifest_bound = len(manifest_base) + segments * len(deterministic_json(reference).encode("utf-8")) + max(0, segments - 1)
        _native_require(manifest_bound <= 16384, "LP03_FAILURE_MAXIMUM_MANIFEST_UNREPRESENTABLE")
        manifest["streams"][0]["segment_refs"] = [reference] * segments
        clock = attempt.registration.issuer.clock
        image_path = str(Path(sys._base_executable).resolve())
        native = dict(process_identity=[maximum, maximum, image_path], exit_code=0xffffffff,
            active_processes=maximum, total_processes=maximum, terminated_processes=maximum,
            assigned_process_ids=[maximum] * 4, effective_limit_flags=maximum,
            effective_active_process_limit=maximum, cpu_ns=maximum, process_memory_high_water_bytes=maximum,
            job_memory_high_water_bytes=maximum)
        point = [maximum] * 3
        process_ref = "LP03-PROCESS::" + str(maximum) + ":" + str(maximum) + ":" + clock.boot_identity_ref.split("::", 1)[1]
        _native_ident(process_ref)
        measurement = dict(clock_domain_id=clock.clock_domain_id, boot_identity_ref=clock.boot_identity_ref,
            process_identity_ref=process_ref, clock_declarations=_evidence_canonical_object_v1(
                deterministic_json(_EvidenceLocalClockV1.declaration_v1(clock)).encode("utf-8")),
            started=point, completed=point, duration_ns=maximum, cpu_ns=maximum, outcome="SUCCESS")
        envelope_body = dict(schema_version="1.0", operation="SVC_PROCESS_FAILURE_AUDIT_V1",
            observation_ref=observation_ref, grant_ref=grant.grant_ref, fence_ref=grant.fence_ref,
            supervisor_instance_ref=supervisor.instance_ref, predecessor_state_ref=state_ref,
            clock_domain_id=clock.clock_domain_id, boot_identity_ref=clock.boot_identity_ref,
            accounting_observed_at=point, consumed_prefix={member.name: getattr(consumption, member.name)
                                                         for member in fields(EvidenceExecutionConsumptionV1)},
            final_accounting_tail="UNRECONCILED_FULL_RESERVATION_RETAINED",
            lifecycle_disposition=max(("ORIGINAL_PREDECESSOR_RETAINED", "NONPOSITIVE_SUCCESSOR_REQUESTED"), key=len),
            reservation_ref=grant.grant_ref + "::RESERVATION", failure_bounds=point, reason_codes=reasons,
            primary_reason=max(reasons, key=len), custody=dict(kind="TERMINATION_UNKNOWN", native_observation_or_absence=native,
                native_observed_between_or_absence=[point, point], stdout_eof=False, stderr_eof=False,
                controller_joined=False, drains_joined=False, cleanup_complete=False),
            capture_manifest_or_absence=manifest, capture_observed_between_or_absence=[point, point],
            controller_error_count=maximum, drain_error_count=maximum, cleanup_error_count=maximum,
            diagnostic_errors={domain: dict(retained_entries=[], omitted_entry_count=maximum, complete=False)
                               for domain in ("controller", "drain", "cleanup")},
            diagnostic_observed_between=[point, point], invocation_measurement_or_absence=measurement,
            trigger_error=_evidence_failure_trigger_header_v1(maximum, cause_present=True, context_present=True,
                suppress_context=False, observed_between=[point, point], secondary_error_count=maximum))
        # Error entries use only the remaining actual whole-body bytes. Their
        # exact omitted counts/completeness always fit this fixed envelope;
        # incomplete diagnostic retention cannot authorize slot release.
        envelope_raw = _encode_evidence_projection_json_v1(envelope_body, maximum_bytes=16384, maximum_nodes=4096)
        persistent_bytes = capture_bytes + observation_bytes + state_bytes
        # The original six admission rows plus at most three positive process
        # observations and the single RUNNING successor are the complete
        # predecessor lineage. No recursive acquisition of audit output.
        parent_bytes = sum(_evidence_failure_row_bytes_v1(row) for row in attempt.readback_rows)
        for stage in ("SUSPENDED", "RUNNING", "TERMINAL"):
            rows = _evidence_failure_claim_rows_v1(grant.grant_ref + "::PROCESS:" + stage, "{}", state_ref,
                created, operation="LP03_SVC_PROCESS_OBSERVATION_APPEND")
            parent_bytes += sum(_evidence_failure_row_bytes_v1(row) for row in rows) + 3 * 16384
        parent_bytes += state_bytes
        parent_count = len(attempt.readback_rows) + 7
        row_count = 2 * segments + 3
        tables = len(REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1)
        # An independent connection verifies one PRAGMA row. Its longest
        # returned database path is the original adapter's exact path.
        metadata_bytes = len(attempt.registration.issuer.control_store.database_path.encode("utf-8")) + 5
        read_count = parent_count + row_count + tables + 1
        read_bytes = parent_bytes + persistent_bytes + 20 * 7 * (parent_count + row_count) + tables + metadata_bytes
        operations = parent_count + row_count + tables + 1 + row_count + 3  # BEGIN, COMMIT, reserved ROLLBACK
        bound = dict(input_reads=read_count, input_bytes=read_bytes,
            persistent_operations=operations, persistent_bytes=persistent_bytes,
            maximum_capture_segments=segments, maximum_capture_chunk=chunk,
            maximum_manifest_bytes=manifest_bound, minimum_failure_body_bytes=len(envelope_raw), launch_image_path=image_path)
        for field in ("input_reads", "input_bytes", "persistent_operations", "persistent_bytes"):
            _native_require(bound[field] <= getattr(limits, "reserved_failure_" + field),
                            "LP03_FAILURE_AUDIT_RESERVE_INSUFFICIENT:" + field)
        return MappingProxyType(bound)

    def _assert_original_v1(self, *, custody=True, in_operation=True):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        _native_require(type(self) is _EvidenceAttemptFailureAuditV1 and type(self.identity_original) is tuple
                        and len(self.identity_original) == 19, "LP03_FAILURE_AUDIT_ORIGINAL_REQUIRED")
        original = self.identity_original
        _native_require(self.attempt is original[0] and self.native is original[1] and self.registration is original[2]
                        and self.issuer is original[3] and self.issuer.host is original[4] and self.issuer.control_store is original[5]
                        and self.issuer.clock is original[6] and self.registration.consumed is original[7]
                        and type(self.registration.consumed) is dict and self.attempt.limits is original[8]
                        and self.attempt.failure_bounds is original[9] is self.attempt.original[9]
                        and self.started is original[10] and tuple(self.prefix.items()) == original[11]
                        and self.predecessor is original[12] and self.attempt.record_original is original[13]
                        and self.attempt.roster_original is original[14] and self.failure_reason == original[15]
                        and self.trigger_original is original[17] and self.trigger_roster is original[18]
                        and self.attempt.failure_audit is self
                        and (not in_operation or (self.issuer.operation is self
                            and self.issuer.lock._is_owned() and self.registration.active_attempt is None))
                        and self.issuer.registrations.get(self.registration.preparation.grant_record.record_id) is self.registration
                        and self.registration.attempts.get((self.attempt.request.lane, self.attempt.request.attempt_ordinal)) is self.attempt
                        and self.native.original[1] is self.attempt, "LP03_FAILURE_AUDIT_BINDING_CHANGED")
        _EvidenceAttemptOperationV1._assert_original_members_v1(self.attempt, canonical=False)
        triggers = tuple(entry for entry in self.attempt.supervisor._failure_trigger_originals if entry[0] is self.native)
        if (not in_operation and self.phase == "COMMIT_OR_OBSERVATION_UNRESOLVED"
                and len(triggers) == len(self.trigger_roster) + 1):
            # SVC retains the failed audit call after the frozen original body.
            # This extra diagnostic contributes no terminal or readback proof.
            late = triggers[-1]
            _native_require(type(late) is tuple and len(late) == 10 and late[0] is self.native
                            and late[1] is self.native.original and late[2] == "FAILURE_AUDIT"
                            and isinstance(late[3], BaseException), "LP03_FAILURE_ORIGINAL_TRIGGER_ROSTER_CHANGED")
            triggers = triggers[:-1]
        _native_require(len(triggers) == len(self.trigger_roster)
                        and all(left is right for left, right in zip(triggers, self.trigger_roster)),
                        "LP03_FAILURE_ORIGINAL_TRIGGER_ROSTER_CHANGED")
        lanes = tuple(entry for entry in self.attempt.supervisor._lane_operation_originals if entry[0] is self.native)
        _native_require((original[16] is None and not lanes and self.attempt.lane_operation is None) or
            (original[16] is not None and len(lanes) == 1 and lanes[0] is original[16]
             and lanes[0][1] is self.attempt and lanes[0][2] is self.attempt.lane_operation
             and lanes[0][2].original is lanes[0][3]), "LP03_FAILURE_ORIGINAL_LANE_ASSOCIATION_CHANGED")
        EvidenceProcessSupervisorV1._assert_custody_v1(self.attempt.supervisor)
        if self.snapshot is not None:
            EvidenceProcessSupervisorV1._require_failure_observation_v1(self.attempt.supervisor, self, self.snapshot)
        if self.parent_original is not None:
            pinned = self.parent_original
            _native_require(self.parent_refs is pinned[0] and self.parent_rows is pinned[1]
                            and self.attempt.roster_original is pinned[2] and self.attempt.observation_appends is pinned[3]
                            and self.native._observation_originals is pinned[5],
                            "LP03_FAILURE_PARENT_ROSTER_CHANGED")
            for append, rows, refs, original in pinned[4]:
                _native_require(append.rows is rows and append.refs is refs and append.original is original
                                and append.phase == "COMMITTED_AND_READBACK", "LP03_FAILURE_PARENT_APPEND_CHANGED")
            lane = pinned[6]
            _native_require((lane is None and self.attempt.lane_operation is None) or
                (lane is not None and self.attempt.lane_operation is lane[0] and lane[0].finalization_phase == lane[1]
                 and lane[0].final_original is lane[2] and lane[0].final_commit_original is lane[3]
                 and lane[0].final_readback_original is lane[4]), "LP03_FAILURE_LANE_FINALIZATION_CHANGED")
        if self.rows_original is not None:
            pinned = self.rows_original
            _native_require(all(left is right for left, right in zip(
                (self.rows, self.refs, self.record, self.body_json, self.body, self.capture_bodies, self.snapshot), pinned[:7]))
                and self.body_json.encode("utf-8") == self.snapshot[4], "LP03_FAILURE_PREPARED_ROWS_CHANGED")
        for observation, pinned in ((self.commit_observation, self.commit_original),
                                     (self.readback_observation, self.readback_original)):
            _native_require((observation is None and pinned is None) or (pinned is not None
                and observation is pinned[0] and self.rows_original is pinned[1]), "LP03_FAILURE_OBSERVATION_CHANGED")
        if custody:
            EvidenceHostBindingV1._assert_local_binding_v1(self.issuer.host)
            _EvidenceBoundStoreV1._require_original_objects_v1(
                self.issuer.control_store._evidence_store_binding_v1, self.issuer.host, self.issuer.control_store)

    def _room_v1(self, **increments):
        _EvidenceAttemptFailureAuditV1._assert_original_v1(self, custody=False)
        totals = dict(self.registration.consumed)
        for name, amount in increments.items():
            _native_require(name in totals and type(amount) is int and amount >= 0, "LP03_FAILURE_AUDIT_CHARGE_TYPE")
            totals[name] += amount
        limits, attempt_prefix = self.attempt.limits, self.attempt.prefix
        aggregate = self.registration.envelope_entry[3].aggregate_execution_limits
        retained = _EvidenceRegistrationOperationV1._retained_capacity_v1(self.registration)
        for counter, reserve, total in (
                ("record_reads", "reserved_failure_input_reads", "max_input_reads"),
                ("query_result_records", "reserved_failure_input_reads", "max_input_reads"),
                ("read_bytes", "reserved_failure_input_bytes", "max_input_bytes"),
                ("control_bytes", "reserved_failure_persistent_bytes", "max_persistent_bytes")):
            _native_require(0 <= totals[counter] - self.prefix[counter] <= getattr(limits, reserve)
                            and 0 <= totals[counter] - attempt_prefix[counter] <= getattr(limits, total)
                            and totals[counter] + retained[total] <= getattr(aggregate, total),
                            "LP03_FAILURE_AUDIT_RESOURCE_EXHAUSTED:" + counter)
        operations = totals["owner_queries"] + totals["control_writes"]
        _native_require(0 <= operations - self.prefix["owner_queries"] - self.prefix["control_writes"]
                            <= limits.reserved_failure_persistent_operations
                        and 0 <= operations - attempt_prefix["owner_queries"] - attempt_prefix["control_writes"]
                            <= limits.max_persistent_operations
                        and operations + retained["max_persistent_operations"] <= aggregate.max_persistent_operations,
                        "LP03_FAILURE_AUDIT_RESOURCE_EXHAUSTED:operations")
        # Prior settlement and parent-process overhead are already in totals.
        # The nominal reserve cannot replenish a total that they consumed.
        attempt_cpu_start = self.attempt.started[2] - self.registration.started_cpu_ns + self.attempt.child_cpu_prefix
        _native_require(0 <= totals["cpu_ns"] - self.prefix["cpu_ns"] <= limits.reserved_failure_cpu_ns
                        and 0 <= totals["cpu_ns"] - attempt_cpu_start <= limits.max_cpu_ns
                        and totals["cpu_ns"] + retained["max_cpu_ns"] <= aggregate.max_cpu_ns,
                        "LP03_FAILURE_AUDIT_RESOURCE_EXHAUSTED:cpu")
        registration_start = self.registration.deadline.admitted_monotonic_ns
        _native_require(totals["wall_ns"] + registration_start < min(self.attempt.failure_bounds[2],
                            self.started[1] + limits.reserved_failure_wall_ns)
                        and totals["wall_ns"] + retained["max_wall_ns"] <= aggregate.max_wall_ns,
                        "LP03_FAILURE_AUDIT_RESOURCE_EXHAUSTED:wall")

    def _charge_v1(self, **increments):
        _EvidenceAttemptFailureAuditV1._assert_original_v1(self, custody=False)
        for name, amount in increments.items():
            _native_require(name in self.registration.consumed and type(amount) is int and amount >= 0,
                            "LP03_FAILURE_AUDIT_CHARGE_TYPE")
            self.registration.consumed[name] += amount
        _EvidenceAttemptFailureAuditV1._room_v1(self)

    def _check_current_v1(self):
        """Current original integrity custody, not expired execution authority."""
        from .latency_policy import _EvidenceLocalClockV1
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        _EvidenceAttemptFailureAuditV1._assert_original_v1(self)
        _native_require(_EvidenceRegistrationOperationV1._observe_accounting_v1(self.registration),
                        "LP03_FAILURE_AUDIT_ACCOUNTING_UNAVAILABLE")
        observed = _EvidenceLocalClockV1.observe_v1(self.issuer.clock)
        self.registration.consumed["wall_ns"] = max(self.registration.consumed["wall_ns"],
            observed[1] - self.registration.deadline.admitted_monotonic_ns)
        usage = EvidenceProcessSupervisorV1._execution_usage_v1(self.attempt.supervisor, self.registration)
        self.registration.consumed["cpu_ns"] = max(self.registration.consumed["cpu_ns"],
            observed[2] - self.registration.started_cpu_ns + usage["cpu_ns"])
        _EvidenceAttemptFailureAuditV1._room_v1(self)
        _EvidenceAttemptFailureAuditV1._assert_original_v1(self, custody=False)
        return observed

    def _prepare_v1(self):
        from dataclasses import replace
        from datetime import timedelta
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        from .lifecycle import EvidenceAttemptStateV1, EVIDENCE_ATTEMPT_STATE_MACHINE_V1, _EVIDENCE_REASON_STATE_V1
        from .models import EvidenceExecutionConsumptionV1
        from .receipts import _lp03_spine_for_record_v1
        from .serialization import _evidence_canonical_object_v1, _evidence_process_failure_body_v1
        from .migrations import REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1
        _native_require(self.phase == "RESERVED" and self.snapshot is None and self.rows_original is None,
                        "LP03_FAILURE_ALREADY_PREPARED")
        _EvidenceAttemptFailureAuditV1._check_current_v1(self)
        attempt = self.attempt
        appends = attempt.observation_appends
        snapshots = self.native._observation_originals
        if not (type(appends) is tuple and type(snapshots) is tuple and len(appends) == len(snapshots) <= 3
                and tuple(item[0] for item in snapshots) == ("SUSPENDED", "RUNNING", "TERMINAL")[:len(snapshots)]
                and all(type(append) is _EvidenceAttemptObservationAppendV1 and append.attempt is attempt
                        and append.native is self.native and append.snapshot is snapshot and append.stage == snapshot[0]
                        for append, snapshot in zip(appends, snapshots, strict=True))):
            raise ContractValidationError(ReasonCode.EVIDENCE_PREFIX_INCOMPLETE,
                "LP03_FAILURE_COMPLETE_PROCESS_PREFIX_REQUIRED")
        # An unresolved earlier native COMMIT cannot be wished away. Retain
        # this original audit reservation and custody if exact lineage is not
        # available; never write a competing successor from a guessed state.
        _native_require(all(append.phase == "COMMITTED_AND_READBACK" for append in appends),
                        "LP03_FAILURE_PARENT_COMMIT_UNRESOLVED")
        for append in appends:
            _EvidenceAttemptObservationAppendV1._assert_original_v1(append)
        self.parent_refs = (*attempt.readback_refs, *(ref for append in appends for ref in append.refs))
        self.parent_rows = (*attempt.readback_rows, *(row for append in appends for row in append.rows))
        lane = attempt.lane_operation
        lane_original = None if lane is None else (lane, lane.finalization_phase, lane.final_original,
                                                   lane.final_commit_original, lane.final_readback_original)
        self.parent_original = (self.parent_refs, self.parent_rows, attempt.roster_original, appends,
            tuple((append, append.rows, append.refs, append.original) for append in appends), snapshots, lane_original)
        self.snapshot = EvidenceProcessSupervisorV1._capture_failure_observation_v1(attempt.supervisor, self)
        self.body_json = self.snapshot[4].decode("utf-8", errors="strict")
        body = _evidence_canonical_object_v1(self.snapshot[4], max_bytes=16384)
        state = EvidenceAttemptStateV1(_EVIDENCE_REASON_STATE_V1[body["primary_reason"]])
        state_gap = body["lifecycle_disposition"] == "ORIGINAL_PREDECESSOR_RETAINED"
        _native_require(state_gap == _EvidenceAttemptFailureAuditV1._state_gap_v1(self, body["custody"]["kind"]),
                        "LP03_FAILURE_LIFECYCLE_DISPOSITION_CHANGED")
        if self.predecessor.state is EvidenceAttemptStateV1.ADMITTED and state is not EvidenceAttemptStateV1.TERMINATION_UNKNOWN:
            if not state_gap:
                _native_require(body["custody"]["kind"] == "NO_CHILD", "LP03_FAILURE_NOT_STARTED_REQUIRES_NO_CHILD")
                state = (EvidenceAttemptStateV1.CANCELLED_NOT_STARTED if state is EvidenceAttemptStateV1.CANCELLED_NOT_STARTED
                         else EvidenceAttemptStateV1.FAILED_TO_START)
        _native_require(state_gap or (self.predecessor.state.value, state.value) in EVIDENCE_ATTEMPT_STATE_MACHINE_V1.allowed_transitions,
                        "LP03_FAILURE_STATE_TRANSITION")
        state_ref = attempt.payload.grant_ref + "::STATE:FAILURE"
        state_rows = ()
        if not state_gap:
            self.record = replace(self.predecessor, record_id=state_ref, created_wall_ns=body["accounting_observed_at"][0],
                causation_ref=self.predecessor.record_id, prior_state_ref=self.predecessor.record_id, state=state,
                all_reason_codes=tuple(body["reason_codes"]), primary_reason=body["primary_reason"],
                event_ordinal=body["consumed_prefix"]["events"], process_observation_ref_or_absence=body["observation_ref"],
                consumed_budget=EvidenceExecutionConsumptionV1.from_canonical_mapping(body["consumed_prefix"]),
                currentness_observation_ref=state_ref)
            spine = _lp03_spine_for_record_v1(self.record, sequence=self.registration.preparation.state_ordinal + 14,
                                            trace_ref=self.registration.preparation.trace_ref)
            state_rows = ((spine.record_id, spine.effective_at.isoformat(), spine.recorded_at.isoformat(), spine.aggregate_id,
                          deterministic_json(spine)),)
        # A created child with no committed RUNNING successor is an actual
        # lifecycle gap. Preserve its native/capture observation against the
        # unchanged predecessor, without inventing RUNNING or no-child proof.
        created = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=body["accounting_observed_at"][0] // 1000)
        result_ref = self.predecessor.record_id if state_gap else state_ref
        observation_rows = _evidence_failure_claim_rows_v1(body["observation_ref"], self.body_json, result_ref, created,
            operation="LP03_SVC_PROCESS_FAILURE_AUDIT")
        plan = self.snapshot[5]
        segment_plan = () if plan is None else plan[3]
        virtual_rows, encoded_extra = [], 0
        for _stream, _first, _size, metadata, encoded_size in segment_plan:
            header = deterministic_json(metadata)
            virtual_rows.extend(_evidence_failure_claim_rows_v1(metadata["capture_segment_ref"], header,
                body["observation_ref"], created, operation="LP03_SVC_PROCESS_CAPTURE"))
            encoded_extra += 2 * (encoded_size - len(header.encode("utf-8")))
        virtual_rows = (*virtual_rows, *observation_rows, *state_rows)
        row_bytes = sum(_evidence_failure_row_bytes_v1(row) for row in virtual_rows) + encoded_extra
        row_count, parents, tables = len(virtual_rows), len(self.parent_rows), len(REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1)
        parent_bytes = sum(_evidence_failure_row_bytes_v1(row) for row in self.parent_rows)
        metadata_bytes = len(self.issuer.control_store.database_path.encode("utf-8")) + 5
        # This exact preflight precedes every base64 allocation and native
        # BEGIN. It includes all column copies and independent full readback.
        _EvidenceAttemptFailureAuditV1._room_v1(self, record_reads=parents + row_count + tables + 1,
            query_result_records=parents + row_count + tables + 1,
            read_bytes=parent_bytes + row_bytes + 20 * 7 * (parents + row_count) + tables + metadata_bytes,
            owner_queries=parents + row_count + tables + 1, control_writes=row_count + 3, control_bytes=row_bytes)
        _EvidenceAttemptFailureAuditV1._check_current_v1(self)

        if plan is not None:
            self.capture_manifest, self.capture_bodies = EvidenceProcessSupervisorV1._capture_manifest_v1(
                attempt.supervisor, self.native, capture_snapshot=self.snapshot[6])
            _native_require(self.capture_manifest == plan[4] and len(self.capture_bodies) == len(segment_plan)
                            and all(len(raw) == entry[4] for raw, entry in zip(self.capture_bodies, segment_plan)),
                            "LP03_FAILURE_CAPTURE_PLAN_CHANGED")
            self.capture_snapshot = self.snapshot[6]
        self.body = _evidence_process_failure_body_v1(self.snapshot[4], capture_segment_bodies=self.capture_bodies,
            maximum_capture_bytes=attempt.limits.max_output_bytes,
            maximum_segment_bytes=min(attempt.limits.segment_max_bytes, attempt.limits.frame_byte_limit),
            maximum_segments=attempt.limits.max_persistent_operations, maximum_total_bytes=attempt.limits.max_persistent_bytes)
        claims = []
        for raw, entry in zip(self.capture_bodies, segment_plan):
            claims.extend(_evidence_failure_claim_rows_v1(entry[3]["capture_segment_ref"], raw.decode("utf-8", errors="strict"),
                body["observation_ref"], created, operation="LP03_SVC_PROCESS_CAPTURE"))
        self.rows = (*claims, *observation_rows, *state_rows)
        self.refs = (*(("idempotency_claims", row[0]) for row in (*claims, *observation_rows)),
                     *(("receipt_records", row[0]) for row in state_rows))
        _native_require(sum(_evidence_failure_row_bytes_v1(row) for row in self.rows) == row_bytes
                        and len(self.refs) == row_count and len({ref for _table, ref in self.refs}) == row_count,
                        "LP03_FAILURE_ENCODED_ROW_PLAN_CHANGED")
        self.rows_original = (self.rows, self.refs, self.record, self.body_json, self.body, self.capture_bodies,
                              self.snapshot, deterministic_json(self.record))
        self.phase = "PREPARED"
        _EvidenceAttemptFailureAuditV1._check_current_v1(self)

    def _state_gap_v1(self, custody_kind):
        from .lifecycle import EvidenceAttemptStateV1
        association = self.identity_original[16]
        lane = None if association is None else association[2]
        # A CONTROL finalization that entered its transaction may already have
        # published the next state. Preserve an observation, never a competing
        # successor, until its original commit/readback custody is reconciled.
        finalization_started = lane is not None and (lane.finalization_phase != "NOT_STARTED"
            or lane.final_original is not None or lane.final_commit_original is not None or lane.final_readback_original is not None)
        return finalization_started or (self.predecessor.state is EvidenceAttemptStateV1.ADMITTED and custody_kind == "TERMINAL")

    def _finish_v1(self):
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        _native_require(self.phase == "COMMITTED_AND_READBACK" and self.commit_original is not None
                        and self.readback_original is not None and self.attempt.current_state is self.predecessor
                        and self.commit_observation[1] <= self.readback_observation[1],
                        "LP03_FAILURE_COMMIT_READBACK_UNRESOLVED")
        _native_require(self.attempt.supervisor._active is self.native, "LP03_FAILURE_ORIGINAL_SLOT_CHANGED")
        observed = _EvidenceAttemptFailureAuditV1._check_current_v1(self)
        consumption = _EvidenceAttemptOperationV1._consumption_v1(self.attempt)
        _native_require(deterministic_json(self.record) == self.rows_original[7], "LP03_FAILURE_STATE_BODY_CHANGED")
        native, supervisor = self.native, self.attempt.supervisor
        cleanup = self.snapshot[9]
        releasable = (self.record is not None and self.body["custody"]["kind"] in ("TERMINAL", "NO_CHILD")
            and self.body["custody"]["cleanup_complete"] and cleanup is not None and not cleanup[3]
            and all(summary["complete"] for summary in self.body["diagnostic_errors"].values())
            and self.body["trigger_error"]["complete"]
            and not native.cleanup_errors and not supervisor._unresolved
            and native.phase in ("TERMINAL_RETAINED_AND_CLOSED", "FAILED_TO_START_NO_CHILD")
            and native._native_custody is cleanup[4] and native._native_custody[:3] == (None, None, None)
            and consumption.active_workers == 0)
        if releasable:
            retained = _EvidenceRegistrationOperationV1._retained_capacity_v1(self.registration)
            totals, aggregate = self.registration.consumed, self.registration.envelope_entry[3].aggregate_execution_limits
            usage = EvidenceProcessSupervisorV1._execution_usage_v1(supervisor, self.registration)
            measured = dict(max_wall_ns=totals["wall_ns"], max_cpu_ns=totals["cpu_ns"],
                max_input_reads=max(totals["record_reads"], totals["query_result_records"]), max_input_bytes=totals["read_bytes"],
                max_persistent_operations=totals["owner_queries"] + totals["control_writes"], max_persistent_bytes=totals["control_bytes"],
                max_events=usage["events"], max_callbacks=usage["callbacks"], max_coordinates=usage["coordinates"],
                max_computations=usage["computations"], max_output_bytes=usage["output_bytes"])
            _native_require(all(measured[name] + retained[name] + getattr(self.attempt.limits, name) <= getattr(aggregate, name)
                                for name in retained), "LP03_FAILURE_FULL_RESERVATION_UNAVAILABLE")
        # All fallible native accounting precedes publication. The final tail
        # below is plain original-object/data comparison, with no clock, SQL,
        # host getter or native refresh after the slot-release prerequisites.
        pinned = (self.rows_original, self.snapshot, self.readback_original, self.commit_original,
                  self.attempt.current_state_original, supervisor, native, cleanup)
        observed = _EvidenceAttemptFailureAuditV1._check_current_v1(self)
        consumption = _EvidenceAttemptOperationV1._consumption_v1(self.attempt)
        _native_require(self.rows_original is pinned[0] and self.snapshot is pinned[1]
                        and self.readback_original is pinned[2] and self.commit_original is pinned[3]
                        and self.attempt.current_state_original is pinned[4] and self.attempt.current_state is self.predecessor
                        and self.attempt.supervisor is pinned[5] is self.issuer.supervisor and self.native is pinned[6]
                        and supervisor._active is native and self.snapshot[9] is pinned[7]
                        and self.record is self.rows_original[2] and self.body is self.rows_original[4]
                        and deterministic_json(self.record) == self.rows_original[7],
                        "LP03_FAILURE_FINAL_ORIGINAL_CUSTODY_CHANGED")
        if releasable:
            _native_require(not supervisor._unresolved and not native.cleanup_errors and cleanup is not None
                            and not cleanup[3] and native._native_custody is cleanup[4]
                            and native._native_custody[:3] == (None, None, None)
                            and native.phase in ("TERMINAL_RETAINED_AND_CLOSED", "FAILED_TO_START_NO_CHILD")
                            and consumption.active_workers == 0, "LP03_FAILURE_FINAL_TERMINAL_CUSTODY_CHANGED")
            measured["max_wall_ns"], measured["max_cpu_ns"] = totals["wall_ns"], totals["cpu_ns"]
            _native_require(all(measured[name] + retained[name] + getattr(self.attempt.limits, name) <= getattr(aggregate, name)
                                for name in retained), "LP03_FAILURE_FULL_RESERVATION_UNAVAILABLE")
        if self.record is not None:
            self.attempt.current_state = self.record
            self.attempt.current_state_original = (self.record, self.rows_original[7])
        if releasable:
            proof = (self, self.record, native, self.snapshot, self.readback_original, observed, consumption)
            self.attempt.terminal_original = self.attempt.terminal_proof = proof
            self.registration.retained_reservations = (*self.registration.retained_reservations,
                (self.attempt, self.attempt.limits, self.attempt.roster_original, proof))
            self.phase, self.attempt.phase = "COMPLETED_RESERVED", "FAILURE_AUDITED_RESERVED"
            supervisor._active = None
        else:
            self.phase, self.attempt.phase = "COMMITTED_QUARANTINED", "FAILURE_AUDITED_QUARANTINED"
            supervisor._unresolved = True
        return self

    def _require_terminal_v1(self):
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        from .lifecycle import EvidenceAttemptStateV1
        _EvidenceAttemptFailureAuditV1._assert_original_v1(self, in_operation=False)
        proof, attempt = self.attempt.terminal_original, self.attempt
        _native_require(type(proof) is tuple and len(proof) == 7 and proof is attempt.terminal_proof
                        and proof[0] is self and proof[1] is self.record is attempt.current_state
                        and proof[2] is self.native and proof[3] is self.snapshot and proof[4] is self.readback_original
                        and self.phase == "COMPLETED_RESERVED" and attempt.phase == "FAILURE_AUDITED_RESERVED"
                        and self.commit_original is not None and self.readback_original is not None
                        and proof[5][1] >= self.readback_observation[1] and proof[6].active_workers == 0
                        and proof[6].cpu_ns <= attempt.limits.max_cpu_ns and proof[6].wall_ns <= attempt.limits.max_wall_ns
                        and self.record.state not in (EvidenceAttemptStateV1.TERMINATION_UNKNOWN, EvidenceAttemptStateV1.COLLECTION_COMPLETE)
                        and self.body["custody"]["cleanup_complete"] and self.snapshot[9] is not None
                        and self.body["trigger_error"]["complete"]
                        and not self.snapshot[9][3] and not self.native.cleanup_errors
                        and self.native._native_custody is self.snapshot[9][4]
                        and self.native._native_custody[:3] == (None, None, None)
                        and self.native.phase in ("TERMINAL_RETAINED_AND_CLOSED", "FAILED_TO_START_NO_CHILD")
                        and attempt.supervisor._active is None, "LP03_FAILURE_TERMINAL_CUSTODY_UNRESOLVED")
        _EvidenceAttemptOperationV1._assert_original_members_v1(attempt, canonical=True)
        EvidenceProcessSupervisorV1._assert_original_v1(attempt.supervisor)
        return proof


class _EvidenceAttemptObservationAppendV1:
    """One exact original SVC-to-CONTROL append, retained across failed writes."""

    __slots__ = ("attempt", "native", "stage", "snapshot", "body", "body_json", "predecessor", "record",
                 "rows", "refs", "original", "phase", "commit_observation", "readback_observation", "identity_original")

    def __init__(self, attempt, native, stage):
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        from .serialization import _evidence_process_observation_body_v1
        _native_require(type(attempt) is _EvidenceAttemptOperationV1 and attempt.phase == "COMMITTED_AND_READBACK"
                        and not any(entry.stage == stage for entry in attempt.observation_appends),
                        "LP03_PROCESS_OBSERVATION_ALREADY_RESERVED")
        self.attempt, self.native, self.stage = attempt, native, stage
        self.snapshot = EvidenceProcessSupervisorV1._capture_process_observation_v1(attempt.supervisor, native, stage)
        self.body_json = self.snapshot[1]
        self.body = _evidence_process_observation_body_v1(self.body_json.encode("utf-8"))
        self.predecessor, self.record = attempt.current_state, None
        self.identity_original = (attempt, native, stage, self.snapshot, self.body, self.body_json, self.predecessor)
        self.rows, self.refs, self.original = (), (), None
        self.phase, self.commit_observation, self.readback_observation = "RESERVED", None, None
        attempt.observation_appends = (*attempt.observation_appends, self)

    def __copy__(self):
        raise TypeError("LP03 observation append cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 observation append cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 observation append cannot be serialized")

    def _assert_original_v1(self, *, canonical=True):
        from ...service.pr169_svc1_resolvers import EvidenceProcessSupervisorV1
        _native_require(type(self) is _EvidenceAttemptObservationAppendV1
                        and any(entry is self for entry in self.attempt.observation_appends), "LP03_PROCESS_APPEND_NOT_ORIGINAL")
        original = self.identity_original
        _native_require(type(original) is tuple and len(original) == 7 and all(left is right for left, right in zip(
            (self.attempt, self.native, self.stage, self.snapshot, self.body, self.body_json, self.predecessor), original))
                        and self.stage == self.snapshot[0] == self.body["stage"]
                        and self.body["grant_ref"] == self.attempt.record_original[1].record_id
                        and self.body["fence_ref"] == self.attempt.record_original[0].fence_ref
                        and self.body["supervisor_instance_ref"] == self.attempt.supervisor.instance_ref,
                        "LP03_PROCESS_APPEND_ORIGINAL_MEMBERS_CHANGED")
        EvidenceProcessSupervisorV1._require_process_observation_v1(self.attempt.supervisor, self.native, self.snapshot)
        roster, snapshots = self.attempt.observation_appends, self.native._observation_originals
        _native_require(type(roster) is tuple and type(snapshots) is tuple and 1 <= len(roster) == len(snapshots) <= 3
                        and tuple(item[0] for item in snapshots) == ("SUSPENDED", "RUNNING", "TERMINAL")[:len(snapshots)]
                        and all(type(entry) is _EvidenceAttemptObservationAppendV1 and entry.attempt is self.attempt
                            and entry.native is self.native and entry.snapshot is snapshot and entry.stage == snapshot[0]
                            for entry, snapshot in zip(roster, snapshots)), "LP03_PROCESS_APPEND_ORIGINAL_LINEAGE_CHANGED")
        _native_require(self.body_json == self.snapshot[1] and (not canonical or deterministic_json(self.body) == self.body_json)
                        and self.body["predecessor_state_ref"] == self.predecessor.record_id,
                        "LP03_PROCESS_APPEND_ORIGINAL_BODY_CHANGED")
        if self.original is not None:
            _native_require(self.record is self.original[0] and self.rows is self.original[1] and self.refs is self.original[2]
                            and (not canonical or self.record is None or deterministic_json(self.record) == self.original[3]),
                            "LP03_PROCESS_APPEND_ORIGINAL_ROWS_CHANGED")

    def _build_state_v1(self):
        from dataclasses import replace
        from .lifecycle import EvidenceAttemptStateV1, EVIDENCE_ATTEMPT_STATE_MACHINE_V1, evidence_attempt_primary_reason_v1
        from .models import EvidenceAbsenceV1
        attempt, body = self.attempt, self.body
        _EvidenceAttemptObservationAppendV1._assert_original_v1(self)
        _native_require(attempt.current_state is self.predecessor, "LP03_PROCESS_STATE_PREDECESSOR_CHANGED")
        if self.stage == "SUSPENDED":
            _native_require(self.predecessor.state is EvidenceAttemptStateV1.ADMITTED, "LP03_PROCESS_SUSPEND_STATE")
            return None
        if self.stage == "TERMINAL":
            # Physical terminality precedes the atomic lane result/accounting
            # batch. Preserve that native fact without claiming collection.
            _native_require(self.predecessor.state is EvidenceAttemptStateV1.RUNNING and body["exchange_complete"],
                            "LP03_PROCESS_TERMINAL_STATE")
            return None
        state, reasons = EvidenceAttemptStateV1.RUNNING, ()
        _native_require(not body["reason_codes"] and (self.stage != "TERMINAL" or body["exchange_complete"])
                        and not any(body[name] for name in ("controller_error_count", "drain_error_count", "cleanup_error_count", "diagnostic_bytes")),
                        "LP03_PROCESS_POSITIVE_STATE_UNPROVEN")
        # This first effect path admits only the original positive exchange.
        # Nonpositive observations retain custody until their audit path exists.
        _native_require((self.predecessor.state.value, state.value) in EVIDENCE_ATTEMPT_STATE_MACHINE_V1.allowed_transitions,
                        "LP03_PROCESS_STATE_TRANSITION")
        observed = _EvidenceRegistrationOperationV1._check_current_v1(attempt.registration)
        state_id = attempt.grant_record.record_id + "::STATE:" + str(len(attempt.observation_appends) - 1)
        self.record = replace(self.predecessor, record_id=state_id, created_wall_ns=observed[0], causation_ref=self.predecessor.record_id,
            prior_state_ref=self.predecessor.record_id, state=state, all_reason_codes=reasons,
            primary_reason=(evidence_attempt_primary_reason_v1(reasons) if reasons else EvidenceAbsenceV1("NO_STOP_REASON")),
            event_ordinal=body["events"],
            process_observation_ref_or_absence=body["observation_ref"],
            consumed_budget=_EvidenceAttemptOperationV1._consumption_v1(attempt), currentness_observation_ref=state_id)
        return self.record


class _EvidenceLaneOperationV1:
    """Original finite lane batch; pending data never grants consumption authority."""

    __slots__ = ("platform", "attempt", "issuer", "native", "exchange", "original", "phase", "unit_of_work_id",
                 "publication_ref", "header", "raw", "raw_original", "records", "accounts", "record_original",
                 "heldout_score_records", "recorded_dr_records", "analytic_conversion_work", "analytic_conversion_record",
                 "rows", "row_original", "commit_observation", "readback_observation", "unit", "unit_original",
                 "transaction_observation", "transaction_original", "data_observations_original",
                 "publication_phase", "publication", "publication_original", "publication_commit_observation",
                 "publication_commit_original", "publication_readback_observation", "publication_readback_original",
                 "control_dependencies", "control_original", "dependency_original", "required_record_refs", "availability",
                 "finalization_phase", "final_state", "final_state_original", "lane_registration", "final_rows", "final_original",
                 "final_commit_observation", "final_commit_original", "final_readback_observation", "final_readback_original",
                 "published_edge_latency")

    def __init__(self, platform, attempt):
        from uuid import uuid4
        from .evidence_execution import EvidencePlatformV1
        from .models import EvidencePublicationRefV1
        EvidencePlatformV1._assert_original_v1(platform)
        _native_require(type(attempt) is _EvidenceAttemptOperationV1 and attempt.supervisor is platform._supervisor
                        and attempt.request.lane is platform._lane and attempt.lane_operation is None
                        and attempt.phase == "NATIVE_TERMINAL_PENDING_LANE_FINALIZATION",
                        "LP03_LANE_ORIGINAL_TERMINAL_REQUIRED")
        native = platform._supervisor._active
        _native_require(native is not None and native.original[1] is attempt and native._exchange_original is not None
                        and native._terminal_original is not None and len(attempt.observation_appends) == 3,
                        "LP03_LANE_ORIGINAL_NATIVE_REQUIRED")
        append = attempt.observation_appends[-1]
        _EvidenceAttemptObservationAppendV1._assert_original_v1(append)
        _native_require(append.stage == "TERMINAL" and append.phase == "COMMITTED_AND_READBACK"
                        and append.readback_observation is not None and append.native is native,
                        "LP03_LANE_TERMINAL_READBACK_REQUIRED")
        self.platform, self.attempt, self.issuer, self.native = platform, attempt, attempt.registration.issuer, native
        self.exchange = native._exchange_original
        self.unit_of_work_id = attempt.grant_record.record_id + "::DATA"
        self.publication_ref = EvidencePublicationRefV1(store_id=platform._store._evidence_store_binding_v1.binding.store_id,
                                                      publication_record_id="LP03PUB::" + uuid4().hex)
        self.original = (platform, attempt, self.issuer, native, self.exchange, native._terminal_original,
                         attempt.observation_appends, self.publication_ref, self.unit_of_work_id,
                         deterministic_json(self.exchange[1:]), attempt.current_state)
        self.phase = "RESERVED"
        self.header = self.raw = self.raw_original = self.records = self.accounts = self.record_original = None
        self.heldout_score_records = self.recorded_dr_records = None
        self.analytic_conversion_work = self.analytic_conversion_record = None
        self.rows, self.row_original = (), None
        self.commit_observation = self.readback_observation = self.unit = self.unit_original = self.transaction_observation = None
        self.transaction_original = None
        self.data_observations_original = None
        self.publication_phase = "NOT_STARTED"
        self.publication = self.publication_original = self.publication_commit_observation = None
        self.publication_commit_original = self.publication_readback_observation = self.publication_readback_original = None
        self.control_dependencies = self.control_original = self.dependency_original = self.required_record_refs = self.availability = None
        self.finalization_phase = "NOT_STARTED"
        self.final_state = self.final_state_original = self.lane_registration = self.final_original = None
        self.final_rows = ()
        self.final_commit_observation = self.final_commit_original = self.final_readback_observation = self.final_readback_original = None
        self.published_edge_latency = None
        _native_require(not any(entry[0] is native for entry in attempt.supervisor._lane_operation_originals),
                        "LP03_LANE_ORIGINAL_ASSOCIATION_ALREADY_RETAINED")
        attempt.lane_operation = self
        attempt.supervisor._lane_operation_originals = (*attempt.supervisor._lane_operation_originals,
            (native, attempt, self, self.original))

    def __copy__(self):
        raise TypeError("LP03 lane operation cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 lane operation cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 lane operation cannot be serialized")

    def _assert_original_v1(self, *, canonical=True):
        from .evidence_execution import EvidencePlatformV1
        from .input_resolver import EvidenceInvocationInputsV1
        _native_require(type(self) is _EvidenceLaneOperationV1 and self.attempt.lane_operation is self,
                        "LP03_LANE_OPERATION_NOT_ORIGINAL")
        association = tuple(entry for entry in self.attempt.supervisor._lane_operation_originals if entry[0] is self.native)
        _native_require(len(association) == 1 and association[0][1] is self.attempt and association[0][2] is self
                        and association[0][3] is self.original, "LP03_LANE_ORIGINAL_ASSOCIATION_CHANGED")
        original = self.original
        _native_require(all(left is right for left, right in zip((self.platform, self.attempt, self.issuer, self.native,
            self.exchange, self.native._terminal_original, self.attempt.observation_appends, self.publication_ref), original[:8]))
            and self.unit_of_work_id == original[8] and self.native._exchange_original is self.exchange
            and (self.attempt.current_state is original[10] or (self.finalization_phase == "COMPLETED_RESERVED"
                 and self.final_state is self.attempt.current_state)), "LP03_LANE_ORIGINAL_MEMBERS_CHANGED")
        EvidencePlatformV1._assert_original_v1(self.platform)
        if self.finalization_phase != "COMPLETED_RESERVED":
            _native_require(self.attempt.supervisor._active is self.native, "LP03_LANE_ORIGINAL_ACTIVE_SLOT_CHANGED")
        registration, preparation = self.attempt.registration, self.attempt.registration.preparation
        for values, pinned, count in (
            ((preparation.readback_refs, preparation.readback_rows, preparation.readback_bodies), preparation.roster_original, 13),
            ((registration.readback_refs, registration.readback_rows, registration.readback_bodies), registration.roster_original, 10),
            ((registration.binding_readback_refs, registration.binding_readback_rows, registration.binding_readback_bodies),
             registration.binding_roster_original, 5)):
            _native_require(pinned is not None and all(left is right for left, right in zip(values, pinned[:3]))
                            and all(len(value) == count for value in values),
                            "LP03_PUBLICATION_ORIGINAL_CONTROL_ROSTER_CHANGED")
        if self.unit_original is not None:
            _native_require(self.unit is self.unit_original[0] and self.unit._adapter is self.unit_original[1]
                            and self.unit._retry_policy is self.unit_original[2], "LP03_LANE_ORIGINAL_UNIT_CHANGED")
        if self.transaction_original is not None:
            _native_require(self.unit is self.transaction_original[0]
                            and self.platform._store._connection is self.transaction_original[1]
                            and self.transaction_observation is self.transaction_original[2]
                            and self.transaction_original[3] == "TRANSACTION_OPEN", "LP03_LANE_ORIGINAL_BEGIN_CHANGED")
        else:
            _native_require(self.transaction_observation is None, "LP03_LANE_ORIGINAL_BEGIN_CHANGED")
        for append in self.attempt.observation_appends:
            _EvidenceAttemptObservationAppendV1._assert_original_v1(append, canonical=canonical)
        EvidenceInvocationInputsV1._require_original_v1(self.exchange[0], self.attempt, canonical=canonical)
        if canonical:
            _native_require(deterministic_json(self.exchange[1:]) == original[9], "LP03_LANE_ORIGINAL_EXCHANGE_CHANGED")
        if self.record_original is not None:
            pinned = self.record_original
            _native_require(all(left is right for left, right in zip(
                (self.header, self.raw, self.raw_original, self.records, self.accounts, self.heldout_score_records,
                    self.recorded_dr_records, self.analytic_conversion_work, self.analytic_conversion_record), pinned[:9]))
                and (not canonical or deterministic_json((self.header, self.raw, self.records, dict(self.accounts),
                    self.heldout_score_records, self.recorded_dr_records, self.analytic_conversion_record)) == pinned[9]),
                "LP03_LANE_ORIGINAL_RECORDS_CHANGED")
        if self.row_original is not None:
            _native_require(self.rows is self.row_original[0] and (not canonical or deterministic_json(self.rows) == self.row_original[1]),
                            "LP03_LANE_ORIGINAL_ROWS_CHANGED")
        if self.data_observations_original is not None:
            pinned = self.data_observations_original
            _native_require(self.commit_observation is pinned[0] and self.readback_observation is pinned[1]
                            and self.unit is pinned[2] and self.row_original is pinned[3],
                            "LP03_LANE_ORIGINAL_DATA_OBSERVATIONS_CHANGED")
        else:
            _native_require(self.commit_observation is None and self.readback_observation is None,
                            "LP03_LANE_UNPINNED_DATA_OBSERVATION")
        if self.publication_original is not None:
            _native_require(self.publication is self.publication_original[0]
                            and (not canonical or deterministic_json(self.publication) == self.publication_original[1]),
                            "LP03_PUBLICATION_ORIGINAL_CHANGED")
        else:
            _native_require(self.publication is None, "LP03_PUBLICATION_UNPINNED")
        for sample, pinned in ((self.publication_commit_observation, self.publication_commit_original),
                               (self.publication_readback_observation, self.publication_readback_original)):
            _native_require((sample is None and pinned is None) or (pinned is not None and sample is pinned[0]
                and self.publication_original is pinned[1] and self.row_original is pinned[2]),
                "LP03_PUBLICATION_ORIGINAL_OBSERVATION_CHANGED")
        if self.dependency_original is not None:
            pinned = self.dependency_original
            _native_require(self.control_dependencies is pinned[0] and self.required_record_refs is pinned[1]
                            and (not canonical or deterministic_json((self.control_dependencies, self.required_record_refs)) == pinned[2]),
                            "LP03_PUBLICATION_ORIGINAL_DEPENDENCIES_CHANGED")
            registration, preparation = self.attempt.registration, self.attempt.registration.preparation
            current = (preparation.readback_refs, preparation.readback_rows, preparation.seal_audit_original,
                       registration.readback_refs, registration.readback_rows, registration.binding_readback_refs,
                       registration.binding_readback_rows, self.attempt.readback_refs, self.attempt.readback_rows)
            _native_require(all(left is right for left, right in zip(current, self.control_original)),
                            "LP03_PUBLICATION_CONTROL_DEPENDENCIES_CHANGED")
        if self.final_state_original is not None:
            _native_require(self.final_state is self.final_state_original[0]
                            and (not canonical or deterministic_json(self.final_state) == self.final_state_original[1]),
                            "LP03_FINAL_STATE_ORIGINAL_CHANGED")
        if self.final_original is not None:
            _native_require(self.final_rows is self.final_original[0] and self.lane_registration is self.final_original[1]
                            and (not canonical or deterministic_json((self.final_rows, self.lane_registration)) == self.final_original[2]),
                            "LP03_FINAL_ROWS_ORIGINAL_CHANGED")
        for observed, pinned in ((self.final_commit_observation, self.final_commit_original),
                                 (self.final_readback_observation, self.final_readback_original)):
            _native_require((observed is None and pinned is None) or (pinned is not None and observed is pinned[0]
                and self.final_original is pinned[1]), "LP03_FINAL_OBSERVATION_ORIGINAL_CHANGED")

    def _room_v1(self, **increments):
        _EvidenceRegistrationOperationV1._room_v1(self.attempt.registration, **increments)

    def _charge_v1(self, **increments):
        _EvidenceRegistrationOperationV1._charge_v1(self.attempt.registration, **increments)

    def _check_current_v1(self):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceHostBindingV1
        _EvidenceLaneOperationV1._assert_original_v1(self)
        registration = self.attempt.registration
        _native_require(registration.active_lane_operation is self and registration.active_attempt is self.attempt
                        and self.issuer.operation is registration and self.issuer.lock._is_owned()
                        and self.phase in ("RESERVED", "BUILDING_RECORDS", "PREPARED", "TRANSACTION_OPEN",
                                           "COMMIT_ATTEMPTED", "COMMITTED_PENDING_READBACK", "COMMITTED_AND_READBACK"),
                        "LP03_LANE_OPERATION_SCOPE_OR_PHASE")
        EvidenceHostBindingV1._assert_local_binding_v1(self.platform._host)
        _EvidenceBoundStoreV1._require_original_objects_v1(self.platform._original[4], self.platform._host, self.platform._store)
        binding = self.platform._original[4].binding
        _native_require(self.attempt.payload.allowed_write_store_ids == (binding.store_id,)
                        and self.attempt.payload.producer_principal == binding.allowed_writer_principal
                        == self.platform._host.public_configuration.service_principal,
                        "LP03_LANE_ORIGINAL_WRITE_SCOPE")
        observed = _EvidenceRegistrationOperationV1._check_current_v1(registration)
        _EvidenceLaneOperationV1._assert_original_v1(self, canonical=False)
        _native_require(registration.active_lane_operation is self and self.issuer.operation is registration,
                        "LP03_LANE_FINAL_OPERATION_CHANGED")
        return observed

    def _require_publication_purpose_v1(self, purpose, current_grant, clock):
        from ...agents.pr169_agent_orch1_resolvers import EvidenceAttemptGrantV1
        _native_require(type(current_grant) is EvidenceAttemptGrantV1 and current_grant is self.attempt.handle
                        and current_grant._attempt is self.attempt and current_grant._owner is self.issuer
                        and clock is self.issuer.clock and purpose == "EVIDENCE_LANE_REGISTRATION_V1",
                        "LP03_PUBLICATION_ORIGINAL_CONSUMER_SCOPE")
        config = self.issuer.host.public_configuration
        envelope = self.attempt.registration.envelope_entry[3]
        _native_require(config.service_owner == "AGENT_ORCH1" and config.service_principal == envelope.issuer_principal
                        and purpose in self.platform._original[4].binding.allowed_reader_purposes
                        and purpose in self.issuer.control_store._evidence_store_binding_v1.binding.allowed_reader_purposes,
                        "LP03_PUBLICATION_CONSUMER_PURPOSE_DENIED")
        required = set(self.attempt.payload.original_source_grant_refs)
        policies = tuple(policy for _custody, rows in self.attempt.registration.policies
                         for policy in rows if policy.rights_ref in required)
        _native_require({policy.rights_ref for policy in policies} == required, "LP03_PUBLICATION_SOURCE_PURPOSE_DENIED")
        if not all(purpose in policy.source_purposes and config.service_principal in policy.consumer_principals
                   for policy in policies):
            raise ContractValidationError(ReasonCode.EVIDENCE_SOURCE_PURPOSE_DENIED, "LP03_PUBLICATION_SOURCE_PURPOSE_DENIED")

    def _storage_observation_v1(self, observation):
        from .latency_policy import _EvidenceLocalClockV1, _evidence_storage_observation_v1
        clock = self.issuer.clock
        return _evidence_storage_observation_v1(dict(wall_ns=observation[0], monotonic_ns=observation[1],
            process_cpu_ns=observation[2], clock_domain_id=clock.clock_domain_id,
            process_identity_ref=clock.process_identity_ref, boot_identity_ref=clock.boot_identity_ref,
            clock_declarations=_EvidenceLocalClockV1.declaration_v1(clock)))

    def _prepare_publication_v1(self):
        from .models import EvidencePublicationRecordV1, EvidenceRecordRefV1, EvidenceAbsenceV1
        from .receipts import _lp03_spine_for_record_v1
        if self.phase != "COMMITTED_AND_READBACK" or self.readback_observation is None:
            raise PersistenceContractError(ReasonCode.EVIDENCE_PUBLICATION_UNPROVEN,
                "LP03_PUBLICATION_DATA_READBACK_REQUIRED")
        _native_require(self.publication_phase == "NOT_STARTED" and self.publication is None,
                        "LP03_PUBLICATION_DATA_READBACK_REQUIRED")
        _EvidenceLaneOperationV1._require_publication_purpose_v1(self, "EVIDENCE_LANE_REGISTRATION_V1", self.attempt.handle, self.issuer.clock)
        _EvidenceLaneOperationV1._assert_original_v1(self)
        registration, preparation = self.attempt.registration, self.attempt.registration.preparation
        audit, audit_row, _audit_commit = preparation.seal_audit_original
        groups = ((preparation.readback_refs, preparation.readback_rows),
                  ((("receipt_records", audit.record_id),), (audit_row,)),
                  (registration.readback_refs, registration.readback_rows),
                  (registration.binding_readback_refs, registration.binding_readback_rows),
                  (self.attempt.readback_refs, self.attempt.readback_rows),
                  *((entry.refs, entry.rows) for entry in self.attempt.observation_appends))
        _native_require(all(len(refs) == len(rows) for refs, rows in groups), "LP03_PUBLICATION_CONTROL_ROSTER")
        for refs, rows in groups:
            _native_require(all(row[0] == ref for (_table, ref), row in zip(refs, rows)), "LP03_PUBLICATION_CONTROL_JOIN")
        self.control_dependencies = tuple((table, row) for refs, rows in groups for (table, _ref), row in zip(refs, rows))
        self.control_original = (preparation.readback_refs, preparation.readback_rows, preparation.seal_audit_original,
            registration.readback_refs, registration.readback_rows, registration.binding_readback_refs,
            registration.binding_readback_rows, self.attempt.readback_refs, self.attempt.readback_rows)
        # Bootstrap CONTROL facts and original input custody are dependencies,
        # not producer data needing recursively self-created publications.
        control_store = self.issuer.control_store._evidence_store_binding_v1.binding.store_id
        self.required_record_refs = tuple(dict.fromkeys((
            *(EvidenceRecordRefV1(self.publication_ref.store_id, row[0]) for _table, row, _record in self.rows),
            *(EvidenceRecordRefV1(control_store, row[0]) for _table, row in self.control_dependencies),
            *(ref for source_slice in self.exchange[0]._source_slices for ref in source_slice.original_record_refs))))
        self.dependency_original = (self.control_dependencies, self.required_record_refs,
            deterministic_json((self.control_dependencies, self.required_record_refs)))
        observed = _EvidenceLaneOperationV1._check_current_v1(self)
        common = dict(self.header)
        common.update(created_wall_ns=observed[0], causation_ref=self.records.result_record_ref)
        record = EvidencePublicationRecordV1(**common, record_id=self.publication_ref.publication_record_id,
            lane=self.attempt.request.lane, fence_ref=self.attempt.payload.fence_ref,
            underlying_store_id=self.publication_ref.store_id, underlying_record_refs=tuple(row[0] for _table, row, _record in self.rows),
            underlying_transaction_ref=self.unit_of_work_id, original_grant_ref=self.attempt.grant_record.record_id,
            publication_purpose="EVIDENCE_LANE_REGISTRATION_V1",
            successful_commit_return_observation=_EvidenceLaneOperationV1._storage_observation_v1(self, self.commit_observation),
            independent_readback_observation=_EvidenceLaneOperationV1._storage_observation_v1(self, self.readback_observation),
            publication_observation=_EvidenceLaneOperationV1._storage_observation_v1(self, observed),
            original_witness_refs=EvidenceAbsenceV1("NO_HISTORICAL_PUBLICATION_WITNESS"),
            storage_qualification=self.platform._original[4].binding.qualification_ref,
            ambiguity_state="ORIGINAL_DATA_COMMIT_AND_READBACK_OBSERVED")
        spine = _lp03_spine_for_record_v1(record, sequence=1, trace_ref=preparation.trace_ref)
        row = (record.record_id, spine.effective_at.isoformat(), spine.recorded_at.isoformat(), spine.aggregate_id, deterministic_json(spine))
        self.publication = (record, spine, row)
        self.publication_original = (self.publication, deterministic_json(self.publication))
        self.publication_phase = "PREPARED"
        _EvidenceLaneOperationV1._check_current_v1(self)

    def _prepare_finalization_v1(self):
        from dataclasses import replace
        from datetime import timedelta
        from .lifecycle import EvidenceAttemptStateV1, EVIDENCE_ATTEMPT_STATE_MACHINE_V1
        from .evidence import register_measured_lane_v1
        from .receipts import _lp03_spine_for_record_v1
        _native_require(self.finalization_phase == "NOT_STARTED" and self.publication_phase == "COMMITTED_AND_READBACK"
                        and self.attempt.current_state is self.original[10] and self.final_state is None,
                        "LP03_FINALIZATION_ORIGINAL_PENDING_LANE")
        observed = EvidenceAvailabilityHandleV1._require_current_v1(self.availability, operation=self,
            purpose="EVIDENCE_LANE_REGISTRATION_V1", current_grant=self.attempt.handle, clock=self.issuer.clock)
        terminal = self.native._terminal_original
        _native_require(self.native.phase == "TERMINAL_RETAINED_AND_CLOSED" and terminal is self.original[5]
                        and terminal[0]["exit_code"] == 0 and terminal[0]["active_processes"] == 0
                        and terminal[1:3] == (True, True) and not any((terminal[3], terminal[5], terminal[7], terminal[8]))
                        and not self.native.cleanup_errors and not self.attempt.supervisor._unresolved,
                        "LP03_FINALIZATION_NATIVE_TERMINAL_REQUIRED")
        _native_require((self.attempt.current_state.state.value, "COLLECTION_COMPLETE")
                        in EVIDENCE_ATTEMPT_STATE_MACHINE_V1.allowed_transitions, "LP03_FINALIZATION_TRANSITION")
        self.finalization_phase = "BUILDING"
        record_id = self.attempt.grant_record.record_id + "::STATE:2"
        self.final_state = replace(self.attempt.current_state, record_id=record_id, created_wall_ns=observed[0],
            causation_ref=self.attempt.current_state.record_id, prior_state_ref=self.attempt.current_state.record_id,
            state=EvidenceAttemptStateV1.COLLECTION_COMPLETE, all_reason_codes=("COLLECTION_COMPLETE",),
            primary_reason="COLLECTION_COMPLETE", event_ordinal=1,
            process_observation_ref_or_absence=self.attempt.observation_appends[-1].body["observation_ref"],
            consumed_budget=_EvidenceAttemptOperationV1._consumption_v1(self.attempt), currentness_observation_ref=record_id)
        self.final_state_original = (self.final_state, deterministic_json(self.final_state))
        self.lane_registration = register_measured_lane_v1(operation=self, terminal_record=self.final_state)
        spines = tuple(_lp03_spine_for_record_v1(record, sequence=sequence, trace_ref=self.attempt.registration.preparation.trace_ref)
                       for sequence, record in enumerate((self.final_state, self.lane_registration), 1))
        observed = _EvidenceLaneOperationV1._check_current_v1(self)
        created = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=observed[0] // 1000)
        claim_id = self.attempt.grant_record.record_id + "::FINALIZATION"
        body = deterministic_json(dict(operation="LP03_ORIGINAL_LANE_FINALIZATION_V1",
            original_grant_ref=self.attempt.grant_record.record_id,
            original_reservation_ref=self.attempt.grant_record.record_id + "::RESERVATION",
            terminal_state_ref=self.final_state.record_id, lane_registration_ref=self.lane_registration.record_id,
            publication_ref=self.publication_ref, publication_readback_observation=self.publication_readback_observation,
            available_at=self.availability.available_at, exact_dependency_refs=self.required_record_refs,
            consumed_prefix=_EvidenceAttemptOperationV1._consumption_v1(self.attempt),
            cumulative_consumed_prefix=dict(self.attempt.registration.consumed),
            retained_full_original_reservation=self.attempt.limits, reservation_state="UNUSED_CAPACITY_RETAINED",
            tail_accounting_state="OBSERVED_PREFIX_WITH_FULL_ORIGINAL_RESERVATION", native_observation=observed))
        claim = IdempotencyClaimReceiptV1(claim_id, "LP03-LANE-FINALIZATION::" + self.attempt.grant_record.record_id,
            "LP03_LANE_FINALIZATION", body, IdempotencyClaimStateV1.ACQUIRED, None, created, None, None)
        result = dict(binding_id=claim_id + "::RESULT", claim_ref=claim_id,
                      result_record_ref=self.lane_registration.record_id, created_at=created)
        self.final_rows = (
            *(("receipt_records", (spine.record_id, spine.effective_at.isoformat(), spine.recorded_at.isoformat(),
                 spine.aggregate_id, deterministic_json(spine)), spine) for spine in spines),
            ("idempotency_claims", (claim_id, None, claim.idempotency_key, body, None, created.isoformat(), deterministic_json(claim)), claim),
            ("idempotency_claims", (result["binding_id"], claim_id, None, None, self.lane_registration.record_id,
                 created.isoformat(), deterministic_json(result)), result))
        self.final_original = (self.final_rows, self.lane_registration, deterministic_json((self.final_rows, self.lane_registration)))
        # This is capacity preflight, not a fabricated observation of the tail.
        size = sum(len(row[-1].encode("utf-8")) for _table, row, _record in self.final_rows)
        _EvidenceLaneOperationV1._room_v1(self, control_writes=7, control_bytes=size,
            owner_queries=16, record_reads=5, query_result_records=5, read_bytes=size + 1024)
        _EvidenceRegistrationOperationV1._room_v1(self.attempt.registration, retained_attempt=self.attempt,
            control_writes=7, control_bytes=size, owner_queries=16, record_reads=5, query_result_records=5, read_bytes=size + 1024)
        self.finalization_phase = "PREPARED"
        _EvidenceLaneOperationV1._check_current_v1(self)

    def _prepare_recorded_dr_uncertainty_v1(self):
        """Join the native estimator continuation to its original lane batch."""
        from .evidence_execution import _evidence_decode_recorded_dr_worker_artifact_v1
        from .models import (
            EvidenceAbsenceV1, EvidenceRecordedDrGroupMeasurementRecordV1,
            EvidenceRecordedDrUncertaintyRecordV1, _evidence_dr_original_source_data_v1,
        )

        attempt = self.attempt
        _, contract, result, _, complete, event = self.exchange
        _native_require(contract.math_id == "MATH-22" and complete["computations"] == 2,
            "LP03_DR_LANE_ORIGINAL_CONTINUATION_COUNT")
        raw_ref = self.raw.record_id
        parts, native, policy, _, original_fit_after_first_label = _evidence_dr_original_source_data_v1(event["payload"], original_raw_ref=raw_ref)
        artifact, certificate = _evidence_decode_recorded_dr_worker_artifact_v1(result["dr_uncertainty_artifact_json"],
            raw_output_json=self.raw_original, attempt_ref=attempt.grant_record.record_id,
            topology_measurement=result["invocation_measurement"], maximum_bytes=attempt.payload.budgets.frame_byte_limit)
        _native_require(artifact["estimator_original_raw_ref"] == raw_ref
            and deterministic_json(certificate["original_input"]) == deterministic_json(native)
            and deterministic_json(certificate["original_policy"]) == deterministic_json(policy)
            and (not original_fit_after_first_label or "OUTCOME_LEAKING_NUISANCE_FIT" in certificate["reasons"]),
            "LP03_DR_LANE_ORIGINAL_ESTIMATOR_AND_SOURCE")
        refs = tuple(part.original_record_refs[0] for part in parts)
        completed = certificate["disposition"] == "CONDITIONAL_DATA_CALCULATION"
        absence = EvidenceAbsenceV1("UNCERTAINTY_UNAVAILABLE")
        weighting = "EQUAL_WEIGHT_COMPLETE_EQUAL_SIZE_ORDERED_GROUPS"
        base = self.unit_of_work_id
        group = None
        if completed:
            group = EvidenceRecordedDrGroupMeasurementRecordV1(**dict(self.header,causation_ref=raw_ref,
                source_lineage_refs=(raw_ref,*(ref.record_id for ref in refs))),record_id=base+"::DR_GROUPS",
                lane=attempt.request.lane, attempt_ref=attempt.grant_record.record_id, original_estimator_ref=raw_ref,
                ordered_input_row_ids=policy["row_ids"],group_members=tuple(row["row_ids"] for row in policy["groups"]),
                group_means=tuple(certificate["group_means"]), original_group_weight=policy["group_weights"][0],
                weighting_rule=weighting,original_raw_json=self.raw_original,reward_unit=policy["unit"],reward_basis=policy["basis"])
        group_ref = group.record_id if group is not None else absence
        interval = certificate["interval"]
        uncertainty = EvidenceRecordedDrUncertaintyRecordV1(**dict(self.header,causation_ref=raw_ref,
            source_lineage_refs=(raw_ref,*(ref.record_id for ref in refs),*((group_ref,) if completed else ()))),
            record_id=base+"::DR_UNCERTAINTY",lane=attempt.request.lane,attempt_ref=attempt.grant_record.record_id,
            original_estimator_ref=raw_ref,original_logged_source_ref=refs[0],original_policy_source_ref=refs[1],
            group_measurement_ref=group_ref,target="MEAN_CONDITIONAL_RECORDED_DR_SCORE",weighting_rule=weighting,
            method_ref="CONDITIONAL_GROUP_MEAN_OUTWARD_64_128_V1",
            interval_exact_rationals={key:interval[key] for key in ("lower","upper")} if completed else absence,
            error_budget_ref=policy["group_bound_proof_ref"] if completed else absence,assumptions_refs=refs[2:],
            numeric_certificate_json=artifact["certificate_json"],native_measurement=artifact["invocation_measurement"],
            availability_disposition="ORIGINAL_CONDITIONAL_RECORDED_SCORE_INTERVAL" if completed else "UNCERTAINTY_UNAVAILABLE",
            unavailable_reasons=tuple(certificate["reasons"]))
        return (group,uncertainty) if completed else (uncertainty,)

    def _prepare_heldout_score_records_v1(self, *, terminal_ref, projected):
        """Retain every native raw invocation and its exact original scoring sources."""
        from fractions import Fraction
        import struct
        from .evidence_execution import _evidence_decode_heldout_worker_artifact_v1, _worker_invocation_contract_v1
        from .models import (
            ComputationExecutionReceiptV1, EvidenceHeldOutCpcvPathScoreRecordV1,
            EvidenceHeldOutFoldScoreRecordV1, _evidence_heldout_source_data_v1,
        )
        from .specification import decode_evidence_raw_output_v1

        attempt = self.attempt
        packet, contract, result, _, complete, event = self.exchange
        profile = attempt.registration.protocol.numeric_profile
        scorer = _worker_invocation_contract_v1(result["scorer_invocation_contract"])
        math_id = contract.math_id
        parts, _, _ = _evidence_heldout_source_data_v1(event["payload"])
        trace, label = (part.original_record_refs[0] for part in parts[-2:])
        topology_wire = self.raw_original.encode("utf-8", "strict")
        maximum_bytes = attempt.payload.budgets.frame_byte_limit
        artifact = _evidence_decode_heldout_worker_artifact_v1(
            result["held_out_score_artifact_json"].encode("utf-8", "strict"),
            topology_math_id=math_id, topology_raw_json=topology_wire, scorer_contract=scorer,
            maximum_bytes=maximum_bytes, maximum_nodes=4096)
        _native_require(scorer.math_id == profile["scorer_math_id"]
            and len(artifact["folds"]) + 1 == complete["computations"],
            "LP03_HELD_OUT_LANE_ORIGINAL_SCORER_AND_COUNT")
        topology = decode_evidence_raw_output_v1(math_id, topology_wire,
            maximum_bytes=maximum_bytes, maximum_nodes=4096)
        unit = profile["output_unit"]
        basis = "PER_SAMPLE_SQUARED_PROBABILITY" if scorer.math_id == "MATH-08" else "per_sample_natural_log_loss"
        raw_scores, fold_scores, paths = [], [], []
        values_by_fold = []
        for row in artifact["folds"]:
            ordinal = row["ordinal"]
            base = f"{self.unit_of_work_id}::FOLD:{ordinal}"
            trace_rows = row["sample_receipts"]
            measured = row["invocation_measurement"]
            sample_lineage = tuple(value for item in trace_rows
                for value in (item["prediction_receipt_ref"], item["label_receipt_ref"]))
            training_ref = row["training_receipt_ref"]
            original = ComputationExecutionReceiptV1(base+"::RAW_VALUE", scorer.math_id, scorer.raw_implementation_id,
                scorer.raw_contract_version, row["scorer_raw_json"])
            raw = DurableComputationExecutionReceiptRecordV1(base+"::RAW", original,
                packet._resolution.context_id, self.raw.input_snapshot_ref,
                (trace.record_id, label.record_id, training_ref, *sample_lineage),
                (attempt.grant_record.record_id, terminal_ref, self.raw.record_id),
                projected(measured["started"][0]), projected(measured["completed"][0]), measured["duration_ns"],
                unit, basis, "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT", False, (), None,
                self.raw.consumer_ref, self.raw.mode_ref)
            header = dict(self.header, causation_ref=raw.record_id,
                source_lineage_refs=(self.raw.record_id, raw.record_id, trace.record_id, label.record_id))
            fold = EvidenceHeldOutFoldScoreRecordV1(**header, record_id=base+"::SCORE", lane=attempt.request.lane,
                attempt_ref=attempt.grant_record.record_id, topology_math_id=math_id, topology_raw_ref=self.raw.record_id,
                fold_or_split_ordinal=ordinal, original_trace_source_ref=trace, original_outcome_source_ref=label,
                scorer_math_id=scorer.math_id, scorer_implementation_id=scorer.raw_implementation_id,
                scorer_raw_schema_ref=scorer.raw_output_schema_ref, scorer_raw_receipt_ref=raw.record_id,
                scorer_output_unit=unit, scorer_measurement_basis=basis, training_membership_receipt_ref=training_ref,
                evaluation_horizon_ref=profile["evaluation_horizon_ref"], ordered_sample_receipt_rows=trace_rows,
                original_scorer_raw_json=row["scorer_raw_json"], scorer_invocation_measurement=measured)
            raw_scores.append(raw)
            fold_scores.append(fold)
            decoded = decode_evidence_raw_output_v1(scorer.math_id, row["scorer_raw_json"].encode("utf-8", "strict"),
                maximum_bytes=maximum_bytes, maximum_nodes=4096)
            values_by_fold.append(tuple((item["sample_id"], value)
                for item, value in zip(trace_rows, decoded["per_observation"], strict=True)))

        if math_id == "MATH-21":
            _native_require(profile["path_aggregation_or_absence"] == "MEAN_COMPLETE_PATH_SAMPLE_SCORES"
                and topology["aggregation_rule"] == "ALL_PATHS_NO_CHERRY_PICKING", "LP03_CPCV_LANE_AGGREGATION")
            all_samples = {name for rows in values_by_fold for name, _ in rows}
            used_splits = set()
            for path in topology["paths"]:
                ids = path["split_ids"]
                _native_require(used_splits.isdisjoint(ids), "LP03_CPCV_LANE_SPLIT_REUSE")
                used_splits.update(ids)
                samples = tuple(pair for split_id in ids for pair in values_by_fold[split_id])
                names = tuple(name for name, _ in samples)
                _native_require(len(samples) == len(all_samples) and set(names) == all_samples,
                    "LP03_CPCV_LANE_COMPLETE_SAMPLE_COVERAGE")
                mean = sum((Fraction(value) for _, value in samples), Fraction()) / len(samples)
                path_refs = tuple(fold_scores[index].record_id for index in ids)
                paths.append(EvidenceHeldOutCpcvPathScoreRecordV1(**dict(self.header,
                    causation_ref=self.raw.record_id, source_lineage_refs=(self.raw.record_id, *path_refs)),
                    record_id=f"{self.unit_of_work_id}::PATH:{path['path_id']}::SCORE", lane=attempt.request.lane,
                    attempt_ref=attempt.grant_record.record_id, topology_raw_ref=self.raw.record_id,
                    path_ordinal=path["path_id"], ordered_fold_score_refs=path_refs, ordered_sample_ids=names,
                    ordered_original_score_bits=tuple(struct.pack(">d", value).hex() for _, value in samples),
                    exact_average=dict(numerator=str(mean.numerator), denominator=str(mean.denominator)),
                    aggregation_method=profile["path_aggregation_or_absence"]))
            _native_require(used_splits == set(range(len(values_by_fold))), "LP03_CPCV_LANE_COMPLETE_SPLIT_COVERAGE")
        return tuple(raw_scores), tuple(fold_scores), tuple(paths)

    def _prepare_analytic_conversion_v1(self):
        """Measure the original RAW-to-analytic conversion inside its lane authority."""
        from .evidence import EVIDENCE_PROJECTION_CONTRACTS_V1
        from .latency_policy import _EvidenceLocalClockV1
        from .models import (EvidenceAbsenceV1, EvidenceAnalyticBinary64ConversionRecordV1,
            _evidence_analytic_conversion_outcome_v1, _evidence_analytic_private_sources_v1)
        from .parameter_policy import _EvidenceNumericalWorkV1
        from .serialization import _native_strict_json
        from .specification import decode_evidence_raw_output_v1

        attempt = self.attempt
        registration = attempt.registration
        packet, invocation, result, _, complete, event = self.exchange
        math_id = invocation.math_id
        _native_require(math_id in ("MATH-29", "MATH-30", "MATH-31", "MATH-37")
            and event["kind"] == "SYNTHETIC_PRIVATE_ANALYTIC_INPUT"
            and complete == dict(events=1, computations=1, segments=1)
            and self.raw_original == self.raw.existing_receipt.output_json == result["raw_output_json"],
            "LP03_ANALYTIC_CONVERSION_ORIGINAL_LANE_RAW")
        profile = registration.protocol.numeric_profile
        projection = EVIDENCE_PROJECTION_CONTRACTS_V1[math_id]
        parts, _, scope = _evidence_analytic_private_sources_v1(event["payload"], math_id=math_id)
        _native_require(tuple(part.original_record_refs[0].record_id for part in parts)
            == registration.protocol.coverage_eligibility["source_record_refs"]
            and profile["output_basis"] == scope["basis"] == projection.basis_requirement
            and profile["output_unit"] == scope["unit"], "LP03_ANALYTIC_CONVERSION_ORIGINAL_SOURCE_SCOPE")
        for part in parts:
            matches = tuple(original for original in packet._source_slices if original.original_record_refs == part.original_record_refs)
            _native_require(len(matches)==1 and deterministic_json(matches[0])==deterministic_json(part),
                "LP03_ANALYTIC_CONVERSION_ORIGINAL_WEIGHT_AND_SOURCE_READ")
        raw = self.raw_original.encode("utf-8")
        decode_evidence_raw_output_v1(math_id, raw, maximum_bytes=65536, maximum_nodes=4096)
        wire = _native_strict_json(raw, max_bytes=65536, max_nodes=4096)
        decimal_text = wire if projection.original_field == "$" else wire[projection.original_field]
        limits = profile["conversion_work_limits"]
        _native_require(self.analytic_conversion_work is None, "LP03_ANALYTIC_CONVERSION_ORIGINAL_WORK_RESERVED")
        _EvidenceLaneOperationV1._check_current_v1(self)
        started = _EvidenceLocalClockV1.observe_v1(self.issuer.clock)
        work = _EvidenceNumericalWorkV1(limits, retained_input_capacity=1)
        pending = (work, work._original, raw, limits, started)
        self.analytic_conversion_work = pending
        certificate = _evidence_analytic_conversion_outcome_v1(work, decimal_text,
            math_id=math_id, unit=scope["unit"], basis=scope["basis"])
        completed = _EvidenceLocalClockV1.observe_v1(self.issuer.clock)
        _EvidenceLaneOperationV1._check_current_v1(self)
        clock = self.issuer.clock
        measurement = dict(clock_domain_id=clock.clock_domain_id, boot_identity_ref=clock.boot_identity_ref,
            process_identity_ref=clock.process_identity_ref, clock_declarations=_EvidenceLocalClockV1.declaration_v1(clock),
            started=started, completed=completed, duration_ns=completed[1]-started[1], cpu_ns=completed[2]-started[2],
            outcome="SUCCESS" if type(certificate) is str else "FAILED")
        weights_ref = parts[0].original_record_refs[0] if math_id == "MATH-29" else EvidenceAbsenceV1("NO_INPUT_WEIGHTS_FOR_SELECTED_FORMULA")
        record = EvidenceAnalyticBinary64ConversionRecordV1(**dict(self.header,
            record_id=self.unit_of_work_id+"::NUMERICAL_CONVERSION", causation_ref=self.raw.record_id,
            source_lineage_refs=(self.raw.record_id, *(part.original_record_refs[0].record_id for part in parts)),
            created_wall_ns=completed[0]), math_id=math_id,
            original_raw_receipt_ref=self.raw.record_id, original_decimal_text=decimal_text,
            original_input_weights_ref_or_absence=weights_ref, output_field=projection.original_field,
            output_unit=scope["unit"], measurement_basis=scope["basis"],
            certificate_json_or_absence=certificate, numerical_work_limits=limits,
            numerical_work_consumption=dict(work.consumed), native_measurement=measurement)
        _native_require(self.analytic_conversion_work is pending and work._original is pending[1],
            "LP03_ANALYTIC_CONVERSION_ORIGINAL_WORK_CHANGED")
        self.analytic_conversion_work = (*pending, record, tuple(work.consumed.items()))
        return record

    def _require_original_quantum_constructor_v1(self):
        """Join the retained measured constructor to the original invocation packet."""
        from .evidence_execution import _evidence_original_quantum_constructor_result_v1
        from .input_resolver import EvidenceInvocationInputsV1
        from .models import _LP03_ORIGINAL_QUANTUM_EXECUTION_IDS_V1

        packet, contract, result, _segment, complete, event = self.exchange
        attempt = self.attempt
        original = EvidenceInvocationInputsV1._require_original_v1(packet, attempt)
        measurement = result["invocation_measurement"]
        terminal = attempt.observation_appends[-1].body
        _native_require(contract.math_id in _LP03_ORIGINAL_QUANTUM_EXECUTION_IDS_V1
            and contract.origin_policy == "SOFTWARE_CONFORMANCE"
            and attempt.payload.component_closure == (contract.math_id,) and not attempt.payload.callback_pins
            and contract.math_id == original.math_spec_id == event["payload"]["math_id"]
            and event["kind"] == "SYNTHETIC_ORIGINAL_QUANTUM_INPUT"
            and complete == dict(events=1, computations=1, segments=1)
            and terminal["invocation_measurement_or_absence"] == measurement and measurement["outcome"] == "SUCCESS",
            "LP03_QUANTUM_ORIGINAL_MEASURED_LANE_JOIN")
        return _evidence_original_quantum_constructor_result_v1(contract.math_id, result["raw_output_json"],
            result["quantum_constructor_receipt_json"], maximum_bytes=attempt.payload.budgets.frame_byte_limit,
            input_lock_ref=attempt.payload.input_lock_ref, original_values=original.authoritative_values)[1]

    def _prepare_original_quantum_trace_spine_v1(self, receipt, *, recorded):
        """Keep the original special trace type in the same atomic lane batch."""
        from .evidence import _source_epoch_refs
        from .quantum_benchmark import QuantumTraceValidationReceiptV1
        from .receipts import ST12FEvidenceControlReceiptRecordV1, ST12FReceiptClassV1

        _native_require(type(receipt) is QuantumTraceValidationReceiptV1
            and self.exchange[1].math_id == receipt.math_spec_id and self.phase == "BUILDING_RECORDS",
            "LP03_QUANTUM_TRACE_ATOMIC_LANE_TYPE")
        attempt, lock = self.attempt, self.attempt.registration.compilation.input_lock
        pins = attempt.payload.component_and_callback_pins["quantum_original_lock"]
        epochs = _source_epoch_refs(lock)
        _native_require(receipt.input_lock_id == lock.input_lock_id == attempt.payload.input_lock_ref
            and receipt.comparison_basis.scenario_set_ref == pins["scenario_set_ref"] == lock.scenario_set_id
            and pins["source_epoch_pairs"] == tuple(sorted(lock.source_epochs.items()))
            and set(epochs) <= set(receipt.comparison_basis.version_epoch_pins),
            "LP03_QUANTUM_TRACE_ATOMIC_ORIGINAL_LOCK")
        ref = self.unit_of_work_id + "::QUANTUM_TRACE"
        payload = ST12FEvidenceControlReceiptRecordV1(
            control_receipt_id=ref, receipt_class=ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION,
            operation_id="ST12F-PRIVATE::REGISTER_CONTROL", request_id=attempt.grant_record.record_id,
            idempotency_key=attempt.request.idempotency_key, contract_type=type(receipt).__name__, contract_id=receipt.receipt_id,
            contract_version=receipt.contract_version, input_lock_id_or_explicit_absence=receipt.input_lock_id,
            parent_version_ref_or_explicit_absence="EXPLICIT_ABSENCE",
            canonical_contract_json=self.exchange[2]["quantum_constructor_receipt_json"],
            source_record_refs=(receipt.trace_id, receipt.strongest_classical_receipt_ref, receipt.no_trade_receipt_ref),
            parameter_value_refs=lock.parameter_value_refs, source_epoch_refs=epochs,
            typed_reason_codes=(), terminal_state=receipt.terminal_state, fixture_only_not_evidence=False,
        )
        _native_require(payload.reconstruct(QuantumTraceValidationReceiptV1) == receipt,
            "LP03_QUANTUM_TRACE_ATOMIC_EXACT_CONSTRUCTOR")
        preparation = attempt.registration.preparation
        return EconomicReceiptEventSpineV1(
            ref, EconomicRecordTypeV1.ST12F_EVIDENCE_CONTROL, "QTT_ST12F_EVIDENCE_CONTROL_RECEIPT_SPINE_V1",
            "ComputationEvidenceServiceV1", "QuantumBenchmarkServiceV1", self.raw.execution_context_ref,
            self.raw.completed_at, recorded, attempt.grant_record.record_id, attempt.grant_record.correlation_ref,
            preparation.trace_ref, "LP03-LANE-DATA", 4, self.unit_of_work_id, 4, "EVIDENCE_CUSTODY_NO_EFFECT", payload,
        )

    def _prepare_records_v1(self):
        from dataclasses import fields
        from datetime import timedelta
        from types import MappingProxyType
        from .models import (EvidenceRecordHeaderV1, EvidenceEventSegmentRecordV1, EvidenceAbsenceV1,
                             ComputationExecutionReceiptV1, EvidenceOriginV1)
        from .receipts import TypedEconomicAmountV1, _lp03_spine_for_record_v1
        from .accounting import JournalAccountV1, JournalPostingV1, JournalTransactionV1, EntrySideV1, NormalBalanceV1
        from .lifecycle import UNIT_OF_WORK_STATE_MACHINE_V1, TransitionDispositionV1
        from .transaction import TrancheCAtomicRecordSetV1, TrancheCUnitOfWorkV1
        from .input_lock import _require_original_input_assembly_outcome_v1
        from .evidence import project_executed_metric_v1
        _native_require(self.phase == "TRANSACTION_OPEN" and self.transaction_observation is not None
                        and self.records is None and type(self.unit) is TrancheCUnitOfWorkV1
                        and self.unit._adapter is self.platform._store and self.unit._adapter._connection.in_transaction,
                        "LP03_LANE_ALREADY_PREPARED")
        when = _EvidenceLaneOperationV1._check_current_v1(self)
        self.phase = "BUILDING_RECORDS"
        attempt, registration = self.attempt, self.attempt.registration
        preparation = registration.preparation
        _require_original_input_assembly_outcome_v1(preparation, preparation.input_assembly_outcome)
        snapshot = preparation.input_assembly_members[2]
        policy = snapshot.accounting_definition
        packet, contract, result, _segment, complete, event = self.exchange
        edge = attempt.payload.component_closure == ("MATH-01","MATH-02")
        held_out = contract.math_id in ("MATH-20", "MATH-21")
        recorded_dr = contract.math_id == "MATH-22"
        ope_point = contract.math_id in ("MATH-23", "MATH-24", "MATH-25")
        private_execution = contract.math_id in ("MATH-32", "MATH-33", "MATH-35", "MATH-36", "MATH-38", "MATH-39", "MATH-40", "MATH-41", "MATH-42", "MATH-43", "MATH-44", "MATH-45")
        analytic = contract.math_id in ("MATH-29", "MATH-30", "MATH-31", "MATH-37")
        quantum = contract.math_id in ("MATH-50", "MATH-51", "MATH-52")
        if held_out:
            from .evidence_execution import _heldout_computation_count_v1
        from .evidence_execution import _evidence_lane_completion_v1
        computation_count = (_heldout_computation_count_v1(contract.math_id, packet._resolution.authoritative_values)
            if held_out else 2 if edge or recorded_dr else 1)
        _native_require(attempt.grant_record.origin is EvidenceOriginV1.SOFTWARE_CONFORMANCE
                        and _evidence_lane_completion_v1(attempt.payload, complete, computation_count)
                        and result["invocation_measurement"]["outcome"] == "SUCCESS", "LP03_LANE_SELECTED_PROFILE")
        baseline_ref = snapshot.portfolio_and_cash_context["permanent_no_trade_baseline_ref"]
        originals = tuple(item for part in packet._source_slices for item in part.reconstructed_canonical_events
                          if item["record_ref"] == baseline_ref)
        _native_require(len(originals) == 1, "LP03_LANE_ORIGINAL_BASELINE_REQUIRED")
        baseline = originals[0]["values"]["baseline"]
        _native_require(baseline["currency"] == policy["currency"] and baseline["positions"] == ()
                        and baseline["origin"] == attempt.grant_record.origin.value, "LP03_LANE_BASELINE_CONTEXT")
        projected = lambda ns: datetime(1970, 1, 1, tzinfo=UTC) + timedelta(microseconds=ns // 1000)
        recorded, effective = projected(when[0]), projected(originals[0]["native_clocks"]["effective_time"])
        base, measurement = self.unit_of_work_id, result["invocation_measurement"]
        common = {field.name: getattr(attempt.grant_record, field.name) for field in fields(EvidenceRecordHeaderV1)
                  if field.name not in ("kind", "record_id")}
        common.update(causation_ref=attempt.grant_record.record_id, producing_owner="QKU_COMPUTATION_CONTROL_PLANE",
            producing_principal=self.platform._host.public_configuration.service_principal, created_wall_ns=when[0],
            source_lineage_refs=tuple(ref["record_id"] for ref in result["original_record_refs"]))
        self.header = MappingProxyType(common)
        terminal_ref = attempt.observation_appends[-1].body["observation_ref"]
        _native_require(attempt.observation_appends[-1].body["invocation_measurement_or_absence"] == measurement,
                        "LP03_LANE_DURABLE_INVOCATION_MEASUREMENT")
        if edge:
            from .models import EvidenceDependencyExecutionRecordV1
            from .input_resolver import EvidenceInvocationInputsV1, _require_evidence_probability_edge_result_v1
            from .implementation_registry import resolve_evidence_invocation_v1
            producer_packet = attempt.invocations[0]
            producer_resolution = EvidenceInvocationInputsV1._require_original_v1(producer_packet,attempt)
            producer_pin = attempt.payload.component_and_callback_pins["components"][0]
            producer_contract = resolve_evidence_invocation_v1(producer_pin[0],implementation_pin=producer_pin[1],
                specification_pin=producer_pin[2],resource_policy_ref=attempt.payload.protocol_ref,origin=attempt.grant_record.origin)
            artifact = _require_evidence_probability_edge_result_v1((producer_packet,packet),attempt,(producer_contract,contract),
                result,original_record_refs=result["original_record_refs"],frame_byte_limit=attempt.payload.budgets.frame_byte_limit)
            producer_measurement = artifact["measured_original_stages"][0]["measurement"]
            measurement = artifact["measured_original_stages"][2]["measurement"]
            producer_existing = ComputationExecutionReceiptV1(base + "::M01_RAW_VALUE","MATH-01",
                producer_contract.raw_implementation_id,producer_contract.raw_contract_version,artifact["producer_output_json"])
            producer_raw = DurableComputationExecutionReceiptRecordV1(base + "::M01_RAW",producer_existing,
                producer_resolution.context_id,preparation.input_assembly_members[3].record_id,producer_resolution.receipt_refs,
                (attempt.grant_record.record_id,terminal_ref),projected(producer_measurement["started"][0]),
                projected(producer_measurement["completed"][0]),producer_measurement["duration_ns"],
                "probability","PAYOUT_NORMALIZED_CONTRACT_PRICE","SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT",False,(),None,
                self.platform._host.public_configuration.service_principal,attempt.request.lane.value)
            dependency = EvidenceDependencyExecutionRecordV1(**self.header,record_id=attempt.grant_record.record_id + "::CONVERSION",
                attempt_ref=attempt.grant_record.record_id,lane=attempt.request.lane,execution_context_ref=producer_resolution.context_id,
                producer_raw_receipt_ref=producer_raw.record_id,consumer_raw_receipt_ref=base + "::RAW",
                producer_invocation_contract=result["producer_invocation_contract"],
                consumer_invocation_contract=result["invocation_contract"],chain_artifact_json=result["chain_artifact_json"],
                invocation_measurement=result["invocation_measurement"],publication_ref=self.publication_ref)
            input_lineage = (*packet._resolution.receipt_refs,producer_raw.record_id)
            dependency_refs = (attempt.grant_record.record_id,terminal_ref,producer_raw.record_id)
        else:
            input_lineage = packet._resolution.receipt_refs
            dependency_refs = (attempt.grant_record.record_id,terminal_ref)
        # Preserve the exact original adapter output carried by the worker;
        # parent storage must not manufacture replacement output bytes.
        self.raw_original = result["raw_output_json"]
        existing = ComputationExecutionReceiptV1(base + "::RAW_VALUE", contract.math_id, contract.raw_implementation_id,
                                                contract.raw_contract_version, self.raw_original)
        self.raw = DurableComputationExecutionReceiptRecordV1(base + "::RAW", existing,
            packet._resolution.context_id, preparation.input_assembly_members[3].record_id, input_lineage,
            dependency_refs, projected(measurement["started"][0]),
            projected(measurement["completed"][0]), measurement["duration_ns"],
            registration.protocol.numeric_profile["output_unit"] if recorded_dr or ope_point or analytic or private_execution or quantum else "sample identifiers and topology" if held_out else attempt.registration.protocol.numeric_profile["output_unit"] if contract.math_id in ("MATH-06", "MATH-07", "MATH-02", "MATH-01", "MATH-04", "MATH-05", "MATH-27", "MATH-28") else
                policy["utility_unit"] if contract.math_id == "MATH-26" else
                "mixed; member-specific" if contract.math_id in ("MATH-15", "MATH-16", "MATH-19") else "statistic_unit" if contract.math_id == "MATH-14" else "probability" if contract.math_id in ("MATH-10", "MATH-11", "MATH-12", "MATH-13", "MATH-17", "MATH-18") else "nats/sample" if contract.math_id == "MATH-09" else "squared probability error" if contract.math_id == "MATH-08" else policy["currency"] + "/" + policy["quantity_unit"],
            "ORIGINAL_RECORDED_DR_ESTIMATOR" if recorded_dr else registration.protocol.numeric_profile["output_basis"] if ope_point or analytic or private_execution or quantum else "ORIGINAL_PURGED_TOPOLOGY" if held_out else policy["measurement_basis" if contract.math_id in ("MATH-06", "MATH-07", "MATH-02", "MATH-01", "MATH-04", "MATH-05", "MATH-08", "MATH-09", "MATH-10", "MATH-11", "MATH-14", "MATH-15", "MATH-16", "MATH-17", "MATH-18", "MATH-19", "MATH-12", "MATH-13", "MATH-26", "MATH-27", "MATH-28") else "midpoint_basis"],
            "SYNTHETIC_MEASURED_VALUE_NO_CASH_MOVEMENT", False, (), None,
            self.platform._host.public_configuration.service_principal, attempt.request.lane.value)
        if held_out:
            self.heldout_score_records = _EvidenceLaneOperationV1._prepare_heldout_score_records_v1(
                self, terminal_ref=terminal_ref, projected=projected)
        if recorded_dr:
            self.recorded_dr_records = _EvidenceLaneOperationV1._prepare_recorded_dr_uncertainty_v1(self)
        if analytic:
            self.analytic_conversion_record = _EvidenceLaneOperationV1._prepare_analytic_conversion_v1(self)
        quantum_trace = (_EvidenceLaneOperationV1._prepare_original_quantum_trace_spine_v1(
            self, _EvidenceLaneOperationV1._require_original_quantum_constructor_v1(self), recorded=recorded)
            if contract.math_id in ("MATH-50", "MATH-51") else None)
        projection = project_executed_metric_v1(operation=self)
        event_id, journal_id = base + "::OPENING", base + "::JOURNAL"
        amount = TypedEconomicAmountV1(str(baseline["cash"]), policy["currency"], policy["ledger_unit"],
                                      policy["opening_basis"], policy["scale"], policy["rounding_policy_ref"])
        economic = EconomicEventRecordV1(event_id, "SYNTHETIC_OPENING_BALANCE", "QKU_COMPUTATION_CONTROL_PLANE",
            base, 1, effective, recorded, (baseline_ref, preparation.input_assembly_members[3].record_id), (amount,),
            "UNINITIALIZED", "SYNTHETIC_OPENING_RECORDED", "LP03_SOFTWARE_CONFORMANCE")
        accounts = tuple(JournalAccountV1(policy[name], kind, normal, amount.ledger_unit, amount.currency_or_asset,
            amount.basis, "ACTIVE") for name, kind, normal in (("cash_account_ref", "ASSET", NormalBalanceV1.DEBIT),
                                                             ("equity_account_ref", "EQUITY", NormalBalanceV1.CREDIT)))
        self.accounts = MappingProxyType({account.account_id: account for account in accounts})
        postings = tuple(JournalPostingV1(base + "::POSTING:" + str(index), journal_id, account.account_id, side,
            amount.amount_text, amount.ledger_unit, amount.currency_or_asset, amount.basis, amount.scale,
            effective, recorded, event_id) for index, (account, side) in enumerate(zip(accounts, (EntrySideV1.DEBIT, EntrySideV1.CREDIT)), 1))
        journal = JournalTransactionV1(journal_id, "SYNTHETIC_OPENING_BALANCE", (event_id,),
            tuple(posting.posting_id for posting in postings), effective, recorded, "ORIGINAL_SYNTHETIC_BASELINE",
            "LP03_SOFTWARE_CONFORMANCE")
        supplementary = (self.recorded_dr_records if recorded_dr else
            tuple(item for group in self.heldout_score_records for item in group) if held_out else
            (self.analytic_conversion_record,) if analytic else (quantum_trace,) if quantum_trace is not None else ())
        ordered_events = (event,) if attempt.payload.causal_timeline_v1() is None else _segment
        _native_require(len(ordered_events) == complete["events"], "LP03_LANE_ORIGINAL_EVENT_ROSTER")
        segment = EvidenceEventSegmentRecordV1(**self.header, record_id=base + "::SEGMENT", lane=attempt.request.lane,
            attempt_ref=attempt.grant_record.record_id, first_event_ordinal=0, last_event_ordinal=len(ordered_events) - 1,
            predecessor_segment_ref=EvidenceAbsenceV1("FIRST_EVENT_SEGMENT"), count=len(ordered_events), exact_ordered_events=ordered_events,
            gap_dispositions=(), observed_bytes=self.native._terminal_original[6],
            aggregate_refs=((self.raw.record_id,projection.record_id,event_id,journal_id,producer_raw.record_id,dependency.record_id)
                if edge else (self.raw.record_id,projection.record_id,event_id,journal_id,*(item.record_id for item in supplementary))),commit_sequence=1)
        raw_spine = EconomicReceiptEventSpineV1(self.raw.record_id, EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT,
            "1", "QKU_COMPUTATION_CONTROL_PLANE", "QKU_COMPUTATION_CONTROL_PLANE", packet._resolution.context_id,
            self.raw.completed_at, recorded, attempt.grant_record.record_id, attempt.grant_record.correlation_ref,
            preparation.trace_ref, "LP03-LANE-DATA", 1, base, 1, "LP03_SOFTWARE_CONFORMANCE", self.raw)
        spines = (raw_spine, *tuple(_lp03_spine_for_record_v1(row, sequence=index, trace_ref=preparation.trace_ref)
                                    for index, row in enumerate((projection, segment), 2)))
        if edge:
            producer_spine = EconomicReceiptEventSpineV1(producer_raw.record_id,EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT,
                "1","QKU_COMPUTATION_CONTROL_PLANE","QKU_COMPUTATION_CONTROL_PLANE",producer_resolution.context_id,
                producer_raw.completed_at,recorded,attempt.grant_record.record_id,attempt.grant_record.correlation_ref,
                preparation.trace_ref,"LP03-LANE-DATA",4,base,4,"LP03_SOFTWARE_CONFORMANCE",producer_raw)
            spines = (*spines,producer_spine,_lp03_spine_for_record_v1(dependency,sequence=5,trace_ref=preparation.trace_ref))
        if quantum_trace is not None:
            spines = (*spines, quantum_trace)
        if held_out:
            original_scores, fold_scores, path_scores = self.heldout_score_records
            score_spines = tuple(EconomicReceiptEventSpineV1(row.record_id, EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT,
                "1", "QKU_COMPUTATION_CONTROL_PLANE", "QKU_COMPUTATION_CONTROL_PLANE", packet._resolution.context_id,
                row.completed_at, recorded, attempt.grant_record.record_id, attempt.grant_record.correlation_ref,
                preparation.trace_ref, "LP03-LANE-DATA", index, base, index, "LP03_SOFTWARE_CONFORMANCE", row)
                for index, row in enumerate(original_scores, 4))
            typed_scores = tuple(_lp03_spine_for_record_v1(row, sequence=index, trace_ref=preparation.trace_ref)
                for index, row in enumerate((*fold_scores, *path_scores), 4 + len(original_scores)))
            spines = (*spines, *score_spines, *typed_scores)
        if recorded_dr:
            spines = (*spines, *tuple(_lp03_spine_for_record_v1(row, sequence=index, trace_ref=preparation.trace_ref)
                for index,row in enumerate(self.recorded_dr_records,4)))
        if analytic:
            spines = (*spines, _lp03_spine_for_record_v1(self.analytic_conversion_record, sequence=4, trace_ref=preparation.trace_ref))
        transition = StateTransitionReceiptV1(base + "::STATE", base,
            UNIT_OF_WORK_STATE_MACHINE_V1.registry_id, "NEW", "ORIGINAL_LANE_UNIT_OF_WORK_ENTERED", "ACTIVE",
            TransitionDispositionV1.ACCEPTED, segment.record_id, 0, 1,
            projected(self.transaction_observation[0]), projected(self.transaction_observation[0]),
            "DATA_PENDING_PUBLICATION_AND_ATTEMPT_FINALIZATION", False)
        body = deterministic_json(dict(operation="LP03_ATOMIC_LANE_DATA_V1", unit_of_work_id=base,
            original_grant_ref=attempt.grant_record.record_id, fence_ref=attempt.payload.fence_ref,
            terminal_observation_ref=terminal_ref, publication_ref=self.publication_ref,
            receipt_refs=tuple(row.record_id for row in spines), economic_event_refs=(event_id,),
            journal_ref=journal_id, posting_refs=journal.posting_refs, transition_ref=transition.transition_id,
            native_record_construction_observation=when, native_transaction_open_observation=self.transaction_observation))
        claim = IdempotencyClaimReceiptV1(base + "::CLAIM", "LP03-LANE-DATA::" + attempt.grant_record.record_id,
            "LP03_LANE_DATA", body, IdempotencyClaimStateV1.ACQUIRED, None, recorded, None, None)
        self.records = TrancheCAtomicRecordSetV1(claim, spines, (economic,), (), journal, postings, transition, projection.record_id)
        self.record_original = (self.header, self.raw, self.raw_original, self.records, self.accounts,
            self.heldout_score_records, self.recorded_dr_records, self.analytic_conversion_work, self.analytic_conversion_record,
            deterministic_json((self.header, self.raw, self.records, dict(self.accounts), self.heldout_score_records,
                self.recorded_dr_records, self.analytic_conversion_record)))
        self.phase = "PREPARED"
        _EvidenceLaneOperationV1._check_current_v1(self)


class EvidenceAvailabilityHandleV1:
    """Current original consumer capability; never durable or historical visibility."""

    __slots__ = ("_operation", "_original", "_available_at", "_purpose", "_record_refs", "_consumer_principal")

    def __init__(self):
        raise TypeError("availability requires the original publication resolver")

    def __copy__(self):
        raise TypeError("LP03 availability cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("LP03 availability cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("LP03 availability cannot be serialized")

    @property
    def available_at(self):
        return self._available_at

    def _assert_original_v1(self, *, operation, purpose, current_grant, clock):
        _native_require(type(self) is EvidenceAvailabilityHandleV1 and self._operation is operation
                        and operation.availability is self and self._original is not None,
                        "LP03_AVAILABILITY_NOT_ORIGINAL")
        original = self._original
        _native_require(self._purpose == purpose == original[0] and self._record_refs is operation.required_record_refs
                        and self._record_refs is original[1] and self._available_at is original[2]
                        and self._consumer_principal == operation.issuer.host.public_configuration.service_principal == original[3]
                        and operation.publication_readback_original is original[4]
                        and current_grant is original[5] and clock is original[6]
                        and operation.publication_phase == "COMMITTED_AND_READBACK", "LP03_AVAILABILITY_SCOPE_CHANGED")

    def _require_current_v1(self, *, operation, purpose, current_grant, clock):
        EvidenceAvailabilityHandleV1._assert_original_v1(self, operation=operation, purpose=purpose, current_grant=current_grant, clock=clock)
        _EvidenceLaneOperationV1._require_publication_purpose_v1(operation, purpose, current_grant, clock)
        observed = _EvidenceLaneOperationV1._check_current_v1(operation)
        EvidenceAvailabilityHandleV1._assert_original_v1(self, operation=operation, purpose=purpose, current_grant=current_grant, clock=clock)
        _EvidenceLaneOperationV1._require_publication_purpose_v1(operation, purpose, current_grant, clock)
        return observed


def _evidence_lane_member_from_storage_v1(raw, original):
    """Closed strict reconstruction after exact original-row comparison."""
    from dataclasses import fields
    from .serialization import _evidence_canonical_object_v1
    from .receipts import (_lp03_spine_from_storage_v1, _evidence_raw_spine_from_storage_v1,
        _evidence_quantum_trace_spine_from_storage_v1, TypedEconomicAmountV1)
    from .accounting import EntrySideV1
    from .lifecycle import TransitionDispositionV1
    if type(original) is EconomicReceiptEventSpineV1:
        if original.record_type is EconomicRecordTypeV1.LP03_EVIDENCE_CONTROL_V1:
            return _lp03_spine_from_storage_v1(raw, expected_record_id=original.record_id)
        if original.record_type is EconomicRecordTypeV1.ST12F_EVIDENCE_CONTROL:
            return _evidence_quantum_trace_spine_from_storage_v1(raw, expected_record_id=original.record_id)
        _native_require(original.record_type is EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT, "LP03_LANE_RAW_KIND")
        return _evidence_raw_spine_from_storage_v1(raw, expected_record_id=original.record_id)
    value = _evidence_canonical_object_v1(raw, max_bytes=1048576)
    if type(original) is dict:
        _native_require(set(original) == set(value) == {"binding_id", "claim_ref", "result_record_ref", "created_at"},
                        "LP03_LANE_RESULT_BINDING_FIELDS")
        _native_require(deterministic_json(value).encode("utf-8") == raw, "LP03_LANE_RESULT_BINDING_ENCODING")
        return value
    cls = type(original)
    _native_require(cls in (EconomicEventRecordV1, JournalTransactionV1, JournalPostingV1, OutboxIntentRecordV1,
                           StateTransitionReceiptV1, IdempotencyClaimReceiptV1), "LP03_LANE_MEMBER_KIND")
    _native_require(set(value) == {field.name for field in fields(cls)}, "LP03_LANE_MEMBER_FIELDS")
    data = dict(value)
    if cls is EconomicEventRecordV1:
        _native_require(type(data["source_record_refs"]) is list and type(data["typed_amounts"]) is list,
                        "LP03_LANE_ECONOMIC_ROSTERS")
        data["source_record_refs"] = tuple(data["source_record_refs"])
        amounts = []
        for amount in data["typed_amounts"]:
            _native_require(type(amount) is dict and set(amount) == {field.name for field in fields(TypedEconomicAmountV1)},
                            "LP03_LANE_ECONOMIC_AMOUNT_FIELDS")
            amounts.append(TypedEconomicAmountV1(**amount))
        data["typed_amounts"] = tuple(amounts)
    elif cls is JournalTransactionV1:
        for name in ("economic_event_refs", "posting_refs"):
            _native_require(type(data[name]) is list, "LP03_LANE_JOURNAL_ROSTER")
            data[name] = tuple(data[name])
    elif cls is JournalPostingV1:
        data["entry_side"] = EntrySideV1(data["entry_side"])
    elif cls is StateTransitionReceiptV1:
        data["disposition"] = TransitionDispositionV1(data["disposition"])
    elif cls is OutboxIntentRecordV1:
        from .outbox import OutboxDispatchStateV1
        data["dispatch_state"] = OutboxDispatchStateV1(data["dispatch_state"])
    else:
        data["claim_state"] = IdempotencyClaimStateV1(data["claim_state"])
    result = cls(**data)
    _native_require(deterministic_json(result).encode("utf-8") == raw, "LP03_LANE_MEMBER_CANONICAL_ENCODING")
    return result


def _evidence_control_operation_owner_v1(operation):
    """Closed exact native readback accounting owners; no caller callbacks."""
    from .input_resolver import _EvidencePublishedSourceReadV1
    owner = type(operation)
    _native_require(owner in (_EvidenceControlBootstrapV1, _EvidenceRegistrationOperationV1, _EvidenceLaneOperationV1,
                             _EvidenceConformanceOperationV1, _EvidenceReviewOperationV1, _EvidenceReviewedConformanceOperationV1,
                             _EvidenceReceiverOperationV1, _EvidenceClosedConformanceOperationV1, _EvidenceAttemptFailureAuditV1,
                             _EvidencePublishedSourceReadV1, _EvidenceColdControlReadV1),
                    "LP03_ORIGINAL_READBACK_OPERATION_REQUIRED")
    if owner is _EvidencePublishedSourceReadV1:
        _EvidencePublishedSourceReadV1._assert_original_v1(operation)
    original_operation = (operation.consumer if owner is _EvidencePublishedSourceReadV1 else
                          operation.attempt.registration if owner is _EvidenceLaneOperationV1 else
                          operation.registration if owner in (_EvidenceConformanceOperationV1, _EvidenceReviewOperationV1,
                              _EvidenceReviewedConformanceOperationV1, _EvidenceReceiverOperationV1,
                              _EvidenceClosedConformanceOperationV1) else operation)
    _native_require(operation.issuer.operation is original_operation and operation.issuer.lock._is_owned(),
                    "LP03_CONTROL_OPERATION_NOT_ORIGINAL")
    return owner


def _evidence_deny_legacy_store_access_v1(adapter) -> None:
    if getattr(adapter, "_evidence_store_binding_v1", None) is not None:
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE,
                                       "LP03_EXACT_PURPOSE_AND_CURRENT_GRANT_REQUIRED")


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


def _public_read_request_v1(request, references):
    from .receipts import _public_profile_v1

    _public_profile_v1(request.profile_id)
    for name in ("scope_ref", "capture_session_id", "root_ref"):
        _native_ident(getattr(request, name))
    _public_refs_v1(references)
    for name in ("effective_cutoff_ns", "recorded_cutoff_ns"):
        _public_nanoseconds_v1(getattr(request, name))
    _public_counter_v1(request.source_use_generation, allow_zero=True)
    _public_counter_v1(request.maximum_rows)
    _public_counter_v1(request.maximum_bytes)
    _native_require(len(references) <= request.maximum_rows <= 4096, "public read row bound exceeded")
    _native_require(type(request.read_purpose) is str and request.read_purpose in {
        "RESTORE_FOR_CURRENT_SESSION", "AUTHORIZED_HISTORICAL_RECONSTRUCTION"}, "unsupported public read purpose")


@dataclass(frozen=True, slots=True)
class PublicCaptureReadRequestV1:
    profile_id: object
    scope_ref: str
    capture_session_id: str
    observation_refs: tuple[str, ...]
    read_purpose: str
    effective_cutoff_ns: int
    recorded_cutoff_ns: int
    source_use_generation: int
    maximum_rows: int
    maximum_bytes: int
    root_ref: str

    def __post_init__(self):
        _public_read_request_v1(self, self.observation_refs)


@dataclass(frozen=True, slots=True)
class PublicPublicationReadRequestV1:
    profile_id: object
    scope_ref: str
    capture_session_id: str
    publication_refs: tuple[str, ...]
    read_purpose: str
    effective_cutoff_ns: int
    recorded_cutoff_ns: int
    source_use_generation: int
    maximum_rows: int
    maximum_bytes: int
    root_ref: str

    def __post_init__(self):
        _public_read_request_v1(self, self.publication_refs)


class PersistenceAdapterV1(ABC):
    """Typed append-only storage boundary; production technology remains unselected."""

    production_selection_state = PRODUCTION_PERSISTENCE_SELECTION_STATE_V1
    _source_use_integrity_failed_v1 = False

    def load_committed_public_capture_v1(self, request: PublicCaptureReadRequestV1, *, root_capability=None):
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "public capture read custody unavailable")

    def load_committed_public_publication_v1(self, request: PublicPublicationReadRequestV1, *, root_capability=None):
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "public publication read custody unavailable")

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
        if _source_action_reserved_v1(record) or _public_record_reserved_v1(record):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "attributed actions require original owner composition")
        if record.record_type is EconomicRecordTypeV1.LP03_EVIDENCE_CONTROL_V1:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE,
                                           "LP03_CONTROL_REQUIRES_ORIGINAL_ROLE_STORE")
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
        if record_ref.startswith(("SOURCE_ACTION::", '["PUBLIC_')):
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "attributed actions require specialized reads")
        with self._lock:
            for rows in self._tables.values():
                if record_ref in rows:
                    if _source_action_reserved_v1(rows[record_ref]) or _public_record_reserved_v1(rows[record_ref]):
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
                    if _public_record_reserved_v1(record):
                        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE,
                            "public records require their purpose-specific owner")
                    effective = getattr(record, "effective_at", None)
                    recorded = getattr(record, "recorded_at", getattr(record, "created_at", None))
                    aggregate = getattr(record, "aggregate_id", None)
                    if isinstance(effective, datetime) and isinstance(recorded, datetime) and effective <= effective_cutoff and recorded <= recorded_cutoff and (not aggregate_scope or aggregate in aggregate_scope):
                        if getattr(record, "record_type", None) is EconomicRecordTypeV1.SOURCE_USE_CONTROL:
                            record = self.load_committed_source_use_record_v1(record.record_id)
                        records.append(record)
        minimum = datetime.min.replace(tzinfo=UTC)
        return tuple(sorted(records, key=lambda row: (getattr(row, "aggregate_id", ""), getattr(row, "sequence", getattr(row, "event_sequence", 0)), getattr(row, "recorded_at", getattr(row, "created_at", minimum)), getattr(row, "record_id", getattr(row, "economic_event_id", getattr(row, "journal_transaction_id", getattr(row, "transition_id", "")))))))


def _public_record_reserved_v1(record: object) -> bool:
    from .receipts import PublicNativeObservationV1, PublicPublicationRecordV1

    return (getattr(record, "record_type", None) in {
                EconomicRecordTypeV1.PUBLIC_SOURCE_USE_CONTROL, EconomicRecordTypeV1.PUBLIC_NATIVE_CAPTURE,
                EconomicRecordTypeV1.PUBLIC_NATIVE_PUBLICATION}
            or type(getattr(record, "typed_payload", None)) in {
                PublicSourceUseOriginalV1, PublicDataSourceUseActionV1, PublicNativeObservationV1, PublicPublicationRecordV1}
            or any(type(value) is str and value.startswith('["PUBLIC_')
                   for value in (getattr(record, "record_id", None), getattr(record, "aggregate_id", None))))


def _source_action_reserved_v1(record: object) -> bool:
    return (getattr(record, "record_type", None) == EconomicRecordTypeV1.SOURCE_USE_ATTRIBUTED_ACTION
            or isinstance(getattr(record, "typed_payload", None), SourceUseAttributedActionV1)
            or type(getattr(record, "typed_payload", None)) is PublicDataSourceUseActionV1
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
        if getattr(self, "_public_control_mode", False):
            if process_ref is not None:
                _source_use_require_v1(process_ref == self._control_scope[2])
                aggregate = _public_identity_v1("PUBLIC_SOURCE_ACTION_V1", process_ref)
                matches = [row for row in tables["receipt_records"].values() if row.aggregate_id == aggregate]
                if not matches:
                    return None
                for row in matches:
                    _source_action_reconstruct_spine_v1(row)
                event_ref = max(matches, key=lambda row: row.sequence).record_id
            from .receipts import _public_control_ref_v1

            identity = _public_control_ref_v1(event_ref, kind="PUBLIC_SOURCE_ACTION_V1")
            _source_use_require_v1(identity[1] == self._control_scope[2])
            value = tables["receipt_records"].get(event_ref)
            return None if value is None else _source_action_from_storage_v1(value, record_id=event_ref)
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

    def _source_use_read_v1(self, tables, *, record_ref=None, stream_id=None):
        if not getattr(self, "_public_control_mode", False):
            return super()._source_use_read_v1(tables, record_ref=record_ref, stream_id=stream_id)
        _source_use_require_v1(self._scope_valid_v1())
        if stream_id is not None:
            _source_use_stream_id_v1(stream_id)
            aggregate = _public_identity_v1("PUBLIC_SOURCE_ORIGINAL_V1", stream_id)
            matches = [row for row in tables["receipt_records"].values() if row.aggregate_id == aggregate]
            if not matches:
                return None
            for row in matches:
                _source_use_reconstruct_spine_v1(row)
            record_ref = max(matches, key=lambda row: row.sequence).record_id
        from .receipts import _public_control_ref_v1

        _public_control_ref_v1(record_ref, kind="PUBLIC_SOURCE_ORIGINAL_V1")
        value = tables["receipt_records"].get(record_ref)
        return None if value is None else _source_use_from_storage_v1(value, record_id=record_ref)

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
