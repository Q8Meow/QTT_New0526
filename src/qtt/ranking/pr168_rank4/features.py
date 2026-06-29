"""Feature vector helpers for RP5G trade-plan evidence."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .models import dec


def by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("trade_plan_candidate_id")): row for row in rows if row.get("trade_plan_candidate_id")}


def scenario_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("trade_plan_candidate_id")), []).append(row)
    out: dict[str, dict[str, Any]] = {}
    for candidate_id, cand_rows in grouped.items():
        count = len(cand_rows)
        pass_count = sum(1 for row in cand_rows if row.get("scenario_pass_flag") is True)
        worst = min((dec(row.get("scenario_expected_pnl_cash")) for row in cand_rows), default=Decimal("0"))
        conservative = next((row for row in cand_rows if row.get("scenario_family") == "combined_conservative_case"), cand_rows[-1] if cand_rows else {})
        out[candidate_id] = {
            "scenario_row_count": count,
            "scenario_pass_count": pass_count,
            "scenario_robustness_score": Decimal(pass_count) / Decimal(count or 1),
            "scenario_worst_case_pnl_cash": worst,
            "scenario_combined_conservative_pnl_cash": dec(conservative.get("scenario_expected_pnl_cash")),
            "scenario_combined_conservative_no_trade_margin_cash": dec(conservative.get("scenario_no_trade_margin_cash")),
            "scenario_combined_conservative_pass_flag": conservative.get("scenario_pass_flag") is True,
        }
    return out

