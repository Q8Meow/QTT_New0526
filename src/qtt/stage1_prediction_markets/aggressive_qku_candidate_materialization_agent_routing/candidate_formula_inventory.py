"""Combined formula, algorithm, and value inventory helpers."""

from __future__ import annotations

from typing import Any


def combined_candidate_inventory(
    formulas: list[dict[str, Any]],
    algorithms: list[dict[str, Any]],
    parameters: list[dict[str, Any]],
    solvers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for kind, values in (
        ("FORMULA", formulas),
        ("ALGORITHM", algorithms),
        ("PARAMETER", parameters),
        ("SOLVER_INPUT", solvers),
    ):
        for record in values:
            records.append(
                {
                    "inventory_id": f"PR162D-CANDIDATE-INVENTORY-{kind}-{len(records) + 1:05d}",
                    "candidate_kind": kind,
                    "candidate_ref": record.get("candidate_id") or record.get("solver_input_candidate_id"),
                    "qku_refs": record.get("qku_refs") or [record.get("qku_id")],
                    "formula_refs": record.get("formula_refs") or [],
                    "algorithm_refs": record.get("algorithm_refs") or [],
                    "agent_route_refs": record.get("agent_route_refs") or ["REPLAY_PAPER_CANDIDATE_ROUTER"],
                    "metadata_only_flag": False,
                    "live_order_authority": False,
                }
            )
    return records
