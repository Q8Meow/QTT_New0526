"""Commander execution handoff rows for PR166-S."""

from __future__ import annotations

from typing import Any

from .input_consumption import row_contract


def build_commander_execution_handoff_rows(
    replay_result_rows: list[dict[str, Any]],
    paper_result_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for source_artifact, sources in (
        ("PR166_S_ReplayRunResultRegistry.report.json", replay_result_rows),
        ("PR166_S_PaperRunResultRegistry.report.json", paper_result_rows),
    ):
        for source in sources:
            index += 1
            result_ref = source.get("replay_run_result_id") or source.get("paper_run_result_id")
            row_id = f"PR166_S_COMMANDER_EXECUTION_HANDOFF::{index:06d}"
            rows.append(
                {
                    "commander_execution_handoff_id": row_id,
                    "source_run_result_ref": result_ref,
                    "source_selected_batch_id": source["source_selected_batch_id"],
                    "commander_action_type": "future PR route coordination for replay/paper result",
                    "future_pr_route": _route(source),
                    "run_mode": source["run_mode"],
                    "run_status": source["run_status"],
                    "tested_candidate_count": source["tested_candidate_count"],
                    "positive_net_edge_count": source["positive_net_edge_count"],
                    "failed_after_cost_count": source["failed_after_cost_count"],
                    **row_contract(
                        row_id=row_id,
                        source_artifact_ref=source_artifact,
                        source_row_ref=result_ref,
                        computed_by_module="commander_execution_handoff",
                        owning_agent="commander_agent",
                        consuming_agent="commander_agent",
                        downstream_action_type="dashboard/governance/commander display input",
                        downstream_pr_route="commander_agent",
                        downstream_artifact_route="commander_agent",
                        no_orphan_status="CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
                    ),
                }
            )
    return rows


def _route(source: dict[str, Any]) -> str:
    if source.get("positive_net_edge_count", 0) > 0:
        return "score_memory_refresh_PR"
    if source.get("failed_after_cost_count", 0) > 0:
        return "PR167"
    return "score_memory_refresh_PR"
