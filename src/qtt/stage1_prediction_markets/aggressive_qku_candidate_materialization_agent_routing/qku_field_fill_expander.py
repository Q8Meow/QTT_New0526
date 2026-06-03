"""QKU field fill expansion records."""

from __future__ import annotations

from typing import Any

from .deterministic_id import deterministic_id


FIELD_FILL_METHODS = (
    "SOURCE_DERIVED_PARTIAL_CANDIDATE",
    "FORMULA_DERIVED_CANDIDATE",
    "DEFAULT_RANGE_CANDIDATE",
    "RELATED_QKU_INFERRED_CANDIDATE",
    "REPLAY_PAPER_ROUTED_OPEN_FIELD",
)


def field_fill_records(reinterpretations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, item in enumerate(reinterpretations):
        method = FIELD_FILL_METHODS[index % len(FIELD_FILL_METHODS)]
        records.append(
            {
                "field_fill_id": deterministic_id(
                    "PR162D-FIELD-FILL", item["qku_id"], index, size=10
                ),
                "qku_id": item["qku_id"],
                "reinterpretation_ref": item["reinterpretation_id"],
                "candidate_field_refs": [
                    "price_candidate",
                    "probability_candidate",
                    "volume_candidate",
                    "timestamp_candidate",
                    "feature_value_candidate",
                ],
                "field_fill_method": method,
                "field_fill_status": item["pr162d_progress_status"],
                "materialized_value_type": (
                    "PARTIAL_VALUE_OR_RANGE" if "OPEN" not in item["pr162d_progress_status"] else "OPEN_TARGET"
                ),
                "source_refs": ["PR162D-CANDIDATE-SOURCE-INTAKE"],
                "formula_refs": ["PR162D-FORMULA-EXPRESSION-CATALOG"],
                "missing_input_behavior": "KEEP_CANDIDATE_OPEN_AND_ROUTE_TO_REPLAY_PAPER",
                "candidate_or_provisional_flag": True,
                "replay_paper_candidate_flag": True,
                "live_order_authority": False,
            }
        )
    return records
