"""Deterministic IO helpers for PR158."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


def json_dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dump(payload), encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def stable_counter(values: list[str] | tuple[str, ...]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def stable_counter_from_records(records: list[Mapping[str, Any]], field: str) -> dict[str, int]:
    return stable_counter([str(record.get(field)) for record in records])


def text(value: Any) -> str:
    return "" if value is None else str(value)

