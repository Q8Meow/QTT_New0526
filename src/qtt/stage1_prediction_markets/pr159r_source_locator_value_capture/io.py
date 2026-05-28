"""Deterministic JSON helpers for PR159R."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dump(payload), encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def record_count(payload: Any) -> int | None:
    if isinstance(payload, dict):
        if isinstance(payload.get("record_count"), int):
            return int(payload["record_count"])
        if isinstance(payload.get("records"), list):
            return len(payload["records"])
    if isinstance(payload, list):
        return len(payload)
    return None


def schema_version(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("schema_version", "schema_id", "version"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, int):
            return str(value)
    return None


def stable_counter(records: Iterable[Mapping[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(item.get(field)) for item in records).items()))

