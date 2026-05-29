"""Deterministic JSON helpers for PR161B."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def records(payload: Mapping[str, Any] | Any) -> list[dict[str, Any]]:
    if isinstance(payload, Mapping):
        raw = payload.get("records")
        if isinstance(raw, list):
            return [dict(item) for item in raw if isinstance(item, Mapping)]
    return []


def stable_counter(values: list[str]) -> dict[str, int]:
    output: dict[str, int] = {}
    for value in sorted(set(values)):
        output[value] = values.count(value)
    return output
