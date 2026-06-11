"""Result attribution for PR166-S replay/paper execution outcomes."""

from __future__ import annotations

from typing import Any

from .execution_cost_engine import by_candidate
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, numeric, ready_contexts


def build_result_attribution_rows(
    contexts: list[ExecutionContext],
    order_rows: list[dict[str, Any]],
    fill_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    orders = by_candidate(order_rows)
    fills = by_candidate(fill_rows)
    costs = by_candidate(cost_rows)
    rows: list[dict[str, Any]] = []
    for context in ready_contexts(contexts):
        cid = context.candidate_packet_id
        order = orders[cid]
        fill = fills[cid]
        cost = costs[cid]
        gross = numeric(cost.get("gross_edge"), 0.0)
        net = numeric(cost.get("net_edge_after_costs"), 0.0)
        total_cost = gross - net
        row_id = f"PR166_S_RESULT_ATTRIBUTION::{context.index:06d}"
        recommended = _recommended_next_state(cost, fill)
        rows.append(
            {
                "result_attribution_id": row_id,
                "candidate_packet_id": cid,
                "order_intent_id": order["order_intent_id"],
                "source_selected_batch_id": context.batch_id,
                "qku_id": context.qku_id,
                "condition_fingerprint_id": context.candidate.get("condition_fingerprint_id", ""),
                "combination_fingerprint_id": context.candidate.get("combination_fingerprint_id", ""),
                "scenario_group_id": context.retest.get("scenario_group_id", ""),
                "gross_return_proxy": round(gross, 6),
                "net_return_proxy": round(net, 6),
                "expected_value_delta": round(net - numeric(context.scenario.get("risk_adjusted_net_edge_candidate"), 0.0), 6),
                "calibration_delta": round(numeric(context.scenario.get("outcome_confidence"), 0.5) - 0.5, 6),
                "hit_miss_outcome_proxy": "SETTLEMENT_NOT_PROMOTED_REPLAY_PAPER_PROXY",
                "cost_drag_ratio": _ratio(total_cost, gross),
                "latency_drag_ratio": _ratio(numeric(cost.get("latency_drag"), 0.0), gross),
                "liquidity_drag_ratio": _ratio(numeric(cost.get("liquidity_drag"), 0.0), gross),
                "adverse_selection_ratio": _ratio(numeric(cost.get("adverse_selection_drag"), 0.0), gross),
                "false_discovery_update": round(numeric(context.selection_fdc.get("false_discovery_penalty"), 0.25), 6),
                "memory_update_candidate": net > 0 and fill.get("fill_status") in {"FULL", "PARTIAL"},
                "score_update_candidate": True,
                "rank_update_candidate": True,
                "recommended_next_state": recommended,
                "post_cost_classification": cost["post_cost_classification"],
                "dominant_failure_driver": cost["dominant_failure_driver"],
                "execution_classification": "REPLAY_AND_PAPER_EXECUTED",
                "no_profit_evidence": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_ExecutionCostLedger.report.json",
                    source_row_ref=cost["execution_cost_id"],
                    computed_by_module="result_attribution",
                    owning_agent="risk_agent",
                    consuming_agent="scoring_agent",
                    downstream_action_type="score and memory refresh evidence input",
                    downstream_artifact_route="PR166_S_ScoreRefreshCandidateRegistry.report.json",
                ),
            }
        )
    return rows


def _ratio(value: float, denominator: float) -> float:
    if abs(denominator) < 1e-9:
        return 0.0
    return round(value / abs(denominator), 6)


def _recommended_next_state(cost: dict[str, Any], fill: dict[str, Any]) -> str:
    if cost.get("post_cost_pass_fail_classification") == "PASS" and fill.get("fill_status") in {"FULL", "PARTIAL"}:
        return "SCORE_MEMORY_REFRESH_CANDIDATE"
    if fill.get("fill_status") == "LATENCY_MISSED":
        return "REPAIR_REQUIRED_BEFORE_EXECUTION::LATENCY_MISSED"
    if fill.get("fill_status") == "LIQUIDITY_INSUFFICIENT":
        return "REPAIR_REQUIRED_BEFORE_EXECUTION::LIQUIDITY_INSUFFICIENT"
    return f"REPAIR_REQUIRED_BEFORE_EXECUTION::{cost.get('dominant_failure_driver')}"
