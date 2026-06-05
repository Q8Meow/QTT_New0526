"""DatasetNormalizationReceiptV1 records for PR162R-B."""

from __future__ import annotations

from typing import Any

from .binding_family_classifier import target_field, unit_for_family
from .source_acquisition_pipeline import source_candidate_for_task


def build_normalization_receipts(
    tasks: list[dict[str, Any]],
    source_candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, task in enumerate(tasks, start=1):
        source = source_candidate_for_task(task, source_candidates)
        family = task["binding_family"]
        rows.append(
            {
                "normalization_receipt_id": f"PR162R_B_NORMALIZATION_RECEIPT::{index:04d}",
                "source_candidate_id": source["source_candidate_id"],
                "binding_task_id": task["binding_task_id"],
                "binding_family": family,
                "raw_field_name": target_field(family),
                "normalized_field_name": target_field(family),
                "input_unit": unit_for_family(family),
                "output_unit": unit_for_family(family),
                "input_scale": task["scale"],
                "output_scale": task["scale"],
                "timestamp_input_policy": "UTC_ISO8601_OR_FIXTURE_SEQUENCE",
                "timestamp_output_policy": "UTC_ISO8601",
                "timezone_policy": "UTC_ONLY",
                "event_time_policy": "event_time_distinct_from_receive_time",
                "receive_time_policy": "receive_time_optional_for_replay_required_for_latency_fixture",
                "market_id_policy": "deterministic_market_id_required",
                "outcome_id_policy": "YES_NO_OUTCOME_IDS_REQUIRED",
                "price_scale_policy": "binary_price_bounds_0_to_1",
                "side_policy": "YES_NO_BUY_SELL_ENUM_WHERE_APPLICABLE",
                "orderbook_depth_policy": "top_levels_sorted_best_to_worst",
                "settlement_label_policy": "YES_NO_VOID_ENUM",
                "missingness_policy": "explicit_null_for_unavailable_non_required_fixture_fields",
                "duplicate_policy": "deduplicate_by_market_outcome_timestamp_sequence",
                "staleness_policy": "observation_timestamp_minus_source_timestamp_seconds",
                "validation_checks": [
                    "schema_parse_ok",
                    "timestamp_parse_ok",
                    "unit_scale_ok",
                    "price_bounds_ok",
                    "side_enum_ok",
                    "settlement_label_enum_ok",
                    "no_private_state_fields",
                    "no_live_order_authority",
                    "no_source_acceptance",
                ],
                "deterministic_transform_receipt": "PR162R_B_DETERMINISTIC_NORMALIZATION_NO_RUNTIME_RETRIEVAL",
                "replay_allowed": task["replay_or_paper_lane"] in {"REPLAY", "BOTH"},
                "paper_allowed": task["replay_or_paper_lane"] in {"PAPER", "BOTH"},
                "live_allowed": False,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def receipt_for_task(task: dict[str, Any], receipts: list[dict[str, Any]]) -> dict[str, Any]:
    for row in receipts:
        if row["binding_task_id"] == task["binding_task_id"]:
            return row
    raise KeyError(task["binding_task_id"])
