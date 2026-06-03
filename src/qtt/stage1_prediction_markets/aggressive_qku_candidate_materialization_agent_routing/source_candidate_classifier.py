"""Source candidate classification helpers."""

from __future__ import annotations

from .source_quality_policy import authority_for_source, confidence_for_source


def classify_source_candidate(record: dict[str, object]) -> dict[str, object]:
    source_tier = str(record["source_tier"])
    source_class = str(record["source_class"])
    return {
        "source_id": record["source_id"],
        "authority_class": authority_for_source(source_tier, source_class),
        "confidence_class": confidence_for_source(source_tier, source_class),
        "candidate_or_provisional_flag": True,
        "replay_paper_candidate_flag": True,
        "acquisition_gate_flag": False,
    }
