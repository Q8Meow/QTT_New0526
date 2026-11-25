"""OP13 contract compiler: one parent lock, 52 templates, and 104 slots."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from types import MappingProxyType
from typing import Mapping

from .context import parse_utc
from .errors import (
    ContractValidationError,
    IdempotencyContractError,
    PersistenceContractError,
    ReasonCode,
)
from .idempotency import (
    IdempotencyClaimReceiptV1,
    IdempotencyClaimStateV1,
    IdempotencyOutcomeV1,
    canonical_request_json_v1,
)
from .input_lock import (
    CanonicalReplayPaperInputSnapshotV1,
    ImmutableReplayPaperInputLockV1,
    ST12F_PAPER_RESULT_CONTRACT_IDS_V1,
    ST12F_REPLAY_RESULT_CONTRACT_IDS_V1,
    ST12F_TEMPLATE_IDS_V1,
    build_immutable_replay_paper_input_lock_v1,
    validated_st12f_identity_token_v1,
)
from .lifecycle import StateTransitionReceiptV1, TransitionDispositionV1
from .models import CompileReplayPaperCohortRequestV1, NO_EFFECTS_V1
from .parameter_policy import initialize_st12f_parameter_registry_v1
from .persistence import PersistenceAdapterV1, PersistenceAvailabilityV1
from .receipts import (
    EconomicReceiptEventSpineV1,
    EconomicRecordTypeV1,
    ST12FEvidenceControlReceiptRecordV1,
    ST12FReceiptClassV1,
)
from .serialization import deterministic_json


COHORT_COMPILATION_SCHEMA_VERSION_V1 = "QTT_ST12F_REPLAY_PAPER_COHORT_COMPILATION_V1_4"
COHORT_COMPILATION_CONTRACT_VERSION_V1 = "1.4"


def _source_epoch_refs(values: Mapping[str, object]) -> tuple[str, ...]:
    return tuple(f"{key}={values[key]}" for key in sorted(values))


@dataclass(frozen=True, slots=True)
class EvidenceRegisteredCompilationRequestV1:
    """Inert exact-reference assertion around the unchanged compilation request."""

    registration_ref: object
    compilation_request: CompileReplayPaperCohortRequestV1

    def __post_init__(self):
        from .context import _native_require
        from .models import EvidenceRecordRefV1
        _native_require(type(self.registration_ref) is EvidenceRecordRefV1
                        and type(self.compilation_request) is CompileReplayPaperCohortRequestV1,
                        "LP03_REGISTERED_COMPILATION_REQUEST")


@dataclass(frozen=True, slots=True)
class ReplayPaperCohortCompilationRecordV1:
    compilation_id: str
    schema_version: str
    contract_version: str
    input_lock_id: str
    cohort_template_ids: tuple[str, ...]
    expected_replay_result_contract_ids: tuple[str, ...]
    expected_paper_result_contract_ids: tuple[str, ...]
    input_lock: ImmutableReplayPaperInputLockV1
    created_at: datetime

    def __post_init__(self) -> None:
        if self.schema_version != COHORT_COMPILATION_SCHEMA_VERSION_V1 or self.contract_version != COHORT_COMPILATION_CONTRACT_VERSION_V1:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "cohort compilation schema or contract version differs",
            )
        token = self.compilation_id.removeprefix("ST12F-COMPILATION::")
        if self.compilation_id != f"ST12F-COMPILATION::{validated_st12f_identity_token_v1(token)}":
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "compilation identity is not the deterministic natural identity",
            )
        if type(self.input_lock) is not ImmutableReplayPaperInputLockV1 or self.input_lock_id != self.input_lock.input_lock_id:
            raise ContractValidationError(
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                "compilation must contain exactly one matching immutable lock",
            )
        if (
            self.cohort_template_ids != ST12F_TEMPLATE_IDS_V1
            or self.expected_replay_result_contract_ids != ST12F_REPLAY_RESULT_CONTRACT_IDS_V1
            or self.expected_paper_result_contract_ids != ST12F_PAPER_RESULT_CONTRACT_IDS_V1
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_TEMPLATE_ROSTER_MISMATCH,
                "compilation must contain the exact 52/52/52 ordered rosters",
            )
        object.__setattr__(
            self,
            "created_at",
            parse_utc(self.created_at, field_name="created_at"),
        )
        if self.created_at != self.input_lock.created_at:
            raise ContractValidationError(
                ReasonCode.POINT_IN_TIME_FRESHNESS_OR_SEQUENCE_INVALID,
                "compilation and immutable lock creation times differ",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "ReplayPaperCohortCompilationRecordV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "cohort compilation payload field roster differs",
            )
        payload = dict(value)
        for name in (
            "cohort_template_ids",
            "expected_replay_result_contract_ids",
            "expected_paper_result_contract_ids",
        ):
            payload[name] = tuple(payload[name])
        payload["input_lock"] = ImmutableReplayPaperInputLockV1.from_canonical_mapping(
            payload["input_lock"]
        )
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


@dataclass(frozen=True, slots=True)
class ReplayPaperExpectedSlotV1:
    compilation_id: str
    input_lock_id: str
    lane: str
    cohort_template_id: str
    expected_result_contract_id: str

    def __post_init__(self) -> None:
        if self.lane not in {"REPLAY", "PAPER"}:
            raise ContractValidationError(
                ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN,
                "expected slot lane must be exact REPLAY or PAPER",
            )
        expected = f"ST12F-{self.lane}-CONTRACT::{self.cohort_template_id}"
        if self.cohort_template_id not in ST12F_TEMPLATE_IDS_V1 or self.expected_result_contract_id != expected:
            raise ContractValidationError(
                ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                "expected result slot identity does not match its template and lane",
            )


def _read_original_compilation_member_v1(raw, *, operation, record_ref):
    """Decode only either original legacy contract in this admitted binding."""
    from .context import _native_require
    from .serialization import _evidence_canonical_object_v1
    original = operation.binding_original
    _native_require(original is not None and operation.compiler is original[0]
                    and operation.compilation_request is original[1] and operation.compilation is original[2]
                    and operation.binding_spines is original[3], "LP03_ORIGINAL_COMPILATION_CHANGED")
    matches = tuple(index for index, spine in enumerate(original[3]) if spine.record_id == record_ref)
    _native_require(len(matches) == 1, "LP03_COMPILATION_READBACK_MEMBER")
    index = matches[0]
    _native_require(raw == original[6][index].encode("utf-8"), "LP03_COMPILATION_READBACK_BYTES")
    parsed = _evidence_canonical_object_v1(raw, max_bytes=1048576)
    body = _evidence_canonical_object_v1(parsed["typed_payload"]["canonical_contract_json"].encode("utf-8"), max_bytes=1048576)
    if index == 0:
        result = ReplayPaperCohortCompilationRecordV1.from_canonical_mapping(body)
        expected = operation.compilation
    else:
        result = ImmutableReplayPaperInputLockV1.from_canonical_mapping(body)
        expected = operation.compilation.input_lock
    _native_require(result == expected, "LP03_COMPILATION_READBACK_CONTRACT")


class ReplayPaperCohortCompilerV1:
    """Pure contract materialization plus existing ST12-C append-only custody."""

    def __init__(
        self,
        canonical_snapshot: CanonicalReplayPaperInputSnapshotV1,
        persistence_adapter: PersistenceAdapterV1,
    ) -> None:
        if type(canonical_snapshot) is not CanonicalReplayPaperInputSnapshotV1:
            raise ContractValidationError(
                ReasonCode.INPUT_OWNER_MISMATCH,
                "compiler requires the exact injected canonical input snapshot",
            )
        if not isinstance(persistence_adapter, PersistenceAdapterV1) or persistence_adapter.availability is not PersistenceAvailabilityV1.AVAILABLE_REFERENCE:
            raise PersistenceContractError(
                ReasonCode.PERSISTENCE_UNAVAILABLE,
                "OP13 requires the existing available ST12-C persistence adapter",
            )
        self._canonical_snapshot = canonical_snapshot
        self._persistence = persistence_adapter
        self._compilations: dict[str, ReplayPaperCohortCompilationRecordV1] = {}
        self._locks: dict[str, ImmutableReplayPaperInputLockV1] = {}
        self._slots: dict[tuple[str, str, str], ReplayPaperExpectedSlotV1] = {}

    @property
    def canonical_snapshot(self) -> CanonicalReplayPaperInputSnapshotV1:
        return self._canonical_snapshot

    def _index(self, compilation: ReplayPaperCohortCompilationRecordV1) -> None:
        compilations, locks, slots = ReplayPaperCohortCompilerV1._index_members_v1(self, compilation)
        self._compilations.update(compilations)
        self._locks.update(locks)
        self._slots.update(slots)

    def _index_members_v1(self, compilation):
        """Build the same inert 104 slots without publishing compiler caches."""
        compilations = {compilation.compilation_id: compilation}
        locks = {compilation.input_lock_id: compilation.input_lock}
        slots = {}
        for lane, contract_ids in (
            ("REPLAY", compilation.expected_replay_result_contract_ids),
            ("PAPER", compilation.expected_paper_result_contract_ids),
        ):
            for template_id, contract_id in zip(
                compilation.cohort_template_ids,
                contract_ids,
                strict=True,
            ):
                slot = ReplayPaperExpectedSlotV1(
                    compilation.compilation_id,
                    compilation.input_lock_id,
                    lane,
                    template_id,
                    contract_id,
                )
                slots[(compilation.compilation_id, lane, contract_id)] = slot
        return compilations, locks, slots

    def _load_compilation_receipt(
        self,
        compilation_id: str,
        *,
        decision_cutoff: datetime,
    ) -> ReplayPaperCohortCompilationRecordV1:
        receipt_ref = f"ST12F-RECEIPT::{compilation_id}::COHORT_COMPILATION"
        cutoff = parse_utc(decision_cutoff, field_name="decision_cutoff")
        matches = tuple(
            row
            for row in self._persistence.reconstruct_as_of(
                effective_cutoff=cutoff,
                recorded_cutoff=cutoff,
                aggregate_scope=(),
            )
            if type(row) is EconomicReceiptEventSpineV1
            and row.record_id == receipt_ref
        )
        spine = matches[0] if len(matches) == 1 else None
        if type(spine) is not EconomicReceiptEventSpineV1 or type(spine.typed_payload) is not ST12FEvidenceControlReceiptRecordV1:
            raise PersistenceContractError(
                ReasonCode.OWNER_DATA_MISSING,
                "cohort compilation receipt is absent",
            )
        compilation = spine.typed_payload.reconstruct(
            ReplayPaperCohortCompilationRecordV1
        )
        self._index(compilation)
        return compilation

    def resolve_compilation(
        self,
        compilation_id: str,
        *,
        decision_cutoff: datetime,
    ) -> ReplayPaperCohortCompilationRecordV1:
        return self._load_compilation_receipt(
            compilation_id,
            decision_cutoff=decision_cutoff,
        )

    def resolve_input_lock(
        self,
        input_lock_id: str,
        *,
        decision_cutoff: datetime,
    ) -> ImmutableReplayPaperInputLockV1:
        token = input_lock_id.removeprefix("ST12F-LOCK::")
        compilation = self.resolve_compilation(
            f"ST12F-COMPILATION::{token}",
            decision_cutoff=decision_cutoff,
        )
        if compilation.input_lock_id != input_lock_id:
            raise ContractValidationError(
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                "resolved compilation belongs to another immutable lock",
            )
        return compilation.input_lock

    def resolve_expected_slot(
        self,
        compilation_id: str,
        lane: str,
        expected_result_contract_id: str,
        *,
        decision_cutoff: datetime,
    ) -> ReplayPaperExpectedSlotV1:
        self.resolve_compilation(
            compilation_id,
            decision_cutoff=decision_cutoff,
        )
        try:
            return self._slots[(compilation_id, lane, expected_result_contract_id)]
        except KeyError as exc:
            raise ContractValidationError(
                ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                "result does not address one exact expected slot",
            ) from exc

    def resolve_evidence_expected_slot_v1(self, *, operation, math_id):
        """Select from the original compilation already in this publication closure."""
        from .context import _native_require
        from .persistence import _EvidenceLaneOperationV1, EvidenceAvailabilityHandleV1
        _native_require(type(self) is ReplayPaperCohortCompilerV1 and type(operation) is _EvidenceLaneOperationV1,
                        "LP03_SLOT_ORIGINAL_COMPILER_REQUIRED")
        registration, attempt = operation.attempt.registration, operation.attempt
        original = registration.binding_original
        _native_require(original is not None and self is original[0] and registration.compiler is self
                        and registration.compilation is original[2] and registration.binding_spines is original[3]
                        and type(math_id) is str and math_id == operation.exchange[1].math_id
                        and math_id in attempt.payload.component_closure
                        and operation.publication_readback_original is not None, "LP03_SLOT_ORIGINAL_BINDING_REQUIRED")
        compilation = original[2]
        _native_require(deterministic_json(compilation) == original[5], "LP03_SLOT_ORIGINAL_COMPILATION_CHANGED")
        # Original exact CONTROL compilation readback occurred in availability
        # resolution. This pure selection neither scans nor reacquires it.
        index = compilation.cohort_template_ids.index(math_id)
        contracts = (compilation.expected_replay_result_contract_ids if attempt.request.lane.value == "REPLAY"
                     else compilation.expected_paper_result_contract_ids)
        result = ReplayPaperExpectedSlotV1(compilation.compilation_id, compilation.input_lock_id,
            attempt.request.lane.value, math_id, contracts[index])
        EvidenceAvailabilityHandleV1._require_current_v1(operation.availability, operation=operation,
            purpose="EVIDENCE_LANE_REGISTRATION_V1", current_grant=attempt.handle, clock=operation.issuer.clock)
        _native_require(registration.binding_original is original and registration.compilation is compilation,
                        "LP03_SLOT_ORIGINAL_BINDING_CHANGED")
        return result

    def _receipt_spine(
        self,
        *,
        request: CompileReplayPaperCohortRequestV1,
        receipt_class: ST12FReceiptClassV1,
        contract: object,
        contract_id: str,
        terminal_state: str,
        input_lock: ImmutableReplayPaperInputLockV1,
    ) -> EconomicReceiptEventSpineV1:
        record_id = f"ST12F-RECEIPT::{contract_id}::{receipt_class.value}"
        payload = ST12FEvidenceControlReceiptRecordV1(
            control_receipt_id=record_id,
            receipt_class=receipt_class,
            operation_id="ST10-OP::13",
            request_id=request.request_id,
            idempotency_key=request.idempotency_key,
            contract_type=type(contract).__name__,
            contract_id=contract_id,
            contract_version=getattr(contract, "contract_version"),
            input_lock_id_or_explicit_absence=input_lock.input_lock_id,
            parent_version_ref_or_explicit_absence="EXPLICIT_ABSENCE",
            canonical_contract_json=deterministic_json(contract),
            source_record_refs=(),
            parameter_value_refs=input_lock.parameter_value_refs,
            source_epoch_refs=_source_epoch_refs(input_lock.source_epochs),
            typed_reason_codes=(),
            terminal_state=terminal_state,
            fixture_only_not_evidence=False,
        )
        return EconomicReceiptEventSpineV1(
            record_id=record_id,
            record_type=EconomicRecordTypeV1.ST12F_EVIDENCE_CONTROL,
            schema_version="QTT_ST12F_EVIDENCE_CONTROL_RECEIPT_SPINE_V1",
            semantic_owner="ComputationEvidenceServiceV1",
            implementation_owner="ReplayPaperCohortCompilerV1",
            context_ref=request.context.context_id,
            effective_at=input_lock.decision_time,
            recorded_at=input_lock.created_at,
            causation_id=input_lock.causation_id,
            correlation_id=input_lock.correlation_id,
            traceparent=request.traceparent,
            tracestate=request.tracestate,
            sequence=0,
            aggregate_id=contract_id,
            aggregate_version=1,
            authority_class="CONTRACT_MATERIALIZATION_ONLY",
            typed_payload=payload,
            no_effect_flags=NO_EFFECTS_V1,
        )

    def _materialize_contract_v1(self, request: CompileReplayPaperCohortRequestV1) -> ReplayPaperCohortCompilationRecordV1:
        """Sole unchanged 52-template/104-slot materialization; no persistence."""
        if type(request) is not CompileReplayPaperCohortRequestV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "OP13 delegate requires the exact public request type",
            )
        if request.template_ids != ST12F_TEMPLATE_IDS_V1 or request.requested_lanes != ("REPLAY", "PAPER"):
            raise ContractValidationError(
                ReasonCode.ST12F_TEMPLATE_ROSTER_MISMATCH,
                "OP13 requires exact ordered templates and both ordered lanes",
            )
        token = validated_st12f_identity_token_v1(request.idempotency_key)
        compilation_id = f"ST12F-COMPILATION::{token}"
        input_lock = build_immutable_replay_paper_input_lock_v1(
            identity_token=token,
            asserted_input_lock_id=request.input_lock_id,
            canonical_snapshot=self._canonical_snapshot,
        )
        return ReplayPaperCohortCompilationRecordV1(
            compilation_id=compilation_id,
            schema_version=COHORT_COMPILATION_SCHEMA_VERSION_V1,
            contract_version=COHORT_COMPILATION_CONTRACT_VERSION_V1,
            input_lock_id=input_lock.input_lock_id,
            cohort_template_ids=ST12F_TEMPLATE_IDS_V1,
            expected_replay_result_contract_ids=ST12F_REPLAY_RESULT_CONTRACT_IDS_V1,
            expected_paper_result_contract_ids=ST12F_PAPER_RESULT_CONTRACT_IDS_V1,
            input_lock=input_lock,
            created_at=input_lock.created_at,
        )

    def compile_registered_experiment_v1(self, request, *, registration_resolver):
        """Bind the original preregistration using the sole existing compiler."""
        from contextlib import ExitStack
        from ...agents.pr169_agent_orch1_resolvers import EvidenceIssuerContextV1, _EvidenceIssuerStateV1
        from .context import _native_require, _native_utc_nanoseconds, ComputationContextKeyV1
        from .input_lock import _require_original_input_assembly_outcome_v1
        from .latency_policy import _EvidenceLocalClockV1
        from .persistence import _EvidenceRegistrationOperationV1
        from .sqlite_reference import SQLiteReferenceAdapterV1

        _native_require(type(self) is ReplayPaperCohortCompilerV1
                        and type(request) is EvidenceRegisteredCompilationRequestV1
                        and type(registration_resolver) is EvidenceIssuerContextV1,
                        "LP03_REGISTERED_COMPILATION_ORIGINAL_CONTEXT")
        state = registration_resolver._EvidenceIssuerContextV1__owner
        _native_require(type(state) is _EvidenceIssuerStateV1, "LP03_ISSUER_CONTEXT_NOT_ORIGINAL")
        EvidenceIssuerContextV1._identity_for_owner_v1(registration_resolver, state.service)
        ref = request.registration_ref.record_id
        _native_require(ref.endswith("::INPUT_ASSEMBLY::EXPERIMENT:1"), "LP03_ORIGINAL_REGISTRATION_REF_REQUIRED")
        key = ref.removesuffix("::INPUT_ASSEMBLY::EXPERIMENT:1")
        operation = state.registrations.get(key)
        _native_require(type(operation) is _EvidenceRegistrationOperationV1 and operation.issuer is state,
                        "LP03_ORIGINAL_REGISTRATION_REF_REQUIRED")
        with state.lock, ExitStack() as locks:
            _native_require(state.operation is None and self._persistence is state.control_store
                            and operation.commit_state == "COMMITTED_AND_READBACK" and operation.handle is not None
                            and operation.handle == request.registration_ref
                            and self._canonical_snapshot is operation.preparation.input_assembly_members[2],
                            "LP03_REGISTERED_COMPILATION_ORIGINAL_JOIN")
            state.operation = operation
            try:
                state._lock_original_source_custodies_v1(locks)
                wall, _mono, _cpu = _EvidenceRegistrationOperationV1._check_current_v1(operation)
                inner, preparation = request.compilation_request, operation.preparation
                envelope = operation.envelope_entry[3]
                first = preparation.input_assembly_members[1][0].reconstructed_canonical_events[0]
                _native_require(type(inner.context) is ComputationContextKeyV1
                                and inner.principal_id == self._canonical_snapshot.created_by
                                and inner.capability_bundle_id == envelope.envelope_ref
                                and inner.context.context_id == first["context_id"]
                                and inner.context.source_epoch_id == first["source_epoch_id"]
                                and inner.context.input_version == first["input_version"]
                                and inner.context.as_of == self._canonical_snapshot.decision_time
                                and inner.context.observed_at == self._canonical_snapshot.decision_time
                                and (inner.context.maximum_age.days * 86400 + inner.context.maximum_age.seconds) * 1_000_000_000
                                    + inner.context.maximum_age.microseconds * 1000
                                    == self._canonical_snapshot.latency_and_staleness_assumptions["ttl_ns"]
                                and operation.records[0].created_wall_ns // 1000 * 1000
                                    <= _native_utc_nanoseconds(inner.requested_at.isoformat()) <= wall,
                                "LP03_COMPILATION_REQUEST_ORIGINAL_SCOPE")
                if operation.compilation_request is None:
                    _native_require(not self._compilations and not self._locks and not self._slots,
                                    "LP03_COMPILER_HAS_UNBOUND_CACHED_CONTRACTS")
                    operation.compiler, operation.compilation_request = self, request
                    operation.binding_state = "ADMITTED"
                else:
                    _native_require(operation.compiler is self and operation.compilation_request == request
                                    and operation.binding_state == "COMMITTED_AND_READBACK",
                                    "LP03_COMPILATION_ALREADY_RESERVED_OR_UNRESOLVED")
                SQLiteReferenceAdapterV1._evidence_registration_readback_v1(state.control_store, operation)
                _require_original_input_assembly_outcome_v1(preparation, preparation.input_assembly_outcome)
                original_snapshot = preparation.input_assembly_members[2]
                _native_require(self._canonical_snapshot is original_snapshot, "LP03_COMPILER_ORIGINAL_SNAPSHOT_CHANGED")
                if operation.binding_state == "COMMITTED_AND_READBACK":
                    SQLiteReferenceAdapterV1._evidence_read_control_members_v1(state.control_store, operation, stage="BOUND_EXPERIMENT")
                else:
                    compilation = ReplayPaperCohortCompilerV1._materialize_contract_v1(self, inner)
                    _native_require(type(compilation) is ReplayPaperCohortCompilationRecordV1
                                    and self._canonical_snapshot is original_snapshot
                                    and all(getattr(compilation.input_lock, member.name) == getattr(original_snapshot, member.name)
                                            for member in fields(CanonicalReplayPaperInputSnapshotV1)),
                                    "LP03_COMPILER_ORIGINAL_SNAPSHOT_CHANGED")
                    spines = tuple(ReplayPaperCohortCompilerV1._receipt_spine(self, request=inner,
                        receipt_class=kind, contract=contract, contract_id=identity, terminal_state=terminal,
                        input_lock=compilation.input_lock) for kind, contract, identity, terminal in (
                            (ST12FReceiptClassV1.COHORT_COMPILATION, compilation, compilation.compilation_id, "COMPILED"),
                            (ST12FReceiptClassV1.INPUT_LOCK, compilation.input_lock, compilation.input_lock_id, "LOCKED_IMMUTABLE")))
                    operation.compilation, operation.binding_spines = compilation, spines
                    operation.binding_original = (self, request, compilation, spines,
                        deterministic_json(request), deterministic_json(compilation), tuple(deterministic_json(row) for row in spines))
                    SQLiteReferenceAdapterV1._evidence_bind_registered_compilation_v1(state.control_store, operation)
                _native_require(operation.binding_commit_observation is not None and operation.binding_readback_observation is not None,
                                "LP03_COMPILATION_BINDING_UNRESOLVED")
                candidate_compilations, candidate_locks, candidate_slots = ReplayPaperCohortCompilerV1._index_members_v1(
                    self, operation.compilation)
                _EvidenceRegistrationOperationV1._check_current_v1(operation)
                # Publish already constructed exact maps. Never dispatch an
                # update method on caller-replaceable cache attributes here.
                self._compilations, self._locks, self._slots = candidate_compilations, candidate_locks, candidate_slots
                return operation.compilation
            except BaseException:
                if operation.binding_state not in ("ROLLED_BACK", "ROLLBACK_UNPROVEN", "COMMIT_OR_OBSERVATION_UNRESOLVED"):
                    operation.binding_state = "BINDING_FAILED_REQUIRES_AUDIT"
                try:
                    _wall, mono, cpu = _EvidenceLocalClockV1.observe_v1(state.clock)
                    _native_require(_EvidenceRegistrationOperationV1._observe_accounting_v1(operation),
                                    "LP03_EXECUTION_ACCOUNTING_UNPROVEN")
                except BaseException:
                    operation.binding_state = "BINDING_CLOCK_CUSTODY_UNAVAILABLE"
                    raise
                raise
            finally:
                state.operation = None

    def compile(
        self, request: CompileReplayPaperCohortRequestV1
    ) -> ReplayPaperCohortCompilationRecordV1:
        initialize_st12f_parameter_registry_v1()
        compilation = ReplayPaperCohortCompilerV1._materialize_contract_v1(self, request)
        token = validated_st12f_identity_token_v1(request.idempotency_key)
        compilation_id = compilation.compilation_id
        input_lock = compilation.input_lock
        request_json = canonical_request_json_v1(request)
        claim = IdempotencyClaimReceiptV1(
            claim_id=f"ST12F-IDEMPOTENCY::{token}::OP13",
            idempotency_key=request.idempotency_key,
            identity_class="ST10-OP::13",
            canonical_request_json=request_json,
            claim_state=IdempotencyClaimStateV1.ACQUIRED,
            result_record_ref=None,
            created_at=request.requested_at,
            completed_at=None,
            failure_code=None,
        )
        transaction = self._persistence.begin_transaction()
        try:
            acquisition = self._persistence.acquire_idempotency_claim(transaction, claim)
            if acquisition.outcome is IdempotencyOutcomeV1.REPLAYED_SAME_PAYLOAD:
                transaction.rollback()
                return self.resolve_compilation(
                    compilation_id,
                    decision_cutoff=request.requested_at,
                )
            if acquisition.outcome is IdempotencyOutcomeV1.CONFLICT_DIFFERENT_PAYLOAD:
                raise IdempotencyContractError(
                    ReasonCode.IDEMPOTENCY_CONFLICT,
                    "OP13 idempotency key already binds different canonical input",
                )
            if acquisition.outcome is not IdempotencyOutcomeV1.ACQUIRED:
                raise IdempotencyContractError(
                    ReasonCode.IDEMPOTENCY_IN_PROGRESS,
                    "OP13 idempotency claim is not terminally available",
                )
            compilation_spine = self._receipt_spine(
                request=request,
                receipt_class=ST12FReceiptClassV1.COHORT_COMPILATION,
                contract=compilation,
                contract_id=compilation.compilation_id,
                terminal_state="COMPILED",
                input_lock=input_lock,
            )
            lock_spine = self._receipt_spine(
                request=request,
                receipt_class=ST12FReceiptClassV1.INPUT_LOCK,
                contract=input_lock,
                contract_id=input_lock.input_lock_id,
                terminal_state="LOCKED_IMMUTABLE",
                input_lock=input_lock,
            )
            self._persistence.insert_receipt_record(transaction, compilation_spine)
            self._persistence.insert_receipt_record(transaction, lock_spine)
            for before, after in (("UNSEEN", "ACQUIRED"), ("ACQUIRED", "COMPLETED")):
                version = 0 if before == "UNSEEN" else 1
                self._persistence.insert_state_transition(
                    transaction,
                    StateTransitionReceiptV1(
                        transition_id=f"{claim.claim_id}::{after}",
                        aggregate_id=claim.claim_id,
                        transition_family="IDEMPOTENCY_CLAIM_STATE_MACHINE_V1",
                        prior_state=before,
                        event_class=f"OP13_{after}",
                        candidate_state=after,
                        disposition=TransitionDispositionV1.ACCEPTED,
                        event_identity=request.request_id,
                        aggregate_version_before=version,
                        aggregate_version_after=version + 1,
                        effective_at=request.requested_at,
                        recorded_at=input_lock.created_at,
                        reason_code=ReasonCode.CENTRAL_ADMISSION_PASS.value,
                        reconciliation_required=False,
                    ),
                )
            self._persistence.bind_idempotency_result(
                transaction,
                acquisition.claim_ref,
                compilation_spine.record_id,
                input_lock.created_at,
            )
            transaction.commit()
        except BaseException:
            if transaction.is_active:
                transaction.rollback()
            raise
        self._index(compilation)
        return compilation

    @property
    def immutable_indexes(self) -> Mapping[str, Mapping[object, object]]:
        return MappingProxyType(
            {
                "compilations": MappingProxyType(self._compilations),
                "locks": MappingProxyType(self._locks),
                "slots": MappingProxyType(self._slots),
            }
        )
