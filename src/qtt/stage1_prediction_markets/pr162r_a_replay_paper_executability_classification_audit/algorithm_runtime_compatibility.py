"""Algorithm runtime compatibility records."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type


def algorithm_runtime_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        if candidate_type(record) != "ALGORITHM":
            continue
        rows.append(
            {
                "candidate_id": candidate_id(record),
                "algorithm_family": record.get("algorithm_family"),
                "deterministic_steps_present_flag": bool(record.get("deterministic_steps")),
                "parameter_ranges_present_flag": bool(record.get("parameter_ranges")),
                "runtime_compatibility_status": "ALGORITHM_RUNTIME_COMPATIBLE_FOR_NONLIVE_INPUT_PREP",
                "live_order_authority": False,
            }
        )
    return rows
