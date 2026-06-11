"""Agent execution contract rows for PR166-S."""

from __future__ import annotations

from typing import Any

from .input_consumption import row_contract


def build_agent_execution_contract_rows(order_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    contracts = (
        ("replay_agent", "execution_simulation_agent", "replay run input"),
        ("paper_agent", "execution_simulation_agent", "paper run input"),
        ("tca_agent", "scoring_agent", "cost/TCA input"),
        ("memory_agent", "memory_agent", "memory-refresh input"),
    )
    for index, order in enumerate(order_rows, start=1):
        owner, consumer, action = contracts[(index - 1) % len(contracts)]
        row_id = f"PR166_S_AGENT_EXECUTION_CONTRACT::{index:06d}"
        rows.append(
            {
                "agent_execution_contract_id": row_id,
                "source_selected_batch_ref": order["source_selected_batch_id"],
                "source_candidate_ref": order["source_candidate_packet_id"],
                "owning_agent": owner,
                "consuming_agent": consumer,
                "agent_action_type": action,
                "agent_input_payload_ref": order["order_intent_id"],
                "agent_output_expected_future_ref": "score_memory_refresh_PR",
                "run_mode": order["run_mode"],
                "authority_boundary_ref": order["authority_boundary_ref"],
                "downstream_pr_route": "score_memory_refresh_PR",
                "no_orphan_status": "CONNECTED_UPSTREAM_AND_DOWNSTREAM",
                **row_contract(
                    row_id=row_id,
                    source_artifact_ref="PR166_S_OrderIntentRegistry.report.json",
                    source_row_ref=order["order_intent_id"],
                    computed_by_module="agent_execution_contract",
                    owning_agent=owner,
                    consuming_agent=consumer,
                    downstream_action_type=action,
                    downstream_artifact_route="PR166_S_AgentExecutionHandoff.report.json",
                ),
            }
        )
    return rows
