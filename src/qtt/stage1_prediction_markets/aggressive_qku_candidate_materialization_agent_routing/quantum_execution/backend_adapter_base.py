"""Base backend adapter interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BackendAdapter:
    adapter_id: str
    adapter_family: str
    dry_run_only: bool = True

    def build_payload(self, problem: dict[str, Any]) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "adapter_family": self.adapter_family,
            "problem": problem,
            "dry_run_only": self.dry_run_only,
            "remote_submission_attempted_flag": False,
            "live_order_authority": False,
        }
