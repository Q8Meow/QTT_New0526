"""Report sharding placeholder for PR162D-R1.

Current PR162D-R1 reports stay below the large-report threshold, so no shard
files are emitted. The module exists to keep the implementation surface
compatible with adjacent PR162D tooling.
"""

from __future__ import annotations

from typing import Any


def shard_report_if_needed(filename: str, payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    return payload, []
