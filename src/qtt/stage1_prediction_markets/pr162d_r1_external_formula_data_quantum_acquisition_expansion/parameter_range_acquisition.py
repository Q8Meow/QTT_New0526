"""External parameter range acquisition facade."""

from __future__ import annotations

from typing import Any

from .candidate_catalog import external_parameter_candidates


def parameter_range_acquisition_records(sources: list[dict[str, Any]], qku_pool: list[str]) -> list[dict[str, Any]]:
    return external_parameter_candidates(sources, qku_pool)
