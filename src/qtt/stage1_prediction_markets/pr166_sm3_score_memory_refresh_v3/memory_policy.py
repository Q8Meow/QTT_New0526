"""Memory policies for PR166-SM3."""

from __future__ import annotations


def memory_scope_for(row: dict[str, object]) -> dict[str, object]:
    return {
        "condition_fingerprint_id": row.get("condition_fingerprint_id"),
        "scenario_group_id": row.get("scenario_group_id"),
        "qku_id": row.get("qku_id"),
        "formula_id": row.get("formula_id"),
        "algorithm_id": row.get("algorithm_id"),
        "parameter_stack_id": row.get("parameter_stack_id"),
        "market_scope": row.get("market_scope", "PREDICTION_MARKET_REPLAY_PAPER_SCOPE"),
        "liquidity_state": row.get("liquidity_state", "REPLAY_PAPER_LIQUIDITY_BUCKET"),
        "execution_context": "REPLAY_PAPER_ONLY_NO_LIVE_AUTHORITY",
    }


def decay_policy(evidence_class: str) -> str:
    if "POSITIVE" in evidence_class:
        return "REFRESH_AFTER_NEXT_REPLAY_PAPER_OR_30_DAY_STALENESS_CHECK"
    if "NO_FILL" in evidence_class:
        return "RETRY_ONLY_AFTER_FILL_MODEL_OR_DEPTH_EVIDENCE_UPDATE"
    if "STILL_NEGATIVE" in evidence_class:
        return "COOLDOWN_UNTIL_REPAIR_ROUTE_PRODUCES_NEW_REPLAY_PAPER_EVIDENCE"
    return "SUPERSEDE_WHEN_DOWNSTREAM_CONSUMER_PRODUCES_STRONGER_EVIDENCE"


def supersession_policy(evidence_class: str) -> str:
    if "POSITIVE" in evidence_class:
        return "SUPERSEDE_BY_HOLDOUT_RETEST_OR_PR166_QC_REPLAY_PAPER_RESULT"
    if "NO_FILL" in evidence_class:
        return "SUPERSEDE_BY_PR166_SD_OR_PR167B_FILL_PROOF"
    if "STILL_NEGATIVE" in evidence_class:
        return "SUPERSEDE_BY_REPAIR_RETEST_CONVERSION_PROOF"
    return "SUPERSEDE_BY_EXACT_DOWNSTREAM_ROUTE_RECEIPT"
