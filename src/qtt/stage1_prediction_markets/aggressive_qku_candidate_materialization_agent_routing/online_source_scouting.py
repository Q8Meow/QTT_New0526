"""Offline-safe record of online scouting performed for PR162D."""

from __future__ import annotations

from .source_intake import candidate_source_records


def online_scouting_records() -> list[dict[str, object]]:
    records = []
    for source in candidate_source_records():
        records.append(
            {
                "snapshot_id": str(source["source_id"]).replace("SOURCE", "SOURCE-SNAPSHOT"),
                "source_id": source["source_id"],
                "source_locator": source["source_locator"],
                "retrieval_status": source["retrieval_status"],
                "source_tier": source["source_tier"],
                "authority_class": source["authority_class"],
                "confidence_class": source["confidence_class"],
                "candidate_route_refs": source["agent_route_refs"],
                "ci_network_dependency_flag": False,
                "source_capture_digest_or_locator_digest": source[
                    "source_capture_digest_or_locator_digest"
                ],
            }
        )
    return records
