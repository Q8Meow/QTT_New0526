"""Mandatory external source acquisition facade."""

from __future__ import annotations

from typing import Any

from .source_catalog import external_source_records


def mandatory_external_source_candidates(qku_pool: list[str]) -> list[dict[str, Any]]:
    return external_source_records(qku_pool)
