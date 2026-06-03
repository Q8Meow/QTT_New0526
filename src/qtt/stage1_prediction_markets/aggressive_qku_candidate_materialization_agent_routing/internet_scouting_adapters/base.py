"""Base source scouting adapter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoutAdapter:
    adapter_id: str
    source_tier: str
    source_class: str
    network_required_for_ci: bool = False

    def dry_run(self) -> dict[str, object]:
        return {
            "adapter_id": self.adapter_id,
            "source_tier": self.source_tier,
            "source_class": self.source_class,
            "network_required_for_ci": self.network_required_for_ci,
            "retrieval_status": "DRY_RUN_LOCATOR_CLASSIFICATION_ONLY",
        }
