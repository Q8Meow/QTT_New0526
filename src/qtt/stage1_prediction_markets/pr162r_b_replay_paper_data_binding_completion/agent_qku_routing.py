"""Agent-consumable QKU/formula/algorithm routing matrix."""

from __future__ import annotations

from typing import Any


def build_agent_qku_routing_rows(row_resolution: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in row_resolution:
        rows.append(
            {
                "routing_id": f"PR162R_B_QKU_FORMULA_ALGORITHM_AGENT_ROUTE::{len(rows) + 1:05d}",
                "candidate_packet_id": row["candidate_packet_id"],
                "qku_ids": row["qku_ids"],
                "formulation_ref": row["formulation_ref"],
                "callable_ref": row["callable_ref"],
                "binding_task_refs": row["binding_task_refs"],
                "replay_binding_refs": row["replay_binding_refs"],
                "paper_binding_refs": row["paper_binding_refs"],
                "quantum_binding_refs": row["quantum_binding_refs"],
                "classical_comparator_binding_refs": row["classical_comparator_binding_refs"],
                "upstream_refs": row["upstream_refs"],
                "downstream_refs": row["downstream_refs"],
                "agent_refs": row["agent_refs"],
                "orphan_flag": False,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows
