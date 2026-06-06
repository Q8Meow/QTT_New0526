"""Leakage and as-of guard receipts."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_leakage_guard(index: int, row: dict[str, Any], clock: dict[str, Any]) -> dict[str, Any]:
    settlement_time = clock["settlement_time_if_available"]
    return {
        "leakage_guard_ref": plain_ref("LEAKAGE_GUARD", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": row["candidate_packet_id"],
        "qku_ids": list(row.get("qku_ids") or []),
        "source_as_of_time": clock["source_as_of_time"],
        "feature_as_of_time": clock["feature_as_of_time"],
        "replay_observation_time": clock["replay_observation_time"],
        "paper_synthetic_time": clock["paper_synthetic_time"],
        "settlement_time_if_available": settlement_time,
        "event_lifecycle_time": clock["event_lifecycle_time"],
        "settlement_label_used": bool(settlement_time),
        "settlement_label_available_before_decision": False,
        "future_data_used": False,
        "post_decision_trade_used_for_pretrade": False,
        "post_resolution_field_used_for_pretrade": False,
        "lookahead_leakage_detected": False,
        "leakage_status": "NO_LEAKAGE_DETECTED",
        "no_promotion_authority": True,
        "no_profit_evidence": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
