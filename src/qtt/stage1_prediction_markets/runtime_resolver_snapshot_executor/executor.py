"""Deterministic PR134 runtime resolver snapshot fixture executor."""

from __future__ import annotations

from typing import Any

from . import policy
from .atomicrows_pre_bridge import build_atomicrows_pre_bridge_compatibility
from .handoff import build_downstream_handoff
from .input_lock import build_runtime_resolver_input_locks
from .integrity import build_integrity_receipts


def _scope_value(record: dict[str, Any]) -> str:
    return str(record.get("venue_id") or record.get("scope_id"))


def _scope_ref_for_value(scope_value: str) -> policy.ScopeRef:
    return next(scope_ref for scope_ref in policy.canonical_scope_refs() if scope_ref.token == scope_value)


def _readiness_state_for_scope(scope_ref: policy.ScopeRef) -> str:
    readiness_by_scope = {
        "FORECASTEX_IBKR": "CONNECTOR_SEMANTIC_REQUIRED",
        "KALSHI": "READY_METADATA_ONLY",
        "POLYMARKET": "SOURCE_REQUIRED",
        "PREDICTION_MARKETS_GENERAL": "COMPARABILITY_SCOPE_REQUIRED",
    }
    return readiness_by_scope[scope_ref.token]


def _snapshot_class_for_readiness(readiness_state: str) -> str:
    if readiness_state == "READY_METADATA_ONLY":
        return "SYNTHETIC_FIXTURE_RUNTIME_RESOLVER_SNAPSHOT"
    if readiness_state == "SOURCE_REQUIRED":
        return "SOURCE_REQUIRED_RUNTIME_RESOLVER_SNAPSHOT_PLACEHOLDER"
    if readiness_state == "CONNECTOR_SEMANTIC_REQUIRED":
        return "CONNECTOR_SEMANTIC_REQUIRED_RUNTIME_RESOLVER_SNAPSHOT_PLACEHOLDER"
    return "QTT_INTERNAL_DEPENDENCY_STATE_METADATA_SNAPSHOT"


def _canonical_dependency_state_set(scope_ref: policy.ScopeRef, readiness_state: str) -> list[dict[str, str]]:
    if readiness_state == "READY_METADATA_ONLY":
        dependencies = [
            ("accepted_source", f"PR106_{scope_ref.token}_ACCEPTED_SOURCE_GATED_METADATA_REF", "ACCEPTED_SOURCE_GATED"),
            ("connector_semantic", f"PR108_{scope_ref.token}_CONNECTOR_SEMANTIC_BINDING_REF", "CONNECTOR_SEMANTIC_GATED"),
            ("contract_normalization", f"PR110_{scope_ref.token}_CONTRACT_NORMALIZATION_DEPENDENCY_REF", "ACCEPTED_SOURCE_GATED"),
            ("comparability_scope", f"PR110_{scope_ref.token}_COMPARABILITY_SCOPE_DEPENDENCY_REF", "ACCEPTED_SOURCE_GATED"),
            ("liquidity_scope", f"PR110_{scope_ref.token}_LIQUIDITY_SCOPE_DEPENDENCY_REF", "ACCEPTED_SOURCE_GATED"),
        ]
    elif readiness_state == "SOURCE_REQUIRED":
        dependencies = [
            ("accepted_source", f"PR106_{scope_ref.token}_SOURCE_REQUIRED_PLACEHOLDER", "SOURCE_REQUIRED"),
            ("connector_semantic", f"PR108_{scope_ref.token}_CONNECTOR_SEMANTIC_BINDING_REF", "CONNECTOR_SEMANTIC_GATED"),
            ("contract_normalization", f"PR110_{scope_ref.token}_CONTRACT_NORMALIZATION_DEPENDENCY_REF", "CONTRACT_NORMALIZATION_REQUIRED"),
            ("comparability_scope", f"PR110_{scope_ref.token}_COMPARABILITY_SCOPE_DEPENDENCY_REF", "COMPARABILITY_SCOPE_REQUIRED"),
            ("liquidity_scope", f"PR110_{scope_ref.token}_LIQUIDITY_SCOPE_DEPENDENCY_REF", "LIQUIDITY_SCOPE_REQUIRED"),
        ]
    elif readiness_state == "CONNECTOR_SEMANTIC_REQUIRED":
        dependencies = [
            ("accepted_source", f"PR106_{scope_ref.token}_ACCEPTED_SOURCE_GATED_METADATA_REF", "ACCEPTED_SOURCE_GATED"),
            ("connector_semantic", f"PR108_{scope_ref.token}_CONNECTOR_SEMANTIC_REQUIRED_PLACEHOLDER", "CONNECTOR_SEMANTIC_REQUIRED"),
            ("contract_normalization", f"PR110_{scope_ref.token}_CONTRACT_NORMALIZATION_DEPENDENCY_REF", "CONTRACT_NORMALIZATION_REQUIRED"),
            ("comparability_scope", f"PR110_{scope_ref.token}_COMPARABILITY_SCOPE_DEPENDENCY_REF", "COMPARABILITY_SCOPE_REQUIRED"),
            ("liquidity_scope", f"PR110_{scope_ref.token}_LIQUIDITY_SCOPE_DEPENDENCY_REF", "LIQUIDITY_SCOPE_REQUIRED"),
        ]
    else:
        dependencies = [
            ("accepted_source", f"PR106_{scope_ref.token}_ACCEPTED_SOURCE_GATED_METADATA_REF", "ACCEPTED_SOURCE_GATED"),
            ("connector_semantic", f"PR108_{scope_ref.token}_CONNECTOR_SEMANTIC_BINDING_REF", "CONNECTOR_SEMANTIC_GATED"),
            ("contract_normalization", f"PR110_{scope_ref.token}_CONTRACT_NORMALIZATION_DEPENDENCY_REF", "CONTRACT_NORMALIZATION_REQUIRED"),
            ("comparability_scope", f"PR110_{scope_ref.token}_COMPARABILITY_SCOPE_DEPENDENCY_REF", "COMPARABILITY_SCOPE_REQUIRED"),
            ("liquidity_scope", f"PR110_{scope_ref.token}_LIQUIDITY_SCOPE_DEPENDENCY_REF", "LIQUIDITY_SCOPE_REQUIRED"),
        ]
    return [
        {
            "dependency_family": dependency_family,
            "dependency_id": dependency_id,
            "dependency_state": dependency_state,
        }
        for dependency_family, dependency_id, dependency_state in sorted(dependencies)
    ]


def build_runtime_resolver_snapshots(
    input_locks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for input_lock in sorted(
        input_locks,
        key=lambda record: (_scope_value(record), int(record["deterministic_sequence_id"])),
    ):
        scope_ref = _scope_ref_for_value(_scope_value(input_lock))
        readiness_state = _readiness_state_for_scope(scope_ref)
        snapshot_id = f"{scope_ref.record_prefix}_RUNTIME_RESOLVER_SNAPSHOT_V1"
        record = policy.common_record_fields("RUNTIME_RESOLVER_SNAPSHOT_RECORD", scope_ref)
        record.update(policy.candidate_set_metadata(scope_ref, int(input_lock["deterministic_sequence_id"])))
        record.update(policy.replay_paper_identity_metadata(scope_ref))
        record.update(
            {
                "runtime_resolver_snapshot_id": snapshot_id,
                "runtime_resolver_input_lock_ref": input_lock["input_lock_id"],
                "runtime_resolver_snapshot_class": _snapshot_class_for_readiness(
                    readiness_state
                ),
                "runtime_resolver_readiness_state": readiness_state,
                "canonical_dependency_state_set": _canonical_dependency_state_set(
                    scope_ref, readiness_state
                ),
                "canonical_input_identity_ref": input_lock["canonical_input_identity_ref"],
                "canonical_sort_key": f"{scope_ref.token}:{int(input_lock['deterministic_sequence_id']):04d}",
                "fixture_runtime_resolver_snapshot_created": True,
                "runtime_resolver_snapshot_is_feature_vector": False,
                "runtime_resolver_snapshot_is_trading_signal": False,
                "runtime_resolver_snapshot_is_scoring_input": False,
                "runtime_resolver_snapshot_is_order_authority": False,
                "runtime_resolver_snapshot_is_replay_execution": False,
                "runtime_resolver_snapshot_is_paper_execution": False,
                "runtime_resolver_snapshot_is_historical_dataset_digest": False,
                "no_live_fetch": True,
                "no_network_io": True,
                "no_order_authority": True,
                "no_profit_evidence": True,
                "no_quantum_execution": True,
                "future_low_latency_runtime_resolver_snapshot_ref": (
                    f"{scope_ref.record_prefix}_FUTURE_LOW_LATENCY_RUNTIME_RESOLVER_SNAPSHOT_REF"
                ),
                "future_hot_path_runtime_resolver_snapshot_ref": (
                    f"{scope_ref.record_prefix}_FUTURE_HOT_PATH_RUNTIME_RESOLVER_SNAPSHOT_REF"
                ),
                "future_pr117_historical_dataset_digest_contract_ref": (
                    f"{scope_ref.record_prefix}_FUTURE_PR117_HISTORICAL_DATASET_DIGEST_CONTRACT_REF"
                ),
                "live_use_requires_future_owner_approval": True,
                "live_use_requires_accepted_source_and_connector_semantic_binding": True,
                "live_candidate_discovery_requires_later_authorization": True,
            }
        )
        records.append(record)
    return records


def build_runtime_resolver_bindings(
    input_locks: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    input_locks_by_scope = {_scope_value(record): record for record in input_locks}
    snapshots_by_scope = {_scope_value(record): record for record in snapshots}
    records: list[dict[str, Any]] = []
    for scope_ref in policy.canonical_scope_refs():
        input_lock = input_locks_by_scope[scope_ref.token]
        snapshot = snapshots_by_scope[scope_ref.token]
        record = policy.common_record_fields("RUNTIME_RESOLVER_SNAPSHOT_BINDING", scope_ref)
        record.update(
            {
                "binding_id": f"{scope_ref.record_prefix}_RUNTIME_RESOLVER_BINDING_V1",
                "executor_name": "runtime_resolver_snapshot_executor",
                "executor_version": policy.SCHEMA_VERSION,
                "executor_scope": "FIXTURE_BACKED_CONTRACT_ONLY",
                "input_lock_refs": [input_lock["input_lock_id"]],
                "runtime_resolver_snapshot_refs": [
                    snapshot["runtime_resolver_snapshot_id"]
                ],
                "orderbook_event_state_snapshot_handoff_ref": policy.PR133_HANDOFF_ID,
                "market_data_ingest_handoff_ref": policy.PR132_MARKET_DATA_HANDOFF_ID,
                "credential_readiness_handoff_ref": (
                    policy.PR131_CREDENTIAL_READINESS_HANDOFF_ID
                ),
                "source_dependency_refs": input_lock["accepted_source_dependency_refs"],
                "connector_semantic_dependency_refs": (
                    input_lock["connector_semantic_dependency_refs"]
                ),
                "runtime_resolver_readiness_policy_ref": (
                    f"{policy.PRODUCER_REPO_PR}_RUNTIME_RESOLVER_READINESS_POLICY"
                ),
                "candidate_set_snapshot_lock_policy_ref": (
                    f"{policy.PRODUCER_REPO_PR}_VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK_POLICY"
                ),
                "future_replay_paper_input_identity_ref": (
                    input_lock["future_replay_paper_input_identity_ref"]
                ),
                "future_replay_paper_same_input_lock_required": True,
                "future_replay_paper_same_runtime_resolver_snapshot_required": True,
                "future_replay_paper_same_candidate_set_snapshot_version_required": True,
                "allowed_use": "FIXTURE_BACKED_RUNTIME_RESOLVER_SNAPSHOT_CONTRACT_ONLY",
                "disallowed_use": list(policy.DISALLOWED_USE),
                "future_live_use_requires_owner_approval": True,
                "future_candidate_additions_require_new_candidate_set_snapshot_version": True,
                "future_live_candidate_discovery_requires_later_authorization": True,
                "future_live_use_requires_accepted_source_packet": True,
                "future_live_use_requires_fresh_revalidation_state": True,
                "future_live_use_requires_connector_semantic_binding": True,
                "future_live_use_requires_credential_provider_receipt_if_credentials_needed": True,
                "future_historical_dataset_use_requires_pr135_authorization": True,
                "future_replay_paper_use_requires_later_authorization": True,
                "future_atomicrows_bridge_requires_post_pr135_owner_authorization": True,
                "future_atomicrows_bundle_sha_requires_explicit_owner_authorization": True,
                "future_quantum_use_requires_pr117_data_chain": True,
                "future_quantum_use_requires_replay_paper_validation": True,
                "future_quantum_use_requires_owner_approval": True,
            }
        )
        records.append(record)
    return records


def build_runtime_resolver_rejections() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, reason_code in enumerate(policy.REJECTION_REASON_CODES, start=1):
        record = policy.common_record_fields("RUNTIME_RESOLVER_SNAPSHOT_REJECTION")
        record.update(
            {
                "rejection_id": f"PR134_RUNTIME_RESOLVER_REJECTION_{index:03d}",
                "rejected_action_or_payload_class": reason_code,
                "rejected_reason_code": reason_code,
                "rejected_artifact_ref": f"tests/fixtures/source_evidence/pr134_runtime_resolver_snapshot_executor/{reason_code}",
                "raw_live_payload_stored": False,
                "live_fetch_performed": False,
                "source_fact_accepted": False,
                "global_candidate_universe_freeze_claim_created": False,
                "future_candidate_addition_blocked": False,
                "live_runtime_authority_created": False,
                "feature_vector_created": False,
                "ranking_output_created": False,
                "quantum_advantage_claim_created": False,
                "validator_fail_closed": True,
            }
        )
        records.append(record)
    return records


def synthetic_pr133_handoff_fixture() -> dict[str, Any]:
    return {
        "record_type": "ORDERBOOK_EVENT_STATE_SNAPSHOT_DOWNSTREAM_HANDOFF",
        "schema_version": "PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_BUILDER_SCHEMA_V1",
        "handoff_id": policy.PR133_HANDOFF_ID,
        "producer_pr": "PR133",
        "producer_roadmap_pr": "PR115",
        "downstream_prs": ["PR116", "PR117"],
        "venue_specific_scope": list(policy.STAGE1_VENUE_IDS),
        "shared_scope": list(policy.SHARED_SCOPE_IDS),
        "contains_orderbook_snapshot_fixtures": True,
        "contains_event_state_snapshot_fixtures": True,
        "contains_live_market_data": False,
        "contains_live_runtime_authority": False,
        "contains_order_authority": False,
        "contains_profit_evidence": False,
        "contains_atomicrows_bundle": False,
        "contains_atomicrows_sha": False,
    }


def build_runtime_resolver_snapshot_artifacts() -> dict[str, Any]:
    pr133_handoff = synthetic_pr133_handoff_fixture()
    input_locks = build_runtime_resolver_input_locks()
    snapshots = build_runtime_resolver_snapshots(input_locks)
    bindings = build_runtime_resolver_bindings(input_locks, snapshots)
    integrity_receipts = build_integrity_receipts(
        input_locks, snapshots, bindings, pr133_handoff
    )
    atomicrows_compatibility = build_atomicrows_pre_bridge_compatibility(snapshots, bindings)
    downstream_handoff = build_downstream_handoff(
        input_locks,
        snapshots,
        bindings,
        integrity_receipts,
        atomicrows_compatibility,
    )
    return {
        "orderbook_event_state_snapshot_downstream_handoff": pr133_handoff,
        "runtime_resolver_input_locks": input_locks,
        "runtime_resolver_snapshots": snapshots,
        "runtime_resolver_bindings": bindings,
        "runtime_resolver_integrity_receipts": integrity_receipts,
        "runtime_resolver_rejections": build_runtime_resolver_rejections(),
        "atomicrows_pre_bridge_compatibility": atomicrows_compatibility,
        "runtime_resolver_downstream_handoff": downstream_handoff,
    }
