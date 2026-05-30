"""Deterministic artifact discovery for PR161D inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .io import read_json, records_from_payload


def selected_artifact_paths(repo_root: Path) -> dict[str, Path | None]:
    paths: dict[str, Path | None] = {}
    for key, rel_path in c.PR161C_REPORT_PATHS.items():
        path = repo_root / rel_path
        paths[f"pr161c_{key}"] = rel_path if path.exists() else None
    for key, rel_path in c.PR136_CONTROL_PLANE_PATHS.items():
        path = repo_root / rel_path
        paths[f"control_plane_{key}"] = rel_path if path.exists() else None
    for name in c.PR82_PR96_ARTIFACT_NAMES:
        path = repo_root / c.GENERATED_DIR / name
        if path.exists():
            paths[f"prior_static_{name}"] = c.GENERATED_DIR / name
    return paths


def read_report(repo_root: Path, rel_path: Path) -> dict[str, Any]:
    payload = read_json(repo_root / rel_path)
    if not isinstance(payload, dict):
        return {"records": records_from_payload(payload)}
    return payload


def read_report_records(repo_root: Path, rel_path: Path) -> list[dict[str, Any]]:
    payload = read_report(repo_root, rel_path)
    records = records_from_payload(payload)
    if records or not payload.get("sharded_flag"):
        return records
    shard_records: list[dict[str, Any]] = []
    for shard_file in payload.get("shard_files") or []:
        shard_path = repo_root / str(shard_file)
        if shard_path.exists():
            shard_records.extend(records_from_payload(read_json(shard_path)))
    return shard_records
