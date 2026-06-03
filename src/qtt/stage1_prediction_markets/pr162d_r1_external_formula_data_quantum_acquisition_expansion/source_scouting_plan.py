"""Mandatory PR162D-R1 online scouting plan."""

from __future__ import annotations

from typing import Any


def source_scouting_plan_records() -> list[dict[str, Any]]:
    lanes = (
        ("LANE_A_KALSHI", "historical markets/trades/candles and open/recent cutoff mapping"),
        ("LANE_B_POLYMARKET", "Gamma/Data/CLOB public market, orderbook, midpoint, spread, price history, and trade mapping"),
        ("LANE_C_FORECASTEX", "public daily and intraday CSV schema mapping"),
        ("LANE_D_FORMULA_LIBRARY", "scoring metrics, technical indicators, optimizer formulas, and parameter defaults"),
        ("LANE_E_QUANTUM", "QUBO, Ising, BQM, CQM, QAOA, VQE, SamplingVQE, and annealing formulations"),
        ("LANE_F_RESEARCH", "research, public GitHub, institutional, data vendor, and social/research candidate intake"),
    )
    return [
        {
            "source_lane": lane,
            "scouting_objective": objective,
            "official_first_not_official_only_flag": True,
            "non_official_routes_to_replay_paper_flag": True,
            "ci_network_required_flag": False,
            "live_order_authority": False,
        }
        for lane, objective in lanes
    ]
