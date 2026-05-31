"""Authenticity classifier for PR161E result-like artifacts."""

from __future__ import annotations

from typing import Any


def authenticity_records(discovery_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source in discovery_records:
        records.append(
            {
                "record_id": source["record_id"].replace("RESULT-DISCOVERY", "AUTHENTICITY"),
                "pr_label": source["pr_label"],
                "source_artifact_path": source["source_artifact_path"],
                "source_artifact_class": source["source_artifact_class"],
                "result_authenticity_class": source["result_authenticity_class"],
                "validation_state": "NO_VALIDATED_RESULT_ARTIFACT",
                "evidence_state": "NO_EVIDENCE",
                "accepted_as_real_qtt_replay_paper_result_flag": False,
                "rejection_or_pending_reason": _reason(source["source_artifact_class"]),
                "no_profit_evidence_created_without_validated_result_packet_flag": True,
                "no_live_profit_evidence_created_flag": True,
            }
        )
    return records


def _reason(artifact_class: str) -> str:
    if artifact_class == "SCHEMA_ONLY_ARTIFACT":
        return "SCHEMA_ONLY_NOT_RESULT_EVIDENCE"
    if artifact_class == "CONTRACT_ONLY_ARTIFACT":
        return "CONTRACT_ONLY_NOT_RESULT_EVIDENCE"
    if artifact_class == "SYNTHETIC_TEST_FIXTURE_RESULT_PACKET":
        return "SYNTHETIC_FIXTURE_NOT_REAL_QTT_PERFORMANCE_EVIDENCE"
    if artifact_class == "PRE_RESULT_RANKING_ARTIFACT":
        return "PR161D_PRE_RESULT_PRIORITY_SURFACE_NOT_RESULT_PACKET"
    if artifact_class.startswith("ACTUAL_"):
        return "ACTUAL_RESULT_CANDIDATE_REQUIRES_SCHEMA_VALIDATION_AND_QKU_MAPPING"
    return "NO_RESULT_ARTIFACT"
