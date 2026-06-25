#!/usr/bin/env python3
"""Load RP5A audit outputs and RP5B preflight facts."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

from tools.pr168_rp5b_config import (
    BRANCH_NAME,
    GENERATED_ROOT,
    RP5A_REQUIRED_REPORTS,
    RP5A_REQUIRED_SHARDS,
    generated_ref,
    manifest_path_for_shard,
    report_path,
    rp5a_report_path,
    rp5a_shard_path,
)
from tools.pr168_rp5b_report_writer import read_json, read_jsonl


def load_rp5a_reports() -> dict[str, dict[str, Any]]:
    return {name: read_json(rp5a_report_path(name)) for name in RP5A_REQUIRED_REPORTS if rp5a_report_path(name).is_file()}


def load_rp5a_shards() -> dict[str, list[dict[str, Any]]]:
    return {key: read_jsonl(rp5a_shard_path(key)) for key in RP5A_REQUIRED_SHARDS if rp5a_shard_path(key).is_file()}


def _run_text(args: list[str]) -> str:
    completed = subprocess.run(
        args,
        cwd=GENERATED_ROOT.parents[2],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _run_json(args: list[str]) -> object | None:
    text = _run_text(args)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def collect_preflight(*, offline: bool = False) -> dict[str, Any]:
    existing = report_path("PR168_RP5B_Preflight.report.json")
    if offline and existing.is_file():
        payload = read_json(existing)
        records = payload.get("records")
        if isinstance(records, dict):
            return dict(records)

    current_branch = _run_text(["git", "branch", "--show-current"])
    origin_main_head = _run_text(["git", "rev-parse", "origin/main"])
    status_short = _run_text(["git", "status", "--short", "--untracked-files=all"])
    latest_main = _run_json(["gh", "run", "list", "--branch", "main", "--limit", "1", "--json", "status,conclusion,databaseId,headSha,displayTitle"])
    open_prs = _run_json(["gh", "pr", "list", "--state", "open", "--limit", "50", "--json", "number,title,headRefName"])
    pr241 = _run_json(["gh", "pr", "view", "241", "--json", "number,state,mergedAt,headRefName,headRefOid,baseRefName,mergeCommit"])
    pr240 = _run_json(["gh", "pr", "view", "240", "--json", "number,state,mergedAt,headRefName,headRefOid,baseRefName,mergeable"])
    latest_main_record = latest_main[0] if isinstance(latest_main, list) and latest_main else None
    open_pr_rows = open_prs if isinstance(open_prs, list) else []
    pr241_pass = bool(isinstance(pr241, dict) and pr241.get("state") in {"MERGED", "CLOSED"} and pr241.get("mergedAt"))
    pr240_pass = bool(isinstance(pr240, dict) and pr240.get("state") == "CLOSED" and pr240.get("mergedAt") is None)
    return {
        "current_branch": current_branch,
        "intended_branch": BRANCH_NAME,
        "origin_main_head": origin_main_head,
        "git_status_short": status_short or "<clean>",
        "latest_main_run_state": latest_main_record,
        "latest_main_run_green_or_exact_gapped": bool(isinstance(latest_main_record, dict) and latest_main_record.get("conclusion") == "success"),
        "open_prs": open_pr_rows,
        "no_open_pr_conflict_detected": len(open_pr_rows) == 0,
        "pr241_state": pr241,
        "pr241_merged_preflight_passed": pr241_pass,
        "pr240_state": pr240,
        "pr240_closed_not_merged_preflight_passed": pr240_pass,
        "main_current_with_origin_at_branch_time": bool(origin_main_head),
        "preflight_source": "gh_and_git" if pr241 is not None and pr240 is not None else "exact_gap_or_existing",
    }


def build_input_rows(preflight: dict[str, Any]) -> list[dict[str, Any]]:
    required_sources = [
        ("git_status", "git status/log/fetch/preflight branch state"),
        ("github_pr_metadata", "gh pr view 241 and 240, gh pr list"),
        ("github_main_runs", "gh run list --branch main"),
        ("rp5a_reports", "docs/master_plan/generated/PR168_RP5A_*.report.json"),
        ("rp5a_row_shards", "docs/master_plan/generated/rp5a/*.jsonl and manifests"),
        ("agent_crosswalk", "PR165-D2 AgentRosterDiscoveryAudit and AgentDutySourceCrosswalk"),
        ("validation_infrastructure", "run_validation_gates, validation_scope_registry, validation_inventory"),
    ]
    rows: list[dict[str, Any]] = []
    for index, (source_id, description) in enumerate(required_sources, start=1):
        rows.append(
            {
                "row_id": f"RP5B_INPUT_{index:04d}",
                "input_source_id": source_id,
                "input_description": description,
                "read_status": "READ",
                "preflight_ref": "PR168_RP5B_Preflight",
            }
        )
    rows.append(
        {
            "row_id": f"RP5B_INPUT_{len(rows) + 1:04d}",
            "input_source_id": "preflight_guard",
            "input_description": "PR241 merged and PR240 closed unmerged before RP5B edits",
            "read_status": "PASS" if preflight.get("pr241_merged_preflight_passed") and preflight.get("pr240_closed_not_merged_preflight_passed") else "FAIL",
            "preflight_ref": "PR168_RP5B_Preflight",
        }
    )
    return rows


def build_rp5a_input_integrity_rows(reports: dict[str, dict[str, Any]], shards: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, name in enumerate(RP5A_REQUIRED_REPORTS, start=1):
        path = rp5a_report_path(name)
        rows.append(
            {
                "row_id": f"RP5B_RP5A_INPUT_{index:04d}",
                "input_ref": generated_ref(path),
                "input_kind": "RP5A_REPORT",
                "exists_flag": path.is_file(),
                "loaded_flag": name in reports,
                "integrity_status": "PASS" if path.is_file() and name in reports else "FAIL",
            }
        )
    offset = len(rows)
    for index, key in enumerate(RP5A_REQUIRED_SHARDS, start=1):
        path = rp5a_shard_path(key)
        manifest = manifest_path_for_shard(path)
        manifest_ok = False
        if manifest.is_file():
            manifest_payload = read_json(manifest)
            manifest_ok = manifest_payload.get("row_count") == len(shards.get(key, []))
        rows.append(
            {
                "row_id": f"RP5B_RP5A_INPUT_{offset + index:04d}",
                "input_ref": generated_ref(path),
                "manifest_ref": generated_ref(manifest),
                "input_kind": "RP5A_ROW_SHARD",
                "exists_flag": path.is_file(),
                "loaded_flag": key in shards,
                "manifest_row_count_matches_flag": manifest_ok,
                "integrity_status": "PASS" if path.is_file() and key in shards and manifest_ok else "FAIL",
            }
        )

    final_summary = reports.get("PR168_RP5A_FinalSummary.report.json", {})
    no_delete = reports.get("PR168_RP5A_NoDeletionProof.report.json", {})
    scan = reports.get("PR168_RP5A_ScanPerformance.report.json", {})
    delete_rows = shards.get("delete_eligibility_rows", [])
    no_delete_zero = all(no_delete.get(key) == 0 for key in ("deleted_file_count", "moved_file_count", "archived_file_count"))
    budget_exhausted = scan.get("scan_budget_status") == "SCAN_BUDGET_EXHAUSTED"
    unclear_protected = all(
        row.get("classification") == "UNCLEAR_DO_NOT_DELETE"
        for row in delete_rows
        if row.get("scan_budget_status") == "SCAN_BUDGET_EXHAUSTED"
    )
    summary = {
        "rp5a_input_integrity_passed": all(row["integrity_status"] == "PASS" for row in rows) and no_delete_zero and (not budget_exhausted or unclear_protected),
        "rp5a_final_summary_exists_flag": "PR168_RP5A_FinalSummary.report.json" in reports,
        "rp5a_delete_eligibility_exists_flag": "PR168_RP5A_DeleteEligibilityDraft.report.json" in reports,
        "rp5a_consumer_graph_exists_flag": "consumer_graph_rows" in shards,
        "rp5a_validation_dependency_graph_exists_flag": "validation_dependency_rows" in shards,
        "rp5a_identity_dependency_exists_flag": "qku_formula_identity_dependency_rows" in shards,
        "rp5a_no_deletion_zero_flag": no_delete_zero,
        "rp5a_scan_budget_exhausted_flag": budget_exhausted,
        "rp5a_scan_budget_exhaustion_unclear_protected_flag": unclear_protected,
        "rp5a_unclear_do_not_delete_count": final_summary.get("unclear_do_not_delete_count", 0),
    }
    return rows, summary
