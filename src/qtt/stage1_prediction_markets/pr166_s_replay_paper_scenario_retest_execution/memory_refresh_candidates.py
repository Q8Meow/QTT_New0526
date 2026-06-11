"""Memory-refresh candidate packet builder for PR166-S."""

from __future__ import annotations

from typing import Any

from .input_consumption import row_contract


def build_memory_refresh_candidate_rows(attribution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, attr in enumerate(attribution_rows, start=1):
        row_id = f"PR166_S_MEMORY_REFRESH::{index:06d}"
        rows.append(
            {
                "memory_refresh_candidate_id": row_id,
                "candidate_packet_id": attr["candidate_packet_id"],
                "result_attribution_ref": attr["result_attribution_id"],
                "condition_fingerprint_id": attr["condition_fingerprint_id"],
                "combination_fingerprint_id": attr["combination_fingerprint_id"],
                "scenario_group_id": attr["scenario_group_id"],
                "memory_update_type": "POSITIVE_CONDITION_SCOPED_MEMORY_CANDIDATE" if attr["net_return_proxy"] > 0 else "NEGATIVE_COST_OR_EXECUTION_MEMORY_CANDIDATE",
                "memory_update_payload": {
                    "post_cost_classification": attr["post_cost_classification"],
                    "dominant_failure_driver": attr["dominant_failure_driver"],
                    "cost_drag_ratio": attr["cost_drag_ratio"],
                    "latency_drag_ratio": attr["latency_drag_ratio"],
                    "liquidity_drag_ratio": attr["liquidity_drag_ratio"],
                },
                "no_live_authority": True,
                "no_order_execution_authority": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_ResultAttributionLedger.report.json",
                    source_row_ref=attr["result_attribution_id"],
                    computed_by_module="memory_refresh_candidates",
                    owning_agent="memory_agent",
                    consuming_agent="memory_agent",
                    downstream_action_type="memory-refresh input",
                    downstream_artifact_route="score_memory_refresh_PR",
                    no_orphan_status="CONNECTED_TO_MEMORY_REFRESH_ROUTE",
                ),
            }
        )
    return rows
