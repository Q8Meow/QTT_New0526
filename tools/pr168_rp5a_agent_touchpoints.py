#!/usr/bin/env python3
"""Agent-route and no-orphan touchpoint builder for PR168-RP5A."""

from __future__ import annotations

from pathlib import Path

from tools.pr168_rp5a_config import AGENT_TOUCHPOINT_REGEX, REPO_ROOT


def _has_agent_touchpoint(file_path: str, repo_root: Path) -> bool:
    try:
        text = (repo_root / file_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(AGENT_TOUCHPOINT_REGEX.search(text))


def build_agent_touchpoint_rows(matched_files: list[str], repo_root: Path = REPO_ROOT) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, file_path in enumerate(matched_files, start=1):
        active = _has_agent_touchpoint(file_path, repo_root)
        rows.append(
            {
                "row_id": f"RP5A_AGENT_TOUCH_{index:07d}",
                "file_path": file_path,
                "agent_ref_or_crosswalk_ref": "PR165_D2_AGENT_OR_LOCAL_AGENT_REF_DETECTED" if active else None,
                "duty_ref_if_any": "AgentDutySourceCrosswalk" if active else None,
                "downstream_consumer_ref_if_any": "downstream_consumer_or_handoff_detected" if active else None,
                "qku_or_formula_ref_if_any": "qku_or_formula_ref_possible" if active else None,
                "active_agent_touchpoint_flag": active,
                "future_replacement_needed_flag": active,
                "future_pr": "PR168_RP5B" if active else "UNKNOWN",
                "recommended_classification": "REWRITE_CONSUMER_FIRST" if active else "NO_AGENT_TOUCHPOINT_DETECTED",
            }
        )
    return rows


def pr165_d2_crosswalk_status(repo_root: Path = REPO_ROOT) -> dict[str, object]:
    roster = repo_root / "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json"
    duty = repo_root / "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"
    return {
        "agent_roster_discovery_audit_present": roster.is_file(),
        "agent_duty_source_crosswalk_present": duty.is_file(),
        "documented_equivalent_crosswalk_present": roster.is_file() and duty.is_file(),
        "missing_crosswalk_report_required": not (roster.is_file() and duty.is_file()),
    }
