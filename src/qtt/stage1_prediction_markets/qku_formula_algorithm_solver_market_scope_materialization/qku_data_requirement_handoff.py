"""PR162C strict dataset requirement handoff from PR162B materialization."""

from __future__ import annotations

from typing import Any


def data_requirement_handoff_records(execution_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for record in execution_records:
        active = not str(record["stage1_prediction_market_activation_status"]).startswith("DORMANT_")
        needs_dataset = active and record["primary_market_scope"] in {
            "PREDICTION_MARKET_BINARY_EVENT_CONTRACT",
            "MARKET_AGNOSTIC_FEATURE",
            "MARKET_AGNOSTIC_MATH",
            "MARKET_AGNOSTIC_RISK",
            "MARKET_AGNOSTIC_OPTIMIZER",
        }
        if not needs_dataset:
            continue
        output.append(
            {
                "handoff_id": f"PR162B-PR162C-DATA-{record['qku_id']}",
                "qku_id": record["qku_id"],
                "formula_refs": record["formula_refs"],
                "algorithm_refs": record["algorithm_refs"],
                "required_market_scope": record["primary_market_scope"],
                "required_venue_scope": "KALSHI_POLYMARKET_FORECASTEX_STAGE1_CANDIDATE",
                "required_input_fields": record["input_field_refs"],
                "required_time_granularity": "event_market_snapshot_or_trade_bar",
                "required_minimum_rows": 1000,
                "required_pre_resolution_features": [
                    field
                    for field in record["input_field_refs"]
                    if field not in {"resolution_status", "settlement_value", "resolution_time"}
                ],
                "required_post_resolution_label_separation": [
                    "resolution_status",
                    "settlement_value",
                    "resolution_time",
                ],
                "replay_lane_required_flag": True,
                "paper_lane_required_flag": True,
                "quantum_feature_dataset_required_flag": bool(record["solver_mapping_refs"]),
                "priority_class": "PR162C_STRICT_DATA_EXPANSION_REQUIRED",
                "downstream_pr_route": "PR162C_STRICT_DATA_EXPANSION",
                "pr162r_ready_flag": False,
                "created_by_pr": "PR162B",
            }
        )
    return output
