"""Fixture-backed PR134 runtime resolver input-lock builders."""

from __future__ import annotations

from typing import Any

from . import policy


def dependency_refs(scope_ref: policy.ScopeRef) -> dict[str, Any]:
    token = scope_ref.token
    return {
        "orderbook_event_state_snapshot_handoff_ref": policy.PR133_HANDOFF_ID,
        "orderbook_snapshot_refs": [f"PR133_{token}_ORDERBOOK_SNAPSHOT_V1"],
        "event_state_snapshot_refs": [f"PR133_{token}_EVENT_STATE_SNAPSHOT_V1"],
        "market_data_ingest_dependency_refs": [
            f"PR132_{token}_MARKET_DATA_INGEST_ADAPTER_CONTRACT_REF"
        ],
        "credential_readiness_dependency_refs": [
            f"PR131_{token}_CREDENTIAL_READINESS_METADATA_REF"
        ],
        "accepted_source_dependency_refs": [
            f"PR106_{token}_ACCEPTED_SOURCE_GATED_METADATA_REF",
            f"PR107_{token}_SOURCE_REVALIDATION_STATE_REF",
        ],
        "connector_semantic_dependency_refs": [
            f"PR108_{token}_CONNECTOR_SEMANTIC_BINDING_REF",
            f"PR126_{token}_CONNECTOR_SEMANTIC_IMPLEMENTATION_GATE_REF",
        ],
        "contract_normalization_dependency_ref": (
            f"PR110_{token}_CONTRACT_NORMALIZATION_DEPENDENCY_REF"
        ),
        "comparability_scope_dependency_ref": (
            f"PR110_{token}_COMPARABILITY_SCOPE_DEPENDENCY_REF"
        ),
        "liquidity_scope_dependency_ref": (
            f"PR110_{token}_LIQUIDITY_SCOPE_DEPENDENCY_REF"
        ),
    }


def build_runtime_resolver_input_locks() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for sequence_id, scope_ref in enumerate(policy.canonical_scope_refs(), start=1):
        input_lock_id = f"{scope_ref.record_prefix}_RUNTIME_RESOLVER_INPUT_LOCK_V1"
        record = policy.common_record_fields("RUNTIME_RESOLVER_INPUT_LOCK", scope_ref)
        record.update(dependency_refs(scope_ref))
        record.update(policy.candidate_set_metadata(scope_ref, sequence_id))
        record.update(policy.replay_paper_identity_metadata(scope_ref))
        record.update(
            {
                "input_lock_id": input_lock_id,
                "runtime_resolver_input_lock_id": input_lock_id,
                "runtime_resolver_input_class": (
                    "PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_HANDOFF_INPUT"
                ),
                "canonical_input_identity_ref": (
                    f"{scope_ref.record_prefix}_CANONICAL_INPUT_IDENTITY"
                ),
                "input_payload_is_synthetic": True,
                "input_contains_live_market_data": False,
                "input_contains_private_state_payload": False,
                "input_contains_order_authority": False,
                "input_contains_exact_live_contract_ids": False,
                "fixture_runtime_resolver_snapshot_allowed": True,
                "live_runtime_execution_allowed": False,
                "live_candidate_discovery_allowed": False,
                "live_contract_selection_allowed": False,
                "historical_dataset_digest_allowed": False,
                "replay_execution_allowed": False,
                "paper_execution_allowed": False,
                "order_execution_allowed": False,
            }
        )
        records.append(record)
    return records
