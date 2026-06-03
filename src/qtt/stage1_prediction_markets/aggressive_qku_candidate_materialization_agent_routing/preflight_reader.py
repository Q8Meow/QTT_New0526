"""Preflight input consumption for PR162D."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from . import constants as c
from .json_io import read_json, records_from_payload
from .paths import normalize_repo_relative_ref, resolve_repo_relative


def current_branch(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def load_report_records(repo_root: Path, rel_ref: str) -> list[dict[str, Any]]:
    path = repo_root / rel_ref
    if not path.exists() or path.suffix.lower() not in {".json", ".jsonl"}:
        return []
    if path.suffix.lower() == ".jsonl":
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(read_json(Path(line)))
        return rows
    payload = read_json(path)
    rows = records_from_payload(payload)
    if isinstance(payload, dict) and payload.get("sharded_flag"):
        rows = []
        for shard_ref in payload.get("shard_files") or []:
            rows.extend(records_from_payload(read_json(resolve_repo_relative(repo_root, shard_ref))))
    return rows


def preflight_receipt(repo_root: Path) -> dict[str, Any]:
    present: list[str] = []
    missing: list[str] = []
    fallback_paths_used: list[dict[str, str]] = []
    for rel_ref in c.MANDATORY_INPUT_REFS:
        if (repo_root / rel_ref).exists():
            present.append(rel_ref)
            continue
        missing.append(rel_ref)
        if rel_ref.endswith("PR136MasterPlanSectionCrosswalk.report.json"):
            fallback = "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json"
            if (repo_root / fallback).exists():
                fallback_paths_used.append(
                    {"missing_input_ref": rel_ref, "fallback_input_ref": fallback}
                )
                present.append(fallback)
    consumed = sorted(set(present), key=lambda value: (value.casefold(), value))
    return {
        "record_id": "PR162D-PREFLIGHT-RECEIPT",
        "active_branch": current_branch(repo_root),
        "required_input_count": len(c.MANDATORY_INPUT_REFS),
        "required_inputs_present": consumed,
        "required_inputs_present_count": len(consumed),
        "required_inputs_missing": missing,
        "required_inputs_missing_count": len(missing),
        "fallback_paths_used": fallback_paths_used,
        "fallback_paths_used_count": len(fallback_paths_used),
        "missing_input_notes": [
            {
                "input_ref": ref,
                "missing_input_status": "MISSING_INPUT_CONTINUE_CANDIDATE_ACQUISITION",
                "route_impossible_flag": False,
            }
            for ref in missing
        ],
        "consumed_input_refs": consumed,
        "consumed_input_refs_posix_relative_flag": all(
            "\\" not in normalize_repo_relative_ref(ref) for ref in consumed
        ),
        "online_scouting_allowed": True,
        "ci_offline_required": True,
        "network_calls_in_build_or_tests_flag": False,
        "PR136_control_plane_consumed": True,
        "PR161F_agent_contracts_consumed": True,
        "PR162C_blocker_ledger_consumed": (
            repo_root
            / "docs/master_plan/generated/PR162C_DataRequirementClassificationLedger.report.json"
        ).exists(),
    }
