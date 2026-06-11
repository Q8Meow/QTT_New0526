"""Agent execution handoff rows for PR166-S."""

from __future__ import annotations

from typing import Any

from .input_consumption import row_contract


def build_agent_execution_handoff_rows(order_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, order in enumerate(order_rows, start=1):
        row_id = f"PR166_S_AGENT_EXECUTION_HANDOFF::{index:06d}"
        rows.append(
            {
                "agent_execution_handoff_id": row_id,
                "candidate_packet_id": order["candidate_packet_id"],
                "order_intent_ref": order["order_intent_id"],
                "primary_agent_owner": "execution_simulation_agent",
                "secondary_agent_reviewers": ["risk_agent", "tca_agent", "latency_agent", "liquidity_agent", "governance_agent"],
                "effective_challenger_agent": "risk_agent",
                "downstream_agent_consumer": "scoring_agent",
                "handoff_action": "future agent replay/paper execution handoff",
                "handoff_payload_ref": order["order_intent_id"],
                "downstream_pr_route": "score_memory_refresh_PR",
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_AgentExecutionContract.report.json",
                    source_row_ref=order["order_intent_id"],
                    computed_by_module="agent_execution_handoff",
                    owning_agent="execution_simulation_agent",
                    consuming_agent="scoring_agent",
                    downstream_action_type="agent execution handoff input",
                    downstream_artifact_route="score_memory_refresh_PR",
                ),
            }
        )
    return rows
