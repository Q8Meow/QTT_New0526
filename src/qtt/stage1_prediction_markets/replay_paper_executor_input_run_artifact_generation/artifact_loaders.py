"""Shared PR161F artifact loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .json_io import read_json, records_from_payload
from .paths import resolve_repo_relative


def load_report(repo_root: Path, path: Path) -> dict[str, Any]:
    payload = read_json(repo_root / path)
    if not isinstance(payload, dict):
        raise ValueError(f"PR161F expected report object: {path.as_posix()}")
    return payload


def load_records(repo_root: Path, path: Path) -> list[dict[str, Any]]:
    payload = load_report(repo_root, path)
    records = records_from_payload(payload)
    if records or not payload.get("sharded_flag"):
        return records
    merged: list[dict[str, Any]] = []
    for shard_ref in payload.get("shard_files") or []:
        shard_payload = read_json(resolve_repo_relative(repo_root, shard_ref))
        defaults = dict(shard_payload.get("compact_record_defaults") or {})
        merged.extend({**defaults, **record} for record in records_from_payload(shard_payload))
    return merged


def consume_text_artifacts(repo_root: Path, paths: tuple[Path, ...]) -> dict[str, bool]:
    status: dict[str, bool] = {}
    for path in paths:
        absolute = repo_root / path
        if absolute.exists() and absolute.is_file():
            absolute.read_text(encoding="utf-8", errors="replace")
            status[path.as_posix()] = True
        elif absolute.exists() and absolute.is_dir():
            for child in sorted(absolute.rglob("*")):
                if child.is_file() and child.suffix in {".py", ".json", ".md"}:
                    child.read_text(encoding="utf-8", errors="replace")
            status[path.as_posix()] = True
        else:
            status[path.as_posix()] = False
    return status


def consume_json_report_map(repo_root: Path, report_paths: dict[str, Path]) -> dict[str, dict[str, Any] | None]:
    consumed: dict[str, dict[str, Any] | None] = {}
    for name, path in report_paths.items():
        absolute = repo_root / path
        consumed[name] = load_report(repo_root, path) if absolute.exists() else None
    return consumed

