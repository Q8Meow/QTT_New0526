"""PR165-B upstream artifact discovery and sharded report loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from . import paths as p
from .json_io import read_json, records_from_payload


@dataclass(frozen=True)
class ArtifactDiscovery:
    required_inputs: tuple[str, ...]
    optional_present: dict[str, tuple[str, ...]]
    optional_missing: dict[str, tuple[str, ...]]
    missing_required_inputs: tuple[str, ...]


def discover_inputs(repo_root: Path) -> ArtifactDiscovery:
    missing_required = tuple(rel for rel in p.REQUIRED_INPUTS if not (repo_root / rel).exists())
    optional_present: dict[str, tuple[str, ...]] = {}
    optional_missing: dict[str, tuple[str, ...]] = {}
    for group, paths in p.OPTIONAL_INPUT_GROUPS.items():
        present = tuple(rel for rel in paths if (repo_root / rel).exists())
        missing = tuple(rel for rel in paths if not (repo_root / rel).exists())
        optional_present[group] = present
        optional_missing[group] = missing
    return ArtifactDiscovery(
        required_inputs=p.REQUIRED_INPUTS,
        optional_present=optional_present,
        optional_missing=optional_missing,
        missing_required_inputs=missing_required,
    )


def source_inputs_from_discovery(discovery: ArtifactDiscovery) -> list[str]:
    source_inputs = list(discovery.required_inputs)
    for paths in discovery.optional_present.values():
        source_inputs.extend(paths)
    return sorted(dict.fromkeys(source_inputs))


def load_report_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    root = repo_root / p.GENERATED_DIR / filename
    payload = read_json(root)
    rows = records_from_payload(payload)
    for shard_path in payload.get("shard_files") or []:
        shard_payload = read_json(p.resolve_repo_relative(repo_root, shard_path))
        rows.extend(records_from_payload(shard_payload))
    return rows


def index_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        if value is not None and str(value) not in indexed:
            indexed[str(value)] = row
    return indexed
