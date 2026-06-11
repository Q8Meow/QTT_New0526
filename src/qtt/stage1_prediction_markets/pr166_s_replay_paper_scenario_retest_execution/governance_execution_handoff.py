"""Governance execution handoff rows for PR166-S."""

from __future__ import annotations

from typing import Any

from .input_consumption import row_contract


def build_governance_execution_handoff_rows(attribution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, attr in enumerate(attribution_rows, start=1):
        row_id = f"PR166_S_GOVERNANCE_EXECUTION_HANDOFF::{index:06d}"
        rows.append(
            {
                "governance_execution_handoff_id": row_id,
                "candidate_packet_id": attr["candidate_packet_id"],
                "governance_view": "NO_ORPHAN_AUTHORITY_EXECUTION_AUDIT",
                "post_cost_classification": attr["post_cost_classification"],
                "authority_boundary_ref": attr["authority_boundary_ref"],
                "challenge_agent": "risk_agent",
                "no_live_authority": True,
                "no_profit_evidence": True,
                "downstream_pr_route": "governance_agent",
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_ResultAttributionLedger.report.json",
                    source_row_ref=attr["result_attribution_id"],
                    computed_by_module="governance_execution_handoff",
                    owning_agent="governance_agent",
                    consuming_agent="governance_agent",
                    downstream_action_type="dashboard/governance/commander display input",
                    downstream_pr_route="governance_agent",
                    downstream_artifact_route="governance_agent",
                    no_orphan_status="CONNECTED_TO_DASHBOARD_GOVERNANCE_COMMANDER_REVIEW",
                ),
            }
        )
    return rows
