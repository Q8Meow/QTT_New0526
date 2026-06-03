"""Source locator registry builder."""

from __future__ import annotations

from typing import Any


def source_locator_records(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_id": source["source_id"],
            "source_locator": source["source_locator"],
            "source_tier": source["source_tier"],
            "source_class": source["source_class"],
            "authority_class": source["authority_class"],
            "confidence_class": source["confidence_class"],
            "offline_safe_snapshot_flag": True,
            "live_order_authority": False,
        }
        for source in sources
    ]
