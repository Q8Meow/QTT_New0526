"""Source snapshot cache manifest helpers."""

from __future__ import annotations

from .online_source_scouting import online_scouting_records


def cached_source_snapshot_manifest_records() -> list[dict[str, object]]:
    return [
        {
            **record,
            "cache_mode": "LOCATOR_AND_CLASSIFICATION_CACHE_NO_LIVE_CI_FETCH",
            "source_content_embedded_flag": False,
        }
        for record in online_scouting_records()
    ]
