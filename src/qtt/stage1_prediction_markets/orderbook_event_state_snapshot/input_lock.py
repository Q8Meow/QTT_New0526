from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy


STATE_BY_SCOPE = {
    "KALSHI": "ACCEPTED_SOURCE_GATED",
    "POLYMARKET": "CONNECTOR_SEMANTIC_GATED",
    "FORECASTEX_IBKR": "SOURCE_REQUIRED",
    "PREDICTION_MARKETS_GENERAL": "CONNECTOR_SEMANTIC_REQUIRED",
}


def input_lock_id(scope_value: str) -> str:
    return f"PR133_{scope_value}_SNAPSHOT_INPUT_LOCK_V1"


def _refs_for_scope(refs: list[object], scope_value: str) -> list[str]:
    return sorted(str(ref) for ref in refs if f"_{scope_value}_" in str(ref))


def build_snapshot_input_locks(
    pr132_handoff: Mapping[str, object],
    pr131_handoff: Mapping[str, object],
) -> list[dict[str, object]]:
    canonical_refs = list(pr132_handoff.get("canonical_market_data_ingest_event_refs", []))
    source_refs = list(pr132_handoff.get("market_data_source_dependency_refs", []))
    credential_ref = str(pr131_handoff["handoff_id"])

    records: list[dict[str, object]] = []
    for sequence, scope_ref in enumerate(policy.stage1_scope_refs(), start=1):
        scope_value = scope_ref.value
        state = STATE_BY_SCOPE[scope_value]
        records.append(
            {
                **policy.common_record_fields(
                    "ORDERBOOK_EVENT_STATE_SNAPSHOT_INPUT_LOCK",
                    scope_value,
                ),
                **policy.scope_field(scope_ref),
                "input_lock_id": input_lock_id(scope_value),
                "market_data_ingest_handoff_ref": str(pr132_handoff["handoff_id"]),
                "canonical_market_data_ingest_event_refs": _refs_for_scope(
                    canonical_refs,
                    scope_value,
                ),
                "accepted_source_dependency_refs": [
                    f"PR106_ACCEPTED_SOURCE_PACKET_REF_METADATA_ONLY_{scope_value}"
                ],
                "connector_semantic_dependency_refs": [
                    f"PR124_CONNECTOR_SEMANTIC_BINDING_REF_METADATA_ONLY_{scope_value}"
                ],
                "market_data_source_dependency_refs": _refs_for_scope(
                    source_refs,
                    scope_value,
                ),
                "credential_readiness_dependency_ref": credential_ref,
                "source_dependency_state": state,
                "snapshot_input_class": (
                    "PR132_MARKET_DATA_INGEST_HANDOFF_INPUT"
                    if state in {"ACCEPTED_SOURCE_GATED", "CONNECTOR_SEMANTIC_GATED"}
                    else "SOURCE_REQUIRED_SNAPSHOT_INPUT_PLACEHOLDER"
                ),
                "input_payload_is_synthetic": True,
                "input_contains_live_market_data": False,
                "input_contains_official_venue_semantic_values": False,
                "deterministic_sequence_id": f"PR133_INPUT_LOCK_SEQUENCE_{sequence:04d}",
                "snapshot_build_allowed": True,
                "live_snapshot_build_allowed": False,
                "runtime_resolver_snapshot_allowed": False,
                "historical_dataset_digest_allowed": False,
                "input_lock_required_for_each_snapshot": True,
                "future_low_latency_snapshot_ref": (
                    f"FUTURE_LOW_LATENCY_SNAPSHOT_REF_METADATA_ONLY_{scope_value}"
                ),
                "future_hot_path_snapshot_ref": (
                    f"FUTURE_HOT_PATH_SNAPSHOT_REF_METADATA_ONLY_{scope_value}"
                ),
                "future_pr116_runtime_resolver_contract_ref": (
                    f"PR116_{scope_value}_RUNTIME_RESOLVER_CONTRACT_REF"
                ),
                "future_pr117_historical_dataset_digest_contract_ref": (
                    f"PR117_{scope_value}_HISTORICAL_DATASET_DIGEST_CONTRACT_REF"
                ),
                "live_use_requires_future_owner_approval": True,
                "live_use_requires_accepted_source_and_connector_semantic_binding": True,
            }
        )
    return records
