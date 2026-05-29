"""Source candidate mapping facade for PR161A."""

from __future__ import annotations

from typing import Any, Mapping


def source_records_by_target(records: list[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    mapped: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        for key in ("atomicrows_mapping", "pr154_mapping"):
            for target_id in record.get(key, []) if isinstance(record.get(key), list) else []:
                mapped.setdefault(str(target_id), []).append(record)
    return mapped

