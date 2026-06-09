"""Stable JSON helpers for PR165-C artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def json_text(payload: Any, *, compact: bool = False) -> str:
    separators = (",", ":") if compact else (",", ": ")
    return json.dumps(
        payload,
        ensure_ascii=True,
        indent=None if compact else 2,
        sort_keys=True,
        separators=separators,
    ) + "\n"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_text(payload, compact=compact), encoding="utf-8")


def records_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("records")
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]
