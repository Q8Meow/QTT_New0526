from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
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
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
    PITRightsAdmissionReceiptV1,
    PITSourceCurrentizationReceiptV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    Stage1SelectedScopeV2,
    Stage1VenueProfileIdV1,
)


def _scope_value(record: Mapping[str, object]) -> str:
    return str(record.get("venue_id") or record.get("scope_id"))


def _scope_ref_from_value(scope_value: str) -> policy.ScopeRef:
    scope_kind = "venue" if scope_value in policy.STAGE1_VENUE_IDS else "shared_scope"
    return policy.ScopeRef(scope_kind, scope_value)


def build_adapter_bindings(
    adapter_inputs: list[Mapping[str, object]],
    canonical_events: list[Mapping[str, object]],
    source_dependencies: list[Mapping[str, object]],
    credential_handoff_ref: str,
) -> list[dict[str, object]]:
    inputs_by_scope: dict[str, list[str]] = {}
    events_by_scope: dict[str, list[str]] = {}
    deps_by_scope: dict[str, list[str]] = {}
    connector_refs_by_scope: dict[str, list[str]] = {}
    for record in adapter_inputs:
        inputs_by_scope.setdefault(_scope_value(record), []).append(str(record["input_id"]))
    for record in canonical_events:
        events_by_scope.setdefault(_scope_value(record), []).append(str(record["event_id"]))
    for record in source_dependencies:
        scope_value = _scope_value(record)
        deps_by_scope.setdefault(scope_value, []).append(str(record["dependency_id"]))
        connector_ref = record.get("connector_semantic_binding_ref")
        if connector_ref:
            connector_refs_by_scope.setdefault(scope_value, []).append(str(connector_ref))

    records: list[dict[str, object]] = []
    for scope_ref in policy.stage1_scope_refs():
        scope_value = scope_ref.value
        records.append(
            {
                **policy.common_record_fields("VENUE_MARKET_DATA_ADAPTER_BINDING"),
                **policy.scope_field(_scope_ref_from_value(scope_value)),
                "binding_id": f"PR132_{scope_value}_MARKET_DATA_ADAPTER_BINDING_V1",
                "adapter_name": f"PR132_{scope_value}_FIXTURE_MARKET_DATA_INGEST_ADAPTER",
                "adapter_version": "v1",
                "adapter_scope": "FIXTURE_BACKED_CONTRACT_ONLY",
                "input_refs": inputs_by_scope[scope_value],
                "output_event_refs": events_by_scope[scope_value],
                "credential_readiness_handoff_ref": credential_handoff_ref,
                "source_dependency_refs": deps_by_scope[scope_value],
                "connector_semantic_dependency_refs": sorted(
                    connector_refs_by_scope.get(scope_value, [])
                ),
                "allowed_use": "FIXTURE_BACKED_MARKET_DATA_INGEST_CONTRACT_ONLY",
                "disallowed_use": list(policy.DISALLOWED_USE),
                "future_live_use_requires_owner_approval": True,
                "future_live_use_requires_accepted_source_packet": True,
                "future_live_use_requires_fresh_revalidation_state": True,
                "future_live_use_requires_connector_semantic_binding": True,
                "future_live_use_requires_credential_provider_receipt_if_credentials_needed": True,
                "future_quantum_use_requires_pr115_pr116_pr117_data_chain": True,
                "future_quantum_use_requires_replay_paper_validation": True,
                "future_quantum_use_requires_owner_approval": True,
            }
        )
    return records


def _pit_binding_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


def _pit_binding_text_tuple(
    value: object,
    name: str,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple or (not allow_empty and not value):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be an exact tuple",
        )
    result = tuple(_pit_binding_text(item, name) for item in value)
    if len(result) != len(set(result)):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
            f"{name} contains duplicate values",
        )
    return result


def _pit_binding_boolean(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be an exact boolean",
        )
    return value


@dataclass(frozen=True, slots=True)
class SelectedPITPublicDataContractV2:
    contract_id: str
    contract_version: str
    profile_id: Stage1VenueProfileIdV1
    scope_receipt_ref: str
    operating_legal_entity: str
    product_profile: str
    jurisdiction: str
    production_rest_base: str
    websocket_url: str
    allowed_access_classes: tuple[policy.PITAccessClassV1, ...]
    allowed_methods: tuple[policy.PITReadActionV1, ...]
    allowed_paths: tuple[str, ...]
    allowed_channels: tuple[str, ...]
    wire_dialect_policy: str
    subscription_form: str
    sequence_model: str
    snapshot_model: str
    recovery_model: str
    heartbeat_model: str
    admitted_event_kinds: tuple[PITEventKindV2, ...]
    event_identity_fields: tuple[str, ...]
    market_identity_fields: tuple[str, ...]
    instrument_identity_fields: tuple[str, ...]
    outcome_and_side_fields: tuple[str, ...]
    depth_class: PITDepthClassV2
    price_quantity_tick_model: str
    lifecycle_and_finality_fields: tuple[str, ...]
    source_currentization_receipt_ref: str
    source_contract_version: str
    rights_receipt_ref: str
    agreement_version: str
    credential_alias_required: bool
    no_private_state_authority: bool
    no_order_authority: bool
    default_failure_reason: PITReasonCodeV1
    unavailable_capabilities: tuple[str, ...]
    recovery_preconditions: tuple[str, ...]
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1 or self.profile_id not in (
            policy.PIT_SELECTED_SCOPE_V2.selected_profile_ids
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "contract profile is outside the selected Stage-1 scope",
            )
        for name in (
            "contract_id",
            "contract_version",
            "scope_receipt_ref",
            "operating_legal_entity",
            "product_profile",
            "jurisdiction",
            "production_rest_base",
            "websocket_url",
            "wire_dialect_policy",
            "subscription_form",
            "sequence_model",
            "snapshot_model",
            "recovery_model",
            "heartbeat_model",
            "price_quantity_tick_model",
            "source_currentization_receipt_ref",
            "source_contract_version",
            "rights_receipt_ref",
            "agreement_version",
        ):
            _pit_binding_text(getattr(self, name), name)
        if self.contract_version != "S1_PIT_PUBLIC_DATA_CONTRACT_V2":
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "selected public-data contract version is not exact V2",
            )
        for name in (
            "allowed_paths",
            "allowed_channels",
            "event_identity_fields",
            "market_identity_fields",
            "instrument_identity_fields",
            "outcome_and_side_fields",
            "lifecycle_and_finality_fields",
            "unavailable_capabilities",
            "recovery_preconditions",
        ):
            _pit_binding_text_tuple(
                getattr(self, name),
                name,
                allow_empty=name == "unavailable_capabilities",
            )
        if type(self.allowed_access_classes) is not tuple or not self.allowed_access_classes or any(
            type(value) is not policy.PITAccessClassV1
            for value in self.allowed_access_classes
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "allowed access classes must be exact typed values",
            )
        if type(self.allowed_methods) is not tuple or not self.allowed_methods or any(
            type(value) is not policy.PITReadActionV1 for value in self.allowed_methods
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "allowed methods must be exact typed values",
            )
        if type(self.admitted_event_kinds) is not tuple or not self.admitted_event_kinds or any(
            type(value) is not PITEventKindV2 for value in self.admitted_event_kinds
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "admitted event kinds must be exact PITEventKindV2 values",
            )
        if len(self.admitted_event_kinds) != len(set(self.admitted_event_kinds)):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                "admitted event kinds must be unique",
            )
        if type(self.depth_class) is not PITDepthClassV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TOP_LEVEL_DEPTH_ONLY,
                "depth class has the wrong exact type",
            )
        for name in (
            "credential_alias_required",
            "no_private_state_authority",
            "no_order_authority",
        ):
            if type(getattr(self, name)) is not bool:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact boolean",
                )
        if not self.no_private_state_authority or not self.no_order_authority:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "selected public-data contracts have no private/order authority",
            )
        if type(self.default_failure_reason) is not PITReasonCodeV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "default failure reason has the wrong exact type",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "selected contract must use exact NO_EFFECTS_V1",
            )
        _pit_validate_exact_profile_contract_v2(self)


_PIT_EVENT_KINDS_BY_PROFILE = MappingProxyType({
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


_PIT_UNAVAILABLE_BY_PROFILE = MappingProxyType({
    Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: (
        "PROVIDER_PUBLICATION_TIME",
        "PROVIDER_HISTORICAL_ORDERBOOK_CHANGE_STREAM",
        "PROVIDER_REVISION_HISTORY",
    ),
    Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: (
        "PROVIDER_NUMERIC_SEQUENCE",
        "WEBSOCKET_COMPLETE_PROVIDER_DEPTH",
        "EXACT_CHANGE_LEVEL_HISTORY",
        "EXACT_IMMUTABLE_TRADE_IDENTITY",
        "PROVIDER_PUBLICATION_TIME",
    ),
    Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: (
        "PROVIDER_PUBLICATION_TIME",
        "PROVIDER_HISTORICAL_ORDERBOOK_CHANGE_STREAM",
        "PROVIDER_REVISION_HISTORY",
    ),
})


def _pit_validate_exact_profile_contract_v2(
    contract: SelectedPITPublicDataContractV2,
) -> None:
    """Prevent a typed contract copy from widening the frozen profile policy."""

    profile_row = next(
        row
        for row in policy.PIT_SELECTED_SCOPE_V2.profiles
        if row.profile_id is contract.profile_id
    )
    protocol = policy._pit_profile_protocol_policy_v2(contract.profile_id)
    expected_fields: dict[str, object] = {
        "contract_id": f"S1-PIT-PUBLIC-DATA::{contract.profile_id.value}::V2",
        "scope_receipt_ref": policy.PIT_SELECTED_SCOPE_V2.source_decision_ref,
        "operating_legal_entity": profile_row.operating_legal_entity,
        "product_profile": profile_row.api_profile,
        "jurisdiction": profile_row.jurisdiction,
        "production_rest_base": protocol["production_rest_base"],
        "websocket_url": protocol["websocket_url"],
        "allowed_access_classes": protocol["allowed_access_classes"],
        "allowed_methods": protocol["allowed_methods"],
        "allowed_paths": protocol["allowed_paths"],
        "allowed_channels": protocol["allowed_channels"],
        "wire_dialect_policy": protocol["wire_dialect_policy"],
        "subscription_form": (
            "use_yes_price=true"
            if contract.profile_id
            is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT
            else "EXACT_PROFILE_ALLOWLISTED_SUBSCRIPTION"
        ),
        "sequence_model": protocol["sequence_model"],
        "snapshot_model": protocol["snapshot_model"],
        "recovery_model": protocol["recovery_model"],
        "heartbeat_model": protocol["heartbeat_model"],
        "admitted_event_kinds": _PIT_EVENT_KINDS_BY_PROFILE[contract.profile_id],
        "event_identity_fields": ("event_id", "event_kind", "source_version"),
        "market_identity_fields": ("market_id", "market_slug_or_ticker"),
        "instrument_identity_fields": ("instrument_id", "source_symbol"),
        "outcome_and_side_fields": (
            "source_outcome_id",
            "source_side",
            "canonical_side",
        ),
        "depth_class": protocol["depth_class"],
        "price_quantity_tick_model": (
            "CANONICAL_DECIMAL_TEXT_SCALE_ORIGIN_INCREMENT"
        ),
        "lifecycle_and_finality_fields": (
            "lifecycle_state",
            "lifecycle_version",
            "settlement_finality_time_or_none",
        ),
        "credential_alias_required": protocol["credential_alias_required"],
        "default_failure_reason": PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
        "unavailable_capabilities": _PIT_UNAVAILABLE_BY_PROFILE[
            contract.profile_id
        ],
        "recovery_preconditions": (
            "NEW_CONNECTION_EPOCH",
            "FRESH_VALID_ANCHOR_OR_CURRENT_STATE_FRAME",
            "INDEPENDENT_RECONSTRUCTION_VALID",
            "CURRENT_SOURCE_AND_RIGHTS",
        ),
    }
    mismatched = tuple(
        name
        for name, expected in expected_fields.items()
        if getattr(contract, name) != expected
    )
    if mismatched:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
            "selected contract differs from its exact frozen profile policy: "
            + ", ".join(mismatched),
        )


def build_selected_pit_public_data_contracts_v2(
    selected_scope: Stage1SelectedScopeV2,
    source_currentization_receipts: tuple[PITSourceCurrentizationReceiptV1, ...],
    rights_receipts: tuple[PITRightsAdmissionReceiptV1, ...],
    *,
    evaluated_at_utc: datetime,
) -> tuple[SelectedPITPublicDataContractV2, ...]:
    """Build the three selected contracts in the sole scope serialization order."""

    if type(selected_scope) is not Stage1SelectedScopeV2 or selected_scope != (
        policy.PIT_SELECTED_SCOPE_V2
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "selected_scope must equal the sole Stage1SelectedScopeV2 authority",
        )
    if type(source_currentization_receipts) is not tuple or any(
        type(value) is not PITSourceCurrentizationReceiptV1
        for value in source_currentization_receipts
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
            "source receipts must be exact typed values",
        )
    if type(rights_receipts) is not tuple or any(
        type(value) is not PITRightsAdmissionReceiptV1 for value in rights_receipts
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
            "rights receipts must be exact typed values",
        )
    source_by_profile = {value.profile_id: value for value in source_currentization_receipts}
    rights_by_profile = {value.profile_id: value for value in rights_receipts}
    expected = set(selected_scope.serialization)
    if (
        len(source_by_profile) != len(source_currentization_receipts)
        or len(rights_by_profile) != len(rights_receipts)
        or set(source_by_profile) != expected
        or set(rights_by_profile) != expected
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "source and rights receipt profile sets must equal selected scope",
        )
    if (
        type(evaluated_at_utc) is not datetime
        or evaluated_at_utc.tzinfo is None
        or evaluated_at_utc.utcoffset() is None
        or evaluated_at_utc.utcoffset().total_seconds() != 0
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
            "evaluated_at_utc must be an aware UTC datetime",
        )
    else:
        evaluated = evaluated_at_utc.astimezone(UTC)
    profile_by_id = {value.profile_id: value for value in selected_scope.profiles}
    contracts: list[SelectedPITPublicDataContractV2] = []
    for profile_id in selected_scope.serialization:
        source = source_by_profile[profile_id]
        rights = rights_by_profile[profile_id]
        if (
            evaluated < source.effective_at_utc
            or evaluated < source.checked_at_utc
            or evaluated - source.checked_at_utc > timedelta(hours=24)
            or evaluated < rights.checked_at_utc
            or evaluated >= source.expires_at_utc
            or evaluated >= rights.expires_at_utc
            or source.source_id != rights.source_id
            or source.invalidating_change_detected
            or rights.revoked
        ):
            raise PITDataContractErrorV1(
                (
                    PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE
                    if evaluated < source.effective_at_utc
                    or evaluated < source.checked_at_utc
                    or evaluated - source.checked_at_utc > timedelta(hours=24)
                    or evaluated >= source.expires_at_utc
                    or source.invalidating_change_detected
                    else PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED
                ),
                "source or rights receipt is stale, revoked, or cross-source",
            )
        row = profile_by_id[profile_id]
        protocol = policy._pit_profile_protocol_policy_v2(profile_id)
        contracts.append(
            SelectedPITPublicDataContractV2(
                contract_id=f"S1-PIT-PUBLIC-DATA::{profile_id.value}::V2",
                contract_version="S1_PIT_PUBLIC_DATA_CONTRACT_V2",
                profile_id=profile_id,
                scope_receipt_ref=selected_scope.source_decision_ref,
                operating_legal_entity=row.operating_legal_entity,
                product_profile=row.api_profile,
                jurisdiction=row.jurisdiction,
                production_rest_base=_pit_binding_text(
                    protocol["production_rest_base"], "production_rest_base"
                ),
                websocket_url=_pit_binding_text(
                    protocol["websocket_url"], "websocket_url"
                ),
                allowed_access_classes=protocol["allowed_access_classes"],
                allowed_methods=protocol["allowed_methods"],
                allowed_paths=protocol["allowed_paths"],
                allowed_channels=protocol["allowed_channels"],
                wire_dialect_policy=_pit_binding_text(
                    protocol["wire_dialect_policy"], "wire_dialect_policy"
                ),
                subscription_form=(
                    "use_yes_price=true"
                    if profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT
                    else "EXACT_PROFILE_ALLOWLISTED_SUBSCRIPTION"
                ),
                sequence_model=_pit_binding_text(
                    protocol["sequence_model"], "sequence_model"
                ),
                snapshot_model=_pit_binding_text(
                    protocol["snapshot_model"], "snapshot_model"
                ),
                recovery_model=_pit_binding_text(
                    protocol["recovery_model"], "recovery_model"
                ),
                heartbeat_model=_pit_binding_text(
                    protocol["heartbeat_model"], "heartbeat_model"
                ),
                admitted_event_kinds=_PIT_EVENT_KINDS_BY_PROFILE[profile_id],
                event_identity_fields=("event_id", "event_kind", "source_version"),
                market_identity_fields=("market_id", "market_slug_or_ticker"),
                instrument_identity_fields=("instrument_id", "source_symbol"),
                outcome_and_side_fields=("source_outcome_id", "source_side", "canonical_side"),
                depth_class=protocol["depth_class"],
                price_quantity_tick_model="CANONICAL_DECIMAL_TEXT_SCALE_ORIGIN_INCREMENT",
                lifecycle_and_finality_fields=(
                    "lifecycle_state",
                    "lifecycle_version",
                    "settlement_finality_time_or_none",
                ),
                source_currentization_receipt_ref=source.receipt_id,
                source_contract_version=source.source_contract_version,
                rights_receipt_ref=rights.receipt_id,
                agreement_version=rights.agreement_version,
                credential_alias_required=_pit_binding_boolean(
                    protocol["credential_alias_required"],
                    "credential_alias_required",
                ),
                no_private_state_authority=True,
                no_order_authority=True,
                default_failure_reason=PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                unavailable_capabilities=_PIT_UNAVAILABLE_BY_PROFILE[profile_id],
                recovery_preconditions=(
                    "NEW_CONNECTION_EPOCH",
                    "FRESH_VALID_ANCHOR_OR_CURRENT_STATE_FRAME",
                    "INDEPENDENT_RECONSTRUCTION_VALID",
                    "CURRENT_SOURCE_AND_RIGHTS",
                ),
            )
        )
    return tuple(contracts)
