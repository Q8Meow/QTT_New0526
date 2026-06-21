#!/usr/bin/env python3
"""Agent routing helpers for PR168-GFP2."""

from __future__ import annotations

from typing import Any

from tools.pr168_gfp2_input_loader import GFP2Inputs


def agent_consumption_rows(inputs: GFP2Inputs, report_name: str, source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    agent_ids = [str(row.get("agent_id")) for row in inputs.agent_roster_rows if row.get("agent_id")]
    return [
        {
            "consumption_id": f"PR168_GFP2_AGENT_CONSUMPTION::{report_name}",
            "source_report_ref": report_name,
            "source_row_count": len(source_rows),
            "agent_roster_refs": ["PR165_D2_AgentRosterDiscoveryAudit.report.json"],
            "agent_duty_crosswalk_refs": ["PR165_D2_AgentDutySourceCrosswalk.report.json"],
            "agent_ids": agent_ids,
            "owning_agent": "Governance Agent",
            "consumer_agents": ["Replay Paper Recompute Agent", "Ranking Agent", "Quantum Optimizer Agent"],
            "downstream_pr_refs": ["PR168-RP2", "PR168-RANK2"],
            "validator_refs": ["tools/pr168_gfp2_validator.py"],
            "test_refs": ["tests/pr168_gfp2"],
            "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
            "authority_class": "AGENT_ROUTING_NO_LIVE_AUTHORITY",
        }
    ]


def qku_routing_rows(universe_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "canonical_row_key": row["canonical_row_key"],
            "qku_id": row["qku_id"],
            "owning_agent": row["agent_owner"],
            "consumer_agents": row["agent_consumers"],
            "downstream_pr_refs": row["downstream_pr_refs"],
            "authority_class": row["authority_class"],
            "no_orphan_status": row["no_orphan_status"],
            "live_order_authority_created_flag": False,
        }
        for row in universe_rows
    ]
