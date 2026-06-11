"""Simulated maker/taker fill model for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import stable_ref
from .execution_cost_engine import by_candidate
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, numeric, ready_contexts


def build_simulated_fill_rows(
    contexts: list[ExecutionContext],
    order_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    latency_rows: list[dict[str, Any]],
    liquidity_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    orders = by_candidate(order_rows)
    costs = by_candidate(cost_rows)
    latencies = by_candidate(latency_rows)
    liquidities = by_candidate(liquidity_rows)
    rows: list[dict[str, Any]] = []
    for context in ready_contexts(contexts):
        cid = context.candidate_packet_id
        order = orders[cid]
        cost = costs[cid]
        latency = latencies[cid]
        liquidity = liquidities[cid]
        size = numeric(order.get("simulated_size"), 1.0)
        fill_status = _fill_status(cost, latency, liquidity)
        filled = _filled_quantity(fill_status, size, liquidity)
        unfilled = round(size - filled, 6)
        maker_taker = "MAKER" if order.get("order_type") == "SIMULATED_POST_ONLY" else "TAKER"
        row_id = stable_ref("PR166_S_FILL", cid)
        rows.append(
            {
                "fill_record_id": row_id,
                "order_intent_id": order["order_intent_id"],
                "candidate_packet_id": cid,
                "state_transition_ref": stable_ref("PR166_S_ORDER_STATE", cid, fill_status),
                "fill_status": fill_status,
                "filled_quantity": filled,
                "unfilled_quantity": unfilled,
                "simulated_fill_price": _fill_price(order, cost, maker_taker),
                "simulated_fill_time": f"PR166_S_TIME::{context.index:06d}::FILL",
                "maker_taker_flag": maker_taker,
                "fee_model_ref": cost["fee_model_ref"],
                "slippage_model_ref": cost["slippage_model_ref"],
                "latency_model_ref": cost["latency_model_ref"],
                "liquidity_model_ref": cost["liquidity_model_ref"],
                "settlement_assumption_ref": cost["settlement_assumption_ref"],
                "replay_paper_only": True,
                "no_live_authority": True,
                "no_profit_evidence": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_OrderIntentRegistry.report.json",
                    source_row_ref=order["order_intent_id"],
                    computed_by_module="fill_model",
                    owning_agent="fill_model_agent",
                    consuming_agent="execution_simulation_agent",
                    downstream_action_type="simulated fill result input",
                    downstream_artifact_route="PR166_S_OrderStateTransitionLedger.report.json",
                ),
            }
        )
    return rows


def _fill_status(cost: dict[str, Any], latency: dict[str, Any], liquidity: dict[str, Any]) -> str:
    if latency.get("latency_miss_flag") is True:
        return "LATENCY_MISSED"
    if str(liquidity.get("liquidity_bucket")) == "LOW" and numeric(cost.get("net_edge_after_costs"), 0.0) <= 0:
        return "LIQUIDITY_INSUFFICIENT"
    if numeric(liquidity.get("partial_fill_probability_proxy"), 0.0) >= 0.50:
        return "PARTIAL"
    if numeric(cost.get("net_edge_after_costs"), 0.0) < -0.20:
        return "NONE"
    return "FULL"


def _filled_quantity(fill_status: str, size: float, liquidity: dict[str, Any]) -> float:
    if fill_status == "FULL":
        return round(size, 6)
    if fill_status == "PARTIAL":
        return round(size * (1.0 - numeric(liquidity.get("partial_fill_probability_proxy"), 0.35) / 2.0), 6)
    return 0.0


def _fill_price(order: dict[str, Any], cost: dict[str, Any], maker_taker: str) -> float:
    base = numeric(order.get("simulated_price"), 0.5)
    adjustment = numeric(cost.get("slippage_cost"), 0.0) / (2.0 if maker_taker == "MAKER" else 1.0)
    return round(min(0.99, max(0.01, base + adjustment)), 6)
