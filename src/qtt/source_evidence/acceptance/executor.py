from __future__ import annotations

from typing import Any, Mapping

from .validator import ExecuteAcceptanceResult, build_acceptance_artifacts


def execute_acceptance_input(input_record: Mapping[str, Any]) -> ExecuteAcceptanceResult:
    candidate = input_record.get("candidate_source_evidence_packet")
    if not isinstance(candidate, Mapping):
        candidate = {
            "candidate_source_evidence_packet_id": "UNKNOWN_CANDIDATE",
            "target_field_path": "UNKNOWN_TARGET",
        }
    return build_acceptance_artifacts(candidate)
