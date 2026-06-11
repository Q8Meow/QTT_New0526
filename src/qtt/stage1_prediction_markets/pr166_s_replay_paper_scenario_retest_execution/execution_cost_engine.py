"""Execution cost and net-edge engine for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .input_consumption import row_contract
from .selected_batch_loader import ExecutionContext, clamp, numeric, ready_contexts


def by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["candidate_packet_id"]): row for row in rows if row.get("candidate_packet_id")}


def build_execution_cost_rows(
    contexts: list[ExecutionContext],
    fee_rows: list[dict[str, Any]],
    spread_rows: list[dict[str, Any]],
    slippage_rows: list[dict[str, Any]],
    latency_rows: list[dict[str, Any]],
    liquidity_rows: list[dict[str, Any]],
    impact_rows: list[dict[str, Any]],
    settlement_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    fees = by_candidate(fee_rows)
    spreads = by_candidate(spread_rows)
    slippages = by_candidate(slippage_rows)
    latencies = by_candidate(latency_rows)
    liquidities = by_candidate(liquidity_rows)
    impacts = by_candidate(impact_rows)
    settlements = by_candidate(settlement_rows)
    rows: list[dict[str, Any]] = []
    for index, context in enumerate(ready_contexts(contexts), start=1):
        cid = context.candidate_packet_id
        fee = fees[cid]
        spread = spreads[cid]
        slippage = slippages[cid]
        latency = latencies[cid]
        liquidity = liquidities[cid]
        impact = impacts[cid]
        settlement = settlements[cid]
        gross = round(
            numeric(
                context.expected.get("expected_value_candidate"),
                numeric(context.scenario.get("net_edge_candidate"), 0.0),
            ),
            6,
        )
        maker_fee = round(max(0.0, numeric(context.tca.get("fee_cost"), 0.0)) * 0.45, 6)
        taker_fee = round(max(0.0, numeric(context.tca.get("fee_cost"), 0.02)) * 0.55, 6)
        total_fee = round(maker_fee + taker_fee, 6)
        spread_cost = round(numeric(spread.get("upstream_spread_cost_candidate"), 0.04), 6)
        slippage_cost = round(numeric(slippage.get("slippage_cost_candidate"), 0.03), 6)
        market_impact_cost = round(numeric(impact.get("impact_bps_cost"), 0.012), 6)
        latency_drag = round(numeric(latency.get("latency_drag_score"), 0.35) * 0.02, 6)
        liquidity_drag = round(numeric(liquidity.get("liquidity_fragility_score"), 0.35) * 0.02, 6)
        adverse_selection_drag = round(numeric(context.scenario.get("adverse_selection_penalty"), 2.0) / 100.0, 6)
        settlement_adjustment = round(numeric(settlement.get("settlement_payoff_adjustment"), 0.0025), 6)
        total_cost = round(
            spread_cost
            + total_fee
            + slippage_cost
            + market_impact_cost
            + latency_drag
            + liquidity_drag
            + adverse_selection_drag
            + settlement_adjustment,
            6,
        )
        net_edge = round(gross - total_cost, 6)
        dominant = dominant_failure_driver(
            {
                "spread_cost": spread_cost,
                "maker_taker_fees": total_fee,
                "slippage_cost": slippage_cost,
                "market_impact_cost": market_impact_cost,
                "latency_drag": latency_drag,
                "liquidity_drag": liquidity_drag,
                "adverse_selection_drag": adverse_selection_drag,
                "settlement_payoff_adjustment": settlement_adjustment,
            }
        )
        classification = post_cost_classification(gross, net_edge, dominant)
        row_id = stable_ref("PR166_S_EXECUTION_COST", cid)
        rows.append(
            {
                "execution_cost_id": row_id,
                "order_intent_id": stable_ref("PR166_S_ORDER_INTENT", cid),
                "candidate_packet_id": cid,
                "qku_id": context.qku_id,
                "gross_edge": gross,
                "spread_cost": spread_cost,
                "maker_fee": maker_fee,
                "taker_fee": taker_fee,
                "maker_taker_fees": total_fee,
                "total_fee": total_fee,
                "slippage_cost": slippage_cost,
                "market_impact_cost": market_impact_cost,
                "latency_drag": latency_drag,
                "liquidity_drag": liquidity_drag,
                "adverse_selection_drag": adverse_selection_drag,
                "settlement_payoff_adjustment": settlement_adjustment,
                "net_edge_after_costs": net_edge,
                "TCA_adjusted_result": round(net_edge - numeric(context.selection_fdc.get("false_discovery_penalty"), 0.25) * 0.01, 6),
                "post_cost_pass_fail_classification": "PASS" if net_edge > 0 else "FAIL",
                "post_cost_classification": classification,
                "dominant_failure_driver": dominant,
                "fee_model_ref": fee["fee_model_id"],
                "spread_model_ref": spread["spread_model_id"],
                "slippage_model_ref": slippage["slippage_model_id"],
                "latency_model_ref": latency["latency_model_id"],
                "liquidity_model_ref": liquidity["liquidity_model_id"],
                "market_impact_model_ref": impact["market_impact_model_id"],
                "settlement_assumption_ref": settlement["settlement_assumption_id"],
                "net_edge_formula_ref": "net_edge_after_costs = gross_edge - spread_cost - maker_taker_fees - slippage_cost - market_impact_cost - latency_drag - liquidity_drag - adverse_selection_drag - settlement_payoff_adjustment",
                "no_profit_evidence": True,
                "replay_paper_only": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR165_D_RetestBatchSelectionQueue.report.json",
                    source_row_ref=context.retest["retest_batch_selection_id"],
                    computed_by_module="execution_cost_engine",
                    owning_agent="tca_agent",
                    consuming_agent="risk_agent",
                    downstream_action_type="execution cost and net-edge result input",
                    downstream_artifact_route="PR166_S_ResultAttributionLedger.report.json",
                    computation_formula_ref="PR166_S_NET_EDGE_AFTER_COSTS_FORMULA",
                ),
            }
        )
    return rows


def dominant_failure_driver(costs: dict[str, float]) -> str:
    driver = max(costs.items(), key=lambda item: (item[1], item[0]))[0]
    return {
        "spread_cost": "COST_DOMINATED",
        "maker_taker_fees": "COST_DOMINATED",
        "slippage_cost": "COST_DOMINATED",
        "market_impact_cost": "LIQUIDITY_DOMINATED",
        "latency_drag": "LATENCY_DOMINATED",
        "liquidity_drag": "LIQUIDITY_DOMINATED",
        "adverse_selection_drag": "ADVERSE_SELECTION_DOMINATED",
        "settlement_payoff_adjustment": "SETTLEMENT_ASSUMPTION_SENSITIVE",
    }[driver]


def post_cost_classification(gross_edge: float, net_edge: float, dominant: str) -> str:
    if gross_edge <= 0:
        return "LOW_CONFIDENCE_OR_NEGATIVE_GROSS_EDGE"
    if net_edge > 0:
        return "POSITIVE_NET_EDGE_AFTER_COSTS"
    if dominant == "LATENCY_DOMINATED":
        return "LATENCY_DOMINATED"
    if dominant == "LIQUIDITY_DOMINATED":
        return "LIQUIDITY_DOMINATED"
    if dominant == "ADVERSE_SELECTION_DOMINATED":
        return "ADVERSE_SELECTION_DOMINATED"
    if dominant == "SETTLEMENT_ASSUMPTION_SENSITIVE":
        return "SETTLEMENT_ASSUMPTION_SENSITIVE"
    return "GROSS_EDGE_POSITIVE_BUT_COST_DOMINATED"
