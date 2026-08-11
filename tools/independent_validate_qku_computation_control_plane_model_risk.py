#!/usr/bin/env python3
"""Independent executable ST12-F model-risk and NO_TRADE validation."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (  # noqa: E402
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.model_risk import (  # noqa: E402
    MODEL_RISK_CONTROL_IDS_V1,
    NO_TRADE_CONDITION_IDS_V1,
    ModelRiskAdjudicationBasisV1,
    ModelRiskControlEvidenceV1,
    ModelRiskControlStateV1,
    ModelRiskEvidenceAdjudicatorV1,
    ModelRiskLaneEvidenceV1,
    NoTradeConditionOutcomeV1,
    PermanentNoTradeEvidenceComparisonV1,
)


NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


def _controls() -> tuple[ModelRiskControlEvidenceV1, ...]:
    return tuple(
        ModelRiskControlEvidenceV1(
            identity,
            ModelRiskControlStateV1.PASS_RECEIPTED,
            (f"R::{identity}",),
            (),
            (),
            True,
        )
        for identity in MODEL_RISK_CONTROL_IDS_V1
    )


def _caller_false_conditions() -> tuple[NoTradeConditionOutcomeV1, ...]:
    return tuple(
        NoTradeConditionOutcomeV1(identity, False, (f"R::{identity}",), ())
        for identity in NO_TRADE_CONDITION_IDS_V1
    )


def _comparison(
    *,
    lcb: str = "0.1",
    candidate: str = "1",
    classical: str = "0.8",
    no_trade: str = "0",
) -> PermanentNoTradeEvidenceComparisonV1:
    utilities = {
        "CANDIDATE": Decimal(candidate),
        "STRONGEST_CLASSICAL": Decimal(classical),
        "NO_TRADE": Decimal(no_trade),
    }
    priority = {"NO_TRADE": 0, "STRONGEST_CLASSICAL": 1, "CANDIDATE": 2}
    strongest = sorted(
        utilities, key=lambda name: (-utilities[name], priority[name])
    )[0]
    return PermanentNoTradeEvidenceComparisonV1(
        "C::1",
        "LOCK::1",
        Decimal(lcb),
        utilities["CANDIDATE"],
        utilities["STRONGEST_CLASSICAL"],
        utilities["NO_TRADE"],
        strongest,
    )


def _lane(lane: str, *, lock: str = "LOCK::1", scope: str = "MATH-01") -> ModelRiskLaneEvidenceV1:
    return ModelRiskLaneEvidenceV1(
        lane=lane,
        result_receipt_ref=f"R::{lane}",
        input_lock_id=lock,
        component_or_template_ref=scope,
        observed_at=NOW - timedelta(minutes=1),
        valid_until=NOW + timedelta(minutes=5),
    )


def _basis(**overrides: object) -> ModelRiskAdjudicationBasisV1:
    values: dict[str, object] = {
        "expected_component_or_template_ref": "MATH-01",
        "evaluated_at": NOW,
        "required_evidence_valid_until": NOW + timedelta(minutes=5),
        "required_evidence_receipt_refs": ("R::REQUIRED",),
        "replay_lane": _lane("REPLAY"),
        "paper_lane": _lane("PAPER"),
        "uncertainty_reserve": Decimal("0.05"),
        "model_risk_reserve": Decimal("0.05"),
        "capacity_hard_veto": False,
        "liquidity_hard_veto": False,
        "capacity_liquidity_receipt_refs": ("R::CAPACITY",),
        "independent_review_state": "READY_FOR_INDEPENDENT_REVIEW",
        "independent_review_receipt_ref": "R::REVIEW",
    }
    values.update(overrides)
    return ModelRiskAdjudicationBasisV1(**values)


def _adjudicate(
    *,
    controls: tuple[ModelRiskControlEvidenceV1, ...] | None = None,
    comparison: PermanentNoTradeEvidenceComparisonV1 | None = None,
    basis: ModelRiskAdjudicationBasisV1 | None = None,
):
    return ModelRiskEvidenceAdjudicatorV1().adjudicate(
        assessment_id="A::1",
        input_lock_id="LOCK::1",
        controls=_controls() if controls is None else controls,
        conditions=_caller_false_conditions(),
        comparison=_comparison() if comparison is None else comparison,
        adjudication_basis=_basis() if basis is None else basis,
        limitations=("L::1",),
        receipt_refs=("R::ASSESSMENT",),
    )


def main() -> int:
    stale_controls = list(_controls())
    stale_controls[0] = ModelRiskControlEvidenceV1(
        stale_controls[0].control_id,
        ModelRiskControlStateV1.BLOCKED_WITH_TYPED_REASON,
        (),
        (ReasonCode.STALE_CONTEXT,),
        (),
        False,
    )
    cases = (
        _adjudicate(comparison=_comparison(lcb="0")),
        _adjudicate(controls=tuple(stale_controls)),
        _adjudicate(basis=_basis(replay_lane=None)),
        _adjudicate(basis=_basis(replay_lane=_lane("REPLAY", lock="LOCK::OTHER"))),
        _adjudicate(
            basis=_basis(
                uncertainty_reserve=Decimal("0.6"),
                model_risk_reserve=Decimal("0.4"),
            )
        ),
        _adjudicate(basis=_basis(capacity_hard_veto=True)),
        _adjudicate(comparison=_comparison(classical="1.1")),
        _adjudicate(),
    )
    independently_matched_conditions = tuple(
        next(
            row.active
            for row in assessment.no_trade_condition_outcomes
            if row.condition_id == condition_id
        )
        for assessment, condition_id in zip(
            cases, NO_TRADE_CONDITION_IDS_V1, strict=True
        )
    )

    classical_tie = _adjudicate(comparison=_comparison(classical="1"))
    no_trade_tie = _adjudicate(comparison=_comparison(no_trade="1"))
    review_pending = _adjudicate()
    review_closed = _adjudicate(
        basis=_basis(independent_review_state="CLOSED_INDEPENDENTLY_VALIDATED")
    )

    checks = (
        len(MODEL_RISK_CONTROL_IDS_V1) == 12,
        len(NO_TRADE_CONDITION_IDS_V1) == 8,
        all(independently_matched_conditions),
        all(case.permanent_no_trade_wins for case in cases),
        all(
            case.no_trade_condition_outcomes[index].active
            for index, case in enumerate(cases)
        ),
        classical_tie.terminal_state == "NO_TRADE",
        no_trade_tie.terminal_state == "NO_TRADE",
        review_pending.terminal_state == "READY_FOR_INDEPENDENT_REVIEW",
        review_closed.terminal_state == "CLOSED_INDEPENDENTLY_VALIDATED",
        all(
            ReasonCode.ST12F_MODEL_RISK_VETO in case.blocker_codes
            for case in cases[:1] + cases[4:7]
        ),
        all(case.automatic_promotion_allowed is False for case in cases),
        all(case.champion_challenger_evidence_only is True for case in cases),
    )
    if not all(checks):
        print("QKU_MODEL_RISK_INDEPENDENT_VALIDATION_FAILED", file=sys.stderr)
        return 1
    print(
        "QKU_MODEL_RISK_INDEPENDENTLY_VALIDATED "
        "checks=12 controls=12 derived_conditions=8 strict_comparisons=2"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
