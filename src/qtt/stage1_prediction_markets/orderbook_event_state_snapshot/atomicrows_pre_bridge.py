from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.builder import (
    binding_id,
)


def _scope_value(record: Mapping[str, object]) -> str:
    return str(record.get("venue_id") or record.get("scope_id"))


def _scope_ref(scope_value: str) -> policy.ScopeRef:
    return policy.ScopeRef(
        "venue" if scope_value in policy.STAGE1_VENUE_IDS else "shared_scope",
        scope_value,
    )


def build_atomicrows_pre_bridge_compatibility_records(
    orderbook_snapshots: list[Mapping[str, object]],
    event_state_snapshots: list[Mapping[str, object]],
) -> list[dict[str, object]]:
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
                    "ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_RECORD",
                    scope_value,
                ),
                **policy.scope_field(_scope_ref(scope_value)),
                "compatibility_id": f"PR133_{scope_value}_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_V1",
                "producer_pr": policy.PRODUCER_REPO_PR,
                "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
                "snapshot_builder_binding_ref": binding_id(scope_value),
                "orderbook_snapshot_refs": [orderbook_by_scope[scope_value]],
                "event_state_snapshot_refs": [event_by_scope[scope_value]],
                "compatibility_class": "PRE_BRIDGE_METADATA_ONLY",
                "bridge_may_consume_after_pr135": True,
                "bridge_materialization_authorized_now": False,
                "bundle_materialization_authorized_now": False,
                "sha_freeze_authorized_now": False,
            }
        )
    return records
