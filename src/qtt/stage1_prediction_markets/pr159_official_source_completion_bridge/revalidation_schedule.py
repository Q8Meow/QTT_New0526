"""Source revalidation schedule construction for PR159."""

from __future__ import annotations

from typing import Any, Mapping


def build_revalidation_schedule(target_queue: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "target_id": target["target_id"],
            "target_field_id": target["target_field_id"],
            "source_population": target["source_population"],
            "revalidation_class": target["revalidation_class"],
            "event_triggered_revalidation_required": True,
            "revalidation_before_connector_binding_required": True,
            "live_authority_created": False,
        }
        for target in sorted(target_queue, key=lambda item: item["target_id"])
    ]

