#!/usr/bin/env python3
"""Execution-adjusted ranking seed helpers for PR168-GFP2."""

from __future__ import annotations

from typing import Any


def ranking_seed_rows(universe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "canonical_row_key": row["canonical_row_key"],
            "qku_id": row["qku_id"],
            "formula_id": row["formula_id"],
            "execution_adjusted_edge_seed": row["execution_adjusted_edge_seed"],
            "fill_adjusted_expected_pnl_seed": row["fill_adjusted_expected_pnl_seed"],
            "lower_confidence_bound_edge_seed": row["lower_confidence_bound_edge_seed"],
            "no_trade_margin_seed": row["no_trade_margin_seed"],
            "seed_status": "GAP_ROUTED_TO_REAL_MARKET_REPLAY_RECOMPUTE",
            "champion_eligible": False,
            "live_candidate_worthy": False,
            "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
            "agent_owner": "Ranking Agent",
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
        }
        for row in universe_rows
    ]
