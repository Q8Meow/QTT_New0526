#!/usr/bin/env python3
"""Order-decision tournament and champion/challenger arbitration."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from tools.pr168_rank_evidence_model import rank_score, result_ref_from_candidate_id, score_components_from_pretrade
from tools.pr168_rank_report_writer import authority_flags


def build_order_decision_tournament(pretrade_rows: list[dict[str, Any]], stack_by_result: dict[str, str]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pretrade_rows:
        grouped[result_ref_from_candidate_id(str(row.get("candidate_id")))].append(row)
    tournament: list[dict[str, Any]] = []
    for index, (result_ref, rows) in enumerate(sorted(grouped.items()), start=1):
        ranked = sorted(rows, key=lambda row: float(row.get("candidate_score_money", 0.0) or 0.0), reverse=True)
        winner = ranked[0]
        no_trade = next((row for row in ranked if row.get("order_type_candidate") == "NO_TRADE_CANDIDATE"), None)
        trade_rows = [row for row in ranked if row.get("order_type_candidate") != "NO_TRADE_CANDIDATE"]
        best_trade = trade_rows[0] if trade_rows else None
        components = score_components_from_pretrade(winner)
        no_trade_dominates = no_trade is not None and (
            best_trade is None
            or float(no_trade.get("candidate_score_money", 0.0) or 0.0)
            >= float(best_trade.get("candidate_score_money", 0.0) or 0.0)
        )
        champion_eligible = (
            winner.get("champion_eligible") is True
            and components["lower_confidence_bound_edge"] > 0
            and components["no_trade_comparison_margin"] > 0
            and components["fill_adjusted_expected_pnl"] > 0
            and not no_trade_dominates
        )
        tournament.append(
            {
                "tournament_id": f"PR168_RANK_TOURNAMENT::{index:05d}",
                "candidate_id": result_ref,
                "candidate_stack_id": stack_by_result.get(result_ref),
                "winning_action": winner.get("order_type_candidate"),
                "winning_source_candidate_id": winner.get("candidate_id"),
                "no_trade_candidate_id": no_trade.get("candidate_id") if no_trade else None,
                "best_trade_candidate_id": best_trade.get("candidate_id") if best_trade else None,
                "best_trade_score": best_trade.get("candidate_score_money") if best_trade else None,
                "no_trade_score": no_trade.get("candidate_score_money") if no_trade else None,
                "no_trade_dominates": no_trade_dominates,
                "rank_score": rank_score(components),
                "champion_eligible": champion_eligible,
                "challenger_eligible": not champion_eligible and bool(rows),
                "retest_required": False,
                "repair_required": not champion_eligible,
                "terminal_true_negative": no_trade_dominates,
                "pareto_frontier_status": "FRONTIER_NO_TRADE" if no_trade_dominates else "FRONTIER_TRADE",
                "selection_reason_codes": _reason_codes(winner, no_trade_dominates, components),
                "score_components": components,
                "why_trade_or_no_trade_ref": f"PR168_RANK_WHY::{index:05d}",
                "mode_scope": winner.get("mode", "REPLAY"),
                "authority_boundary_flags": authority_flags(),
                "upstream_numeric_evidence_refs": [row.get("candidate_id") for row in rows[:7]],
            }
        )
    return tournament


def _reason_codes(row: dict[str, Any], no_trade_dominates: bool, components: dict[str, float]) -> list[str]:
    codes = list(row.get("champion_eligibility_blockers", []))
    if no_trade_dominates:
        codes.append("NO_TRADE_DOMINATES")
    if components["lower_confidence_bound_edge"] <= 0:
        codes.append("LCB_NOT_POSITIVE")
    if components["fill_adjusted_expected_pnl"] <= 0:
        codes.append("FILL_ADJUSTED_PNL_NOT_POSITIVE")
    return sorted(dict.fromkeys(codes))
