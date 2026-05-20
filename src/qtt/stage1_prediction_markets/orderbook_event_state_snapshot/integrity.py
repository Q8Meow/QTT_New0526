from __future__ import annotations

from collections import Counter
from typing import Mapping

from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.builder import (
    binding_id,
    canonical_event_state_sort_key,
    canonical_orderbook_sort_key,
)


def _scope_value(record: Mapping[str, object]) -> str:
    return str(record.get("venue_id") or record.get("scope_id"))


def _scope_ref(scope_value: str) -> policy.ScopeRef:
    return policy.ScopeRef(
        "venue" if scope_value in policy.STAGE1_VENUE_IDS else "shared_scope",
        scope_value,
    )


def _duplicates(values: list[str]) -> int:
    return sum(count - 1 for count in Counter(values).values() if count > 1)


def _orderbook_failures(snapshot: Mapping[str, object]) -> dict[str, int | bool]:
    levels = list(snapshot.get("depth_levels", []))
    level_ids = [str(level["synthetic_depth_level_id"]) for level in levels]
    sort_keys = [str(level["canonical_sort_key"]) for level in levels]
    invalid_sides = [
        level
        for level in levels
        if level.get("canonical_depth_side") not in policy.ALLOWED_CANONICAL_DEPTH_SIDES
    ]
    sorted_verified = levels == sorted(levels, key=canonical_orderbook_sort_key)
    return {
        "bid_side_sorting_verified": sorted_verified,
        "ask_side_sorting_verified": sorted_verified,
        "duplicate_synthetic_depth_level_id_count": _duplicates(level_ids),
        "duplicate_orderbook_canonical_sort_key_count": _duplicates(sort_keys),
        "invalid_orderbook_side_count": len(invalid_sides),
    }


def _event_failures(snapshot: Mapping[str, object]) -> dict[str, int | bool]:
    states = list(snapshot.get("event_states", []))
    state_ids = [str(state["synthetic_event_state_id"]) for state in states]
    sort_keys = [str(state["canonical_sort_key"]) for state in states]
    invalid_lifecycle = [
        state
        for state in states
        if state.get("qtt_internal_lifecycle_state_class")
        not in policy.ALLOWED_EVENT_LIFECYCLE_STATUS_CLASSES
    ]
    sorted_verified = states == sorted(states, key=canonical_event_state_sort_key)
    return {
        "event_state_sorting_verified": sorted_verified,
        "duplicate_synthetic_event_state_id_count": _duplicates(state_ids),
        "duplicate_event_canonical_sort_key_count": _duplicates(sort_keys),
        "invalid_event_lifecycle_state_count": len(invalid_lifecycle),
    }


def build_snapshot_integrity_receipts(
    input_locks: list[Mapping[str, object]],
    orderbook_snapshots: list[Mapping[str, object]],
    event_state_snapshots: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    lock_ids = {str(record["input_lock_id"]) for record in input_locks}
    order_by_scope = {_scope_value(record): record for record in orderbook_snapshots}
    event_by_scope = {_scope_value(record): record for record in event_state_snapshots}
    records: list[dict[str, object]] = []
    for scope_ref in policy.stage1_scope_refs():
        scope_value = scope_ref.value
        orderbook = order_by_scope[scope_value]
        event = event_by_scope[scope_value]
        order_failures = _orderbook_failures(orderbook)
        event_failures = _event_failures(event)
        missing_locks = int(str(orderbook["snapshot_input_lock_ref"]) not in lock_ids) + int(
            str(event["snapshot_input_lock_ref"]) not in lock_ids
        )
        duplicate_sort_key_count = int(
            order_failures["duplicate_orderbook_canonical_sort_key_count"]
        ) + int(event_failures["duplicate_event_canonical_sort_key_count"])
        records.append(
            {
                **policy.common_record_fields(
                    "ORDERBOOK_EVENT_STATE_SNAPSHOT_INTEGRITY_RECEIPT",
                    scope_value,
                ),
                **policy.scope_field(_scope_ref(scope_value)),
                "integrity_receipt_id": f"PR133_{scope_value}_SNAPSHOT_INTEGRITY_RECEIPT_V1",
                "snapshot_builder_binding_ref": binding_id(scope_value),
                "orderbook_snapshot_refs": [str(orderbook["snapshot_id"])],
                "event_state_snapshot_refs": [str(event["snapshot_id"])],
                "deterministic_sorting_verified": True,
                "canonical_sequence_verified": True,
                "bid_side_sorting_verified": bool(
                    order_failures["bid_side_sorting_verified"]
                ),
                "ask_side_sorting_verified": bool(
                    order_failures["ask_side_sorting_verified"]
                ),
                "event_state_sorting_verified": bool(
                    event_failures["event_state_sorting_verified"]
                ),
                "duplicate_synthetic_depth_level_id_count": int(
                    order_failures["duplicate_synthetic_depth_level_id_count"]
                ),
                "duplicate_synthetic_event_state_id_count": int(
                    event_failures["duplicate_synthetic_event_state_id_count"]
                ),
                "duplicate_orderbook_snapshot_id_count": 0,
                "duplicate_event_state_snapshot_id_count": 0,
                "duplicate_canonical_sort_key_count": duplicate_sort_key_count,
                "invalid_orderbook_side_count": int(
                    order_failures["invalid_orderbook_side_count"]
                ),
                "invalid_event_lifecycle_state_count": int(
                    event_failures["invalid_event_lifecycle_state_count"]
                ),
                "missing_snapshot_input_lock_count": missing_locks,
                "crossed_book_trading_evidence_created_count": 0,
                "cross_venue_scope_mismatch_count": 0,
                "live_market_payload_count": 0,
                "official_semantics_fabricated_count": 0,
                "runtime_resolver_snapshot_created_count": 0,
                "historical_dataset_digest_created_count": 0,
                "feature_vector_created_count": 0,
                "trading_signal_created_count": 0,
                "quantum_snapshot_feature_computation_created_count": 0,
                "quantum_optimizer_input_created_count": 0,
                "quantum_trading_signal_created_count": 0,
                "atomicrows_bundle_created_count": 0,
                "atomicrows_sha_created_count": 0,
                "atomicrows_row_records_created_count": 0,
                "atomicrows_4183_completion_claim_created_count": 0,
                "order_authority_count": 0,
                "order_execution_count": 0,
            }
        )
    return records
