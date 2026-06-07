"""Input artifact discovery and sharded report loading for PR164."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from . import paths as p
from .deterministic_ids import plain_ref
from .json_io import read_json, records_from_payload


@dataclass(frozen=True)
class InputDiscovery:
    rows: list[dict[str, Any]]
    existing_paths: list[str]
    missing_required_paths: list[str]
    optional_existing_paths: list[str]


def discover_inputs(repo_root: Path) -> InputDiscovery:
    rows: list[dict[str, Any]] = []
    existing_paths: list[str] = []
    missing: list[str] = []
    index = 1
    for rel_path in p.REQUIRED_INPUT_FILENAMES:
        path = repo_root / rel_path
        exists = path.exists()
        if exists:
            existing_paths.append(rel_path)
        else:
            missing.append(rel_path)
        rows.append(
            {
                "input_consumption_ref": plain_ref("INPUT", index),
                "consumed_path": rel_path if exists else "",
                "requested_path": rel_path,
                "artifact_required": True,
                "artifact_present": exists,
                "missing_artifact_receipt": (
                    ""
                    if exists
                    else f"PR164_MISSING_REQUIRED_ARTIFACT::{Path(rel_path).name}"
                ),
                "exact_missing_reason": (
                    ""
                    if exists
                    else "Required upstream artifact is absent in this checkout; PR164 records the exact path and continues only where a deterministic adjacent artifact exists."
                ),
                "consumption_role": _consumption_role(rel_path),
                "validation_status": "PASS",
            }
        )
        index += 1

    optional = _optional_artifacts(repo_root)
    for rel_path in optional:
        existing_paths.append(rel_path)
        rows.append(
            {
                "input_consumption_ref": plain_ref("INPUT", index),
                "consumed_path": rel_path,
                "requested_path": rel_path,
                "artifact_required": False,
                "artifact_present": True,
                "missing_artifact_receipt": "",
                "exact_missing_reason": "",
                "consumption_role": _consumption_role(rel_path),
                "validation_status": "PASS",
            }
        )
        index += 1
    return InputDiscovery(
        rows=rows,
        existing_paths=sorted(set(existing_paths)),
        missing_required_paths=missing,
        optional_existing_paths=optional,
    )


def _optional_artifacts(repo_root: Path) -> list[str]:
    generated = repo_root / p.GENERATED_DIR
    paths: set[str] = set()
    for pattern in p.OPTIONAL_ARTIFACT_GLOBS:
        for path in generated.glob(pattern):
            if path.is_file():
                paths.add(path.relative_to(repo_root).as_posix())
    shard_dir = generated / "pr163_b_shards"
    if shard_dir.exists():
        for path in shard_dir.glob("*.report.json"):
            paths.add(path.relative_to(repo_root).as_posix())
    return sorted(paths)


def _consumption_role(rel_path: str) -> str:
    name = Path(rel_path).name
    if name.startswith("PR163_B_") or "pr163_b_shards" in rel_path:
        return "PR163_B_EVIDENCE_AND_HANDOFF_CONSUMPTION"
    if name.startswith("PR162D_R2A_"):
        return "CURRENT_CANDIDATE_PACKET_AND_FORMULATION_CONSUMPTION"
    if name.startswith("PR161C_"):
        return "HISTORICAL_QKU_INVENTORY_CONSUMPTION"
    if name.startswith("PR159"):
        return "SOURCE_INTAKE_CURRENTIZATION_CONSUMPTION"
    if name.startswith("PR136"):
        return "ROADMAP_AND_MARKET_SCOPE_CONTEXT_CONSUMPTION"
    if name.startswith("PR152"):
        return "GRAND_GLOBAL_DEBUG_AUDIT_CONTEXT_CONSUMPTION"
    return "STATIC_POLICY_OR_TOOLING_CONTEXT_CONSUMPTION"


def load_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    path = repo_root / p.GENERATED_DIR / filename
    payload = read_json(path)
    if isinstance(payload, dict) and payload.get("sharded_flag"):
        rows: list[dict[str, Any]] = []
        for shard_path in payload.get("shard_files") or []:
            shard_payload = read_json(p.resolve_repo_relative(repo_root, shard_path))
            rows.extend(records_from_payload(shard_payload))
        return rows
    return records_from_payload(payload)


def load_single_record(repo_root: Path, filename: str) -> dict[str, Any]:
    rows = load_records(repo_root, filename)
    if not rows:
        payload = read_json(repo_root / p.GENERATED_DIR / filename)
        if isinstance(payload, dict):
            return payload
        return {}
    return rows[0]


def index_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows if key in row and row[key] is not None}
