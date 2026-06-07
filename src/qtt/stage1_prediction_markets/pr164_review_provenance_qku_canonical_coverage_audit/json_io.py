"""Deterministic JSON IO helpers for PR164."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(payload: Any, *, compact: bool = False) -> str:
    if compact:
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def write_json(path: Path, payload: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_text(payload, compact=compact), encoding="utf-8")


def records_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return [row for row in payload["records"] if isinstance(row, dict)]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def stable_counter(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def index_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(row[key]): row for row in rows if key in row and row[key] is not None}
