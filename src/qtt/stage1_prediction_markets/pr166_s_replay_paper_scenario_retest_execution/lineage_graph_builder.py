"""Lineage graph builder for PR166-S."""

from __future__ import annotations

from typing import Any

from .input_consumption import row_contract


def build_lineage_graph_rows(attribution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, attr in enumerate(attribution_rows, start=1):
        row_id = f"PR166_S_LINEAGE::{index:06d}"
        rows.append(
            {
                "lineage_graph_id": row_id,
                "candidate_packet_id": attr["candidate_packet_id"],
                "qku_id": attr["qku_id"],
                "dag_edges": [
                    "PR165 score/rank",
                    "PR165-B condition/scenario memory",
                    "PR165-C computability and retest routing",
                    "PR165-D selected batch",
                    "PR166-S replay/paper run plan",
                    "PR166-S event stream",
                    "PR166-S simulated order intent",
                    "PR166-S simulated fill and execution cost",
                    "PR166-S result attribution",
                    "score/memory refresh candidate",
                    "dashboard/governance/commander handoff",
                ],
                "upstream_input_refs": [
                    "PR165_D_RetestBatchSelectionQueue.report.json",
                    "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json",
                    "PR165_TCAAdjustedScoreRegistry.report.json",
                ],
                "downstream_batch_ref": attr["source_selected_batch_id"],
                "downstream_result_ref": attr["result_attribution_id"],
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_ResultAttributionLedger.report.json",
                    source_row_ref=attr["result_attribution_id"],
                    computed_by_module="lineage_graph_builder",
                    owning_agent="governance_agent",
                    consuming_agent="commander_agent",
                    downstream_action_type="lineage graph audit input",
                    downstream_artifact_route="PR166_S_FinalSummary.report.json",
                ),
            }
        )
    return rows
