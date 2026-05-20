from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from src.qtt.stage1_prediction_markets.market_data_ingest.source_dependency import (
    adapter_input_class_for,
    dependency_lookup,
)


def _scope_refs_for_adapter() -> tuple[policy.ScopeRef, ...]:
    return policy.stage1_scope_refs()


def _event_kinds_for(scope_ref: policy.ScopeRef) -> tuple[str, ...]:
    if scope_ref.scope_kind == "venue":
        return policy.ALLOWED_CANONICAL_EVENT_KIND_CLASSES
    return ("VENUE_HEALTH_INPUT_METADATA_ENVELOPE",)


def _input_id(scope_value: str, event_kind_class: str) -> str:
    return f"PR132_{scope_value}_{event_kind_class}_ADAPTER_INPUT_V1"


def _event_id(scope_value: str, event_kind_class: str) -> str:
    return f"PR132_{scope_value}_{event_kind_class}_CANONICAL_EVENT_V1"


def _binding_id(scope_value: str) -> str:
    return f"PR132_{scope_value}_MARKET_DATA_ADAPTER_BINDING_V1"


def _fixture_payload_ref(scope_value: str, event_kind_class: str) -> str:
    return f"PR132_SYNTHETIC_FIXTURE_PAYLOAD_REF_{scope_value}_{event_kind_class}"


def build_adapter_inputs(
    dependencies: list[Mapping[str, object]],
    credential_handoff_ref: str,
) -> list[dict[str, object]]:
    by_scope_event = dependency_lookup(dependencies)
    records: list[dict[str, object]] = []
    for scope_ref in _scope_refs_for_adapter():
        for event_kind in _event_kinds_for(scope_ref):
            dependency = by_scope_event[(scope_ref.value, event_kind)]
            state = str(dependency["dependency_state"])
            records.append(
                {
                    **policy.common_record_fields("VENUE_MARKET_DATA_ADAPTER_INPUT"),
                    **policy.scope_field(scope_ref),
                    "input_id": _input_id(scope_ref.value, event_kind),
                    "adapter_input_class": adapter_input_class_for(state),
                    "event_kind_class": event_kind,
                    "fixture_payload_ref": _fixture_payload_ref(
                        scope_ref.value,
                        event_kind,
                    ),
                    "fixture_payload_is_synthetic": True,
                    "fixture_payload_contains_live_market_data": False,
                    "fixture_payload_contains_official_venue_semantic_values": False,
                    "accepted_source_dependency_refs": [
                        value
                        for value in [dependency.get("accepted_source_packet_ref")]
                        if value
                    ],
                    "connector_semantic_dependency_refs": [
                        value
                        for value in [dependency.get("connector_semantic_binding_ref")]
                        if value
                    ],
                    "credential_readiness_dependency_ref": credential_handoff_ref,
                    "source_dependency_state": state,
                    "official_semantics_claimed": False,
                    "live_fetch_attempted": False,
                    "downstream_pr115_contract_ref": (
                        f"PR115_{scope_ref.value}_ORDERBOOK_EVENT_STATE_CONTRACT_REF"
                    ),
                    "downstream_pr116_contract_ref": (
                        f"PR116_{scope_ref.value}_RUNTIME_RESOLVER_CONTRACT_REF"
                    ),
                    "downstream_pr117_contract_ref": (
                        f"PR117_{scope_ref.value}_HISTORICAL_DATASET_CONTRACT_REF"
                    ),
                    "future_low_latency_adapter_ref": (
                        f"FUTURE_LOW_LATENCY_ADAPTER_REF_{scope_ref.value}"
                    ),
                    "live_use_requires_future_owner_approval": True,
                    "live_use_requires_accepted_source_and_connector_semantic_binding": True,
                }
            )
    return records


def build_canonical_events(
    adapter_inputs: list[Mapping[str, object]],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for sequence, input_record in enumerate(adapter_inputs, start=1):
        scope_value = str(input_record.get("venue_id") or input_record.get("scope_id"))
        event_kind = str(input_record["event_kind_class"])
        source_state = str(input_record["source_dependency_state"])
        all_deps_ready = source_state == "CONNECTOR_SEMANTIC_GATED"
        scope_ref = policy.ScopeRef(
            "venue" if "venue_id" in input_record else "shared_scope",
            scope_value,
        )
        records.append(
            {
                **policy.common_record_fields("CANONICAL_MARKET_DATA_INGEST_EVENT"),
                **policy.scope_field(scope_ref),
                "event_id": _event_id(scope_value, event_kind),
                "adapter_binding_ref": _binding_id(scope_value),
                "event_kind_class": event_kind,
                "deterministic_sequence_id": f"PR132_SEQUENCE_{sequence:04d}",
                "fixture_payload_ref": str(input_record["fixture_payload_ref"]),
                "normalized_payload_class": "QTT_INTERNAL_FIXTURE_METADATA_ENVELOPE",
                "qtt_internal_field_class": event_kind,
                "official_venue_field_value_source_state": source_state,
                "source_required_for_live_use": not all_deps_ready,
                "connector_semantic_required_for_live_use": not all_deps_ready,
                "adapter_output_is_trading_signal": False,
                "adapter_output_is_feature_vector": False,
                "adapter_output_is_scoring_input": False,
                "adapter_output_is_quantum_feature_vector": False,
                "adapter_output_is_quantum_optimizer_input": False,
                "adapter_output_is_quantum_trading_signal": False,
                "adapter_output_is_order_authority": False,
                "adapter_output_is_orderbook_snapshot": False,
                "adapter_output_is_event_state_snapshot": False,
                "adapter_output_is_runtime_resolver_snapshot": False,
                "adapter_output_is_historical_dataset": False,
                "no_live_fetch": True,
                "no_network_io": True,
                "no_order_authority": True,
                "no_profit_evidence": True,
                "no_quantum_execution": True,
                "no_quantum_feature_computation": True,
                "no_quantum_optimizer_input": True,
                "no_quantum_trading_signal": True,
                "future_hot_path_snapshot_ref": (
                    f"FUTURE_HOT_PATH_SNAPSHOT_REF_{scope_value}"
                ),
                "future_pr115_snapshot_builder_contract_ref": (
                    f"PR115_{scope_value}_SNAPSHOT_BUILDER_CONTRACT_REF"
                ),
                "future_pr116_runtime_resolver_contract_ref": (
                    f"PR116_{scope_value}_RUNTIME_RESOLVER_CONTRACT_REF"
                ),
                "future_pr117_historical_dataset_digest_contract_ref": (
                    f"PR117_{scope_value}_HISTORICAL_DATASET_DIGEST_CONTRACT_REF"
                ),
            }
        )
    return records
