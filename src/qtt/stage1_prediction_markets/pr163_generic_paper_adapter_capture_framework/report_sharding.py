"""Report sharding helpers.

PR163 currently emits compact monolithic registries. This module is retained so
future row-volume growth can switch to deterministic shards without changing
validator imports.
"""

from __future__ import annotations

from typing import Any


def shard_rows(rows: list[dict[str, Any]], shard_size: int) -> list[list[dict[str, Any]]]:
    if shard_size <= 0:
        return [rows]
    return [rows[index : index + shard_size] for index in range(0, len(rows), shard_size)]
