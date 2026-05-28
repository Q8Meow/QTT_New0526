"""PR158 selection-readiness source update metadata for PR159."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build_selection_updates(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for record in records:
        ready = record["completion_status"] == c.SourceTargetState.ACCEPTED_COMPLETED.value
        updates.append(
            {
                "row_id": record["row_id"],
                "accepted_source_packet_ref_or_null": record["accepted_source_packet_ref_or_null"],
                "source_ready_flag": ready,
                "source_revalidation_class": record["revalidation_class"],
                "scoring_readiness_impact": "SOURCE_READY_METADATA_ONLY" if ready else "SOURCE_REQUIRED_BLOCKED",
                "trade_context_readiness_impact": "SOURCE_READY_METADATA_ONLY" if ready else "SOURCE_REQUIRED_BLOCKED",
                "low_latency_precomputed_index_eligibility_impact": "SOURCE_READY_METADATA_ONLY" if ready else "BLOCKED_FROM_LOW_LATENCY_LIVE_PATH",
                "no_scoring_ranking_selection_execution": True,
                "no_optimizer_execution": True,
                "no_quantum_backend_execution": True,
                "no_live_order_authority": True,
            }
        )
    return sorted(updates, key=lambda item: item["row_id"])

