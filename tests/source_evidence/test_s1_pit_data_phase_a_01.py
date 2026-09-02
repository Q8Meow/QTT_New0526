from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any, Callable, Mapping

import pytest


_T0 = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)
_SELECTED_PROFILE_VALUES = (
    "GEMINI_TITAN_DIRECT",
    "POLYMARKET_US_RETAIL_DIRECT",
    "KALSHI_US_DCM_DIRECT",
)
_ALLOWED_SEMANTIC_PATHS = frozenset(
    {
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/point_in_time.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/freshness.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/input_resolver.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/receipts.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/source_policy.py",
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/__init__.py",
        "src/qtt/stage1_prediction_markets/market_data_ingest/policy.py",
        "src/qtt/stage1_prediction_markets/market_data_ingest/adapter.py",
        "src/qtt/stage1_prediction_markets/market_data_ingest/binding.py",
        "src/qtt/stage1_prediction_markets/market_data_ingest/source_dependency.py",
        "src/qtt/stage1_prediction_markets/market_data_ingest/validator.py",
        "src/qtt/stage1_prediction_markets/market_data_ingest/canonical_market_data_ingest_event.schema.json",
        "src/qtt/stage1_prediction_markets/market_data_ingest/market_data_source_dependency.schema.json",
        "src/qtt/stage1_prediction_markets/market_data_ingest/market_data_no_live_network_attestation.schema.json",
        "src/qtt/stage1_prediction_markets/market_data_ingest/handoff.py",
        "src/qtt/stage1_prediction_markets/market_data_ingest/market_data_ingest_downstream_handoff.schema.json",
        "src/qtt/stage1_prediction_markets/market_data_ingest/__init__.py",
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/policy.py",
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/builder.py",
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/integrity.py",
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/input_lock.py",
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/validator.py",
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/event_state_snapshot.schema.json",
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/orderbook_snapshot.schema.json",
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/snapshot_builder_binding.schema.json",
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/handoff.py",
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/snapshot_downstream_handoff.schema.json",
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/__init__.py",
        "tests/source_evidence/test_pr132_schema_enums_and_quantum_fields_match_policy_constants.py",
        "tests/source_evidence/test_s1_pit_data_phase_a_01.py",
    }
)
_ALLOWED_CENTRAL_CLOSURE_PATHS = frozenset(
    {
        "tools/ci_branch_context.py",
        "tools/validation_scope_registry.py",
        "tools/validation_inventory.py",
        "tools/changed_area_validation_router.py",
        "tests/tools/test_ci_branch_context.py",
        "tests/tools/test_validation_scope_registry.py",
        "tests/tools/test_validation_inventory.py",
        "tests/tools/test_changed_area_validation_router.py",
    }
)
_ALLOWED_CONDITIONAL_PATHS = frozenset(
    {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json",
    }
)
_ALLOWED_CANDIDATE_PATHS = frozenset(
    (
        *_ALLOWED_SEMANTIC_PATHS,
        *_ALLOWED_CENTRAL_CLOSURE_PATHS,
        *_ALLOWED_CONDITIONAL_PATHS,
    )
)


@dataclass(frozen=True, slots=True)
class PITCase:
    name: str
    operation: Callable[[], None]

    def run(self) -> None:
        self.operation()


def _expect_pit_error(operation: Callable[[], object], reason: object | None = None) -> None:
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITDataContractErrorV1,
    )

    with pytest.raises(PITDataContractErrorV1) as caught:
        operation()
    if reason is not None:
        assert caught.value.pit_reason_code is reason


def _build_source_and_rights() -> tuple[tuple[object, ...], tuple[object, ...]]:
    from src.qtt.stage1_prediction_markets.market_data_ingest import policy
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
        PITRightsAdmissionReceiptV1,
        PITSourceCurrentizationReceiptV1,
        validate_pit_source_rights_admission_v1,
    )

    sources = []
    rights = []
    for profile_id in policy.PIT_SELECTED_SCOPE_V2.serialization:
        source_id = f"SOURCE::{profile_id.value}"
        source = PITSourceCurrentizationReceiptV1(
            receipt_id=f"SOURCE-RECEIPT::{profile_id.value}",
            profile_id=profile_id,
            source_id=source_id,
            source_contract_version=f"SOURCE-CONTRACT::{profile_id.value}::V1",
            checked_at_utc=_T0,
            effective_at_utc=_T0 - timedelta(hours=1),
            expires_at_utc=_T0 + timedelta(hours=12),
            currentization_owner_id="SOURCE_CURRENTIZATION_OWNER_V1",
            recheck_triggers=("DETECTED_CHANGE", "EXPIRY"),
            invalidating_change_detected=False,
            admitted_current=True,
        )
        right = PITRightsAdmissionReceiptV1(
            receipt_id=f"RIGHTS-RECEIPT::{profile_id.value}",
            profile_id=profile_id,
            account_scope=f"PUBLIC-MARKET-DATA::{profile_id.value}",
            source_id=source_id,
            agreement_id=f"AGREEMENT::{profile_id.value}",
            agreement_version="OWNER-ADMISSION-V1",
            internal_use_class="INTERNAL_REFERENCE_AND_RECONSTRUCTION",
            owner_decision="ADMITTED_INTERNAL_USE",
            checked_at_utc=_T0,
            expires_at_utc=_T0 + timedelta(hours=12),
            recheck_triggers=("RIGHTS_CHANGE", "EXPIRY"),
            revoked=False,
            permitted_retention_class="APPEND_ONLY_INTERNAL_REFERENCE",
            prohibited_redistribution_class="NO_EXTERNAL_REDISTRIBUTION",
        )
        admission = validate_pit_source_rights_admission_v1(
            source,
            right,
            admission_id=f"SOURCE-RIGHTS::{profile_id.value}",
            profile_id=profile_id,
            account_scope=right.account_scope,
            internal_use_class=right.internal_use_class,
            permitted_retention_class=right.permitted_retention_class,
            evaluated_at_utc=_T0,
        )
        assert admission.admitted is True
        sources.append(source)
        rights.append(right)
    return tuple(sources), tuple(rights)


def _build_contracts() -> tuple[object, ...]:
    from src.qtt.stage1_prediction_markets.market_data_ingest import policy
    from src.qtt.stage1_prediction_markets.market_data_ingest.binding import (
        build_selected_pit_public_data_contracts_v2,
    )

    sources, rights = _build_source_and_rights()
    return build_selected_pit_public_data_contracts_v2(
        policy.PIT_SELECTED_SCOPE_V2,
        sources,
        rights,
        evaluated_at_utc=_T0,
    )


def _contract_by_value(profile_value: str) -> object:
    return next(
        contract
        for contract in _build_contracts()
        if contract.profile_id.value == profile_value
    )


def _frame(
    profile_value: str,
    source_tree: Mapping[str, object],
    *,
    suffix: str,
    channel: str,
    wire_dialect: str,
    connection_epoch: str = "EPOCH-1",
    capture_session_id: str = "CAPTURE-1",
) -> object:
    from src.qtt.stage1_prediction_markets.market_data_ingest.adapter import PITRawFrameV1

    contract = _contract_by_value(profile_value)
    return PITRawFrameV1(
        frame_id=f"FRAME::{profile_value}::{suffix}",
        profile_id=contract.profile_id,
        connection_epoch=connection_epoch,
        capture_session_id=capture_session_id,
        wire_dialect=wire_dialect,
        channel=channel,
        raw_utf8_text_or_none=None,
        parsed_source_scalar_tree_or_none=dict(source_tree),
        qtt_received_at_utc=_T0 + timedelta(seconds=1),
        qtt_received_monotonic_ns=100,
        process_epoch_id="PROCESS-EPOCH-1",
        monotonic_clock_id="PERF-COUNTER-NS-1",
        wall_clock_source_id="TEST-WALL-CLOCK-1",
        clock_quality_receipt_ref="CLOCK-QUALITY-1",
        wall_clock_uncertainty_ns=1_000,
        source_contract_refs=(contract.contract_id,),
    )


def _ingest(
    frame: object,
    event_kind: object,
    *,
    dispatcher: object | None = None,
    explicit_pre_data_subscription_error: bool = False,
) -> object:
    from src.qtt.stage1_prediction_markets.market_data_ingest.validator import (
        PITMarketDataIngestDispatcherV2,
        ingest_pit_frame_v2,
    )

    active_dispatcher = dispatcher or PITMarketDataIngestDispatcherV2(
        _build_contracts()
    )
    return ingest_pit_frame_v2(
        active_dispatcher,
        frame,
        event_kind=event_kind,
        parse_completed_at_utc=_T0 + timedelta(seconds=2),
        parse_completed_monotonic_ns=200,
        price_increment_text="0.01",
        price_origin_text="0",
        quantity_increment_text_or_none="0.01",
        explicit_pre_data_subscription_error=explicit_pre_data_subscription_error,
    )


def _clock(**changes: object) -> object:
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITClockSetV3,
    )

    values = {
        "provider_event_time_utc_or_none": _T0,
        "provider_publication_time_utc_or_none": None,
        "qtt_received_at_utc": _T0 + timedelta(seconds=1),
        "qtt_received_monotonic_ns": 10,
        "qtt_parse_completed_at_utc": _T0 + timedelta(seconds=2),
        "qtt_parse_completed_monotonic_ns": 20,
        "durable_commit_completed_at_utc": _T0 + timedelta(seconds=3),
        "durable_commit_completed_monotonic_ns": 30,
        "strategy_available_at_utc": _T0 + timedelta(seconds=4),
        "strategy_available_monotonic_ns": 40,
        "revision_effective_time_utc_or_none": _T0 + timedelta(seconds=3),
        "settlement_finality_time_utc_or_none": _T0 + timedelta(seconds=3),
        "process_epoch_id": "PROCESS-EPOCH-1",
        "monotonic_clock_id": "PERF-COUNTER-NS-1",
        "wall_clock_source_id": "WALL-CLOCK-1",
        "clock_quality_receipt_ref": "CLOCK-QUALITY-1",
        "wall_clock_uncertainty_ns": 1_000,
    }
    values.update(changes)
    return PITClockSetV3(**values)


def _good_freshness(capability_key: str, **observation_changes: object) -> object:
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.freshness import (
        PITFreshnessObservationV2,
        PITFreshnessRequirementV2,
        evaluate_pit_freshness_v2,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITAnchorStateV1,
        PITContinuityStateV3,
        PITDepthClassV2,
        PITIntegrityStateV1,
        PITTransportStateV1,
    )

    requirement = PITFreshnessRequirementV2(
        capability_key=capability_key,
        maximum_provider_event_age_or_none=None,
        maximum_local_receive_age=timedelta(seconds=60),
        maximum_durable_commit_age=timedelta(seconds=60),
        maximum_strategy_availability_age=timedelta(seconds=60),
        economic_ttl=timedelta(seconds=60),
    )
    values = {
        "source_current": True,
        "rights_active": True,
        "transport_state": PITTransportStateV1.CONNECTED_HEALTHY,
        "anchor_state": PITAnchorStateV1.ANCHOR_ACCEPTED,
        "continuity_state": PITContinuityStateV3.CONTIGUOUS,
        "integrity_state": PITIntegrityStateV1.VALID,
        "current_state_parity_passed": True,
        "provider_event_age_or_none": None,
        "provider_publication_time_present": False,
        "local_receive_age": timedelta(seconds=1),
        "durable_commit_age": timedelta(seconds=1),
        "strategy_availability_age": timedelta(seconds=1),
        "lifecycle_admissible": True,
        "precision_valid": True,
        "tick_valid": True,
        "wall_clock_quality_sufficient": True,
        "source_conflict": False,
        "depth_class": PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT,
        "economic_age": timedelta(seconds=1),
        "durable_commit_complete": True,
    }
    values.update(observation_changes)
    return evaluate_pit_freshness_v2(
        requirement,
        PITFreshnessObservationV2(**values),
    )


def _case_scope_and_legacy_isolation() -> None:
    from src.qtt.stage1_prediction_markets.market_data_ingest import policy
    from src.qtt.stage1_prediction_markets.market_data_ingest.validator import (
        validate_pit_ingest_record_v2,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITReasonCodeV1,
    )

    scope = policy.PIT_SELECTED_SCOPE_V2
    assert tuple(value.value for value in scope.serialization) == _SELECTED_PROFILE_VALUES
    assert tuple(value.value for value in scope.excluded_profile_ids) == (
        "FORECASTEX_IBKR",
        "FORECASTEX_DIRECT_MEMBER",
    )
    assert tuple(contract.profile_id for contract in _build_contracts()) == scope.serialization
    _expect_pit_error(
        lambda: validate_pit_ingest_record_v2("GENERIC_UNKNOWN_PROFILE"),
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    )
    schema_dir = Path("src/qtt/stage1_prediction_markets/market_data_ingest")
    legacy_only = json.loads(
        (schema_dir / "market_data_no_live_network_attestation.schema.json").read_text(
            encoding="utf-8"
        )
    )
    assert legacy_only["properties"]["schema_version"]["const"].endswith("_V1")
    assert "oneOf" not in legacy_only
    for name in (
        "canonical_market_data_ingest_event.schema.json",
        "market_data_source_dependency.schema.json",
        "market_data_ingest_downstream_handoff.schema.json",
    ):
        schema = json.loads((schema_dir / name).read_text(encoding="utf-8"))
        assert len(schema["oneOf"]) == 2
        v2_text = json.dumps(schema["oneOf"][1], sort_keys=True)
        assert "FORECASTEX" not in v2_text


def _assert_owned_objects_strict(node: object) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False
        for value in node.values():
            _assert_owned_objects_strict(value)
    elif isinstance(node, list):
        for value in node:
            _assert_owned_objects_strict(value)


def _resolve_local_schema_refs(schema_path: Path, node: object) -> None:
    if isinstance(node, dict):
        reference = node.get("$ref")
        if isinstance(reference, str):
            file_part, _, fragment = reference.partition("#")
            target_path = schema_path if not file_part else schema_path.parent / file_part
            target = json.loads(target_path.read_text(encoding="utf-8"))
            if fragment:
                for token in fragment.lstrip("/").split("/"):
                    target = target[token.replace("~1", "/").replace("~0", "~")]
            assert target is not None
        for value in node.values():
            _resolve_local_schema_refs(schema_path, value)
    elif isinstance(node, list):
        for value in node:
            _resolve_local_schema_refs(schema_path, value)


def _case_schema_and_serialization() -> None:
    from src.qtt.stage1_prediction_markets.market_data_ingest.adapter import (
        _pit_payload_matches_event_kind,
        _pit_typed_fields_payload,
    )
    from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import (
        policy as snapshot_policy,
    )
    from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import (
        validator as snapshot_validator,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITClockSetV3,
        PITEventKindV2,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
        deterministic_json,
    )

    schema_paths = tuple(
        Path(path)
        for path in sorted(_ALLOWED_SEMANTIC_PATHS)
        if path.endswith(".schema.json")
    )
    for path in schema_paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["additionalProperties"] is False
        _assert_owned_objects_strict(schema.get("$defs", {}))
        if "oneOf" in schema:
            _assert_owned_objects_strict(schema["oneOf"][1])
        _resolve_local_schema_refs(path, schema)
    fixture = json.loads(
        Path(
            "tests/fixtures/source_evidence/pr132_venue_market_data_ingest_adapters/"
            "canonical_market_data_ingest_events.v1.fixture.json"
        ).read_text(encoding="utf-8")
    )
    assert json.loads(json.dumps(fixture, sort_keys=True)) == fixture
    clocks = _clock()
    encoded = deterministic_json(clocks)
    decoded = json.loads(encoded)
    rebuilt = PITClockSetV3(
        **{
            name: (
                datetime.fromisoformat(value)
                if "_utc" in name and value is not None
                else value
            )
            for name, value in decoded.items()
        }
    )
    assert rebuilt == clocks
    with pytest.raises(ValueError):
        PITEventKindV2("UNKNOWN_EVENT_KIND")
    canonical_schema = json.loads(
        Path(
            "src/qtt/stage1_prediction_markets/market_data_ingest/"
            "canonical_market_data_ingest_event.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert "unknown_field" not in canonical_schema["properties"]
    canonical_v2_branch = canonical_schema["oneOf"][1]
    assert len(canonical_v2_branch["allOf"]) >= 20
    assert "$data" not in json.dumps(canonical_v2_branch, sort_keys=True)
    assert {
        condition["if"]["properties"]["profile_id"]["const"]
        for condition in canonical_v2_branch["allOf"]
        if "if" in condition
        and "profile_id" in condition["if"].get("properties", {})
        and "const" in condition["if"]["properties"]["profile_id"]
    } == set(_SELECTED_PROFILE_VALUES)
    handoff_schema = json.loads(
        Path(
            "src/qtt/stage1_prediction_markets/market_data_ingest/"
            "market_data_ingest_downstream_handoff.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert {
        condition["if"]["properties"]["profile_id"]["const"]
        for condition in handoff_schema["$defs"]["selectedContractV2"]["allOf"]
    } == set(_SELECTED_PROFILE_VALUES)
    orderbook_schema = json.loads(
        Path(
            "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/"
            "orderbook_snapshot.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert len(orderbook_schema["$defs"]["orderBookStateV2"]["allOf"]) == 5
    shared_envelope_fields = [
        "schema_version",
        "record_type",
        "created_by",
        "authority_class",
    ]
    snapshot_schema_dir = Path(
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot"
    )
    for schema_name in (
        "event_state_snapshot.schema.json",
        "orderbook_snapshot.schema.json",
        "snapshot_builder_binding.schema.json",
        "snapshot_downstream_handoff.schema.json",
    ):
        snapshot_schema = json.loads(
            (snapshot_schema_dir / schema_name).read_text(encoding="utf-8")
        )
        legacy_record_type = snapshot_schema["oneOf"][0]["properties"][
            "record_type"
        ]["const"]
        v2_record_type = snapshot_policy.PIT_V2_DISCRIMINATOR_BY_LEGACY_V1_RECORD_TYPE[
            legacy_record_type
        ][1]
        expected_common = (
            snapshot_policy.LEGACY_PR133_V1_REQUIRED_FIELDS_BY_RECORD_TYPE[
                legacy_record_type
            ]
            & snapshot_policy.PIT_V2_REQUIRED_FIELDS_BY_RECORD_TYPE[v2_record_type]
        )
        assert set(snapshot_schema["required"]) == expected_common
        assert set(shared_envelope_fields) <= expected_common
        assert set(shared_envelope_fields) < set(
            snapshot_schema["oneOf"][0]["required"]
        )

    def independent_ref_target(
        schema: Mapping[str, object],
        reference: object,
    ) -> Mapping[str, object]:
        assert isinstance(reference, str) and reference.startswith("#/")
        target: object = schema
        for raw_token in reference[2:].split("/"):
            token = raw_token.replace("~1", "/").replace("~0", "~")
            assert isinstance(target, dict) and token in target
            target = target[token]
        assert isinstance(target, dict)
        return target

    def independent_fragment_contract(
        schema: Mapping[str, object],
        fragment: Mapping[str, object],
        seen_refs: tuple[str, ...] = (),
    ) -> tuple[frozenset[str], dict[str, Mapping[str, object]]]:
        required: set[str] = set()
        properties: dict[str, Mapping[str, object]] = {}
        reference = fragment.get("$ref")
        if reference is not None:
            assert isinstance(reference, str) and reference not in seen_refs
            ref_required, ref_properties = independent_fragment_contract(
                schema,
                independent_ref_target(schema, reference),
                (*seen_refs, reference),
            )
            required.update(ref_required)
            properties.update(ref_properties)
        all_of = fragment.get("allOf", [])
        assert isinstance(all_of, list)
        for child in all_of:
            assert isinstance(child, dict)
            child_required, child_properties = independent_fragment_contract(
                schema,
                child,
                seen_refs,
            )
            required.update(child_required)
            properties.update(child_properties)
        raw_required = fragment.get("required", [])
        assert isinstance(raw_required, list)
        assert all(isinstance(field, str) and field for field in raw_required)
        assert len(raw_required) == len(set(raw_required))
        required.update(raw_required)
        raw_properties = fragment.get("properties", {})
        assert isinstance(raw_properties, dict)
        assert all(
            isinstance(field, str) and isinstance(field_schema, dict)
            for field, field_schema in raw_properties.items()
        )
        properties.update(raw_properties)
        return frozenset(required), properties

    def independent_branch_contracts(
        schema: Mapping[str, object],
    ) -> tuple[
        frozenset[str],
        dict[str, Mapping[str, object]],
        tuple[
            tuple[
                tuple[str, str],
                frozenset[str],
                dict[str, Mapping[str, object]],
            ],
            ...,
        ],
    ]:
        root_required, root_properties = independent_fragment_contract(schema, schema)
        branches = schema.get("oneOf", [])
        assert isinstance(branches, list)
        resolved = []
        for branch in branches:
            assert isinstance(branch, dict)
            branch_required, branch_properties = independent_fragment_contract(
                schema,
                branch,
            )
            effective_properties = dict(root_properties)
            effective_properties.update(branch_properties)
            discriminator = (
                effective_properties["schema_version"]["const"],
                effective_properties["record_type"]["const"],
            )
            assert all(isinstance(value, str) for value in discriminator)
            resolved.append(
                (
                    discriminator,
                    frozenset(root_required | branch_required),
                    effective_properties,
                )
            )
        return root_required, root_properties, tuple(resolved)

    def independent_minimal_record(
        required: frozenset[str],
        properties: Mapping[str, Mapping[str, object]],
    ) -> dict[str, object]:
        record: dict[str, object] = {}
        for field in required:
            field_schema = properties[field]
            if "const" in field_schema:
                value = field_schema["const"]
            elif field_schema.get("enum"):
                value = field_schema["enum"][0]
            elif field_schema.get("type") == "string":
                value = "X"
            elif field_schema.get("type") == "integer":
                value = 1
            elif field_schema.get("type") == "boolean":
                value = False
            elif field_schema.get("type") == "array":
                value = []
            elif field_schema.get("type") == "object":
                value = {}
            else:
                value = None
            record[field] = value
        return record

    def independent_accepting_discriminators(
        schema: Mapping[str, object],
        record: Mapping[str, object],
    ) -> tuple[tuple[str, str], ...]:
        root_required, root_properties, branches = independent_branch_contracts(schema)
        if not root_required.issubset(record) or not set(record).issubset(root_properties):
            return ()
        accepted = []
        for discriminator, required, properties in branches:
            if not required.issubset(record):
                continue
            valid = True
            for field, value in record.items():
                field_schema = properties[field]
                if "const" in field_schema and value != field_schema["const"]:
                    valid = False
                if "enum" in field_schema and value not in field_schema["enum"]:
                    valid = False
            if valid:
                accepted.append(discriminator)
        return tuple(accepted)

    schema_documents = {
        schema_name: json.loads((snapshot_schema_dir / schema_name).read_text(encoding="utf-8"))
        for schema_name in snapshot_validator.SCHEMA_FILES
    }
    legacy_required_counts = {
        "ORDERBOOK_EVENT_STATE_SNAPSHOT_INPUT_LOCK": 86,
        "ORDERBOOK_SNAPSHOT_RECORD": 97,
        "EVENT_STATE_SNAPSHOT_RECORD": 94,
        "ORDERBOOK_EVENT_STATE_SNAPSHOT_BUILDER_BINDING": 96,
        "ORDERBOOK_EVENT_STATE_SNAPSHOT_INTEGRITY_RECEIPT": 102,
        "ORDERBOOK_EVENT_STATE_SNAPSHOT_REJECTION": 85,
        "ORDERBOOK_EVENT_STATE_SNAPSHOT_DOWNSTREAM_HANDOFF": 108,
        "ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_RECORD": 80,
    }
    legacy_placeholder_fields = frozenset(
        {
            *snapshot_policy.QUANTUM_FORWARD_SNAPSHOT_METADATA_FIELDS,
            *snapshot_policy.QUANTUM_ZERO_AUTHORITY_FLAGS,
            *snapshot_policy.ATOMICROWS_PRE_BRIDGE_METADATA_FIELDS,
            *snapshot_policy.ATOMICROWS_ZERO_AUTHORITY_FLAGS,
        }
    )
    v1_only_count = 0
    union_count = 0
    for schema_name, schema in schema_documents.items():
        if "oneOf" not in schema:
            v1_only_count += 1
            required = frozenset(schema["required"])
            record_type = schema["properties"]["record_type"]["const"]
            assert schema["properties"]["schema_version"]["const"] == snapshot_policy.SCHEMA_VERSION
            assert len(required) == legacy_required_counts[record_type]
            assert snapshot_policy.LEGACY_PR133_V1_SHARED_REQUIRED_FIELDS <= required
            assert (
                required
                == snapshot_policy.LEGACY_PR133_V1_REQUIRED_FIELDS_BY_RECORD_TYPE[
                    record_type
                ]
            )
            continue

        union_count += 1
        root_required, _, branches = independent_branch_contracts(schema)
        assert len(branches) == 2
        assert len({discriminator for discriminator, _, _ in branches}) == 2
        v1_branch = next(
            branch
            for branch in branches
            if branch[0][0] == snapshot_policy.SCHEMA_VERSION
        )
        v2_discriminator = snapshot_policy.PIT_V2_DISCRIMINATOR_BY_LEGACY_V1_RECORD_TYPE[
            v1_branch[0][1]
        ]
        v2_branch = next(branch for branch in branches if branch[0] == v2_discriminator)
        assert {branch[0] for branch in branches} == {
            (snapshot_policy.SCHEMA_VERSION, v1_branch[0][1]),
            v2_discriminator,
        }
        expected_v1 = snapshot_policy.LEGACY_PR133_V1_REQUIRED_FIELDS_BY_RECORD_TYPE[
            v1_branch[0][1]
        ]
        expected_v2 = snapshot_policy.PIT_V2_REQUIRED_FIELDS_BY_RECORD_TYPE[
            v2_discriminator[1]
        ]
        expected_common = expected_v1 & expected_v2
        assert snapshot_policy.SCHEMA_COMMON_REQUIRED_FIELDS <= expected_common
        assert root_required == expected_common
        assert v1_branch[1] == expected_v1
        assert v2_branch[1] == expected_v2
        assert (
            v1_branch[1] - root_required
            == expected_v1 - expected_common
        )
        assert (
            v2_branch[1] - root_required
            == expected_v2 - expected_common
        )
        assert tuple(v2_branch[2]["profile_id"]["enum"]) == _SELECTED_PROFILE_VALUES
        assert "FORECASTEX_IBKR" not in v2_branch[2]["profile_id"]["enum"]

        minimal_v1 = independent_minimal_record(v1_branch[1], v1_branch[2])
        minimal_v2 = independent_minimal_record(v2_branch[1], v2_branch[2])
        assert independent_accepting_discriminators(schema, minimal_v1) == (v1_branch[0],)
        assert independent_accepting_discriminators(schema, minimal_v2) == (v2_branch[0],)
        assert not set(minimal_v2).intersection(legacy_placeholder_fields)
        for field in sorted(v1_branch[1]):
            missing = dict(minimal_v1)
            del missing[field]
            assert independent_accepting_discriminators(schema, missing) == ()
        for field in sorted(v2_branch[1]):
            missing = dict(minimal_v2)
            del missing[field]
            assert independent_accepting_discriminators(schema, missing) == ()
        unknown = dict(minimal_v2)
        unknown["unknown_field"] = "REJECT"
        assert independent_accepting_discriminators(schema, unknown) == ()

    assert v1_only_count == 4
    assert union_count == 4

    event_schema = schema_documents["event_state_snapshot.schema.json"]
    v2_branch_index = next(
        index
        for index, branch in enumerate(event_schema["oneOf"])
        if branch["properties"]["schema_version"]["const"]
        == "PIT_EVENT_STATE_SNAPSHOT_V2"
    )
    forecast_mutation = deepcopy(event_schema)
    forecast_mutation["properties"]["profile_id"]["enum"].append("FORECASTEX_IBKR")
    assert snapshot_validator._validate_schema_document(
        forecast_mutation,
        "forecast mutation",
    )
    moved_legacy_mutation = deepcopy(event_schema)
    moved_legacy_mutation["oneOf"][v2_branch_index]["required"].append(
        snapshot_policy.QUANTUM_FORWARD_SNAPSHOT_METADATA_FIELDS[0]
    )
    assert snapshot_validator._validate_schema_document(
        moved_legacy_mutation,
        "legacy field moved into V2",
    )
    root_mismatch = deepcopy(event_schema)
    root_mismatch["required"].append("state_id")
    assert snapshot_validator._validate_schema_document(root_mismatch, "root mismatch")
    branch_mismatch = deepcopy(event_schema)
    branch_mismatch["oneOf"][v2_branch_index]["required"].remove("state_id")
    assert snapshot_validator._validate_schema_document(
        branch_mismatch,
        "branch-local mismatch",
    )
    ambiguous = deepcopy(event_schema)
    ambiguous["oneOf"][v2_branch_index]["properties"]["schema_version"]["const"] = (
        snapshot_policy.SCHEMA_VERSION
    )
    ambiguous["oneOf"][v2_branch_index]["properties"]["record_type"]["const"] = (
        "EVENT_STATE_SNAPSHOT_RECORD"
    )
    assert snapshot_validator._validate_schema_document(
        ambiguous,
        "duplicate V1 discriminator",
    )
    assert snapshot_validator._schema_validation(Path(".")) == []
    historical_check = subprocess.run(
        (
            sys.executable,
            "-B",
            "tools/orderbook_event_state_snapshot_builder_validate.py",
            "--repo-root",
            ".",
            "--check-only",
        ),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert historical_check.returncode == 0, historical_check.stdout + historical_check.stderr
    assert "QTT_ORDERBOOK_AND_EVENT_STATE_SNAPSHOT_BUILDER_OK" in historical_check.stdout
    scalar_event_kinds = (
        PITEventKindV2.CATALOG,
        PITEventKindV2.LIFECYCLE,
        PITEventKindV2.BBO,
        PITEventKindV2.TRADE,
        PITEventKindV2.SETTLEMENT,
        PITEventKindV2.REFERENCE_PRICE,
        PITEventKindV2.HEARTBEAT,
        PITEventKindV2.SOURCE_STATUS,
    )
    typed_payloads = tuple(
        _pit_typed_fields_payload(event_kind, {"field": event_kind.value})
        for event_kind in scalar_event_kinds
    )
    assert len({type(payload) for payload in typed_payloads}) == len(
        scalar_event_kinds
    )
    assert all(
        _pit_payload_matches_event_kind(payload, event_kind)
        for payload, event_kind in zip(typed_payloads, scalar_event_kinds, strict=True)
    )
    assert all(
        json.loads(deterministic_json(payload))["event_kind"] == event_kind.value
        for payload, event_kind in zip(typed_payloads, scalar_event_kinds, strict=True)
    )
    mutable_source = {"nested": {"value": "ORIGINAL"}}
    immutable_payload = _pit_typed_fields_payload(
        PITEventKindV2.CATALOG,
        mutable_source,
    )
    mutable_source["nested"]["value"] = "MUTATED"
    assert dict(immutable_payload.fields)["nested"]["value"] == "ORIGINAL"
    typed_discriminator_branch = canonical_schema["$defs"]["payloadV2"]["oneOf"][4]
    assert {
        branch["properties"]["event_kind"]["const"]
        for branch in typed_discriminator_branch["oneOf"]
    } == {event_kind.value for event_kind in scalar_event_kinds}
    _expect_pit_error(
        lambda: replace(
            _build_contracts()[0],
            contract_version="UNRECOGNIZED_CONTRACT_VERSION",
        )
    )
    _expect_pit_error(
        lambda: replace(
            _build_contracts()[0],
            websocket_url="wss://not-the-frozen-selected-profile.example",
        )
    )
    _expect_pit_error(
        lambda: replace(
            _build_contracts()[0],
            admitted_event_kinds=tuple(PITEventKindV2),
        )
    )
    _expect_pit_error(
        lambda: _frame(
            "GEMINI_TITAN_DIRECT",
            {"instrumentSymbol": "X", "private_key": "UNTRUSTED"},
            suffix="PRIVATE",
            channel="prediction_markets.depth",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
        )
    )


def _case_clock_and_leakage() -> None:
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITReasonCodeV1,
        validate_pit_clock_set_v3,
    )

    admitted = validate_pit_clock_set_v3(
        _clock(),
        receipt_id="CLOCK-ADMISSION-1",
        decision_time_utc_or_none=_T0 + timedelta(seconds=5),
        requires_cross_clock_comparison=True,
        maximum_wall_clock_uncertainty_ns_or_none=2_000,
        required_process_epoch_id_or_none="PROCESS-EPOCH-1",
        required_monotonic_clock_id_or_none="PERF-COUNTER-NS-1",
    )
    assert admitted.admitted is True
    _expect_pit_error(
        lambda: validate_pit_clock_set_v3(
            _clock(),
            receipt_id="CLOCK-EPOCH-MISMATCH",
            required_process_epoch_id_or_none="PROCESS-EPOCH-2",
        ),
        PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
    )
    _expect_pit_error(
        lambda: validate_pit_clock_set_v3(
            _clock(wall_clock_uncertainty_ns=3_000),
            receipt_id="CLOCK-UNCERTAIN",
            requires_cross_clock_comparison=True,
            maximum_wall_clock_uncertainty_ns_or_none=2_000,
        ),
        PITReasonCodeV1.PIT_WALL_CLOCK_UNCERTAIN,
    )
    _expect_pit_error(
        lambda: validate_pit_clock_set_v3(
            _clock(),
            receipt_id="CLOCK-PUBLICATION-ABSENT",
            requires_provider_publication_time=True,
        ),
        PITReasonCodeV1.PIT_PROVIDER_PUBLICATION_TIME_UNAVAILABLE,
    )
    for field, requirement, reason in (
        (
            "revision_effective_time_utc_or_none",
            "requires_revision_at_decision",
            PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
        ),
        (
            "settlement_finality_time_utc_or_none",
            "requires_finality_at_decision",
            PITReasonCodeV1.PIT_LIFECYCLE_BLOCKED,
        ),
    ):
        kwargs = {field: _T0 + timedelta(seconds=8)}
        options = {requirement: True}
        _expect_pit_error(
            lambda kwargs=kwargs, options=options: validate_pit_clock_set_v3(
                _clock(**kwargs),
                receipt_id=f"CLOCK-LEAK::{field}",
                decision_time_utc_or_none=_T0 + timedelta(seconds=5),
                **options,
            ),
            reason,
        )
    _expect_pit_error(
        lambda: validate_pit_clock_set_v3(
            _clock(strategy_available_at_utc=_T0 + timedelta(seconds=7)),
            receipt_id="CLOCK-AVAILABILITY-CUTOFF",
            decision_time_utc_or_none=_T0 + timedelta(seconds=5),
        ),
        PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
    )


def _case_decimal_side_tick_and_book() -> None:
    from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.builder import (
        PITBookDeltaLevelV2,
        PITBookStateLevelV2,
        apply_pit_event_v2,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITEventKindV2,
        PITReasonCodeV1,
    )

    _expect_pit_error(
        lambda: _frame(
            "GEMINI_TITAN_DIRECT",
            {"instrumentSymbol": "X", "price": 0.5},
            suffix="FLOAT",
            channel="prediction_markets.depth",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
        )
    )
    _expect_pit_error(
        lambda: PITBookStateLevelV2(
            source_side="BID",
            canonical_side="BID",
            price_text="0.405",
            price=Decimal("0.405"),
            quantity_text="1.00",
            quantity=Decimal("1.00"),
            price_scale=3,
            quantity_scale=2,
            price_increment=Decimal("0.01"),
            price_origin=Decimal("0"),
            quantity_increment=Decimal("0.01"),
        )
    )
    _expect_pit_error(
        lambda: PITBookStateLevelV2(
            source_side="BID",
            canonical_side="BID",
            price_text="01.00",
            price=Decimal("1.00"),
            quantity_text="1",
            quantity=Decimal("1"),
            price_scale=2,
            quantity_scale=0,
            price_increment=Decimal("0.01"),
            price_origin=Decimal("0"),
            quantity_increment=None,
        )
    )
    signed = PITBookDeltaLevelV2(
        source_side="YES",
        canonical_side="YES_BID",
        price_text="0.40",
        price=Decimal("0.40"),
        quantity_delta_text="-1.00",
        quantity_delta=Decimal("-1.00"),
        price_scale=2,
        quantity_scale=2,
    )
    assert signed.quantity_delta < 0
    _expect_pit_error(
        lambda: PITBookDeltaLevelV2(
            source_side="YES",
            canonical_side="YES_BID",
            price_text="0.40",
            price=Decimal("0.40"),
            quantity_delta_text="-0.00",
            quantity_delta=Decimal("-0.00"),
            price_scale=2,
            quantity_scale=2,
        ),
        PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
    )
    _expect_pit_error(
        lambda: PITBookStateLevelV2(
            source_side="BID",
            canonical_side="BID",
            price_text="-0.00",
            price=Decimal("-0.00"),
            quantity_text="1.00",
            quantity=Decimal("1.00"),
            price_scale=2,
            quantity_scale=2,
            price_increment=Decimal("0.01"),
            price_origin=Decimal("0"),
            quantity_increment=Decimal("0.01"),
        ),
        PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
    )
    negative_zero_tree = _gemini_snapshot_tree()
    negative_zero_tree["bids"] = [["-0.00", "1.00"]]
    _expect_pit_error(
        lambda: _ingest(
            _frame(
                "GEMINI_TITAN_DIRECT",
                negative_zero_tree,
                suffix="NEGATIVE-ZERO-PRICE",
                channel="prediction_markets.depth",
                wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
            ),
            PITEventKindV2.BOOK_SNAPSHOT,
        ),
        PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
    )
    valid_snapshot = _ingest(
        _frame(
            "GEMINI_TITAN_DIRECT",
            _gemini_snapshot_tree(),
            suffix="DIRECT-STATE-BOUND",
            channel="prediction_markets.depth",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
        ),
        PITEventKindV2.BOOK_SNAPSHOT,
    )
    valid_state = apply_pit_event_v2(
        None, valid_snapshot, candidate_event_ordinal=1
    ).post_state
    out_of_range_level = replace(
        valid_state.levels[0],
        price_text="1.40",
        price=Decimal("1.40"),
        price_scale=2,
    )
    _expect_pit_error(
        lambda: replace(
            valid_state,
            levels=(out_of_range_level, *valid_state.levels[1:]),
        ),
        PITReasonCodeV1.PIT_TICK_GRID_INVALID,
    )


def _gemini_snapshot_tree(sequence: int = 1) -> dict[str, object]:
    return {
        "instrumentSymbol": "GEMINI-EVENT-1",
        "marketId": "GEMINI-MARKET-1",
        "U": sequence,
        "u": sequence,
        "bids": [["0.40", "2.00"]],
        "asks": [["0.60", "3.00"]],
    }


def _case_gemini_algorithm() -> None:
    from src.qtt.stage1_prediction_markets.market_data_ingest.validator import (
        PITMarketDataIngestDispatcherV2,
    )
    from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.builder import (
        apply_pit_event_v2,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITAvailabilityStateV2,
        PITEventDispositionV1,
        PITEventKindV2,
        PITReasonCodeV1,
        PITTransportStateV1,
    )

    dispatcher = PITMarketDataIngestDispatcherV2(_build_contracts())
    snapshot = _ingest(
        _frame(
            "GEMINI_TITAN_DIRECT",
            _gemini_snapshot_tree(),
            suffix="SNAPSHOT",
            channel="prediction_markets.depth",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
        ),
        PITEventKindV2.BOOK_SNAPSHOT,
        dispatcher=dispatcher,
    )
    anchored = apply_pit_event_v2(None, snapshot, candidate_event_ordinal=1)
    assert anchored.event_disposition is PITEventDispositionV1.COMMITTED
    assert len(anchored.post_state.levels) == 2
    duplicate = apply_pit_event_v2(
        anchored.post_state, snapshot, candidate_event_ordinal=2
    )
    assert duplicate.event_disposition is PITEventDispositionV1.DUPLICATE_IGNORED
    conflicting_tree = _gemini_snapshot_tree()
    conflicting_tree["bids"] = [["0.40", "9.00"]]
    conflicting = _ingest(
        _frame(
            "GEMINI_TITAN_DIRECT",
            conflicting_tree,
            suffix="CONFLICT",
            channel="prediction_markets.depth",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
        ),
        PITEventKindV2.BOOK_SNAPSHOT,
    )
    conflict_result = apply_pit_event_v2(
        anchored.post_state, conflicting, candidate_event_ordinal=2
    )
    assert conflict_result.failure_reason_or_none is PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE
    gap_tree = {
        **_gemini_snapshot_tree(3),
        "bids": [["0.40", "1.00"]],
        "asks": [],
    }
    gap = _ingest(
        _frame(
            "GEMINI_TITAN_DIRECT",
            gap_tree,
            suffix="GAP",
            channel="prediction_markets.depth",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
        ),
        PITEventKindV2.BOOK_DELTA,
    )
    gap_result = apply_pit_event_v2(anchored.post_state, gap, candidate_event_ordinal=2)
    assert gap_result.failure_reason_or_none is PITReasonCodeV1.PIT_SEQUENCE_GAP
    covering_tree = {
        **_gemini_snapshot_tree(),
        "U": 1,
        "u": 2,
        "bids": [["0.40", "0"]],
        "asks": [],
    }
    covering = _ingest(
        _frame(
            "GEMINI_TITAN_DIRECT",
            covering_tree,
            suffix="COVERING",
            channel="prediction_markets.depth",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
        ),
        PITEventKindV2.BOOK_DELTA,
    )
    assert apply_pit_event_v2(
        gap_result.post_state,
        covering,
        candidate_event_ordinal=2,
    ).failure_reason_or_none is PITReasonCodeV1.PIT_ANCHOR_REQUIRED
    updated = apply_pit_event_v2(
        anchored.post_state, covering, candidate_event_ordinal=2
    )
    assert all(level.canonical_side != "BID" for level in updated.post_state.levels)
    timeout = apply_pit_event_v2(
        None,
        snapshot,
        candidate_event_ordinal=1,
        transport_state=PITTransportStateV1.HEARTBEAT_OVERDUE,
    )
    assert timeout.post_state.state_vector.availability_state is PITAvailabilityStateV2.STALE
    new_epoch_delta = replace(gap, connection_epoch="EPOCH-2")
    recovery_required = apply_pit_event_v2(
        anchored.post_state, new_epoch_delta, candidate_event_ordinal=2
    )
    assert recovery_required.failure_reason_or_none is PITReasonCodeV1.PIT_ANCHOR_REQUIRED
    new_epoch_snapshot = replace(snapshot, connection_epoch="EPOCH-2", event_record_id="NEW-EPOCH-ANCHOR")
    recovered = apply_pit_event_v2(
        anchored.post_state, new_epoch_snapshot, candidate_event_ordinal=2
    )
    assert recovered.post_state.connection_epoch == "EPOCH-2"
    same_epoch_anchor = _ingest(
        _frame(
            "GEMINI_TITAN_DIRECT",
            _gemini_snapshot_tree(2),
            suffix="SAME-EPOCH-ANCHOR",
            channel="prediction_markets.depth",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
        ),
        PITEventKindV2.BOOK_SNAPSHOT,
    )
    assert apply_pit_event_v2(
        anchored.post_state,
        same_epoch_anchor,
        candidate_event_ordinal=2,
    ).failure_reason_or_none is PITReasonCodeV1.PIT_ANCHOR_REQUIRED
    assert apply_pit_event_v2(
        gap_result.post_state,
        same_epoch_anchor,
        candidate_event_ordinal=2,
    ).failure_reason_or_none is PITReasonCodeV1.PIT_ANCHOR_REQUIRED
    trade_tree = {
        "instrumentSymbol": "GEMINI-EVENT-1",
        "marketId": "GEMINI-MARKET-1",
        "tradeId": "GEMINI-TRADE-1",
        "price": "0.50",
        "quantity": "1.00",
    }
    trade = _ingest(
        _frame(
            "GEMINI_TITAN_DIRECT",
            trade_tree,
            suffix="TRADE",
            channel="prediction_markets.trades",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
        ),
        PITEventKindV2.TRADE,
    )
    trade_transition = apply_pit_event_v2(
        anchored.post_state,
        trade,
        candidate_event_ordinal=2,
    )
    assert trade_transition.event_disposition is PITEventDispositionV1.COMMITTED
    assert trade_transition.post_state.levels == anchored.post_state.levels
    scalar_before_anchor = apply_pit_event_v2(
        None,
        trade,
        candidate_event_ordinal=1,
    )
    anchored_after_scalar = apply_pit_event_v2(
        scalar_before_anchor.post_state,
        snapshot,
        candidate_event_ordinal=2,
    )
    assert anchored_after_scalar.event_disposition is PITEventDispositionV1.COMMITTED
    assert apply_pit_event_v2(
        trade_transition.post_state,
        trade,
        candidate_event_ordinal=3,
    ).event_disposition is PITEventDispositionV1.DUPLICATE_IGNORED
    _expect_pit_error(
        lambda: _ingest(
            _frame(
                "GEMINI_TITAN_DIRECT",
                {key: value for key, value in trade_tree.items() if key != "tradeId"},
                suffix="TRADE-NO-ID",
                channel="prediction_markets.trades",
                wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
            ),
            PITEventKindV2.TRADE,
        ),
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    )
    _expect_pit_error(
        lambda: _ingest(
            _frame(
                "GEMINI_TITAN_DIRECT",
                _gemini_snapshot_tree(),
                suffix="WRONG-CHANNEL",
                channel="prediction_markets.bookTicker",
                wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
            ),
            PITEventKindV2.BOOK_SNAPSHOT,
        ),
        PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
    )
    nanosecond_tree = _gemini_snapshot_tree()
    nanosecond_tree["E"] = 1_000_000_001
    _expect_pit_error(
        lambda: _ingest(
            _frame(
                "GEMINI_TITAN_DIRECT",
                nanosecond_tree,
                suffix="UNREPRESENTABLE-NANOSECOND",
                channel="prediction_markets.depth",
                wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
            ),
            PITEventKindV2.BOOK_SNAPSHOT,
        ),
        PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
    )


def _polymarket_tree(*, bid_quantity: str = "2.00", include_bid: bool = True) -> dict[str, object]:
    return {
        "marketId": "POLY-MARKET-1",
        "marketSlug": "poly-market-1",
        "state": "OPEN",
        "marketSides": [
            {"sideId": "SIDE-A", "label": "ALPHA"},
            {"sideId": "SIDE-B", "label": "BETA"},
        ],
        "orderPriceMinTickSize": "0.01",
        "bids": [["0.40", bid_quantity]] if include_bid else [],
        "offers": [["0.60", "3.00"]],
    }


def _case_polymarket_retail_algorithm() -> None:
    from src.qtt.stage1_prediction_markets.market_data_ingest import policy
    from src.qtt.stage1_prediction_markets.market_data_ingest.adapter import (
        build_pit_read_requests_v2,
    )
    from src.qtt.stage1_prediction_markets.market_data_ingest.validator import (
        PITMarketDataIngestDispatcherV2,
    )
    from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.builder import (
        apply_pit_event_v2,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITDepthClassV2,
        PITEventKindV2,
        PITReasonCodeV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
        Stage1VenueProfileIdV1,
    )

    dispatcher = PITMarketDataIngestDispatcherV2(_build_contracts())
    primary = _ingest(
        _frame(
            "POLYMARKET_US_RETAIL_DIRECT",
            _polymarket_tree(),
            suffix="PRIMARY",
            channel="markets",
            wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
            capture_session_id="POLY-PRIMARY",
        ),
        PITEventKindV2.BOOK_REPLACEMENT,
        dispatcher=dispatcher,
    )
    assert primary.provider_sequence_end_or_none is None
    assert primary.depth_class is PITDepthClassV2.PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME
    assert primary.payload.source_lifecycle_state == "OPEN"
    assert len(json.loads(primary.payload.market_sides_json)) == 2
    assert primary.payload.order_price_min_tick_size_text == "0.01"
    for missing_field in ("state", "marketSides", "orderPriceMinTickSize"):
        malformed_tree = _polymarket_tree()
        malformed_tree.pop(missing_field)
        _expect_pit_error(
            lambda malformed_tree=malformed_tree, missing_field=missing_field: _ingest(
                _frame(
                    "POLYMARKET_US_RETAIL_DIRECT",
                    malformed_tree,
                    suffix=f"MISSING-{missing_field}",
                    channel="markets",
                    wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
                ),
                PITEventKindV2.BOOK_REPLACEMENT,
            ),
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
        )
    wrong_state_tree = _polymarket_tree()
    wrong_state_tree["state"] = 1
    _expect_pit_error(
        lambda: _ingest(
            _frame(
                "POLYMARKET_US_RETAIL_DIRECT",
                wrong_state_tree,
                suffix="WRONG-STATE-DIALECT",
                channel="markets",
                wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
            ),
            PITEventKindV2.BOOK_REPLACEMENT,
        ),
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    )
    legacy_outcomes_tree = _polymarket_tree()
    legacy_outcomes_tree["outcomes"] = ["YES", "NO"]
    _expect_pit_error(
        lambda: _ingest(
            _frame(
                "POLYMARKET_US_RETAIL_DIRECT",
                legacy_outcomes_tree,
                suffix="REMOVED-OUTCOMES",
                channel="markets",
                wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
            ),
            PITEventKindV2.BOOK_REPLACEMENT,
        ),
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    )
    wrong_tick_tree = _polymarket_tree()
    wrong_tick_tree["orderPriceMinTickSize"] = "0.005"
    _expect_pit_error(
        lambda: _ingest(
            _frame(
                "POLYMARKET_US_RETAIL_DIRECT",
                wrong_tick_tree,
                suffix="WRONG-TICK-BINDING",
                channel="markets",
                wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
            ),
            PITEventKindV2.BOOK_REPLACEMENT,
        ),
        PITReasonCodeV1.PIT_TICK_GRID_INVALID,
    )
    state = apply_pit_event_v2(None, primary, candidate_event_ordinal=1).post_state
    replacement = _ingest(
        _frame(
            "POLYMARKET_US_RETAIL_DIRECT",
            _polymarket_tree(include_bid=False),
            suffix="REPLACEMENT",
            channel="markets",
            wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
            capture_session_id="POLY-PRIMARY",
        ),
        PITEventKindV2.BOOK_REPLACEMENT,
        dispatcher=dispatcher,
    )
    replaced = apply_pit_event_v2(state, replacement, candidate_event_ordinal=2)
    assert all(level.canonical_side != "BID" for level in replaced.post_state.levels)
    fallback_dispatcher = PITMarketDataIngestDispatcherV2(_build_contracts())
    fallback_tree = {
        "market_id": "POLY-MARKET-2",
        "market_slug": "poly-market-2",
        "state": 1,
        "market_sides": [
            {"side_id": "SIDE-A", "label": "ALPHA"},
            {"side_id": "SIDE-B", "label": "BETA"},
        ],
        "order_price_min_tick_size": "0.01",
        "bids": [["0.40", "1.00"]],
        "offers": [["0.60", "1.00"]],
    }
    fallback = _frame(
        "POLYMARKET_US_RETAIL_DIRECT",
        fallback_tree,
        suffix="FALLBACK",
        channel="markets",
        wire_dialect="POLYMARKET_RETAIL_SNAKE_NUMERIC_V1",
        capture_session_id="POLY-FALLBACK",
    )
    _ingest(
        fallback,
        PITEventKindV2.BOOK_REPLACEMENT,
        dispatcher=fallback_dispatcher,
        explicit_pre_data_subscription_error=True,
    )
    mixed = _frame(
        "POLYMARKET_US_RETAIL_DIRECT",
        _polymarket_tree(),
        suffix="MIXED",
        channel="markets",
        wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
        capture_session_id="POLY-FALLBACK",
    )
    _expect_pit_error(
        lambda: _ingest(
            mixed,
            PITEventKindV2.BOOK_REPLACEMENT,
            dispatcher=fallback_dispatcher,
        ),
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    )
    identifiers = tuple(f"market-{index}" for index in range(101))
    _expect_pit_error(
        lambda: build_pit_read_requests_v2(
            _build_contracts(),
            market_identifiers_by_profile={
                Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: identifiers
            },
        ),
        PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
    )
    contract = _contract_by_value("POLYMARKET_US_RETAIL_DIRECT")
    assert contract.heartbeat_model.startswith("ADAPTIVE_MONOTONIC")
    assert {
        "PROVIDER_NUMERIC_SEQUENCE",
        "WEBSOCKET_COMPLETE_PROVIDER_DEPTH",
        "EXACT_CHANGE_LEVEL_HISTORY",
    } <= set(contract.unavailable_capabilities)
    parity_dispatcher = PITMarketDataIngestDispatcherV2(_build_contracts())
    parity_ws_tree = _polymarket_tree()
    parity_ws_tree["bids"] = [["0.40", "2.00"], ["0.30", "4.00"]]
    parity_ws_tree["offers"] = [["0.60", "3.00"], ["0.70", "5.00"]]
    parity_ws = _ingest(
        _frame(
            "POLYMARKET_US_RETAIL_DIRECT",
            parity_ws_tree,
            suffix="PARITY-WS",
            channel="markets",
            wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
            capture_session_id="POLY-PARITY",
        ),
        PITEventKindV2.BOOK_REPLACEMENT,
        dispatcher=parity_dispatcher,
    )
    parity_ws_state = apply_pit_event_v2(
        None, parity_ws, candidate_event_ordinal=1
    ).post_state
    rest_tree = _polymarket_tree()
    rest_tree["bids"] = [
        ["0.40", "2.00"],
        ["0.30", "4.00"],
        ["0.20", "6.00"],
    ]
    rest_tree["offers"] = [
        ["0.60", "3.00"],
        ["0.70", "5.00"],
        ["0.80", "7.00"],
    ]
    rest_snapshot = _ingest(
        _frame(
            "POLYMARKET_US_RETAIL_DIRECT",
            rest_tree,
            suffix="PARITY-REST",
            channel="REST_BOOK",
            wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
            capture_session_id="POLY-PARITY",
        ),
        PITEventKindV2.BOOK_REPLACEMENT,
        dispatcher=parity_dispatcher,
    )
    parity_state = apply_pit_event_v2(
        parity_ws_state,
        rest_snapshot,
        candidate_event_ordinal=2,
    )
    assert parity_state.event_disposition.value == "COMMITTED"
    assert parity_state.post_state.state_vector.depth_class is (
        PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT
    )
    divergent_tree = deepcopy(parity_ws_tree)
    divergent_tree["bids"][1][1] = "9.00"
    divergent_ws = _ingest(
        _frame(
            "POLYMARKET_US_RETAIL_DIRECT",
            divergent_tree,
            suffix="PARITY-DIVERGENCE",
            channel="markets",
            wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
            capture_session_id="POLY-PARITY",
        ),
        PITEventKindV2.BOOK_REPLACEMENT,
        dispatcher=parity_dispatcher,
    )
    parity_failure = apply_pit_event_v2(
        parity_state.post_state,
        divergent_ws,
        candidate_event_ordinal=3,
    )
    assert parity_failure.failure_reason_or_none is (
        PITReasonCodeV1.PIT_CURRENT_STATE_PARITY_FAILED
    )
    empty_published_tree = _polymarket_tree(include_bid=False)
    empty_published_tree["offers"] = []
    empty_published = _ingest(
        _frame(
            "POLYMARKET_US_RETAIL_DIRECT",
            empty_published_tree,
            suffix="PARITY-EMPTY-PUBLISHED",
            channel="markets",
            wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
            capture_session_id="POLY-PARITY",
        ),
        PITEventKindV2.BOOK_REPLACEMENT,
        dispatcher=parity_dispatcher,
    )
    assert apply_pit_event_v2(
        parity_state.post_state,
        empty_published,
        candidate_event_ordinal=3,
    ).failure_reason_or_none is PITReasonCodeV1.PIT_CURRENT_STATE_PARITY_FAILED
    hidden_top_tree = _polymarket_tree()
    hidden_top_tree["bids"] = [["0.30", "4.00"]]
    hidden_top_tree["offers"] = [["0.70", "5.00"]]
    hidden_top = _ingest(
        _frame(
            "POLYMARKET_US_RETAIL_DIRECT",
            hidden_top_tree,
            suffix="PARITY-HIDDEN-TOP",
            channel="markets",
            wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
            capture_session_id="POLY-PARITY",
        ),
        PITEventKindV2.BOOK_REPLACEMENT,
        dispatcher=parity_dispatcher,
    )
    assert apply_pit_event_v2(
        parity_state.post_state,
        hidden_top,
        candidate_event_ordinal=3,
    ).failure_reason_or_none is PITReasonCodeV1.PIT_CURRENT_STATE_PARITY_FAILED
    assert apply_pit_event_v2(
        parity_failure.post_state,
        hidden_top,
        candidate_event_ordinal=3,
    ).failure_reason_or_none is PITReasonCodeV1.PIT_ANCHOR_REQUIRED
    reconnected_replacement = replace(
        hidden_top,
        event_record_id="POLY-PARITY-RECONNECTED",
        connection_epoch="EPOCH-2",
    )
    assert apply_pit_event_v2(
        parity_failure.post_state,
        reconnected_replacement,
        candidate_event_ordinal=3,
    ).event_disposition.value == "COMMITTED"
    _expect_pit_error(
        lambda: _ingest(
            _frame(
                "POLYMARKET_US_RETAIL_DIRECT",
                fallback_tree,
                suffix="PRIMARY-WITH-SNAKE-FIELDS",
                channel="markets",
                wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
                capture_session_id="POLY-WRONG-FIELDS",
            ),
            PITEventKindV2.BOOK_REPLACEMENT,
            dispatcher=PITMarketDataIngestDispatcherV2(_build_contracts()),
        ),
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    )
    envelope = policy.PIT_SAFETY_SEED_AND_CALIBRATION_ENVELOPE_V2
    assert envelope._polymarket_heartbeat_deadline_seconds(()) == Decimal("30")
    assert envelope._polymarket_heartbeat_deadline_seconds(
        tuple(Decimal(value) for value in ("1", "2", "3", "4", "5"))
    ) == Decimal("15")
    assert envelope._polymarket_heartbeat_deadline_seconds(
        (Decimal("50"),) * 5
    ) == Decimal("120")
    assert envelope.backoff_upper_seconds(
        base_seconds=Decimal("1"),
        cap_seconds=Decimal("30"),
        consecutive_failure_index=3,
    ) == Decimal("8")
    assert envelope._full_jitter_backoff_seconds(
        base_seconds=Decimal("1"),
        cap_seconds=Decimal("30"),
        consecutive_failure_index=3,
        uniform_sampler=lambda lower, upper: (lower + upper) / Decimal(2),
    ) == Decimal("4")
    heartbeat = _ingest(
        _frame(
            "POLYMARKET_US_RETAIL_DIRECT",
            {"type": "heartbeat"},
            suffix="HEARTBEAT",
            channel="markets",
            wire_dialect="POLYMARKET_RETAIL_CAMEL_STRING_V1",
            capture_session_id="POLY-HEARTBEAT",
        ),
        PITEventKindV2.HEARTBEAT,
        dispatcher=PITMarketDataIngestDispatcherV2(_build_contracts()),
    )
    heartbeat_transition = apply_pit_event_v2(
        None,
        heartbeat,
        candidate_event_ordinal=1,
    )
    assert heartbeat_transition.event_disposition.value == "COMMITTED"
    assert not heartbeat_transition.post_state.levels


def _kalshi_snapshot_tree(sequence: int = 1) -> dict[str, object]:
    return {
        "type": "orderbook_snapshot",
        "sid": "SID-1",
        "seq": sequence,
        "msg": {
            "market_ticker": "KALSHI-MARKET-1",
            "yes_dollars": [["0.40", "2.00"]],
            "no_dollars": [["0.50", "3.00"]],
        },
    }


def _kalshi_delta_tree(sequence: int, delta: str = "-1.00") -> dict[str, object]:
    return {
        "type": "orderbook_delta",
        "sid": "SID-1",
        "seq": sequence,
        "msg": {
            "market_ticker": "KALSHI-MARKET-1",
            "side": "YES",
            "price_dollars": "0.40",
            "delta_fp": delta,
        },
    }


def _case_kalshi_algorithm() -> None:
    from src.qtt.stage1_prediction_markets.market_data_ingest import policy
    from src.qtt.stage1_prediction_markets.market_data_ingest.adapter import (
        build_pit_read_requests_v2,
    )
    from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.builder import (
        apply_pit_event_v2,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITEventDispositionV1,
        PITEventKindV2,
        PITReasonCodeV1,
    )

    snapshot = _ingest(
        _frame(
            "KALSHI_US_DCM_DIRECT",
            _kalshi_snapshot_tree(),
            suffix="SNAPSHOT",
            channel="orderbook_delta",
            wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
            capture_session_id="KALSHI-ALGORITHM",
        ),
        PITEventKindV2.BOOK_SNAPSHOT,
    )
    anchored = apply_pit_event_v2(None, snapshot, candidate_event_ordinal=1)
    delta = _ingest(
        _frame(
            "KALSHI_US_DCM_DIRECT",
            _kalshi_delta_tree(2),
            suffix="DELTA-2",
            channel="orderbook_delta",
            wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
            capture_session_id="KALSHI-ALGORITHM",
        ),
        PITEventKindV2.BOOK_DELTA,
    )
    advanced = apply_pit_event_v2(
        anchored.post_state, delta, candidate_event_ordinal=2
    )
    assert advanced.event_disposition is PITEventDispositionV1.COMMITTED
    yes_level = next(
        level for level in advanced.post_state.levels if level.canonical_side == "YES_BID"
    )
    assert yes_level.quantity == Decimal("1.00")
    duplicate = apply_pit_event_v2(
        advanced.post_state, delta, candidate_event_ordinal=3
    )
    assert duplicate.event_disposition is PITEventDispositionV1.DUPLICATE_IGNORED
    conflicting = replace(delta, payload=replace(delta.payload, deltas=(replace(delta.payload.deltas[0], quantity_delta_text="-0.50", quantity_delta=Decimal("-0.50"), quantity_scale=2),)))
    corrupted = apply_pit_event_v2(
        advanced.post_state, conflicting, candidate_event_ordinal=3
    )
    assert corrupted.failure_reason_or_none is PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE
    gap = _ingest(
        _frame(
            "KALSHI_US_DCM_DIRECT",
            _kalshi_delta_tree(4),
            suffix="GAP-4",
            channel="orderbook_delta",
            wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
            capture_session_id="KALSHI-ALGORITHM",
        ),
        PITEventKindV2.BOOK_DELTA,
    )
    gap_result = apply_pit_event_v2(
        advanced.post_state, gap, candidate_event_ordinal=3
    )
    assert gap_result.failure_reason_or_none is PITReasonCodeV1.PIT_SEQUENCE_GAP
    sequential_after_gap = _ingest(
        _frame(
            "KALSHI_US_DCM_DIRECT",
            _kalshi_delta_tree(3),
            suffix="SEQUENTIAL-AFTER-GAP",
            channel="orderbook_delta",
            wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
            capture_session_id="KALSHI-ALGORITHM",
        ),
        PITEventKindV2.BOOK_DELTA,
    )
    assert apply_pit_event_v2(
        gap_result.post_state,
        sequential_after_gap,
        candidate_event_ordinal=3,
    ).failure_reason_or_none is PITReasonCodeV1.PIT_ANCHOR_REQUIRED
    crossed_tree = _kalshi_snapshot_tree()
    crossed_tree["msg"] = {
        "market_ticker": "KALSHI-MARKET-1",
        "yes_dollars": [["0.60", "1.00"]],
        "no_dollars": [["0.50", "1.00"]],
    }
    _expect_pit_error(
        lambda: _ingest(
            _frame(
                "KALSHI_US_DCM_DIRECT",
                crossed_tree,
                suffix="CROSSED",
                channel="orderbook_delta",
                wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
                capture_session_id="KALSHI-CROSSED",
            ),
            PITEventKindV2.BOOK_SNAPSHOT,
        ),
        PITReasonCodeV1.PIT_BOOK_CROSSED_INVALID,
    )
    recovered_snapshot = _ingest(
        _frame(
            "KALSHI_US_DCM_DIRECT",
            _kalshi_snapshot_tree(7),
            suffix="GET-SNAPSHOT-RECOVERY",
            channel="orderbook_delta",
            wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
            capture_session_id="KALSHI-ALGORITHM",
        ),
        PITEventKindV2.BOOK_SNAPSHOT,
    )
    recovered = apply_pit_event_v2(
        gap_result.post_state,
        recovered_snapshot,
        candidate_event_ordinal=3,
    )
    assert recovered.event_disposition is PITEventDispositionV1.COMMITTED
    assert recovered.post_state.last_provider_sequence_end_or_none == 7
    wrong_sid_tree = _kalshi_snapshot_tree(8)
    wrong_sid_tree["sid"] = "SID-2"
    wrong_sid = _ingest(
        _frame(
            "KALSHI_US_DCM_DIRECT",
            wrong_sid_tree,
            suffix="WRONG-SID-RECOVERY",
            channel="orderbook_delta",
            wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
            capture_session_id="KALSHI-ALGORITHM",
        ),
        PITEventKindV2.BOOK_SNAPSHOT,
    )
    assert apply_pit_event_v2(
        recovered.post_state,
        wrong_sid,
        candidate_event_ordinal=4,
    ).failure_reason_or_none is PITReasonCodeV1.PIT_ANCHOR_REQUIRED
    lower_side_tree = _kalshi_delta_tree(8)
    lower_side_tree["msg"] = {**lower_side_tree["msg"], "side": "yes"}
    _expect_pit_error(
        lambda: _ingest(
            _frame(
                "KALSHI_US_DCM_DIRECT",
                lower_side_tree,
                suffix="LOWER-SIDE",
                channel="orderbook_delta",
                wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
                capture_session_id="KALSHI-ALGORITHM",
            ),
            PITEventKindV2.BOOK_DELTA,
        ),
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    )
    removed_alias_tree = _kalshi_snapshot_tree()
    removed_alias_tree["msg"] = {
        "market_ticker": "KALSHI-MARKET-1",
        "yes": [[40, 2]],
        "no": [[50, 3]],
    }
    _expect_pit_error(
        lambda: _ingest(
            _frame(
                "KALSHI_US_DCM_DIRECT",
                removed_alias_tree,
                suffix="REMOVED-CENT-ALIASES",
                channel="orderbook_delta",
                wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
            ),
            PITEventKindV2.BOOK_SNAPSHOT,
        ),
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    )
    wrong_type_tree = _kalshi_delta_tree(8)
    wrong_type_tree["type"] = "orderbook_snapshot"
    _expect_pit_error(
        lambda: _ingest(
            _frame(
                "KALSHI_US_DCM_DIRECT",
                wrong_type_tree,
                suffix="WRONG-MESSAGE-TYPE",
                channel="orderbook_delta",
                wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
            ),
            PITEventKindV2.BOOK_DELTA,
        ),
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    )
    trade = _ingest(
        _frame(
            "KALSHI_US_DCM_DIRECT",
            {
                "msg": {
                    "market_ticker": "KALSHI-MARKET-1",
                    "trade_id": "KALSHI-TRADE-1",
                    "price_dollars": "0.50",
                    "count_fp": "1.00",
                }
            },
            suffix="LIVE-TRADE",
            channel="trade",
            wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
            capture_session_id="KALSHI-ALGORITHM",
        ),
        PITEventKindV2.TRADE,
    )
    trade_transition = apply_pit_event_v2(
        recovered.post_state,
        trade,
        candidate_event_ordinal=4,
    )
    assert trade_transition.event_disposition is PITEventDispositionV1.COMMITTED
    scalar_before_anchor = apply_pit_event_v2(
        None,
        trade,
        candidate_event_ordinal=1,
    )
    anchored_after_scalar = apply_pit_event_v2(
        scalar_before_anchor.post_state,
        snapshot,
        candidate_event_ordinal=2,
    )
    assert anchored_after_scalar.event_disposition is PITEventDispositionV1.COMMITTED
    heartbeat = _ingest(
        _frame(
            "KALSHI_US_DCM_DIRECT",
            {"type": "ping", "id": "PING-1"},
            suffix="SERVER-PING",
            channel="server_ping",
            wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
            capture_session_id="KALSHI-ALGORITHM",
        ),
        PITEventKindV2.HEARTBEAT,
    )
    assert apply_pit_event_v2(
        None,
        heartbeat,
        candidate_event_ordinal=1,
    ).event_disposition is PITEventDispositionV1.COMMITTED
    source_status = _ingest(
        _frame(
            "KALSHI_US_DCM_DIRECT",
            {"read_tier": "BASIC", "read_capacity": "20"},
            suffix="ACCOUNT-LIMITS",
            channel="/portfolio/account_limits",
            wire_dialect="KALSHI_TRADE_API_WS_V2_FIXED_POINT",
            capture_session_id="KALSHI-ALGORITHM",
        ),
        PITEventKindV2.SOURCE_STATUS,
    )
    assert source_status.instrument_id == "KALSHI_US_DCM_DIRECT::VENUE"
    requests = build_pit_read_requests_v2(_build_contracts())
    kalshi = [request for request in requests if request.profile_id.value == "KALSHI_US_DCM_DIRECT"]
    assert any(
        ("use_yes_price", True) in request.query_or_subscription_payload
        for request in kalshi
    )
    recovery_request = next(
        request
        for request in kalshi
        if request.read_action is policy.PITReadActionV1.WEBSOCKET_RECOVERY
    )
    assert dict(recovery_request.query_or_subscription_payload)["command"] == "get_snapshot"
    heartbeat_request = next(
        request
        for request in kalshi
        if request.read_action is policy.PITReadActionV1.WEBSOCKET_PONG
    )
    assert dict(heartbeat_request.query_or_subscription_payload) == {
        "command": "pong",
        "reply_to": "server_ping",
    }
    historical = next(
        request for request in kalshi if request.path_or_channel == "/historical/trades"
    )
    assert historical.credential_alias_required is False
    assert dict(historical.query_or_subscription_payload) == {
        "provider_cutoff_required": True,
        "provider_cursor_required": True,
    }
    live_trade = next(
        request
        for request in kalshi
        if request.path_or_channel == "trade"
    )
    assert live_trade.credential_alias_required is True
    account_limit = next(
        request for request in kalshi if request.path_or_channel == "/portfolio/account_limits"
    )
    assert account_limit.credential_alias_required is True
    contract = _contract_by_value("KALSHI_US_DCM_DIRECT")
    assert contract.recovery_model.startswith("get_snapshot")
    assert "TWO_MISSES_PLUS_5_SECONDS" in contract.heartbeat_model


def _case_freshness_and_availability() -> None:
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.freshness import (
        PITFreshnessObservationV2,
        PITFreshnessRequirementV2,
        evaluate_pit_freshness_v2,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITAnchorStateV1,
        PITContinuityStateV3,
        PITDepthClassV2,
        PITInputAvailabilityV2,
        PITIntegrityStateV1,
        PITTransportStateV1,
    )

    base_requirement = PITFreshnessRequirementV2(
        capability_key="FRESHNESS-MATRIX",
        maximum_provider_event_age_or_none=timedelta(seconds=60),
        maximum_local_receive_age=timedelta(seconds=60),
        maximum_durable_commit_age=timedelta(seconds=60),
        maximum_strategy_availability_age=timedelta(seconds=60),
        economic_ttl=timedelta(seconds=60),
        require_numeric_continuity=True,
        require_current_state_parity=True,
        require_provider_event_time=True,
        require_provider_publication_time=True,
        require_wall_clock_quality=True,
        required_depth_class=PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT,
    )
    base = PITFreshnessObservationV2(
        source_current=True,
        rights_active=True,
        transport_state=PITTransportStateV1.CONNECTED_HEALTHY,
        anchor_state=PITAnchorStateV1.ANCHOR_ACCEPTED,
        continuity_state=PITContinuityStateV3.CONTIGUOUS,
        integrity_state=PITIntegrityStateV1.VALID,
        current_state_parity_passed=True,
        provider_event_age_or_none=timedelta(seconds=1),
        provider_publication_time_present=True,
        local_receive_age=timedelta(seconds=1),
        durable_commit_age=timedelta(seconds=1),
        strategy_availability_age=timedelta(seconds=1),
        lifecycle_admissible=True,
        precision_valid=True,
        tick_valid=True,
        wall_clock_quality_sufficient=True,
        source_conflict=False,
        depth_class=PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT,
        economic_age=timedelta(seconds=1),
        durable_commit_complete=True,
    )
    assert evaluate_pit_freshness_v2(
        base_requirement, base
    ).terminal_availability is PITInputAvailabilityV2.AVAILABLE
    failures = (
        {"source_current": False},
        {"rights_active": False},
        {"transport_state": PITTransportStateV1.HEARTBEAT_OVERDUE},
        {"anchor_state": PITAnchorStateV1.REANCHOR_REQUIRED},
        {"continuity_state": PITContinuityStateV3.GAP_DETECTED},
        {"integrity_state": PITIntegrityStateV1.CURRENT_STATE_PARITY_FAILED},
        {"current_state_parity_passed": False},
        {"provider_event_age_or_none": None},
        {"provider_publication_time_present": False},
        {"local_receive_age": timedelta(seconds=61)},
        {"durable_commit_age": timedelta(seconds=61)},
        {"strategy_availability_age": timedelta(seconds=61)},
        {"lifecycle_admissible": False},
        {"precision_valid": False},
        {"tick_valid": False},
        {"wall_clock_quality_sufficient": False},
        {"source_conflict": True},
        {"depth_class": PITDepthClassV2.BBO_ONLY},
        {"economic_age": timedelta(seconds=61)},
        {"durable_commit_complete": False},
    )
    for mutation in failures:
        result = evaluate_pit_freshness_v2(
            base_requirement, replace(base, **mutation)
        )
        assert result.terminal_availability is not PITInputAvailabilityV2.AVAILABLE
        assert result.terminal_reason_or_none is not None
        assert result.recovery_requirements
    quiet = _good_freshness("QUIET-MARKET")
    assert quiet.terminal_availability is PITInputAvailabilityV2.AVAILABLE
    integrity_without_parity_requirement = evaluate_pit_freshness_v2(
        replace(base_requirement, require_current_state_parity=False),
        replace(
            base,
            integrity_state=PITIntegrityStateV1.CORRUPT,
            current_state_parity_passed=True,
        ),
    )
    assert integrity_without_parity_requirement.terminal_availability is not (
        PITInputAvailabilityV2.AVAILABLE
    )
    assert integrity_without_parity_requirement.terminal_reason_or_none is not None


def _case_commit_checkpoint_and_crash() -> None:
    from src.qtt.stage1_prediction_markets.market_data_ingest import policy
    from src.qtt.stage1_prediction_markets.market_data_ingest.adapter import (
        PITCanonicalEventV2,
    )
    from src.qtt.stage1_prediction_markets.market_data_ingest.validator import (
        validate_pit_ingest_record_v2,
    )
    from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.handoff import (
        PITAdmissionStateV2,
        _pit_partition_receipt_payloads,
        _pit_persist_receipt_payloads,
        _pit_recover_persisted_partition_v1,
        _pit_spine_record,
        commit_and_publish_pit_state_v2,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import (
        InMemoryPersistenceAdapterV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
        PersistenceContractError,
        ReasonCode,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.sqlite_reference import (
        SQLiteReferenceAdapterV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITEventDispositionV1,
        PITEventKindV2,
        PITReasonCodeV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
        CaptureAndGapReceiptV2,
        PITCheckpointV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
        deterministic_json,
    )
    from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.integrity import (
        reconstruct_pit_state_v2,
    )

    class _CrashInjectingAdapter(InMemoryPersistenceAdapterV1):
        def __init__(
            self,
            *,
            fail_before_commit_number: int | None = None,
            fail_after_commit_number: int | None = None,
        ) -> None:
            super().__init__()
            self.commit_count = 0
            self.fail_before_commit_number = fail_before_commit_number
            self.fail_after_commit_number = fail_after_commit_number

        def _commit(self, transaction: Any) -> None:
            self.commit_count += 1
            if self.commit_count == self.fail_before_commit_number:
                raise RuntimeError("injected crash before durable commit")
            super()._commit(transaction)
            if self.commit_count == self.fail_after_commit_number:
                raise RuntimeError("injected crash after durable commit")

    def _commit_once(
        persistence: Any,
        candidate: object,
        prior_state: object | None,
        *,
        partition_id: str,
        intent_id: str,
    ) -> object:
        prior_ordinal = (
            0
            if prior_state is None
            else prior_state.last_completed_event_ordinal
        )
        intent_offset_seconds = 3 + (2 * prior_ordinal)
        return commit_and_publish_pit_state_v2(
            persistence,
            contract,
            candidate,
            prior_state,
            partition_id=partition_id,
            intent_id=intent_id,
            intent_created_at_utc=_T0
            + timedelta(seconds=intent_offset_seconds),
            coordinator_clock=lambda: _T0
            + timedelta(seconds=intent_offset_seconds + 1),
            capability_context_id=f"CAPABILITY-CONTEXT::{partition_id}",
        )

    def _snapshot_candidate(suffix: str) -> object:
        return _ingest(
            _frame(
                "GEMINI_TITAN_DIRECT",
                _gemini_snapshot_tree(),
                suffix=suffix,
                channel="prediction_markets.depth",
                wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
                capture_session_id=f"CAPTURE::{suffix}",
            ),
            PITEventKindV2.BOOK_SNAPSHOT,
        )

    def _covering_candidate(suffix: str, *, capture_session_id: str) -> object:
        return _ingest(
            _frame(
                "GEMINI_TITAN_DIRECT",
                {
                    **_gemini_snapshot_tree(),
                    "U": 1,
                    "u": 2,
                    "bids": [["0.40", "0"]],
                    "asks": [],
                },
                suffix=suffix,
                channel="prediction_markets.depth",
                wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
                capture_session_id=capture_session_id,
            ),
            PITEventKindV2.BOOK_DELTA,
        )

    adapter = InMemoryPersistenceAdapterV1()
    contract = _contract_by_value("GEMINI_TITAN_DIRECT")
    first = _ingest(
        _frame(
            "GEMINI_TITAN_DIRECT",
            _gemini_snapshot_tree(),
            suffix="COMMIT-1",
            channel="prediction_markets.depth",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
            capture_session_id="COMMIT-CAPTURE",
        ),
        PITEventKindV2.BOOK_SNAPSHOT,
    )
    result = commit_and_publish_pit_state_v2(
        adapter,
        contract,
        first,
        None,
        partition_id="COMMIT-PARTITION",
        intent_id="COMMIT-INTENT-1",
        intent_created_at_utc=_T0 + timedelta(seconds=3),
        coordinator_clock=lambda: _T0 + timedelta(seconds=4),
        capability_context_id="CAPABILITY-CONTEXT-1",
    )
    assert result.admission_state is PITAdmissionStateV2.REFERENCE_COMPLETED_NO_EFFECT
    assert result.reason_code is PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE
    assert result.commit_completion.committed_event_ordinal == 1
    assert result.availability_receipt.published_pointer is False
    assert adapter.get_record(result.commit_completion.completion_id) is not None
    _expect_pit_error(
        lambda: replace(
            result.availability_receipt,
            strategy_available_at_utc_or_none=_T0 + timedelta(seconds=4),
        ),
        PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
    )
    _expect_pit_error(
        lambda: replace(
            result.downstream_handoff.reconstruction_receipt,
            reconstructed_levels=(),
        ),
        PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
    )
    mismatched_lock = replace(
        result.downstream_handoff.reconstruction_input_lock,
        market_id="MUTATED-MARKET",
    )
    _expect_pit_error(
        lambda: replace(
            result.downstream_handoff,
            reconstruction_input_lock=mismatched_lock,
        ),
        PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
    )
    checkpoint = PITCheckpointV1(
        checkpoint_id="CHECKPOINT-1",
        profile_id=first.profile_id,
        market_or_instrument_id=first.instrument_id,
        capture_session_id=first.capture_session_id,
        connection_epoch=first.connection_epoch,
        wire_dialect=first.wire_dialect,
        anchor_event_ref=result.commit_completion.final_event_record_ref,
        last_completed_event_ordinal=1,
        last_provider_range_or_sequence_or_none=1,
        ordered_bid_levels=(("0.40", "2.00"),),
        ordered_offer_levels=(("0.60", "3.00"),),
        depth_class=result.transition_result.post_state.state_vector.depth_class,
        transport_state=result.transition_result.post_state.state_vector.transport_state,
        anchor_state=result.transition_result.post_state.state_vector.anchor_state,
        continuity_state=result.transition_result.post_state.state_vector.continuity_state,
        integrity_state=result.transition_result.post_state.state_vector.integrity_state,
        availability_state=result.transition_result.post_state.state_vector.availability_state,
        lifecycle_state="ADMISSIBLE",
        lifecycle_version_ref="LIFECYCLE-V1",
        settlement_version_ref_or_none=None,
        source_currentization_receipt_ref=first.source_receipt_ref,
        rights_receipt_ref=first.rights_receipt_ref,
        previous_checkpoint_ref_or_none=None,
        serializer_version="QKU_DETERMINISTIC_JSON_V1",
        reconstruction_receipt_ref=result.downstream_handoff.reconstruction_receipt.receipt_id,
    )
    assert checkpoint.last_completed_event_ordinal == 1
    checkpoint_spine = _pit_spine_record(
        checkpoint,
        partition_id="COMMIT-PARTITION",
        recorded_at_utc=_T0 + timedelta(seconds=4),
        sequence=1,
    )
    assert checkpoint_spine.record_id == checkpoint.checkpoint_id
    assert checkpoint_spine.record_type.value == "PIT_CHECKPOINT"
    _pit_persist_receipt_payloads(
        adapter,
        (checkpoint,),
        partition_id="COMMIT-PARTITION",
        recorded_at_utc=_T0 + timedelta(seconds=4),
        sequence=1,
    )
    assert checkpoint in _pit_partition_receipt_payloads(
        adapter,
        partition_id="COMMIT-PARTITION",
        cutoff_utc=_T0 + timedelta(seconds=4),
    )
    _expect_pit_error(
        lambda: replace(
            checkpoint,
            ordered_bid_levels=(("0.30", "1"), ("0.40", "2")),
        ),
        PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
    )
    _expect_pit_error(
        lambda: replace(
            checkpoint,
            ordered_bid_levels=(("0.70", "1"),),
        ),
        PITReasonCodeV1.PIT_BOOK_CROSSED_INVALID,
    )
    _expect_pit_error(
        lambda: replace(
            result.downstream_handoff,
            full_depth_available=False,
        ),
        PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
    )
    _expect_pit_error(
        lambda: replace(
            result.commit_completion,
            completed_at_utc=_T0 + timedelta(seconds=3),
        ),
        PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
    )
    _expect_pit_error(
        lambda: replace(
            result.commit_completion,
            completed_at_utc=result.commit_completion.completed_at_utc.isoformat(),
        ),
        PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
    )
    event_spine = adapter.get_record(
        f"PIT-EVENT-RECEIPT::{first.event_record_id}"
    )
    assert event_spine is not None
    event_receipt = event_spine.typed_payload
    assert first.source_receipt_ref in event_receipt.canonical_event_json
    forged_spine_adapter = InMemoryPersistenceAdapterV1()
    forged_spine_transaction = forged_spine_adapter.begin_transaction()
    forged_spine_adapter.insert_receipt_record(
        forged_spine_transaction,
        replace(event_spine, semantic_owner="FORGED-SEMANTIC-OWNER"),
    )
    forged_spine_transaction.commit()
    _expect_pit_error(
        lambda: _pit_partition_receipt_payloads(
            forged_spine_adapter,
            partition_id="COMMIT-PARTITION",
            cutoff_utc=_T0 + timedelta(seconds=4),
        ),
        PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
    )
    forged_lineage_adapter = InMemoryPersistenceAdapterV1()
    forged_lineage_transaction = forged_lineage_adapter.begin_transaction()
    for persisted_spine in adapter.reconstruct_as_of(
        effective_cutoff=_T0 + timedelta(seconds=4),
        recorded_cutoff=_T0 + timedelta(seconds=4),
        aggregate_scope=("COMMIT-PARTITION",),
    ):
        payload = persisted_spine.typed_payload
        if type(payload) is CaptureAndGapReceiptV2:
            payload = replace(payload, post_state_ref="FORGED-POST-STATE")
        forged_lineage_adapter.insert_receipt_record(
            forged_lineage_transaction,
            _pit_spine_record(
                payload,
                partition_id="COMMIT-PARTITION",
                recorded_at_utc=persisted_spine.recorded_at,
                sequence=persisted_spine.sequence,
            ),
        )
    forged_lineage_transaction.commit()
    _expect_pit_error(
        lambda: _pit_recover_persisted_partition_v1(
            forged_lineage_adapter,
            (id(forged_lineage_adapter), "COMMIT-PARTITION"),
            partition_id="COMMIT-PARTITION",
            current_candidate_event_record_id="UNRELATED-CANDIDATE",
            cutoff_utc=_T0 + timedelta(seconds=4),
            coordinator_clock=lambda: _T0 + timedelta(seconds=5),
        ),
        PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
    )
    _expect_pit_error(
        lambda: replace(
            event_receipt,
            canonical_event_json=event_receipt.canonical_event_json.replace(
                first.source_receipt_ref,
                "MUTATED-SOURCE-RECEIPT",
            ),
        ),
        PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
    )
    event_mapping_with_extra = json.loads(event_receipt.canonical_event_json)
    event_mapping_with_extra["unexpected_field"] = "REJECT"
    _expect_pit_error(
        lambda: replace(
            event_receipt,
            canonical_event_json=deterministic_json(event_mapping_with_extra),
        ),
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    )
    final_clocks = _clock(
        provider_event_time_utc_or_none=first.provider_event_time_utc_or_none,
        qtt_received_at_utc=first.qtt_received_at_utc,
        qtt_received_monotonic_ns=first.qtt_received_monotonic_ns,
        qtt_parse_completed_at_utc=first.qtt_parse_completed_at_utc,
        qtt_parse_completed_monotonic_ns=first.qtt_parse_completed_monotonic_ns,
        durable_commit_completed_at_utc=result.commit_completion.completed_at_utc,
        durable_commit_completed_monotonic_ns=300,
        strategy_available_at_utc=_T0 + timedelta(seconds=5),
        strategy_available_monotonic_ns=400,
        revision_effective_time_utc_or_none=None,
        settlement_finality_time_utc_or_none=None,
        wall_clock_source_id=first.wall_clock_source_id,
        clock_quality_receipt_ref=first.clock_quality_receipt_ref,
        wall_clock_uncertainty_ns=first.wall_clock_uncertainty_ns,
    )
    final_event = PITCanonicalEventV2(
        event_record_id=first.event_record_id,
        profile_id=first.profile_id,
        market_id=first.market_id,
        instrument_id=first.instrument_id,
        channel=first.channel,
        connection_epoch=first.connection_epoch,
        capture_session_id=first.capture_session_id,
        committed_event_ordinal=1,
        event_kind=first.event_kind,
        schema_version=first.schema_version,
        wire_dialect=first.wire_dialect,
        source_currentization_version=first.source_currentization_version,
        provider_sequence_start_or_none=first.provider_sequence_start_or_none,
        provider_sequence_end_or_none=first.provider_sequence_end_or_none,
        provider_trade_id_or_none=first.provider_trade_id_or_none,
        provider_subscription_id_or_none=first.provider_subscription_id_or_none,
        payload=first.payload,
        depth_class=first.depth_class,
        clocks=final_clocks,
        pre_state_ref="NO-PRIOR-STATE::COMMIT-PARTITION",
        post_state_ref=result.transition_result.post_state.state_id,
        event_disposition=PITEventDispositionV1.COMMITTED,
        failure_reason_or_none=None,
        rights_receipt_ref=first.rights_receipt_ref,
        source_receipt_ref=first.source_receipt_ref,
        commit_completion_ref=result.commit_completion.completion_id,
        prior_event_ref_or_none=None,
        checkpoint_ref_or_none=None,
        recovery_receipt_ref_or_none=None,
        no_private_state_authority=True,
        no_order_authority=True,
        no_profit_claim=True,
        no_qpu_effect=True,
        no_llm_effect=True,
    )
    assert validate_pit_ingest_record_v2(final_event, contract=contract) is final_event
    _expect_pit_error(
        lambda: validate_pit_ingest_record_v2(
            replace(final_event, channel="prediction_markets.bookTicker"),
            contract=contract,
        ),
        PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
    )
    reconstructed = reconstruct_pit_state_v2(
        (final_event,),
        (result.commit_completion,),
    )
    assert reconstructed.levels == result.transition_result.post_state.levels
    _expect_pit_error(
        lambda: reconstruct_pit_state_v2(
            (replace(final_event, post_state_ref="MUTATED-POST-STATE"),),
            (result.commit_completion,),
        ),
        PITReasonCodeV1.PIT_RECONSTRUCTION_DIVERGENCE,
    )
    extra_completion = replace(
        result.commit_completion,
        completion_id="EXTRANEOUS-COMPLETION",
    )
    _expect_pit_error(
        lambda: reconstruct_pit_state_v2(
            (final_event,),
            (result.commit_completion, extra_completion),
        ),
        PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
    )
    visible = _oracle_visible_ordinals(
        (
            {"ordinal": 1, "intent": True, "committed": False, "completion": False},
            {"ordinal": 1, "intent": True, "committed": True, "completion": True},
            {"ordinal": 2, "intent": True, "committed": False, "completion": False},
        )
    )
    assert visible == (1,)
    assert _oracle_visible_ordinals(
        (
            {"ordinal": 1, "intent": True, "committed": True, "completion": True},
            {"ordinal": 2, "intent": True, "committed": True, "completion": True},
        )
    ) == (1, 2)

    sqlite_adapter = SQLiteReferenceAdapterV1(
        ":memory:",
        busy_timeout_ms=0,
        max_transaction_attempts=1,
    )
    try:
        sqlite_first = _snapshot_candidate("SQLITE-REFERENCE-1")
        sqlite_first_result = _commit_once(
            sqlite_adapter,
            sqlite_first,
            None,
            partition_id="SQLITE-REFERENCE-PARTITION",
            intent_id="SQLITE-REFERENCE-INTENT-1",
        )
        assert sqlite_first_result.admission_state is (
            PITAdmissionStateV2.REFERENCE_COMPLETED_NO_EFFECT
        )
        assert sqlite_first_result.reason_code is (
            PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE
        )
        assert sqlite_first_result.commit_completion.committed_event_ordinal == 1
        assert sqlite_first_result.availability_receipt.published_pointer is False
        assert sqlite_adapter.get_record(
            sqlite_first_result.commit_completion.completion_id
        ) is not None

        sqlite_conflict = replace(
            _snapshot_candidate("SQLITE-REFERENCE-CONFLICT"),
            event_record_id=sqlite_first.event_record_id,
            connection_epoch="SQLITE-REFERENCE-CONFLICT-EPOCH",
            capture_session_id=sqlite_first.capture_session_id,
        )
        with pytest.raises(PersistenceContractError) as sqlite_conflict_error:
            _commit_once(
                sqlite_adapter,
                sqlite_conflict,
                sqlite_first_result.transition_result.post_state,
                partition_id="SQLITE-REFERENCE-PARTITION",
                intent_id="SQLITE-REFERENCE-CONFLICT-INTENT",
            )
        assert sqlite_conflict_error.value.reason_code is ReasonCode.PERSISTENCE_CONFLICT

        sqlite_second = _covering_candidate(
            "SQLITE-REFERENCE-2",
            capture_session_id=sqlite_first.capture_session_id,
        )
        sqlite_second_result = _commit_once(
            sqlite_adapter,
            sqlite_second,
            sqlite_first_result.transition_result.post_state,
            partition_id="SQLITE-REFERENCE-PARTITION",
            intent_id="SQLITE-REFERENCE-INTENT-2",
        )
        assert sqlite_second_result.commit_completion.committed_event_ordinal == 2
        sqlite_rows = sqlite_adapter.reconstruct_as_of(
            effective_cutoff=_T0 + timedelta(seconds=7),
            recorded_cutoff=_T0 + timedelta(seconds=7),
            aggregate_scope=("SQLITE-REFERENCE-PARTITION",),
        )
        assert sqlite_rows == sqlite_adapter.reconstruct_as_of(
            effective_cutoff=_T0 + timedelta(seconds=7),
            recorded_cutoff=_T0 + timedelta(seconds=7),
            aggregate_scope=("SQLITE-REFERENCE-PARTITION",),
        )
        assert len(sqlite_rows) == 11
    finally:
        sqlite_adapter.close()

    with TemporaryDirectory(prefix="qtt-pit-sqlite-reference-") as temp_directory:
        database_path = Path(temp_directory) / "pit-reference.sqlite3"
        sqlite_before_restart = SQLiteReferenceAdapterV1(
            database_path,
            busy_timeout_ms=0,
            max_transaction_attempts=1,
        )
        restart_first = _snapshot_candidate("SQLITE-RESTART-1")
        try:
            restart_first_result = _commit_once(
                sqlite_before_restart,
                restart_first,
                None,
                partition_id="SQLITE-RESTART-PARTITION",
                intent_id="SQLITE-RESTART-INTENT-1",
            )
        finally:
            sqlite_before_restart.close()
        sqlite_after_restart = SQLiteReferenceAdapterV1(
            database_path,
            busy_timeout_ms=0,
            max_transaction_attempts=1,
        )
        try:
            restart_second = _covering_candidate(
                "SQLITE-RESTART-2",
                capture_session_id=restart_first.capture_session_id,
            )
            restart_second_result = _commit_once(
                sqlite_after_restart,
                restart_second,
                restart_first_result.transition_result.post_state,
                partition_id="SQLITE-RESTART-PARTITION",
                intent_id="SQLITE-RESTART-INTENT-2",
            )
            assert restart_second_result.commit_completion.committed_event_ordinal == 2
            assert restart_second_result.admission_state is (
                PITAdmissionStateV2.REFERENCE_COMPLETED_NO_EFFECT
            )
        finally:
            sqlite_after_restart.close()

    crash_before_intent = _CrashInjectingAdapter(fail_before_commit_number=1)
    before_intent_candidate = _snapshot_candidate("CRASH-BEFORE-INTENT")
    with pytest.raises(RuntimeError, match="before durable commit"):
        _commit_once(
            crash_before_intent,
            before_intent_candidate,
            None,
            partition_id="CRASH-BEFORE-INTENT-PARTITION",
            intent_id="CRASH-BEFORE-INTENT-ID",
        )
    assert crash_before_intent.get_record("CRASH-BEFORE-INTENT-ID") is None
    assert (
        crash_before_intent.get_record(
            f"PIT-EVENT-RECEIPT::{before_intent_candidate.event_record_id}"
        )
        is None
    )

    crash_before_event = _CrashInjectingAdapter(fail_before_commit_number=2)
    before_event_candidate = _snapshot_candidate("CRASH-BEFORE-EVENT")
    with pytest.raises(RuntimeError, match="before durable commit"):
        _commit_once(
            crash_before_event,
            before_event_candidate,
            None,
            partition_id="CRASH-BEFORE-EVENT-PARTITION",
            intent_id="CRASH-BEFORE-EVENT-ID",
        )
    assert crash_before_event.get_record("CRASH-BEFORE-EVENT-ID") is not None
    assert (
        crash_before_event.get_record(
            f"PIT-EVENT-RECEIPT::{before_event_candidate.event_record_id}"
        )
        is None
    )
    recovered_before_event = _commit_once(
        crash_before_event,
        before_event_candidate,
        None,
        partition_id="CRASH-BEFORE-EVENT-PARTITION",
        intent_id="CRASH-BEFORE-EVENT-ID",
    )
    assert recovered_before_event.commit_completion.committed_event_ordinal == 1

    crash_after_event = _CrashInjectingAdapter(fail_after_commit_number=2)
    after_event_candidate = _snapshot_candidate("CRASH-AFTER-EVENT")
    with pytest.raises(RuntimeError, match="after durable commit"):
        _commit_once(
            crash_after_event,
            after_event_candidate,
            None,
            partition_id="CRASH-AFTER-EVENT-PARTITION",
            intent_id="CRASH-AFTER-EVENT-ID",
        )
    assert (
        crash_after_event.get_record(
            f"PIT-EVENT-RECEIPT::{after_event_candidate.event_record_id}"
        )
        is not None
    )
    assert (
        crash_after_event.get_record(
            f"PIT-COMPLETION::{after_event_candidate.event_record_id}"
        )
        is None
    )
    recovered_after_event = _commit_once(
        crash_after_event,
        after_event_candidate,
        None,
        partition_id="CRASH-AFTER-EVENT-PARTITION",
        intent_id="CRASH-AFTER-EVENT-ID",
    )
    assert recovered_after_event.commit_completion.committed_event_ordinal == 1

    crash_before_completion = _CrashInjectingAdapter(fail_before_commit_number=3)
    before_completion_candidate = _snapshot_candidate("CRASH-BEFORE-COMPLETION")
    incomplete = _commit_once(
        crash_before_completion,
        before_completion_candidate,
        None,
        partition_id="CRASH-BEFORE-COMPLETION-PARTITION",
        intent_id="CRASH-BEFORE-COMPLETION-ID",
    )
    assert incomplete.admission_state is PITAdmissionStateV2.REJECTED
    assert incomplete.commit_completion is None
    assert incomplete.availability_receipt is None
    _expect_pit_error(
        lambda: replace(
            incomplete,
            commit_completion=result.commit_completion,
        ),
        PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
    )
    assert (
        crash_before_completion.get_record(
            f"PIT-COMPLETION::{before_completion_candidate.event_record_id}"
        )
        is None
    )
    after_recovery_candidate = _covering_candidate(
        "AFTER-COMPLETION-RECOVERY",
        capture_session_id="CAPTURE::CRASH-BEFORE-COMPLETION",
    )
    after_recovery = _commit_once(
        crash_before_completion,
        after_recovery_candidate,
        incomplete.transition_result.post_state,
        partition_id="CRASH-BEFORE-COMPLETION-PARTITION",
        intent_id="AFTER-COMPLETION-RECOVERY-ID",
    )
    assert (
        crash_before_completion.get_record(
            f"PIT-COMPLETION::{before_completion_candidate.event_record_id}"
        )
        is not None
    )
    assert after_recovery.commit_completion.committed_event_ordinal == 2
    assert after_recovery.availability_receipt.published_pointer is False
    assert policy.PIT_SAFETY_SEED_AND_CALIBRATION_ENVELOPE_V2.checkpoint_event_threshold == 10_000


def _case_rights_and_security() -> None:
    from src.qtt.stage1_prediction_markets.market_data_ingest import policy
    from src.qtt.stage1_prediction_markets.market_data_ingest.adapter import (
        PITRawFrameV1,
        build_pit_read_requests_v2,
    )
    from src.qtt.stage1_prediction_markets.market_data_ingest.binding import (
        build_selected_pit_public_data_contracts_v2,
    )
    from src.qtt.stage1_prediction_markets.market_data_ingest.source_dependency import (
        PIT_SOURCE_DEPENDENCIES_V2,
    )
    from src.qtt.stage1_prediction_markets.market_data_ingest.validator import (
        PITMarketDataIngestDispatcherV2,
        validate_pit_ingest_record_v2,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITDepthClassV2,
        PITEventKindV2,
        PITReasonCodeV1,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import (
        validate_pit_source_rights_admission_v1,
    )

    contracts = _build_contracts()
    sources, rights = _build_source_and_rights()
    with pytest.raises(TypeError):
        build_selected_pit_public_data_contracts_v2(
            policy.PIT_SELECTED_SCOPE_V2,
            sources,
            rights,
        )
    assert len(PIT_SOURCE_DEPENDENCIES_V2) == 26
    requests = build_pit_read_requests_v2(contracts)
    dependencies_by_id = {
        dependency.dependency_id: dependency
        for dependency in PIT_SOURCE_DEPENDENCIES_V2
    }
    assert len(requests) == 26
    assert len({request.request_id for request in requests}) == len(requests)
    assert len(
        {request.source_dependency_ref for request in requests}
    ) == len(requests)
    assert {request.source_dependency_ref for request in requests} == set(
        dependencies_by_id
    )
    for read_request in requests:
        dependency = dependencies_by_id[read_request.source_dependency_ref]
        request_contract = next(
            contract
            for contract in contracts
            if contract.profile_id is read_request.profile_id
        )
        validate_pit_ingest_record_v2(read_request, contract=request_contract)
        assert read_request.profile_id is dependency.profile_id
        assert read_request.event_kind is dependency.event_kind
        assert read_request.access_class is dependency.access_class
        assert read_request.host == dependency.host
        assert read_request.path_or_channel == dependency.path_or_channel
        assert read_request.read_action is dependency.read_action
        assert (
            read_request.credential_alias_required
            is dependency.credential_alias_required
        )
        assert read_request.no_write is True
        assert read_request.no_private_state is True
    assert not any(
        read_request.read_action is policy.PITReadActionV1.GET
        and read_request.path_or_channel == "/markets/{ticker}/orderbook"
        for read_request in requests
    )
    kalshi_snapshot_requests = tuple(
        read_request
        for read_request in requests
        if read_request.profile_id.value == "KALSHI_US_DCM_DIRECT"
        and read_request.event_kind is PITEventKindV2.BOOK_SNAPSHOT
    )
    assert len(kalshi_snapshot_requests) == 1
    kalshi_snapshot_request = kalshi_snapshot_requests[0]
    assert (
        kalshi_snapshot_request.read_action
        is policy.PITReadActionV1.WEBSOCKET_RECOVERY
    )
    assert kalshi_snapshot_request.path_or_channel == "orderbook_delta"
    assert dict(kalshi_snapshot_request.query_or_subscription_payload) == {
        "command": "get_snapshot",
        "channels": ("orderbook_delta",),
        "market_tickers": (),
        "use_yes_price": True,
    }
    for dependency in PIT_SOURCE_DEPENDENCIES_V2:
        validate_pit_ingest_record_v2(dependency)
        if dependency.event_kind is PITEventKindV2.BOOK_SNAPSHOT:
            assert dependency.depth_class is PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT
        elif dependency.event_kind is PITEventKindV2.BOOK_DELTA:
            assert dependency.depth_class is PITDepthClassV2.INCREMENTAL_FROM_COMPLETE_ANCHOR
        elif dependency.event_kind is PITEventKindV2.BBO:
            assert dependency.depth_class is PITDepthClassV2.BBO_ONLY
        elif dependency.event_kind is PITEventKindV2.BOOK_REPLACEMENT:
            expected_depth = (
                PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT
                if dependency.read_action is policy.PITReadActionV1.GET
                else PITDepthClassV2.PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME
            )
            assert dependency.depth_class is expected_depth
    sources, rights = _build_source_and_rights()
    _expect_pit_error(
        lambda: build_selected_pit_public_data_contracts_v2(
            policy.PIT_SELECTED_SCOPE_V2,
            sources,
            rights[:-1],
            evaluated_at_utc=_T0,
        ),
        PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
    )
    _expect_pit_error(
        lambda: validate_pit_source_rights_admission_v1(
            sources[0],
            rights[0],
            admission_id="PRECHECK-SOURCE-RIGHTS",
            profile_id=sources[0].profile_id,
            account_scope=rights[0].account_scope,
            internal_use_class=rights[0].internal_use_class,
            permitted_retention_class=rights[0].permitted_retention_class,
            evaluated_at_utc=_T0 - timedelta(microseconds=1),
        ),
        PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
    )
    long_sources = tuple(
        replace(
            source,
            effective_at_utc=_T0 - timedelta(days=365),
            expires_at_utc=_T0 + timedelta(hours=48),
        )
        for source in sources
    )
    long_rights = tuple(
        replace(right, expires_at_utc=_T0 + timedelta(hours=48))
        for right in rights
    )
    build_selected_pit_public_data_contracts_v2(
        policy.PIT_SELECTED_SCOPE_V2,
        long_sources,
        long_rights,
        evaluated_at_utc=_T0 + timedelta(hours=24),
    )
    _expect_pit_error(
        lambda: build_selected_pit_public_data_contracts_v2(
            policy.PIT_SELECTED_SCOPE_V2,
            long_sources,
            long_rights,
            evaluated_at_utc=_T0 + timedelta(hours=24, microseconds=1),
        ),
        PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
    )
    _expect_pit_error(
        lambda: build_selected_pit_public_data_contracts_v2(
            policy.PIT_SELECTED_SCOPE_V2,
            sources,
            (replace(rights[0], expires_at_utc=_T0 + timedelta(hours=1)), *rights[1:]),
            evaluated_at_utc=_T0 + timedelta(hours=2),
        ),
        PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
    )
    _expect_pit_error(
        lambda: replace(rights[0], revoked=True),
        PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
    )
    _expect_pit_error(
        lambda: replace(sources[0], invalidating_change_detected=True),
        PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
    )
    _expect_pit_error(
        lambda: replace(sources[0], recheck_triggers=()),
        PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
    )
    _expect_pit_error(
        lambda: replace(rights[0], recheck_triggers=()),
        PITReasonCodeV1.PIT_RIGHTS_NOT_ADMITTED,
    )
    long_source = replace(
        sources[0],
        effective_at_utc=_T0 - timedelta(days=365),
        expires_at_utc=_T0 + timedelta(hours=48),
    )
    validate_pit_source_rights_admission_v1(
        long_source,
        replace(rights[0], expires_at_utc=_T0 + timedelta(hours=48)),
        admission_id="SOURCE-RIGHTS-AT-24H",
        profile_id=long_source.profile_id,
        account_scope=rights[0].account_scope,
        internal_use_class=rights[0].internal_use_class,
        permitted_retention_class=rights[0].permitted_retention_class,
        evaluated_at_utc=_T0 + timedelta(hours=24),
    )
    _expect_pit_error(
        lambda: validate_pit_source_rights_admission_v1(
            long_source,
            replace(rights[0], expires_at_utc=_T0 + timedelta(hours=48)),
            admission_id="SOURCE-RIGHTS-AFTER-24H",
            profile_id=long_source.profile_id,
            account_scope=rights[0].account_scope,
            internal_use_class=rights[0].internal_use_class,
            permitted_retention_class=rights[0].permitted_retention_class,
            evaluated_at_utc=_T0 + timedelta(hours=24, microseconds=1),
        ),
        PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
    )
    _expect_pit_error(
        lambda: build_selected_pit_public_data_contracts_v2(
            policy.PIT_SELECTED_SCOPE_V2,
            sources,
            rights,
            evaluated_at_utc=_T0 + timedelta(hours=13),
        ),
        PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
    )
    _expect_pit_error(
        lambda: replace(
            _build_contracts()[0], no_private_state_authority=False
        ),
        PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
    )
    request = requests[0]
    request_contract = next(
        value for value in contracts if value.profile_id is request.profile_id
    )
    _expect_pit_error(
        lambda: validate_pit_ingest_record_v2(
            replace(request, path_or_channel="/private/account/orders"),
            contract=request_contract,
        ),
        PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
    )
    _expect_pit_error(
        lambda: validate_pit_ingest_record_v2(
            replace(request, read_action=policy.PITReadActionV1.WEBSOCKET_UNSUBSCRIBE),
            contract=request_contract,
        ),
        PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
    )
    for request_mutation in (
        {"request_id": "MUTATED-REQUEST-ID"},
        {"source_dependency_ref": "MUTATED-DEPENDENCY"},
        {"credential_alias_required": not request.credential_alias_required},
    ):
        _expect_pit_error(
            lambda request_mutation=request_mutation: validate_pit_ingest_record_v2(
                replace(request, **request_mutation),
                contract=request_contract,
            ),
            PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
        )
    _expect_pit_error(
        lambda: validate_pit_ingest_record_v2(
            replace(request, source_contract_version="MUTATED-SOURCE-CONTRACT"),
            contract=request_contract,
        ),
        PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
    )
    websocket_request = next(
        value
        for value in requests
        if value.read_action is policy.PITReadActionV1.WEBSOCKET_SUBSCRIBE
    )
    _expect_pit_error(
        lambda: validate_pit_ingest_record_v2(
            replace(websocket_request, path_or_channel="private_user_orders"),
            contract=next(
                value
                for value in contracts
                if value.profile_id is websocket_request.profile_id
            ),
        ),
        PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
    )
    _expect_pit_error(
        lambda: _frame(
            "GEMINI_TITAN_DIRECT",
            {"instrumentSymbol": "X", "account_id": "PRIVATE"},
            suffix="PRIVATE-FIELD",
            channel="prediction_markets.depth",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
        ),
        PITReasonCodeV1.PIT_PRIVATE_FIELD_CLASS_REJECTED,
    )
    _expect_pit_error(
        lambda: _frame(
            "GEMINI_TITAN_DIRECT",
            {"instrumentSymbol": "X", "accountBalance": "PRIVATE"},
            suffix="PRIVATE-CAMEL-FIELD",
            channel="prediction_markets.depth",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
        ),
        PITReasonCodeV1.PIT_PRIVATE_FIELD_CLASS_REJECTED,
    )
    contract = _contract_by_value("GEMINI_TITAN_DIRECT")
    _expect_pit_error(
        lambda: PITRawFrameV1(
            frame_id="SECRET-FRAME",
            profile_id=contract.profile_id,
            connection_epoch="EPOCH",
            capture_session_id="CAPTURE",
            wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
            channel="prediction_markets.depth",
            raw_utf8_text_or_none="{\"instrumentSymbol\":\"X\"}",
            parsed_source_scalar_tree_or_none=None,
            qtt_received_at_utc=_T0,
            qtt_received_monotonic_ns=1,
            process_epoch_id="PROCESS",
            monotonic_clock_id="CLOCK",
            wall_clock_source_id="WALL",
            clock_quality_receipt_ref="QUALITY",
            wall_clock_uncertainty_ns=1,
            source_contract_refs=(contract.contract_id,),
            contains_credential=True,
        ),
        PITReasonCodeV1.PIT_PRIVATE_FIELD_CLASS_REJECTED,
    )
    malformed_frame = PITRawFrameV1(
        frame_id="UNTRUSTED-DUPLICATE-KEY-FRAME",
        profile_id=contract.profile_id,
        connection_epoch="EPOCH",
        capture_session_id="CAPTURE",
        wire_dialect="GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
        channel="prediction_markets.depth",
        raw_utf8_text_or_none='{"market_id":"A","market_id":"B"}',
        parsed_source_scalar_tree_or_none=None,
        qtt_received_at_utc=_T0,
        qtt_received_monotonic_ns=1,
        process_epoch_id="PROCESS",
        monotonic_clock_id="CLOCK",
        wall_clock_source_id="WALL",
        clock_quality_receipt_ref="QUALITY",
        wall_clock_uncertainty_ns=1,
        source_contract_refs=(contract.contract_id,),
    )
    _expect_pit_error(
        lambda: validate_pit_ingest_record_v2(
            replace(
                malformed_frame,
                frame_id="RAW-PRIVATE-CAMEL-FIELD",
                raw_utf8_text_or_none=(
                    '{"instrumentSymbol":"X","accountBalance":"PRIVATE"}'
                ),
            ),
            contract=contract,
        ),
        PITReasonCodeV1.PIT_PRIVATE_FIELD_CLASS_REJECTED,
    )
    _expect_pit_error(
        lambda: validate_pit_ingest_record_v2(
            replace(
                malformed_frame,
                frame_id="RAW-EXTRA-CONTRACT-REF",
                raw_utf8_text_or_none='{"instrumentSymbol":"X"}',
                source_contract_refs=(contract.contract_id, "EXTRA-CONTRACT"),
            ),
            contract=contract,
        ),
        PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
    )
    _expect_pit_error(
        lambda: validate_pit_ingest_record_v2(
            replace(
                malformed_frame,
                frame_id="RAW-WRONG-DIALECT",
                raw_utf8_text_or_none='{"instrumentSymbol":"X"}',
                wire_dialect="WRONG-DIALECT",
            ),
            contract=contract,
        ),
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    )
    descriptor_with_identifiers = next(
        descriptor
        for descriptor in build_pit_read_requests_v2(
            contracts,
            market_identifiers_by_profile={contract.profile_id: ("GEMINI-EVENT-1",)},
        )
        if descriptor.profile_id is contract.profile_id
        and descriptor.read_action is policy.PITReadActionV1.WEBSOCKET_SUBSCRIBE
    )
    assert type(
        dict(descriptor_with_identifiers.query_or_subscription_payload)["symbols"]
    ) is tuple
    _expect_pit_error(
        lambda: replace(
            descriptor_with_identifiers,
            query_or_subscription_payload=tuple(
                (key, [*value] if key == "symbols" else value)
                for key, value in descriptor_with_identifiers.query_or_subscription_payload
            ),
        ),
        PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
    )
    dispatcher = PITMarketDataIngestDispatcherV2(contracts)
    _expect_pit_error(
        lambda: dispatcher.ingest(
            malformed_frame,
            event_kind=PITEventKindV2.CATALOG,
            parse_completed_at_utc=_T0 + timedelta(microseconds=1),
            parse_completed_monotonic_ns=2,
            price_increment_text="0.01",
            price_origin_text="0.00",
            quantity_increment_text_or_none=None,
        ),
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
    )
    sources = []
    rights = []
    for profile_contract in contracts:
        sources.append(profile_contract.source_currentization_receipt_ref)
        rights.append(profile_contract.rights_receipt_ref)
    assert len(set(sources)) == len(contracts)
    assert len(set(rights)) == len(contracts)


def _case_formula_input_capability() -> None:
    from src.qtt.stage1_prediction_markets.market_data_ingest.handoff import (
        build_pit_input_capabilities_v2,
        build_pit_market_data_handoff_v2,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.input_resolver import (
        CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID,
        FormulaInputAuthorityBindingV1,
        PITFormulaInputPacketV2,
        ST12DMath39RawInputBindingV1,
        partition_pit_formula_input_authority_v1,
        resolve_pit_formula_inputs_v2,
    )
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
        PITInputAvailabilityV2,
    )

    partition = partition_pit_formula_input_authority_v1()
    assert partition.all_row_count == 144
    assert partition.pit_row_count == 21
    assert partition.non_pit_row_count == 123
    assert set(partition.all_binding_ids) == (
        set(partition.pit_applicable_binding_order)
        | set(partition.non_pit_binding_order)
    )
    assert not set(partition.pit_applicable_binding_order) & set(
        partition.non_pit_binding_order
    )
    freshness = tuple(
        _good_freshness(f"{profile}::{binding_id}")
        for profile in _SELECTED_PROFILE_VALUES
        for binding_id in partition.pit_applicable_binding_order
    )
    contracts = _build_contracts()
    capabilities = build_pit_input_capabilities_v2(
        contracts,
        freshness,
        event_or_snapshot_refs_by_profile=tuple(
            (contract.profile_id, f"STATE::{contract.profile_id.value}")
            for contract in contracts
        ),
        context_id="FORMULA-CONTEXT-1",
        source_epoch_id="SOURCE-EPOCH-1",
        input_version="INPUT-VERSION-1",
    )
    assert len(capabilities) == 63
    keys = {(value.profile_id, value.binding_id) for value in capabilities}
    assert len(keys) == 63
    for profile in (contract.profile_id for contract in contracts):
        assert {
            capability.binding_id
            for capability in capabilities
            if capability.profile_id is profile
        } == set(partition.pit_applicable_binding_order)
    assert all(
        capability.declared_input_type
        and capability.unit_or_basis
        and capability.source_field_path
        for capability in capabilities
    )
    rows_by_binding_id = {
        row.binding_id: row
        for rows in CURRENT_FORMULA_INPUT_AUTHORITY_BY_MATH_ID.values()
        for row in rows
        if row.binding_id in partition.pit_applicable_binding_ids
    }
    for capability in capabilities:
        row = rows_by_binding_id[capability.binding_id]
        assert capability.input_name == row.input_name
        assert capability.accepted_packet_or_snapshot_type == (
            row.accepted_packet_or_snapshot_type
        )
        assert capability.source_field_path == row.exact_field_path
        assert capability.unit_or_basis == row.unit_or_basis
        if type(row) is FormulaInputAuthorityBindingV1:
            assert capability.math_spec_id == row.math_spec_id
            assert capability.declared_input_type == row.input_type
            assert capability.transform == row.canonical_typed_value_extraction
            assert capability.required_clock_fields == row.required_clock_fields
        else:
            assert type(row) is ST12DMath39RawInputBindingV1
            assert capability.math_spec_id == "MATH-39"
            assert capability.declared_input_type == "SequencedBookEventsPacketV1"
            assert capability.transform == row.point_in_time_rule
        intrinsically_unavailable = (
            (
                type(row) is FormulaInputAuthorityBindingV1
                and row.accepted_upstream_owner_id
                in {
                    "KalshiAcceptedOrderBookStateOwnerV1",
                    "KalshiMarketMetadataOwnerV1",
                }
                and capability.profile_id.value != "KALSHI_US_DCM_DIRECT"
            )
            or (
                capability.profile_id.value == "POLYMARKET_US_RETAIL_DIRECT"
                and (
                    type(row) is ST12DMath39RawInputBindingV1
                    or (
                        type(row) is FormulaInputAuthorityBindingV1
                        and row.domain == "CURRENT_CONTIGUOUS_BOOK"
                    )
                )
            )
        )
        assert (
            capability.availability is not PITInputAvailabilityV2.AVAILABLE
        ) is intrinsically_unavailable
        if (
            capability.profile_id.value == "POLYMARKET_US_RETAIL_DIRECT"
            and capability.source_field_path
            in {"market_state.best_bid", "market_state.best_ask"}
        ):
            assert capability.provider_sequence_required is False
    assert sum(
        capability.availability is PITInputAvailabilityV2.AVAILABLE
        for capability in capabilities
    ) == 45
    capability_source = Path(
        "src/qtt/stage1_prediction_markets/market_data_ingest/handoff.py"
    ).read_text(encoding="utf-8")
    assert '"::MATH-36::" in' not in capability_source
    assert '.startswith("list[")' not in capability_source
    assert any(
        capability.availability is not PITInputAvailabilityV2.AVAILABLE
        and capability.unavailable_reason_or_none is not None
        for capability in capabilities
    )
    handoff = build_pit_market_data_handoff_v2(
        contracts,
        capabilities,
        canonical_event_refs=("EVENT-1",),
        capture_and_gap_receipt_refs=("CAPTURE-1",),
    )
    assert handoff.exact_capability_key_set_equal is True
    truncated_capabilities = capabilities[:-1]
    _expect_pit_error(
        lambda: replace(
            handoff,
            input_capabilities=truncated_capabilities,
            expected_capability_keys=frozenset(
                (capability.profile_id, capability.binding_id)
                for capability in truncated_capabilities
            ),
        )
    )
    mutated = replace(capabilities[0], binding_id="FUZZY-MUTATED-IDENTITY")
    _expect_pit_error(
        lambda: build_pit_market_data_handoff_v2(
            contracts,
            (mutated, *capabilities[1:]),
            canonical_event_refs=("EVENT-1",),
            capture_and_gap_receipt_refs=("CAPTURE-1",),
        )
    )
    unavailable = next(
        capability
        for capability in capabilities
        if capability.availability is not PITInputAvailabilityV2.AVAILABLE
    )
    _expect_pit_error(
        lambda: replace(unavailable, event_or_snapshot_ref_or_none="FORBIDDEN-LINEAGE")
    )

    def packet_value(declared_type: str) -> object:
        return {
            "boolean": True,
            "int": 1,
            "Decimal string": "0.50",
            "list[Decimal string]": ("0.40", "0.60"),
            "enum": "ACTIVE",
            "list[record]": ({"record_id": "RECORD-1"},),
            "SequencedBookEventsPacketV1": (
                {"event_ref": "EVENT-1", "ordinal": 1},
            ),
        }[declared_type]

    packets = tuple(
        PITFormulaInputPacketV2(
            packet_id=f"PACKET::{capability.capability_id}",
            profile_id=capability.profile_id,
            binding_id=capability.binding_id,
            context_id=capability.context_id,
            source_epoch_id=capability.source_epoch_id,
            input_version=capability.input_version,
            declared_input_type=capability.declared_input_type,
            declared_shape_or_none=capability.declared_shape_or_none,
            unit_or_basis=capability.unit_or_basis,
            source_field_path=capability.source_field_path,
            value=packet_value(capability.declared_input_type),
            event_or_snapshot_ref=capability.event_or_snapshot_ref_or_none,
            freshness_receipt_ref=capability.freshness_receipt_ref_or_none,
        )
        for capability in capabilities
        if capability.availability is PITInputAvailabilityV2.AVAILABLE
    )
    assert packets
    resolution = resolve_pit_formula_inputs_v2(
        capabilities,
        packets,
        resolution_id="FORMULA-RESOLUTION-1",
        context_id="FORMULA-CONTEXT-1",
        source_epoch_id="SOURCE-EPOCH-1",
        input_version="INPUT-VERSION-1",
    )
    assert resolution.exact_key_set_equal is True
    assert len(resolution.resolved_inputs) == len(packets)
    assert len(resolution.unavailable_capabilities) + len(packets) == 63
    _expect_pit_error(
        lambda: resolve_pit_formula_inputs_v2(
            (replace(capabilities[0], source_field_path="FUZZY.FIELD"), *capabilities[1:]),
            packets,
            resolution_id="FORMULA-RESOLUTION-METADATA-MUTATION",
            context_id="FORMULA-CONTEXT-1",
            source_epoch_id="SOURCE-EPOCH-1",
            input_version="INPUT-VERSION-1",
        )
    )
    malformed_index = next(
        index
        for index, packet in enumerate(packets)
        if packet.declared_input_type != "boolean"
    )
    malformed_packets = list(packets)
    malformed_packets[malformed_index] = replace(
        packets[malformed_index], value=False
    )
    _expect_pit_error(
        lambda: resolve_pit_formula_inputs_v2(
            capabilities,
            tuple(malformed_packets),
            resolution_id="FORMULA-RESOLUTION-VALUE-MUTATION",
            context_id="FORMULA-CONTEXT-1",
            source_epoch_id="SOURCE-EPOCH-1",
            input_version="INPUT-VERSION-1",
        )
    )


def _oracle_decimal(text: object, scale: object, tick: object, origin: object) -> Decimal:
    decimal_pattern = r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?"
    if (
        type(text) is not str
        or type(tick) is not str
        or type(origin) is not str
        or type(scale) is not int
        or isinstance(scale, bool)
        or re.fullmatch(decimal_pattern, text) is None
        or re.fullmatch(decimal_pattern, tick) is None
        or re.fullmatch(decimal_pattern, origin) is None
    ):
        raise ValueError("oracle decimal type")
    try:
        value = Decimal(text)
        increment = Decimal(tick)
        base = Decimal(origin)
    except InvalidOperation as exc:
        raise ValueError("oracle decimal parse") from exc
    if (
        not value.is_finite()
        or str(value) != text
        or (value.is_zero() and value.is_signed())
    ):
        raise ValueError("oracle noncanonical decimal")
    actual_scale = max(0, -value.as_tuple().exponent)
    if actual_scale != scale or increment <= 0 or (value - base) % increment != 0:
        raise ValueError("oracle scale/tick")
    return value


def _oracle_visible_ordinals(rows: tuple[Mapping[str, object], ...]) -> tuple[int, ...]:
    visible = tuple(
        int(row["ordinal"])
        for row in rows
        if row.get("committed") is True and row.get("completion") is True
    )
    if visible and visible != tuple(range(1, max(visible) + 1)):
        raise ValueError("visible ordinal gap")
    return visible


def _oracle_reconstruct(
    events: tuple[Mapping[str, object], ...],
    *,
    profile: str,
    decision_time: datetime,
    expected_depth: str,
    checkpoint: tuple[tuple[str, str, str], ...] | None = None,
) -> tuple[tuple[str, str, str], ...]:
    visible = tuple(event for event in events if event["completion"] is True)
    ordinals = tuple(int(event["ordinal"]) for event in visible)
    if ordinals != tuple(range(1, len(ordinals) + 1)):
        raise ValueError("ordinal order or completion gap")
    levels: dict[tuple[str, Decimal], Decimal] = {}
    identities: dict[tuple[object, ...], tuple[object, ...]] = {}
    last_sequence: int | None = None
    clock_domain: str | None = None
    anchored = False
    anchor_epoch: str | None = None
    anchor_subscription_id: str | None = None
    for event in visible:
        if (
            event["rights"] is not True
            or event["source"] is not True
            or event["parity"] is not True
        ):
            raise ValueError("source/rights/parity")
        if event["available_at"] > decision_time:
            raise ValueError("decision cutoff")
        if event["depth"] != expected_depth:
            raise ValueError("depth class")
        if clock_domain is None:
            clock_domain = str(event["clock_domain"])
        elif event["clock_domain"] != clock_domain:
            raise ValueError("clock domain")
        if profile == "POLYMARKET":
            identity = (event["epoch"], event["ordinal"])
        elif profile == "KALSHI":
            identity = (
                event["epoch"],
                event.get("subscription_id"),
                event.get("sequence_start"),
                event.get("sequence_end"),
            )
        else:
            identity = (
                event["epoch"],
                event.get("sequence_start"),
                event.get("sequence_end"),
            )
        content = tuple(
            tuple(sorted(item.items())) for item in event.get("levels", ())
        )
        if identity in identities:
            if identities[identity] != content:
                raise ValueError("conflicting duplicate")
            continue
        identities[identity] = content
        kind = event["kind"]
        if kind in {"SNAPSHOT", "REPLACEMENT"}:
            if profile == "GEMINI" and anchored and anchor_epoch == event["epoch"]:
                raise ValueError("Gemini same-epoch reanchor")
            levels.clear()
            anchored = True
            anchor_epoch = str(event["epoch"])
            if profile == "KALSHI":
                subscription_id = event.get("subscription_id")
                if type(subscription_id) is not str or not subscription_id:
                    raise ValueError("Kalshi subscription identity absent")
                anchor_subscription_id = subscription_id
        elif not anchored:
            raise ValueError("anchor required")
        if profile == "KALSHI" and event.get("subscription_id") != (
            anchor_subscription_id
        ):
            raise ValueError("Kalshi subscription identity changed")
        start = event.get("sequence_start")
        end = event.get("sequence_end")
        if start is not None and end is not None and int(start) > int(end):
            raise ValueError("reversed provider range")
        if profile == "GEMINI" and kind == "DELTA":
            if last_sequence is None or not (int(start) <= last_sequence + 1 <= int(end)):
                raise ValueError("Gemini range gap")
        if profile == "KALSHI" and kind == "DELTA":
            if last_sequence is None or int(start) != last_sequence + 1 or start != end:
                raise ValueError("Kalshi sequence gap")
        if profile == "POLYMARKET" and (start is not None or end is not None):
            raise ValueError("Retail sequence overclaim")
        if profile in {"GEMINI", "KALSHI"} and kind == "SNAPSHOT" and (
            start is None or end is None
        ):
            raise ValueError("sequenced anchor identity absent")
        if profile == "KALSHI" and kind == "SNAPSHOT" and start != end:
            raise ValueError("Kalshi snapshot sequence malformed")
        event_level_keys: set[tuple[str, Decimal]] = set()
        for raw in event.get("levels", ()):
            side = raw["side"]
            allowed = {
                "GEMINI": {"BID", "ASK"},
                "POLYMARKET": {"BID", "ASK"},
                "KALSHI": {"YES_BID", "NO_BID"},
            }[profile]
            if side not in allowed:
                raise ValueError("side")
            price = _oracle_decimal(raw["price"], raw["price_scale"], raw["tick"], raw["origin"])
            if price < 0 or price > 1:
                raise ValueError("price range")
            quantity = _oracle_decimal(
                raw["quantity"], raw["quantity_scale"], raw["quantity_tick"], "0"
            )
            key = (side, price)
            if key in event_level_keys:
                raise ValueError("duplicate price level")
            event_level_keys.add(key)
            if kind == "DELTA" and profile == "KALSHI":
                quantity = levels.get(key, Decimal(0)) + quantity
            if quantity < 0:
                raise ValueError("negative state")
            if quantity == 0:
                levels.pop(key, None)
            else:
                levels[key] = quantity
        if end is not None:
            last_sequence = int(end)
    bids = [price for (side, price) in levels if side == "BID"]
    asks = [price for (side, price) in levels if side == "ASK"]
    if bids and asks and max(bids) > min(asks):
        raise ValueError("crossed")
    yes = [price for (side, price) in levels if side == "YES_BID"]
    no = [price for (side, price) in levels if side == "NO_BID"]
    if yes and no and max(yes) + max(no) > Decimal(1):
        raise ValueError("complement crossed")
    result = tuple(
        (side, str(price), str(quantity))
        for (side, price), quantity in sorted(
            levels.items(), key=lambda item: (item[0][0], item[0][1])
        )
    )
    if checkpoint is not None and checkpoint != result:
        raise ValueError("checkpoint divergence")
    return result


def _oracle_base_events() -> tuple[dict[str, object], ...]:
    common = {
        "epoch": "EPOCH-1",
        "completion": True,
        "source": True,
        "rights": True,
        "parity": True,
        "depth": "INCREMENTAL_FROM_COMPLETE_ANCHOR",
        "available_at": _T0,
        "clock_domain": "PROCESS-1::CLOCK-1",
    }
    return (
        {
            **common,
            "ordinal": 1,
            "kind": "SNAPSHOT",
            "sequence_start": 1,
            "sequence_end": 1,
            "levels": (
                {"side": "BID", "price": "0.40", "price_scale": 2, "tick": "0.01", "origin": "0", "quantity": "2.00", "quantity_scale": 2, "quantity_tick": "0.01"},
                {"side": "ASK", "price": "0.60", "price_scale": 2, "tick": "0.01", "origin": "0", "quantity": "3.00", "quantity_scale": 2, "quantity_tick": "0.01"},
            ),
        },
        {
            **common,
            "ordinal": 2,
            "kind": "DELTA",
            "sequence_start": 1,
            "sequence_end": 2,
            "levels": (
                {"side": "BID", "price": "0.40", "price_scale": 2, "tick": "0.01", "origin": "0", "quantity": "0", "quantity_scale": 0, "quantity_tick": "0.01"},
            ),
        },
    )


def _case_independent_reconstruction_mutations() -> None:
    base = _oracle_base_events()
    expected = (("ASK", "0.60", "3.00"),)
    assert _oracle_reconstruct(
        base,
        profile="GEMINI",
        decision_time=_T0 + timedelta(seconds=1),
        expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
        checkpoint=expected,
    ) == expected
    exact_duplicate = deepcopy(base[1])
    exact_duplicate["ordinal"] = 3
    assert _oracle_reconstruct(
        (*base, exact_duplicate),
        profile="GEMINI",
        decision_time=_T0 + timedelta(seconds=1),
        expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
    ) == expected
    mutations: list[tuple[dict[str, object], int]] = []
    for index, change in (
        (0, {"sequence_start": 2}),
        (1, {"sequence_start": 4, "sequence_end": 4}),
        (1, {"clock_domain": "PROCESS-2::CLOCK-2"}),
        (1, {"rights": False}),
        (1, {"source": False}),
        (1, {"parity": False}),
        (1, {"depth": "BBO_ONLY"}),
        (1, {"available_at": _T0 + timedelta(seconds=2)}),
    ):
        mutations.append((change, index))
    for change, index in mutations:
        mutated = [deepcopy(event) for event in base]
        mutated[index].update(change)
        with pytest.raises(ValueError):
            _oracle_reconstruct(
                tuple(mutated),
                profile="GEMINI",
                decision_time=_T0 + timedelta(seconds=1),
                expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
            )
    with pytest.raises(ValueError):
        _oracle_reconstruct(
            (base[1], base[0]),
            profile="GEMINI",
            decision_time=_T0 + timedelta(seconds=1),
            expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
        )
    polymarket_common = {
        "epoch": "POLY-EPOCH-1",
        "completion": True,
        "source": True,
        "rights": True,
        "parity": True,
        "depth": "PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME",
        "available_at": _T0,
        "clock_domain": "PROCESS-1::CLOCK-1",
        "sequence_start": None,
        "sequence_end": None,
    }
    polymarket_events = (
        {
            **polymarket_common,
            "ordinal": 1,
            "kind": "REPLACEMENT",
            "levels": (
                {"side": "BID", "price": "0.40", "price_scale": 2, "tick": "0.01", "origin": "0", "quantity": "2.00", "quantity_scale": 2, "quantity_tick": "0.01"},
                {"side": "ASK", "price": "0.60", "price_scale": 2, "tick": "0.01", "origin": "0", "quantity": "3.00", "quantity_scale": 2, "quantity_tick": "0.01"},
            ),
        },
        {
            **polymarket_common,
            "ordinal": 2,
            "kind": "REPLACEMENT",
            "levels": (
                {"side": "ASK", "price": "0.61", "price_scale": 2, "tick": "0.01", "origin": "0", "quantity": "1.00", "quantity_scale": 2, "quantity_tick": "0.01"},
            ),
        },
    )
    assert _oracle_reconstruct(
        polymarket_events,
        profile="POLYMARKET",
        decision_time=_T0 + timedelta(seconds=1),
        expected_depth="PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME",
    ) == (("ASK", "0.61", "1.00"),)
    polymarket_overclaim = [deepcopy(event) for event in polymarket_events]
    polymarket_overclaim[1]["sequence_start"] = 2
    polymarket_overclaim[1]["sequence_end"] = 2
    with pytest.raises(ValueError):
        _oracle_reconstruct(
            tuple(polymarket_overclaim),
            profile="POLYMARKET",
            decision_time=_T0 + timedelta(seconds=1),
            expected_depth="PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME",
        )
    kalshi_common = {
        "epoch": "KALSHI-EPOCH-1",
        "subscription_id": "KALSHI-SUBSCRIPTION-1",
        "completion": True,
        "source": True,
        "rights": True,
        "parity": True,
        "depth": "INCREMENTAL_FROM_COMPLETE_ANCHOR",
        "available_at": _T0,
        "clock_domain": "PROCESS-1::CLOCK-1",
    }
    kalshi_events = (
        {
            **kalshi_common,
            "ordinal": 1,
            "kind": "SNAPSHOT",
            "sequence_start": 1,
            "sequence_end": 1,
            "levels": (
                {"side": "YES_BID", "price": "0.40", "price_scale": 2, "tick": "0.01", "origin": "0", "quantity": "2.00", "quantity_scale": 2, "quantity_tick": "0.01"},
                {"side": "NO_BID", "price": "0.50", "price_scale": 2, "tick": "0.01", "origin": "0", "quantity": "3.00", "quantity_scale": 2, "quantity_tick": "0.01"},
            ),
        },
        {
            **kalshi_common,
            "ordinal": 2,
            "kind": "DELTA",
            "sequence_start": 2,
            "sequence_end": 2,
            "levels": (
                {"side": "YES_BID", "price": "0.40", "price_scale": 2, "tick": "0.01", "origin": "0", "quantity": "-1.00", "quantity_scale": 2, "quantity_tick": "0.01"},
            ),
        },
    )
    kalshi_expected = (
        ("NO_BID", "0.50", "3.00"),
        ("YES_BID", "0.40", "1.00"),
    )
    assert _oracle_reconstruct(
        kalshi_events,
        profile="KALSHI",
        decision_time=_T0 + timedelta(seconds=1),
        expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
        checkpoint=kalshi_expected,
    ) == kalshi_expected
    kalshi_gap = [deepcopy(event) for event in kalshi_events]
    kalshi_gap[1]["sequence_start"] = 3
    kalshi_gap[1]["sequence_end"] = 3
    with pytest.raises(ValueError):
        _oracle_reconstruct(
            tuple(kalshi_gap),
            profile="KALSHI",
            decision_time=_T0 + timedelta(seconds=1),
            expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
        )
    kalshi_wrong_subscription = [deepcopy(event) for event in kalshi_events]
    kalshi_wrong_subscription[1]["subscription_id"] = "KALSHI-SUBSCRIPTION-2"
    with pytest.raises(ValueError):
        _oracle_reconstruct(
            tuple(kalshi_wrong_subscription),
            profile="KALSHI",
            decision_time=_T0 + timedelta(seconds=1),
            expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
        )
    kalshi_conflict = deepcopy(kalshi_events[1])
    kalshi_conflict["ordinal"] = 3
    kalshi_conflict["levels"] = (
        {**kalshi_conflict["levels"][0], "quantity": "-0.50"},
    )
    with pytest.raises(ValueError):
        _oracle_reconstruct(
            (*kalshi_events, kalshi_conflict),
            profile="KALSHI",
            decision_time=_T0 + timedelta(seconds=1),
            expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
        )
    for field, value in (
        ("side", "UNKNOWN_SIDE"),
        ("price", "0.405"),
        ("price_scale", 3),
        ("price", "-0.00"),
    ):
        mutated = [deepcopy(event) for event in base]
        changed_level = dict(mutated[0]["levels"][0])
        changed_level[field] = value
        mutated[0]["levels"] = (changed_level, mutated[0]["levels"][1])
        with pytest.raises(ValueError):
            _oracle_reconstruct(
                tuple(mutated),
                profile="GEMINI",
                decision_time=_T0 + timedelta(seconds=1),
                expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
            )
    conflict = deepcopy(base[1])
    conflict["ordinal"] = 3
    conflict["levels"] = (
        {**conflict["levels"][0], "quantity": "1.00", "quantity_scale": 2},
    )
    with pytest.raises(ValueError):
        _oracle_reconstruct(
            (*base, conflict),
            profile="GEMINI",
            decision_time=_T0 + timedelta(seconds=1),
            expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
        )
    incomplete = [deepcopy(event) for event in base]
    incomplete[1]["completion"] = False
    assert _oracle_reconstruct(
        tuple(incomplete),
        profile="GEMINI",
        decision_time=_T0 + timedelta(seconds=1),
        expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
    ) != expected
    with pytest.raises(ValueError):
        _oracle_reconstruct(
            base,
            profile="GEMINI",
            decision_time=_T0 + timedelta(seconds=1),
            expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
            checkpoint=(("ASK", "0.61", "3.00"),),
        )
    with pytest.raises(ValueError):
        _oracle_reconstruct(
            (base[1],),
            profile="GEMINI",
            decision_time=_T0 + timedelta(seconds=1),
            expected_depth="INCREMENTAL_FROM_COMPLETE_ANCHOR",
        )


def _git_paths(arguments: tuple[str, ...]) -> set[str]:
    completed = subprocess.run(
        ("git", *arguments),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()}


def _case_physical_anti_sprawl() -> None:
    committed = _git_paths(("diff", "--name-only", "--diff-filter=ACDMRTUXB", "origin/main...HEAD"))
    staged = _git_paths(("diff", "--cached", "--name-only", "--diff-filter=ACDMRTUXB"))
    unstaged = _git_paths(("diff", "--name-only", "--diff-filter=ACDMRTUXB"))
    untracked = _git_paths(("ls-files", "--others", "--exclude-standard"))
    changed = committed | staged | unstaged | untracked
    assert len(_ALLOWED_SEMANTIC_PATHS) == 30
    assert len(_ALLOWED_CENTRAL_CLOSURE_PATHS) == 8
    assert _ALLOWED_SEMANTIC_PATHS.isdisjoint(_ALLOWED_CENTRAL_CLOSURE_PATHS)
    normal_paths = _ALLOWED_SEMANTIC_PATHS | _ALLOWED_CENTRAL_CLOSURE_PATHS
    assert len(normal_paths) == 38
    assert _ALLOWED_CONDITIONAL_PATHS == {
        "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
    }
    assert normal_paths.isdisjoint(_ALLOWED_CONDITIONAL_PATHS)
    assert len(_ALLOWED_CANDIDATE_PATHS) == 39
    assert changed == _ALLOWED_CANDIDATE_PATHS
    added = (
        _git_paths(("diff", "--name-only", "--diff-filter=A", "origin/main...HEAD"))
        | _git_paths(("diff", "--cached", "--name-only", "--diff-filter=A"))
        | _git_paths(("diff", "--name-only", "--diff-filter=A"))
        | untracked
    )
    assert added == {"tests/source_evidence/test_s1_pit_data_phase_a_01.py"}
    source = Path("tests/source_evidence/test_s1_pit_data_phase_a_01.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    tests = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    assert len(tests) == 1
    pr132_target_source = Path(
        "tests/source_evidence/"
        "test_pr132_schema_enums_and_quantum_fields_match_policy_constants.py"
    ).read_text(encoding="utf-8")
    pr132_target_tree = ast.parse(pr132_target_source)
    pr132_target_tests = [
        node
        for node in pr132_target_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    assert len(pr132_target_tests) == 1
    adapter_source = Path(
        "src/qtt/stage1_prediction_markets/market_data_ingest/adapter.py"
    ).read_text(encoding="utf-8")
    adapter_tree = ast.parse(adapter_source)
    request_builders = [
        node
        for node in adapter_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "build_pit_read_requests_v2"
    ]
    assert len(request_builders) == 1
    assert not any(
        isinstance(node, ast.Constant) and node.value == "recovery_action"
        for node in ast.walk(request_builders[0])
    )
    assert not any(path.startswith(".github/workflows/") for path in changed)
    assert not any("run_validation_gates.py" in path for path in changed)
    assert not any("MasterPlan" in path or "Roadmap" in path for path in changed)
    assert {path for path in changed if path.endswith(".report.json")} == set(
        _ALLOWED_CONDITIONAL_PATHS
    )


def _build_cases() -> tuple[PITCase, ...]:
    return (
        PITCase("scope_and_legacy_isolation", _case_scope_and_legacy_isolation),
        PITCase("schema_and_serialization", _case_schema_and_serialization),
        PITCase("clock_and_leakage", _case_clock_and_leakage),
        PITCase("decimal_side_tick_and_book", _case_decimal_side_tick_and_book),
        PITCase("gemini", _case_gemini_algorithm),
        PITCase("polymarket_retail", _case_polymarket_retail_algorithm),
        PITCase("kalshi", _case_kalshi_algorithm),
        PITCase("freshness_and_availability", _case_freshness_and_availability),
        PITCase("commit_checkpoint_and_crash", _case_commit_checkpoint_and_crash),
        PITCase("rights_and_security", _case_rights_and_security),
        PITCase("formula_input_capability", _case_formula_input_capability),
        PITCase(
            "independent_reconstruction_mutations",
            _case_independent_reconstruction_mutations,
        ),
        PITCase("physical_anti_sprawl", _case_physical_anti_sprawl),
    )


PIT_CASES = _build_cases()


@pytest.mark.parametrize("case", PIT_CASES)
def test_s1_pit_data_phase_a_contract_matrix(case: PITCase) -> None:
    case.run()
