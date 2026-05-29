"""Deterministic IO helpers for PR161A."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping


def json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dump(payload), encoding="utf-8")


def as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def stable_counter(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def records(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [as_mapping(record) for record in as_list(payload.get("records"))]

