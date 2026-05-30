"""Stage 1 applicability classification."""

from __future__ import annotations


def classify_stage1_applicability(
    qku_type: str,
    replay_paper_required: bool,
    source_upgrade: bool = False,
    market_primary: str = "PREDICTION_MARKET",
) -> str:
    if qku_type == "DOCTRINE_ONLY_QKU":
        return "STAGE1_DOCTRINE_ONLY"
    if source_upgrade:
        return "STAGE1_SOURCE_UPGRADE_OPTIONAL"
    if market_primary not in {"PREDICTION_MARKET", "MARKET_AGNOSTIC"}:
        return "STAGE1_NOT_APPLICABLE_FUTURE_MARKET"
    if qku_type in {"ATOMICROW_QKU", "PR154_TARGET_QKU"} and market_primary == "PREDICTION_MARKET":
        return "STAGE1_DIRECTLY_APPLICABLE"
    if qku_type in {"PARAMETER_QKU", "DEFAULT_VALUE_QKU", "RANGE_QKU", "FORMULA_QKU", "ALGORITHM_QKU", "OPTIMIZER_SETTING_QKU", "CONSTRAINT_QKU"}:
        return "STAGE1_INDIRECTLY_APPLICABLE"
    if replay_paper_required:
        return "STAGE1_REPLAY_PAPER_ONLY"
    return "STAGE1_INDIRECTLY_APPLICABLE"
