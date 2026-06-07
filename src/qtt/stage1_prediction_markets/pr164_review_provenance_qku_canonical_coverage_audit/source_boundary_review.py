"""Source boundary review helpers."""

from __future__ import annotations

from typing import Any


def build_source_boundary_flags() -> dict[str, Any]:
    return {
        "source_truth_created": False,
        "source_acceptance_created": False,
        "connector_semantics_created": False,
        "nonofficial_values_candidate_only": True,
        "official_values_candidate_only_until_downstream_verified": True,
    }
