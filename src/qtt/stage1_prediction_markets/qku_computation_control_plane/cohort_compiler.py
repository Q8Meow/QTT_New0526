"""OP13 contract compiler: one parent lock, 52 templates, and 104 slots."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from types import MappingProxyType
from typing import Mapping

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
        self._compilations[compilation.compilation_id] = compilation
        self._locks[compilation.input_lock_id] = compilation.input_lock
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
                self._slots[(compilation.compilation_id, lane, contract_id)] = slot

    def _load_compilation_receipt(
        self, compilation_id: str
    ) -> ReplayPaperCohortCompilationRecordV1:
        receipt_ref = f"ST12F-RECEIPT::{compilation_id}::COHORT_COMPILATION"
        spine = self._persistence.get_record(receipt_ref)
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
        self, compilation_id: str
    ) -> ReplayPaperCohortCompilationRecordV1:
        compilation = self._compilations.get(compilation_id)
        return compilation if compilation is not None else self._load_compilation_receipt(compilation_id)

    def resolve_input_lock(self, input_lock_id: str) -> ImmutableReplayPaperInputLockV1:
        lock = self._locks.get(input_lock_id)
        if lock is not None:
            return lock
        token = input_lock_id.removeprefix("ST12F-LOCK::")
        compilation = self.resolve_compilation(f"ST12F-COMPILATION::{token}")
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
    ) -> ReplayPaperExpectedSlotV1:
        self.resolve_compilation(compilation_id)
        try:
            return self._slots[(compilation_id, lane, expected_result_contract_id)]
        except KeyError as exc:
            raise ContractValidationError(
                ReasonCode.ST12F_RESULT_SLOT_CONFLICT,
                "result does not address one exact expected slot",
            ) from exc

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

    def compile(
        self, request: CompileReplayPaperCohortRequestV1
    ) -> ReplayPaperCohortCompilationRecordV1:
        initialize_st12f_parameter_registry_v1()
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
        compilation = ReplayPaperCohortCompilationRecordV1(
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
                return self.resolve_compilation(compilation_id)
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
