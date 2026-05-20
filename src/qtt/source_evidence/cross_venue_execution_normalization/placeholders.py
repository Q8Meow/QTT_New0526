from __future__ import annotations

from typing import Any, Sequence

from .taxonomy import (
    ACTIVE_STAGE1_VENUES,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    FUTURE_PR_MAPPING,
    REQUIRED_PLACEHOLDER_DIMENSIONS,
)


_PLACEHOLDER_RECORD_TYPE_BY_DIMENSION = {
    "fill_integrity": "CROSS_VENUE_FILL_INTEGRITY_NORMALIZATION_PLACEHOLDER",
    "cashflow_pnl": "CROSS_VENUE_CASHFLOW_PNL_NORMALIZATION_PLACEHOLDER",
    "latency_component": "CROSS_VENUE_LATENCY_COMPONENT_NORMALIZATION_PLACEHOLDER",
    "settlement_finality": "CROSS_VENUE_SETTLEMENT_FINALITY_NORMALIZATION_PLACEHOLDER",
    "reconciliation": "CROSS_VENUE_RECONCILIATION_NORMALIZATION_PLACEHOLDER",
}

_RUNTIME_RECEIPT_REQUIRED = {
    "fill_integrity": False,
    "cashflow_pnl": True,
    "latency_component": False,
    "settlement_finality": False,
    "reconciliation": True,
}

_FUTURE_PRODUCTION_PR_BY_DIMENSION = {
    "fill_integrity": "PR114_PR115_PR116",
    "cashflow_pnl": "PR111_PR112_PR116",
    "latency_component": "PR114_PR115_PR116",
    "settlement_finality": "PR114_PR115_PR116",
    "reconciliation": "PR111_PR112_PR114_PR115_PR116",
}


def build_placeholder_normalization_records(
    venue_ids: Sequence[str] = ACTIVE_STAGE1_VENUES,
) -> list[dict[str, Any]]:
    return [
        {
            "placeholder_normalization_record_type": _PLACEHOLDER_RECORD_TYPE_BY_DIMENSION[
                dimension
            ],
            "placeholder_normalization_id": (
                f"PR128_PLACEHOLDER_{dimension.upper()}_NORMALIZATION_FIXTURE"
            ),
            "normalization_dimension": f"{dimension}_taxonomy",
            "venue_ids_in_scope": list(venue_ids),
            "accepted_source_evidence_required_flag": True,
            "runtime_receipt_required_flag": _RUNTIME_RECEIPT_REQUIRED[dimension],
            "production_value_populated": False,
            "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
            "production_cross_venue_normalization_authority": False,
            "production_arbitrage_comparability_authority": False,
            "future_pr_required_for_production_population": (
                _FUTURE_PRODUCTION_PR_BY_DIMENSION[dimension]
            ),
            "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
            "future_production_launch_path_preserved": True,
            **FUTURE_PR_MAPPING,
        }
        for dimension in REQUIRED_PLACEHOLDER_DIMENSIONS
    ]
