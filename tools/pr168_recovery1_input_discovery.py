#!/usr/bin/env python3
"""Load committed PR168-RANK3/RP3/MAP3/DATA lineage for Recovery1."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from tools.pr168_recovery1_config import GENERATED_ROOT, REPO_ROOT
from tools.pr168_rank3_config import REPORT_ALIASES as RANK3_REPORT_ALIASES
from tools.pr168_rank3_config import ROW_SHARDS as RANK3_ROW_SHARDS
from tools.pr168_rank3_config import SHARD_ROOT as RANK3_SHARD_ROOT
from tools.pr168_rp3_config import ROW_SHARDS as RP3_ROW_SHARDS
from tools.pr168_rp3_config import SHARD_ROOT as RP3_SHARD_ROOT


@dataclass(frozen=True)
class Recovery1Inputs:
    rank3_reports: dict[str, dict[str, Any]]
    rank3_rows: dict[str, list[dict[str, Any]]]
    rank3_manifests: dict[str, dict[str, Any]]
    rp3_rows: dict[str, list[dict[str, Any]]]
    rp3_manifests: dict[str, dict[str, Any]]
    map3_reports: dict[str, dict[str, Any]]
    upstream_reports: dict[str, dict[str, Any]]
    recovery1_test_files: tuple[str, ...]
    agent_crosswalk_present: bool
    agent_crosswalk_refs: tuple[str, ...]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_inputs() -> Recovery1Inputs:
    rank3_reports = _load_reports(RANK3_REPORT_ALIASES)
    rank3_rows, rank3_manifests = _load_shards(RANK3_SHARD_ROOT, RANK3_ROW_SHARDS)
    rp3_rows, rp3_manifests = _load_shards(RP3_SHARD_ROOT, RP3_ROW_SHARDS)
    map3_reports = _load_prefixed_reports("PR168_MAP3_")
    upstream_reports: dict[str, dict[str, Any]] = {}
    for prefix in (
        "PR168_DATA1",
        "PR168_DATA1A",
        "PR168_GFP2R",
        "PR168_RP2",
        "PR165_B",
        "PR165_C",
        "PR165_D",
        "PR165_D2",
        "PR165_D3",
        "PR166_S",
        "PR166_S2",
        "PR166_SF",
        "PR166_SM",
        "PR162E",
        "PR162E_Q",
        "PR166_Q",
        "PR166_QB",
        "PR166_QC",
        "PR167",
    ):
        upstream_reports.update(_load_prefixed_reports(prefix))
    test_root = REPO_ROOT / "tests" / "pr168_recovery1"
    test_files = tuple(sorted(str(path.relative_to(REPO_ROOT)).replace("\\", "/") for path in test_root.glob("test_*.py"))) if test_root.exists() else ()
    agent_refs = (
        "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
        "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
    )
    return Recovery1Inputs(
        rank3_reports=rank3_reports,
        rank3_rows=rank3_rows,
        rank3_manifests=rank3_manifests,
        rp3_rows=rp3_rows,
        rp3_manifests=rp3_manifests,
        map3_reports=map3_reports,
        upstream_reports=upstream_reports,
        recovery1_test_files=test_files,
        agent_crosswalk_present=all((REPO_ROOT / ref).exists() for ref in agent_refs),
        agent_crosswalk_refs=agent_refs,
    )


def _load_reports(aliases: dict[str, str]) -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    for logical_id, filename in aliases.items():
        path = GENERATED_ROOT / filename
        if path.exists():
            loaded[logical_id] = read_json(path)
    return loaded


def _load_shards(root: Path, shards: dict[str, str]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    manifests: dict[str, dict[str, Any]] = {}
    for key, filename in shards.items():
        path = root / filename
        rows[key] = read_jsonl(path)
        manifest_path = path.with_suffix(".manifest.json")
        if manifest_path.exists():
            manifests[key] = read_json(manifest_path)
    return rows, manifests


def _load_prefixed_reports(prefix: str) -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    for path in GENERATED_ROOT.glob(f"{prefix}*.report.json"):
        loaded[path.name] = read_json(path)
    return loaded
