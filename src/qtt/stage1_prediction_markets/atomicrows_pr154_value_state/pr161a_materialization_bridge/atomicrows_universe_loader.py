"""AtomicRows universe loader for PR161A."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .io import as_list, as_mapping, read_json


def load_atomicrows_universe(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for shard_path in sorted((root / c.PR157_ATOMICROWS_SHARD_DIR).glob("*.json")):
        payload = as_mapping(read_json(shard_path))
        records.extend(dict(record) for record in as_list(payload.get("records")))
    return sorted(records, key=lambda item: str(item.get("row_id_or_row_ref") or item.get("parameter_id")))


def atomicrows_row_id(record: dict[str, Any]) -> str:
    return str(record.get("row_id_or_row_ref") or record.get("parameter_id"))

