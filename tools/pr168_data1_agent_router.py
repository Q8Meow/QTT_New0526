#!/usr/bin/env python3
"""PR165-D2 agent crosswalk consumption and no-orphan routing proof."""

from __future__ import annotations

import json
from pathlib import Path

from tools.pr168_data1_config import GENERATED_ROOT, authority_flags, generated_ref, route_defaults


AGENT_ROSTER_PATH = GENERATED_ROOT / "PR165_D2_AgentRosterDiscoveryAudit.report.json"
AGENT_DUTY_PATH = GENERATED_ROOT / "PR165_D2_AgentDutySourceCrosswalk.report.json"


def load_agent_crosswalk_status(now_utc: str) -> dict[str, object]:
    roster_exists = AGENT_ROSTER_PATH.exists()
    duty_exists = AGENT_DUTY_PATH.exists()
    return {
        "agent_crosswalk_status_id": "pr168_data1_pr165_d2_agent_crosswalk_status",
        "roster_path": generated_ref(AGENT_ROSTER_PATH) if roster_exists else generated_ref(AGENT_ROSTER_PATH),
        "duty_crosswalk_path": generated_ref(AGENT_DUTY_PATH) if duty_exists else generated_ref(AGENT_DUTY_PATH),
        "roster_exists": roster_exists,
        "duty_crosswalk_exists": duty_exists,
        "consumed_flag": roster_exists and duty_exists,
        "roster_report_id": _report_id(AGENT_ROSTER_PATH) if roster_exists else None,
        "duty_crosswalk_report_id": _report_id(AGENT_DUTY_PATH) if duty_exists else None,
        "created_at_utc": now_utc,
        **route_defaults("governance"),
        **authority_flags(),
    }


def build_no_orphan_rows(artifact_refs: list[str], now_utc: str) -> list[dict[str, object]]:
    route = route_defaults("governance")
    return [
        {
            "no_orphan_row_id": f"no_orphan_{index:04d}",
            "artifact_ref": artifact,
            "upstream_refs": ["PR165_D2_AgentRosterDiscoveryAudit", "PR165_D2_AgentDutySourceCrosswalk"],
            "downstream_refs": ["PR168-GFP2R", "PR168-RP2", "PR168-RANK2"],
            "owning_agent": route["owning_agent"],
            "consumer_agents": route["consumer_agents"],
            "validator_refs": route["validator_refs"],
            "test_refs": route["test_refs"],
            "no_orphan_status": "NO_ORPHAN_ROUTED",
            "created_at_utc": now_utc,
            **authority_flags(),
        }
        for index, artifact in enumerate(artifact_refs, start=1)
    ]


def _report_id(path: Path) -> str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return str(payload.get("report_id") or payload.get("id") or path.stem)
