#!/usr/bin/env python3
"""Order-policy ranking for PR168-RP pretrade candidates."""

from __future__ import annotations

from typing import Any


def rank_policy_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(
        candidates,
        key=lambda row: (
            float(row.get("candidate_score_money", 0.0)),
            float(row.get("lower_confidence_bound_edge", 0.0)),
            str(row.get("candidate_id")),
        ),
        reverse=True,
    )
    rows: list[dict[str, Any]] = []
    no_trade_score = next((float(row.get("candidate_score_money", 0.0)) for row in candidates if row.get("order_type_candidate") == "NO_TRADE_CANDIDATE"), 0.0)
    for rank, row in enumerate(ranked, start=1):
        margin = float(row.get("candidate_score_money", 0.0)) - no_trade_score
        rows.append(
            {
                **row,
                "order_policy_rank": rank,
                "no_trade_comparison_margin": round(margin, 10),
                "champion_eligible": False,
                "champion_eligibility_blockers": [
                    "MISSING_DEFAULT_THRESHOLD",
                    "NO_LIVE_ORDER_AUTHORITY",
                    "NO_CONNECTOR_TRUTH_OR_BINDING",
                ],
                "downstream_route": "PR168_RP_To_PR168_RANK_PreTradeRankingSeed.report.json",
                "no_orphan_status": "CONNECTED_TO_PRETRADE_RANKING_CONSUMER",
            }
        )
    return rows
