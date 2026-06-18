"""Path and JSON helpers for PR162E reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def repo_relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"expected object payload: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def records_from_payload(repo_root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(payload.get("records") or [])
    shard_paths = payload.get("shard_files") or payload.get("shard_paths") or []
    for shard in shard_paths:
        shard_path = repo_root / str(shard)
        if not shard_path.exists():
            continue
        shard_payload = read_json(shard_path)
        rows.extend(shard_payload.get("records") or [])
    return rows


def read_report(repo_root: Path, filename: str) -> tuple[bool, dict[str, Any], list[dict[str, Any]]]:
    path = repo_root / "docs/master_plan/generated" / filename
    if not path.exists():
        return False, {}, []
    payload = read_json(path)
    return True, payload, records_from_payload(repo_root, payload)
