#!/usr/bin/env python3
"""GitHub PR metadata scanner for PR168-RP5A."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from tools.pr168_rp5a_config import BRANCH_NAME, PR240_HEAD_REF
from tools.pr168_rp5a_term_taxonomy import match_text


def _gh_json(args: list[str]) -> object | None:
    completed = subprocess.run(
        ["gh", *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return None
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None


def _merge_commit_oid(value: object) -> str | None:
    if isinstance(value, dict):
        oid = value.get("oid")
        return None if oid is None else str(oid)
    return None


def fetch_pr_metadata_rows(existing_rows_path: Path | None = None) -> tuple[list[dict[str, object]], dict[str, object]]:
    payload = _gh_json(
        [
            "pr",
            "list",
            "--state",
            "all",
            "--limit",
            "300",
            "--json",
            "number,title,state,mergedAt,headRefName,baseRefName,mergeCommit,body",
        ]
    )
    if not isinstance(payload, list):
        if existing_rows_path and existing_rows_path.is_file():
            rows = [json.loads(line) for line in existing_rows_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            return rows, {"github_metadata_source": "existing_committed_rows_fallback", "github_prs_scanned_count": len(rows)}
        return [], {"github_metadata_source": "unavailable_exact_gap", "github_prs_scanned_count": 0}

    rows: list[dict[str, object]] = []
    for pr in payload:
        if not isinstance(pr, dict):
            continue
        if pr.get("headRefName") == BRANCH_NAME:
            continue
        haystack = "\n".join(str(pr.get(key) or "") for key in ("title", "body", "headRefName"))
        matches = match_text(haystack)
        term_ids = sorted({str(match["term_id"]) for match in matches})
        term_families = sorted({str(match["term_family"]) for match in matches})
        number = pr.get("number")
        state = str(pr.get("state") or "")
        merged_at = pr.get("mergedAt")
        if number == 240 and state == "CLOSED" and merged_at is None:
            next_action = "HISTORICAL_ONLY"
            confidence = "HIGH"
            current_tree_status = "CLOSED_NOT_MERGED_HISTORICAL_ONLY"
        elif term_ids:
            next_action = "AUDIT_FILES"
            confidence = "MEDIUM"
            current_tree_status = "UNKNOWN_NEEDS_FILE_AUDIT"
        else:
            next_action = "HISTORICAL_ONLY"
            confidence = "LOW"
            current_tree_status = "NO_STALE_PR_METADATA_MATCH"
        if not term_ids and number != 240:
            continue
        rows.append(
            {
                "pr_number": number,
                "pr_title": pr.get("title"),
                "state": state,
                "merged_at": merged_at,
                "head_ref": pr.get("headRefName"),
                "base_ref": pr.get("baseRefName"),
                "merge_commit_if_available": _merge_commit_oid(pr.get("mergeCommit")),
                "matched_terms": term_ids,
                "matched_term_families": term_families,
                "semantic_risk_summary": "matched stale legacy semantics in PR metadata" if term_ids else "required Recovery1 preflight record",
                "known_artifact_prefixes_if_inferred": _artifact_prefixes(str(pr.get("title") or ""), str(pr.get("headRefName") or "")),
                "current_main_contains_pr_outputs_unknown_or_proven": current_tree_status,
                "audit_confidence": confidence,
                "next_action": next_action,
            }
        )
    rows.sort(key=lambda row: int(row["pr_number"] or 0), reverse=True)
    pr240_rows = [row for row in rows if row.get("pr_number") == 240]
    pr240_closed_not_merged = bool(pr240_rows and pr240_rows[0]["state"] == "CLOSED" and pr240_rows[0]["merged_at"] is None and pr240_rows[0]["head_ref"] == PR240_HEAD_REF)
    return rows, {
        "github_metadata_source": "gh_pr_list",
        "github_prs_scanned_count": len(payload),
        "github_prs_with_stale_terms_count": len([row for row in rows if row["matched_terms"]]),
        "pr240_closed_not_merged_preflight_passed": pr240_closed_not_merged,
    }


def _artifact_prefixes(title: str, head: str) -> list[str]:
    text = f"{title} {head}".upper().replace("-", "_")
    prefixes: list[str] = []
    for token in ("PR168_RANK3", "PR168_RP3", "PR168_MAP3", "PR168_RP2", "PR168_GFP2R", "PR168_DATA1A", "PR168_DATA1", "PR168_RANK", "PR168_RP", "PR168_GFP", "PR165_D2", "PR166_SF", "PR166_SM2", "PR162E_Q", "PR162E"):
        if token in text:
            prefixes.append(token)
    return prefixes
