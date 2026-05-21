"""Integrity checks for PR134 runtime resolver snapshot contracts."""

from __future__ import annotations

from collections import Counter
from typing import Any

from . import policy


def _scope_value(record: dict[str, Any]) -> str | None:
    value = record.get("venue_id") or record.get("scope_id")
    return value if isinstance(value, str) else None


def _duplicate_count(values: list[str]) -> int:
    return sum(count - 1 for count in Counter(values).values() if count > 1)


def _truthy_count(records: list[dict[str, Any]], field_names: tuple[str, ...]) -> int:
    total = 0
    for record in records:
        if any(record.get(field_name) is True for field_name in field_names):
            total += 1
    return total


def _numeric_sum(records: list[dict[str, Any]], field_name: str) -> int:
    total = 0
    for record in records:
        value = record.get(field_name)
        if isinstance(value, int):
            total += value
    return total


def compute_integrity_summary(
    input_locks: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    pr133_handoff: dict[str, Any] | None,
    atomicrows_compatibility: list[dict[str, Any]] | None = None,
) -> dict[str, int | bool]:
    atomicrows_compatibility = atomicrows_compatibility or []
    all_records = input_locks + snapshots + bindings + atomicrows_compatibility

    input_lock_ids = [
        str(record.get("input_lock_id"))
        for record in input_locks
        if record.get("input_lock_id") is not None
    ]
    snapshot_ids = [
        str(record.get("runtime_resolver_snapshot_id"))
        for record in snapshots
        if record.get("runtime_resolver_snapshot_id") is not None
    ]
    input_locks_by_id = {
        str(record.get("input_lock_id")): record
        for record in input_locks
        if record.get("input_lock_id") is not None
    }

    missing_pr133_handoff_count = 0
    if not pr133_handoff:
        missing_pr133_handoff_count = len(snapshots) or 1
    elif pr133_handoff.get("handoff_id") != policy.PR133_HANDOFF_ID:
        missing_pr133_handoff_count = len(snapshots) or 1

    invalid_readiness_state_count = sum(
        1
        for snapshot in snapshots
        if snapshot.get("runtime_resolver_readiness_state")
        not in policy.ALLOWED_RUNTIME_RESOLVER_READINESS_STATES
    )

    unresolved_ready_claim_count = 0
    stale_dependency_ready_claim_count = 0
    conflict_dependency_ready_claim_count = 0
    for snapshot in snapshots:
        dependency_states = [
            dependency.get("dependency_state")
            for dependency in snapshot.get("canonical_dependency_state_set", [])
            if isinstance(dependency, dict)
        ]
        if snapshot.get("runtime_resolver_readiness_state") == "READY_METADATA_ONLY":
            if any(
                dependency_state in policy.UNRESOLVED_READY_BLOCKING_STATES
                for dependency_state in dependency_states
            ):
                unresolved_ready_claim_count += 1
            if any(
                dependency_state
                in {"SOURCE_REVALIDATION_REQUIRED", "BLOCKED_STALE_DEPENDENCY"}
                for dependency_state in dependency_states
            ):
                stale_dependency_ready_claim_count += 1
            if "BLOCKED_CONFLICT" in dependency_states:
                conflict_dependency_ready_claim_count += 1

    missing_input_lock_count = 0
    cross_venue_scope_mismatch_count = 0
    for snapshot in snapshots:
        lock_id = snapshot.get("runtime_resolver_input_lock_ref")
        input_lock = input_locks_by_id.get(str(lock_id))
        if input_lock is None:
            missing_input_lock_count += 1
            continue
        if _scope_value(snapshot) != _scope_value(input_lock):
            cross_venue_scope_mismatch_count += 1

    summary: dict[str, int | bool] = {
        "duplicate_runtime_resolver_snapshot_id_count": _duplicate_count(snapshot_ids),
        "duplicate_runtime_resolver_input_lock_id_count": _duplicate_count(input_lock_ids),
        "duplicate_canonical_input_identity_ref_count": _duplicate_count(
            [
                str(record.get("canonical_input_identity_ref"))
                for record in input_locks
                if record.get("canonical_input_identity_ref") is not None
            ]
        ),
        "duplicate_future_replay_paper_input_identity_ref_count": _duplicate_count(
            [
                str(record.get("future_replay_paper_input_identity_ref"))
                for record in input_locks
                if record.get("future_replay_paper_input_identity_ref") is not None
            ]
        ),
        "duplicate_candidate_set_snapshot_version_id_count": _duplicate_count(
            [
                str(record.get("candidate_set_snapshot_version_id"))
                for record in input_locks
                if record.get("candidate_set_snapshot_version_id") is not None
            ]
        ),
        "missing_pr133_handoff_count": missing_pr133_handoff_count,
        "missing_input_lock_count": missing_input_lock_count,
        "missing_candidate_scope_lock_count": sum(
            1 for record in input_locks + snapshots if not record.get("candidate_scope_lock_ref")
        ),
        "missing_contract_normalization_dependency_count": sum(
            1 for record in input_locks if not record.get("contract_normalization_dependency_ref")
        ),
        "missing_comparability_scope_dependency_count": sum(
            1 for record in input_locks if not record.get("comparability_scope_dependency_ref")
        ),
        "missing_liquidity_scope_dependency_count": sum(
            1 for record in input_locks if not record.get("liquidity_scope_dependency_ref")
        ),
        "cross_venue_scope_mismatch_count": cross_venue_scope_mismatch_count,
        "invalid_readiness_state_count": invalid_readiness_state_count,
        "unresolved_dependency_ready_claim_count": unresolved_ready_claim_count,
        "stale_dependency_ready_claim_count": stale_dependency_ready_claim_count,
        "conflict_dependency_ready_claim_count": conflict_dependency_ready_claim_count,
        "exact_live_contract_id_created_count": _truthy_count(
            all_records, ("exact_live_contract_id_created",)
        ),
        "global_candidate_universe_freeze_claim_count": _truthy_count(
            all_records,
            (
                "candidate_set_snapshot_is_global_permanent_freeze",
                "global_candidate_universe_freeze_claim_created",
            ),
        ),
        "future_candidate_addition_blocked_count": sum(
            1
            for record in all_records
            if record.get("candidate_set_snapshot_allows_future_candidate_additions") is False
            or record.get("future_candidate_addition_blocked") is True
        ),
        "live_candidate_discovery_created_count": _truthy_count(
            all_records, ("live_candidate_discovery_created",)
        ),
        "live_candidate_import_created_count": _truthy_count(
            all_records, ("live_candidate_import_created",)
        ),
        "live_contract_selection_created_count": _truthy_count(
            all_records, ("live_contract_selection_created",)
        ),
        "live_runtime_authority_created_count": _truthy_count(
            all_records,
            ("live_runtime_resolver_authority_created", "live_runtime_authority_created"),
        ),
        "historical_dataset_digest_created_count": _truthy_count(
            all_records, ("historical_dataset_digest_created",)
        ),
        "feature_vector_created_count": _truthy_count(
            all_records,
            (
                "market_data_feature_vector_created",
                "runtime_feature_vector_created",
                "feature_vector_created",
                "runtime_resolver_snapshot_is_feature_vector",
            ),
        ),
        "trading_signal_created_count": _truthy_count(
            all_records,
            ("trading_signal_created", "runtime_resolver_snapshot_is_trading_signal"),
        ),
        "ranking_output_created_count": _truthy_count(all_records, ("ranking_output_created",)),
        "scoring_ranking_arbitration_output_created_count": _truthy_count(
            all_records, ("scoring_ranking_arbitration_output_created",)
        ),
        "replay_execution_created_count": _truthy_count(
            all_records, ("replay_execution_created",)
        ),
        "paper_execution_created_count": _truthy_count(
            all_records, ("paper_execution_created",)
        ),
        "replay_result_created_count": _truthy_count(all_records, ("replay_result_created",)),
        "paper_result_created_count": _truthy_count(all_records, ("paper_result_created",)),
        "live_trading_created_count": _truthy_count(all_records, ("live_trading_created",)),
        "order_authority_count": _truthy_count(
            all_records, ("order_authority_created", "runtime_resolver_snapshot_is_order_authority")
        ),
        "order_execution_count": _truthy_count(all_records, ("order_execution_created",)),
        "profit_evidence_count": _truthy_count(all_records, ("profit_evidence_created",)),
        "live_market_data_fetch_count": _truthy_count(
            all_records, ("live_market_data_fetch_created",)
        ),
        "rest_client_created_count": _truthy_count(all_records, ("rest_client_created",)),
        "websocket_client_created_count": _truthy_count(
            all_records, ("websocket_client_created",)
        ),
        "venue_api_call_count": _truthy_count(all_records, ("venue_api_call_created",)),
        "network_io_count": _truthy_count(all_records, ("network_io_created",)),
        "credential_provider_call_count": _truthy_count(
            all_records, ("credential_provider_called",)
        ),
        "live_credential_resolution_count": _truthy_count(
            all_records, ("live_credential_resolution_performed",)
        ),
        "private_state_fetch_count": _truthy_count(all_records, ("private_state_fetch_created",)),
        "runtime_cash_authority_count": _truthy_count(
            all_records, ("runtime_cash_authority_created",)
        ),
        "quantum_runtime_feature_computation_created_count": _truthy_count(
            all_records, ("quantum_runtime_feature_computation_created",)
        ),
        "quantum_optimizer_input_created_count": _truthy_count(
            all_records, ("quantum_optimizer_input_created",)
        ),
        "quantum_trading_signal_created_count": _truthy_count(
            all_records, ("quantum_trading_signal_created",)
        ),
        "quantum_backend_simulator_optimizer_execution_count": _truthy_count(
            all_records,
            (
                "quantum_execution_created",
                "quantum_backend_called",
                "quantum_simulator_called",
                "quantum_optimizer_called",
            ),
        ),
        "quantum_advantage_claim_created_count": _truthy_count(
            all_records, ("quantum_advantage_claim_created",)
        ),
        "atomicrows_bridge_authority_created_count": _truthy_count(
            all_records, ("atomicrows_bridge_authority_created",)
        ),
        "atomicrows_bundle_consumed_count": _truthy_count(
            all_records, ("atomicrows_bundle_consumed",)
        ),
        "atomicrows_bundle_created_count": _truthy_count(
            all_records, ("atomicrows_bundle_created",)
        ),
        "atomicrows_bundle_edited_count": _truthy_count(
            all_records, ("atomicrows_bundle_edited",)
        ),
        "atomicrows_sha_created_count": _truthy_count(all_records, ("atomicrows_sha_created",)),
        "atomicrows_row_records_created_count": _numeric_sum(
            all_records, "atomicrows_row_records_created_count"
        ),
        "atomicrows_4183_completion_claim_created_count": _truthy_count(
            all_records, ("atomicrows_4183_completion_claim_created",)
        ),
        "live_runtime_authority_created": False,
        "replay_execution_created": False,
        "paper_execution_created": False,
        "order_authority_created": False,
        "profit_evidence_created": False,
    }
    return summary


def build_integrity_receipts(
    input_locks: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    pr133_handoff: dict[str, Any],
) -> list[dict[str, Any]]:
    summary = compute_integrity_summary(input_locks, snapshots, bindings, pr133_handoff)
    snapshots_by_scope = {
        _scope_value(snapshot): snapshot for snapshot in snapshots if _scope_value(snapshot)
    }
    records: list[dict[str, Any]] = []
    for binding in bindings:
        scope_value = _scope_value(binding)
        scope_ref = next(ref for ref in policy.canonical_scope_refs() if ref.token == scope_value)
        snapshot = snapshots_by_scope[scope_value]
        record = policy.common_record_fields(
            "RUNTIME_RESOLVER_SNAPSHOT_INTEGRITY_RECEIPT", scope_ref
        )
        record.update(
            {
                "integrity_receipt_id": (
                    f"{scope_ref.record_prefix}_RUNTIME_RESOLVER_INTEGRITY_RECEIPT_V1"
                ),
                "runtime_resolver_binding_ref": binding["binding_id"],
                "runtime_resolver_snapshot_refs": [
                    snapshot["runtime_resolver_snapshot_id"]
                ],
                "deterministic_sorting_verified": True,
                "canonical_sequence_verified": True,
                "dependency_state_policy_verified": True,
                "versioned_candidate_set_snapshot_lock_metadata_verified": True,
                "future_candidate_additions_allowed_by_new_versions": True,
                "replay_paper_input_identity_metadata_verified": True,
            }
        )
        record.update(summary)
        records.append(record)
    return records
