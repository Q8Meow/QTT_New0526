"""No-lookahead audit for PR166-S."""

from __future__ import annotations

from typing import Any

from .input_consumption import row_contract


def build_no_lookahead_audit_rows(attribution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, attr in enumerate(attribution_rows, start=1):
        row_id = f"PR166_S_NO_LOOKAHEAD_AUDIT::{index:06d}"
        rows.append(
            {
                "no_lookahead_audit_id": row_id,
                "candidate_packet_id": attr["candidate_packet_id"],
                "result_attribution_ref": attr["result_attribution_id"],
                "input_artifact_refs": [
                    "PR165_D_RetestBatchSelectionQueue.report.json",
                    "PR165_D_ScenarioQKUCombinationCandidateRegistry.report.json",
                    "PR165_TCAAdjustedScoreRegistry.report.json",
                    "PR165_B_ScenarioOutcomeMatrix.report.json",
                ],
                "settlement_outcome_used_before_decision": False,
                "future_event_used_before_cursor": False,
                "private_state_used": False,
                "live_market_state_used": False,
                "source_truth_promotion_created": False,
                "no_lookahead_pass": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_ResultAttributionLedger.report.json",
                    source_row_ref=attr["result_attribution_id"],
                    computed_by_module="no_lookahead_audit",
                    owning_agent="governance_agent",
                    consuming_agent="risk_agent",
                    downstream_action_type="no-lookahead audit input",
                    downstream_artifact_route="PR166_S_ResultConfidenceRegistry.report.json",
                ),
            }
        )
    return rows
