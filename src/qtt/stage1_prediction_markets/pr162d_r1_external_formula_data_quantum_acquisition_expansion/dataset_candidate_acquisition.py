"""Dataset candidate acquisition facade."""

from __future__ import annotations

from typing import Any

from .candidate_catalog import dataset_candidates


def dataset_candidate_records(sources: list[dict[str, Any]], qku_pool: list[str]) -> list[dict[str, Any]]:
    return dataset_candidates(sources, qku_pool)
