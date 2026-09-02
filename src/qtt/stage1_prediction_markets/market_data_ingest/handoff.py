from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest.binding import (
    SelectedPITPublicDataContractV2,
)
from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
    FormulaInputAuthorityBindingV1,
    ST12DMath39RawInputBindingV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.freshness import (
    FreshnessAndDowngradePolicyV2,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
    PITInputCapabilityV2,
    partition_pit_formula_input_authority_v1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
    NoEffectFlagsV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PITDataContractErrorV1,
    PITDepthClassV2,
    PITInputAvailabilityV2,
    PITReasonCodeV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
    CaptureAndGapReceiptV2,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    Stage1VenueProfileIdV1,
)


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


def _pit_handoff_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


def _pit_applicable_binding_rows() -> tuple[object, ...]:
    partition = partition_pit_formula_input_authority_v1()
    applicable = partition.pit_applicable_binding_ids
    rows: list[object] = []
    for values in CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID.values():
        for value in values:
            if value.binding_id in applicable:
                rows.append(value)
    if tuple(value.binding_id for value in rows) != (
        partition.pit_applicable_binding_order
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
            "capability builder did not preserve canonical binding order",
        )
    return tuple(rows)


def _pit_binding_metadata(row: object) -> dict[str, object]:
    if type(row) is FormulaInputAuthorityBindingV1:
        sequence_required_paths = frozenset(
            {
                "market_state.snapshot_state",
                "orderbook.yes_bids",
                "orderbook.no_bids",
                "orderbook.book_sequence",
                "orderbook.expected_sequence",
                "orderbook.book_state",
            }
        )
        complete_depth_paths = frozenset(
            {"orderbook.yes_bids", "orderbook.no_bids"}
        )
        bbo_paths = frozenset(
            {
                "market_state.contract_price",
                "market_state.best_bid",
                "market_state.best_ask",
            }
        )
        shape_by_exact_type = {
            "Decimal string": "SCALAR",
            "boolean": "SCALAR",
            "enum": "SCALAR",
            "int": "SCALAR",
            "list[Decimal string]": "SEQUENCE",
            "list[record]": "SEQUENCE",
        }
        try:
            declared_shape = shape_by_exact_type[row.input_type]
        except KeyError as exc:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "PIT formula binding has an unclassified exact input type",
            ) from exc
        depth = (
            PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT
            if row.exact_field_path in complete_depth_paths
            else (
                PITDepthClassV2.BBO_ONLY
                if row.exact_field_path in bbo_paths
                else None
            )
        )
        return {
            "math_spec_id": row.math_spec_id,
            "input_name": row.input_name,
            "packet_type": row.accepted_packet_or_snapshot_type,
            "source_path": row.exact_field_path,
            "input_type": row.input_type,
            "shape": declared_shape,
            "unit": row.unit_or_basis,
            "transform": row.canonical_typed_value_extraction,
            "required_clock_fields": tuple(row.required_clock_fields),
            "depth": depth,
            "sequence_required": row.exact_field_path in sequence_required_paths,
            "required_state": (
                "CURRENT_CONTIGUOUS_BOOK"
                if row.exact_field_path in sequence_required_paths
                else "CURRENT_POINT_IN_TIME_VALUE"
            ),
        }
    if type(row) is ST12DMath39RawInputBindingV1:
        return {
            "math_spec_id": "MATH-39",
            "input_name": row.input_name,
            "packet_type": row.accepted_packet_or_snapshot_type,
            "source_path": row.exact_field_path,
            "input_type": "SequencedBookEventsPacketV1",
            "shape": "SEQUENCE",
            "unit": row.unit_or_basis,
            "transform": row.point_in_time_rule,
            "required_clock_fields": (
                "qtt_received_at_utc",
                "qtt_parse_completed_at_utc",
                "durable_commit_completed_at_utc",
                "strategy_available_at_utc",
            ),
            "depth": PITDepthClassV2.INCREMENTAL_FROM_COMPLETE_ANCHOR,
            "sequence_required": True,
            "required_state": "CURRENT_CONTIGUOUS_CHANGE_LEVEL_BOOK",
        }
    raise PITDataContractErrorV1(
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
        "capability builder received an unclassified binding type",
    )


def _pit_intrinsic_capability_failure(
    profile_id: Stage1VenueProfileIdV1,
    row: object,
) -> tuple[PITInputAvailabilityV2, PITReasonCodeV1] | None:
    if (
        type(row) is FormulaInputAuthorityBindingV1
        and row.accepted_upstream_owner_id
        in {
            "KalshiAcceptedOrderBookStateOwnerV1",
            "KalshiMarketMetadataOwnerV1",
        }
        and profile_id is not Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT
    ):
        return (
            PITInputAvailabilityV2.UNAVAILABLE_SOURCE_FIELD,
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
        )
    if type(row) is ST12DMath39RawInputBindingV1 and profile_id is (
        Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT
    ):
        return (
            PITInputAvailabilityV2.UNAVAILABLE_CHANGE_LEVEL_HISTORY,
            PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE,
        )
    if (
        type(row) is FormulaInputAuthorityBindingV1
        and row.accepted_upstream_owner_id
        == "SelectedVenuePublicMarketDataOwnerV1"
        and row.domain == "CURRENT_CONTIGUOUS_BOOK"
        and profile_id is Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT
    ):
        return (
            PITInputAvailabilityV2.UNAVAILABLE_CONTINUITY,
            PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE,
        )
    return None


def build_pit_input_capabilities_v2(
    contracts: tuple[SelectedPITPublicDataContractV2, ...],
    freshness_policies: tuple[FreshnessAndDowngradePolicyV2, ...],
    *,
    event_or_snapshot_refs_by_profile: tuple[
        tuple[Stage1VenueProfileIdV1, str], ...
    ],
    context_id: str,
    source_epoch_id: str,
    input_version: str,
) -> tuple[PITInputCapabilityV2, ...]:
    """Construct the exact selected-profile by PIT-binding capability matrix."""

    for name, value in (
        ("context_id", context_id),
        ("source_epoch_id", source_epoch_id),
        ("input_version", input_version),
    ):
        _pit_handoff_text(value, name)
    if type(contracts) is not tuple or any(
        type(value) is not SelectedPITPublicDataContractV2 for value in contracts
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "capability construction requires exact selected contracts",
        )
    contract_by_profile = {value.profile_id: value for value in contracts}
    expected_profiles = set(policy.PIT_SELECTED_SCOPE_V2.serialization)
    if len(contract_by_profile) != len(contracts) or set(contract_by_profile) != (
        expected_profiles
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "contract profile set differs from selected scope",
        )
    if type(event_or_snapshot_refs_by_profile) is not tuple or any(
        type(value) is not tuple
        or len(value) != 2
        or type(value[0]) is not Stage1VenueProfileIdV1
        or type(value[1]) is not str
        for value in event_or_snapshot_refs_by_profile
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "event/snapshot references must be exact profile/reference pairs",
        )
    event_ref_by_profile = dict(event_or_snapshot_refs_by_profile)
    if len(event_ref_by_profile) != 3 or set(event_ref_by_profile) != expected_profiles:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "event/snapshot reference set differs from selected profiles",
        )
    for value in event_ref_by_profile.values():
        _pit_handoff_text(value, "event_or_snapshot_ref")
    if type(freshness_policies) is not tuple or any(
        type(value) is not FreshnessAndDowngradePolicyV2
        for value in freshness_policies
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_FRESHNESS_EXPIRED,
            "freshness policies must be exact per-capability decisions",
        )
    freshness_by_key = {value.capability_key: value for value in freshness_policies}
    if len(freshness_by_key) != len(freshness_policies):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
            "duplicate freshness capability key",
        )
    binding_rows = _pit_applicable_binding_rows()
    expected_keys = {
        (profile_id, row.binding_id)
        for profile_id in policy.PIT_SELECTED_SCOPE_V2.serialization
        for row in binding_rows
    }
    expected_freshness_keys = {
        f"{profile_id.value}::{binding_id}"
        for profile_id, binding_id in expected_keys
    }
    if set(freshness_by_key) != expected_freshness_keys:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_FRESHNESS_EXPIRED,
            "freshness policy keys must equal profile by PIT-binding keys",
        )
    capabilities: list[PITInputCapabilityV2] = []
    for profile_id in policy.PIT_SELECTED_SCOPE_V2.serialization:
        contract = contract_by_profile[profile_id]
        for row in binding_rows:
            metadata = _pit_binding_metadata(row)
            capability_key = f"{profile_id.value}::{row.binding_id}"
            freshness = freshness_by_key[capability_key]
            intrinsic = _pit_intrinsic_capability_failure(profile_id, row)
            if intrinsic is not None:
                availability, reason = intrinsic
                event_ref: str | None = None
                freshness_ref: str | None = None
            elif freshness.terminal_availability is not (
                PITInputAvailabilityV2.AVAILABLE
            ):
                availability = freshness.terminal_availability
                reason = freshness.terminal_reason_or_none
                if reason is None:
                    raise PITDataContractErrorV1(
                        PITReasonCodeV1.PIT_FRESHNESS_EXPIRED,
                        "unavailable freshness decision lacks a specific reason",
                    )
                event_ref = None
                freshness_ref = None
            else:
                availability = PITInputAvailabilityV2.AVAILABLE
                reason = None
                event_ref = event_ref_by_profile[profile_id]
                freshness_ref = f"FRESHNESS::{capability_key}"
            capabilities.append(
                PITInputCapabilityV2(
                    capability_id=f"PIT-CAPABILITY::{capability_key}",
                    profile_id=profile_id,
                    binding_id=row.binding_id,
                    math_spec_id=metadata["math_spec_id"],
                    input_name=metadata["input_name"],
                    accepted_packet_or_snapshot_type=metadata["packet_type"],
                    source_field_path=metadata["source_path"],
                    declared_input_type=metadata["input_type"],
                    declared_shape_or_none=metadata["shape"],
                    unit_or_basis=metadata["unit"],
                    transform=metadata["transform"],
                    required_clock_fields=metadata["required_clock_fields"],
                    required_depth_class_or_none=metadata["depth"],
                    provider_sequence_required=metadata["sequence_required"],
                    provider_publication_time_required=False,
                    required_state=metadata["required_state"],
                    source_contract_ref=contract.contract_id,
                    rights_receipt_ref=contract.rights_receipt_ref,
                    availability=availability,
                    unavailable_reason_or_none=reason,
                    event_or_snapshot_ref_or_none=event_ref,
                    freshness_receipt_ref_or_none=freshness_ref,
                    context_id=context_id,
                    source_epoch_id=source_epoch_id,
                    input_version=input_version,
                )
            )
    actual_keys = {(value.profile_id, value.binding_id) for value in capabilities}
    if len(capabilities) != len(expected_keys) or actual_keys != expected_keys:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
            "emitted capability key set does not equal exact expected set",
        )
    return tuple(capabilities)


def _pit_validate_capability_matrix_metadata(
    contracts: tuple[SelectedPITPublicDataContractV2, ...],
    capabilities: tuple[PITInputCapabilityV2, ...],
) -> None:
    expected_profile_order = policy.PIT_SELECTED_SCOPE_V2.serialization
    if tuple(contract.profile_id for contract in contracts) != expected_profile_order:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "handoff contracts do not preserve selected serialization order",
        )
    contract_by_profile = {contract.profile_id: contract for contract in contracts}
    rows_by_id = {row.binding_id: row for row in _pit_applicable_binding_rows()}
    contexts = {
        (capability.context_id, capability.source_epoch_id, capability.input_version)
        for capability in capabilities
    }
    if len(contexts) != 1:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
            "capability matrix must bind one context, source epoch, and input version",
        )
    for capability in capabilities:
        row = rows_by_id.get(capability.binding_id)
        contract = contract_by_profile.get(capability.profile_id)
        if row is None or contract is None:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "capability does not bind an exact selected profile/formula row",
            )
        metadata = _pit_binding_metadata(row)
        expected_metadata = {
            "capability_id": (
                f"PIT-CAPABILITY::{capability.profile_id.value}::"
                f"{capability.binding_id}"
            ),
            "math_spec_id": metadata["math_spec_id"],
            "input_name": metadata["input_name"],
            "accepted_packet_or_snapshot_type": metadata["packet_type"],
            "source_field_path": metadata["source_path"],
            "declared_input_type": metadata["input_type"],
            "declared_shape_or_none": metadata["shape"],
            "unit_or_basis": metadata["unit"],
            "transform": metadata["transform"],
            "required_clock_fields": metadata["required_clock_fields"],
            "required_depth_class_or_none": metadata["depth"],
            "provider_sequence_required": metadata["sequence_required"],
            "provider_publication_time_required": False,
            "required_state": metadata["required_state"],
            "source_contract_ref": contract.contract_id,
            "rights_receipt_ref": contract.rights_receipt_ref,
        }
        if any(
            getattr(capability, name) != expected
            for name, expected in expected_metadata.items()
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "capability metadata differs from its canonical formula/source binding",
            )
        intrinsic = _pit_intrinsic_capability_failure(capability.profile_id, row)
        if intrinsic is not None and (
            capability.availability is not intrinsic[0]
            or capability.unavailable_reason_or_none is not intrinsic[1]
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "capability overstates an intrinsic selected-profile limit",
            )
        if capability.availability is PITInputAvailabilityV2.AVAILABLE and (
            capability.freshness_receipt_ref_or_none
            != f"FRESHNESS::{capability.profile_id.value}::{capability.binding_id}"
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_FRESHNESS_EXPIRED,
                "available capability freshness lineage is not exact",
            )


@dataclass(frozen=True, slots=True)
class PITMarketDataDownstreamHandoffV2:
    handoff_id: str
    schema_version: str
    selected_contracts: tuple[SelectedPITPublicDataContractV2, ...]
    input_capabilities: tuple[PITInputCapabilityV2, ...]
    canonical_event_refs: tuple[str, ...]
    capture_and_gap_receipt_refs: tuple[str, ...]
    expected_capability_keys: frozenset[
        tuple[Stage1VenueProfileIdV1, str]
    ]
    exact_capability_key_set_equal: bool
    provider_sequence_unavailable_profiles: tuple[Stage1VenueProfileIdV1, ...]
    provider_publication_time_unavailable_profiles: tuple[
        Stage1VenueProfileIdV1, ...
    ]
    change_history_unavailable_profiles: tuple[Stage1VenueProfileIdV1, ...]
    no_network_effect: bool
    no_private_state: bool
    no_order_or_capital_effect: bool
    no_llm_or_quantum_effect: bool
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        _pit_handoff_text(self.handoff_id, "handoff_id")
        _pit_handoff_text(self.schema_version, "schema_version")
        if self.schema_version != "PIT_MARKET_DATA_DOWNSTREAM_HANDOFF_V2":
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "market-data handoff schema version is not exact V2",
            )
        if type(self.selected_contracts) is not tuple or any(
            type(value) is not SelectedPITPublicDataContractV2
            for value in self.selected_contracts
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "handoff contracts have the wrong exact type",
            )
        if type(self.input_capabilities) is not tuple or any(
            type(value) is not PITInputCapabilityV2
            for value in self.input_capabilities
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "handoff capabilities have the wrong exact type",
            )
        _pit_validate_capability_matrix_metadata(
            self.selected_contracts,
            self.input_capabilities,
        )
        for name in (
            "canonical_event_refs",
            "capture_and_gap_receipt_refs",
        ):
            value = getattr(self, name)
            if type(value) is not tuple or not value or any(
                type(item) is not str or not item for item in value
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact text tuple",
                )
            if len(value) != len(set(value)):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                    f"{name} contains duplicates",
                )
        if type(self.expected_capability_keys) is not frozenset:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "expected capability keys must be an exact frozenset",
            )
        partition = partition_pit_formula_input_authority_v1()
        canonical_expected = frozenset(
            (profile_id, binding_id)
            for profile_id in policy.PIT_SELECTED_SCOPE_V2.serialization
            for binding_id in partition.pit_applicable_binding_order
        )
        actual = {
            (value.profile_id, value.binding_id)
            for value in self.input_capabilities
        }
        if (
            type(self.exact_capability_key_set_equal) is not bool
            or not self.exact_capability_key_set_equal
            or self.expected_capability_keys != canonical_expected
            or actual != set(self.expected_capability_keys)
            or len(actual) != len(self.input_capabilities)
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "handoff capability matrix is not exact and unique",
            )
        for name in (
            "provider_sequence_unavailable_profiles",
            "provider_publication_time_unavailable_profiles",
            "change_history_unavailable_profiles",
        ):
            value = getattr(self, name)
            if type(value) is not tuple or any(
                type(item) is not Stage1VenueProfileIdV1 for item in value
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                    f"{name} has the wrong exact profile type",
                )
        exact_unavailable_profiles = {
            "provider_sequence_unavailable_profiles": (
                Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT,
            ),
            "provider_publication_time_unavailable_profiles": (
                *policy.PIT_SELECTED_SCOPE_V2.serialization,
            ),
            "change_history_unavailable_profiles": (
                Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT,
            ),
        }
        if any(
            getattr(self, name) != expected
            for name, expected in exact_unavailable_profiles.items()
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "handoff unavailable-profile limits are not exact",
            )
        for name in (
            "no_network_effect",
            "no_private_state",
            "no_order_or_capital_effect",
            "no_llm_or_quantum_effect",
        ):
            if type(getattr(self, name)) is not bool or not getattr(self, name):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                    f"{name} must be exact True",
                )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "handoff must carry exact NO_EFFECTS_V1",
            )


def build_pit_market_data_handoff_v2(
    contracts: tuple[SelectedPITPublicDataContractV2, ...],
    capabilities: tuple[PITInputCapabilityV2, ...],
    *,
    canonical_event_refs: tuple[str, ...],
    capture_and_gap_receipt_refs: tuple[str, ...],
    handoff_id: str = "S1-PIT-MARKET-DATA-DOWNSTREAM-HANDOFF-V2",
) -> PITMarketDataDownstreamHandoffV2:
    partition = partition_pit_formula_input_authority_v1()
    expected_keys = frozenset(
        (profile_id, binding_id)
        for profile_id in policy.PIT_SELECTED_SCOPE_V2.serialization
        for binding_id in partition.pit_applicable_binding_order
    )
    actual_keys = {(value.profile_id, value.binding_id) for value in capabilities}
    return PITMarketDataDownstreamHandoffV2(
        handoff_id=handoff_id,
        schema_version="PIT_MARKET_DATA_DOWNSTREAM_HANDOFF_V2",
        selected_contracts=contracts,
        input_capabilities=capabilities,
        canonical_event_refs=canonical_event_refs,
        capture_and_gap_receipt_refs=capture_and_gap_receipt_refs,
        expected_capability_keys=expected_keys,
        exact_capability_key_set_equal=(
            actual_keys == set(expected_keys)
            and len(actual_keys) == len(capabilities)
        ),
        provider_sequence_unavailable_profiles=(
            Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT,
        ),
        provider_publication_time_unavailable_profiles=(
            *policy.PIT_SELECTED_SCOPE_V2.serialization,
        ),
        change_history_unavailable_profiles=(
            Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT,
        ),
        no_network_effect=True,
        no_private_state=True,
        no_order_or_capital_effect=True,
        no_llm_or_quantum_effect=True,
    )


def project_selected_pit_public_data_contract_v1(
    contract: SelectedPITPublicDataContractV2,
) -> Mapping[str, object]:
    if type(contract) is not SelectedPITPublicDataContractV2:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "V1 projection requires exact V2 selected contract",
        )
    return MappingProxyType(
        {
            "schema_version": "SELECTED_PIT_PUBLIC_DATA_CONTRACT_V1_PROJECTION",
            "contract_id": contract.contract_id,
            "profile_id": contract.profile_id.value,
            "rest_base": contract.production_rest_base,
            "websocket_url": contract.websocket_url,
            "allowed_paths": contract.allowed_paths,
            "allowed_channels": contract.allowed_channels,
            "source_receipt_ref": contract.source_currentization_receipt_ref,
            "rights_receipt_ref": contract.rights_receipt_ref,
            "depth_class": contract.depth_class.value,
            "provider_sequence_model": contract.sequence_model,
            "provider_publication_time": "EXPLICITLY_UNAVAILABLE",
            "unsupported_v1_fields": (
                "CROSS_CLOCK_PUBLICATION_LATENCY",
                "GENERIC_FULL_DEPTH_OVERCLAIM",
            ),
        }
    )


def project_capture_and_gap_receipt_v1(
    receipt: CaptureAndGapReceiptV2,
) -> Mapping[str, object]:
    if type(receipt) is not CaptureAndGapReceiptV2:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "V1 projection requires exact CaptureAndGapReceiptV2",
        )
    return MappingProxyType(
        {
            "schema_version": "CAPTURE_AND_GAP_RECEIPT_V1_PROJECTION",
            "receipt_id": receipt.receipt_id,
            "event_id": receipt.event_record_id,
            "profile_id": receipt.profile_id.value,
            "connection_epoch": receipt.connection_epoch,
            "event_disposition": receipt.event_disposition.value,
            "continuity_result": receipt.continuity_result.value,
            "integrity_result": receipt.integrity_result.value,
            "failure_reason_or_none": (
                receipt.failure_reason_or_none.value
                if receipt.failure_reason_or_none is not None
                else None
            ),
            "recovery_required": receipt.recovery_required,
            "commit_completion_ref_or_none": (
                receipt.commit_completion_ref_or_none
            ),
            "unsupported_v1_fields": (),
        }
    )


def project_freshness_and_downgrade_policy_v1(
    freshness: FreshnessAndDowngradePolicyV2,
) -> Mapping[str, object]:
    if type(freshness) is not FreshnessAndDowngradePolicyV2:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "V1 projection requires exact V2 freshness decision",
        )
    return MappingProxyType(
        {
            "schema_version": "FRESHNESS_AND_DOWNGRADE_POLICY_V1_PROJECTION",
            "capability_key": freshness.capability_key,
            "terminal_availability": freshness.terminal_availability.value,
            "terminal_reason_or_none": (
                freshness.terminal_reason_or_none.value
                if freshness.terminal_reason_or_none is not None
                else None
            ),
            "downgrade_route": freshness.downgrade_route,
            "recovery_requirements": freshness.recovery_requirements,
            "unsupported_v1_fields": (
                "PROVIDER_PUBLICATION_LATENCY_WHEN_SOURCE_TIME_ABSENT",
            ),
        }
    )
