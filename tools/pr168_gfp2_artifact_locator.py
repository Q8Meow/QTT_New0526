#!/usr/bin/env python3
"""Artifact discovery for PR168-GFP2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.pr168_gfp2_constants import REQUIRED_UPSTREAM_ARTIFACTS


def locate_required_artifacts(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in REQUIRED_UPSTREAM_ARTIFACTS:
        path = repo_root / rel
        rows.append(
            {
                "artifact_path": rel,
                "artifact_family": _family(rel),
                "required_for_pr168_gfp2": True,
                "found_flag": path.exists(),
                "missing_reason": None if path.exists() else "REQUIRED_UPSTREAM_ARTIFACT_NOT_FOUND",
                "read_status": "FOUND_AND_READ_OR_STRUCTURED_LOADED" if path.exists() else "MISSING_GAP_ROUTED",
                "upstream_refs": [rel],
                "downstream_refs": ["PR168_GFP2_FullUniverseInputDiscovery.report.json"],
                "owning_agent": "Governance Agent",
                "consumer_agents": ["Replay Paper Recompute Agent", "Ranking Agent"],
                "downstream_prs": ["PR168-RP2", "PR168-RANK2"],
                "value_type": "UPSTREAM_ARTIFACT",
                "evidence_tier": "UNKNOWN_OR_UNVERIFIED",
                "authority_class": "INPUT_DISCOVERY_NOT_SOURCE_TRUTH",
                "validation_refs": ["tools/pr168_gfp2_validator.py"],
                "test_refs": ["tests/pr168_gfp2/test_pr168_gfp2_pr165_d2_agent_crosswalk_required.py"],
                "no_orphan_status": "CONNECTED_TO_DECLARED_CONSUMER",
                "terminal_by_nature_flag": False,
                "terminal_reason_code": None,
                "repair_route_if_gap": "PR168_GFP2_MissingAgentCrosswalkBlocker.report.json"
                if "PR165_D2_Agent" in rel and not path.exists()
                else "PR168_GFP2_RealDataMissingProofComponentQueue.report.json",
            }
        )
    return rows


def missing_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not row["found_flag"]]


def pr165_d2_missing(rows: list[dict[str, Any]]) -> bool:
    required = {
        "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
        "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
    }
    found = {str(row["artifact_path"]) for row in rows if row["found_flag"]}
    return bool(required - found)


def _family(rel: str) -> str:
    if "PR165_D2" in rel:
        return "PR165_D2_AGENT_ARTIFACT"
    if "PR168_GFP" in rel:
        return "PR168_GFP_UPSTREAM"
    if "PR168_RP" in rel:
        return "PR168_RP_UPSTREAM"
    if "PR168_RANK" in rel:
        return "PR168_RANK_UPSTREAM"
    if "source_evidence" in rel:
        return "SOURCE_EVIDENCE"
    if "roadmap" in rel:
        return "ROADMAP"
    return "MASTER_PLAN"
