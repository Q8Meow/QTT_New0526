"""PR134 downstream handoff metadata builder."""

from __future__ import annotations

from typing import Any

from . import policy


def build_downstream_handoff(
    input_locks: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    integrity_receipts: list[dict[str, Any]],
    atomicrows_compatibility: list[dict[str, Any]],
) -> dict[str, Any]:
    handoff = policy.common_record_fields("RUNTIME_RESOLVER_SNAPSHOT_DOWNSTREAM_HANDOFF")
    handoff.update(
        {
            "handoff_id": policy.PR134_HANDOFF_ID,
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
                "PR115",
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
            "runtime_resolver_input_lock_refs": [
                record["input_lock_id"] for record in input_locks
            ],
            "runtime_resolver_snapshot_refs": [
                record["runtime_resolver_snapshot_id"] for record in snapshots
            ],
            "runtime_resolver_binding_refs": [
                record["binding_id"] for record in bindings
            ],
            "runtime_resolver_integrity_receipt_refs": [
                record["integrity_receipt_id"] for record in integrity_receipts
            ],
            "atomicrows_pre_bridge_compatibility_refs": [
                record["compatibility_id"] for record in atomicrows_compatibility
            ],
            "contains_fixture_runtime_resolver_snapshot": True,
            "contains_versioned_candidate_set_snapshot_lock_metadata": True,
            "contains_future_replay_paper_input_identity_metadata": True,
            "contains_global_candidate_universe_freeze": False,
            "contains_live_candidate_discovery": False,
            "contains_live_candidate_import": False,
            "contains_live_contract_selection": False,
            "contains_live_runtime_resolver_authority": False,
            "contains_live_market_data": False,
            "contains_live_credentials": False,
            "contains_private_state_payload": False,
            "contains_historical_dataset_digest": False,
            "contains_feature_vector": False,
            "contains_trading_signal": False,
            "contains_ranking_output": False,
            "contains_replay_execution": False,
            "contains_paper_execution": False,
            "contains_replay_result": False,
            "contains_paper_result": False,
            "contains_order_authority": False,
            "contains_profit_evidence": False,
            "contains_quantum_feature_vector": False,
            "contains_quantum_optimizer_input": False,
            "contains_quantum_trading_signal": False,
            "contains_quantum_execution": False,
            "contains_atomicrows_materialized_rows": False,
            "contains_atomicrows_bundle": False,
            "contains_atomicrows_sha": False,
            "future_candidate_additions_allowed_by_new_snapshot_versions": True,
            "downstream_pr117_contract_prepared": True,
            "downstream_pr117_execution_authorized": False,
            "downstream_historical_dataset_digest_authorized_now": False,
            "downstream_replay_paper_execution_authorized_now": False,
            "downstream_replay_paper_result_authorized_now": False,
            "downstream_order_authority_authorized_now": False,
            "downstream_live_candidate_discovery_authorized_now": False,
            "downstream_quantum_feature_computation_authorized": False,
            "downstream_quantum_optimizer_input_creation_authorized": False,
            "downstream_quantum_trading_signal_creation_authorized": False,
            "downstream_atomicrows_bridge_authorized_now": False,
            "downstream_atomicrows_bridge_recommended_after_pr135": True,
            "downstream_atomicrows_bundle_sha_authorized_now": False,
            "atomicrows_bundle_consumed": False,
            "atomicrows_sha_created": False,
        }
    )
    return handoff
