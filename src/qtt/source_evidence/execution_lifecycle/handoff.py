from __future__ import annotations

from typing import Any, Mapping, Sequence


REQUIRED_FUTURE_NORMALIZATION_DIMENSIONS: tuple[str, ...] = (
    "execution_phase_taxonomy",
    "execution_transition_taxonomy",
    "fill_integrity_taxonomy",
    "cashflow_pnl_taxonomy",
    "latency_component_taxonomy",
    "settlement_finality_taxonomy",
    "reconciliation_taxonomy",
    "order_state_taxonomy",
    "cancellation_state_taxonomy",
    "partial_fill_state_taxonomy",
    "rejection_error_taxonomy",
)


def build_cross_venue_normalization_handoff(
    *,
    model_records: Sequence[Mapping[str, Any]],
    deterministic_fixture_time: str,
    fixture_authority_class: str,
) -> dict[str, Any]:
    lifecycle_model_ids = [
        str(record["per_venue_execution_lifecycle_model_id"])
        for record in sorted(model_records, key=lambda item: str(item["venue_id"]))
    ]
    return {
        "cross_venue_normalization_handoff_id": (
            "PR127_CROSS_VENUE_NORMALIZATION_HANDOFF_FIXTURE_V1"
        ),
        "fixture_authority_class": fixture_authority_class,
        "source_repo_pr_label": "PR127",
        "future_roadmap_pr": "PR110",
        "venue_ids_in_scope": ["KALSHI", "POLYMARKET", "FORECASTEX_IBKR"],
        "lifecycle_model_ids": lifecycle_model_ids,
        "placeholder_semantic_families_requiring_future_source_support": [
            "fill_integrity",
            "cashflow_pnl",
            "latency_component",
            "settlement_finality",
            "reconciliation",
        ],
        "required_future_normalization_dimensions": list(
            REQUIRED_FUTURE_NORMALIZATION_DIMENSIONS
        ),
        "production_cross_venue_normalization_authority": False,
        "production_arbitrage_comparability_authority": False,
        "future_cross_venue_normalization_path_preserved": True,
        "deterministic_fixture_time": deterministic_fixture_time,
    }
