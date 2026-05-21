"""AtomicRows pre-bridge compatibility metadata for PR134."""

from __future__ import annotations

from typing import Any

from . import policy


def build_atomicrows_pre_bridge_compatibility(
    snapshots: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    snapshots_by_scope = {
        snapshot.get("venue_id") or snapshot.get("scope_id"): snapshot
        for snapshot in snapshots
    }
    bindings_by_scope = {
        binding.get("venue_id") or binding.get("scope_id"): binding
        for binding in bindings
    }
    records: list[dict[str, Any]] = []
    for scope_ref in policy.canonical_scope_refs():
        snapshot = snapshots_by_scope[scope_ref.token]
        binding = bindings_by_scope[scope_ref.token]
        record = policy.common_record_fields(
            "RUNTIME_RESOLVER_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_RECORD",
            scope_ref,
        )
        record.update(
            {
                "compatibility_id": (
                    f"{scope_ref.record_prefix}_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_V1"
                ),
                "runtime_resolver_binding_ref": binding["binding_id"],
                "runtime_resolver_snapshot_refs": [
                    snapshot["runtime_resolver_snapshot_id"]
                ],
                "compatibility_class": "PRE_BRIDGE_METADATA_ONLY",
                "bridge_may_consume_after_pr135": True,
                "bridge_materialization_authorized_now": False,
                "bundle_materialization_authorized_now": False,
                "sha_freeze_authorized_now": False,
            }
        )
        records.append(record)
    return records
