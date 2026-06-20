#!/usr/bin/env python3
"""Agent duty and downstream route mapping for PR168-RP."""

from __future__ import annotations

from typing import Any


def route_for_assignment(row: dict[str, Any], agent_status: dict[str, Any]) -> dict[str, Any]:
    owning_agent = str(row.get("owning_agent") or "Replay Paper Recompute Agent")
    if owning_agent == "Quantum AutoMapper Agent":
        downstream_agent = "Quantum Repair Agent"
        downstream_pr = "PR166-QC-R2"
    elif owning_agent == "Formula Materialization Agent":
        downstream_agent = "Formula Plugin Intake Agent"
        downstream_pr = "PR162E/PR162F"
    else:
        downstream_agent = "Ranking Agent"
        downstream_pr = "PR168-RANK"
    duty_source_ref = (
        "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"
        if agent_status.get("agent_duty_source_resolved")
        else "PR168_RP_AgentDutySourceGapQueue.report.json"
    )
    return {
        "owning_agent": owning_agent,
        "supporting_agents": ["Replay Paper Recompute Agent", "Risk Manager Agent", "Governance Agent"],
        "duty_source_ref": duty_source_ref,
        "downstream_agent": downstream_agent,
        "downstream_pr": downstream_pr,
        "downstream_route": row.get("downstream_route") or downstream_pr,
        "agent_duty_source_resolved": bool(agent_status.get("agent_duty_source_resolved")),
    }
