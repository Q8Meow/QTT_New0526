from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest import policy


DEPENDENCY_STATE_BY_EVENT_KIND = {
    "MARKET_CATALOG_INPUT_METADATA_ENVELOPE": "ACCEPTED_SOURCE_GATED",
    "MARKET_STATUS_INPUT_METADATA_ENVELOPE": "CONNECTOR_SEMANTIC_GATED",
    "PRICE_QUOTE_INPUT_METADATA_ENVELOPE": "SOURCE_REQUIRED",
    "TRADE_PRINT_INPUT_METADATA_ENVELOPE": "CONNECTOR_SEMANTIC_REQUIRED",
    "ORDERBOOK_INPUT_METADATA_ENVELOPE_FOR_PR115_ONLY": "SOURCE_REQUIRED",
    "ORDERBOOK_DELTA_INPUT_METADATA_ENVELOPE_FOR_PR115_ONLY": (
        "CONNECTOR_SEMANTIC_REQUIRED"
    ),
    "SETTLEMENT_STATUS_INPUT_METADATA_ENVELOPE": "ACCEPTED_SOURCE_GATED",
    "VENUE_HEALTH_INPUT_METADATA_ENVELOPE": "CONNECTOR_SEMANTIC_GATED",
}

INPUT_CLASS_BY_STATE = {
    "ACCEPTED_SOURCE_GATED": "ACCEPTED_SOURCE_GATED_MARKET_DATA_INPUT_METADATA",
    "CONNECTOR_SEMANTIC_GATED": (
        "CONNECTOR_SEMANTIC_REQUIRED_MARKET_DATA_INPUT_PLACEHOLDER"
    ),
    "SOURCE_REQUIRED": "SOURCE_REQUIRED_MARKET_DATA_INPUT_PLACEHOLDER",
    "CONNECTOR_SEMANTIC_REQUIRED": (
        "CONNECTOR_SEMANTIC_REQUIRED_MARKET_DATA_INPUT_PLACEHOLDER"
    ),
    "BLOCKED_SCOPE_MISMATCH": "SOURCE_REQUIRED_MARKET_DATA_INPUT_PLACEHOLDER",
}


def dependency_state_for(event_kind_class: str) -> str:
    return DEPENDENCY_STATE_BY_EVENT_KIND[event_kind_class]


def adapter_input_class_for(dependency_state: str) -> str:
    return INPUT_CLASS_BY_STATE[dependency_state]


def dependency_id(scope_value: str, event_kind_class: str) -> str:
    return f"PR132_{scope_value}_{event_kind_class}_SOURCE_DEPENDENCY_V1"


def _accepted_source_ref(scope_value: str, state: str) -> str | None:
    if state in {"ACCEPTED_SOURCE_GATED", "CONNECTOR_SEMANTIC_GATED"}:
        return f"PR106_ACCEPTED_SOURCE_PACKET_REF_METADATA_ONLY_{scope_value}"
    return None


def _connector_semantic_ref(scope_value: str, state: str) -> str | None:
    if state == "CONNECTOR_SEMANTIC_GATED":
        return f"PR124_CONNECTOR_SEMANTIC_BINDING_REF_METADATA_ONLY_{scope_value}"
    return None


def build_source_dependencies() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for scope_ref in policy.stage1_scope_refs():
        event_kinds = (
            policy.ALLOWED_CANONICAL_EVENT_KIND_CLASSES
            if scope_ref.scope_kind == "venue"
            else ("VENUE_HEALTH_INPUT_METADATA_ENVELOPE",)
        )
        for event_kind in event_kinds:
            state = dependency_state_for(event_kind)
            scope_value = scope_ref.value
            records.append(
                {
                    **policy.common_record_fields("MARKET_DATA_SOURCE_DEPENDENCY"),
                    **policy.scope_field(scope_ref),
                    "dependency_id": dependency_id(scope_value, event_kind),
                    "target_field_class": event_kind,
                    "dependency_state": state,
                    "accepted_source_packet_ref": _accepted_source_ref(
                        scope_value,
                        state,
                    ),
                    "connector_semantic_binding_ref": _connector_semantic_ref(
                        scope_value,
                        state,
                    ),
                    "revalidation_state_ref": (
                        f"PR125_REVALIDATION_STATE_REF_METADATA_ONLY_{scope_value}"
                    ),
                    "live_use_allowed": False,
                }
            )
    return records


def build_no_live_network_attestations(
    scanned_artifact_refs: list[str],
) -> list[dict[str, object]]:
    return [
        {
            **policy.common_record_fields("MARKET_DATA_NO_LIVE_NETWORK_ATTESTATION"),
            "attestation_id": "PR132_MARKET_DATA_NO_LIVE_NETWORK_ATTESTATION_V1",
            "scanned_artifact_refs": scanned_artifact_refs,
            "rest_client_import_count": 0,
            "websocket_client_import_count": 0,
            "socket_import_count": 0,
            "network_io_count": 0,
            "venue_api_call_count": 0,
            "live_market_data_fetch_count": 0,
            "environment_credential_read_count": 0,
            "credential_provider_call_count": 0,
            "production_connector_client_count": 0,
            "private_state_fetch_count": 0,
            "orderbook_snapshot_created_count": 0,
            "runtime_resolver_snapshot_created_count": 0,
            "historical_dataset_digest_created_count": 0,
            "feature_vector_created_count": 0,
            "trading_signal_created_count": 0,
            "quantum_feature_computation_created_count": 0,
            "quantum_optimizer_input_created_count": 0,
            "quantum_trading_signal_created_count": 0,
            "quantum_backend_simulator_optimizer_execution_count": 0,
            "quantum_advantage_claim_created_count": 0,
            "order_authority_count": 0,
            "order_execution_count": 0,
            "logs_contain_live_market_payload": False,
            "reports_contain_live_market_payload": False,
            "fixtures_contain_live_market_payload": False,
        }
    ]


def build_rejection_receipts() -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    for index, reason in enumerate(policy.REJECTION_REASON_CODES, start=1):
        receipts.append(
            {
                **policy.common_record_fields("VENUE_MARKET_DATA_ADAPTER_REJECTION"),
                "rejection_id": f"PR132_MARKET_DATA_ADAPTER_REJECTION_{index:02d}_V1",
                "rejected_action_or_payload_class": reason.replace("BLOCKED_", ""),
                "rejected_reason_code": reason,
                "rejected_artifact_ref": f"PR132_BLOCKED_FIXTURE_{index:02d}",
                "raw_live_payload_stored": False,
                "live_fetch_performed": False,
                "source_fact_accepted": False,
                "connector_semantic_binding_created": False,
                "official_semantics_fabricated": False,
                "validator_fail_closed": True,
            }
        )
    return receipts


def dependency_lookup(
    dependencies: list[Mapping[str, object]],
) -> dict[tuple[str, str], Mapping[str, object]]:
    return {
        (
            str(record.get("venue_id") or record.get("scope_id")),
            str(record["target_field_class"]),
        ): record
        for record in dependencies
    }
