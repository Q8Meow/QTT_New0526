"""Deterministic ST12-F model-risk adjudication with permanent NO_TRADE."""

from __future__ import annotations

from dataclasses import dataclass, fields
from decimal import Decimal
from enum import StrEnum
from typing import Mapping

from .context import exact_decimal
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
        payload["blocker_codes"] = tuple(ReasonCode(code) for code in payload["blocker_codes"])
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
        expected = sorted(utilities, key=lambda key: (-utilities[key], key))[0]
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
class ModelRiskEvidenceAssessmentV1:
    assessment_id: str
    schema_version: str
    contract_version: str
    input_lock_id: str
    control_evidence: tuple[ModelRiskControlEvidenceV1, ...]
    no_trade_condition_outcomes: tuple[NoTradeConditionOutcomeV1, ...]
    permanent_no_trade_comparison: PermanentNoTradeEvidenceComparisonV1
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
        if self.permanent_no_trade_wins != active or (active and self.terminal_state != "NO_TRADE"):
            raise ContractValidationError(
                ReasonCode.ST12F_MODEL_RISK_VETO,
                "NO_TRADE terminal result must preserve every active veto",
            )
        if not active and self.terminal_state != "READY_FOR_INDEPENDENT_REVIEW":
            raise ContractValidationError(
                ReasonCode.ST12F_INDEPENDENT_REVIEW_REQUIRED,
                "veto-free evidence remains pending independent review",
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
        payload["blocker_codes"] = tuple(ReasonCode(code) for code in payload["blocker_codes"])
        return cls(**payload)

    def canonical_json(self) -> str:
        return deterministic_json(self)


class ModelRiskEvidenceAdjudicatorV1:
    def adjudicate(
        self,
        *,
        assessment_id: str,
        input_lock_id: str,
        controls: tuple[ModelRiskControlEvidenceV1, ...],
        conditions: tuple[NoTradeConditionOutcomeV1, ...],
        comparison: PermanentNoTradeEvidenceComparisonV1,
        limitations: tuple[str, ...],
        receipt_refs: tuple[str, ...],
    ) -> ModelRiskEvidenceAssessmentV1:
        if tuple(row.control_id for row in controls) != MODEL_RISK_CONTROL_IDS_V1 or tuple(row.condition_id for row in conditions) != NO_TRADE_CONDITION_IDS_V1:
            raise ContractValidationError(
                ReasonCode.ST12F_EVIDENCE_INCOMPLETE,
                "adjudication requires exact 12-control and eight-condition inputs",
            )
        mutable = list(conditions)
        missing_or_stale = any(
            row.state is ModelRiskControlStateV1.BLOCKED_WITH_TYPED_REASON or not row.current
            for row in controls
        )
        if missing_or_stale:
            index = NO_TRADE_CONDITION_IDS_V1.index("MISSING_OR_STALE_REQUIRED_EVIDENCE")
            prior = mutable[index]
            mutable[index] = NoTradeConditionOutcomeV1(
                prior.condition_id,
                True,
                prior.evidence_receipt_refs,
                tuple(dict.fromkeys((*prior.reason_codes, ReasonCode.ST12F_MODEL_RISK_VETO))),
            )
        if comparison.execution_adjusted_lcb <= 0:
            index = NO_TRADE_CONDITION_IDS_V1.index("NEGATIVE_OR_ZERO_EXECUTION_ADJUSTED_LCB")
            prior = mutable[index]
            mutable[index] = NoTradeConditionOutcomeV1(
                prior.condition_id,
                True,
                prior.evidence_receipt_refs,
                tuple(dict.fromkeys((*prior.reason_codes, ReasonCode.ST12F_MODEL_RISK_VETO))),
            )
        active_conditions = tuple(mutable)
        blockers = tuple(
            dict.fromkeys(
                code
                for condition in active_conditions
                for code in condition.reason_codes
                if condition.active
            )
        )
        no_trade = any(row.active for row in active_conditions)
        return ModelRiskEvidenceAssessmentV1(
            assessment_id=assessment_id,
            schema_version="QTT_ST12F_MODEL_RISK_ASSESSMENT_V1_4",
            contract_version="1.4",
            input_lock_id=input_lock_id,
            control_evidence=controls,
            no_trade_condition_outcomes=active_conditions,
            permanent_no_trade_comparison=comparison,
            blocker_codes=blockers,
            limitations=limitations,
            receipt_refs=receipt_refs,
            permanent_no_trade_wins=no_trade,
            champion_challenger_evidence_only=True,
            automatic_promotion_allowed=False,
            terminal_state="NO_TRADE" if no_trade else "READY_FOR_INDEPENDENT_REVIEW",
        )


if len(MODEL_RISK_CONTROL_IDS_V1) != 12 or len(NO_TRADE_CONDITION_IDS_V1) != 8:
    raise ContractValidationError(
        ReasonCode.SCHEMA_MISMATCH,
        "model-risk and permanent NO_TRADE denominators differ",
    )
