"""Typed append-only receipt, event, and value-lineage contracts for Tranche C."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from .context import exact_decimal, parse_utc
from .errors import ContractValidationError, ReasonCode
from .models import (
    ComputationExecutionReceiptV1,
    ModeSnapshotCandidateProposalResultV1,
    NO_EFFECTS_V1,
    NoEffectFlagsV1,
    SnapshotCandidateStateV1,
)
from .serialization import deterministic_json, safe_json_loads


def _required(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{name} is required")


def _identifier_tuple(value: object, name: str, *, allow_empty: bool = True) -> None:
    if not isinstance(value, tuple) or any(not isinstance(item, str) or not item for item in value):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be a string tuple")
    if not allow_empty and not value:
        raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{name} must not be empty")
    if len(value) != len(set(value)):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be unique")


def _time(value: datetime | str, name: str) -> datetime:
    return parse_utc(value, field_name=name)


def _canonical_decimal_text(value: str, name: str) -> None:
    _required(value, name)
    if str(exact_decimal(value, field_name=name)) != value:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be canonical Decimal text")


def _require_declared_scale(value: str, scale: int, name: str) -> None:
    if isinstance(scale, bool) or not isinstance(scale, int) or scale < 0:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "scale must be nonnegative integer")
    if exact_decimal(value, field_name=name).as_tuple().exponent != -scale:
        raise ContractValidationError(
            ReasonCode.INVALID_CONTRACT,
            f"{name} precision does not match its declared scale",
        )


class EconomicRecordTypeV1(StrEnum):
    DURABLE_COMPUTATION_RECEIPT = "DURABLE_COMPUTATION_RECEIPT"
    ECONOMIC_EVENT = "ECONOMIC_EVENT"
    JOURNAL_TRANSACTION = "JOURNAL_TRANSACTION"
    JOURNAL_POSTING = "JOURNAL_POSTING"
    STATE_TRANSITION = "STATE_TRANSITION"
    IDEMPOTENCY_CLAIM = "IDEMPOTENCY_CLAIM"
    OUTBOX_INTENT = "OUTBOX_INTENT"
    REVERSAL = "REVERSAL"
    RECONCILIATION_BREAK = "RECONCILIATION_BREAK"
    ORDER_INTENT = "ORDER_INTENT"
    EXECUTION_CUSTODY = "EXECUTION_CUSTODY"
    MODE_SNAPSHOT_CONTROL = "MODE_SNAPSHOT_CONTROL"
    ST12F_EVIDENCE_CONTROL = "ST12F_EVIDENCE_CONTROL"


class ModeSnapshotControlClassV1(StrEnum):
    MODE_SNAPSHOT_EVALUATION = "MODE_SNAPSHOT_EVALUATION"
    SNAPSHOT_CANDIDATE_BUILD = "SNAPSHOT_CANDIDATE_BUILD"
    SNAPSHOT_CANDIDATE_VALIDATION = "SNAPSHOT_CANDIDATE_VALIDATION"
    SNAPSHOT_PINNING = "SNAPSHOT_PINNING"
    SNAPSHOT_ROLLBACK_PROPOSAL = "SNAPSHOT_ROLLBACK_PROPOSAL"
    SNAPSHOT_STALE_OR_RETIREMENT = "SNAPSHOT_STALE_OR_RETIREMENT"
    LATENCY_MEASUREMENT = "LATENCY_MEASUREMENT"


class ST12FReceiptClassV1(StrEnum):
    COHORT_COMPILATION = "COHORT_COMPILATION"
    INPUT_LOCK = "INPUT_LOCK"
    REPLAY_REGISTRATION = "REPLAY_REGISTRATION"
    PAPER_REGISTRATION = "PAPER_REGISTRATION"
    DIVERGENCE_ASSESSMENT = "DIVERGENCE_ASSESSMENT"
    MODEL_RISK_ASSESSMENT = "MODEL_RISK_ASSESSMENT"
    QUANTUM_TRACE_VALIDATION = "QUANTUM_TRACE_VALIDATION"
    LLM_ANNOTATION_VALIDATION = "LLM_ANNOTATION_VALIDATION"
    EVIDENCE_BUNDLE_VERSION = "EVIDENCE_BUNDLE_VERSION"
    INDEPENDENT_REVIEW_VERSION = "INDEPENDENT_REVIEW_VERSION"
    D_EVIDENCE_REFERENCE = "D_EVIDENCE_REFERENCE"
    G_HANDOFF_REFERENCE = "G_HANDOFF_REFERENCE"


ST12F_RECEIPT_CONTRACT_ALLOWLIST: Mapping[
    ST12FReceiptClassV1, tuple[str, str]
] = MappingProxyType(
    {
        ST12FReceiptClassV1.COHORT_COMPILATION: (
            "cohort_compiler",
            "ReplayPaperCohortCompilationRecordV1",
        ),
        ST12FReceiptClassV1.INPUT_LOCK: (
            "input_lock",
            "ImmutableReplayPaperInputLockV1",
        ),
        ST12FReceiptClassV1.REPLAY_REGISTRATION: (
            "evidence",
            "ReplayResultContractV1",
        ),
        ST12FReceiptClassV1.PAPER_REGISTRATION: (
            "evidence",
            "PaperResultContractV1",
        ),
        ST12FReceiptClassV1.DIVERGENCE_ASSESSMENT: (
            "evidence",
            "DivergenceAssessmentV1",
        ),
        ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT: (
            "model_risk",
            "ModelRiskEvidenceAssessmentV1",
        ),
        ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION: (
            "quantum_benchmark",
            "QuantumTraceValidationReceiptV1",
        ),
        ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION: (
            "llm_gateway",
            "DeterministicEvidenceAnnotationContractV1",
        ),
        ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION: (
            "evidence",
            "ComputationEvidenceBundleV1",
        ),
        ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION: (
            "evidence",
            "IndependentReviewRecordV1",
        ),
        ST12FReceiptClassV1.D_EVIDENCE_REFERENCE: (
            "models",
            "ST12FEvidenceReferenceV1",
        ),
        ST12FReceiptClassV1.G_HANDOFF_REFERENCE: (
            "evidence",
            "FToGHandoffReferencesV1",
        ),
    }
)


@dataclass(frozen=True, slots=True)
class ST12FEvidenceControlReceiptRecordV1:
    control_receipt_id: str
    receipt_class: ST12FReceiptClassV1
    operation_id: str
    request_id: str
    idempotency_key: str
    contract_type: str
    contract_id: str
    contract_version: str
    input_lock_id_or_explicit_absence: str
    parent_version_ref_or_explicit_absence: str
    canonical_contract_json: str
    source_record_refs: tuple[str, ...]
    parameter_value_refs: tuple[str, ...]
    source_epoch_refs: tuple[str, ...]
    typed_reason_codes: tuple[ReasonCode, ...]
    terminal_state: str
    fixture_only_not_evidence: bool
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        for name in (
            "control_receipt_id",
            "operation_id",
            "request_id",
            "idempotency_key",
            "contract_type",
            "contract_id",
            "contract_version",
            "input_lock_id_or_explicit_absence",
            "parent_version_ref_or_explicit_absence",
            "canonical_contract_json",
            "terminal_state",
        ):
            _required(getattr(self, name), name)
        if type(self.receipt_class) is not ST12FReceiptClassV1:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "ST12-F receipt_class must be the exact allowlisted enum",
            )
        expected_module, expected_type = ST12F_RECEIPT_CONTRACT_ALLOWLIST[
            self.receipt_class
        ]
        if self.contract_type != expected_type:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "ST12-F receipt class and canonical contract type differ",
            )
        for name in (
            "source_record_refs",
            "parameter_value_refs",
            "source_epoch_refs",
        ):
            _identifier_tuple(getattr(self, name), name)
        if (
            not isinstance(self.typed_reason_codes, tuple)
            or any(type(code) is not ReasonCode for code in self.typed_reason_codes)
            or len(self.typed_reason_codes) != len(set(self.typed_reason_codes))
        ):
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "typed_reason_codes must be a unique ReasonCode tuple",
            )
        if type(self.fixture_only_not_evidence) is not bool:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "fixture_only_not_evidence must be an exact boolean",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1:
            raise ContractValidationError(
                ReasonCode.RUNTIME_EFFECT_FORBIDDEN,
                "ST12-F receipts require the shared no-effect custody type",
            )
        payload = safe_json_loads(self.canonical_contract_json)
        if not isinstance(payload, dict) or deterministic_json(payload) != self.canonical_contract_json:
            raise ContractValidationError(
                ReasonCode.SERIALIZATION_UNSAFE,
                "canonical_contract_json must be exact deterministic object text",
            )
        if not expected_module or not expected_type:
            raise ContractValidationError(
                ReasonCode.INVALID_CONTRACT,
                "ST12-F receipt allowlist entry is incomplete",
            )

    def reconstruct(self, expected_type: type[object]) -> object:
        expected_module, expected_name = ST12F_RECEIPT_CONTRACT_ALLOWLIST[
            self.receipt_class
        ]
        if (
            expected_type.__name__ != expected_name
            or expected_type.__module__.rsplit(".", 1)[-1] != expected_module
            or self.contract_type != expected_name
        ):
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "receipt reconstruction type is not the exact allowlisted class",
            )
        constructor = getattr(expected_type, "from_canonical_mapping", None)
        if not callable(constructor):
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "allowlisted contract lacks canonical reconstruction authority",
            )
        payload = safe_json_loads(self.canonical_contract_json)
        value = constructor(payload)
        if type(value) is not expected_type or deterministic_json(value) != self.canonical_contract_json:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "canonical contract reconstruction did not round-trip exactly",
            )
        self._validate_metadata(value)
        return value

    def _validate_metadata(self, value: object) -> None:
        """Bind receipt metadata to the reconstructed immutable contract."""

        identifier_fields = {
            ST12FReceiptClassV1.COHORT_COMPILATION: "compilation_id",
            ST12FReceiptClassV1.INPUT_LOCK: "input_lock_id",
            ST12FReceiptClassV1.REPLAY_REGISTRATION: "result_id",
            ST12FReceiptClassV1.PAPER_REGISTRATION: "result_id",
            ST12FReceiptClassV1.DIVERGENCE_ASSESSMENT: "assessment_id",
            ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT: "assessment_id",
            ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION: "receipt_id",
            ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION: "annotation_id",
            ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION: "evidence_bundle_version",
            ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION: "review_id",
            ST12FReceiptClassV1.D_EVIDENCE_REFERENCE: "reference_id",
            ST12FReceiptClassV1.G_HANDOFF_REFERENCE: "handoff_id",
        }
        contract_id = getattr(value, identifier_fields[self.receipt_class], None)
        contract_version = getattr(value, "contract_version", None)
        input_lock_id = getattr(value, "input_lock_id", None)
        if self.receipt_class is ST12FReceiptClassV1.COHORT_COMPILATION:
            input_lock_id = getattr(getattr(value, "input_lock", None), "input_lock_id", None)
        if (
            contract_id != self.contract_id
            or contract_version != self.contract_version
            or input_lock_id != self.input_lock_id_or_explicit_absence
        ):
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "ST12-F receipt identity, version, or input-lock metadata differs from its contract",
            )

        if self.receipt_class is not ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION:
            parent = "EXPLICIT_ABSENCE"
            if self.receipt_class is ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION:
                parent = getattr(value, "prior_bundle_ref", None)
            elif self.receipt_class is ST12FReceiptClassV1.D_EVIDENCE_REFERENCE:
                parent = getattr(value, "evidence_ref", None)
            elif self.receipt_class is ST12FReceiptClassV1.G_HANDOFF_REFERENCE:
                parent = getattr(value, "evidence_bundle_ref", None)
            if parent != self.parent_version_ref_or_explicit_absence:
                raise ContractValidationError(
                    ReasonCode.SCHEMA_MISMATCH,
                    "ST12-F receipt parent-version metadata differs from its contract",
                )

        expected_sources: tuple[str, ...] | None = None
        if self.receipt_class in {
            ST12FReceiptClassV1.COHORT_COMPILATION,
            ST12FReceiptClassV1.INPUT_LOCK,
        }:
            expected_sources = ()
        elif self.receipt_class in {
            ST12FReceiptClassV1.REPLAY_REGISTRATION,
            ST12FReceiptClassV1.PAPER_REGISTRATION,
        }:
            expected_sources = (getattr(value, "run_reference"),)
        elif self.receipt_class is ST12FReceiptClassV1.DIVERGENCE_ASSESSMENT:
            expected_sources = (
                getattr(value, "replay_result_ref"),
                getattr(value, "paper_result_ref"),
            )
        elif self.receipt_class is ST12FReceiptClassV1.MODEL_RISK_ASSESSMENT:
            expected_sources = tuple(getattr(value, "receipt_refs"))
        elif self.receipt_class is ST12FReceiptClassV1.QUANTUM_TRACE_VALIDATION:
            expected_sources = (
                getattr(value, "trace_id"),
                getattr(value, "strongest_classical_receipt_ref"),
                getattr(value, "no_trade_receipt_ref"),
            )
        elif self.receipt_class is ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION:
            expected_sources = tuple(
                dict.fromkeys(
                    (
                        *getattr(value, "evidence_bundle_refs"),
                        *(row.evidence_receipt_ref for row in getattr(value, "canonical_numeric_evidence")),
                        *getattr(value, "deterministic_numeric_recheck_receipt_refs"),
                    )
                )
            )
        elif self.receipt_class is ST12FReceiptClassV1.EVIDENCE_BUNDLE_VERSION:
            expected_sources = tuple(getattr(value, "source_and_provenance_refs"))
        elif self.receipt_class is ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION:
            expected_sources = (
                getattr(value, "prior_bundle_ref"),
                getattr(value, "authority_receipt_ref"),
            )
        elif self.receipt_class is ST12FReceiptClassV1.D_EVIDENCE_REFERENCE:
            expected_sources = (getattr(value, "evidence_ref"),)
        elif self.receipt_class is ST12FReceiptClassV1.G_HANDOFF_REFERENCE:
            expected_sources = tuple(
                dict.fromkeys(
                    (
                        getattr(value, "evidence_bundle_ref"),
                        *getattr(value, "no_trade_blocker_refs"),
                        *getattr(value, "champion_challenger_evidence_refs"),
                        *getattr(value, "portfolio_utility_refs"),
                        getattr(value, "quantum_classical_comparison_receipt_ref"),
                    )
                )
            )
        if expected_sources != self.source_record_refs:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "ST12-F receipt source-record metadata differs from its contract",
            )

        expected_epochs: tuple[str, ...] | None = None
        source_epochs = getattr(value, "source_epochs", None)
        if isinstance(source_epochs, Mapping):
            expected_epochs = tuple(
                f"{key}={source_epochs[key]}" for key in sorted(source_epochs)
            )
        if self.receipt_class is ST12FReceiptClassV1.COHORT_COMPILATION:
            source_epochs = getattr(getattr(value, "input_lock", None), "source_epochs", None)
            if isinstance(source_epochs, Mapping):
                expected_epochs = tuple(
                    f"{key}={source_epochs[key]}" for key in sorted(source_epochs)
                )
        for field_name in ("source_epoch_refs", "reviewed_source_epoch_refs"):
            if hasattr(value, field_name):
                expected_epochs = tuple(getattr(value, field_name))
        if expected_epochs is not None and expected_epochs != self.source_epoch_refs:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "ST12-F receipt source-epoch metadata differs from its contract",
            )

        expected_parameters = getattr(value, "parameter_value_refs", None)
        if self.receipt_class is ST12FReceiptClassV1.COHORT_COMPILATION:
            expected_parameters = getattr(getattr(value, "input_lock", None), "parameter_value_refs", None)
        if expected_parameters is not None and tuple(expected_parameters) != self.parameter_value_refs:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "ST12-F receipt parameter metadata differs from its contract",
            )

        terminal = {
            ST12FReceiptClassV1.COHORT_COMPILATION: "COMPILED",
            ST12FReceiptClassV1.INPUT_LOCK: "LOCKED_IMMUTABLE",
            ST12FReceiptClassV1.REPLAY_REGISTRATION: "REPLAY_REGISTERED",
            ST12FReceiptClassV1.PAPER_REGISTRATION: "PAPER_REGISTERED",
            ST12FReceiptClassV1.LLM_ANNOTATION_VALIDATION: "ANNOTATION_VALIDATED_NO_EFFECT",
        }.get(self.receipt_class, getattr(value, "terminal_state", None))
        if hasattr(terminal, "value"):
            terminal = terminal.value
        if self.receipt_class is ST12FReceiptClassV1.DIVERGENCE_ASSESSMENT:
            terminal = getattr(value, "terminal_state").value
        if self.receipt_class is ST12FReceiptClassV1.INDEPENDENT_REVIEW_VERSION:
            terminal = getattr(value, "decision").value
        reasons = getattr(value, "blocker_codes", getattr(value, "typed_blockers", ()))
        fixture = getattr(value, "fixture_only_not_evidence", False)
        contract_no_effects = getattr(value, "no_effect_flags", NO_EFFECTS_V1)
        if (
            terminal != self.terminal_state
            or tuple(reasons) != self.typed_reason_codes
            or contract_no_effects != self.no_effect_flags
            or self.no_effect_flags != NO_EFFECTS_V1
        ):
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "ST12-F receipt state, reason, or no-effect metadata differs from its contract",
            )
        if (
            self.receipt_class is ST12FReceiptClassV1.G_HANDOFF_REFERENCE
            and self.fixture_only_not_evidence is True
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_FIXTURE_NOT_EVIDENCE,
                "G-handoff control receipt cannot be marked fixture-only evidence",
            )
        if fixture != self.fixture_only_not_evidence:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "ST12-F receipt fixture metadata differs from its contract",
            )


ECONOMIC_RECORD_PAYLOAD_CLASS: Mapping[EconomicRecordTypeV1, tuple[str, str]] = MappingProxyType(
    {
        EconomicRecordTypeV1.DURABLE_COMPUTATION_RECEIPT: ("receipts", "DurableComputationExecutionReceiptRecordV1"),
        EconomicRecordTypeV1.ECONOMIC_EVENT: ("receipts", "EconomicEventRecordV1"),
        EconomicRecordTypeV1.JOURNAL_TRANSACTION: ("accounting", "JournalTransactionV1"),
        EconomicRecordTypeV1.JOURNAL_POSTING: ("accounting", "JournalPostingV1"),
        EconomicRecordTypeV1.STATE_TRANSITION: ("lifecycle", "StateTransitionReceiptV1"),
        EconomicRecordTypeV1.IDEMPOTENCY_CLAIM: ("idempotency", "IdempotencyClaimReceiptV1"),
        EconomicRecordTypeV1.OUTBOX_INTENT: ("outbox", "OutboxIntentRecordV1"),
        EconomicRecordTypeV1.REVERSAL: ("rollback", "ReversalReceiptV1"),
        EconomicRecordTypeV1.RECONCILIATION_BREAK: ("accounting", "ReconciliationBreakReceiptV1"),
        EconomicRecordTypeV1.ORDER_INTENT: ("lifecycle", "OrderIntentRecordV1"),
        EconomicRecordTypeV1.EXECUTION_CUSTODY: ("lifecycle", "ExecutionCustodyReceiptV1"),
        EconomicRecordTypeV1.MODE_SNAPSHOT_CONTROL: (
            "receipts",
            "ModeSnapshotControlReceiptRecordV1",
        ),
        EconomicRecordTypeV1.ST12F_EVIDENCE_CONTROL: (
            "receipts",
            "ST12FEvidenceControlReceiptRecordV1",
        ),
    }
)


@dataclass(frozen=True, slots=True)
class EconomicReceiptEventSpineV1:
    record_id: str
    record_type: EconomicRecordTypeV1
    schema_version: str
    semantic_owner: str
    implementation_owner: str
    context_ref: str
    effective_at: datetime | str
    recorded_at: datetime | str
    causation_id: str
    correlation_id: str
    traceparent: str
    tracestate: str
    sequence: int
    aggregate_id: str
    aggregate_version: int
    authority_class: str
    typed_payload: object
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        for name in (
            "record_id", "schema_version", "semantic_owner", "implementation_owner",
            "context_ref", "causation_id", "correlation_id", "traceparent", "tracestate",
            "aggregate_id", "authority_class",
        ):
            _required(getattr(self, name), name)
        if not isinstance(self.record_type, EconomicRecordTypeV1):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "record_type must be allowlisted")
        if self.causation_id == self.correlation_id:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "causation and correlation identities must remain distinct")
        if self.traceparent in {self.record_id, self.aggregate_id, self.causation_id, self.correlation_id}:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "trace context cannot be economic identity")
        for name in ("sequence", "aggregate_version"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractValidationError(ReasonCode.INVALID_CONTRACT, f"{name} must be nonnegative integer")
        expected_module, expected_class = ECONOMIC_RECORD_PAYLOAD_CLASS[self.record_type]
        if (
            type(self.typed_payload).__name__ != expected_class
            or type(self.typed_payload).__module__.rsplit(".", 1)[-1] != expected_module
        ):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "record discriminator/payload type mismatch")
        if not isinstance(self.no_effect_flags, NoEffectFlagsV1):
            raise ContractValidationError(ReasonCode.RUNTIME_EFFECT_FORBIDDEN, "typed no-effect flags are required")
        object.__setattr__(self, "effective_at", _time(self.effective_at, "effective_at"))
        object.__setattr__(self, "recorded_at", _time(self.recorded_at, "recorded_at"))


@dataclass(frozen=True, slots=True)
class DurableComputationExecutionReceiptRecordV1:
    record_id: str
    existing_receipt: ComputationExecutionReceiptV1
    execution_context_ref: str
    input_snapshot_ref: str
    input_value_lineage_refs: tuple[str, ...]
    dependency_receipt_refs: tuple[str, ...]
    started_at: datetime | str
    completed_at: datetime | str
    latency_ns: int
    output_unit: str
    output_basis: str
    accounting_class: str
    fallback_used: bool
    warning_codes: tuple[str, ...]
    failure_code: str | None
    consumer_ref: str
    mode_ref: str
    no_order_authority_flag: bool = True

    def __post_init__(self) -> None:
        for name in (
            "record_id", "execution_context_ref", "input_snapshot_ref", "output_unit",
            "output_basis", "accounting_class", "consumer_ref", "mode_ref",
        ):
            _required(getattr(self, name), name)
        if type(self.existing_receipt) is not ComputationExecutionReceiptV1:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "existing_receipt must be exact ComputationExecutionReceiptV1")
        _identifier_tuple(self.input_value_lineage_refs, "input_value_lineage_refs", allow_empty=False)
        _identifier_tuple(self.dependency_receipt_refs, "dependency_receipt_refs")
        _identifier_tuple(self.warning_codes, "warning_codes")
        if self.failure_code is not None:
            _required(self.failure_code, "failure_code")
        if isinstance(self.latency_ns, bool) or not isinstance(self.latency_ns, int) or self.latency_ns < 0:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "latency_ns must be nonnegative integer")
        if type(self.fallback_used) is not bool or self.no_order_authority_flag is not True:
            raise ContractValidationError(ReasonCode.RUNTIME_EFFECT_FORBIDDEN, "receipt must retain no-order authority")
        started = _time(self.started_at, "started_at")
        completed = _time(self.completed_at, "completed_at")
        if completed < started:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "completed_at precedes started_at")
        object.__setattr__(self, "started_at", started)
        object.__setattr__(self, "completed_at", completed)


@dataclass(frozen=True, slots=True)
class ModeSnapshotControlReceiptRecordV1:
    """One typed D control payload carried by the existing receipt spine."""

    control_receipt_id: str
    control_class: ModeSnapshotControlClassV1
    request_id: str
    task_id: str
    principal_id: str
    capability_decision_ref: str
    context_ref: str
    snapshot_candidate_ref_or_explicit_absence: str
    mode_snapshot_decision_ref: str
    transition_proposal_ref: str
    transition_id: str
    source_state: str
    destination_state: str
    target_candidate_version: str
    implementation_pin_refs: tuple[str, ...]
    parameter_value_refs: tuple[str, ...]
    source_epoch_refs: tuple[str, ...]
    predecessor_transition_receipt_refs: tuple[str, ...]
    state_before_refs: tuple[str, ...]
    state_after_refs: tuple[str, ...]
    typed_reason_codes: tuple[ReasonCode, ...]
    fallback_route: str
    owner_review_route: str
    latency_measurement_ref_or_explicit_absence: str
    owner_action_policy_ref: str
    no_mutation_flag: bool = True
    no_activation_flag: bool = True
    no_order_authority_flag: bool = True

    def __post_init__(self) -> None:
        for name in (
            "control_receipt_id",
            "request_id",
            "task_id",
            "principal_id",
            "capability_decision_ref",
            "context_ref",
            "snapshot_candidate_ref_or_explicit_absence",
            "mode_snapshot_decision_ref",
            "transition_proposal_ref",
            "transition_id",
            "source_state",
            "destination_state",
            "target_candidate_version",
            "fallback_route",
            "owner_review_route",
            "latency_measurement_ref_or_explicit_absence",
            "owner_action_policy_ref",
        ):
            _required(getattr(self, name), name)
        if type(self.control_class) is not ModeSnapshotControlClassV1:
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "control_class must use the single D control-class enum",
            )
        for name in ("implementation_pin_refs", "parameter_value_refs"):
            _identifier_tuple(getattr(self, name), name)
        _identifier_tuple(
            self.predecessor_transition_receipt_refs,
            "predecessor_transition_receipt_refs",
        )
        for name in ("source_epoch_refs", "state_before_refs", "state_after_refs"):
            _identifier_tuple(getattr(self, name), name, allow_empty=False)
        if (
            not isinstance(self.typed_reason_codes, tuple)
            or not self.typed_reason_codes
            or any(type(reason) is not ReasonCode for reason in self.typed_reason_codes)
            or len(self.typed_reason_codes) != len(set(self.typed_reason_codes))
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "typed_reason_codes must be a nonempty unique ReasonCode tuple",
            )
        if (
            self.no_mutation_flag is not True
            or self.no_activation_flag is not True
            or self.no_order_authority_flag is not True
        ):
            raise ContractValidationError(
                ReasonCode.ORDER_RELEASE_FORBIDDEN,
                "D control receipts must retain no-mutation/no-activation/no-order authority",
            )


def materialize_mode_snapshot_control_receipts(
    result: ModeSnapshotCandidateProposalResultV1,
    *,
    parameter_value_refs: tuple[str, ...],
    effective_at: datetime | str,
    recorded_at: datetime | str,
    traceparent: str,
    tracestate: str,
) -> tuple[EconomicReceiptEventSpineV1, ...]:
    """Materialize only the D stages that were actually executed."""

    if type(result) is not ModeSnapshotCandidateProposalResultV1:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "D receipt materialization requires an exact proposal result",
        )
    _identifier_tuple(parameter_value_refs, "parameter_value_refs")
    decision = result.mode_snapshot_decision
    trace = result.executed_transition_trace
    proposal = trace.final_proposal
    candidate = result.snapshot_candidate_or_explicit_absence
    candidate_ref = (
        candidate.snapshot_candidate_id
        if candidate is not None
        else proposal.target_candidate_ref
        if decision.snapshot_candidate_state is not SnapshotCandidateStateV1.ABSENT
        else "EXPLICIT_ABSENCE"
    )
    implementation_refs = tuple(
        f"{pin.math_spec_id}::{pin.implementation_id}"
        for pin in decision.implementation_pins
    )
    proposal_by_transition_id = {
        row.transition_id: row for row in trace.proposals
    }
    stage_proposals = [
        (ModeSnapshotControlClassV1.MODE_SNAPSHOT_EVALUATION, proposal),
    ]
    if "T08" in proposal_by_transition_id:
        stage_proposals.append(
            (
                ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_BUILD,
                proposal_by_transition_id["T08"],
            )
        )
    validation_proposal = next(
        (
            proposal_by_transition_id[transition_id]
            for transition_id in ("T09", "T10")
            if transition_id in proposal_by_transition_id
        ),
        None,
    )
    if validation_proposal is not None:
        stage_proposals.append(
            (
                ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_VALIDATION,
                validation_proposal,
            )
        )
    stage_proposal_tuple = tuple(stage_proposals)
    suffix_by_class = {
        ModeSnapshotControlClassV1.MODE_SNAPSHOT_EVALUATION: "EVALUATION",
        ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_BUILD: "BUILD",
        ModeSnapshotControlClassV1.SNAPSHOT_CANDIDATE_VALIDATION: "VALIDATION",
    }
    expected_refs = tuple(
        f"MODE-SNAPSHOT-CONTROL::{decision.request_id}::{suffix_by_class[row]}"
        for row, _proposal in stage_proposal_tuple
    )
    if result.control_receipt_refs and result.control_receipt_refs != expected_refs:
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            "D result/control receipt identities differ from executed stages",
        )
    rows: list[EconomicReceiptEventSpineV1] = []
    from .mode_snapshot_policy import TRANSITION_BY_ID

    for index, (receipt_ref, (control_class, stage_proposal)) in enumerate(
        zip(expected_refs, stage_proposal_tuple, strict=True)
    ):
        stage_rule = TRANSITION_BY_ID[stage_proposal.transition_id]
        payload = ModeSnapshotControlReceiptRecordV1(
            control_receipt_id=receipt_ref,
            control_class=control_class,
            request_id=decision.request_id,
            task_id=decision.task_id,
            principal_id=decision.principal_id,
            capability_decision_ref=decision.capability_decision_ref,
            context_ref=decision.context_ref,
            snapshot_candidate_ref_or_explicit_absence=candidate_ref,
            mode_snapshot_decision_ref=decision.decision_id,
            transition_proposal_ref=stage_proposal.proposal_id,
            transition_id=stage_proposal.transition_id,
            source_state=stage_proposal.source_state,
            destination_state=stage_proposal.destination_state,
            target_candidate_version=stage_proposal.target_candidate_version,
            implementation_pin_refs=implementation_refs,
            parameter_value_refs=parameter_value_refs,
            source_epoch_refs=decision.source_epoch_refs,
            predecessor_transition_receipt_refs=(
                stage_proposal.predecessor_transition_receipt_refs
            ),
            state_before_refs=tuple(
                dict.fromkeys(
                    (
                        stage_proposal.source_state,
                        stage_proposal.expected_owner_state_ref,
                        stage_proposal.source_candidate_ref_or_explicit_absence,
                        *stage_proposal.predecessor_transition_receipt_refs,
                    )
                )
            ),
            state_after_refs=tuple(
                dict.fromkeys(
                    (
                        stage_proposal.destination_state,
                        stage_proposal.target_candidate_ref,
                    )
                )
            ),
            typed_reason_codes=stage_proposal.typed_reason_codes,
            fallback_route=stage_rule.terminal_route,
            owner_review_route=decision.owner_review_route,
            latency_measurement_ref_or_explicit_absence=(
                decision.latency_measurement_ref_or_explicit_absence
            ),
            owner_action_policy_ref=decision.owner_action_policy_ref,
        )
        rows.append(
            EconomicReceiptEventSpineV1(
                record_id=receipt_ref,
                record_type=EconomicRecordTypeV1.MODE_SNAPSHOT_CONTROL,
                schema_version="ST12D_MODE_SNAPSHOT_CONTROL_V1",
                semantic_owner="QKUComputationControlPlaneV1",
                implementation_owner="QKUComputationControlPlaneV1",
                context_ref=decision.context_ref,
                effective_at=effective_at,
                recorded_at=recorded_at,
                causation_id=stage_proposal.causation_id,
                correlation_id=stage_proposal.correlation_id,
                traceparent=traceparent,
                tracestate=tracestate,
                sequence=index,
                aggregate_id=f"MODE-SNAPSHOT::{decision.request_id}",
                aggregate_version=index,
                authority_class="NO_EFFECT_MODE_SNAPSHOT_CONTROL_ONLY",
                typed_payload=payload,
            )
        )
    return tuple(rows)


@dataclass(frozen=True, slots=True)
class TypedEconomicAmountV1:
    amount_text: str
    currency_or_asset: str
    ledger_unit: str
    basis: str
    scale: int
    rounding_policy_ref: str

    def __post_init__(self) -> None:
        for name in ("amount_text", "currency_or_asset", "ledger_unit", "basis", "rounding_policy_ref"):
            _required(getattr(self, name), name)
        _canonical_decimal_text(self.amount_text, "amount_text")
        _require_declared_scale(self.amount_text, self.scale, "amount_text")


@dataclass(frozen=True, slots=True)
class EconomicEventRecordV1:
    economic_event_id: str
    event_class: str
    semantic_owner: str
    aggregate_id: str
    event_sequence: int
    effective_at: datetime | str
    recorded_at: datetime | str
    source_record_refs: tuple[str, ...]
    typed_amounts: tuple[TypedEconomicAmountV1, ...]
    lifecycle_state_before: str
    lifecycle_state_after: str
    authority_class: str

    def __post_init__(self) -> None:
        for name in ("economic_event_id", "event_class", "semantic_owner", "aggregate_id", "lifecycle_state_before", "lifecycle_state_after", "authority_class"):
            _required(getattr(self, name), name)
        if isinstance(self.event_sequence, bool) or not isinstance(self.event_sequence, int) or self.event_sequence < 0:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "event_sequence must be nonnegative integer")
        _identifier_tuple(self.source_record_refs, "source_record_refs")
        if not isinstance(self.typed_amounts, tuple) or any(not isinstance(row, TypedEconomicAmountV1) for row in self.typed_amounts):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "typed_amounts must contain typed amounts")
        if not self.source_record_refs:
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "economic event source lineage is required")
        if self.event_class not in {"NO_FILL", "PREFLIGHT_BLOCKED", "NO_ECONOMIC_EFFECT", "ORDER_INTENT"} and not self.typed_amounts:
            raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "economic-effect event requires at least one typed amount")
        if "PROVIDER" in self.authority_class.upper():
            raise ContractValidationError(ReasonCode.CAPABILITY_DENIED, "Tranche C cannot manufacture provider-origin economic truth")
        object.__setattr__(self, "effective_at", _time(self.effective_at, "effective_at"))
        object.__setattr__(self, "recorded_at", _time(self.recorded_at, "recorded_at"))


@dataclass(frozen=True, slots=True)
class ValueLineageNodeV1:
    value_node_id: str
    record_ref: str
    field_id: str
    value_text: str
    value_kind: str
    unit: str
    basis: str
    currency_or_asset: str
    scale: int
    effective_at: datetime | str
    recorded_at: datetime | str
    source_authority_class: str

    def __post_init__(self) -> None:
        for name in ("value_node_id", "record_ref", "field_id", "value_text", "value_kind", "unit", "basis", "currency_or_asset", "source_authority_class"):
            _required(getattr(self, name), name)
        _canonical_decimal_text(self.value_text, "value_text")
        _require_declared_scale(self.value_text, self.scale, "value_text")
        object.__setattr__(self, "effective_at", _time(self.effective_at, "effective_at"))
        object.__setattr__(self, "recorded_at", _time(self.recorded_at, "recorded_at"))


@dataclass(frozen=True, slots=True)
class ValueLineageEdgeV1:
    lineage_edge_id: str
    producer_record_id: str
    producer_field_id: str
    consumer_record_id: str
    consumer_field_id: str
    source_value_text: str
    target_value_text: str
    source_unit: str
    target_unit: str
    source_basis: str
    target_basis: str
    transformation_id: str
    materiality_class: str
    effective_at: datetime | str
    recorded_at: datetime | str
    causation_id: str
    correlation_id: str
    producer_node_id: str
    consumer_node_id: str
    conversion_policy_ref: str

    def __post_init__(self) -> None:
        for name in (
            "lineage_edge_id", "producer_record_id", "producer_field_id", "consumer_record_id",
            "consumer_field_id", "source_value_text", "target_value_text", "source_unit",
            "target_unit", "source_basis", "target_basis", "transformation_id",
            "materiality_class", "causation_id", "correlation_id",
        ):
            _required(getattr(self, name), name)
        _canonical_decimal_text(self.source_value_text, "source_value_text")
        _canonical_decimal_text(self.target_value_text, "target_value_text")
        for name in ("producer_node_id", "consumer_node_id", "conversion_policy_ref"):
            _required(getattr(self, name), name)
        if self.producer_record_id == self.consumer_record_id and self.producer_field_id == self.consumer_field_id:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "lineage self-cycle is forbidden")
        if self.causation_id == self.correlation_id:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "causation and correlation must be distinct")
        transformation_class = VALUE_TRANSFORMATION_REGISTRY_V1.get(self.transformation_id)
        if transformation_class is None:
            raise ContractValidationError(ReasonCode.UNKNOWN_IMPLEMENTATION, "lineage transformation is not centrally registered")
        if transformation_class == "IDENTITY":
            if (
                self.source_value_text != self.target_value_text
                or self.source_unit != self.target_unit
                or self.source_basis != self.target_basis
                or self.conversion_policy_ref != "IDENTITY_NO_CONVERSION"
            ):
                raise ContractValidationError(ReasonCode.UNIT_BASIS_MISMATCH, "identity lineage cannot convert or mutate a value")
        elif transformation_class == "UNIT_CONVERSION" and (
            self.source_unit == self.target_unit or self.source_basis != self.target_basis
        ):
            raise ContractValidationError(ReasonCode.UNIT_BASIS_MISMATCH, "unit conversion lineage must change only the declared unit")
        elif transformation_class == "BASIS_CONVERSION" and (
            self.source_basis == self.target_basis or self.source_unit != self.target_unit
        ):
            raise ContractValidationError(ReasonCode.UNIT_BASIS_MISMATCH, "basis conversion lineage must change only the declared basis")
        object.__setattr__(self, "effective_at", _time(self.effective_at, "effective_at"))
        object.__setattr__(self, "recorded_at", _time(self.recorded_at, "recorded_at"))


@dataclass(frozen=True, slots=True)
class CausalLineageV1:
    causation_id: str
    correlation_id: str
    traceparent: str
    tracestate: str
    linked_record_refs: tuple[str, ...]
    relationship_classes: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("causation_id", "correlation_id", "traceparent", "tracestate"):
            _required(getattr(self, name), name)
        if self.causation_id == self.correlation_id or self.traceparent in {self.causation_id, self.correlation_id}:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "trace/correlation/causation identities must remain distinct")
        _identifier_tuple(self.linked_record_refs, "linked_record_refs", allow_empty=False)
        _identifier_tuple(self.relationship_classes, "relationship_classes", allow_empty=False)


@dataclass(frozen=True, slots=True)
class BitemporalLineageV1:
    record_id: str
    effective_at: datetime | str
    recorded_at: datetime | str
    supersedes_ref: str | None = None
    correction_ref: str | None = None
    source_revision_ref: str | None = None

    def __post_init__(self) -> None:
        _required(self.record_id, "record_id")
        for name in ("supersedes_ref", "correction_ref", "source_revision_ref"):
            value = getattr(self, name)
            if value is not None:
                _required(value, name)
        object.__setattr__(self, "effective_at", _time(self.effective_at, "effective_at"))
        object.__setattr__(self, "recorded_at", _time(self.recorded_at, "recorded_at"))


@dataclass(frozen=True, slots=True)
class LineageReconstructionV1:
    reconstruction_id: str
    effective_cutoff: datetime | str
    recorded_cutoff: datetime | str
    aggregate_scope: tuple[str, ...]
    included_record_refs: tuple[str, ...]
    excluded_late_record_refs: tuple[str, ...]
    projection_version: str

    def __post_init__(self) -> None:
        _required(self.reconstruction_id, "reconstruction_id")
        _required(self.projection_version, "projection_version")
        _identifier_tuple(self.aggregate_scope, "aggregate_scope", allow_empty=False)
        _identifier_tuple(self.included_record_refs, "included_record_refs")
        _identifier_tuple(self.excluded_late_record_refs, "excluded_late_record_refs")
        if set(self.included_record_refs) & set(self.excluded_late_record_refs):
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "a record cannot be included and excluded")
        object.__setattr__(self, "effective_cutoff", _time(self.effective_cutoff, "effective_cutoff"))
        object.__setattr__(self, "recorded_cutoff", _time(self.recorded_cutoff, "recorded_cutoff"))


def validate_lineage_acyclic_v1(edges: tuple[ValueLineageEdgeV1, ...]) -> None:
    """Reject a cyclic producer-to-consumer value graph deterministically."""

    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        producer = edge.producer_node_id
        consumer = edge.consumer_node_id
        adjacency.setdefault(producer, set()).add(consumer)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, "value-lineage graph is cyclic")
        if node in visited:
            return
        visiting.add(node)
        for child in sorted(adjacency.get(node, ())):
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(adjacency):
        visit(node)


VALUE_TRANSFORMATION_REGISTRY_V1: Mapping[str, str] = MappingProxyType(
    {
        "IDENTITY": "IDENTITY",
        "EXPLICIT_UNIT_CONVERSION": "UNIT_CONVERSION",
        "EXPLICIT_BASIS_CONVERSION": "BASIS_CONVERSION",
        "QUANTIZATION": "QUANTIZATION",
        **{f"MATH-{number}": "REGISTERED_FORMULA" for number in range(26, 39)},
    }
)
