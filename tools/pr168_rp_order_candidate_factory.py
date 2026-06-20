#!/usr/bin/env python3
"""PreTradeDecisionCandidateV1 factory for PR168-RP."""

from __future__ import annotations

from typing import Any


ORDER_POLICIES = [
    "PASSIVE_MAKER_LIMIT",
    "MIDPOINT_IMPROVING_LIMIT",
    "AGGRESSIVE_MARKETABLE_LIMIT",
    "FAK_STYLE_IMMEDIATE_CANDIDATE",
    "SPLIT_ORDER_CHILD_SLICE",
    "WAIT_FOR_BETTER_SPREAD",
    "NO_TRADE_CANDIDATE",
]


def make_order_candidates(computed: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    metrics = computed["metrics"]
    micro = computed["microstructure"]
    for index, policy in enumerate(ORDER_POLICIES, start=1):
        candidate_id = f"PR168_RP_PRETRADE::{computed['result_ref']}::{index:02d}"
        no_trade = policy == "NO_TRADE_CANDIDATE"
        rows.append(
            {
                "candidate_id": candidate_id,
                "mode": "PAPER",
                "market_id": micro.get("market_id"),
                "event_id": computed.get("qku_id"),
                "venue": micro.get("venue"),
                "side": computed.get("side"),
                "quantity_candidate": 0.0 if no_trade else metrics["position_size"],
                "limit_price_candidate": None if no_trade else _policy_price(policy, micro),
                "worst_price_limit_candidate": None if no_trade else micro.get("worst_price_limit_candidate"),
                "order_type_candidate": policy,
                "time_in_force_candidate": _time_in_force(policy),
                "qku_refs": [computed.get("qku_id")],
                "formula_refs": computed.get("formula_ids", []),
                "algorithm_refs": ["PR168_RP_PRETRADE_SIMULATION_KERNEL"],
                "parameter_stack_refs": [computed.get("parameter_stack_ref", "PR168_RP_PARAMETER_STACK::REPLAY_PAPER")],
                "quantum_objective_refs": [computed.get("quantum_objective_ref")],
                "classical_fallback_refs": ["PR168_RP_CLASSICAL_FALLBACK_ONLY"],
                "input_snapshot_ref": computed.get("input_ref"),
                "scenario_set_ref": f"PR168_RP_SCENARIO_SET::{computed['result_ref']}",
                "computed_formula_output_ref": computed.get("output_ref"),
                "execution_adjusted_ranking_ref": "PR168_RP_OrderPolicyCandidateRanking.report.json",
                "no_trade_candidate_ref": f"PR168_RP_PRETRADE::{computed['result_ref']}::07",
                "no_trade_comparison_margin": 0.0,
                "latency_budget_ref": f"PR168_RP_LATENCY::{candidate_id}",
                "decision_status": "NO_TRADE_CANDIDATE_REQUIRED" if no_trade else "PRETRADE_SIMULATION_CANDIDATE_CREATED",
                "downstream_route": "PR168_RP_OrderPolicyCandidateRanking.report.json",
                "owning_agent": "Execution Simulation Agent",
                "consumer_agent": "Ranking Agent",
                "connector_candidate_route": computed.get("connector_candidate_route"),
                "connector_semantic_binding_state": "NOT_BOUND_CANDIDATE_ONLY",
                "source_truth_authority": False,
                "connector_truth_authority": False,
                "live_authority": False,
                "execution_router_required_future_gate": policy != "NO_TRADE_CANDIDATE",
                "no_orphan_status": "CONNECTED_TO_PRETRADE_RANKING_CONSUMER",
                "producer": "PR168_RP_ORDER_CANDIDATE_FACTORY",
                "consumer": "PR168_RANK",
                "upstream_source": computed.get("result_ref"),
            }
        )
    return rows


def _policy_price(policy: str, micro: dict[str, Any]) -> float:
    bid = float(micro["top_of_book_bid"])
    ask = float(micro["top_of_book_ask"])
    mid = float(micro["midpoint"])
    if policy == "PASSIVE_MAKER_LIMIT":
        return bid
    if policy == "MIDPOINT_IMPROVING_LIMIT":
        return mid
    if policy == "AGGRESSIVE_MARKETABLE_LIMIT":
        return ask
    if policy == "FAK_STYLE_IMMEDIATE_CANDIDATE":
        return ask
    if policy == "SPLIT_ORDER_CHILD_SLICE":
        return mid
    if policy == "WAIT_FOR_BETTER_SPREAD":
        return max(bid, mid - float(micro["spread"]) / 4.0)
    return mid


def _time_in_force(policy: str) -> str:
    if policy == "FAK_STYLE_IMMEDIATE_CANDIDATE":
        return "FAK_CANDIDATE_IF_FUTURE_VENUE_SUPPORTS"
    if policy == "PASSIVE_MAKER_LIMIT":
        return "GTC_CANDIDATE"
    if policy == "NO_TRADE_CANDIDATE":
        return "HOLD"
    return "IOC_OR_GTC_CANDIDATE_NONLIVE"
