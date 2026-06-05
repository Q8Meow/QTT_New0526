"""Priority queue construction for PR162R-B binding tasks."""

from __future__ import annotations

from typing import Any


FAMILY_PRIORITY_BONUS = {
    "PAPER_MARKET_STATE_BINDING": 0.18,
    "PAPER_SYNTHETIC_FILL_MODEL": 0.18,
    "PAPER_PORTFOLIO_STATE": 0.18,
    "PAPER_EXECUTION_COST_MODEL": 0.18,
    "HISTORICAL_ORDERBOOK_SNAPSHOT_SERIES": 0.14,
    "HISTORICAL_TRADE_SERIES": 0.12,
    "HISTORICAL_PRICE_SERIES": 0.12,
    "SETTLEMENT_OUTCOME_LABELS": 0.12,
    "EVENT_STATE_TIMELINE": 0.10,
    "QUANTUM_OBJECTIVE_INPUTS": 0.10,
    "QUANTUM_CONSTRAINT_INPUTS": 0.10,
    "QUANTUM_VARIABLE_DOMAIN_INPUTS": 0.08,
}


def build_priority_rows(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(
        tasks,
        key=lambda task: (
            -float(task.get("priority_score", 0.0)) - FAMILY_PRIORITY_BONUS.get(str(task.get("binding_family")), 0.0),
            str(task.get("binding_task_id")),
        ),
    )
    rows: list[dict[str, Any]] = []
    for rank, task in enumerate(ranked, start=1):
        score = round(float(task.get("priority_score", 0.0)) + FAMILY_PRIORITY_BONUS.get(str(task.get("binding_family")), 0.0), 4)
        rows.append(
            {
                "priority_queue_id": f"PR162R_B_DATA_BINDING_PRIORITY::{rank:04d}",
                "binding_task_ref": task["binding_task_id"],
                "binding_family": task["binding_family"],
                "venue_scope": task["venue_scope"],
                "expected_rows_resolved": task["expected_rows_resolved"],
                "priority_score": score,
                "priority_reason": "Materializes reusable replay/paper binding and fans out to impacted CandidatePacketV1 rows.",
                "materialization_status": task["materialization_status"],
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows
