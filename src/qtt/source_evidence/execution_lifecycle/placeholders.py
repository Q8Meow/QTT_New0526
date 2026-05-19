from __future__ import annotations

from typing import Any


PLACEHOLDER_SPECS: dict[str, dict[str, Any]] = {
    "fill_integrity": {
        "placeholder_record_type": "FILL_INTEGRITY_PLACEHOLDER",
        "future_pr_required_for_production_population": "PR127_DOWNSTREAM_ACCEPTED_SOURCE_AND_RUNTIME_RECEIPT_GATE",
        "runtime_receipt_required_flag": False,
    },
    "cashflow_pnl": {
        "placeholder_record_type": "CASHFLOW_PNL_PLACEHOLDER",
        "future_pr_required_for_production_population": "PR111",
        "runtime_receipt_required_flag": True,
    },
    "latency_component": {
        "placeholder_record_type": "LATENCY_COMPONENT_PLACEHOLDER",
        "future_pr_required_for_production_population": "PR114_PR115_PR116",
        "runtime_receipt_required_flag": False,
    },
    "settlement_finality": {
        "placeholder_record_type": "SETTLEMENT_FINALITY_PLACEHOLDER",
        "future_pr_required_for_production_population": "PR147",
        "runtime_receipt_required_flag": False,
    },
    "reconciliation": {
        "placeholder_record_type": "RECONCILIATION_PLACEHOLDER",
        "future_pr_required_for_production_population": "PR147",
        "runtime_receipt_required_flag": True,
    },
}

FUTURE_PR_MAPPING = {
    "cross_venue_normalization_future_pr": "PR110",
    "runtime_cash_component_field_map_future_pr": "PR111",
    "private_state_read_receipt_future_pr": "PR112",
    "market_data_ingest_future_pr": "PR114",
    "orderbook_event_snapshot_future_pr": "PR115",
    "runtime_resolver_snapshot_future_pr": "PR116",
}


def build_placeholder_record(
    *,
    model_id: str,
    venue_id: str,
    target_semantic_family: str,
    deterministic_fixture_time: str,
    fixture_authority_class: str,
) -> dict[str, Any]:
    spec = PLACEHOLDER_SPECS[target_semantic_family]
    placeholder_id = (
        f"{model_id}__PLACEHOLDER_{target_semantic_family.upper()}"
    )
    return {
        "placeholder_record_type": spec["placeholder_record_type"],
        "placeholder_id": placeholder_id,
        "per_venue_execution_lifecycle_model_id": model_id,
        "venue_id": venue_id,
        "target_semantic_family": target_semantic_family,
        "accepted_source_evidence_required_flag": True,
        "runtime_receipt_required_flag": spec["runtime_receipt_required_flag"],
        "production_value_populated": False,
        "fixture_authority_class": fixture_authority_class,
        "production_execution_lifecycle_authority": False,
        "future_pr_required_for_production_population": spec[
            "future_pr_required_for_production_population"
        ],
        "future_pr_mapping": dict(FUTURE_PR_MAPPING),
        "deterministic_fixture_time": deterministic_fixture_time,
    }
