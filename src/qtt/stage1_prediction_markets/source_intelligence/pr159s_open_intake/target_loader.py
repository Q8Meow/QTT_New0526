"""Load the PR159S 868-target input inventory from prior PR159R artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import constants as c
from .io import as_list, as_mapping, read_json


def load_input_targets(root: Path) -> list[dict[str, Any]]:
    payload = as_mapping(read_json(root / c.PR159R_UNRESOLVED_FILL_PATH))
    records = [dict(as_mapping(record)) for record in as_list(payload.get("records"))]
    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        target_population = str(record.get("target_population"))
        source_family = "ATOMICROWS" if target_population.startswith("ATOMICROWS") else "PR154"
        normalized.append(
            {
                **record,
                "pr159s_sequence": index,
                "input_inventory_source": c.PR159R_UNRESOLVED_FILL_PATH.as_posix(),
                "source_family": source_family,
                "atomicrows_linked_flag": source_family == "ATOMICROWS",
            }
        )
    return normalized


def inventory_counts(records: list[Mapping[str, Any]]) -> dict[str, int]:
    atomicrows = sum(1 for record in records if record.get("source_family") == "ATOMICROWS")
    pr154 = sum(1 for record in records if record.get("source_family") == "PR154")
    return {
        "input_total": len(records),
        "atomicrows_input": atomicrows,
        "pr154_input": pr154,
    }

