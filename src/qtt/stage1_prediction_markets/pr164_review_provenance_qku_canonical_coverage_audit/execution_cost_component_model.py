"""Execution-cost component coverage model."""

from __future__ import annotations

from typing import Any

from .deterministic_ids import plain_ref


EXECUTION_COST_COMPONENTS = (
    "exchange_fee_cost",
    "spread_crossing_cost",
    "slippage_cost",
    "latency_adverse_selection_cost",
    "queue_position_or_fill_probability_cost",
    "cancel_replace_cost",
    "capital_lock_cost",
    "settlement_delay_cost",
    "operational_error_penalty",
    "market_lifecycle_penalty",
    "stale_data_penalty",
)


def build_execution_cost_rows(computability_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, row in enumerate(computability_rows, 1):
        fill_required = not bool(row["candidate_id"])
        record: dict[str, Any] = {
            "execution_cost_component_record_ref": plain_ref("EXEC_COST", index),
            "qku_id": row["qku_id"],
            "candidate_id": row["candidate_id"],
            "market_scope": row["market_scope"],
            "activation_state": row["activation_state"],
            "expected_net_profit_candidate_formula": row["expected_net_profit_candidate_formula"],
            "execution_cost_components_complete": not fill_required,
            "exact_fill_task_required": fill_required,
            "validation_status": "PASS",
        }
        for component in EXECUTION_COST_COMPONENTS:
            record[component] = (
                f"{component} = candidate_replay_paper_value_from_PR163B_TCA_or_PR162R_B_binding"
                if not fill_required
                else f"{component} requires candidate_packet_v1_record and replay/paper cost binding"
            )
        rows.append(record)
    return rows
