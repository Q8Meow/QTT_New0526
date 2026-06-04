"""PR162R adapter rerun input pack builder."""

from __future__ import annotations

from typing import Any


def adapter_input_pack_records(
    classifications: list[dict[str, Any]],
    computability_by_id: dict[str, dict[str, Any]],
    latency_by_id: dict[str, dict[str, Any]],
    utility_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in classifications:
        state = str(row.get("primary_executability_state"))
        if not state.startswith(("EXECUTABLE", "PARTIAL_EXECUTABLE")):
            continue
        cid = row["candidate_id"]
        rows.append(
            {
                "adapter_input_pack_id": f"PR162R_A_ADAPTER_INPUT::{cid}",
                "candidate_id": cid,
                "primary_executability_state": state,
                "computability_class": computability_by_id[cid]["computability_class"],
                "latency_class": latency_by_id[cid]["latency_class"],
                "trading_utility_class": utility_by_id[cid]["trading_utility_class"],
                "replay_input_eligible_flag": "REPLAY" in state,
                "paper_input_eligible_flag": "PAPER" in state,
                "adapter_execution_performed_flag": False,
                "result_packet_created_flag": False,
                "live_order_authority": False,
            }
        )
    return rows
