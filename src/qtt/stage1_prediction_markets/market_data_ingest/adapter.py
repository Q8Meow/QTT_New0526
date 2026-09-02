from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from src.qtt.stage1_prediction_markets.market_data_ingest.binding import (
    SelectedPITPublicDataContractV2,
)
from src.qtt.stage1_prediction_markets.market_data_ingest.source_dependency import (
    PIT_SOURCE_DEPENDENCIES_V2,
    adapter_input_class_for,
    dependency_lookup,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    SerializationSafetyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
    NoEffectFlagsV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PITClockSetV3,
    PITDataContractErrorV1,
    PITDepthClassV2,
    PITEventDispositionV1,
    PITEventKindV2,
    PITReasonCodeV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
    safe_json_loads,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    Stage1VenueProfileIdV1,
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


def _pit_adapter_text(value: object, name: str) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 for character in value)
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


def _pit_adapter_text_tuple(
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
    result = tuple(_pit_adapter_text(item, name) for item in value)
    if len(result) != len(set(result)):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
            f"{name} contains duplicate identities",
        )
    return result


def _pit_adapter_utc(value: object, name: str) -> datetime:
    if (
        type(value) is not datetime
        or value.tzinfo is None
        or value.utcoffset() is None
        or value.utcoffset().total_seconds() != 0
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
            f"{name} must be an aware UTC datetime",
        )
    return value.astimezone(UTC)


def _pit_adapter_nonnegative_int(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be a nonnegative exact integer",
        )
    return value


def _pit_source_field_class(value: str) -> str:
    snake = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value)
    return re.sub(r"[^a-z0-9]+", "_", snake.casefold()).strip("_")


def _pit_freeze_scalar_tree(value: object, *, name: str = "source tree") -> object:
    if value is None or type(value) in {str, int, bool}:
        return value
    if type(value) is float or type(value) is Decimal:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
            f"{name} rejects binary float and parsed numeric truth",
        )
    if isinstance(value, Mapping):
        frozen: dict[str, object] = {}
        for key, item in value.items():
            _pit_adapter_text(key, f"{name} key")
            normalized = _pit_source_field_class(key)
            if normalized in policy.PIT_PRIVATE_FIELD_DENYLIST_V1:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_PRIVATE_FIELD_CLASS_REJECTED,
                    "private/account/order field class is forbidden",
                )
            frozen[key] = _pit_freeze_scalar_tree(item, name=f"{name}.{key}")
        return MappingProxyType(frozen)
    if type(value) in {list, tuple}:
        return tuple(
            _pit_freeze_scalar_tree(item, name=f"{name}[]") for item in value
        )
    raise PITDataContractErrorV1(
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
        f"{name} contains unsupported {type(value).__name__}",
    )


def _pit_decimal_text(value: object, name: str) -> tuple[str, Decimal, int]:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", value) is None
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
            f"{name} must be exact source decimal text",
        )
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
            f"{name} is not an exact decimal",
        ) from exc
    if not parsed.is_finite() or str(parsed) != value:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
            f"{name} must be finite canonical decimal text",
        )
    exponent = parsed.as_tuple().exponent
    scale = -exponent if exponent < 0 else 0
    return value, parsed, scale


def _pit_exact_int_or_none(value: object, name: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be an exact nonnegative integer or absent",
        )
    return value


def _pit_validate_read_request_payload(
    profile_id: Stage1VenueProfileIdV1,
    read_action: policy.PITReadActionV1,
    path_or_channel: str,
    payload: tuple[tuple[str, object], ...],
) -> None:
    values = dict(payload)

    def require_keys(*keys: str) -> None:
        if set(values) != set(keys):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "request payload key set is not exact for its selected surface",
            )

    def validate_identifiers(name: str) -> tuple[str, ...]:
        identifiers = values.get(name)
        if type(identifiers) is not tuple:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                f"{name} must be an exact identifier tuple",
            )
        return _pit_adapter_text_tuple(
            identifiers,
            name,
            allow_empty=True,
        )

    if read_action is policy.PITReadActionV1.GET:
        fixed_by_path: dict[str, tuple[str, object]] = {
            "/historical/trades": ("provider_cutoff_required", True),
            "/portfolio/account_limits": ("scheduler_capacity_only", True),
        }
        allowed = {"market_identifiers"}
        if path_or_channel == "/historical/trades":
            allowed.update({"provider_cutoff_required", "provider_cursor_required"})
        elif path_or_channel == "/portfolio/account_limits":
            allowed.add("scheduler_capacity_only")
        if not set(values).issubset(allowed):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "GET request payload contains a noncanonical parameter",
            )
        if "market_identifiers" in values:
            validate_identifiers("market_identifiers")
        fixed = fixed_by_path.get(path_or_channel)
        if fixed is not None and values.get(fixed[0]) is not fixed[1]:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "GET request omits its exact safety/currentization parameter",
            )
        if path_or_channel == "/historical/trades" and values.get(
            "provider_cursor_required"
        ) is not True:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "historical trade request requires dynamic cutoff and cursor routing",
            )
        return
    if profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT:
        require_keys("action", "symbols", "snapshot")
        if values["action"] != "subscribe" or values["snapshot"] != -1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "Gemini subscription must request exact differential-depth anchoring",
            )
        validate_identifiers("symbols")
        return
    if profile_id is Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT:
        require_keys("action", "marketSlugs", "responseType")
        identifiers = validate_identifiers("marketSlugs")
        if (
            values["action"] != "subscribe"
            or values["responseType"] != "FULL"
            or len(identifiers) > 100
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "Retail subscription violates its exact primary request form",
            )
        return
    if read_action is policy.PITReadActionV1.WEBSOCKET_PONG:
        require_keys("command", "reply_to")
        if values != {"command": "pong", "reply_to": "server_ping"}:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "Kalshi heartbeat response must be an exact Pong descriptor",
            )
        return
    require_keys("command", "channels", "market_tickers", "use_yes_price")
    expected_command = (
        "get_snapshot"
        if read_action is policy.PITReadActionV1.WEBSOCKET_RECOVERY
        else "subscribe"
    )
    if (
        values["command"] != expected_command
        or values["channels"] != (path_or_channel,)
        or values["use_yes_price"] is not True
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
            "Kalshi descriptor must preserve command, channel, and YES-price convention",
        )
    validate_identifiers("market_tickers")


@dataclass(frozen=True, slots=True)
class PITReadRequestV1:
    request_id: str
    profile_id: Stage1VenueProfileIdV1
    event_kind: PITEventKindV2
    access_class: policy.PITAccessClassV1
    read_action: policy.PITReadActionV1
    host: str
    path_or_channel: str
    query_or_subscription_payload: tuple[tuple[str, object], ...]
    source_contract_version: str
    source_dependency_ref: str
    credential_alias_required: bool
    no_write: bool
    no_private_state: bool
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1 or self.profile_id not in (
            policy.PIT_SELECTED_SCOPE_V2.selected_profile_ids
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "request profile is outside selected scope",
            )
        if type(self.event_kind) is not PITEventKindV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "request event kind has the wrong exact type",
            )
        if type(self.access_class) is not policy.PITAccessClassV1 or type(
            self.read_action
        ) is not policy.PITReadActionV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
                "request access/action has the wrong exact type",
            )
        for name in (
            "request_id",
            "host",
            "path_or_channel",
            "source_contract_version",
            "source_dependency_ref",
        ):
            _pit_adapter_text(getattr(self, name), name)
        if type(self.query_or_subscription_payload) is not tuple or any(
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            for item in self.query_or_subscription_payload
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "request payload must be an exact ordered key/value tuple",
            )
        keys = tuple(item[0] for item in self.query_or_subscription_payload)
        _pit_adapter_text_tuple(keys, "request payload keys", allow_empty=True)
        _pit_validate_read_request_payload(
            self.profile_id,
            self.read_action,
            self.path_or_channel,
            self.query_or_subscription_payload,
        )
        frozen_payload = tuple(
            (
                key,
                _pit_freeze_scalar_tree(value, name=f"request payload {key}"),
            )
            for key, value in self.query_or_subscription_payload
        )
        object.__setattr__(self, "query_or_subscription_payload", frozen_payload)
        _pit_validate_read_request_payload(
            self.profile_id,
            self.read_action,
            self.path_or_channel,
            frozen_payload,
        )
        for name in ("credential_alias_required", "no_write", "no_private_state"):
            if type(getattr(self, name)) is not bool:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact boolean",
                )
        if not self.no_write or not self.no_private_state:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "PIT request cannot authorize write or private state",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "PIT request must carry exact NO_EFFECTS_V1",
            )


@dataclass(frozen=True, slots=True)
class PITRawFrameV1:
    frame_id: str
    profile_id: Stage1VenueProfileIdV1
    connection_epoch: str
    capture_session_id: str
    wire_dialect: str
    channel: str
    raw_utf8_text_or_none: str | None
    parsed_source_scalar_tree_or_none: object | None
    qtt_received_at_utc: datetime
    qtt_received_monotonic_ns: int
    process_epoch_id: str
    monotonic_clock_id: str
    wall_clock_source_id: str
    clock_quality_receipt_ref: str
    wall_clock_uncertainty_ns: int
    source_contract_refs: tuple[str, ...]
    contains_credential: bool = False
    contains_signature: bool = False
    contains_authorization_header: bool = False
    contains_private_state: bool = False

    def __post_init__(self) -> None:
        if type(self.profile_id) is not Stage1VenueProfileIdV1 or self.profile_id not in (
            policy.PIT_SELECTED_SCOPE_V2.selected_profile_ids
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "raw frame profile is outside selected scope",
            )
        for name in (
            "frame_id",
            "connection_epoch",
            "capture_session_id",
            "wire_dialect",
            "channel",
            "process_epoch_id",
            "monotonic_clock_id",
            "wall_clock_source_id",
            "clock_quality_receipt_ref",
        ):
            _pit_adapter_text(getattr(self, name), name)
        raw_present = self.raw_utf8_text_or_none is not None
        tree_present = self.parsed_source_scalar_tree_or_none is not None
        if raw_present == tree_present:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "raw frame requires exactly one raw text or parsed scalar tree",
            )
        if raw_present:
            _pit_adapter_text(self.raw_utf8_text_or_none, "raw_utf8_text_or_none")
            try:
                self.raw_utf8_text_or_none.encode("utf-8", errors="strict")
            except UnicodeError as exc:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    "raw frame text is not strict UTF-8",
                ) from exc
        else:
            object.__setattr__(
                self,
                "parsed_source_scalar_tree_or_none",
                _pit_freeze_scalar_tree(self.parsed_source_scalar_tree_or_none),
            )
        object.__setattr__(
            self,
            "qtt_received_at_utc",
            _pit_adapter_utc(self.qtt_received_at_utc, "qtt_received_at_utc"),
        )
        _pit_adapter_nonnegative_int(
            self.qtt_received_monotonic_ns,
            "qtt_received_monotonic_ns",
        )
        _pit_adapter_nonnegative_int(
            self.wall_clock_uncertainty_ns,
            "wall_clock_uncertainty_ns",
        )
        _pit_adapter_text_tuple(
            self.source_contract_refs,
            "source_contract_refs",
            allow_empty=False,
        )
        for name in (
            "contains_credential",
            "contains_signature",
            "contains_authorization_header",
            "contains_private_state",
        ):
            if type(getattr(self, name)) is not bool:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_PRIVATE_FIELD_CLASS_REJECTED,
                    f"{name} must be an exact boolean",
                )
            if getattr(self, name):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_PRIVATE_FIELD_CLASS_REJECTED,
                    "credential/signature/header/private state is forbidden",
                )


@dataclass(frozen=True, slots=True)
class _PITBookLevelV2:
    source_side: str
    canonical_side: str
    price_text: str
    price: Decimal
    quantity_text: str
    quantity: Decimal
    price_scale: int
    quantity_scale: int
    price_increment: Decimal
    price_origin: Decimal
    quantity_increment_or_none: Decimal | None

    def __post_init__(self) -> None:
        _pit_adapter_text(self.source_side, "source_side")
        _pit_adapter_text(self.canonical_side, "canonical_side")
        price_text, price, price_scale = _pit_decimal_text(
            self.price_text, "price_text"
        )
        quantity_text, quantity, quantity_scale = _pit_decimal_text(
            self.quantity_text, "quantity_text"
        )
        if (
            type(self.price) is not Decimal
            or self.price != price
            or type(self.quantity) is not Decimal
            or self.quantity != quantity
            or type(self.price_scale) is not int
            or self.price_scale != price_scale
            or type(self.quantity_scale) is not int
            or self.quantity_scale != quantity_scale
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
                "book level text, Decimal, and scale must agree exactly",
            )
        if quantity < 0:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
                "book state quantity cannot be negative",
            )
        if price.is_zero() and price.is_signed():
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
                "book level price cannot use a negative-zero representation",
            )
        if quantity.is_signed():
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
                "book state quantity cannot use a negative-zero representation",
            )
        if (
            type(self.price_increment) is not Decimal
            or not self.price_increment.is_finite()
            or self.price_increment <= 0
            or type(self.price_origin) is not Decimal
            or not self.price_origin.is_finite()
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TICK_GRID_INVALID,
                "price increment/origin must be finite exact Decimal values",
            )
        if (price - self.price_origin) % self.price_increment != 0:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TICK_GRID_INVALID,
                "book level price is off its exact origin/increment grid",
            )
        if self.quantity_increment_or_none is not None:
            if (
                type(self.quantity_increment_or_none) is not Decimal
                or not self.quantity_increment_or_none.is_finite()
                or self.quantity_increment_or_none <= 0
                or quantity % self.quantity_increment_or_none != 0
            ):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
                    "book level quantity is off its exact increment grid",
                )
        object.__setattr__(self, "price_text", price_text)
        object.__setattr__(self, "quantity_text", quantity_text)


@dataclass(frozen=True, slots=True)
class _PITAbsoluteLevelUpdateV2:
    source_side: str
    canonical_side: str
    price_text: str
    price: Decimal
    absolute_quantity_text: str
    absolute_quantity: Decimal
    price_scale: int
    quantity_scale: int
    price_increment: Decimal
    price_origin: Decimal
    quantity_increment_or_none: Decimal | None

    def __post_init__(self) -> None:
        level = _PITBookLevelV2(
            source_side=self.source_side,
            canonical_side=self.canonical_side,
            price_text=self.price_text,
            price=self.price,
            quantity_text=self.absolute_quantity_text,
            quantity=self.absolute_quantity,
            price_scale=self.price_scale,
            quantity_scale=self.quantity_scale,
            price_increment=self.price_increment,
            price_origin=self.price_origin,
            quantity_increment_or_none=self.quantity_increment_or_none,
        )
        object.__setattr__(self, "price_text", level.price_text)
        object.__setattr__(
            self, "absolute_quantity_text", level.quantity_text
        )


@dataclass(frozen=True, slots=True)
class _PITDeltaLevelV2:
    source_side: str
    canonical_side: str
    price_text: str
    price: Decimal
    quantity_delta_text: str
    quantity_delta: Decimal
    price_scale: int
    quantity_scale: int
    price_increment: Decimal
    price_origin: Decimal
    quantity_increment_or_none: Decimal | None

    def __post_init__(self) -> None:
        _pit_adapter_text(self.source_side, "source_side")
        _pit_adapter_text(self.canonical_side, "canonical_side")
        _, price, price_scale = _pit_decimal_text(self.price_text, "price_text")
        _, quantity_delta, quantity_scale = _pit_decimal_text(
            self.quantity_delta_text, "quantity_delta_text"
        )
        if (
            type(self.price) is not Decimal
            or self.price != price
            or type(self.quantity_delta) is not Decimal
            or self.quantity_delta != quantity_delta
            or type(self.price_scale) is not int
            or self.price_scale != price_scale
            or type(self.quantity_scale) is not int
            or self.quantity_scale != quantity_scale
            or type(self.price_increment) is not Decimal
            or not self.price_increment.is_finite()
            or self.price_increment <= 0
            or type(self.price_origin) is not Decimal
            or not self.price_origin.is_finite()
            or (price - self.price_origin) % self.price_increment != 0
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
                "signed delta text, Decimal, scale, and grid must agree exactly",
            )
        if quantity_delta.is_zero() and quantity_delta.is_signed():
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
                "signed delta cannot use a negative-zero representation",
            )
        if price.is_zero() and price.is_signed():
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DECIMAL_OR_SCALE_INVALID,
                "signed delta price cannot use a negative-zero representation",
            )
        if self.quantity_increment_or_none is not None and (
            type(self.quantity_increment_or_none) is not Decimal
            or not self.quantity_increment_or_none.is_finite()
            or self.quantity_increment_or_none <= 0
            or quantity_delta % self.quantity_increment_or_none != 0
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
                "signed delta is off its exact quantity-increment grid",
            )


@dataclass(frozen=True, slots=True)
class _PITBookSnapshotPayloadV2:
    levels: tuple[_PITBookLevelV2, ...]
    provider_sequence: int
    provider_subscription_id_or_none: str | None
    complete_provider_snapshot: bool

    def __post_init__(self) -> None:
        if type(self.levels) is not tuple or any(
            type(value) is not _PITBookLevelV2 for value in self.levels
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "snapshot levels must be exact typed values",
            )
        _pit_adapter_nonnegative_int(self.provider_sequence, "provider_sequence")
        if self.provider_subscription_id_or_none is not None:
            _pit_adapter_text(
                self.provider_subscription_id_or_none,
                "provider_subscription_id_or_none",
            )
        if type(self.complete_provider_snapshot) is not bool or not self.complete_provider_snapshot:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_ANCHOR_REQUIRED,
                "book snapshot payload must be complete",
            )


@dataclass(frozen=True, slots=True)
class _PITBookAbsoluteUpdatePayloadV2:
    updates: tuple[_PITAbsoluteLevelUpdateV2, ...]
    first_provider_sequence: int
    last_provider_sequence: int

    def __post_init__(self) -> None:
        if type(self.updates) is not tuple or any(
            type(value) is not _PITAbsoluteLevelUpdateV2 for value in self.updates
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "absolute updates must be exact typed values",
            )
        first = _pit_adapter_nonnegative_int(
            self.first_provider_sequence, "first_provider_sequence"
        )
        last = _pit_adapter_nonnegative_int(
            self.last_provider_sequence, "last_provider_sequence"
        )
        if first > last:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SEQUENCE_GAP,
                "provider update range is malformed",
            )


@dataclass(frozen=True, slots=True)
class _PITBookDeltaPayloadV2:
    deltas: tuple[_PITDeltaLevelV2, ...]
    provider_sequence: int
    provider_subscription_id: str

    def __post_init__(self) -> None:
        if type(self.deltas) is not tuple or any(
            type(value) is not _PITDeltaLevelV2 for value in self.deltas
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "signed deltas must be exact typed values",
            )
        _pit_adapter_nonnegative_int(self.provider_sequence, "provider_sequence")
        _pit_adapter_text(
            self.provider_subscription_id,
            "provider_subscription_id",
        )


@dataclass(frozen=True, slots=True)
class _PITBookReplacementPayloadV2:
    levels: tuple[_PITBookLevelV2, ...]
    surface_class: str
    provider_sequence_unavailable: bool
    source_lifecycle_state: str | int
    market_sides_json: str
    order_price_min_tick_size_text: str

    def __post_init__(self) -> None:
        if type(self.levels) is not tuple or any(
            type(value) is not _PITBookLevelV2 for value in self.levels
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "replacement levels must be exact typed values",
            )
        _pit_adapter_text(self.surface_class, "surface_class")
        if type(self.provider_sequence_unavailable) is not bool or not (
            self.provider_sequence_unavailable
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE,
                "Polymarket replacement must declare provider sequence unavailable",
            )
        if type(self.source_lifecycle_state) is str:
            _pit_adapter_text(self.source_lifecycle_state, "source_lifecycle_state")
        elif type(self.source_lifecycle_state) is not int or self.source_lifecycle_state < 0:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "Retail lifecycle state must be an exact string or nonnegative integer enum",
            )
        _pit_adapter_text(self.market_sides_json, "market_sides_json")
        try:
            market_sides = safe_json_loads(self.market_sides_json)
        except SerializationSafetyError as exc:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "Retail marketSides custody is not safe canonical JSON",
            ) from exc
        if (
            type(market_sides) is not list
            or len(market_sides) < 2
            or any(type(side) is not dict or not side for side in market_sides)
            or len({deterministic_json(side) for side in market_sides})
            != len(market_sides)
            or deterministic_json(market_sides) != self.market_sides_json
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "Retail marketSides must be a canonical array of unique nonempty mappings",
            )
        _, tick, _ = _pit_decimal_text(
            self.order_price_min_tick_size_text,
            "order_price_min_tick_size_text",
        )
        if tick <= 0:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TICK_GRID_INVALID,
                "Retail per-market price tick must be positive",
            )


def _pit_validate_typed_fields_payload(
    event_kind: object,
    fields: object,
    *,
    expected_event_kind: PITEventKindV2,
) -> tuple[tuple[str, object], ...]:
    if type(event_kind) is not PITEventKindV2 or event_kind is not expected_event_kind:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "typed scalar payload discriminator does not match its exact type",
        )
    if type(fields) is not tuple or not fields or any(
        type(item) is not tuple
        or len(item) != 2
        or type(item[0]) is not str
        for item in fields
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "typed scalar payload requires ordered fields",
        )
    keys = tuple(key for key, _ in fields)
    _pit_adapter_text_tuple(keys, "typed payload fields", allow_empty=False)
    return tuple(
        (key, _pit_freeze_scalar_tree(value, name=f"typed payload {key}"))
        for key, value in fields
    )


@dataclass(frozen=True, slots=True)
class _PITCatalogPayloadV2:
    event_kind: PITEventKindV2
    fields: tuple[tuple[str, object], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fields",
            _pit_validate_typed_fields_payload(
                self.event_kind,
                self.fields,
                expected_event_kind=PITEventKindV2.CATALOG,
            ),
        )


@dataclass(frozen=True, slots=True)
class _PITLifecyclePayloadV2:
    event_kind: PITEventKindV2
    fields: tuple[tuple[str, object], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fields",
            _pit_validate_typed_fields_payload(
                self.event_kind,
                self.fields,
                expected_event_kind=PITEventKindV2.LIFECYCLE,
            ),
        )


@dataclass(frozen=True, slots=True)
class _PITBBOPayloadV2:
    event_kind: PITEventKindV2
    fields: tuple[tuple[str, object], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fields",
            _pit_validate_typed_fields_payload(
                self.event_kind,
                self.fields,
                expected_event_kind=PITEventKindV2.BBO,
            ),
        )


@dataclass(frozen=True, slots=True)
class _PITTradePayloadV2:
    event_kind: PITEventKindV2
    fields: tuple[tuple[str, object], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fields",
            _pit_validate_typed_fields_payload(
                self.event_kind,
                self.fields,
                expected_event_kind=PITEventKindV2.TRADE,
            ),
        )


@dataclass(frozen=True, slots=True)
class _PITSettlementPayloadV2:
    event_kind: PITEventKindV2
    fields: tuple[tuple[str, object], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fields",
            _pit_validate_typed_fields_payload(
                self.event_kind,
                self.fields,
                expected_event_kind=PITEventKindV2.SETTLEMENT,
            ),
        )


@dataclass(frozen=True, slots=True)
class _PITReferencePricePayloadV2:
    event_kind: PITEventKindV2
    fields: tuple[tuple[str, object], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fields",
            _pit_validate_typed_fields_payload(
                self.event_kind,
                self.fields,
                expected_event_kind=PITEventKindV2.REFERENCE_PRICE,
            ),
        )


@dataclass(frozen=True, slots=True)
class _PITHeartbeatPayloadV2:
    event_kind: PITEventKindV2
    fields: tuple[tuple[str, object], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fields",
            _pit_validate_typed_fields_payload(
                self.event_kind,
                self.fields,
                expected_event_kind=PITEventKindV2.HEARTBEAT,
            ),
        )


@dataclass(frozen=True, slots=True)
class _PITSourceStatusPayloadV2:
    event_kind: PITEventKindV2
    fields: tuple[tuple[str, object], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "fields",
            _pit_validate_typed_fields_payload(
                self.event_kind,
                self.fields,
                expected_event_kind=PITEventKindV2.SOURCE_STATUS,
            ),
        )


_PITCanonicalPayloadV2 = (
    _PITBookSnapshotPayloadV2
    | _PITBookAbsoluteUpdatePayloadV2
    | _PITBookDeltaPayloadV2
    | _PITBookReplacementPayloadV2
    | _PITCatalogPayloadV2
    | _PITLifecyclePayloadV2
    | _PITBBOPayloadV2
    | _PITTradePayloadV2
    | _PITSettlementPayloadV2
    | _PITReferencePricePayloadV2
    | _PITHeartbeatPayloadV2
    | _PITSourceStatusPayloadV2
)


_PIT_TYPED_PAYLOAD_TYPE_BY_EVENT_KIND_V2 = MappingProxyType(
    {
        PITEventKindV2.CATALOG: _PITCatalogPayloadV2,
        PITEventKindV2.LIFECYCLE: _PITLifecyclePayloadV2,
        PITEventKindV2.BBO: _PITBBOPayloadV2,
        PITEventKindV2.TRADE: _PITTradePayloadV2,
        PITEventKindV2.SETTLEMENT: _PITSettlementPayloadV2,
        PITEventKindV2.REFERENCE_PRICE: _PITReferencePricePayloadV2,
        PITEventKindV2.HEARTBEAT: _PITHeartbeatPayloadV2,
        PITEventKindV2.SOURCE_STATUS: _PITSourceStatusPayloadV2,
    }
)


def _pit_payload_matches_event_kind(
    payload: object,
    event_kind: PITEventKindV2,
) -> bool:
    if event_kind is PITEventKindV2.BOOK_SNAPSHOT:
        return type(payload) is _PITBookSnapshotPayloadV2
    if event_kind is PITEventKindV2.BOOK_DELTA:
        return type(payload) in {
            _PITBookAbsoluteUpdatePayloadV2,
            _PITBookDeltaPayloadV2,
        }
    if event_kind is PITEventKindV2.BOOK_REPLACEMENT:
        return type(payload) is _PITBookReplacementPayloadV2
    expected_type = _PIT_TYPED_PAYLOAD_TYPE_BY_EVENT_KIND_V2.get(event_kind)
    return (
        expected_type is not None
        and type(payload) is expected_type
        and payload.event_kind is event_kind
    )


@dataclass(frozen=True, slots=True)
class PITCanonicalEventCandidateV2:
    event_record_id: str
    profile_id: Stage1VenueProfileIdV1
    market_id: str
    instrument_id: str
    channel: str
    connection_epoch: str
    capture_session_id: str
    event_kind: PITEventKindV2
    schema_version: str
    wire_dialect: str
    source_currentization_version: str
    provider_sequence_start_or_none: int | None
    provider_sequence_end_or_none: int | None
    provider_trade_id_or_none: str | None
    provider_subscription_id_or_none: str | None
    payload: _PITCanonicalPayloadV2
    depth_class: PITDepthClassV2
    provider_event_time_utc_or_none: datetime | None
    provider_publication_time_utc_or_none: datetime | None
    qtt_received_at_utc: datetime
    qtt_received_monotonic_ns: int
    qtt_parse_completed_at_utc: datetime
    qtt_parse_completed_monotonic_ns: int
    process_epoch_id: str
    monotonic_clock_id: str
    wall_clock_source_id: str
    clock_quality_receipt_ref: str
    wall_clock_uncertainty_ns: int
    source_receipt_ref: str
    rights_receipt_ref: str
    raw_frame_ref: str
    no_private_state_authority: bool
    no_order_authority: bool
    no_profit_claim: bool
    no_qpu_effect: bool
    no_llm_effect: bool
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        if self.schema_version != "PIT_CANONICAL_EVENT_V2":
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "event candidate schema version is not exact V2",
            )
        if type(self.profile_id) is not Stage1VenueProfileIdV1 or self.profile_id not in (
            policy.PIT_SELECTED_SCOPE_V2.selected_profile_ids
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "event candidate profile is outside selected scope",
            )
        for name in (
            "event_record_id",
            "market_id",
            "instrument_id",
            "channel",
            "connection_epoch",
            "capture_session_id",
            "schema_version",
            "wire_dialect",
            "source_currentization_version",
            "process_epoch_id",
            "monotonic_clock_id",
            "wall_clock_source_id",
            "clock_quality_receipt_ref",
            "source_receipt_ref",
            "rights_receipt_ref",
            "raw_frame_ref",
        ):
            _pit_adapter_text(getattr(self, name), name)
        if type(self.event_kind) is not PITEventKindV2 or not (
            _pit_payload_matches_event_kind(self.payload, self.event_kind)
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "event kind and exact typed payload discriminator differ",
            )
        if type(self.depth_class) is not PITDepthClassV2:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TOP_LEVEL_DEPTH_ONLY,
                "candidate depth class has the wrong exact type",
            )
        for name in (
            "provider_sequence_start_or_none",
            "provider_sequence_end_or_none",
        ):
            _pit_exact_int_or_none(getattr(self, name), name)
        if (
            self.provider_sequence_start_or_none is not None
            and self.provider_sequence_end_or_none is not None
            and self.provider_sequence_start_or_none
            > self.provider_sequence_end_or_none
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SEQUENCE_GAP,
                "candidate provider sequence range is malformed",
            )
        for name in (
            "provider_trade_id_or_none",
            "provider_subscription_id_or_none",
        ):
            value = getattr(self, name)
            if value is not None:
                _pit_adapter_text(value, name)
        for name in (
            "provider_event_time_utc_or_none",
            "provider_publication_time_utc_or_none",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _pit_adapter_utc(value, name))
        if self.provider_publication_time_utc_or_none is not None:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_PROVIDER_PUBLICATION_TIME_UNAVAILABLE,
                "selected provider contracts expose no distinct publication time",
            )
        for name in ("qtt_received_at_utc", "qtt_parse_completed_at_utc"):
            object.__setattr__(self, name, _pit_adapter_utc(getattr(self, name), name))
        received = _pit_adapter_nonnegative_int(
            self.qtt_received_monotonic_ns,
            "qtt_received_monotonic_ns",
        )
        parsed = _pit_adapter_nonnegative_int(
            self.qtt_parse_completed_monotonic_ns,
            "qtt_parse_completed_monotonic_ns",
        )
        if parsed < received:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
                "parse-complete monotonic time precedes ingress",
            )
        _pit_adapter_nonnegative_int(
            self.wall_clock_uncertainty_ns,
            "wall_clock_uncertainty_ns",
        )
        for name in (
            "no_private_state_authority",
            "no_order_authority",
            "no_profit_claim",
            "no_qpu_effect",
            "no_llm_effect",
        ):
            if type(getattr(self, name)) is not bool or not getattr(self, name):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                    f"{name} must be exact True",
                )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "event candidate must carry exact NO_EFFECTS_V1",
            )


@dataclass(frozen=True, slots=True)
class PITCanonicalEventV2:
    event_record_id: str
    profile_id: Stage1VenueProfileIdV1
    market_id: str
    instrument_id: str
    channel: str
    connection_epoch: str
    capture_session_id: str
    committed_event_ordinal: int
    event_kind: PITEventKindV2
    schema_version: str
    wire_dialect: str
    source_currentization_version: str
    provider_sequence_start_or_none: int | None
    provider_sequence_end_or_none: int | None
    provider_trade_id_or_none: str | None
    provider_subscription_id_or_none: str | None
    payload: _PITCanonicalPayloadV2
    depth_class: PITDepthClassV2
    clocks: PITClockSetV3
    pre_state_ref: str
    post_state_ref: str
    event_disposition: PITEventDispositionV1
    failure_reason_or_none: PITReasonCodeV1 | None
    rights_receipt_ref: str
    source_receipt_ref: str
    commit_completion_ref: str
    prior_event_ref_or_none: str | None
    checkpoint_ref_or_none: str | None
    recovery_receipt_ref_or_none: str | None
    no_private_state_authority: bool
    no_order_authority: bool
    no_profit_claim: bool
    no_qpu_effect: bool
    no_llm_effect: bool
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        if self.schema_version != "PIT_CANONICAL_EVENT_V2":
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "final event schema version is not exact V2",
            )
        for name in (
            "event_record_id",
            "market_id",
            "instrument_id",
            "channel",
            "connection_epoch",
            "capture_session_id",
            "schema_version",
            "wire_dialect",
            "source_currentization_version",
            "pre_state_ref",
            "post_state_ref",
            "rights_receipt_ref",
            "source_receipt_ref",
            "commit_completion_ref",
        ):
            _pit_adapter_text(getattr(self, name), name)
        if type(self.profile_id) is not Stage1VenueProfileIdV1 or self.profile_id not in (
            policy.PIT_SELECTED_SCOPE_V2.selected_profile_ids
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "final event profile is outside selected scope",
            )
        if type(self.committed_event_ordinal) is not int or self.committed_event_ordinal < 1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_DURABLE_COMMIT_INCOMPLETE,
                "final event requires a positive committed ordinal",
            )
        if type(self.event_kind) is not PITEventKindV2 or not (
            _pit_payload_matches_event_kind(self.payload, self.event_kind)
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "final event kind and payload discriminator differ",
            )
        if type(self.depth_class) is not PITDepthClassV2 or type(
            self.clocks
        ) is not PITClockSetV3:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "final event depth/clocks have wrong exact types",
            )
        for name in (
            "provider_sequence_start_or_none",
            "provider_sequence_end_or_none",
        ):
            _pit_exact_int_or_none(getattr(self, name), name)
        if (
            self.provider_sequence_start_or_none is not None
            and self.provider_sequence_end_or_none is not None
            and self.provider_sequence_start_or_none
            > self.provider_sequence_end_or_none
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SEQUENCE_GAP,
                "final event provider sequence range is malformed",
            )
        for name in (
            "provider_trade_id_or_none",
            "provider_subscription_id_or_none",
            "prior_event_ref_or_none",
            "checkpoint_ref_or_none",
            "recovery_receipt_ref_or_none",
        ):
            value = getattr(self, name)
            if value is not None:
                _pit_adapter_text(value, name)
        if type(self.event_disposition) is not PITEventDispositionV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "final event disposition has the wrong exact type",
            )
        if self.failure_reason_or_none is not None and type(
            self.failure_reason_or_none
        ) is not PITReasonCodeV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "final event failure reason has the wrong exact type",
            )
        if self.event_disposition is PITEventDispositionV1.COMMITTED:
            if self.failure_reason_or_none is not None:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_CONFLICTING_DUPLICATE,
                    "committed event cannot carry a failure reason",
                )
        elif self.failure_reason_or_none is None:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "noncommitted final event requires a failure reason",
            )
        for name in (
            "no_private_state_authority",
            "no_order_authority",
            "no_profit_claim",
            "no_qpu_effect",
            "no_llm_effect",
        ):
            if type(getattr(self, name)) is not bool or not getattr(self, name):
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                    f"{name} must be exact True",
                )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "final event must carry exact NO_EFFECTS_V1",
            )


def build_pit_read_requests_v2(
    contracts: tuple[SelectedPITPublicDataContractV2, ...],
    *,
    market_identifiers_by_profile: Mapping[
        Stage1VenueProfileIdV1, tuple[str, ...]
    ]
    | None = None,
) -> tuple[PITReadRequestV1, ...]:
    """Build immutable request descriptors only; this function performs no I/O."""

    if type(contracts) is not tuple or any(
        type(value) is not SelectedPITPublicDataContractV2 for value in contracts
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "contracts must be exact SelectedPITPublicDataContractV2 values",
        )
    contract_by_profile = {value.profile_id: value for value in contracts}
    expected_profiles = set(policy.PIT_SELECTED_SCOPE_V2.serialization)
    if len(contract_by_profile) != len(contracts) or set(contract_by_profile) != (
        expected_profiles
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "contract set must equal the exact selected profile set",
        )
    supplied_ids = market_identifiers_by_profile or {}
    if not isinstance(supplied_ids, Mapping) or any(
        type(profile_id) is not Stage1VenueProfileIdV1
        or profile_id not in expected_profiles
        or type(values) is not tuple
        for profile_id, values in supplied_ids.items()
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "market identifier mapping contains an excluded or malformed profile",
        )
    normalized_ids: dict[Stage1VenueProfileIdV1, tuple[str, ...]] = {}
    for profile_id in policy.PIT_SELECTED_SCOPE_V2.serialization:
        values = supplied_ids.get(profile_id, ())
        normalized_ids[profile_id] = _pit_adapter_text_tuple(
            values,
            f"market identifiers for {profile_id.value}",
            allow_empty=True,
        )
    if (
        len(
            normalized_ids[Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT]
        )
        > 100
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_ENDPOINT_NOT_ALLOWLISTED,
            "Polymarket Retail subscriptions permit no more than 100 market slugs",
        )
    requests: list[PITReadRequestV1] = []
    for dependency in PIT_SOURCE_DEPENDENCIES_V2:
        contract = contract_by_profile[dependency.profile_id]
        identifiers = normalized_ids[dependency.profile_id]
        if dependency.read_action is policy.PITReadActionV1.GET:
            payload_parts: list[tuple[str, object]] = []
            if identifiers:
                payload_parts.append(("market_identifiers", identifiers))
            if dependency.path_or_channel == "/historical/trades":
                payload_parts.extend(
                    (
                        ("provider_cutoff_required", True),
                        ("provider_cursor_required", True),
                    )
                )
            elif dependency.path_or_channel == "/portfolio/account_limits":
                payload_parts.append(("scheduler_capacity_only", True))
            payload = tuple(payload_parts)
        elif dependency.profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT:
            payload = (
                ("action", "subscribe"),
                ("symbols", identifiers),
                ("snapshot", -1),
            )
        elif dependency.profile_id is (
            Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT
        ):
            payload = (
                ("action", "subscribe"),
                ("marketSlugs", identifiers),
                ("responseType", "FULL"),
            )
        elif dependency.read_action is policy.PITReadActionV1.WEBSOCKET_PONG:
            payload = (
                ("command", "pong"),
                ("reply_to", "server_ping"),
            )
        elif dependency.read_action is policy.PITReadActionV1.WEBSOCKET_RECOVERY:
            payload = (
                ("command", "get_snapshot"),
                ("channels", (dependency.path_or_channel,)),
                ("market_tickers", identifiers),
                ("use_yes_price", True),
            )
        else:
            payload = (
                ("command", "subscribe"),
                ("channels", (dependency.path_or_channel,)),
                ("market_tickers", identifiers),
                ("use_yes_price", True),
            )
        requests.append(
            PITReadRequestV1(
                request_id=(
                    f"S1-PIT-READ::{dependency.profile_id.value}::"
                    f"{dependency.event_kind.value}::{dependency.access_class.value}"
                ),
                profile_id=dependency.profile_id,
                event_kind=dependency.event_kind,
                access_class=dependency.access_class,
                read_action=dependency.read_action,
                host=dependency.host,
                path_or_channel=dependency.path_or_channel,
                query_or_subscription_payload=payload,
                source_contract_version=contract.source_contract_version,
                source_dependency_ref=dependency.dependency_id,
                credential_alias_required=dependency.credential_alias_required,
                no_write=True,
                no_private_state=True,
            )
        )
    return tuple(requests)


def _pit_frame_tree(frame: PITRawFrameV1) -> Mapping[str, object]:
    if frame.raw_utf8_text_or_none is not None:
        try:
            parsed = safe_json_loads(frame.raw_utf8_text_or_none)
        except SerializationSafetyError as exc:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "raw provider text is not safe canonical JSON",
            ) from exc
        frozen = _pit_freeze_scalar_tree(parsed)
    else:
        frozen = frame.parsed_source_scalar_tree_or_none
    if not isinstance(frozen, Mapping):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "provider frame root must be an exact object",
        )
    return frozen


def _pit_provider_time(value: object, name: str) -> datetime | None:
    if value is None:
        return None
    if type(value) is int:
        if value < 0:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
                f"{name} cannot be negative",
            )
        seconds, nanoseconds = divmod(value, 1_000_000_000)
        if nanoseconds % 1_000 != 0:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
                f"{name} exceeds datetime microsecond precision",
            )
        return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(
            seconds=seconds,
            microseconds=nanoseconds // 1_000,
        )
    if type(value) is str:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
                f"{name} is not an ISO-8601 timestamp",
            ) from exc
        return _pit_adapter_utc(parsed, name)
    raise PITDataContractErrorV1(
        PITReasonCodeV1.PIT_CLOCK_DOMAIN_MISMATCH,
        f"{name} must be exact integer nanoseconds, ISO text, or absent",
    )


def _pit_tree_value(
    tree: Mapping[str, object],
    *names: str,
    required: bool,
) -> object | None:
    present = [(name, tree[name]) for name in names if name in tree]
    if len(present) > 1:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"mixed aliases are forbidden: {', '.join(names)}",
        )
    if not present:
        if required:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                f"required source field is absent: {names[0]}",
            )
        return None
    return present[0][1]


def _pit_level_from_source(
    item: object,
    *,
    source_side: str,
    canonical_side: str,
    price_increment: Decimal,
    price_origin: Decimal,
    quantity_increment_or_none: Decimal | None,
) -> _PITBookLevelV2:
    if type(item) is tuple and len(item) == 2:
        price_value, quantity_value = item
    elif isinstance(item, Mapping):
        price_value = _pit_tree_value(
            item, "price", "price_dollars", required=True
        )
        quantity_value = _pit_tree_value(
            item, "quantity", "quantity_fp", "size", required=True
        )
    else:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "book level must be exact pair or admitted object",
        )
    price_text, price, price_scale = _pit_decimal_text(price_value, "level price")
    quantity_text, quantity, quantity_scale = _pit_decimal_text(
        quantity_value, "level quantity"
    )
    return _PITBookLevelV2(
        source_side=source_side,
        canonical_side=canonical_side,
        price_text=price_text,
        price=price,
        quantity_text=quantity_text,
        quantity=quantity,
        price_scale=price_scale,
        quantity_scale=quantity_scale,
        price_increment=price_increment,
        price_origin=price_origin,
        quantity_increment_or_none=quantity_increment_or_none,
    )


def _pit_levels(
    tree: Mapping[str, object],
    *,
    bid_names: tuple[str, ...],
    offer_names: tuple[str, ...],
    price_increment: Decimal,
    price_origin: Decimal,
    quantity_increment_or_none: Decimal | None,
) -> tuple[_PITBookLevelV2, ...]:
    result: list[_PITBookLevelV2] = []
    for names, source_side, canonical_side in (
        (bid_names, "BID", "BID"),
        (offer_names, "OFFER", "ASK"),
    ):
        raw = _pit_tree_value(tree, *names, required=True)
        if type(raw) is not tuple:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                f"{source_side} levels must be an exact array",
            )
        result.extend(
            _pit_level_from_source(
                item,
                source_side=source_side,
                canonical_side=canonical_side,
                price_increment=price_increment,
                price_origin=price_origin,
                quantity_increment_or_none=quantity_increment_or_none,
            )
            for item in raw
        )
    return tuple(result)


def _pit_typed_fields_payload(
    event_kind: PITEventKindV2,
    tree: Mapping[str, object],
) -> _PITCanonicalPayloadV2:
    fields = tuple((key, tree[key]) for key in sorted(tree))
    if event_kind is PITEventKindV2.CATALOG:
        return _PITCatalogPayloadV2(event_kind=event_kind, fields=fields)
    if event_kind is PITEventKindV2.LIFECYCLE:
        return _PITLifecyclePayloadV2(event_kind=event_kind, fields=fields)
    if event_kind is PITEventKindV2.BBO:
        return _PITBBOPayloadV2(event_kind=event_kind, fields=fields)
    if event_kind is PITEventKindV2.TRADE:
        return _PITTradePayloadV2(event_kind=event_kind, fields=fields)
    if event_kind is PITEventKindV2.SETTLEMENT:
        return _PITSettlementPayloadV2(event_kind=event_kind, fields=fields)
    if event_kind is PITEventKindV2.REFERENCE_PRICE:
        return _PITReferencePricePayloadV2(event_kind=event_kind, fields=fields)
    if event_kind is PITEventKindV2.HEARTBEAT:
        return _PITHeartbeatPayloadV2(event_kind=event_kind, fields=fields)
    if event_kind is PITEventKindV2.SOURCE_STATUS:
        return _PITSourceStatusPayloadV2(event_kind=event_kind, fields=fields)
    raise PITDataContractErrorV1(
        PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
        "event kind does not have a typed scalar payload",
    )


def _pit_candidate(
    *,
    contract: SelectedPITPublicDataContractV2,
    frame: PITRawFrameV1,
    event_kind: PITEventKindV2,
    market_id: str,
    instrument_id: str,
    payload: _PITCanonicalPayloadV2,
    depth_class: PITDepthClassV2,
    provider_sequence_start_or_none: int | None,
    provider_sequence_end_or_none: int | None,
    provider_trade_id_or_none: str | None,
    provider_subscription_id_or_none: str | None,
    provider_event_time_utc_or_none: datetime | None,
    parse_completed_at_utc: datetime,
    parse_completed_monotonic_ns: int,
) -> PITCanonicalEventCandidateV2:
    return PITCanonicalEventCandidateV2(
        event_record_id=f"{frame.frame_id}::CANONICAL-EVENT-V2",
        profile_id=frame.profile_id,
        market_id=market_id,
        instrument_id=instrument_id,
        channel=frame.channel,
        connection_epoch=frame.connection_epoch,
        capture_session_id=frame.capture_session_id,
        event_kind=event_kind,
        schema_version="PIT_CANONICAL_EVENT_V2",
        wire_dialect=frame.wire_dialect,
        source_currentization_version=contract.source_contract_version,
        provider_sequence_start_or_none=provider_sequence_start_or_none,
        provider_sequence_end_or_none=provider_sequence_end_or_none,
        provider_trade_id_or_none=provider_trade_id_or_none,
        provider_subscription_id_or_none=provider_subscription_id_or_none,
        payload=payload,
        depth_class=depth_class,
        provider_event_time_utc_or_none=provider_event_time_utc_or_none,
        provider_publication_time_utc_or_none=None,
        qtt_received_at_utc=frame.qtt_received_at_utc,
        qtt_received_monotonic_ns=frame.qtt_received_monotonic_ns,
        qtt_parse_completed_at_utc=parse_completed_at_utc,
        qtt_parse_completed_monotonic_ns=parse_completed_monotonic_ns,
        process_epoch_id=frame.process_epoch_id,
        monotonic_clock_id=frame.monotonic_clock_id,
        wall_clock_source_id=frame.wall_clock_source_id,
        clock_quality_receipt_ref=frame.clock_quality_receipt_ref,
        wall_clock_uncertainty_ns=frame.wall_clock_uncertainty_ns,
        source_receipt_ref=contract.source_currentization_receipt_ref,
        rights_receipt_ref=contract.rights_receipt_ref,
        raw_frame_ref=frame.frame_id,
        no_private_state_authority=True,
        no_order_authority=True,
        no_profit_claim=True,
        no_qpu_effect=True,
        no_llm_effect=True,
    )


def _decode_gemini_titan_frame_v2(
    contract: SelectedPITPublicDataContractV2,
    frame: PITRawFrameV1,
    *,
    event_kind: PITEventKindV2,
    parse_completed_at_utc: datetime,
    parse_completed_monotonic_ns: int,
    price_increment: Decimal,
    price_origin: Decimal,
    quantity_increment_or_none: Decimal | None,
) -> PITCanonicalEventCandidateV2:
    tree = _pit_frame_tree(frame)
    symbol = _pit_tree_value(
        tree, "instrumentSymbol", "symbol", required=True
    )
    market_id_value = _pit_tree_value(
        tree, "marketId", "market_id", "eventId", required=False
    )
    instrument_id = _pit_adapter_text(symbol, "Gemini instrument symbol")
    market_id = (
        _pit_adapter_text(market_id_value, "Gemini market identity")
        if market_id_value is not None
        else instrument_id
    )
    sequence_start: int | None = None
    sequence_end: int | None = None
    if event_kind in {PITEventKindV2.BOOK_SNAPSHOT, PITEventKindV2.BOOK_DELTA}:
        sequence_start = _pit_exact_int_or_none(
            _pit_tree_value(tree, "U", required=True), "Gemini U"
        )
        sequence_end = _pit_exact_int_or_none(
            _pit_tree_value(tree, "u", required=True), "Gemini u"
        )
        if sequence_start is None or sequence_end is None or sequence_start > sequence_end:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SEQUENCE_GAP,
                "Gemini U/u range is malformed",
            )
        levels = _pit_levels(
            tree,
            bid_names=("bids", "b"),
            offer_names=("asks", "a"),
            price_increment=price_increment,
            price_origin=price_origin,
            quantity_increment_or_none=quantity_increment_or_none,
        )
        if event_kind is PITEventKindV2.BOOK_SNAPSHOT:
            payload: _PITCanonicalPayloadV2 = _PITBookSnapshotPayloadV2(
                levels=levels,
                provider_sequence=sequence_end,
                provider_subscription_id_or_none=None,
                complete_provider_snapshot=True,
            )
            depth_class = PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT
        else:
            payload = _PITBookAbsoluteUpdatePayloadV2(
                updates=tuple(
                    _PITAbsoluteLevelUpdateV2(
                        source_side=level.source_side,
                        canonical_side=level.canonical_side,
                        price_text=level.price_text,
                        price=level.price,
                        absolute_quantity_text=level.quantity_text,
                        absolute_quantity=level.quantity,
                        price_scale=level.price_scale,
                        quantity_scale=level.quantity_scale,
                        price_increment=level.price_increment,
                        price_origin=level.price_origin,
                        quantity_increment_or_none=(
                            level.quantity_increment_or_none
                        ),
                    )
                    for level in levels
                ),
                first_provider_sequence=sequence_start,
                last_provider_sequence=sequence_end,
            )
            depth_class = PITDepthClassV2.INCREMENTAL_FROM_COMPLETE_ANCHOR
    else:
        payload = _pit_typed_fields_payload(event_kind, tree)
        depth_class = (
            PITDepthClassV2.BBO_ONLY
            if event_kind is PITEventKindV2.BBO
            else contract.depth_class
        )
    trade_id_value = _pit_tree_value(
        tree, "tradeId", "trade_id", required=False
    )
    trade_id = (
        _pit_adapter_text(trade_id_value, "Gemini trade ID")
        if trade_id_value is not None
        else None
    )
    event_time = _pit_provider_time(
        _pit_tree_value(tree, "E", "eventTime", required=False),
        "Gemini provider event time",
    )
    return _pit_candidate(
        contract=contract,
        frame=frame,
        event_kind=event_kind,
        market_id=market_id,
        instrument_id=instrument_id,
        payload=payload,
        depth_class=depth_class,
        provider_sequence_start_or_none=sequence_start,
        provider_sequence_end_or_none=sequence_end,
        provider_trade_id_or_none=trade_id,
        provider_subscription_id_or_none=None,
        provider_event_time_utc_or_none=event_time,
        parse_completed_at_utc=parse_completed_at_utc,
        parse_completed_monotonic_ns=parse_completed_monotonic_ns,
    )


def _decode_polymarket_us_retail_frame_v2(
    contract: SelectedPITPublicDataContractV2,
    frame: PITRawFrameV1,
    *,
    event_kind: PITEventKindV2,
    parse_completed_at_utc: datetime,
    parse_completed_monotonic_ns: int,
    price_increment: Decimal,
    price_origin: Decimal,
    quantity_increment_or_none: Decimal | None,
) -> PITCanonicalEventCandidateV2:
    if frame.wire_dialect not in {
        "POLYMARKET_RETAIL_CAMEL_STRING_V1",
        "POLYMARKET_RETAIL_SNAKE_NUMERIC_V1",
    }:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "Polymarket Retail frame uses an unknown locked dialect",
        )
    tree = _pit_frame_tree(frame)
    primary_dialect = frame.wire_dialect == "POLYMARKET_RETAIL_CAMEL_STRING_V1"
    market_name = "marketId" if primary_dialect else "market_id"
    slug_name = "marketSlug" if primary_dialect else "market_slug"
    time_name = "transactTime" if primary_dialect else "transact_time"
    market_sides_name = "marketSides" if primary_dialect else "market_sides"
    tick_name = (
        "orderPriceMinTickSize"
        if primary_dialect
        else "order_price_min_tick_size"
    )
    forbidden_names = (
        (
            "market_id",
            "market_slug",
            "transact_time",
            "market_sides",
            "order_price_min_tick_size",
        )
        if primary_dialect
        else (
            "marketId",
            "marketSlug",
            "transactTime",
            "marketSides",
            "orderPriceMinTickSize",
        )
    )
    removed_legacy_outcome_names = (
        "outcomes",
        "outcomeNames",
        "outcome_names",
        "outcomePrices",
        "outcome_prices",
    )
    if any(name in tree for name in (*forbidden_names, *removed_legacy_outcome_names)):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "Retail frame uses the other dialect or a removed legacy outcome field",
        )
    if event_kind is PITEventKindV2.HEARTBEAT:
        if _pit_tree_value(tree, "type", required=True) != "heartbeat":
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "Retail heartbeat requires its exact source message type",
            )
        market_id = "POLYMARKET_US_RETAIL_DIRECT::VENUE"
        instrument_id = market_id
    else:
        market_value = _pit_tree_value(tree, market_name, required=True)
        slug_value = _pit_tree_value(tree, slug_name, required=True)
        market_id = _pit_adapter_text(market_value, "Polymarket market ID")
        instrument_id = _pit_adapter_text(slug_value, "Polymarket market slug")
    if event_kind is PITEventKindV2.BOOK_REPLACEMENT:
        source_lifecycle_state = _pit_tree_value(tree, "state", required=True)
        lifecycle_type_valid = (
            type(source_lifecycle_state) is str
            if primary_dialect
            else type(source_lifecycle_state) is int
            and source_lifecycle_state >= 0
        )
        if not lifecycle_type_valid:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "Retail lifecycle enum type differs from the locked wire dialect",
            )
        if primary_dialect:
            _pit_adapter_text(source_lifecycle_state, "Retail lifecycle state")
        market_sides = _pit_tree_value(tree, market_sides_name, required=True)
        if (
            type(market_sides) is not tuple
            or len(market_sides) < 2
            or any(not isinstance(side, Mapping) or not side for side in market_sides)
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "Retail marketSides must be an array of at least two mappings",
            )
        tick_text, source_tick, _ = _pit_decimal_text(
            _pit_tree_value(tree, tick_name, required=True),
            "Retail orderPriceMinTickSize",
        )
        if (
            source_tick <= 0
            or source_tick.as_tuple() != price_increment.as_tuple()
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TICK_GRID_INVALID,
                "Retail frame tick differs from its exact per-market tick binding",
            )
        levels = _pit_levels(
            tree,
            bid_names=("bids",),
            offer_names=("offers",),
            price_increment=price_increment,
            price_origin=price_origin,
            quantity_increment_or_none=quantity_increment_or_none,
        )
        is_rest = frame.channel in {"REST_BOOK", "/v1/markets/{slug}/book"}
        payload: _PITCanonicalPayloadV2 = _PITBookReplacementPayloadV2(
            levels=levels,
            surface_class=(
                "POLYMARKET_RETAIL_REST_COMPLETE_BOOK_CURRENT_STATE"
                if is_rest
                else "POLYMARKET_RETAIL_WEBSOCKET_TOP_LEVEL_CURRENT_STATE"
            ),
            provider_sequence_unavailable=True,
            source_lifecycle_state=source_lifecycle_state,
            market_sides_json=deterministic_json(market_sides),
            order_price_min_tick_size_text=tick_text,
        )
        depth_class = (
            PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT
            if is_rest
            else PITDepthClassV2.PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME
        )
    else:
        payload = _pit_typed_fields_payload(event_kind, tree)
        depth_class = (
            PITDepthClassV2.BBO_ONLY
            if event_kind is PITEventKindV2.BBO
            else contract.depth_class
        )
    event_time = _pit_provider_time(
        _pit_tree_value(tree, time_name, required=False),
        "Polymarket provider event time",
    )
    return _pit_candidate(
        contract=contract,
        frame=frame,
        event_kind=event_kind,
        market_id=market_id,
        instrument_id=instrument_id,
        payload=payload,
        depth_class=depth_class,
        provider_sequence_start_or_none=None,
        provider_sequence_end_or_none=None,
        provider_trade_id_or_none=None,
        provider_subscription_id_or_none=None,
        provider_event_time_utc_or_none=event_time,
        parse_completed_at_utc=parse_completed_at_utc,
        parse_completed_monotonic_ns=parse_completed_monotonic_ns,
    )


def _pit_kalshi_snapshot_levels(
    message: Mapping[str, object],
    *,
    price_increment: Decimal,
    price_origin: Decimal,
    quantity_increment_or_none: Decimal | None,
) -> tuple[_PITBookLevelV2, ...]:
    result: list[_PITBookLevelV2] = []
    for field_names, source_side, canonical_side in (
        (("yes_dollars",), "YES", "YES_BID"),
        (("no_dollars",), "NO", "NO_BID"),
    ):
        raw = _pit_tree_value(message, *field_names, required=True)
        if type(raw) is not tuple:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "Kalshi snapshot side must be an exact array",
            )
        for item in raw:
            normalized_item = item
            if isinstance(item, Mapping):
                normalized_item = (
                    _pit_tree_value(item, "price_dollars", required=True),
                    _pit_tree_value(item, "quantity_fp", required=True),
                )
            result.append(
                _pit_level_from_source(
                    normalized_item,
                    source_side=source_side,
                    canonical_side=canonical_side,
                    price_increment=price_increment,
                    price_origin=price_origin,
                    quantity_increment_or_none=quantity_increment_or_none,
                )
            )
    return tuple(result)


def _decode_kalshi_us_dcm_frame_v2(
    contract: SelectedPITPublicDataContractV2,
    frame: PITRawFrameV1,
    *,
    event_kind: PITEventKindV2,
    parse_completed_at_utc: datetime,
    parse_completed_monotonic_ns: int,
    price_increment: Decimal,
    price_origin: Decimal,
    quantity_increment_or_none: Decimal | None,
) -> PITCanonicalEventCandidateV2:
    tree = _pit_frame_tree(frame)
    if event_kind in {PITEventKindV2.BOOK_SNAPSHOT, PITEventKindV2.BOOK_DELTA}:
        expected_message_type = (
            "orderbook_snapshot"
            if event_kind is PITEventKindV2.BOOK_SNAPSHOT
            else "orderbook_delta"
        )
        if _pit_tree_value(tree, "type", required=True) != expected_message_type:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "Kalshi book message type differs from its exact event kind",
            )
    message_value = _pit_tree_value(tree, "msg", required=False)
    if message_value is None:
        message: Mapping[str, object] = tree
    elif isinstance(message_value, Mapping):
        message = message_value
    else:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "Kalshi msg must be an exact object",
        )
    if any(
        name in container
        for container in (tree, message)
        for name in ("yes", "no", "price", "delta")
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "removed Kalshi integer/cent aliases are forbidden",
        )
    venue_wide = event_kind in {
        PITEventKindV2.HEARTBEAT,
        PITEventKindV2.SOURCE_STATUS,
    }
    if event_kind is PITEventKindV2.HEARTBEAT and (
        _pit_tree_value(tree, "type", required=True) != "ping"
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "Kalshi heartbeat requires its exact server Ping message type",
        )
    ticker_value = _pit_tree_value(
        message, "market_ticker", required=not venue_wide
    )
    ticker = (
        _pit_adapter_text(ticker_value, "Kalshi market ticker")
        if ticker_value is not None
        else "KALSHI_US_DCM_DIRECT::VENUE"
    )
    sid_value = _pit_tree_value(tree, "sid", required=False)
    if sid_value is None:
        sid_value = _pit_tree_value(message, "sid", required=False)
    if sid_value is not None and type(sid_value) not in {str, int}:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "Kalshi sid must be exact text or integer",
        )
    if isinstance(sid_value, bool):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "Kalshi sid cannot be Boolean",
        )
    sid = str(sid_value) if sid_value is not None else None
    sequence_value = _pit_tree_value(tree, "seq", required=False)
    if sequence_value is None:
        sequence_value = _pit_tree_value(message, "seq", required=False)
    sequence: int | None = None
    if event_kind in {PITEventKindV2.BOOK_SNAPSHOT, PITEventKindV2.BOOK_DELTA}:
        sequence = _pit_exact_int_or_none(sequence_value, "Kalshi seq")
        if sequence is None or sid is None:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "Kalshi book message requires exact sid and seq",
            )
    if event_kind is PITEventKindV2.BOOK_SNAPSHOT:
        payload: _PITCanonicalPayloadV2 = _PITBookSnapshotPayloadV2(
            levels=_pit_kalshi_snapshot_levels(
                message,
                price_increment=price_increment,
                price_origin=price_origin,
                quantity_increment_or_none=quantity_increment_or_none,
            ),
            provider_sequence=sequence,
            provider_subscription_id_or_none=sid,
            complete_provider_snapshot=True,
        )
        depth_class = PITDepthClassV2.COMPLETE_PROVIDER_SNAPSHOT
    elif event_kind is PITEventKindV2.BOOK_DELTA:
        source_side_value = _pit_tree_value(message, "side", required=True)
        source_side = _pit_adapter_text(source_side_value, "Kalshi source side")
        if source_side not in {"YES", "NO"}:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "Kalshi book delta side must be exact YES or NO",
            )
        price_value = _pit_tree_value(message, "price_dollars", required=True)
        delta_value = _pit_tree_value(message, "delta_fp", required=True)
        price_text, price, price_scale = _pit_decimal_text(
            price_value, "Kalshi delta price"
        )
        delta_text, delta, delta_scale = _pit_decimal_text(
            delta_value, "Kalshi quantity delta"
        )
        payload = _PITBookDeltaPayloadV2(
            deltas=(
                _PITDeltaLevelV2(
                    source_side=source_side,
                    canonical_side=f"{source_side}_BID",
                    price_text=price_text,
                    price=price,
                    quantity_delta_text=delta_text,
                    quantity_delta=delta,
                    price_scale=price_scale,
                    quantity_scale=delta_scale,
                    price_increment=price_increment,
                    price_origin=price_origin,
                    quantity_increment_or_none=quantity_increment_or_none,
                ),
            ),
            provider_sequence=sequence,
            provider_subscription_id=sid,
        )
        depth_class = PITDepthClassV2.INCREMENTAL_FROM_COMPLETE_ANCHOR
    else:
        payload = _pit_typed_fields_payload(event_kind, message)
        depth_class = contract.depth_class
    trade_id_value = _pit_tree_value(message, "trade_id", required=False)
    trade_id = (
        _pit_adapter_text(trade_id_value, "Kalshi trade ID")
        if trade_id_value is not None
        else None
    )
    event_time = _pit_provider_time(
        _pit_tree_value(message, "created_time", required=False),
        "Kalshi provider event time",
    )
    return _pit_candidate(
        contract=contract,
        frame=frame,
        event_kind=event_kind,
        market_id=ticker,
        instrument_id=ticker,
        payload=payload,
        depth_class=depth_class,
        provider_sequence_start_or_none=sequence,
        provider_sequence_end_or_none=sequence,
        provider_trade_id_or_none=trade_id,
        provider_subscription_id_or_none=sid,
        provider_event_time_utc_or_none=event_time,
        parse_completed_at_utc=parse_completed_at_utc,
        parse_completed_monotonic_ns=parse_completed_monotonic_ns,
    )


_PIT_PRIVATE_DECODER_BY_PROFILE_V2 = MappingProxyType({
    Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: _decode_gemini_titan_frame_v2,
    Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: (
        _decode_polymarket_us_retail_frame_v2
    ),
    Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: _decode_kalshi_us_dcm_frame_v2,
})


def _decode_pit_frame_v2(
    contract: SelectedPITPublicDataContractV2,
    frame: PITRawFrameV1,
    *,
    event_kind: PITEventKindV2,
    parse_completed_at_utc: datetime,
    parse_completed_monotonic_ns: int,
    price_increment_text: str,
    price_origin_text: str,
    quantity_increment_text_or_none: str | None,
) -> PITCanonicalEventCandidateV2:
    if type(contract) is not SelectedPITPublicDataContractV2 or type(
        frame
    ) is not PITRawFrameV1:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "decode requires exact contract and raw frame types",
        )
    if contract.profile_id is not frame.profile_id:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "raw frame profile differs from selected contract profile",
        )
    if (
        frame.profile_id
        is not Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT
        and frame.wire_dialect != contract.wire_dialect_policy
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "raw frame wire dialect differs from the exact selected contract",
        )
    if type(event_kind) is not PITEventKindV2 or event_kind not in (
        contract.admitted_event_kinds
    ):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            "event kind is not admitted by the selected contract",
        )
    if frame.source_contract_refs != (contract.contract_id,):
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SOURCE_CURRENTIZATION_STALE,
            "raw frame does not bind the exact selected contract",
        )
    _, price_increment, _ = _pit_decimal_text(
        price_increment_text, "price_increment_text"
    )
    _, price_origin, _ = _pit_decimal_text(price_origin_text, "price_origin_text")
    if price_increment <= 0:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_TICK_GRID_INVALID,
            "price increment must be positive",
        )
    quantity_increment: Decimal | None = None
    if quantity_increment_text_or_none is not None:
        _, quantity_increment, _ = _pit_decimal_text(
            quantity_increment_text_or_none,
            "quantity_increment_text_or_none",
        )
        if quantity_increment <= 0:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_QUANTITY_GRID_INVALID,
                "quantity increment must be positive",
            )
    decoder = _PIT_PRIVATE_DECODER_BY_PROFILE_V2.get(frame.profile_id)
    if decoder is None:
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
            "no decoder exists outside the selected three-profile scope",
        )
    return decoder(
        contract,
        frame,
        event_kind=event_kind,
        parse_completed_at_utc=parse_completed_at_utc,
        parse_completed_monotonic_ns=parse_completed_monotonic_ns,
        price_increment=price_increment,
        price_origin=price_origin,
        quantity_increment_or_none=quantity_increment,
    )
