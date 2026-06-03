"""Offline-safe source snapshot manifest."""

from __future__ import annotations

from typing import Any


def offline_safe_source_snapshot_records(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "snapshot_id": f"PR162D_R1_OFFLINE_SAFE_SNAPSHOT_{index:03d}",
            "source_id": source["source_id"],
            "source_locator": source["source_locator"],
            "snapshot_mode": "LOCATOR_AND_FIELD_SUMMARY_ONLY_NO_PRIVATE_STATE_NO_LIVE_NETWORK_IN_CI",
            "stored_private_state_flag": False,
            "stored_secret_flag": False,
            "ci_network_required_flag": False,
            "live_order_authority": False,
        }
        for index, source in enumerate(sources, start=1)
    ]
