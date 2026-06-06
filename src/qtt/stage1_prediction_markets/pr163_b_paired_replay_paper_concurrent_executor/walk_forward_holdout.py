"""Walk-forward and holdout readiness candidates."""

from __future__ import annotations

from typing import Any

from .authority_policy import no_authority_fields, plain_ref


def build_walk_forward(index: int, ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "walk_forward_ref": plain_ref("WALK_FORWARD", index),
        "paired_run_ref": plain_ref("RUN_INPUT", index),
        "candidate_packet_id": ctx["row"]["candidate_packet_id"],
        "qku_ids": list(ctx["row"].get("qku_ids") or []),
        "train_window_candidate_ref": plain_ref("TRAIN_WINDOW", index),
        "replay_window_candidate_ref": plain_ref("REPLAY_WINDOW", index),
        "paper_window_candidate_ref": plain_ref("PAPER_WINDOW", index),
        "holdout_window_candidate_ref": plain_ref("HOLDOUT_WINDOW", index),
        "leakage_guard_ref": ctx["leakage_guard"]["leakage_guard_ref"],
        "data_as_of_policy": "SOURCE_AND_FEATURE_AS_OF_BEFORE_DECISION_NO_RANDOM_SPLIT",
        "overfit_risk_bucket": "MEDIUM" if ctx["row"].get("data_quality_tier") == "DQ0_SYNTHETIC_TEST_ONLY" else "LOW",
        "sample_count_candidate": 1,
        "event_category_bucket": "PREDICTION_MARKET_SYNTHETIC_EVENT",
        "venue_scope": ctx["paper"]["order"].get("venue_scope"),
        "market_scope": ctx["paper"]["order"].get("market_scope"),
        "readiness_status": "WALK_FORWARD_READY_FOR_LATER_PR",
        "no_ranking_created": True,
        "no_profit_evidence": True,
        "validation_status": "PASS",
        **no_authority_fields(),
    }
