#!/usr/bin/env python3
"""Independent ST12-F model-risk/NO_TRADE validation."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ReasonCode
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.model_risk import (
    MODEL_RISK_CONTROL_IDS_V1,
    NO_TRADE_CONDITION_IDS_V1,
    ModelRiskControlEvidenceV1,
    ModelRiskControlStateV1,
    ModelRiskEvidenceAdjudicatorV1,
    NoTradeConditionOutcomeV1,
    PermanentNoTradeEvidenceComparisonV1,
)


def main() -> int:
    controls = tuple(
        ModelRiskControlEvidenceV1(identity, ModelRiskControlStateV1.PASS_RECEIPTED, (f"R::{identity}",), (), (), True)
        for identity in MODEL_RISK_CONTROL_IDS_V1
    )
    conditions = tuple(
        NoTradeConditionOutcomeV1(identity, False, (f"R::{identity}",), ())
        for identity in NO_TRADE_CONDITION_IDS_V1
    )
    comparison = PermanentNoTradeEvidenceComparisonV1(
        "C::1", "ST12F-LOCK::1", Decimal("0"), Decimal("1"), Decimal("0.5"), Decimal("0"), "CANDIDATE"
    )
    result = ModelRiskEvidenceAdjudicatorV1().adjudicate(
        assessment_id="A::1",
        input_lock_id="ST12F-LOCK::1",
        controls=controls,
        conditions=conditions,
        comparison=comparison,
        limitations=("L::1",),
        receipt_refs=("R::ASSESSMENT",),
    )
    checks = (
        len(MODEL_RISK_CONTROL_IDS_V1) == 12,
        len(NO_TRADE_CONDITION_IDS_V1) == 8,
        result.permanent_no_trade_wins,
        result.terminal_state == "NO_TRADE",
        ReasonCode.ST12F_MODEL_RISK_VETO in result.blocker_codes,
        result.automatic_promotion_allowed is False,
        result.champion_challenger_evidence_only is True,
    )
    if not all(checks):
        print("QKU_MODEL_RISK_INDEPENDENT_VALIDATION_FAILED", file=sys.stderr)
        return 1
    print("QKU_MODEL_RISK_INDEPENDENTLY_VALIDATED checks=7 controls=12 conditions=8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
