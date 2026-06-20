#!/usr/bin/env python3
"""No-trade comparator for PR168-RP."""

from __future__ import annotations

from typing import Any


def no_trade_comparison_row(candidate: dict[str, Any]) -> dict[str, Any]:
    margin = float(candidate.get("no_trade_comparison_margin", 0.0))
    return {
        "candidate_id": candidate["candidate_id"],
        "no_trade_candidate_ref": candidate["no_trade_candidate_ref"],
        "candidate_score_money": candidate.get("candidate_score_money"),
        "no_trade_comparison_margin": round(margin, 10),
        "no_trade_dominates": margin <= 0,
        "decision_reason_code": "NO_TRADE_DOMINATES" if margin <= 0 else "MISSING_DEFAULT_THRESHOLD",
        "downstream_route": "PR168_RP_NoTradeCandidateComparison.report.json",
        "producer": "PR168_RP_NO_TRADE_COMPARATOR",
        "consumer": "PR168_RANK",
        "upstream_source": candidate["candidate_id"],
        "owning_agent": "Execution Simulation Agent",
        "no_orphan_status": "CONNECTED_TO_NO_TRADE_CONSUMER",
    }
