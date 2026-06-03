"""External formula acquisition facade and deterministic placeholders."""

from __future__ import annotations

from typing import Any

from .candidate_catalog import external_formula_candidates


def formula_acquisition_records(sources: list[dict[str, Any]], qku_pool: list[str]) -> list[dict[str, Any]]:
    return external_formula_candidates(sources, qku_pool)


def compute_candidate_formula(inputs: dict[str, Any]) -> dict[str, Any]:
    return {"candidate_only_result": inputs, "live_order_authority": False}
