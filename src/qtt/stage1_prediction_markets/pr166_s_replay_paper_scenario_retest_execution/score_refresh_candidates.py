"""Score-refresh candidate packet builder for PR166-S."""

from __future__ import annotations

from typing import Any

from .execution_cost_engine import by_candidate
from .input_consumption import row_contract


def build_score_refresh_candidate_rows(
    attribution_rows: list[dict[str, Any]],
    confidence_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    confidence_by_candidate = by_candidate(confidence_rows)
    rows: list[dict[str, Any]] = []
    for index, attr in enumerate(attribution_rows, start=1):
        cid = str(attr["candidate_packet_id"])
        confidence = confidence_by_candidate[cid]
        row_id = f"PR166_S_SCORE_REFRESH::{index:06d}"
        rows.append(
            {
                "score_refresh_candidate_id": row_id,
                "candidate_packet_id": cid,
                "result_attribution_ref": attr["result_attribution_id"],
                "result_confidence_ref": confidence["result_confidence_id"],
                "gross_edge": attr["gross_return_proxy"],
                "net_edge_after_costs": attr["net_return_proxy"],
                "post_cost_classification": attr["post_cost_classification"],
                "result_confidence_score": confidence["result_confidence_score"],
                "score_refresh_action": "UPWEIGHT_AFTER_COSTS" if attr["net_return_proxy"] > 0 else "DOWNWEIGHT_AFTER_COSTS",
                "score_refresh_payload": {
                    "dominant_failure_driver": attr["dominant_failure_driver"],
                    "recommended_next_state": attr["recommended_next_state"],
                    "false_discovery_risk_adjustment": confidence["false_discovery_risk_adjustment"],
                },
                "no_live_authority": True,
                "no_profit_evidence": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_ResultAttributionLedger.report.json",
                    source_row_ref=attr["result_attribution_id"],
                    computed_by_module="score_refresh_candidates",
                    owning_agent="scoring_agent",
                    consuming_agent="scoring_agent",
                    downstream_action_type="score-refresh input",
                    downstream_artifact_route="score_memory_refresh_PR",
                    no_orphan_status="CONNECTED_TO_SCORE_REFRESH_ROUTE",
                ),
            }
        )
    return rows
