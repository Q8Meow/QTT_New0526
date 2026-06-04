"""Source locator compatibility records."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type


def source_locator_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": candidate_id(record),
            "candidate_type": candidate_type(record),
            "source_locator": record.get("source_locator"),
            "source_tier": record.get("source_tier"),
            "source_locator_present_flag": bool(record.get("source_locator")),
            "source_private_secret_illegal_flag": False,
            "source_locator_status": "SOURCE_LOCATOR_PRESENT",
            "live_order_authority": False,
        }
        for record in records
    ]
