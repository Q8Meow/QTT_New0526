from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.input_lock import (
    input_lock_id,
)


def _scope_value(record: Mapping[str, object]) -> str:
    return str(record.get("venue_id") or record.get("scope_id"))


def _scope_ref_from_value(scope_value: str) -> policy.ScopeRef:
    return policy.ScopeRef(
        "venue" if scope_value in policy.STAGE1_VENUE_IDS else "shared_scope",
        scope_value,
    )


def orderbook_snapshot_id(scope_value: str) -> str:
    return f"PR133_{scope_value}_ORDERBOOK_SNAPSHOT_V1"


def event_state_snapshot_id(scope_value: str) -> str:
    return f"PR133_{scope_value}_EVENT_STATE_SNAPSHOT_V1"


def binding_id(scope_value: str) -> str:
    return f"PR133_{scope_value}_SNAPSHOT_BUILDER_BINDING_V1"


def canonical_orderbook_sort_key(level: Mapping[str, object]) -> tuple[object, ...]:
    side = str(level["canonical_depth_side"])
    if side == "BID_METADATA":
        return (
            side,
            -int(level["canonical_price_rank"]),
            -int(level["canonical_quantity_rank"]),
            str(level["synthetic_depth_level_id"]),
        )
    if side == "ASK_METADATA":
        return (
            side,
            int(level["canonical_price_rank"]),
            -int(level["canonical_quantity_rank"]),
            str(level["synthetic_depth_level_id"]),
        )
    return (
        side,
        str(level["synthetic_depth_level_id"]),
    )


def canonical_event_state_sort_key(state: Mapping[str, object]) -> tuple[object, ...]:
    lifecycle = str(state["qtt_internal_lifecycle_state_class"])
    return (
        int(state["canonical_event_state_rank"]),
        str(state["synthetic_event_state_id"]),
        lifecycle,
    )


def _depth_levels(scope_value: str) -> list[dict[str, object]]:
    raw = [
        ("BID_METADATA", 20, 9, "BID_A"),
        ("BID_METADATA", 10, 7, "BID_B"),
        ("ASK_METADATA", 30, 8, "ASK_A"),
        ("ASK_METADATA", 40, 6, "ASK_B"),
        ("UNKNOWN_SOURCE_REQUIRED", 0, 0, "UNKNOWN_A"),
    ]
    levels = []
    for side, price_rank, quantity_rank, suffix in raw:
        level_id = f"PR133_{scope_value}_DEPTH_LEVEL_{suffix}_V1"
        levels.append(
            {
                "synthetic_depth_level_id": level_id,
                "canonical_depth_side": side,
                "canonical_price_rank": price_rank,
                "canonical_quantity_rank": quantity_rank,
                "canonical_sort_key": (
                    f"{side}|{price_rank:04d}|{quantity_rank:04d}|{level_id}"
                ),
                "qtt_internal_orderbook_side_class": side,
                "qtt_internal_price_level_class": "QTT_INTERNAL_PRICE_RANK_METADATA_ONLY",
                "qtt_internal_quantity_level_class": (
                    "QTT_INTERNAL_QUANTITY_RANK_METADATA_ONLY"
                ),
                "deterministic_sequence_id": f"PR133_{scope_value}_{suffix}_DEPTH_SEQUENCE",
            }
        )
    return sorted(levels, key=canonical_orderbook_sort_key)


def _event_states(scope_value: str) -> list[dict[str, object]]:
    states = []
    for lifecycle in policy.ALLOWED_EVENT_LIFECYCLE_STATUS_CLASSES:
        state_id = f"PR133_{scope_value}_{lifecycle}_EVENT_STATE_V1"
        rank = policy.EVENT_LIFECYCLE_RANKS[lifecycle]
        states.append(
            {
                "synthetic_event_state_id": state_id,
                "canonical_event_state_rank": rank,
                "canonical_sort_key": f"{rank:04d}|{state_id}",
                "qtt_internal_event_status_class": lifecycle,
                "qtt_internal_lifecycle_state_class": lifecycle,
                "qtt_internal_settlement_state_class": (
                    "QTT_INTERNAL_SETTLEMENT_METADATA_ONLY"
                ),
                "deterministic_sequence_id": (
                    f"PR133_{scope_value}_{lifecycle}_EVENT_STATE_SEQUENCE"
                ),
            }
        )
    return sorted(states, key=canonical_event_state_sort_key)


def build_orderbook_snapshots(
    input_locks: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for sequence, lock in enumerate(input_locks, start=1):
        scope_value = _scope_value(lock)
        scope_ref = _scope_ref_from_value(scope_value)
        levels = _depth_levels(scope_value)
        records.append(
            {
                **policy.common_record_fields("ORDERBOOK_SNAPSHOT_RECORD", scope_value),
                **policy.scope_field(scope_ref),
                "snapshot_id": orderbook_snapshot_id(scope_value),
                "snapshot_input_lock_ref": str(lock["input_lock_id"]),
                "snapshot_class": "SYNTHETIC_FIXTURE_ORDERBOOK_SNAPSHOT",
                "qtt_internal_snapshot_class": "QTT_INTERNAL_ORDERBOOK_DEPTH_METADATA_SNAPSHOT",
                "deterministic_sequence_id": f"PR133_ORDERBOOK_SEQUENCE_{sequence:04d}",
                "synthetic_depth_level_refs": [
                    str(level["synthetic_depth_level_id"]) for level in levels
                ],
                "synthetic_depth_level_id": f"PR133_{scope_value}_ORDERBOOK_AGGREGATE_V1",
                "depth_levels": levels,
                "canonical_depth_side": "UNKNOWN_SOURCE_REQUIRED",
                "canonical_price_rank": 0,
                "canonical_quantity_rank": 0,
                "canonical_sort_key": f"PR133_{scope_value}_ORDERBOOK_AGGREGATE_SORT_KEY",
                "qtt_internal_orderbook_side_class": "QTT_INTERNAL_DEPTH_METADATA_MIXED",
                "qtt_internal_price_level_class": "QTT_INTERNAL_PRICE_RANK_METADATA_ONLY",
                "qtt_internal_quantity_level_class": (
                    "QTT_INTERNAL_QUANTITY_RANK_METADATA_ONLY"
                ),
                "official_venue_field_value_source_state": str(
                    lock["source_dependency_state"]
                ),
                "fixture_orderbook_snapshot_created": True,
                "crossed_book_valid_trading_evidence_created": False,
                "orderbook_snapshot_is_trading_signal": False,
                "orderbook_snapshot_is_feature_vector": False,
                "orderbook_snapshot_is_quantum_feature_vector": False,
                "orderbook_snapshot_is_atomicrows_row": False,
                "orderbook_snapshot_is_order_authority": False,
                "orderbook_snapshot_is_runtime_resolver_snapshot": False,
                "no_live_fetch": True,
                "no_network_io": True,
                "no_order_authority": True,
                "no_profit_evidence": True,
                "no_quantum_execution": True,
            }
        )
    return records


def build_event_state_snapshots(
    input_locks: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for sequence, lock in enumerate(input_locks, start=1):
        scope_value = _scope_value(lock)
        scope_ref = _scope_ref_from_value(scope_value)
        states = _event_states(scope_value)
        records.append(
            {
                **policy.common_record_fields("EVENT_STATE_SNAPSHOT_RECORD", scope_value),
                **policy.scope_field(scope_ref),
                "snapshot_id": event_state_snapshot_id(scope_value),
                "snapshot_input_lock_ref": str(lock["input_lock_id"]),
                "snapshot_class": "SYNTHETIC_FIXTURE_EVENT_STATE_SNAPSHOT",
                "qtt_internal_snapshot_class": "QTT_INTERNAL_EVENT_LIFECYCLE_METADATA_SNAPSHOT",
                "deterministic_sequence_id": f"PR133_EVENT_STATE_SEQUENCE_{sequence:04d}",
                "synthetic_event_state_refs": [
                    str(state["synthetic_event_state_id"]) for state in states
                ],
                "synthetic_event_state_id": f"PR133_{scope_value}_EVENT_STATE_AGGREGATE_V1",
                "event_states": states,
                "canonical_event_state_rank": 0,
                "canonical_sort_key": f"PR133_{scope_value}_EVENT_STATE_AGGREGATE_SORT_KEY",
                "qtt_internal_event_status_class": "QTT_INTERNAL_STATUS_METADATA_MIXED",
                "qtt_internal_lifecycle_state_class": "UNKNOWN_SOURCE_REQUIRED",
                "qtt_internal_settlement_state_class": "QTT_INTERNAL_SETTLEMENT_METADATA_ONLY",
                "official_venue_field_value_source_state": str(
                    lock["source_dependency_state"]
                ),
                "fixture_event_state_snapshot_created": True,
                "event_state_snapshot_is_trading_signal": False,
                "event_state_snapshot_is_feature_vector": False,
                "event_state_snapshot_is_quantum_feature_vector": False,
                "event_state_snapshot_is_atomicrows_row": False,
                "event_state_snapshot_is_order_authority": False,
                "event_state_snapshot_is_runtime_resolver_snapshot": False,
                "no_live_fetch": True,
                "no_network_io": True,
                "no_order_authority": True,
                "no_profit_evidence": True,
                "no_quantum_execution": True,
            }
        )
    return records


def build_snapshot_builder_bindings(
    input_locks: list[Mapping[str, object]],
    orderbook_snapshots: list[Mapping[str, object]],
    event_state_snapshots: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    inputs_by_scope = {_scope_value(record): str(record["input_lock_id"]) for record in input_locks}
    orderbook_by_scope = {
        _scope_value(record): str(record["snapshot_id"]) for record in orderbook_snapshots
    }
    event_by_scope = {
        _scope_value(record): str(record["snapshot_id"]) for record in event_state_snapshots
    }
    records: list[dict[str, object]] = []
    for scope_ref in policy.stage1_scope_refs():
        scope_value = scope_ref.value
        records.append(
            {
                **policy.common_record_fields(
                    "ORDERBOOK_EVENT_STATE_SNAPSHOT_BUILDER_BINDING",
                    scope_value,
                ),
                **policy.scope_field(scope_ref),
                "binding_id": binding_id(scope_value),
                "builder_name": f"PR133_{scope_value}_FIXTURE_SNAPSHOT_BUILDER",
                "builder_version": "v1",
                "builder_scope": "FIXTURE_BACKED_CONTRACT_ONLY",
                "input_lock_refs": [inputs_by_scope[scope_value]],
                "orderbook_snapshot_refs": [orderbook_by_scope[scope_value]],
                "event_state_snapshot_refs": [event_by_scope[scope_value]],
                "market_data_ingest_handoff_ref": "PR132_MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF_V1",
                "credential_readiness_handoff_ref": "PR131_CREDENTIAL_READINESS_DOWNSTREAM_HANDOFF_V1",
                "source_dependency_refs": [
                    f"PR132_{scope_value}_ORDERBOOK_INPUT_METADATA_ENVELOPE_FOR_PR115_ONLY_SOURCE_DEPENDENCY_V1"
                ],
                "connector_semantic_dependency_refs": [
                    f"PR124_CONNECTOR_SEMANTIC_BINDING_REF_METADATA_ONLY_{scope_value}"
                ],
                "orderbook_canonical_sort_rules_ref": "PR133_ORDERBOOK_CANONICAL_SORT_RULES_POLICY",
                "event_state_canonical_sort_rules_ref": "PR133_EVENT_STATE_CANONICAL_SORT_RULES_POLICY",
                "allowed_use": "FIXTURE_BACKED_ORDERBOOK_EVENT_STATE_SNAPSHOT_CONTRACT_ONLY",
                "disallowed_use": list(policy.DISALLOWED_USE),
                "future_live_use_requires_owner_approval": True,
                "future_live_use_requires_accepted_source_packet": True,
                "future_live_use_requires_fresh_revalidation_state": True,
                "future_live_use_requires_connector_semantic_binding": True,
                "future_live_use_requires_credential_provider_receipt_if_credentials_needed": True,
                "future_runtime_resolver_use_requires_pr134_authorization": True,
                "future_historical_dataset_use_requires_pr135_authorization": True,
                "future_atomicrows_bridge_requires_post_pr135_owner_authorization": True,
                "future_atomicrows_bundle_sha_requires_explicit_owner_authorization": True,
                "future_quantum_use_requires_pr116_pr117_data_chain": True,
                "future_quantum_use_requires_replay_paper_validation": True,
                "future_quantum_use_requires_owner_approval": True,
            }
        )
    return records
