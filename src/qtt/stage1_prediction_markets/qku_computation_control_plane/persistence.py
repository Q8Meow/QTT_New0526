"""Backend-neutral typed persistence hierarchy and deterministic memory reference."""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
import time
import threading
from _thread import RLock
from typing import Mapping, ContextManager
from types import MappingProxyType

from .accounting import JournalPostingV1, JournalTransactionV1, ReconciliationBreakReceiptV1
from .context import _native_ident, parse_utc, _f14_freeze_v1, _f14_plain_v1
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
    EconomicRecordTypeV1,
    PrivateObservationClockReceiptV1, PrivateEvidenceWitnessV1,
    _f14_singleton_witness_v1, _f14_typed_spine_v1,
    ValueLineageEdgeV1,
    _private_clock_reconstruct_spine_v1,
    ProbabilityProducerControlReceiptV1, _validate_probability_control_spine_v1,
    _probability_control_spine_from_cells_v1, _probability_control_projection_v1,
    _probability_scope_mapping_v1,
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
from .models import (
    ProbabilityPredictionArtifactWriteRequestV1,
    ProbabilityPredictionArtifactSealV1,
    ProbabilityProducerScopeV1, ProbabilityPredictionReadRequestV1,
    ProbabilityPredictionReviewBasisReadRequestV1,
    _probability_require_v1, _probability_text_v1, _probability_ns_v1, _probability_int_v1,
)
from .serialization import _iter_prediction_artifact_frames_v1, _bounded_probability_json_v1


@dataclass(frozen=True, slots=True)
class ProbabilityProducerReadLimitsV1:
    max_records: int
    max_total_bytes: int
    max_frame_bytes: int
    max_sql_steps: int
    deadline_monotonic_ns: int

    def __post_init__(self) -> None:
        for value in (self.max_records, self.max_total_bytes, self.max_frame_bytes,
                      self.max_sql_steps, self.deadline_monotonic_ns):
            _probability_int_v1(value, 1)
        _probability_require_v1(self.max_records <= 2**63 - 2 and self.max_frame_bytes <= 1048576,
                                "PROBABILITY_READ_LIMIT")


@dataclass(frozen=True, slots=True)
class ProbabilityProducerReadRequestV1:
    scope: ProbabilityProducerScopeV1
    purpose: str
    binding_ref: str | None
    request_id: str | None
    receipt_id: str | None
    effective_cutoff_ns: int
    recorded_cutoff_ns: int
    limits: ProbabilityProducerReadLimitsV1

    def __post_init__(self) -> None:
        _probability_require_v1(type(self.scope) is ProbabilityProducerScopeV1 and
                                type(self.limits) is ProbabilityProducerReadLimitsV1, "PROBABILITY_READ_TYPES")
        _probability_ns_v1(self.effective_cutoff_ns); _probability_ns_v1(self.recorded_cutoff_ns)
        _probability_require_v1(type(self.purpose) is str and self.purpose in
                                ("MATERIALIZE_CURRENT", "CONSTRUCT_CANDIDATE", "READ_CURRENT_STATE", "EXACT_REPEAT"),
                                "PROBABILITY_READ_PURPOSE")
        if self.purpose in ("MATERIALIZE_CURRENT", "CONSTRUCT_CANDIDATE"):
            _probability_text_v1(self.binding_ref)
            _probability_require_v1(self.request_id is None and self.receipt_id is None, "PROBABILITY_READ_IDENTITY")
        elif self.purpose == "READ_CURRENT_STATE":
            _probability_require_v1(self.binding_ref is self.request_id is self.receipt_id is None, "PROBABILITY_READ_IDENTITY")
        else:
            _probability_text_v1(self.request_id); _probability_text_v1(self.receipt_id)
            _probability_require_v1(self.binding_ref is None and self.request_id != self.receipt_id, "PROBABILITY_READ_IDENTITY")


@dataclass(frozen=True, slots=True)
class ProbabilityProducerReadSnapshotV1:
    scope: ProbabilityProducerScopeV1
    records_by_ref: Mapping[str, EconomicReceiptEventSpineV1]
    publication_records: tuple[EconomicReceiptEventSpineV1, ...]
    revocation_records: tuple[EconomicReceiptEventSpineV1, ...]
    read_completed_ns: int

    def __post_init__(self) -> None:
        _probability_require_v1(type(self.scope) is ProbabilityProducerScopeV1 and
                                type(self.records_by_ref) in (dict, MappingProxyType), "PROBABILITY_SNAPSHOT")
        _probability_ns_v1(self.read_completed_ns)
        for key, record in self.records_by_ref.items():
            _validate_probability_control_spine_v1(record)
            _probability_require_v1(key == record.record_id and record.typed_payload.scope == self.scope,
                                    "PROBABILITY_SNAPSHOT_IDENTITY")
        for records, kind in ((self.publication_records, "PUBLICATION"), (self.revocation_records, "REVOCATION_APPLICATION")):
            _probability_require_v1(type(records) is tuple, "PROBABILITY_SNAPSHOT_ROWS")
            for record in records:
                _probability_require_v1(self.records_by_ref.get(record.record_id) is record and
                                        record.typed_payload.control_kind == kind, "PROBABILITY_SNAPSHOT_OBJECT")
        object.__setattr__(self, "records_by_ref", MappingProxyType(dict(self.records_by_ref)))


def _probability_read_check_v1(request) -> int:
    if type(request) not in (ProbabilityProducerReadRequestV1, ProbabilityPredictionReadRequestV1,
                             ProbabilityPredictionReviewBasisReadRequestV1):
        raise PersistenceContractError(ReasonCode.SCHEMA_MISMATCH, "PROBABILITY_READ_REQUEST")
    request.__post_init__()
    request.limits.__post_init__()
    now, mono = time.time_ns(), time.monotonic_ns()
    _probability_ns_v1(now)
    if type(mono) is not int or mono >= request.limits.deadline_monotonic_ns:
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "PROBABILITY_READ_DEADLINE")
    if request.effective_cutoff_ns > now or request.recorded_cutoff_ns > now:
        raise PersistenceContractError(ReasonCode.INVALID_CONTRACT, "PROBABILITY_READ_FUTURE_CUTOFF")
    return now


def _probability_read_roots_v1(request) -> tuple[str, ...]:
    if type(request) is ProbabilityProducerReadRequestV1:
        return (request.receipt_id,) if request.purpose == "EXACT_REPEAT" else (request.binding_ref,) if request.binding_ref is not None else ()
    if type(request) is ProbabilityPredictionReviewBasisReadRequestV1:
        return (request.result_ref, *request.validation_receipt_refs, request.use_limit_ref,
                request.model_risk_receipt_ref, request.binding_ref)
    return (request.result_ref,) if request.review_ref is None else (request.result_ref, request.review_ref)


def _probability_read_aggregates_v1(scope) -> tuple[str, ...]:
    return tuple(deterministic_json(("V35", kind, _probability_scope_mapping_v1(scope))) for kind in
                 ("PUBLICATION", "INPUT_BINDING", "ACCEPTANCE_MANIFEST", "ACCEPTANCE_RECEIPT", "REVOCATION_APPLICATION"))


def _probability_cell_sizes_v1(cells, *, max_frame_bytes: int) -> tuple[int, ...]:
    if type(cells) is not tuple or len(cells) != 5 or any(type(cell) is not str for cell in cells):
        raise PersistenceContractError(ReasonCode.SCHEMA_MISMATCH, "PROBABILITY_STORAGE_CELLS")
    lengths = []
    for cell in cells:
        length = 0
        for char in cell:
            point = ord(char)
            if 0xD800 <= point <= 0xDFFF:
                raise PersistenceContractError(ReasonCode.SCHEMA_MISMATCH, "PROBABILITY_STORAGE_SURROGATE")
            length += 1 if point < 128 else 2 if point < 2048 else 3 if point < 65536 else 4
            if length > max_frame_bytes:
                raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "PROBABILITY_READ_FRAME_BUDGET")
        lengths.append(length)
    return tuple(lengths)


def _probability_require_append_context_v1(adapter, transaction, record) -> None:
    # Only the original private owner binds this guard. Historical hydration and
    # a matching record ID cannot create an active issued append context.
    guard = getattr(adapter, "_probability_preappend_guard_v1", None)
    if guard is None:
        raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "probability append context is absent")
    guard(transaction, record)


def _probability_select_committed_cells_v1(request, exact, aggregate):
    """One closed selection program shared by the two storage owners."""
    cells_by_ref, decoded = {}, {}

    def retain(cells):
        if cells is None:
            return None
        key = cells[0]
        if key in cells_by_ref:
            if cells_by_ref[key] != cells:
                raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "PROBABILITY_RECORD_CHANGED")
            return decoded[key]
        record = _probability_control_spine_from_cells_v1(cells, expected_record_id=key,
                    expected_scope=request.scope, max_frame_bytes=request.limits.max_frame_bytes)
        cells_by_ref[key], decoded[key] = cells, record
        return record

    def get(ref, kind=None, *, required=True):
        record = retain(exact(ref, required))
        if record is not None and kind is not None and record.typed_payload.control_kind != kind:
            raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_SELECTED_KIND")
        return record

    def ancestry(binding_ref):
        binding = get(binding_ref, "INPUT_BINDING")
        manifest = get(binding.typed_payload.body["acceptance_manifest_ref"], "ACCEPTANCE_MANIFEST")
        if manifest.typed_payload.body["binding_ref"] != binding_ref:
            raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_MANIFEST_BINDING")
        roles = tuple(get(ref, "ACCEPTANCE_RECEIPT") for ref in manifest.typed_payload.body["receipt_refs"])
        origins = {row.typed_payload.body["binding_ref"] for row in roles[:6]}
        if len(origins) != 1:
            raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_MIXED_ORIGIN")
        origin_ref = next(iter(origins))
        if origin_ref != binding_ref:
            if len(roles) != 7 or roles[-1].typed_payload.body["binding_ref"] != binding_ref:
                raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_SUCCESSOR_LAYOUT")
            origin = get(origin_ref, "INPUT_BINDING")
            original_manifest = get(origin.typed_payload.body["acceptance_manifest_ref"], "ACCEPTANCE_MANIFEST")
            if (original_manifest.typed_payload.body["binding_ref"] != origin_ref or
                    original_manifest.typed_payload.body["receipt_refs"] != manifest.typed_payload.body["receipt_refs"][:6]):
                raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_RECURSIVE_OR_CHANGED_ORIGIN")
        return binding

    if request.purpose == "EXACT_REPEAT":
        root = get(request.receipt_id, "PUBLICATION", required=False)
        if root is None:
            return cells_by_ref, decoded
        if root.typed_payload.body["request_id"] != request.request_id:
            raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_EXACT_REPEAT_IDENTITY")
    elif request.purpose in ("CONSTRUCT_CANDIDATE", "MATERIALIZE_CURRENT"):
        ancestry(request.binding_ref)
    elif type(request) in (ProbabilityPredictionReadRequestV1, ProbabilityPredictionReviewBasisReadRequestV1):
        result = get(request.result_ref, "PREDICTION_RESULT")
        # Only direct native dependencies are inspected; arbitrary ancestors are
        # never recursively chased. External references still need issuer proof.
        bindings = []
        for ref in result.typed_payload.dependency_refs:
            dependency = get(ref, required=False)
            if dependency is not None and dependency.typed_payload.control_kind == "INPUT_BINDING":
                bindings.append(dependency)
        if len(bindings) != 1:
            raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_RESULT_ORIGINAL_BINDING")
        binding = ancestry(bindings[0].record_id)
        if tuple(row["role"] for row in binding.typed_payload.body["objects"]) != ("MODEL", "CATALOG", "POLICY"):
            raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_RESULT_PRE_RESULT_BINDING")
        if type(request) is ProbabilityPredictionReviewBasisReadRequestV1:
            if request.binding_ref != binding.record_id:
                raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_BASIS_BINDING")
            basis = (*request.validation_receipt_refs, request.use_limit_ref, request.model_risk_receipt_ref)
        elif request.review_ref is not None:
            review = get(request.review_ref, "PREDICTION_REVIEW")
            body = review.typed_payload.body
            if body["result_ref"] != result.record_id:
                raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_REVIEW_RESULT_JOIN")
            basis = (*body["validation_receipt_refs"], body["use_limit_ref"], body["model_risk_receipt_ref"])
        else:
            basis = ()
        for ref in basis:
            get(ref, "ACCEPTANCE_RECEIPT")
    kinds = ("PUBLICATION", "INPUT_BINDING", "ACCEPTANCE_MANIFEST", "ACCEPTANCE_RECEIPT", "REVOCATION_APPLICATION") if request.purpose == "READ_CURRENT_STATE" else (
        ("PUBLICATION", "REVOCATION_APPLICATION") if type(request) is ProbabilityProducerReadRequestV1 else ("REVOCATION_APPLICATION",))
    for kind in kinds:
        key = deterministic_json(("V35", kind, _probability_scope_mapping_v1(request.scope)))
        for cells in aggregate(key):
            retain(cells)
    return cells_by_ref, decoded


def _probability_snapshot_from_cells_v1(request, cells_by_ref, observed_ns, *, decoded_records=None):
    records = {}
    for key, cells in cells_by_ref.items():
        _probability_read_check_v1(request)
        record = (decoded_records[key] if decoded_records is not None else
                  _probability_control_spine_from_cells_v1(cells, expected_record_id=key,
                    expected_scope=request.scope, max_frame_bytes=request.limits.max_frame_bytes))
        payload = record.typed_payload
        if (payload.effective_ns <= request.effective_cutoff_ns and payload.recorded_ns <= request.recorded_cutoff_ns
                and payload.available_ns <= observed_ns):
            records[key] = record
        elif request.purpose not in ("READ_CURRENT_STATE", "EXACT_REPEAT") and payload.control_kind not in ("PUBLICATION", "REVOCATION_APPLICATION"):
            raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "PROBABILITY_REQUIRED_RECORD_AFTER_CUTOFF")
    for ref in _probability_read_roots_v1(request):
        if ref not in records:
            if request.purpose == "EXACT_REPEAT" and ref not in cells_by_ref:
                return ProbabilityProducerReadSnapshotV1(request.scope, {}, (), (), observed_ns)
            raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "PROBABILITY_REQUIRED_COMMITTED_RECORD")
    if request.purpose == "EXACT_REPEAT":
        payload = records[request.receipt_id].typed_payload
        if payload.control_kind != "PUBLICATION" or payload.body["request_id"] != request.request_id:
            raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_EXACT_REPEAT_IDENTITY")
    publications = tuple(sorted((row for row in records.values() if row.typed_payload.control_kind == "PUBLICATION"), key=lambda row: row.sequence))
    previous = None
    for index, record in enumerate(publications, 1):
        if record.sequence != index or record.typed_payload.body["expected_head_ref"] != previous:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "PROBABILITY_PUBLICATION_HISTORY")
        previous = record.record_id
    revocations = tuple(sorted((row for row in records.values() if row.typed_payload.control_kind == "REVOCATION_APPLICATION"), key=lambda row: row.sequence))
    if revocations:
        identity = tuple(revocations[0].typed_payload.body[key] for key in ("issuer_ref", "stream_ref", "baseline_ref"))
        for index, record in enumerate(revocations):
            body = record.typed_payload.body
            if (tuple(body[key] for key in ("issuer_ref", "stream_ref", "baseline_ref")) != identity or
                    record.sequence != revocations[0].sequence + index):
                raise PersistenceContractError(ReasonCode.PERSISTENCE_CONFLICT, "PROBABILITY_REVOCATION_HISTORY")
    if request.purpose in ("MATERIALIZE_CURRENT", "CONSTRUCT_CANDIDATE"):
        binding = records[request.binding_ref]
        if binding.typed_payload.control_kind != "INPUT_BINDING":
            raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_BINDING_KIND")
        manifest = records.get(binding.typed_payload.body["acceptance_manifest_ref"])
        if (manifest is None or manifest.typed_payload.control_kind != "ACCEPTANCE_MANIFEST" or
                manifest.typed_payload.body["binding_ref"] != binding.record_id):
            raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "PROBABILITY_MANIFEST_JOIN")
        expected = ("SOURCE_RIGHTS", "ENVIRONMENT", "MODEL_BUILD", "MODEL_REVIEW", "USE_POLICY", "CATALOG")
        if len(binding.typed_payload.body["objects"]) == 4:
            expected += ("COMPUTATION",)
        if request.purpose == "CONSTRUCT_CANDIDATE" and len(expected) != 6:
            raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_CONSTRUCTION_HAS_RESULT")
        role_refs = manifest.typed_payload.body["receipt_refs"]
        if len(role_refs) != len(expected):
            raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_MANIFEST_ROLES")
        for ref, role in zip(role_refs, expected, strict=True):
            receipt = records.get(ref)
            if (receipt is None or receipt.typed_payload.control_kind != "ACCEPTANCE_RECEIPT" or
                    receipt.typed_payload.body["role"] != role):
                raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_ROLE_JOIN")
    if type(request) in (ProbabilityPredictionReadRequestV1, ProbabilityPredictionReviewBasisReadRequestV1):
        if records[request.result_ref].typed_payload.control_kind != "PREDICTION_RESULT":
            raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_RESULT_KIND")
        if type(request) is ProbabilityPredictionReadRequestV1 and request.review_ref is not None:
            review = records[request.review_ref].typed_payload
            if review.control_kind != "PREDICTION_REVIEW" or review.body["result_ref"] != request.result_ref:
                raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_REVIEW_RESULT_JOIN")
    return ProbabilityProducerReadSnapshotV1(request.scope, records, publications, revocations, observed_ns)


def _finalize_prediction_artifact_v1(*, bank, request, artifact_writer, check_current=None) -> ProbabilityPredictionArtifactSealV1:
    """Finalize one bounded artifact; receipt publication remains a separate step.

    The caller retains the original admitted bank/request/writer and dependency
    fence. A returned seal does not admit a source, a model, or a receipt append.
    """
    def require(ok: bool, message: str) -> None:
        if not ok:
            raise PersistenceContractError(ReasonCode.INVALID_CONTRACT, message)

    require(type(request) is ProbabilityPredictionArtifactWriteRequestV1,
            "PROBABILITY_ARTIFACT_REQUEST")
    if artifact_writer is None or not callable(getattr(artifact_writer, "begin_prediction_artifact_v1", None)):
        raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "prediction artifact writer is absent")
    effective_valid_until_ns = request.valid_until_ns
    previous_utc = previous_monotonic = None

    def current() -> int:
        nonlocal previous_utc, previous_monotonic
        now = time.time_ns()
        mono = time.monotonic_ns()
        require(type(now) is int and type(mono) is int, "PROBABILITY_ARTIFACT_CLOCK")
        require((previous_utc is None or now >= previous_utc) and
                (previous_monotonic is None or mono >= previous_monotonic), "PROBABILITY_ARTIFACT_CLOCK_REGRESSED")
        require(now < effective_valid_until_ns, "PROBABILITY_ARTIFACT_EXPIRED")
        require(mono < request.deadline_monotonic_ns, "PROBABILITY_ARTIFACT_DEADLINE")
        if check_current is not None:
            require(check_current() is None, "PROBABILITY_ARTIFACT_SOURCE_CHECK_RESULT")
        previous_utc, previous_monotonic = now, mono
        return now

    def frames():
        return _iter_prediction_artifact_frames_v1(
            bank, max_bytes=request.max_artifact_bytes, max_frames=request.max_frames)

    current()
    body_ok = seal_attempted = False
    seal = None
    body_error = abort_error = exit_error = None
    try:
        with artifact_writer.begin_prediction_artifact_v1(request) as session:
            try:
                total = count = 0
                for frame in frames():
                    current()
                    require(type(frame) is bytes and 0 < len(frame) <= 65537 and frame.endswith(b"\n"),
                            "PROBABILITY_ARTIFACT_FRAME")
                    require(total + len(frame) <= request.max_artifact_bytes and count < request.max_frames,
                            "PROBABILITY_ARTIFACT_BUDGET")
                    session.append_prediction_frame_v1(frame)
                    total += len(frame)
                    count += 1
                    current()
                require(count > 0 and total > 0, "PROBABILITY_ARTIFACT_EMPTY")
                current()
                written = iter(session.iter_written_prediction_frames_v1())
                expected = iter(frames())
                expected_end, actual_end = object(), object()
                verified_count = verified_bytes = 0
                while True:
                    current()
                    wanted = next(expected, expected_end)
                    current()
                    actual = next(written, actual_end)
                    current()
                    if wanted is expected_end and actual is actual_end:
                        break
                    require(wanted is not expected_end and actual is not actual_end and
                            type(actual) is bytes and actual == wanted, "PROBABILITY_ARTIFACT_READBACK")
                    verified_count += 1
                    verified_bytes += len(actual)
                require((verified_count, verified_bytes) == (count, total), "PROBABILITY_ARTIFACT_READBACK_COUNT")
                current()
                # Even a raising or malformed seal can have published the artifact.
                seal_attempted = True
                seal = session.seal_prediction_artifact_v1()
                require(type(seal) is ProbabilityPredictionArtifactSealV1, "PROBABILITY_ARTIFACT_SEAL")
                require((seal.artifact_ref, seal.scope, seal.result_ref, seal.dependency_refs) ==
                        (request.artifact_ref, request.scope, request.result_ref, request.dependency_refs),
                        "PROBABILITY_ARTIFACT_SEAL_IDENTITY")
                require(type(seal.byte_count) is int and type(seal.frame_count) is int and
                        (seal.byte_count, seal.frame_count) == (total, count), "PROBABILITY_ARTIFACT_SEAL_COUNT")
                require(seal.observed_ns <= current() < seal.valid_until_ns <= request.valid_until_ns,
                        "PROBABILITY_ARTIFACT_SEAL_LIFETIME")
                effective_valid_until_ns = min(effective_valid_until_ns, seal.valid_until_ns)
                current()
                body_ok = True
            except BaseException as error:
                body_error = error
                if not seal_attempted:
                    try:
                        session.abort_unpublished_prediction_stage_v1()
                    except BaseException as cleanup_error:
                        abort_error = cleanup_error
                raise
    except BaseException as error:
        exit_error = error
    failures = []
    for error in (body_error, abort_error, exit_error):
        if error is not None and not any(error is saved for saved in failures):
            failures.append(error)
    if len(failures) == 1:
        raise failures[0]
    if failures:
        raise BaseExceptionGroup("prediction artifact body, abort and exit failures", failures)
    require(body_ok and seal is not None, "PROBABILITY_ARTIFACT_BODY_NOT_COMPLETED")
    current()
    return seal


@contextmanager
def _probability_combined_read_budget_v1(adapter, *, scope, max_total_bytes):
    """One owned byte allowance spanning both metadata reads and the artifact."""
    _probability_int_v1(max_total_bytes, 1)
    _probability_require_v1(type(scope) is ProbabilityProducerScopeV1, "PROBABILITY_SCOPE")
    if getattr(adapter, "_probability_read_accounting_v1", None) is not None:
        raise PersistenceContractError(ReasonCode.TRANSACTION_STATE_INVALID, "probability combined read is already owned")
    ledger = {"scope": scope, "maximum": max_total_bytes, "used": 0,
              "thread": threading.get_ident()}
    adapter._probability_read_accounting_v1 = ledger
    try:
        yield ledger
    finally:
        if getattr(adapter, "_probability_read_accounting_v1", None) is not ledger:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "probability byte owner changed")
        adapter._probability_read_accounting_v1 = None


def _probability_charge_read_v1(adapter, scope, size):
    ledger = getattr(adapter, "_probability_read_accounting_v1", None)
    if ledger is None:
        return
    if (ledger["scope"] != scope or ledger["thread"] != threading.get_ident() or
            type(size) is not int or size < 0 or ledger["used"] + size > ledger["maximum"]):
        raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "PROBABILITY_COMBINED_READ_BYTE_BUDGET")
    ledger["used"] += size


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

    def load_committed_probability_producer_state_v1(
        self, request: ProbabilityProducerReadRequestV1 | ProbabilityPredictionReadRequestV1 | ProbabilityPredictionReviewBasisReadRequestV1,
    ) -> ContextManager[ProbabilityProducerReadSnapshotV1]:
        raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "committed probability reader is absent")

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
        self._probability_read_active_v1 = False

    @property
    def availability(self) -> PersistenceAvailabilityV1:
        return PersistenceAvailabilityV1.AVAILABLE_REFERENCE

    def begin_transaction(self) -> PersistenceTransactionV1:
        self._lock.acquire()
        try:
            if self._probability_read_active_v1:
                raise TransactionContractError(ReasonCode.TRANSACTION_STATE_INVALID, "probability read owns this adapter")
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

    def _probability_append_snapshot_v1(self, transaction, request):
        from dataclasses import replace
        tx = self._transaction(transaction)
        # The writer's committed cut is fresh. The preparation cut cannot hide
        # a later competing publication or applied revocation from the CAS.
        now = _probability_read_check_v1(request)
        request = replace(request, effective_cutoff_ns=now, recorded_cutoff_ns=now)
        cells, decoded = _probability_memory_cells_v1(self, request, tx._committed_snapshot)
        return _probability_snapshot_from_cells_v1(request, cells, _probability_read_check_v1(request), decoded_records=decoded)

    def insert_receipt_record(self, transaction: PersistenceTransactionV1, record: EconomicReceiptEventSpineV1) -> None:
        tx = self._transaction(transaction)
        payload = record.typed_payload
        if (record.record_type is EconomicRecordTypeV1.PROBABILITY_PRODUCER_CONTROL
                or type(payload) is ProbabilityProducerControlReceiptV1):
            _validate_probability_control_spine_v1(record)
            _probability_require_append_context_v1(self, tx, record)
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

    @contextmanager
    def load_committed_probability_producer_state_v1(self, request):
        started = _probability_read_check_v1(request)
        self._lock.acquire()
        claimed = False
        body_error = cleanup_error = None
        body_ok = False
        try:
            if self._probability_read_active_v1 or (self._active_transaction is not None and self._active_transaction.is_active):
                raise PersistenceContractError(ReasonCode.TRANSACTION_STATE_INVALID, "probability read conflicts with adapter ownership")
            self._probability_read_active_v1 = True
            claimed = True
            selected_cells, decoded = _probability_memory_cells_v1(self, request, self._tables)
            observed = _probability_read_check_v1(request)
            if observed < started:
                raise PersistenceContractError(ReasonCode.INVALID_CONTRACT, "PROBABILITY_READ_CLOCK_REGRESSED")
            snapshot = _probability_snapshot_from_cells_v1(request, selected_cells, observed, decoded_records=decoded)
            yield snapshot
            body_ok = True
        except BaseException as error:
            body_error = error
        finally:
            try:
                self._lock.release()
            except BaseException as error:
                cleanup_error = error
            else:
                if claimed:
                    self._probability_read_active_v1 = False
        failures = [error for error in (body_error, cleanup_error) if error is not None]
        if len(failures) == 1:
            raise failures[0]
        if failures:
            raise BaseExceptionGroup("probability memory read and cleanup failures", failures)
        if not body_ok:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "PROBABILITY_READ_BODY_NOT_COMPLETED")
        if _probability_read_check_v1(request) < observed:
            raise PersistenceContractError(ReasonCode.INVALID_CONTRACT, "PROBABILITY_READ_CLOCK_REGRESSED")

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


def _probability_memory_cells_v1(self, request, tables):
    cells_by_ref = {}
    total = 0

    def acquire(record):
        nonlocal total
        _probability_read_check_v1(request)
        if type(record) is not EconomicReceiptEventSpineV1:
            raise PersistenceContractError(ReasonCode.SCHEMA_MISMATCH, "PROBABILITY_RECORD_TYPE")
        if record.record_id in cells_by_ref:
            return cells_by_ref[record.record_id]
        if type(record.typed_payload) is not ProbabilityProducerControlReceiptV1:
            raise PersistenceContractError(ReasonCode.SCHEMA_MISMATCH, "PROBABILITY_PAYLOAD_TYPE")
        if len(cells_by_ref) >= request.limits.max_records:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "PROBABILITY_READ_RECORD_BUDGET")
        canonical = _bounded_probability_json_v1(_probability_control_projection_v1(record), max_bytes=request.limits.max_frame_bytes)
        _validate_probability_control_spine_v1(record)
        cells = (record.record_id, record.effective_at.isoformat(), record.recorded_at.isoformat(), record.aggregate_id, canonical)
        size = sum(_probability_cell_sizes_v1(cells, max_frame_bytes=request.limits.max_frame_bytes))
        if total + size > request.limits.max_total_bytes:
            raise PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "PROBABILITY_READ_BYTE_BUDGET")
        _probability_charge_read_v1(self, request.scope, size)
        cells_by_ref[record.record_id] = cells
        total += size
        return cells

    def exact(ref, required):
        _probability_read_check_v1(request)
        record = tables["receipt_records"].get(ref)
        if record is None:
            if (required or request.purpose == "EXACT_REPEAT") and any(ref in rows for name, rows in tables.items() if name != "receipt_records"):
                raise PersistenceContractError(ReasonCode.INPUT_OWNER_MISMATCH, "PROBABILITY_REFERENCE_TABLE")
            if required:
                raise PersistenceContractError(ReasonCode.OWNER_DATA_MISSING, "PROBABILITY_REQUIRED_COMMITTED_RECORD")
            return None
        return acquire(record)

    def aggregate(key):
        for record in tables["receipt_records"].values():
            _probability_read_check_v1(request)
            if type(record) is EconomicReceiptEventSpineV1 and record.aggregate_id == key:
                yield acquire(record)

    selected_cells, decoded = _probability_select_committed_cells_v1(request, exact, aggregate)
    return selected_cells, decoded
