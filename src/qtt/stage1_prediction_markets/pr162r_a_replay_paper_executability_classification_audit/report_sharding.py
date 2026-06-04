"""Report sharding placeholder for PR162R-A."""

from __future__ import annotations

from typing import Any


def shard_report_if_needed(filename: str, payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    return payload, []
