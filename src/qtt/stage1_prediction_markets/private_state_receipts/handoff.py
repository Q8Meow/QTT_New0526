from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.private_state_receipts.request import (
    ACTIVE_STAGE1_VENUES,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
)


def build_private_state_downstream_handoff(
    *,
    private_state_read_receipts: list[Mapping[str, object]],
    account_wallet_balance_receipts: list[Mapping[str, object]],
    linkage_receipts: list[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "private_state_downstream_handoff_id": "PR130_PRIVATE_STATE_DOWNSTREAM_HANDOFF_V1",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "source_repo_pr_label": "PR130",
        "venue_ids_in_scope": list(ACTIVE_STAGE1_VENUES),
        "private_state_read_receipt_ids": [
            record["private_state_read_receipt_id"]
            for record in private_state_read_receipts
        ],
        "account_wallet_balance_receipt_ids": [
            record["account_wallet_balance_receipt_id"]
            for record in account_wallet_balance_receipts
        ],
        "private_state_to_runtime_cash_linkage_receipt_ids": [
            record["private_state_to_runtime_cash_linkage_receipt_id"]
            for record in linkage_receipts
        ],
        "future_credential_alias_secret_no_capture_pr": "PR113",
        "future_market_data_ingest_pr": "PR114",
        "future_orderbook_event_snapshot_pr": "PR115",
        "future_runtime_resolver_snapshot_pr": "PR116",
        "future_atomicrows_bridge_materialization_recommended_after_repo_pr": "PR135",
        "production_downstream_authority": False,
        "future_production_launch_path_preserved": True,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
