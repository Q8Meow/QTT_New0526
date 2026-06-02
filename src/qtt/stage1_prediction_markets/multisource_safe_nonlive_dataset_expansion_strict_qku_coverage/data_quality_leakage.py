"""PR162C data quality, leakage, and time-window audits."""

from __future__ import annotations

from typing import Any

from . import constants as c


def provided_required_fields(normalized_rows: list[dict[str, Any]]) -> list[str]:
    provided: set[str] = set()
    for row in normalized_rows:
        for normalized_field, required_fields in c.PR162A_NORMALIZED_TO_REQUIRED_FIELD_MAP.items():
            if row.get(normalized_field) is not None:
                provided.update(required_fields)
    return sorted(provided)


def leakage_audit_records(normalized_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    provided = provided_required_fields(normalized_rows)
    post_separated = not any(field in provided for field in c.POST_RESOLUTION_FIELDS)
    return [
        {
            "audit_id": "PR162C-DATA-QUALITY-LEAKAGE-AUDIT-PR162A-KALSHI-TINY",
            "dataset_id": c.DATASET_IDS[0],
            "row_count": len(normalized_rows),
            "time_window_start": normalized_rows[0]["timestamp"] if normalized_rows else None,
            "time_window_end": normalized_rows[-1]["timestamp"] if normalized_rows else None,
            "provided_input_fields": provided,
            "pre_resolution_features_present": True,
            "post_resolution_labels_separated": post_separated,
            "leakage_audit_status": "PASS" if post_separated else "BLOCKED_LEAKAGE_RISK",
            "row_count_threshold_pass": len(normalized_rows) >= c.MIN_STRICT_ROW_COUNT,
            "created_by_pr": c.PR_ID,
        }
    ]
