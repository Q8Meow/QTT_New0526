#!/usr/bin/env python3
"""Load committed RP3/MAP3/upstream artifacts for PR168-RANK3."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from tools.pr168_rank3_config import GENERATED_ROOT, REPO_ROOT
from tools.pr168_rp3_config import REPORT_ALIASES as RP3_REPORT_ALIASES
from tools.pr168_rp3_config import ROW_SHARDS as RP3_ROW_SHARDS
from tools.pr168_rp3_config import SHARD_ROOT as RP3_SHARD_ROOT


@dataclass(frozen=True)
class RP3Inputs:
    reports: dict[str, dict[str, Any]]
    rows: dict[str, list[dict[str, Any]]]
    shard_manifests: dict[str, dict[str, Any]]
    map3_reports: dict[str, dict[str, Any]]
    upstream_reports: dict[str, dict[str, Any]]
    rp3_test_files: tuple[str, ...]
    agent_crosswalk_present: bool
    agent_crosswalk_refs: tuple[str, ...]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_inputs() -> RP3Inputs:
    reports: dict[str, dict[str, Any]] = {}
    for logical_id, filename in RP3_REPORT_ALIASES.items():
        path = GENERATED_ROOT / filename
        if path.exists():
            reports[logical_id] = read_json(path)

    rows: dict[str, list[dict[str, Any]]] = {}
    manifests: dict[str, dict[str, Any]] = {}
    for key, filename in RP3_ROW_SHARDS.items():
        path = RP3_SHARD_ROOT / filename
        rows[key] = read_jsonl(path)
        manifest_path = path.with_suffix(".manifest.json")
        if manifest_path.exists():
            manifests[key] = read_json(manifest_path)

    map3_reports = _load_prefixed_reports("PR168_MAP3_")
    upstream_reports: dict[str, dict[str, Any]] = {}
    for prefix in ("PR168_DATA1", "PR168_DATA1A", "PR168_GFP2R", "PR168_RP2", "PR165_D2"):
        upstream_reports.update(_load_prefixed_reports(prefix))

    test_files = tuple(
        sorted(
            str(path.relative_to(REPO_ROOT)).replace("\\", "/")
            for path in (REPO_ROOT / "tests" / "pr168_rp3").glob("test_*.py")
        )
    )
    agent_refs = (
        "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
        "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
    )
    agent_present = all((REPO_ROOT / ref).exists() for ref in agent_refs)
    return RP3Inputs(
        reports=reports,
        rows=rows,
        shard_manifests=manifests,
        map3_reports=map3_reports,
        upstream_reports=upstream_reports,
        rp3_test_files=test_files,
        agent_crosswalk_present=agent_present,
        agent_crosswalk_refs=agent_refs,
    )


def _load_prefixed_reports(prefix: str) -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    for path in GENERATED_ROOT.glob(f"{prefix}*.report.json"):
        loaded[path.name] = read_json(path)
    return loaded
