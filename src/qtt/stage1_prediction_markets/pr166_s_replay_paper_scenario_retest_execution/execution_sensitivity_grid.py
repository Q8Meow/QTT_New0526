"""Execution sensitivity scenario grid for PR166-S."""

from __future__ import annotations

from typing import Any

from .central_vocab import SENSITIVITY_SCENARIOS
from .execution_cost_engine import by_candidate
from .input_consumption import row_contract
from .selected_batch_loader import numeric


STRESS_ADJUSTMENTS = {
    "BASELINE_COSTS": 0.0,
    "HIGH_FEE_STRESS": 0.010,
    "HIGH_SLIPPAGE_STRESS": 0.020,
    "HIGH_LATENCY_STRESS": 0.015,
    "LOW_LIQUIDITY_STRESS": 0.018,
    "ADVERSE_SELECTION_STRESS": 0.020,
    "SETTLEMENT_UNCERTAINTY_STRESS": 0.012,
    "COMBINED_WORST_REASONABLE_STRESS": 0.060,
}


def build_execution_sensitivity_rows(
    attribution_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    costs = by_candidate(cost_rows)
    rows: list[dict[str, Any]] = []
    index = 0
    for attr in attribution_rows:
        cost = costs[str(attr["candidate_packet_id"])]
        base_net = numeric(cost.get("net_edge_after_costs"), 0.0)
        for scenario in SENSITIVITY_SCENARIOS:
            index += 1
            stressed = round(base_net - STRESS_ADJUSTMENTS[scenario], 6)
            row_id = f"PR166_S_SENSITIVITY::{index:06d}"
            rows.append(
                {
                    "stress_scenario_id": row_id,
                    "candidate_packet_id": attr["candidate_packet_id"],
                    "input_result_ref": attr["result_attribution_id"],
                    "stress_scenario_name": scenario,
                    "base_net_edge": base_net,
                    "stressed_net_edge": stressed,
                    "pass_fail_delta": "PASS_TO_FAIL" if base_net > 0 >= stressed else "NO_PASS_FAIL_CHANGE",
                    "dominant_failure_driver": _driver_for_scenario(scenario, cost),
                    "repair_route_if_failed": _repair_for_scenario(scenario) if stressed <= 0 else "NO_REPAIR_REQUIRED",
                    **row_contract(
                        row_id=row_id,
                        source_artifact_ref="PR166_S_ResultAttributionLedger.report.json",
                        source_row_ref=attr["result_attribution_id"],
                        computed_by_module="execution_sensitivity_grid",
                        owning_agent="risk_agent",
                        consuming_agent="repair_agent",
                        downstream_action_type="execution stress sensitivity input",
                        downstream_artifact_route="PR166_S_RepairFeedbackRouter.report.json",
                    ),
                }
            )
    return rows


def _driver_for_scenario(scenario: str, cost: dict[str, Any]) -> str:
    mapping = {
        "HIGH_FEE_STRESS": "COST_DOMINATED",
        "HIGH_SLIPPAGE_STRESS": "COST_DOMINATED",
        "HIGH_LATENCY_STRESS": "LATENCY_DOMINATED",
        "LOW_LIQUIDITY_STRESS": "LIQUIDITY_DOMINATED",
        "ADVERSE_SELECTION_STRESS": "ADVERSE_SELECTION_DOMINATED",
        "SETTLEMENT_UNCERTAINTY_STRESS": "SETTLEMENT_ASSUMPTION_SENSITIVE",
        "COMBINED_WORST_REASONABLE_STRESS": str(cost.get("dominant_failure_driver", "COST_DOMINATED")),
    }
    return mapping.get(scenario, str(cost.get("dominant_failure_driver", "COST_DOMINATED")))


def _repair_for_scenario(scenario: str) -> str:
    if "LATENCY" in scenario:
        return "LATENCY_MISSED"
    if "LIQUIDITY" in scenario:
        return "LIQUIDITY_INSUFFICIENT"
    if "SETTLEMENT" in scenario:
        return "SETTLEMENT_ASSUMPTION_WEAK"
    if "ADVERSE" in scenario:
        return "ADVERSE_SELECTION_DOMINATED"
    return "COST_DOMINATED"
