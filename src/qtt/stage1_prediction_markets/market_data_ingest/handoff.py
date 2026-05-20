from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest import policy


def build_downstream_handoff(
    adapter_inputs: list[Mapping[str, object]],
    bindings: list[Mapping[str, object]],
    canonical_events: list[Mapping[str, object]],
    source_dependencies: list[Mapping[str, object]],
    no_live_attestations: list[Mapping[str, object]],
) -> dict[str, object]:
    return {
        **policy.common_record_fields("MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF"),
        "handoff_id": "PR132_MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF_V1",
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
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
        ],
        "downstream_prs": list(policy.DOWNSTREAM_PR_IDS),
        "venue_specific_scope": list(policy.STAGE1_VENUE_IDS),
        "shared_scope": list(policy.SHARED_SCOPE_IDS),
        "adapter_input_refs": [record["input_id"] for record in adapter_inputs],
        "adapter_binding_refs": [record["binding_id"] for record in bindings],
        "canonical_market_data_ingest_event_refs": [
            record["event_id"] for record in canonical_events
        ],
        "market_data_source_dependency_refs": [
            record["dependency_id"] for record in source_dependencies
        ],
        "no_live_network_attestation_refs": [
            record["attestation_id"] for record in no_live_attestations
        ],
        "contains_live_market_data": False,
        "contains_live_credentials": False,
        "contains_private_state_payload": False,
        "contains_orderbook_snapshot": False,
        "contains_event_state_snapshot": False,
        "contains_runtime_resolver_snapshot": False,
        "contains_historical_dataset_digest": False,
        "contains_feature_vector": False,
        "contains_trading_signal": False,
        "contains_quantum_feature_vector": False,
        "contains_quantum_optimizer_input": False,
        "contains_quantum_trading_signal": False,
        "contains_order_authority": False,
        "contains_profit_evidence": False,
        "contains_quantum_execution": False,
        "downstream_pr115_contract_prepared": True,
        "downstream_pr115_execution_authorized": False,
        "downstream_pr116_contract_prepared": True,
        "downstream_pr116_execution_authorized": False,
        "downstream_pr117_contract_prepared": True,
        "downstream_pr117_execution_authorized": False,
        "downstream_quantum_feature_computation_authorized": False,
        "downstream_quantum_optimizer_input_creation_authorized": False,
        "downstream_quantum_trading_signal_creation_authorized": False,
    }
