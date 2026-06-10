"""Artifact discovery and report loading for PR165-C."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import paths as p
from .json_io import read_json, records_from_payload


@dataclass(frozen=True)
class InputDiscovery:
    required_inputs: tuple[str, ...]
    missing_required_inputs: tuple[str, ...]
    optional_present: dict[str, tuple[str, ...]]
    optional_missing: dict[str, tuple[str, ...]]


def discover_inputs(repo_root: Path) -> InputDiscovery:
    required_inputs = tuple(p.normalize_repo_ref(rel) for rel in p.REQUIRED_INPUTS)
    missing = tuple(rel for rel in required_inputs if not p.resolve_repo_relative(repo_root, rel).exists())
    optional_present: dict[str, tuple[str, ...]] = {}
    optional_missing: dict[str, tuple[str, ...]] = {}
    for group, path_refs in p.OPTIONAL_INPUT_GROUPS.items():
        normalized_refs = tuple(p.normalize_repo_ref(rel) for rel in path_refs)
        present = tuple(rel for rel in normalized_refs if p.resolve_repo_relative(repo_root, rel).exists())
        absent = tuple(rel for rel in normalized_refs if not p.resolve_repo_relative(repo_root, rel).exists())
        optional_present[group] = present
        optional_missing[group] = absent
    return InputDiscovery(
        required_inputs=required_inputs,
        missing_required_inputs=missing,
        optional_present=optional_present,
        optional_missing=optional_missing,
    )


def load_report_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    payload = read_json(repo_root / p.GENERATED_DIR / filename)
    if not payload.get("sharded_flag"):
        return records_from_payload(payload)
    rows: list[dict[str, Any]] = []
    for shard_path in payload.get("shard_files") or []:
        rows.extend(records_from_payload(read_json(p.resolve_repo_relative(repo_root, shard_path))))
    return rows


def index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows if key in row}


def group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if key in row:
            grouped.setdefault(str(row[key]), []).append(row)
    return grouped


def discover_agent_related_reports(repo_root: Path) -> tuple[str, ...]:
    patterns = ("agent", "router", "handoff", "task", "governance", "dashboard", "commander", "lineage", "ownership", "qku")
    generated = repo_root / p.GENERATED_DIR
    if not generated.exists():
        return ()
    matches = []
    for path in sorted(generated.rglob("*")):
        if path.is_file() and any(pattern in path.name.lower() for pattern in patterns):
            matches.append(p.to_repo_posix(path, repo_root))
    return tuple(matches)
