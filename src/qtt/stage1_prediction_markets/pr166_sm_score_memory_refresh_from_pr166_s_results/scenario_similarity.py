"""Condition-scoped scenario similarity computation."""

from __future__ import annotations

from typing import Any

from . import constants as c
from .normalization import round6


FIELD_ALIASES = {
    "market_scope": ("market_scope_bucket", "market_type"),
    "contract_type": ("contract_type", "market_type"),
    "order_type": ("order_type", "order_type_candidate"),
    "settlement_bucket": ("settlement_bucket", "market_maturity_bucket"),
    "probability_bucket": ("probability_bucket", "entry_price_bucket"),
    "data_quality_bucket": ("data_quality_bucket", "rank_confidence_tier"),
    "quantum_compatibility_bucket": ("quantum_compatibility_bucket", "quantum_formulation_class"),
    "source_quality_bucket": ("source_quality_bucket", "source_provenance_tier"),
}


def _value(row: dict[str, Any], field: str) -> str:
    if field in row and row[field] not in ("", None):
        return str(row[field])
    for alias in FIELD_ALIASES.get(field, ()):
        if alias in row and row[alias] not in ("", None):
            return str(row[alias])
    return ""


def scenario_similarity_score(condition_row: dict[str, Any], regime_row: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    weighted_match = 0.0
    available_weight = 0.0
    matched: list[str] = []
    materialization_actions: list[str] = []
    scope = condition_row.get("condition_scope")
    condition_scope = scope if isinstance(scope, dict) else condition_row
    for field, weight in c.SCENARIO_SIMILARITY_WEIGHTS.items():
        left = _value(condition_scope, field)
        right = _value(regime_row, field) or _value(condition_scope, field)
        if not left or not right:
            materialization_actions.append(f"PR166_SM_MATERIALIZE_BUCKET::{field}")
            continue
        available_weight += weight
        if left == right:
            weighted_match += weight
            matched.append(field)
    if available_weight == 0.0:
        return 0.5, matched, materialization_actions
    return round6(weighted_match / available_weight), matched, materialization_actions
