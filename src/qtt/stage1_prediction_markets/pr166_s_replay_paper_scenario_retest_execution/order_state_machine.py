"""Deterministic simulated order state transitions for PR166-S."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import ordinal_ref, stable_ref
from .execution_cost_engine import by_candidate
from .input_consumption import row_contract


def build_order_state_transition_rows(
    order_rows: list[dict[str, Any]],
    fill_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    fills = by_candidate(fill_rows)
    costs = by_candidate(cost_rows)
    rows: list[dict[str, Any]] = []
    transition_index = 0
    for order in order_rows:
        cid = str(order["candidate_packet_id"])
        fill = fills[cid]
        cost = costs[cid]
        states = _states_for(order, fill, cost)
        previous = "START"
        for state_index, state in enumerate(states, start=1):
            transition_index += 1
            row_id = ordinal_ref("PR166_S_ORDER_STATE_TRANSITION", transition_index)
            rows.append(
                {
                    "order_state_transition_id": row_id,
                    "order_intent_id": order["order_intent_id"],
                    "candidate_packet_id": cid,
                    "transition_sequence": state_index,
                    "from_state": previous,
                    "to_state": state,
                    "transition_time": f"PR166_S_TIME::{transition_index:06d}::{state}",
                    "transition_reason": _reason_for_state(state, fill, cost),
                    "state_machine_scope": "REPLAY_AND_PAPER_SIMULATED_ONLY",
                    "no_live_authority": True,
                    **row_contract(
                        row_id=row_id,
                        source_artifact_ref="PR166_S_OrderIntentRegistry.report.json",
                        source_row_ref=order["order_intent_id"],
                        computed_by_module="order_state_machine",
                        owning_agent="execution_simulation_agent",
                        consuming_agent="risk_agent",
                        downstream_action_type="simulated order state transition input",
                        downstream_artifact_route="PR166_S_SimulatedFillLedger.report.json",
                    ),
                }
            )
            previous = state
    return rows


def _states_for(order: dict[str, Any], fill: dict[str, Any], cost: dict[str, Any]) -> list[str]:
    states = ["INTENT_CREATED", "REPLAY_SUBMITTED", "PAPER_SUBMITTED"]
    states.append("MAKER_RESTING" if order.get("order_type") == "SIMULATED_POST_ONLY" else "TAKER_SUBMITTED")
    fill_status = str(fill.get("fill_status"))
    states.append(
        {
            "FULL": "FULLY_FILLED",
            "PARTIAL": "PARTIALLY_FILLED",
            "NONE": "NO_FILL",
            "CANCELLED": "CANCELLED",
            "EXPIRED": "EXPIRED",
            "REJECTED": "REJECTED_BY_SIMULATED_RULE",
            "LATENCY_MISSED": "LATENCY_MISSED",
            "LIQUIDITY_INSUFFICIENT": "LIQUIDITY_INSUFFICIENT",
        }[fill_status]
    )
    if str(cost.get("post_cost_classification")) == "GROSS_EDGE_POSITIVE_BUT_COST_DOMINATED":
        states.append("COST_DOMINATED")
    if str(cost.get("post_cost_classification")) == "SETTLEMENT_ASSUMPTION_SENSITIVE":
        states.append("SETTLEMENT_ASSUMPTION_REQUIRED")
    states.extend(["RESULT_ATTRIBUTED", "SCORE_REFRESH_CANDIDATE_CREATED", "MEMORY_REFRESH_CANDIDATE_CREATED"])
    if cost.get("post_cost_pass_fail_classification") == "FAIL":
        states.append("REPAIR_FEEDBACK_CREATED")
    return states


def _reason_for_state(state: str, fill: dict[str, Any], cost: dict[str, Any]) -> str:
    if state in {"FULLY_FILLED", "PARTIALLY_FILLED", "NO_FILL", "LATENCY_MISSED", "LIQUIDITY_INSUFFICIENT"}:
        return f"SIMULATED_FILL_STATUS::{fill.get('fill_status')}"
    if state == "COST_DOMINATED":
        return "NET_EDGE_AFTER_COSTS_NON_POSITIVE"
    if state == "SETTLEMENT_ASSUMPTION_REQUIRED":
        return "SETTLEMENT_PAYOFF_ASSUMPTION_DRIVES_RESULT_SENSITIVITY"
    return f"DETERMINISTIC_STATE::{state}"
