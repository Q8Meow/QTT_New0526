from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .family_j import FormulaDomainError
from .policy import STABLE_VALIDATOR_RULE_IDS


def _require(condition: bool, rule_id: str) -> bool:
    if not condition:
        raise FormulaDomainError(f"INVARIANT_VIOLATION:{rule_id}")
    return True


def midpoint_or_last_trade_cannot_create_realized_profit(row: Mapping[str, Any]) -> bool:
    return _require(not row.get("realized_delta") or bool(row.get("fill_or_settlement_receipt")), STABLE_VALIDATOR_RULE_IDS[0])


def exit_profit_remains_projected_until_exit_fill(row: Mapping[str, Any]) -> bool:
    realized = row.get("state") in {"REALIZED_PAPER_EXIT_NET_CASH", "REALIZED_PAPER_SETTLEMENT_NET_CASH"}
    return _require(not realized or bool(row.get("fill_or_settlement_receipt") and row.get("ledger_reconciled")), STABLE_VALIDATOR_RULE_IDS[1])


def spread_slippage_impact_cannot_be_double_counted(row: Mapping[str, Any]) -> bool:
    component_ids=list(row.get("cost_component_ids",()))
    return _require(len(component_ids)==len(set(component_ids)) and abs(float(row.get("reconciliation_residual",0)))<=float(row.get("tolerance",0)), STABLE_VALIDATOR_RULE_IDS[2])


def one_positive_trade_cannot_authorize_unrestricted_scaling(row: Mapping[str, Any]) -> bool:
    return _require(not row.get("scale_authorized") or all(row.get(key) for key in ("evidence_pass","capacity_pass","risk_pass","owner_envelope_pass")), STABLE_VALIDATOR_RULE_IDS[3])


def hold_until_breakeven_cannot_be_the_default_loss_policy(row: Mapping[str, Any]) -> bool:
    return _require(row.get("default_action")!="HOLD_UNTIL_BREAKEVEN" and row.get("selected_action")==max(row["forward_values"],key=row["forward_values"].get), STABLE_VALIDATOR_RULE_IDS[4])


def reentry_requires_a_new_positive_edge_determination(row: Mapping[str, Any]) -> bool:
    return _require(not row.get("reentry_allowed") or all(row.get(key) for key in ("fresh_edge","cooldown_pass","state_change","capacity_pass")), STABLE_VALIDATOR_RULE_IDS[5])


def campaign_children_share_aggregate_capacity_and_exposure(row: Mapping[str, Any]) -> bool:
    children=list(row.get("children",()))
    used=sum(float(child["filled_quantity"]) for child in children)
    return _require(len({child["parent_campaign_id"] for child in children})<=1 and abs(float(row["initial_capacity"])-used-float(row["remaining_capacity"]))<=1e-9, STABLE_VALIDATOR_RULE_IDS[6])


def trade_frequency_cannot_be_used_as_an_objective_without_net_cash_utility(row: Mapping[str, Any]) -> bool:
    winner=max(row["candidates"],key=lambda candidate:(candidate["robust_net_cash"],-candidate["trade_count"]))
    return _require(row["selected_candidate_id"]==winner["candidate_id"], STABLE_VALIDATOR_RULE_IDS[7])


def fixed_seven_day_duration_cannot_be_universal(row: Mapping[str, Any]) -> bool:
    return _require(not (row.get("universal_default") and row.get("duration_days")==7) and row.get("stop_policy") in {"EVIDENCE_EVENT_OWNER_BOUNDED","NOT_APPLICABLE"}, STABLE_VALIDATOR_RULE_IDS[8])


def paper_loop_cannot_submit_live_orders(row: Mapping[str, Any]) -> bool:
    return _require(row.get("mode")!="PAPER" or not any(row.get(key) for key in ("connector_write","venue_submit","execution_router_release")), STABLE_VALIDATOR_RULE_IDS[9])


def quantum_output_cannot_bypass_execution_router(row: Mapping[str, Any]) -> bool:
    return _require(not row.get("quantum_direct_order_release") and row.get("authority_state") in {"CANDIDATE_ONLY","EVIDENCE_ONLY"}, STABLE_VALIDATOR_RULE_IDS[10])


RULE_FUNCTIONS: dict[str, Callable[[Mapping[str, Any]], bool]] = {
    "midpoint_or_last_trade_cannot_create_realized_profit": midpoint_or_last_trade_cannot_create_realized_profit,
    "exit_profit_remains_projected_until_exit_fill": exit_profit_remains_projected_until_exit_fill,
    "spread_slippage_impact_cannot_be_double_counted": spread_slippage_impact_cannot_be_double_counted,
    "one_positive_trade_cannot_authorize_unrestricted_scaling": one_positive_trade_cannot_authorize_unrestricted_scaling,
    "hold_until_breakeven_cannot_be_the_default_loss_policy": hold_until_breakeven_cannot_be_the_default_loss_policy,
    "reentry_requires_a_new_positive_edge_determination": reentry_requires_a_new_positive_edge_determination,
    "campaign_children_share_aggregate_capacity_and_exposure": campaign_children_share_aggregate_capacity_and_exposure,
    "trade_frequency_cannot_be_used_as_an_objective_without_net_cash_utility": trade_frequency_cannot_be_used_as_an_objective_without_net_cash_utility,
    "fixed_seven_day_duration_cannot_be_universal": fixed_seven_day_duration_cannot_be_universal,
    "paper_loop_cannot_submit_live_orders": paper_loop_cannot_submit_live_orders,
    "quantum_output_cannot_bypass_execution_router": quantum_output_cannot_bypass_execution_router,
}


def valid_fixture(rule_id: str) -> dict[str, Any]:
    fixtures={
        STABLE_VALIDATOR_RULE_IDS[0]:{"realized_delta":0,"fill_or_settlement_receipt":None},
        STABLE_VALIDATOR_RULE_IDS[1]:{"state":"PROJECTED_EXECUTABLE_NET_CASH","fill_or_settlement_receipt":None,"ledger_reconciled":False},
        STABLE_VALIDATOR_RULE_IDS[2]:{"cost_component_ids":["spread","fee"],"reconciliation_residual":0,"tolerance":0},
        STABLE_VALIDATOR_RULE_IDS[3]:{"scale_authorized":True,"evidence_pass":True,"capacity_pass":True,"risk_pass":True,"owner_envelope_pass":True},
        STABLE_VALIDATOR_RULE_IDS[4]:{"default_action":"FORWARD_VALUE_MAX","forward_values":{"EXIT":1,"HOLD":0},"selected_action":"EXIT"},
        STABLE_VALIDATOR_RULE_IDS[5]:{"reentry_allowed":True,"fresh_edge":True,"cooldown_pass":True,"state_change":True,"capacity_pass":True},
        STABLE_VALIDATOR_RULE_IDS[6]:{"initial_capacity":10,"remaining_capacity":7,"children":[{"parent_campaign_id":"P","filled_quantity":1},{"parent_campaign_id":"P","filled_quantity":2}]},
        STABLE_VALIDATOR_RULE_IDS[7]:{"selected_candidate_id":"cash","candidates":[{"candidate_id":"cash","robust_net_cash":2,"trade_count":1},{"candidate_id":"frequency","robust_net_cash":1,"trade_count":10}]},
        STABLE_VALIDATOR_RULE_IDS[8]:{"universal_default":False,"duration_days":7,"stop_policy":"EVIDENCE_EVENT_OWNER_BOUNDED"},
        STABLE_VALIDATOR_RULE_IDS[9]:{"mode":"PAPER","connector_write":False,"venue_submit":False,"execution_router_release":False},
        STABLE_VALIDATOR_RULE_IDS[10]:{"quantum_direct_order_release":False,"authority_state":"CANDIDATE_ONLY"},
    }
    return fixtures[rule_id]


def invalid_fixture(rule_id: str) -> dict[str, Any]:
    row=dict(valid_fixture(rule_id))
    mutators={
        STABLE_VALIDATOR_RULE_IDS[0]:lambda value:value.update(realized_delta=1),
        STABLE_VALIDATOR_RULE_IDS[1]:lambda value:value.update(state="REALIZED_PAPER_EXIT_NET_CASH"),
        STABLE_VALIDATOR_RULE_IDS[2]:lambda value:value.update(cost_component_ids=["spread","spread"]),
        STABLE_VALIDATOR_RULE_IDS[3]:lambda value:value.update(evidence_pass=False),
        STABLE_VALIDATOR_RULE_IDS[4]:lambda value:value.update(default_action="HOLD_UNTIL_BREAKEVEN"),
        STABLE_VALIDATOR_RULE_IDS[5]:lambda value:value.update(fresh_edge=False),
        STABLE_VALIDATOR_RULE_IDS[6]:lambda value:value.update(remaining_capacity=10),
        STABLE_VALIDATOR_RULE_IDS[7]:lambda value:value.update(selected_candidate_id="frequency"),
        STABLE_VALIDATOR_RULE_IDS[8]:lambda value:value.update(universal_default=True),
        STABLE_VALIDATOR_RULE_IDS[9]:lambda value:value.update(venue_submit=True),
        STABLE_VALIDATOR_RULE_IDS[10]:lambda value:value.update(quantum_direct_order_release=True),
    }
    mutators[rule_id](row)
    return row
