from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy


def build_downstream_handoff(
    input_locks: list[Mapping[str, object]],
    bindings: list[Mapping[str, object]],
    orderbook_snapshots: list[Mapping[str, object]],
    event_state_snapshots: list[Mapping[str, object]],
    integrity_receipts: list[Mapping[str, object]],
) -> dict[str, object]:
    scope_value = "PREDICTION_MARKETS_GENERAL"
    return {
        **policy.common_record_fields(
            "ORDERBOOK_EVENT_STATE_SNAPSHOT_DOWNSTREAM_HANDOFF",
            scope_value,
        ),
        "handoff_id": "PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_DOWNSTREAM_HANDOFF_V1",
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "upstream_prs": [
            "PR105",
            "PR106",
            "PR107",
            "PR108",
            "PR109",
            "PR110",
            "PR111",
            "PR112",
            "PR113",
            "PR114",
        ],
        "downstream_prs": list(policy.DOWNSTREAM_PR_IDS),
        "future_atomicrows_bridge_recommended_after_repo_pr": (
            policy.RECOMMENDED_ATOMICROWS_BRIDGE_AFTER_REPO_PR
        ),
        "future_atomicrows_bridge_candidate_repo_pr": (
            policy.RECOMMENDED_ATOMICROWS_BRIDGE_CANDIDATE_REPO_PR
        ),
        "venue_specific_scope": list(policy.STAGE1_VENUE_IDS),
        "shared_scope": list(policy.SHARED_SCOPE_IDS),
        "snapshot_input_lock_refs": [record["input_lock_id"] for record in input_locks],
        "snapshot_builder_binding_refs": [record["binding_id"] for record in bindings],
        "orderbook_snapshot_refs": [record["snapshot_id"] for record in orderbook_snapshots],
        "event_state_snapshot_refs": [record["snapshot_id"] for record in event_state_snapshots],
        "snapshot_integrity_receipt_refs": [
            record["integrity_receipt_id"] for record in integrity_receipts
        ],
        "contains_fixture_orderbook_snapshot": True,
        "contains_fixture_event_state_snapshot": True,
        "contains_live_orderbook_snapshot": False,
        "contains_live_event_state_snapshot": False,
        "contains_live_market_data": False,
        "contains_live_credentials": False,
        "contains_private_state_payload": False,
        "contains_runtime_resolver_snapshot": False,
        "contains_historical_dataset_digest": False,
        "contains_feature_vector": False,
        "contains_trading_signal": False,
        "contains_quantum_feature_vector": False,
        "contains_quantum_optimizer_input": False,
        "contains_quantum_trading_signal": False,
        "contains_order_authority": False,
        "contains_profit_evidence": False,
        "contains_quantum_execution": False,
        "contains_atomicrows_materialized_rows": False,
        "contains_atomicrows_bundle": False,
        "contains_atomicrows_sha": False,
        "orderbook_canonicalization_verified": True,
        "event_state_canonicalization_verified": True,
        "downstream_pr116_contract_prepared": True,
        "downstream_pr116_execution_authorized": False,
        "downstream_pr117_contract_prepared": True,
        "downstream_pr117_execution_authorized": False,
        "downstream_quantum_feature_computation_authorized": False,
        "downstream_quantum_optimizer_input_creation_authorized": False,
        "downstream_quantum_trading_signal_creation_authorized": False,
        "downstream_atomicrows_bridge_authorized_now": False,
        "downstream_atomicrows_bridge_recommended_after_pr135": True,
        "downstream_atomicrows_bundle_sha_authorized_now": False,
    }
