#!/usr/bin/env python3
"""Input discovery for PR168-DATA1A."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from tools.pr168_data1a_config import (
    DATA1_MERGE_COMMIT,
    FORECASTEX_IBKR_MANIFEST,
    GENERATED_ROOT,
    HISTORICAL_CANDIDATE_JSONL,
    KALSHI_FORWARD_L2_JSONL,
    KALSHI_SNAPSHOT_JSONL,
    POLYMARKET_FORWARD_L2_JSONL,
    POLYMARKET_SNAPSHOT_JSONL,
    REPO_ROOT,
    REQUIRED_DATA1_REPORT_IDS,
    generated_ref,
    manifest_path,
    report_path,
    route_defaults,
)

AGENT_ROSTER_PATH = GENERATED_ROOT / "PR165_D2_AgentRosterDiscoveryAudit.report.json"
AGENT_DUTY_PATH = GENERATED_ROOT / "PR165_D2_AgentDutySourceCrosswalk.report.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise TypeError(f"JSON artifact is not an object: {path}")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise TypeError(f"JSONL row is not an object: {path}:{line_number}")
            rows.append(value)
    return rows


def read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return load_json(path)


def data1_report_refs() -> list[str]:
    return [generated_ref(report_path(report_id)) for report_id in REQUIRED_DATA1_REPORT_IDS]


def snapshot_jsonl_paths() -> list[Path]:
    return [KALSHI_SNAPSHOT_JSONL, POLYMARKET_SNAPSHOT_JSONL]


def forward_l2_jsonl_paths() -> list[Path]:
    return [KALSHI_FORWARD_L2_JSONL, POLYMARKET_FORWARD_L2_JSONL]


def snapshot_manifest_paths() -> list[Path]:
    return [manifest_path(path) for path in snapshot_jsonl_paths()]


def forward_l2_manifest_paths() -> list[Path]:
    return [manifest_path(path) for path in forward_l2_jsonl_paths()]


def all_data1_input_paths() -> list[Path]:
    return (
        [report_path(report_id) for report_id in REQUIRED_DATA1_REPORT_IDS]
        + snapshot_jsonl_paths()
        + snapshot_manifest_paths()
        + forward_l2_jsonl_paths()
        + forward_l2_manifest_paths()
        + [HISTORICAL_CANDIDATE_JSONL, manifest_path(HISTORICAL_CANDIDATE_JSONL), FORECASTEX_IBKR_MANIFEST]
    )


def _git_contains_data1_commit() -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", DATA1_MERGE_COMMIT, "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    return completed.returncode == 0


def discover_inputs(created_at_utc: str) -> dict[str, Any]:
    missing: list[str] = []
    unreadable: list[str] = []
    parse_errors: list[str] = []
    required_paths = all_data1_input_paths()
    for path in required_paths:
        if not path.exists():
            missing.append(generated_ref(path))
            continue
        try:
            if path.suffix == ".jsonl":
                load_jsonl(path)
            else:
                load_json(path)
        except Exception as exc:  # noqa: BLE001 - audit needs exact parse failure capture
            unreadable.append(generated_ref(path))
            parse_errors.append(f"{generated_ref(path)}::{type(exc).__name__}:{exc}")

    top_level_reports = sorted(GENERATED_ROOT.glob("PR168_DATA1_*.report.json"))
    snapshot_jsonls = [path for path in snapshot_jsonl_paths() if path.exists()]
    manifests = [path for path in snapshot_manifest_paths() + forward_l2_manifest_paths() if path.exists()]
    agent_missing = [generated_ref(path) for path in [AGENT_ROSTER_PATH, AGENT_DUTY_PATH] if not path.exists()]

    return {
        "input_discovery_id": "pr168_data1a_input_discovery",
        "created_at_utc": created_at_utc,
        "pr233_state": "MERGED_CONFIRMED_BY_LOCAL_MAIN_COMMIT"
        if _git_contains_data1_commit()
        else "UNKNOWN_OR_DATA1_COMMIT_NOT_ANCESTOR",
        "pr233_merge_commit": DATA1_MERGE_COMMIT,
        "main_commit_contains_data1_flag": _git_contains_data1_commit(),
        "DATA1_top_level_report_count": len(top_level_reports),
        "DATA1_snapshot_jsonl_file_count": len(snapshot_jsonls),
        "DATA1_snapshot_manifest_file_count": len(manifests),
        "DATA1_missing_required_artifact_count": len(missing),
        "DATA1_missing_required_artifact_refs": missing,
        "DATA1_extra_artifact_count": len(
            [path for path in top_level_reports if path.stem.replace(".report", "") not in REQUIRED_DATA1_REPORT_IDS]
        ),
        "DATA1_readable_artifact_count": len(required_paths) - len(missing) - len(unreadable),
        "DATA1_unreadable_artifact_count": len(unreadable),
        "DATA1_schema_parse_error_count": len(parse_errors),
        "DATA1_parse_error_refs": parse_errors,
        "pr165_d2_agent_crosswalk_missing_refs": agent_missing,
        "pr165_d2_agent_crosswalk_consumed_flag": not agent_missing,
        **route_defaults("governance", data1_refs=data1_report_refs()),
    }


def load_data1_context() -> dict[str, Any]:
    reports = {
        report_id: load_json(report_path(report_id))
        for report_id in REQUIRED_DATA1_REPORT_IDS
        if report_path(report_id).exists()
    }
    return {
        "reports": reports,
        "kalshi_rows": load_jsonl(KALSHI_SNAPSHOT_JSONL) if KALSHI_SNAPSHOT_JSONL.exists() else [],
        "polymarket_rows": load_jsonl(POLYMARKET_SNAPSHOT_JSONL) if POLYMARKET_SNAPSHOT_JSONL.exists() else [],
        "kalshi_l2_rows": load_jsonl(KALSHI_FORWARD_L2_JSONL) if KALSHI_FORWARD_L2_JSONL.exists() else [],
        "polymarket_l2_rows": load_jsonl(POLYMARKET_FORWARD_L2_JSONL) if POLYMARKET_FORWARD_L2_JSONL.exists() else [],
        "candidate_rows": load_jsonl(HISTORICAL_CANDIDATE_JSONL) if HISTORICAL_CANDIDATE_JSONL.exists() else [],
        "manifests": [
            load_json(path)
            for path in snapshot_manifest_paths() + forward_l2_manifest_paths() + [manifest_path(HISTORICAL_CANDIDATE_JSONL), FORECASTEX_IBKR_MANIFEST]
            if path.exists()
        ],
        "agent_roster": read_optional_json(AGENT_ROSTER_PATH),
        "agent_duty": read_optional_json(AGENT_DUTY_PATH),
    }
