"""AtomicRows source/profit readiness aggregate records."""

from __future__ import annotations

from typing import Any, Mapping


def build_atomicrows_source_profit_readiness_records(
    atomicrows_candidate_records: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "atomicrows_source_profit_readiness_id": f"PR159S_ATOMICROWS_SOURCE_PROFIT__{index:04d}",
            "target_id_or_row_id": record["target_id_or_row_id"],
            "target_field_id": record["target_field_id"],
            "source_provenance_tag": record["source_provenance_tag"],
            "profit_validation_tag": record["profit_validation_tag"],
            "row_level_aggregate_provenance_tag": record["row_level_aggregate_provenance_tag"],
            "atomicrows_official_source_ready": record["atomicrows_official_source_ready"],
            "atomicrows_research_candidate_ready": record["atomicrows_research_candidate_ready"],
            "atomicrows_replay_paper_candidate_ready": record["atomicrows_replay_paper_candidate_ready"],
            "atomicrows_profit_proven_ready": record["atomicrows_profit_proven_ready"],
            "atomicrows_non_profitable_retired": record["atomicrows_non_profitable_retired"],
            "atomicrows_quantum_candidate_ready": record["atomicrows_quantum_candidate_ready"],
            "atomicrows_owner_policy_ready": record["atomicrows_owner_policy_ready"],
            "atomicrows_connector_fact_pending": record["atomicrows_connector_fact_pending"],
            "atomicrows_live_use_pending": record["atomicrows_live_use_pending"],
        }
        for index, record in enumerate(atomicrows_candidate_records, start=1)
    ]

