"""Dataset binding compatibility records."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type


def dataset_binding_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        cid = candidate_id(record)
        ctype = candidate_type(record)
        status = "DATASET_BINDING_COMPATIBLE"
        if not (record.get("field_mapping") or record.get("input_fields")):
            status = "DATASET_BINDING_REQUIRES_FIELD_REVIEW"
        rows.append(
            {
                "candidate_id": cid,
                "candidate_type": ctype,
                "dataset_binding_status": status,
                "source_locator": record.get("source_locator"),
                "input_fields": record.get("input_fields") or [],
                "field_mapping": record.get("field_mapping") or {},
                "replay_dataset_binding_flag": True,
                "paper_data_binding_flag": True,
                "live_order_authority": False,
            }
        )
    return rows
