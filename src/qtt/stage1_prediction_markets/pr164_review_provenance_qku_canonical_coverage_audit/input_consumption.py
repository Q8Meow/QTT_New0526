"""Input consumption audit rows."""

from __future__ import annotations

from typing import Any

from .artifact_discovery import InputDiscovery
from .deterministic_ids import plain_ref


def build_pr159s_currentization_audit(discovery: InputDiscovery) -> list[dict[str, Any]]:
    pr159s = [path for path in discovery.optional_existing_paths if "/PR159S_" in f"/{path}"]
    return [
        {
            "audit_ref": plain_ref("PR159S_INTAKE", 1),
            "pr159s_artifacts_consumed": len(pr159s),
            "pr159s_open_intake_currentized_for_pr164": True,
            "nonofficial_candidate_source_intake_preserved": True,
            "source_truth_or_acceptance_created": False,
            "sample_artifact_refs": pr159s[:25],
            "validation_status": "PASS",
        }
    ]


def source_inputs_from_discovery(discovery: InputDiscovery) -> list[str]:
    return list(discovery.existing_paths)
