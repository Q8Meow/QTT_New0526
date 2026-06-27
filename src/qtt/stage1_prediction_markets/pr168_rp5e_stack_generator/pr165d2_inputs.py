"""PR165-D2 agent duty input access for RP5E."""

from __future__ import annotations

from .models import REPO_ROOT, read_json


def agent_roster_audit() -> dict[str, object]:
    return read_json(REPO_ROOT / "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json")


def agent_duty_crosswalk() -> dict[str, object]:
    return read_json(REPO_ROOT / "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json")
