"""PR136 route/crosswalk/market/command consumption for PR162R."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_route_consumption_audit(discovery_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ids = {
        "PR136_ROUTE_TRIAGE",
        "PR136_MASTER_PLAN_SECTION_CROSSWALK",
        "PR136_MARKET_INDEX",
        "PR136_COMMAND_ACTION",
        "PR136_COVERAGE_TO_READINESS",
    }
    rows = []
    for row in discovery_rows:
        if row["input_id"] in ids:
            rows.append(
                {
                    "route_consumption_id": f"PR162R_ROUTE_CONSUMPTION::{row['input_id']}",
                    "input_id": row["input_id"],
                    "requested_path": row["requested_path"],
                    "consumed_path": row["consumed_path"],
                    "present_flag": row["present_flag"],
                    "fallback_lineage_used": row["fallback_lineage_used"],
                    "exact_missing_input_note": row["exact_missing_input_note"],
                    "consumed_for_row_level_binding_flag": row["consumed_path"] is not None,
                    "live_order_authority": False,
                    "validation_status": "PASS",
                }
            )
    return rows


def build_market_specific_index_rows(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, packet in enumerate(packets, start=1):
        rows.append(
            {
                "market_specific_qku_adapter_index_id": f"PR162R_MARKET_INDEX::{index:05d}",
                "candidate_packet_ref": packet.get("candidate_packet_id"),
                "qku_id": _first_qku(packet),
                "domain_family_key": packet.get("domain_family_key"),
                "market_specific_index_refs": ["docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"],
                "coverage_to_readiness_refs": ["docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"],
                "market_route_status": "MISSING_MARKET_SPECIFIC_ROUTE_FILL_ACTION_ATTACHED",
                "fill_action_family": "MISSING_MARKET_SPECIFIC_ROUTE",
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_command_action_binding_rows(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, packet in enumerate(packets, start=1):
        rows.append(
            {
                "command_action_binding_id": f"PR162R_COMMAND_ACTION::{index:05d}",
                "candidate_packet_ref": packet.get("candidate_packet_id"),
                "qku_id": _first_qku(packet),
                "command_action_refs": ["docs/master_plan/generated/PR136CommandActionMatrix.report.json"],
                "best_available_action": "prepare_replay_paper_adapter_input_candidate",
                "agent_consumer_route": "Replay/Paper Candidate Router",
                "agent_consumer_route_fill_required_flag": False,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def _first_qku(packet: dict[str, Any]) -> str:
    qku_ids = packet.get("qku_ids") or []
    return str(qku_ids[0]) if qku_ids else ""
