"""Point-in-time execution audit for PR166-S."""

from __future__ import annotations

from typing import Any

from .input_consumption import row_contract


def build_point_in_time_execution_audit_rows(attribution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, attr in enumerate(attribution_rows, start=1):
        row_id = f"PR166_S_POINT_IN_TIME_AUDIT::{index:06d}"
        rows.append(
            {
                "point_in_time_execution_audit_id": row_id,
                "candidate_packet_id": attr["candidate_packet_id"],
                "result_attribution_ref": attr["result_attribution_id"],
                "event_time": f"PR166_S_EVENT_TIME::{index:06d}",
                "decision_time": f"PR166_S_TIME::{index:06d}::DECISION",
                "simulated_submission_time": f"PR166_S_TIME::{index:06d}::SUBMISSION",
                "simulated_fill_time": f"PR166_S_TIME::{index:06d}::FILL",
                "data_available_at_decision_time": True,
                "event_cursor_at_decision": index,
                "event_cursor_at_fill": index + 1,
                "no_future_outcome_used": True,
                "no_settlement_leak_used": True,
                "no_private_state_used": True,
                "no_live_market_state_used": True,
                "no_source_truth_promotion": True,
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_ResultAttributionLedger.report.json",
                    source_row_ref=attr["result_attribution_id"],
                    computed_by_module="point_in_time_execution_audit",
                    owning_agent="governance_agent",
                    consuming_agent="risk_agent",
                    downstream_action_type="point-in-time audit input",
                    downstream_artifact_route="PR166_S_ResultConfidenceRegistry.report.json",
                ),
            }
        )
    return rows
