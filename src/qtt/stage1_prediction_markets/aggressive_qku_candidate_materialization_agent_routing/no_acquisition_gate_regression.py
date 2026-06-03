"""No acquisition gate regression audit."""

from __future__ import annotations

from typing import Any


def no_acquisition_gate_regression_records(
    reinterpretations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    remaining = sum(
        1 for record in reinterpretations if record.get("generic_required_fields_blocker_remaining_flag")
    )
    return [
        {
            "record_id": "PR162D-NO-ACQUISITION-GATE-REGRESSION",
            "candidate_materialization_target_count": len(reinterpretations),
            "generic_required_fields_blocker_remaining_count": remaining,
            "non_official_source_quality_gate_count": 0,
            "partial_field_missing_gate_count": 0,
            "metadata_only_materialization_pass_count": 0,
            "audit_status": "PASS" if remaining == 0 else "FAIL",
        }
    ]
