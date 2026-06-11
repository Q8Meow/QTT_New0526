"""Dashboard execution handoff rows for PR166-S."""

from __future__ import annotations

from typing import Any

from .input_consumption import row_contract


def build_dashboard_execution_handoff_rows(attribution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, attr in enumerate(attribution_rows, start=1):
        row_id = f"PR166_S_DASHBOARD_EXECUTION_HANDOFF::{index:06d}"
        rows.append(
            {
                "dashboard_execution_handoff_id": row_id,
                "candidate_packet_id": attr["candidate_packet_id"],
                "dashboard_view": "REPLAY_PAPER_EXECUTION_RESULTS",
                "display_action_type": "replay/paper result display input",
                "post_cost_classification": attr["post_cost_classification"],
                "dominant_failure_driver": attr["dominant_failure_driver"],
                "net_return_proxy": attr["net_return_proxy"],
                "no_live_button": True,
                "no_order_ready_action": True,
                "downstream_pr_route": "dashboard_agent",
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_ResultAttributionLedger.report.json",
                    source_row_ref=attr["result_attribution_id"],
                    computed_by_module="dashboard_execution_handoff",
                    owning_agent="dashboard_agent",
                    consuming_agent="dashboard_agent",
                    downstream_action_type="dashboard/governance/commander display input",
                    downstream_pr_route="dashboard_agent",
                    downstream_artifact_route="dashboard_agent",
                    no_orphan_status="CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
                ),
            }
        )
    return rows
