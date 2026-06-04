"""Input/output/unit compatibility records."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type


def input_output_unit_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": candidate_id(record),
            "candidate_type": candidate_type(record),
            "input_fields_present_flag": bool(record.get("input_fields")),
            "output_fields_present_flag": bool(record.get("output_fields")),
            "units_present_flag": bool(record.get("units")),
            "input_fields": record.get("input_fields") or [],
            "output_fields": record.get("output_fields") or [],
            "units": record.get("units"),
            "unit_safety_status": "UNIT_SAFE_FOR_REPLAY_PAPER_CLASSIFICATION"
            if record.get("units")
            else "UNIT_REVIEW_REQUIRED",
            "live_order_authority": False,
        }
        for record in records
    ]
