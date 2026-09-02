from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
    NoEffectFlagsV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PITDataContractErrorV1,
    PITDepthClassV2,
    PITEventKindV2,
    PITReasonCodeV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    Stage1VenueProfileIdV1,
)


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


@dataclass(frozen=True, slots=True)
class PITSourceDependencyV2:
    dependency_id: str
    profile_id: Stage1VenueProfileIdV1
    event_kind: PITEventKindV2
    access_class: policy.PITAccessClassV1
    host: str
    path_or_channel: str
    read_action: policy.PITReadActionV1
    wire_dialect: str
    depth_class: PITDepthClassV2
    sequence_model: str
    recovery_model: str
    rights_receipt_required: bool
    source_currentization_receipt_required: bool
    credential_alias_required: bool
    no_private_state: bool
    no_write: bool
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1 or self.profile_id not in (
            policy.PIT_SELECTED_SCOPE_V2.selected_profile_ids
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "source dependency profile is outside selected scope",
            )
        if type(self.event_kind) is not PITEventKindV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "event_kind must be exact PITEventKindV2",
            )
        if type(self.access_class) is not policy.PITAccessClassV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "access_class must be exact PITAccessClassV1",
            )
        if type(self.read_action) is not policy.PITReadActionV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "read_action must be exact PITReadActionV1",
            )
        if type(self.depth_class) is not PITDepthClassV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TOP_LEVEL_DEPTH_ONLY,
                "depth_class must be exact PITDepthClassV2",
            )
        for name in (
            "dependency_id",
            "host",
            "path_or_channel",
            "wire_dialect",
            "sequence_model",
            "recovery_model",
        ):
            value = getattr(self, name)
            if type(value) is not str or not value or value != value.strip():
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be canonical nonempty text",
                )
        for name in (
            "rights_receipt_required",
            "source_currentization_receipt_required",
            "credential_alias_required",
            "no_private_state",
            "no_write",
        ):
            if type(getattr(self, name)) is not bool:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact boolean",
                )
        if (
            not self.rights_receipt_required
            or not self.source_currentization_receipt_required
            or not self.no_private_state
            or not self.no_write
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "PIT source dependency requires source/rights and zero write authority",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "PIT source dependency must carry exact NO_EFFECTS_V1",
            )


def _pit_dependency_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


_PIT_DEPENDENCY_EVENT_KINDS = MappingProxyType({
    Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: (
        PITEventKindV2.CATALOG,
        PITEventKindV2.LIFECYCLE,
        PITEventKindV2.BOOK_SNAPSHOT,
        PITEventKindV2.BOOK_DELTA,
        PITEventKindV2.BBO,
        PITEventKindV2.TRADE,
        PITEventKindV2.SETTLEMENT,
        PITEventKindV2.SOURCE_STATUS,
    ),
    Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: (
        PITEventKindV2.CATALOG,
        PITEventKindV2.LIFECYCLE,
        PITEventKindV2.BOOK_REPLACEMENT,
        PITEventKindV2.BBO,
        PITEventKindV2.TRADE,
        PITEventKindV2.SETTLEMENT,
        PITEventKindV2.HEARTBEAT,
        PITEventKindV2.SOURCE_STATUS,
    ),
    Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: (
        PITEventKindV2.CATALOG,
        PITEventKindV2.LIFECYCLE,
        PITEventKindV2.BOOK_SNAPSHOT,
        PITEventKindV2.BOOK_DELTA,
        PITEventKindV2.TRADE,
        PITEventKindV2.SETTLEMENT,
        PITEventKindV2.HEARTBEAT,
        PITEventKindV2.SOURCE_STATUS,
    ),
})


def _pit_dependency_surface(
    profile_id: Stage1VenueProfileIdV1,
    event_kind: PITEventKindV2,
) -> tuple[policy.PITAccessClassV1, str, policy.PITReadActionV1]:
    protocol = policy._pit_profile_protocol_policy_v2(profile_id)
    if profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT:
        authenticated = (
            policy.PITAccessClassV1.AUTHENTICATED_PUBLIC_MARKET_DATA_READ
        )
        public = policy.PITAccessClassV1.PUBLIC_UNAUTHENTICATED_READ
        if event_kind is PITEventKindV2.BOOK_SNAPSHOT:
            return (
                authenticated,
                "orderbook_delta",
                policy.PITReadActionV1.WEBSOCKET_RECOVERY,
            )
        if event_kind is PITEventKindV2.TRADE:
            return public, "/historical/trades", policy.PITReadActionV1.GET
        if event_kind is PITEventKindV2.SOURCE_STATUS:
            return (
                authenticated,
                "/portfolio/account_limits",
                policy.PITReadActionV1.GET,
            )
        if event_kind is PITEventKindV2.HEARTBEAT:
            return (
                authenticated,
                "server_ping",
                policy.PITReadActionV1.WEBSOCKET_PONG,
            )
        if event_kind is PITEventKindV2.BOOK_DELTA:
            return (
                authenticated,
                "orderbook_delta",
                policy.PITReadActionV1.WEBSOCKET_SUBSCRIBE,
            )
        if event_kind is PITEventKindV2.LIFECYCLE:
            return (
                authenticated,
                "market_lifecycle_v2",
                policy.PITReadActionV1.WEBSOCKET_SUBSCRIBE,
            )
        return public, "/markets", policy.PITReadActionV1.GET
    websocket_kinds = {
        PITEventKindV2.BOOK_SNAPSHOT,
        PITEventKindV2.BOOK_DELTA,
        PITEventKindV2.BOOK_REPLACEMENT,
        PITEventKindV2.BBO,
        PITEventKindV2.TRADE,
        PITEventKindV2.HEARTBEAT,
        PITEventKindV2.SOURCE_STATUS,
    }
    if event_kind in websocket_kinds:
        access = (
            policy.PITAccessClassV1.PUBLIC_UNAUTHENTICATED_READ
            if profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT
            else policy.PITAccessClassV1.AUTHENTICATED_PUBLIC_MARKET_DATA_READ
        )
        if profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT:
            channel_by_kind = {
                PITEventKindV2.BOOK_SNAPSHOT: "prediction_markets.depth",
                PITEventKindV2.BOOK_DELTA: "prediction_markets.depth",
                PITEventKindV2.BBO: "prediction_markets.bookTicker",
                PITEventKindV2.TRADE: "prediction_markets.trades",
                PITEventKindV2.SOURCE_STATUS: "prediction_markets.depth",
            }
            channel = channel_by_kind[event_kind]
        else:
            channel = "markets"
        return access, channel, policy.PITReadActionV1.WEBSOCKET_SUBSCRIBE
    return (
        policy.PITAccessClassV1.PUBLIC_UNAUTHENTICATED_READ,
        _pit_dependency_text(protocol["allowed_paths"][0], "allowed path"),
        policy.PITReadActionV1.GET,
    )


def _build_pit_source_dependencies_v2() -> tuple[PITSourceDependencyV2, ...]:
    rows: list[PITSourceDependencyV2] = []

    def append_row(
        *,
        profile_id: Stage1VenueProfileIdV1,
        event_kind: PITEventKindV2,
        access_class: policy.PITAccessClassV1,
        path_or_channel: str,
        read_action: policy.PITReadActionV1,
    ) -> None:
        protocol = policy._pit_profile_protocol_policy_v2(profile_id)
        host = (
            _pit_dependency_text(
                protocol["production_rest_base"], "production_rest_base"
            )
            if read_action is policy.PITReadActionV1.GET
            else _pit_dependency_text(protocol["websocket_url"], "websocket_url")
        )
        if event_kind is PITEventKindV2.BOOK_SNAPSHOT:
            depth_class = PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT
        elif event_kind is PITEventKindV2.BOOK_REPLACEMENT:
            depth_class = (
                PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT
                if read_action is policy.PITReadActionV1.GET
                else PITDepthClassV2.PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME
            )
        elif event_kind is PITEventKindV2.BBO:
            depth_class = PITDepthClassV2.BBO_ONLY
        else:
            depth_class = protocol["depth_class"]
        rows.append(
            PITSourceDependencyV2(
                dependency_id=(
                    f"S1-PIT-DEPENDENCY::{profile_id.value}::"
                    f"{event_kind.value}::{access_class.value}"
                ),
                profile_id=profile_id,
                event_kind=event_kind,
                access_class=access_class,
                host=host,
                path_or_channel=path_or_channel,
                read_action=read_action,
                wire_dialect=_pit_dependency_text(
                    protocol["wire_dialect_policy"], "wire_dialect_policy"
                ),
                depth_class=depth_class,
                sequence_model=_pit_dependency_text(
                    protocol["sequence_model"], "sequence_model"
                ),
                recovery_model=_pit_dependency_text(
                    protocol["recovery_model"], "recovery_model"
                ),
                rights_receipt_required=True,
                source_currentization_receipt_required=True,
                credential_alias_required=(
                    access_class
                    is policy.PITAccessClassV1.AUTHENTICATED_PUBLIC_MARKET_DATA_READ
                ),
                no_private_state=True,
                no_write=True,
            )
        )

    for profile_id in policy.PIT_SELECTED_SCOPE_V2.serialization:
        for event_kind in _PIT_DEPENDENCY_EVENT_KINDS[profile_id]:
            access_class, path_or_channel, read_action = _pit_dependency_surface(
                profile_id, event_kind
            )
            append_row(
                profile_id=profile_id,
                event_kind=event_kind,
                access_class=access_class,
                path_or_channel=path_or_channel,
                read_action=read_action,
            )
        if profile_id is Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT:
            append_row(
                profile_id=profile_id,
                event_kind=PITEventKindV2.BOOK_REPLACEMENT,
                access_class=policy.PITAccessClassV1.PUBLIC_UNAUTHENTICATED_READ,
                path_or_channel="/v1/markets/{slug}/book",
                read_action=policy.PITReadActionV1.GET,
            )
        if profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT:
            append_row(
                profile_id=profile_id,
                event_kind=PITEventKindV2.TRADE,
                access_class=(
                    policy.PITAccessClassV1.AUTHENTICATED_PUBLIC_MARKET_DATA_READ
                ),
                path_or_channel="trade",
                read_action=policy.PITReadActionV1.WEBSOCKET_SUBSCRIBE,
            )
    return tuple(rows)


PIT_SOURCE_DEPENDENCIES_V2 = _build_pit_source_dependencies_v2()
_PIT_SOURCE_DEPENDENCY_BY_KEY_V2 = MappingProxyType({
    (row.profile_id, row.event_kind, row.access_class): row
    for row in PIT_SOURCE_DEPENDENCIES_V2
})
if len(_PIT_SOURCE_DEPENDENCY_BY_KEY_V2) != len(PIT_SOURCE_DEPENDENCIES_V2):
    raise RuntimeError("PIT source-dependency keys must be unique")


def _resolve_pit_source_dependency_v2(
    profile_id: Stage1VenueProfileIdV1,
    event_kind: PITEventKindV2,
    access_class: policy.PITAccessClassV1,
) -> PITSourceDependencyV2:
    if (
        type(profile_id) is not Stage1VenueProfileIdV1
        or type(event_kind) is not PITEventKindV2
        or type(access_class) is not policy.PITAccessClassV1
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "source dependency resolution requires exact typed keys",
        )
    try:
        return _PIT_SOURCE_DEPENDENCY_BY_KEY_V2[
            (profile_id, event_kind, access_class)
        ]
    except KeyError as exc:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
            "no selected source dependency matches the exact key",
        ) from exc
