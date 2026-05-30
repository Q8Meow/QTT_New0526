"""Launch-stage classification for QKU records."""

from __future__ import annotations


def classify_launch_stage(market_primary: str, qku_type: str) -> dict[str, object]:
    if qku_type == "DOCTRINE_ONLY_QKU":
        primary = "DOCTRINE_ONLY_STAGELESS"
    elif market_primary == "PREDICTION_MARKET":
        primary = "STAGE1_PREDICTION_MARKET"
    elif market_primary == "MARKET_AGNOSTIC":
        primary = "MARKET_AGNOSTIC_FOUNDATION"
    else:
        primary = "FUTURE_MARKET_EXPANSION"
    return {
        "qku_launch_stage_primary": primary,
        "qku_launch_stage_secondary": "MARKET_AGNOSTIC_FOUNDATION",
        "qku_launch_stage_basis": "PR136_DAY1_LAUNCH_READINESS_PR161B_CONTEXT_AND_PR161C_STAGE1_POLICY",
        "qku_launch_stage_classification_source": "PR136_DERIVED" if market_primary == "PREDICTION_MARKET" else "MASTER_PLAN_DERIVED",
        "qku_stage1_prediction_market_priority_lane": "STAGE1_QKU_AGENT_RETRIEVAL_AND_REPLAY_PAPER_PREP",
        "qku_future_stage_route": "FUTURE_PR_REVIEW_QUEUE",
        "qku_launch_readiness_route": "STAGE1_PREDICTION_MARKET_LAUNCH_PREP_INDEX",
    }
