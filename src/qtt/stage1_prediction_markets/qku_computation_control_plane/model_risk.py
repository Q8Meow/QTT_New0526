"""Deterministic ST12-F model-risk adjudication with permanent NO_TRADE."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Mapping

from .context import exact_decimal, parse_utc
from .errors import ContractValidationError, ReasonCode
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
            key=lambda key: (-utilities[key], conservative_priority[key]),
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
        reserve_dominates = (
            adjudication_basis.uncertainty_reserve
            + adjudication_basis.model_risk_reserve
            >= comparison.candidate_utility
        )
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
            if review_not_closed
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
