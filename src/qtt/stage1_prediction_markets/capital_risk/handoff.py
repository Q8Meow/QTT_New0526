from __future__ import annotations

from src.qtt.stage1_prediction_markets.capital_risk.field_map_constants import (
    ACTIVE_STAGE1_VENUES,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
)


def build_runtime_cash_downstream_handoff(
    *,
    field_map_ids: list[str],
    available_receipt_ids: list[str],
    gate_receipt_ids: list[str],
) -> dict[str, object]:
    return {
        "runtime_cash_downstream_handoff_id": "PR129_RUNTIME_CASH_DOWNSTREAM_HANDOFF_V1",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "source_repo_pr_label": "PR129",
        "venue_ids_in_scope": list(ACTIVE_STAGE1_VENUES),
        "runtime_cash_component_field_map_ids": field_map_ids,
        "runtime_available_after_commitments_receipt_ids": available_receipt_ids,
        "new_exposure_cash_gate_receipt_ids": gate_receipt_ids,
        "future_private_state_read_receipt_pr": "PR112",
        "future_credential_alias_secret_no_capture_pr": "PR113",
        "future_market_data_ingest_pr": "PR114",
        "future_orderbook_event_snapshot_pr": "PR115",
        "future_runtime_resolver_snapshot_pr": "PR116",
        "future_atomicrows_bridge_materialization_recommended_after_repo_pr": "PR135",
        "production_downstream_authority": False,
        "future_production_launch_path_preserved": True,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
