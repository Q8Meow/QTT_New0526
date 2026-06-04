"""Formula runtime compatibility records."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type


def formula_runtime_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        if candidate_type(record) != "FORMULA":
            continue
        rows.append(
            {
                "candidate_id": candidate_id(record),
                "formula_family": record.get("formula_family"),
                "expression_present_flag": bool(record.get("expression")),
                "deterministic_runtime_reference": record.get("deterministic_implementation_function_reference"),
                "runtime_compatibility_status": "FORMULA_RUNTIME_COMPATIBLE_FOR_REPLAY_PAPER_INPUT",
                "live_order_authority": False,
            }
        )
    return rows
