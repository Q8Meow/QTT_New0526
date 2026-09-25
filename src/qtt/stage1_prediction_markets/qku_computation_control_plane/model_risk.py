"""Deterministic ST12-F model-risk adjudication with permanent NO_TRADE."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from decimal import Decimal, DecimalException, Inexact, localcontext
from enum import StrEnum
from typing import Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ProbabilityProducerScopeV1, PreparedProbabilityPredictionV1, ComputationExecutionContextV1
    from .input_resolver import ProbabilityOutcomeJoinV1
    from .persistence import ProbabilityProducerReadSnapshotV1

from .context import decimal_context_v1, exact_decimal, parse_utc
from .errors import ContractValidationError, NumericDomainError, ReasonCode
from .serialization import deterministic_json


MODEL_RISK_CONTROL_IDS_V1 = tuple(
    f"ST12-CLOSURE::ST11-MODEL-RISK::{number:03d}" for number in range(9, 21)
)
NO_TRADE_CONDITION_IDS_V1 = (
    "NEGATIVE_OR_ZERO_EXECUTION_ADJUSTED_LCB",
    "MISSING_OR_STALE_REQUIRED_EVIDENCE",
    "REPLAY_OR_PAPER_LANE_MISSING",
    "LOCK_OR_SCOPE_CONFLICT",
    "UNCERTAINTY_OR_MODEL_RISK_DOMINATES_EDGE",
    "CAPACITY_OR_LIQUIDITY_HARD_VETO",
    "STRONGEST_CLASSICAL_OR_NO_TRADE_DOMINATES",
    "INDEPENDENT_REVIEW_NOT_CLOSED",
)


_PROBABILITY_NATIVE_BINDING_GROUPS_V1 = (
    ("FIVAB::MATH-02::calibrated_model_probability", "FIVAB::MATH-02::calibration_state"),
    ("FIVAB::MATH-02::calibrated_model_probability", "FIVAB::MATH-02::calibration_state",
     "FIVAB::MATH-06::p_win", "FIVAB::MATH-06::p_void"),
)


@dataclass(frozen=True, slots=True)
class ProbabilityNativeUseRequestV1:
    producer_scope: ProbabilityProducerScopeV1
    prepared_prediction: PreparedProbabilityPredictionV1
    execution_context: ComputationExecutionContextV1
    query_key: tuple[str, tuple[str, ...]]
    binding_ids: tuple[str, ...]
    outcome_join: ProbabilityOutcomeJoinV1 | None
    selected_use_decision_ref: str
    effective_cutoff_ns: int
    recorded_cutoff_ns: int

    def __post_init__(self) -> None:
        from .models import (ProbabilityProducerScopeV1, PreparedProbabilityPredictionV1, ComputationExecutionContextV1,
                             _probability_require_v1, _probability_text_v1, _probability_ns_v1)
        need = _probability_require_v1
        need(type(self.producer_scope) is ProbabilityProducerScopeV1 and
             type(self.prepared_prediction) is PreparedProbabilityPredictionV1 and
             type(self.execution_context) is ComputationExecutionContextV1, "PROBABILITY_NATIVE_USE_TYPES")
        need(type(self.query_key) is tuple and self.query_key in self.prepared_prediction.request_keys,
             "PROBABILITY_NATIVE_QUERY")
        need(type(self.binding_ids) is tuple and self.binding_ids in _PROBABILITY_NATIVE_BINDING_GROUPS_V1,
             "PROBABILITY_NATIVE_BINDINGS")
        if self.binding_ids == _PROBABILITY_NATIVE_BINDING_GROUPS_V1[0]:
            need(self.outcome_join is None, "PROBABILITY_OUTCOME_NOT_SELECTED")
        else:
            from .input_resolver import ProbabilityOutcomeJoinV1
            need(type(self.outcome_join) is ProbabilityOutcomeJoinV1 and self.outcome_join.query_key == self.query_key and
                 self.outcome_join.context_identity == self.execution_context.execution_identity_tuple, "PROBABILITY_OUTCOME_JOIN")
        _probability_text_v1(self.selected_use_decision_ref)
        _probability_ns_v1(self.effective_cutoff_ns); _probability_ns_v1(self.recorded_cutoff_ns)
        need(self.prepared_prediction.generation == self.producer_scope.generation and
             self.prepared_prediction.input_lock_ref == self.producer_scope.input_lock_ref, "PROBABILITY_NATIVE_SCOPE")


@dataclass(frozen=True, slots=True)
class ProbabilityNativeUseAdmissionV1:
    request: ProbabilityNativeUseRequestV1
    accepted_use_decision_ref: str
    accepted_use_policy_ref: str
    accepted_transition_ref: str
    available_ns: int
    valid_until_ns: int
    dependency_refs: tuple[str, ...]
    policy_ref: str
    policy_epoch: int
    registry_version: str
    process_ref: str
    source_generation: int
    invalidation_cut_ref: str

    def __post_init__(self) -> None:
        from .models import (_probability_require_v1, _probability_text_v1, _probability_int_v1,
                             _probability_ns_v1, _probability_refs_v1)
        need = _probability_require_v1
        need(type(self.request) is ProbabilityNativeUseRequestV1, "PROBABILITY_NATIVE_USE_REQUEST")
        for name in ("accepted_use_decision_ref", "accepted_use_policy_ref", "accepted_transition_ref", "policy_ref",
                     "registry_version", "process_ref", "invalidation_cut_ref"):
            _probability_text_v1(getattr(self, name))
        _probability_ns_v1(self.available_ns); _probability_ns_v1(self.valid_until_ns)
        _probability_int_v1(self.policy_epoch); _probability_int_v1(self.source_generation)
        _probability_refs_v1(self.dependency_refs, nonempty=True)
        need(self.accepted_use_decision_ref == self.request.selected_use_decision_ref and
             self.accepted_use_policy_ref != self.request.producer_scope.policy_ref and
             self.source_generation == self.request.prepared_prediction.generation,
             "PROBABILITY_NATIVE_USE_BINDING")
        need(self.available_ns < self.valid_until_ns <= self.request.prepared_prediction.valid_until_ns,
             "PROBABILITY_NATIVE_USE_LIFETIME")
        need({self.accepted_use_decision_ref, self.accepted_use_policy_ref, self.accepted_transition_ref,
              self.request.producer_scope.policy_ref, *self.request.prepared_prediction.dependency_refs}.issubset(self.dependency_refs),
             "PROBABILITY_NATIVE_USE_DEPENDENCIES")


def _refs(value: object, name: str, *, required: bool = False) -> tuple[str, ...]:
    if (
        not isinstance(value, tuple)
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
        or (required and not value)
    ):
        raise ContractValidationError(
            ReasonCode.CONTRACT_OR_TYPE_INVALID,
            f"{name} must be a unique typed reference tuple",
        )
    return value


class ModelRiskControlStateV1(StrEnum):
    PASS_RECEIPTED = "PASS_RECEIPTED"
    BLOCKED_WITH_TYPED_REASON = "BLOCKED_WITH_TYPED_REASON"
    NOT_APPLICABLE_WITH_PROOF = "NOT_APPLICABLE_WITH_PROOF"


@dataclass(frozen=True, slots=True)
class ModelRiskControlEvidenceV1:
    control_id: str
    state: ModelRiskControlStateV1
    evidence_receipt_refs: tuple[str, ...]
    blocker_codes: tuple[ReasonCode, ...]
    limitation_refs: tuple[str, ...]
    current: bool

    def __post_init__(self) -> None:
        if self.control_id not in MODEL_RISK_CONTROL_IDS_V1 or type(self.state) is not ModelRiskControlStateV1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "model-risk control identity or state is not owner-certified",
            )
        _refs(self.evidence_receipt_refs, "evidence_receipt_refs")
        _refs(self.limitation_refs, "limitation_refs")
        if (
            not isinstance(self.blocker_codes, tuple)
            or any(type(code) is not ReasonCode for code in self.blocker_codes)
            or len(self.blocker_codes) != len(set(self.blocker_codes))
            or type(self.current) is not bool
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "model-risk control evidence must be exact and typed",
            )
        if self.state is ModelRiskControlStateV1.PASS_RECEIPTED and (
            not self.evidence_receipt_refs or self.blocker_codes or not self.current
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "a passing control requires current receipts and zero blockers",
            )
        if self.state is ModelRiskControlStateV1.BLOCKED_WITH_TYPED_REASON and not self.blocker_codes:
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "a blocked control requires a typed reason",
            )
        if self.state is ModelRiskControlStateV1.NOT_APPLICABLE_WITH_PROOF and not self.evidence_receipt_refs:
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "not-applicable control disposition requires proof",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "ModelRiskControlEvidenceV1":
        if not isinstance(value, Mapping):
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "control payload must be a mapping")
        payload = dict(value)
        payload["state"] = ModelRiskControlStateV1(payload["state"])
        payload["evidence_receipt_refs"] = tuple(payload["evidence_receipt_refs"])
        payload["blocker_codes"] = tuple(ReasonCode(code) for code in payload["blocker_codes"])
        payload["limitation_refs"] = tuple(payload["limitation_refs"])
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class NoTradeConditionOutcomeV1:
    condition_id: str
    active: bool
    evidence_receipt_refs: tuple[str, ...]
    reason_codes: tuple[ReasonCode, ...]

    def __post_init__(self) -> None:
        if self.condition_id not in NO_TRADE_CONDITION_IDS_V1 or type(self.active) is not bool:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "NO_TRADE condition identity or activity is invalid",
            )
        _refs(self.evidence_receipt_refs, "evidence_receipt_refs")
        if (
            not isinstance(self.reason_codes, tuple)
            or any(type(code) is not ReasonCode for code in self.reason_codes)
            or len(self.reason_codes) != len(set(self.reason_codes))
        ):
            raise ContractValidationError(
                ReasonCode.CONTRACT_OR_TYPE_INVALID,
                "NO_TRADE reason codes must be a unique typed tuple",
            )
        if self.active and not self.reason_codes:
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "an active NO_TRADE condition requires a typed reason",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "NoTradeConditionOutcomeV1":
        if not isinstance(value, Mapping):
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "condition payload must be a mapping")
        payload = dict(value)
        payload["evidence_receipt_refs"] = tuple(payload["evidence_receipt_refs"])
        payload["reason_codes"] = tuple(ReasonCode(code) for code in payload["reason_codes"])
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class PermanentNoTradeEvidenceComparisonV1:
    comparison_id: str
    input_lock_id: str
    execution_adjusted_lcb: Decimal
    candidate_utility: Decimal
    strongest_classical_utility: Decimal
    no_trade_utility: Decimal
    strongest_comparator: str
    permanent_no_trade_present: bool = True

    def __post_init__(self) -> None:
        for name in ("comparison_id", "input_lock_id", "strongest_comparator"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, f"{name} is required")
        for name in (
            "execution_adjusted_lcb",
            "candidate_utility",
            "strongest_classical_utility",
            "no_trade_utility",
        ):
            object.__setattr__(self, name, exact_decimal(getattr(self, name), field_name=name))
        if type(self.permanent_no_trade_present) is not bool or not self.permanent_no_trade_present:
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "permanent NO_TRADE comparator cannot be removed",
            )
        utilities = {
            "CANDIDATE": self.candidate_utility,
            "STRONGEST_CLASSICAL": self.strongest_classical_utility,
            "NO_TRADE": self.no_trade_utility,
        }
        conservative_priority = {
            "NO_TRADE": 0,
            "STRONGEST_CLASSICAL": 1,
            "CANDIDATE": 2,
        }
        expected = sorted(
            utilities,
            key=lambda key: (utilities[key].copy_negate(), conservative_priority[key]),
        )[0]
        if self.strongest_comparator != expected:
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "strongest comparator is not the deterministic same-basis winner",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "PermanentNoTradeEvidenceComparisonV1":
        if not isinstance(value, Mapping):
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "comparison payload must be a mapping")
        return cls(**dict(value))


@dataclass(frozen=True, slots=True)
class ModelRiskLaneEvidenceV1:
    lane: str
    result_receipt_ref: str
    input_lock_id: str
    component_or_template_ref: str
    observed_at: datetime
    valid_until: datetime

    def __post_init__(self) -> None:
        if self.lane not in {"REPLAY", "PAPER"}:
            raise ContractValidationError(
                ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN,
                "model-risk lane evidence must be exact REPLAY or PAPER",
            )
        for name in (
            "result_receipt_ref",
            "input_lock_id",
            "component_or_template_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    f"{name} is required for model-risk lane evidence",
                )
        observed = parse_utc(self.observed_at, field_name="observed_at")
        valid_until = parse_utc(self.valid_until, field_name="valid_until")
        object.__setattr__(self, "observed_at", observed)
        object.__setattr__(self, "valid_until", valid_until)
        if observed > valid_until:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "model-risk lane validity precedes observation",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "ModelRiskLaneEvidenceV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "model-risk lane evidence fields differ",
            )
        return cls(**dict(value))


@dataclass(frozen=True, slots=True)
class ModelRiskAdjudicationBasisV1:
    expected_component_or_template_ref: str
    evaluated_at: datetime
    required_evidence_valid_until: datetime
    required_evidence_receipt_refs: tuple[str, ...]
    replay_lane: ModelRiskLaneEvidenceV1 | None
    paper_lane: ModelRiskLaneEvidenceV1 | None
    uncertainty_reserve: Decimal
    model_risk_reserve: Decimal
    capacity_hard_veto: bool
    liquidity_hard_veto: bool
    capacity_liquidity_receipt_refs: tuple[str, ...]
    independent_review_state: str
    independent_review_receipt_ref: str

    def __post_init__(self) -> None:
        for name in (
            "expected_component_or_template_ref",
            "independent_review_state",
            "independent_review_receipt_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    f"{name} is required for model-risk adjudication",
                )
        _refs(
            self.required_evidence_receipt_refs,
            "required_evidence_receipt_refs",
            required=True,
        )
        _refs(
            self.capacity_liquidity_receipt_refs,
            "capacity_liquidity_receipt_refs",
            required=True,
        )
        for name, lane in (("replay_lane", self.replay_lane), ("paper_lane", self.paper_lane)):
            if lane is not None and type(lane) is not ModelRiskLaneEvidenceV1:
                raise ContractValidationError(
                    ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                    f"{name} must be exact typed lane evidence or explicit absence",
                )
        if self.replay_lane is not None and self.replay_lane.lane != "REPLAY":
            raise ContractValidationError(
                ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN,
                "replay model-risk evidence carries another lane",
            )
        if self.paper_lane is not None and self.paper_lane.lane != "PAPER":
            raise ContractValidationError(
                ReasonCode.ST12F_LANE_SUBSTITUTION_FORBIDDEN,
                "paper model-risk evidence carries another lane",
            )
        evaluated = parse_utc(self.evaluated_at, field_name="evaluated_at")
        valid_until = parse_utc(
            self.required_evidence_valid_until,
            field_name="required_evidence_valid_until",
        )
        object.__setattr__(self, "evaluated_at", evaluated)
        object.__setattr__(self, "required_evidence_valid_until", valid_until)
        for name in ("uncertainty_reserve", "model_risk_reserve"):
            value = exact_decimal(getattr(self, name), field_name=name)
            if value < 0:
                raise ContractValidationError(
                    ReasonCode.ST12F_MODEL_RISK_VETO,
                    f"{name} must be nonnegative",
                )
            object.__setattr__(self, name, value)
        if type(self.capacity_hard_veto) is not bool or type(self.liquidity_hard_veto) is not bool:
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "capacity and liquidity vetoes must be exact booleans",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "ModelRiskAdjudicationBasisV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(
                ReasonCode.SCHEMA_MISMATCH,
                "model-risk adjudication basis fields differ",
            )
        payload = dict(value)
        payload["required_evidence_receipt_refs"] = tuple(
            payload["required_evidence_receipt_refs"]
        )
        payload["capacity_liquidity_receipt_refs"] = tuple(
            payload["capacity_liquidity_receipt_refs"]
        )
        for name in ("replay_lane", "paper_lane"):
            if payload[name] is not None:
                payload[name] = ModelRiskLaneEvidenceV1.from_canonical_mapping(
                    payload[name]
                )
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class ModelRiskEvidenceAssessmentV1:
    assessment_id: str
    schema_version: str
    contract_version: str
    input_lock_id: str
    control_evidence: tuple[ModelRiskControlEvidenceV1, ...]
    no_trade_condition_outcomes: tuple[NoTradeConditionOutcomeV1, ...]
    permanent_no_trade_comparison: PermanentNoTradeEvidenceComparisonV1
    adjudication_basis: ModelRiskAdjudicationBasisV1
    blocker_codes: tuple[ReasonCode, ...]
    limitations: tuple[str, ...]
    receipt_refs: tuple[str, ...]
    permanent_no_trade_wins: bool
    champion_challenger_evidence_only: bool
    automatic_promotion_allowed: bool
    terminal_state: str

    def __post_init__(self) -> None:
        if self.schema_version != "QTT_ST12F_MODEL_RISK_ASSESSMENT_V1_4" or self.contract_version != "1.4":
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "model-risk schema differs")
        if tuple(row.control_id for row in self.control_evidence) != MODEL_RISK_CONTROL_IDS_V1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "model-risk assessment must carry exactly 12 ordered controls",
            )
        if tuple(row.condition_id for row in self.no_trade_condition_outcomes) != NO_TRADE_CONDITION_IDS_V1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_IDENTITY_INVALID,
                "model-risk assessment must carry exactly eight ordered conditions",
            )
        if type(self.permanent_no_trade_comparison) is not PermanentNoTradeEvidenceComparisonV1 or self.permanent_no_trade_comparison.input_lock_id != self.input_lock_id:
            raise ContractValidationError(ReasonCode.ST12F_INPUT_LOCK_MISMATCH, "comparison lock differs")
        if type(self.adjudication_basis) is not ModelRiskAdjudicationBasisV1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "model-risk assessment lacks its typed adjudication basis",
            )
        _refs(self.limitations, "limitations")
        _refs(self.receipt_refs, "receipt_refs")
        if (
            not isinstance(self.blocker_codes, tuple)
            or any(type(code) is not ReasonCode for code in self.blocker_codes)
            or len(self.blocker_codes) != len(set(self.blocker_codes))
            or type(self.permanent_no_trade_wins) is not bool
            or type(self.champion_challenger_evidence_only) is not bool
            or type(self.automatic_promotion_allowed) is not bool
            or not self.champion_challenger_evidence_only
            or self.automatic_promotion_allowed
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "assessment may create evidence but never promotion authority",
            )
        active = any(row.active for row in self.no_trade_condition_outcomes)
        non_review_veto = any(
            row.active and row.condition_id != "INDEPENDENT_REVIEW_NOT_CLOSED"
            for row in self.no_trade_condition_outcomes
        )
        review_pending = next(
            row.active
            for row in self.no_trade_condition_outcomes
            if row.condition_id == "INDEPENDENT_REVIEW_NOT_CLOSED"
        )
        if self.permanent_no_trade_wins != active or (
            non_review_veto and self.terminal_state != "NO_TRADE"
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "NO_TRADE terminal result must preserve every active veto",
            )
        if not non_review_veto and review_pending and self.terminal_state != "READY_FOR_INDEPENDENT_REVIEW":
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "veto-free evidence remains pending independent review",
            )
        if not active and self.terminal_state != "CLOSED_INDEPENDENTLY_VALIDATED":
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "review-closed model-risk evidence requires its closed terminal state",
            )

    @classmethod
    def from_canonical_mapping(cls, value: object) -> "ModelRiskEvidenceAssessmentV1":
        if not isinstance(value, Mapping) or set(value) != {field.name for field in fields(cls)}:
            raise ContractValidationError(ReasonCode.SCHEMA_MISMATCH, "assessment payload fields differ")
        payload = dict(value)
        payload["control_evidence"] = tuple(
            ModelRiskControlEvidenceV1.from_canonical_mapping(row)
            for row in payload["control_evidence"]
        )
        payload["no_trade_condition_outcomes"] = tuple(
            NoTradeConditionOutcomeV1.from_canonical_mapping(row)
            for row in payload["no_trade_condition_outcomes"]
        )
        payload["permanent_no_trade_comparison"] = PermanentNoTradeEvidenceComparisonV1.from_canonical_mapping(
            payload["permanent_no_trade_comparison"]
        )
        payload["adjudication_basis"] = ModelRiskAdjudicationBasisV1.from_canonical_mapping(
            payload["adjudication_basis"]
        )
        payload["blocker_codes"] = tuple(ReasonCode(code) for code in payload["blocker_codes"])
        payload["limitations"] = tuple(payload["limitations"])
        payload["receipt_refs"] = tuple(payload["receipt_refs"])
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)

    def assert_independent_review_join(
        self,
        *,
        assessment_receipt_ref: str,
        parent_ready_bundle_ref: str,
        reviewed_parent_bundle_ref: str,
        candidate_bundle_version: str,
        reviewed_candidate_bundle_version: str,
        review_receipt_ref: str,
        reviewer_authority_receipt_ref: str,
        input_lock_id: str,
        component_or_template_ref: str,
        source_epoch_refs: tuple[str, ...],
        reviewed_source_epoch_refs: tuple[str, ...],
        effective_cutoff: datetime,
        recorded_cutoff: datetime,
        review_recorded_at: datetime,
    ) -> None:
        effective = parse_utc(effective_cutoff, field_name="effective_cutoff")
        recorded = parse_utc(recorded_cutoff, field_name="recorded_cutoff")
        review_recorded = parse_utc(
            review_recorded_at,
            field_name="review_recorded_at",
        )
        expected_assessment_ref = (
            f"ST12F-RECEIPT::{self.assessment_id}::MODEL_RISK_ASSESSMENT"
        )
        required_receipts = {
            parent_ready_bundle_ref,
            review_receipt_ref,
            reviewer_authority_receipt_ref,
        }
        non_review_conditions = tuple(
            row
            for row in self.no_trade_condition_outcomes
            if row.condition_id != "INDEPENDENT_REVIEW_NOT_CLOSED"
        )
        if (
            assessment_receipt_ref != expected_assessment_ref
            or parent_ready_bundle_ref != reviewed_parent_bundle_ref
            or candidate_bundle_version != reviewed_candidate_bundle_version
            or self.input_lock_id != input_lock_id
            or self.adjudication_basis.expected_component_or_template_ref
            != component_or_template_ref
            or self.adjudication_basis.independent_review_receipt_ref
            != review_receipt_ref
            or self.adjudication_basis.independent_review_state
            != "CLOSED_INDEPENDENTLY_VALIDATED"
            or source_epoch_refs != reviewed_source_epoch_refs
            or not required_receipts <= set(self.receipt_refs)
            or effective != recorded
            or review_recorded > recorded
            or not self.adjudication_basis.evaluated_at
            <= effective
            <= self.adjudication_basis.required_evidence_valid_until
            or len(non_review_conditions) != 7
            or any(row.active for row in non_review_conditions)
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "model-risk review closure differs from the exact assessment, parent, candidate, review, authority, lock, epoch, or cutoff join",
            )


class ModelRiskEvidenceAdjudicatorV1:
    def adjudicate(
        self,
        *,
        assessment_id: str,
        input_lock_id: str,
        controls: tuple[ModelRiskControlEvidenceV1, ...],
        conditions: tuple[NoTradeConditionOutcomeV1, ...],
        comparison: PermanentNoTradeEvidenceComparisonV1,
        adjudication_basis: ModelRiskAdjudicationBasisV1,
        limitations: tuple[str, ...],
        receipt_refs: tuple[str, ...],
    ) -> ModelRiskEvidenceAssessmentV1:
        if tuple(row.control_id for row in controls) != MODEL_RISK_CONTROL_IDS_V1 or tuple(row.condition_id for row in conditions) != NO_TRADE_CONDITION_IDS_V1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "adjudication requires exact 12-control and eight-condition inputs",
            )
        if (
            type(comparison) is not PermanentNoTradeEvidenceComparisonV1
            or type(adjudication_basis) is not ModelRiskAdjudicationBasisV1
            or comparison.input_lock_id != input_lock_id
        ):
            raise ContractValidationError(
                ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
                "model-risk comparison and adjudication basis must share one exact lock",
            )
        mutable = {row.condition_id: row for row in conditions}

        def activate(
            condition_id: str,
            derived: bool,
            *,
            evidence_refs: tuple[str, ...],
            reason_code: ReasonCode,
        ) -> None:
            prior = mutable[condition_id]
            active = prior.active or derived
            mutable[condition_id] = NoTradeConditionOutcomeV1(
                condition_id=condition_id,
                active=active,
                evidence_receipt_refs=tuple(
                    dict.fromkeys((*prior.evidence_receipt_refs, *evidence_refs))
                ),
                reason_codes=(
                    tuple(dict.fromkeys((*prior.reason_codes, reason_code)))
                    if derived
                    else prior.reason_codes
                ),
            )

        lane_rows = tuple(
            row
            for row in (adjudication_basis.replay_lane, adjudication_basis.paper_lane)
            if row is not None
        )
        lane_refs = tuple(row.result_receipt_ref for row in lane_rows)
        missing_or_stale = (
            adjudication_basis.evaluated_at
            > adjudication_basis.required_evidence_valid_until
            or any(
                not row.observed_at
                <= adjudication_basis.evaluated_at
                <= row.valid_until
                for row in lane_rows
            )
            or any(
                row.state is ModelRiskControlStateV1.BLOCKED_WITH_TYPED_REASON
                or not row.current
                for row in controls
            )
        )
        lanes_missing = (
            adjudication_basis.replay_lane is None
            or adjudication_basis.paper_lane is None
        )
        lock_or_scope_conflict = any(
            row.input_lock_id != input_lock_id
            or row.component_or_template_ref
            != adjudication_basis.expected_component_or_template_ref
            for row in lane_rows
        )
        try:
            with localcontext(decimal_context_v1()) as context:
                context.traps[Inexact] = True
                combined_reserve = (
                    adjudication_basis.uncertainty_reserve
                    + adjudication_basis.model_risk_reserve
                )
        except DecimalException as exc:
            raise NumericDomainError(
                ReasonCode.INVALID_NUMERIC_INPUT,
                "model-risk reserve sum must be exactly representable in the canonical Decimal context",
            ) from exc
        reserve_dominates = combined_reserve >= comparison.candidate_utility
        capacity_or_liquidity_veto = (
            adjudication_basis.capacity_hard_veto
            or adjudication_basis.liquidity_hard_veto
        )
        comparator_dominates = comparison.candidate_utility <= max(
            comparison.strongest_classical_utility,
            comparison.no_trade_utility,
        )
        review_not_closed = (
            adjudication_basis.independent_review_state
            != "CLOSED_INDEPENDENTLY_VALIDATED"
        )

        activate(
            "NEGATIVE_OR_ZERO_EXECUTION_ADJUSTED_LCB",
            comparison.execution_adjusted_lcb <= 0,
            evidence_refs=(comparison.comparison_id,),
            reason_code=ReasonCode.ST12F_MODEL_RISK_VETO,
        )
        activate(
            "MISSING_OR_STALE_REQUIRED_EVIDENCE",
            missing_or_stale,
            evidence_refs=adjudication_basis.required_evidence_receipt_refs,
            reason_code=ReasonCode.STALE_CONTEXT,
        )
        activate(
            "REPLAY_OR_PAPER_LANE_MISSING",
            lanes_missing,
            evidence_refs=lane_refs,
            reason_code=ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
        )
        activate(
            "LOCK_OR_SCOPE_CONFLICT",
            lock_or_scope_conflict,
            evidence_refs=lane_refs,
            reason_code=ReasonCode.ST12F_INPUT_LOCK_MISMATCH,
        )
        activate(
            "UNCERTAINTY_OR_MODEL_RISK_DOMINATES_EDGE",
            reserve_dominates,
            evidence_refs=adjudication_basis.required_evidence_receipt_refs,
            reason_code=ReasonCode.ST12F_MODEL_RISK_VETO,
        )
        activate(
            "CAPACITY_OR_LIQUIDITY_HARD_VETO",
            capacity_or_liquidity_veto,
            evidence_refs=adjudication_basis.capacity_liquidity_receipt_refs,
            reason_code=ReasonCode.ST12F_MODEL_RISK_VETO,
        )
        activate(
            "STRONGEST_CLASSICAL_OR_NO_TRADE_DOMINATES",
            comparator_dominates,
            evidence_refs=(comparison.comparison_id,),
            reason_code=ReasonCode.ST12F_MODEL_RISK_VETO,
        )
        activate(
            "INDEPENDENT_REVIEW_NOT_CLOSED",
            review_not_closed,
            evidence_refs=(adjudication_basis.independent_review_receipt_ref,),
            reason_code=ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
        )
        active_conditions = tuple(mutable[row_id] for row_id in NO_TRADE_CONDITION_IDS_V1)
        blockers = tuple(
            dict.fromkeys(
                code
                for condition in active_conditions
                for code in condition.reason_codes
                if condition.active
            )
        )
        no_trade = any(row.active for row in active_conditions)
        non_review_veto = any(
            row.active and row.condition_id != "INDEPENDENT_REVIEW_NOT_CLOSED"
            for row in active_conditions
        )
        terminal_state = (
            "NO_TRADE"
            if non_review_veto
            else "READY_FOR_INDEPENDENT_REVIEW"
            if mutable["INDEPENDENT_REVIEW_NOT_CLOSED"].active
            else "CLOSED_INDEPENDENTLY_VALIDATED"
        )
        return ModelRiskEvidenceAssessmentV1(
            assessment_id=assessment_id,
            schema_version="QTT_ST12F_MODEL_RISK_ASSESSMENT_V1_4",
            contract_version="1.4",
            input_lock_id=input_lock_id,
            control_evidence=controls,
            no_trade_condition_outcomes=active_conditions,
            permanent_no_trade_comparison=comparison,
            adjudication_basis=adjudication_basis,
            blocker_codes=blockers,
            limitations=limitations,
            receipt_refs=receipt_refs,
            permanent_no_trade_wins=no_trade,
            champion_challenger_evidence_only=True,
            automatic_promotion_allowed=False,
            terminal_state=terminal_state,
        )


if len(MODEL_RISK_CONTROL_IDS_V1) != 12 or len(NO_TRADE_CONDITION_IDS_V1) != 8:
    raise ContractValidationError(
        ReasonCode.SCHEMA_MISMATCH,
        "model-risk and permanent NO_TRADE denominators differ",
    )


def _bind_probability_condition_evidence_v1(
    *, scope: ProbabilityProducerScopeV1, read_snapshot: ProbabilityProducerReadSnapshotV1,
    evaluated_ns: int, model_available_ns: int, model_valid_until_ns: int,
    receipt_dependency_refs: tuple[str, ...], receipt_valid_until_ns: int,
    conditions: tuple[NoTradeConditionOutcomeV1, ...],
) -> tuple[NoTradeConditionOutcomeV1, ...]:
    """Add one conservative probability-evidence floor to the original eight rows."""
    from .models import ProbabilityProducerScopeV1, _probability_ns_v1, _probability_refs_v1
    from .persistence import ProbabilityProducerReadSnapshotV1
    from .receipts import _validate_probability_control_spine_v1

    def need(ok, detail):
        if not ok:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, detail)

    need(type(scope) is ProbabilityProducerScopeV1 and type(read_snapshot) is ProbabilityProducerReadSnapshotV1
         and read_snapshot.scope == scope, "PROBABILITY_RISK_SCOPE")
    for instant in (evaluated_ns, model_available_ns, model_valid_until_ns, receipt_valid_until_ns):
        _probability_ns_v1(instant)
    _probability_refs_v1(receipt_dependency_refs, nonempty=True)
    need(type(conditions) is tuple and len(conditions) == 8 and
         all(type(row) is NoTradeConditionOutcomeV1 for row in conditions) and
         tuple(row.condition_id for row in conditions) == NO_TRADE_CONDITION_IDS_V1,
         "PROBABILITY_CONDITION_ROSTER")
    need(read_snapshot.read_completed_ns <= evaluated_ns, "PROBABILITY_RISK_FUTURE_READ")
    blocker = not (model_available_ns <= read_snapshot.read_completed_ns <= evaluated_ns < model_valid_until_ns
                   and evaluated_ns < receipt_valid_until_ns)
    retained = list(receipt_dependency_refs)
    invalidated = set()
    for record in read_snapshot.revocation_records:
        _validate_probability_control_spine_v1(record)
        payload = record.typed_payload
        need(payload.scope == scope and payload.available_ns <= read_snapshot.read_completed_ns and
             payload.effective_ns <= evaluated_ns, "PROBABILITY_RISK_REVOCATION_CUT")
        invalidated.update(payload.body["invalidated_dependency_refs"])
        retained.extend((record.record_id, *payload.dependency_refs))
    blocker = blocker or bool(invalidated.intersection(receipt_dependency_refs))
    prior = None
    bad = green = 0
    # A retained initial latch is conservative evidence; accepted genesis is
    # reconstructed by the materializer. This consumer must never clear it.
    latched = bool(read_snapshot.publication_records and
                   read_snapshot.publication_records[0].typed_payload.body["after"]["latched"])
    seen_rows, seen_clusters = set(), set()
    for sequence, record in enumerate(read_snapshot.publication_records, 1):
        _validate_probability_control_spine_v1(record)
        payload, body = record.typed_payload, record.typed_payload.body
        need(payload.scope == scope and payload.available_ns <= read_snapshot.read_completed_ns and
             payload.effective_ns <= evaluated_ns and record.sequence == sequence, "PROBABILITY_RISK_PUBLICATION_CUT")
        need(body["expected_head_ref"] == (None if prior is None else prior.record_id), "PROBABILITY_RISK_PUBLICATION_PARENT")
        if prior is not None:
            previous = prior.typed_payload.body["after"]
            need(body["expected_high_watermark"] == previous["high_watermark"] and
                 body["cutoff_ns"] >= previous["last_cutoff_ns"], "PROBABILITY_RISK_PUBLICATION_CURSOR")
        if body["kind"] == "WINDOW":
            for row in body["selected_rows"]:
                need(row["cluster_id"] not in seen_clusters and not seen_rows.intersection(row["row_ids"]),
                     "PROBABILITY_WINDOW_REUSE")
                seen_clusters.add(row["cluster_id"]); seen_rows.update(row["row_ids"])
            if body["family_result"] == "MATERIAL_BREACH":
                bad, green = min(2, bad + 1), 0
                latched = latched or bad == 2
            elif body["family_result"] == "FAMILY_NONREJECTION":
                bad, green = 0, min(2, green + 1)
            else:
                bad = green = 0
        else:
            bad = green = 0
            latched = latched or body["kind"] == "HARD_FAILURE"
            if prior is not None:
                need(body["after"]["last_maturity_ns"] == prior.typed_payload.body["after"]["last_maturity_ns"],
                     "PROBABILITY_NONWINDOW_MATURITY")
        need((body["after"]["bad_streak"], body["after"]["green_streak"], body["after"]["latched"]) ==
             (bad, green, latched), "PROBABILITY_RISK_STATE_TRANSITION")
        retained.extend((record.record_id, *payload.dependency_refs))
        prior = record
    if prior is not None:
        last = prior.typed_payload.body
        blocker = (blocker or latched or last["kind"] == "EVIDENCE_UNAVAILABLE" or
                   (last["kind"] == "WINDOW" and last["family_result"] == "UNAVAILABLE"))
    for reference in receipt_dependency_refs:
        record = read_snapshot.records_by_ref.get(reference)
        if record is not None:
            payload = record.typed_payload
            need(payload.available_ns <= read_snapshot.read_completed_ns, "PROBABILITY_RISK_FUTURE_DEPENDENCY")
            blocker = blocker or (payload.valid_until_ns is not None and evaluated_ns >= payload.valid_until_ns)
    retained_refs = tuple(dict.fromkeys(retained))
    before = conditions[1]
    after = NoTradeConditionOutcomeV1(before.condition_id, before.active or blocker,
        tuple(dict.fromkeys((*before.evidence_receipt_refs, *retained_refs))),
        tuple(dict.fromkeys((*before.reason_codes, *((ReasonCode.ST12F_MODEL_RISK_VETO,) if blocker else ())))))
    return (conditions[0], after, *conditions[2:])


from .models import (
    ProbabilityProducerScopeV1, _ProbabilityWindowRequestV1, _probability_require_v1,
    _probability_projection_integer_v1, _probability_projection_names_v1,
)
import copy as _probability_copy_v1


def _probability_genesis_v1(scope: ProbabilityProducerScopeV1, *, reference_clusters: tuple[str, ...], reference_rows: tuple[str, ...], reference_cutoff_ns: int, initial_latch: bool) -> dict:
    _probability_require_v1(type(scope) is ProbabilityProducerScopeV1 and type(initial_latch) is bool, 'GENESIS_TYPE')
    _probability_projection_names_v1(reference_clusters, 'REFERENCE_CLUSTERS', empty=True)
    _probability_projection_names_v1(reference_rows, 'REFERENCE_ROWS', empty=True)
    _probability_projection_integer_v1(reference_cutoff_ns, 'REFERENCE_CUTOFF_NS', None)
    return {'scope': scope.as_dict(), 'head_ref': None, 'sequence': 0, 'high_watermark': 0, 'last_maturity_ns': reference_cutoff_ns, 'last_cutoff_ns': reference_cutoff_ns, 'bad_streak': 0, 'green_streak': 0, 'latched': initial_latch, 'used_clusters': list(reference_clusters), 'used_rows': list(reference_rows)}

def _derive_probability_window_v1(state: dict, request: _ProbabilityWindowRequestV1, *, window_size: int, max_catalog_rows: int) -> dict:
    """Pure window transition over detached accepted-owner projections."""
    _probability_require_v1(type(window_size) is int and window_size == 200, 'WINDOW_SIZE')
    _probability_projection_integer_v1(max_catalog_rows, 'CATALOG_BUDGET', 1)
    _probability_require_v1(type(request) is _ProbabilityWindowRequestV1, 'REQUEST_TYPE')
    _probability_require_v1(state['scope'] == request.scope.as_dict(), 'SCOPE_MISMATCH')
    _probability_require_v1((state['head_ref'], state['sequence'], state['high_watermark']) == (request.expected_head_ref, request.expected_sequence, request.expected_high_watermark), 'STALE_PARENT')
    _probability_require_v1(request.cutoff_ns >= state['last_cutoff_ns'], 'CUTOFF_REGRESSION')
    selected = ()
    if request.kind == 'WINDOW':
        _probability_require_v1(sum((len(r.row_ids) for r in request.catalog)) <= max_catalog_rows, 'CATALOG_RESOURCE_LIMIT')
        cids, rids = ([], [])
        maturity = state['last_maturity_ns']
        for offset, row in enumerate(request.catalog, 1):
            _probability_require_v1(row.ordinal == state['high_watermark'] + offset, 'ORDINAL_GAP')
            _probability_require_v1(row.maturity_ns >= maturity, 'MATURITY_ORDER')
            maturity = row.maturity_ns
            cids.append(row.cluster_id)
            rids.extend(row.row_ids)
        _probability_require_v1(len(cids) == len(set(cids)) and len(rids) == len(set(rids)), 'CATALOG_DUPLICATE')
        _probability_require_v1(not set(cids).intersection(state['used_clusters']), 'CLUSTER_REUSE')
        _probability_require_v1(not set(rids).intersection(state['used_rows']), 'SOURCE_ROW_REUSE')
        mature = tuple((r for r in request.catalog if r.maturity_ns <= request.cutoff_ns))
        if len(mature) < window_size:
            return {'disposition': 'NOT_READY_NO_TRANSITION', 'state': _probability_copy_v1.deepcopy(state), 'record': None, 'model_use_authorized': False}
        selected = mature[:window_size]
    after = _probability_copy_v1.deepcopy(state)
    after.update(head_ref=request.receipt_id, sequence=state['sequence'] + 1, last_cutoff_ns=request.cutoff_ns)
    if selected:
        after['high_watermark'] = selected[-1].ordinal
        after['last_maturity_ns'] = selected[-1].maturity_ns
        after['used_clusters'].extend((r.cluster_id for r in selected))
        after['used_rows'].extend((x for r in selected for x in r.row_ids))
    if request.kind == 'HARD_FAILURE':
        after.update(latched=True, bad_streak=0, green_streak=0)
    elif request.kind == 'EVIDENCE_UNAVAILABLE' or request.family_result == 'UNAVAILABLE':
        after.update(bad_streak=0, green_streak=0)
    elif request.family_result == 'MATERIAL_BREACH':
        after.update(bad_streak=min(2, state['bad_streak'] + 1), green_streak=0)
        after['latched'] = state['latched'] or after['bad_streak'] == 2
    else:
        after.update(bad_streak=0, green_streak=min(2, state['green_streak'] + 1))
    record = {'schema_version': 'PROBABILITY_WINDOW_DERIVATION_V1', 'request': request.as_dict(), 'sequence': after['sequence'], 'parent_ref': state['head_ref'], 'selected_rows': [r.as_dict() for r in selected], 'after': {k: v for k, v in after.items() if k not in ('used_rows', 'used_clusters')}, 'authority_class': 'NO_EFFECT_MODEL_REVIEW_EVIDENCE'}
    return {'disposition': 'APPEND_CANDIDATE', 'state': after, 'record': record, 'model_use_authorized': False}
