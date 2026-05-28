"""Quantum/classical compatibility metadata updates for PR160."""

from __future__ import annotations

from typing import Any, Mapping


def build(decisions: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "quantum_compatibility_update_id": f"PR160_QUANTUM_COMPAT__{item['PR154_target_id']}",
            "PR154_target_id": item["PR154_target_id"],
            "final_route_class": item["final_route_class"],
            "quantum_classical_compatibility": item["quantum_classical_compatibility"],
            "quantum_metadata_only_no_backend_execution": True,
            "quantum_advantage_claim_created_flag": False,
            "optimizer_execution_created_flag": False,
            "future_route": item["future_pr_route"],
        }
        for item in decisions
    ]
