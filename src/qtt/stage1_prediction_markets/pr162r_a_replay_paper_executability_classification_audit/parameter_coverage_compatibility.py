"""Parameter coverage compatibility records."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type


def parameter_coverage_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        defaults = record.get("default_parameter_candidates") or record.get("parameter_ranges_defaults") or {}
        if record.get("default_value_candidate") is not None:
            defaults = {"default_value_candidate": record.get("default_value_candidate")}
        rows.append(
            {
                "candidate_id": candidate_id(record),
                "candidate_type": candidate_type(record),
                "default_or_range_present_flag": bool(defaults or record.get("valid_range") or record.get("parameter_ranges")),
                "default_parameter_candidates": defaults,
                "valid_range": record.get("valid_range") or record.get("parameter_ranges") or record.get("parameter_ranges_defaults") or {},
                "parameter_coverage_status": "PARAMETER_COVERED_OR_NOT_REQUIRED",
                "calibration_needed_noncritical_flag": candidate_type(record) == "PARAMETER",
                "live_order_authority": False,
            }
        )
    return rows
