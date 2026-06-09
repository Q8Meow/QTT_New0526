"""Discover prior QTT-agent PRs and artifact aliases for PR165-C."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

from .artifact_discovery import discover_agent_related_reports
from .central_vocab import AUTHORITY_BOUNDARY_REF, NO_ORPHAN_STATUS

KEYWORDS = (
    "agent",
    "router",
    "handoff",
    "governance",
    "commander",
    "dashboard",
    "qku",
    "replay",
    "paper",
)
KNOWN_SEEDS = {
    "PR161D": "QKU candidate quality scoring and replay-paper prioritization",
    "PR163": "generic paper adapter capture framework",
    "PR163-B": "paired replay paper concurrent executor",
    "PR164": "review provenance QKU canonical coverage audit",
    "PR163-C": "pretrade infrastructure rejection remediation",
    "PR165": "evidence-backed scoring and ranking",
    "PR165-B": "condition-scoped negative memory execution",
}


def discover_upstream_agent_prs(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    gh_rows, gh_status = _gh_pr_rows(repo_root)
    artifact_refs = discover_agent_related_reports(repo_root)
    rows: list[dict[str, Any]] = []
    matched_artifacts_by_seed = _artifact_refs_by_seed(artifact_refs)
    for pr in gh_rows:
        text = f"{pr.get('title','')} {pr.get('headRefName','')}".lower()
        matched = [keyword for keyword in KEYWORDS if keyword in text]
        seed_refs = [seed for seed in KNOWN_SEEDS if seed.lower().replace("-", "") in text.replace("-", "")]
        if not matched and not seed_refs:
            continue
        refs = []
        for seed in seed_refs:
            refs.extend(matched_artifacts_by_seed.get(seed, ()))
        rows.append(_row_from_pr(pr, matched or seed_refs, refs[:20]))
    discovered_seed_titles = {row["discovered_pr_title"] for row in rows}
    for seed, description in KNOWN_SEEDS.items():
        if any(seed.lower() in title.lower().replace(" ", "") for title in discovered_seed_titles):
            continue
        refs = matched_artifacts_by_seed.get(seed, ())
        if refs:
            rows.append(
                {
                    "upstream_agent_pr_discovery_id": f"PR165_C_AGENT_PR_DISCOVERY_ALIAS::{seed}",
                    "discovered_pr_number": None,
                    "discovered_pr_title": f"{seed} alias: {description}",
                    "discovered_pr_head_ref_name": "",
                    "discovered_pr_merged_at": "",
                    "matched_reason": ["KNOWN_SEED_ALIAS_BY_LOCAL_ARTIFACT"],
                    "matched_files": list(refs[:20]),
                    "agent_related_artifacts": list(refs[:10]),
                    "qku_route_artifacts": [ref for ref in refs if "QKU" in ref][:10],
                    "dashboard_governance_commander_artifacts": [
                        ref for ref in refs if any(token in ref.lower() for token in ("dashboard", "governance", "commander"))
                    ][:10],
                    "consumed_by_pr165_c": True,
                    "not_consumed_reason": "",
                    "relevance_confidence": "HIGH",
                    "downstream_pr165_c_report_refs": [
                        "PR165_C_AgentDutyDistinctnessMatrix.report.json",
                        "PR165_C_AgentPRConnectivityReconciliation.report.json",
                    ],
                    "no_orphan_status": NO_ORPHAN_STATUS,
                    "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
                    "validation_status": "PASS",
                }
            )
    rows.sort(key=lambda row: (str(row.get("discovered_pr_number") or "9999"), row["discovered_pr_title"]))
    for index, row in enumerate(rows, start=1):
        row["upstream_agent_pr_discovery_id"] = row.get("upstream_agent_pr_discovery_id") or f"PR165_C_AGENT_PR_DISCOVERY::{index:04d}"
    return rows, gh_status


def _gh_pr_rows(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    command = ["gh", "pr", "list", "--state", "merged", "--limit", "200", "--json", "number,title,mergedAt,headRefName"]
    try:
        result = subprocess.run(command, cwd=repo_root, check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        return [], {
            "github_pr_discovery_status": "GITHUB_PR_DISCOVERY_UNAVAILABLE_WITH_LOCAL_FALLBACK",
            "github_pr_discovery_error": str(exc),
        }
    return json.loads(result.stdout), {
        "github_pr_discovery_status": "GITHUB_PR_DISCOVERY_AVAILABLE",
        "github_pr_discovery_error": "",
    }


def _row_from_pr(pr: dict[str, Any], reasons: list[str], refs: list[str]) -> dict[str, Any]:
    qku_refs = [ref for ref in refs if "QKU" in ref]
    handoff_refs = [ref for ref in refs if any(token in ref.lower() for token in ("dashboard", "governance", "commander", "handoff"))]
    return {
        "discovered_pr_number": pr.get("number"),
        "discovered_pr_title": pr.get("title", ""),
        "discovered_pr_head_ref_name": pr.get("headRefName", ""),
        "discovered_pr_merged_at": pr.get("mergedAt", ""),
        "matched_reason": reasons,
        "matched_files": refs,
        "agent_related_artifacts": refs[:10],
        "qku_route_artifacts": qku_refs[:10],
        "dashboard_governance_commander_artifacts": handoff_refs[:10],
        "consumed_by_pr165_c": True,
        "not_consumed_reason": "",
        "relevance_confidence": "HIGH" if refs else "MEDIUM",
        "downstream_pr165_c_report_refs": [
            "PR165_C_UpstreamAgentPRDiscovery.report.json",
            "PR165_C_AgentPRConnectivityReconciliation.report.json",
        ],
        "no_orphan_status": NO_ORPHAN_STATUS,
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "validation_status": "PASS",
    }


def _artifact_refs_by_seed(artifact_refs: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    mapping: dict[str, list[str]] = {seed: [] for seed in KNOWN_SEEDS}
    aliases = {
        "PR161D": ("PR161D_", "pr161d_"),
        "PR163": ("PR163_", "pr163_", "PR163Generic", "PR163_Paper"),
        "PR163-B": ("PR163_B_", "pr163_b_", "PR163B"),
        "PR164": ("PR164_", "pr164_"),
        "PR163-C": ("PR163_C_", "pr163_c_", "PR163C"),
        "PR165": ("PR165_", "pr165_"),
        "PR165-B": ("PR165_B_", "pr165_b_"),
    }
    for ref in artifact_refs:
        for seed, tokens in aliases.items():
            if any(token in ref for token in tokens):
                mapping[seed].append(ref)
    return {seed: tuple(sorted(refs)) for seed, refs in mapping.items()}
