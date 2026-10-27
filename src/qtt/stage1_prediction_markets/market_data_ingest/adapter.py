from __future__ import annotations

import re
import base64
import json
from dataclasses import dataclass, fields as dataclass_fields
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from types import MappingProxyType
from typing import Mapping
from urllib.parse import quote, urlencode

from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from src.qtt.stage1_prediction_markets.market_data_ingest.binding import (
    SelectedPITPublicDataContractV2,
    PublicMetadataSnapshotV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import (
    _native_ident, _native_require, _public_counter_v1, _public_refs_v1, _public_scalar_tree_v1,
    _public_exact_clock_v1, _public_on_price_grid_v1,
    _native_utc_receipt_pair,
    _native_utc_nanoseconds,
    _native_retail_finite_decimal_text_v1,
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
    _native_strict_json, _check_key,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    Stage1VenueProfileIdV1,
)


@dataclass(frozen=True, slots=True)
class PublicDataReadRequestV1:
    request_id: str
    profile_id: Stage1VenueProfileIdV1
    operation_id: str
    native_contract_version: str
    instrument_ids: tuple[str, ...]
    pagination_cursor_or_none: str | None
    time_bounds_or_none: tuple[int, int] | None
    source_binding_ref: str
    metadata_refs: tuple[str, ...]
    capture_request_ref: str
    request_options: Mapping[str, object]

    def __post_init__(self):
        from src.qtt.stage1_prediction_markets.qku_computation_control_plane.receipts import (
            _PUBLIC_OPERATIONS_V1, _public_profile_v1,
        )

        _public_profile_v1(self.profile_id)
        for name in ("request_id", "operation_id", "native_contract_version", "source_binding_ref", "capture_request_ref"):
            _native_ident(getattr(self, name))
        _native_require(self.operation_id in _PUBLIC_OPERATIONS_V1[self.profile_id], "unsupported public operation")
        _public_refs_v1(self.instrument_ids)
        _public_refs_v1(self.metadata_refs, allow_empty=True)
        if self.pagination_cursor_or_none is not None:
            _native_ident(self.pagination_cursor_or_none)
        if self.time_bounds_or_none is not None:
            _native_require(type(self.time_bounds_or_none) is tuple and len(self.time_bounds_or_none) == 2,
                            "invalid request time interval")
            for value in self.time_bounds_or_none:
                _public_counter_v1(value, allow_zero=True)
            _native_require(self.time_bounds_or_none[0] <= self.time_bounds_or_none[1], "reversed request interval")
        _native_require(type(self.request_options) in (dict, MappingProxyType), "invalid request options")
        object.__setattr__(self, "request_options", _public_scalar_tree_v1(self.request_options))


def _public_native_path_id_v1(value):
    _native_ident(value)
    _native_require(not any(c in value for c in "/\\?#%:") and value not in {".", ".."},
                    "unsafe native path identity")
    return quote(value, safe="")


def compile_public_read_request_v1(*, request: PublicDataReadRequestV1,
                                   source_binding, metadata: tuple[PublicMetadataSnapshotV1, ...]):
    """Compile a closed, data-only descriptor. This function grants no effect."""
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.source_policy import PublicDataSourceBindingV1

    _native_require(type(request) is PublicDataReadRequestV1 and type(source_binding) is PublicDataSourceBindingV1,
                    "public compiler requires exact input types")
    request.__post_init__()
    source_binding.__post_init__()
    _native_require(request.profile_id is source_binding.profile_id
                    and request.source_binding_ref == source_binding.binding_id
                    and request.operation_id in source_binding.allowed_operation_ids
                    and request.native_contract_version in source_binding.source_contract_versions,
                    "public request does not bind accepted source contract")
    _native_require(type(metadata) is tuple and len(metadata) <= 4096, "invalid metadata selection")
    for row in metadata:
        _native_require(type(row) is PublicMetadataSnapshotV1 and row.profile_id is request.profile_id,
                        "cross-profile metadata selection")
        row.__post_init__()
    _native_require(tuple(row.metadata_id for row in metadata) == request.metadata_refs,
                    "request metadata references differ from selected immutable inputs")
    op, options = request.operation_id, request.request_options
    host = {
        Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: "api.elections.kalshi.com",
        Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: "gateway.polymarket.us",
        Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: "api.gemini.com",
    }[request.profile_id]
    routes = {
        "K_MARKET": ("ticker", "/trade-api/v2/markets/"),
        "K_EVENT": ("event_ticker", "/trade-api/v2/events/"),
        "K_SERIES": ("series_ticker", "/trade-api/v2/series/"),
        "P_MARKET": ("slug", "/v1/market/slug/"),
        "P_BOOK": ("slug", "/v1/markets/"),
        "P_SETTLEMENT": ("slug", "/v1/markets/"),
        "G_EVENT": ("eventTicker", "/v1/prediction-markets/events/"),
    }
    query, command, receive_scope = [], None, "SELECTED_INSTRUMENTS"
    if op in routes:
        name, prefix = routes[op]
        _native_require(set(options) == {name}, "unexpected single-resource request option")
        native_id = options[name]
        allowed = set(request.instrument_ids)
        if op in {"K_EVENT", "G_EVENT"}:
            allowed = {row.event_id_or_none for row in metadata}
        elif op == "K_SERIES":
            allowed = {row.series_id_or_none for row in metadata}
        _native_require(allowed == {native_id}, "native path identity is outside selected metadata/instruments")
        path = prefix + _public_native_path_id_v1(native_id)
        if op in {"P_BOOK", "P_SETTLEMENT"}:
            path += "/book" if op == "P_BOOK" else "/settlement"
    elif op == "K_SERIES_FEES":
        _native_require(set(options) == {"series_ticker", "show_historical"}
                        and type(options["show_historical"]) is bool, "invalid Series fee request")
        _native_require({row.series_id_or_none for row in metadata} == {options["series_ticker"]}, "unbound Series")
        _public_native_path_id_v1(options["series_ticker"])
        path = "/trade-api/v2/series/fee_changes"
        query = [("series_ticker", options["series_ticker"]),
                 ("show_historical", "true" if options["show_historical"] else "false")]
    elif op in {"K_EVENT_FEES", "K_HISTORY_TRADES"}:
        required = {"event_ticker", "limit", "cursor"} if op == "K_EVENT_FEES" else {
            "ticker", "limit", "min_ts", "max_ts", "cursor"}
        _native_require(set(options) == required and type(options["limit"]) is int
                        and 1 <= options["limit"] <= 1000, "invalid bounded paginated request")
        name = "event_ticker" if op == "K_EVENT_FEES" else "ticker"
        allowed = {row.event_id_or_none for row in metadata} if op == "K_EVENT_FEES" else set(request.instrument_ids)
        _native_require(allowed == {options[name]}, "paginated request identity outside scope")
        _public_native_path_id_v1(options[name])
        _native_require(options["cursor"] == request.pagination_cursor_or_none, "cursor does not bind descriptor")
        path = "/trade-api/v2/events/fee_changes" if op == "K_EVENT_FEES" else "/trade-api/v2/historical/trades"
        query = [(name, options[name]), ("limit", options["limit"])]
        if op == "K_HISTORY_TRADES":
            _native_require(request.time_bounds_or_none is not None
                            and (options["min_ts"], options["max_ts"]) == request.time_bounds_or_none,
                            "historical window does not bind descriptor")
            for key in ("min_ts", "max_ts"):
                _public_counter_v1(options[key], allow_zero=True)
                query.append((key, options[key]))
        if options["cursor"] is not None:
            query.append(("cursor", options["cursor"]))
    elif op in {"K_STATUS", "K_HISTORY_CUTOFF"}:
        _native_require(not options, "status/cutoff accepts no options")
        path = "/trade-api/v2/exchange/status" if op == "K_STATUS" else "/trade-api/v2/historical/cutoff"
    elif op == "G_EVENTS":
        _native_require(set(options) == {"limit", "offset"} and type(options["limit"]) is int
                        and 1 <= options["limit"] <= 500, "invalid global discovery request")
        _public_counter_v1(options["offset"], allow_zero=True)
        path, query, receive_scope = "/v1/prediction-markets/events", list(options.items()), "GLOBAL_PUBLIC_DISCOVERY"
    elif op == "K_WS":
        _native_require(set(options) == {"id", "cmd", "params"}, "invalid Kalshi control fields")
        _public_counter_v1(options["id"])
        params = options["params"]
        _native_require(type(params) is MappingProxyType, "invalid Kalshi control params")
        if options["cmd"] == "subscribe":
            channels = params.get("channels")
            _native_require(type(channels) is tuple and len(channels) == 1
                            and channels[0] in {"orderbook_delta", "trade", "market_lifecycle_v2"},
                            "unselected Kalshi channel")
            if channels[0] == "market_lifecycle_v2":
                _native_require(set(params) == {"channels"}, "global lifecycle does not support ticker filtering")
                receive_scope = "GLOBAL_PUBLIC_LIFECYCLE"
            else:
                _native_require(set(params) == {"channels", "market_tickers"}, "invalid selected subscription")
                _public_refs_v1(params["market_tickers"])
                _native_require(set(params["market_tickers"]) <= set(request.instrument_ids), "unselected ticker")
        else:
            _native_require(options["cmd"] == "unsubscribe" and set(params) == {"sids"}
                            and type(params["sids"]) is tuple and len(params["sids"]) == 1,
                            "unselected Kalshi command")
            _public_counter_v1(params["sids"][0])
        path, command = "/trade-api/ws/v2", options
    elif op == "P_WS":
        _native_require(set(options) == {"subscribe"} and type(options["subscribe"]) is MappingProxyType,
                        "invalid Retail subscription envelope")
        sub = options["subscribe"]
        _native_require(set(sub) == {"requestId", "subscriptionType", "marketSlugs"}, "invalid Retail subscription fields")
        _native_ident(sub["requestId"])
        _public_refs_v1(sub["marketSlugs"])
        _native_require(sub["subscriptionType"] in {"SUBSCRIPTION_TYPE_MARKET_DATA", "SUBSCRIPTION_TYPE_TRADE"}
                        and len(sub["marketSlugs"]) <= 100
                        and set(sub["marketSlugs"]) <= set(request.instrument_ids), "unselected Retail subscription")
        host, path, command = "api.polymarket.us", "/v1/ws/markets", options
    elif op == "G_WS":
        _native_require(set(options) == {"id", "method", "params"}
                        and options["method"] in {"SUBSCRIBE", "UNSUBSCRIBE"}, "unselected Gemini command")
        _native_ident(options["id"])
        _public_refs_v1(options["params"])
        allowed = {instrument + "@" + channel for instrument in request.instrument_ids
                   for channel in ("depth", "bookTicker", "trade")}
        allowed.add("contractStatus")
        _native_require(set(options["params"]) <= allowed, "unselected Gemini stream")
        if "contractStatus" in options["params"]:
            receive_scope = "GLOBAL_PUBLIC_LIFECYCLE"
        host, path, query, command = "ws.gemini.com", "/", [("snapshot", "-1")], options
    else:
        _native_require(False, "unselected public operation")
    if op not in {"K_EVENT_FEES", "K_HISTORY_TRADES"}:
        _native_require(request.pagination_cursor_or_none is None, "unused cursor")
    if op != "K_HISTORY_TRADES":
        _native_require(request.time_bounds_or_none is None, "unused time bounds")
    return _public_scalar_tree_v1(dict(request_ref=request.request_id, host=host, port=443,
        method="GET" if command is None else "WEBSOCKET", path=path,
        query=urlencode(query), command=command, receive_scope_class=receive_scope))


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
        if ((Fraction(price) - Fraction(self.price_origin)) / Fraction(self.price_increment)).denominator != 1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_TICK_GRID_INVALID,
                "book level price is off its exact origin/increment grid",
            )
        if self.quantity_increment_or_none is not None:
            if (
                type(self.quantity_increment_or_none) is not Decimal
                or not self.quantity_increment_or_none.is_finite()
                or self.quantity_increment_or_none <= 0
                or (Fraction(quantity) / Fraction(self.quantity_increment_or_none)).denominator != 1
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
            or ((Fraction(price) - Fraction(self.price_origin)) / Fraction(self.price_increment)).denominator != 1
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
            or (Fraction(quantity_delta) / Fraction(self.quantity_increment_or_none)).denominator != 1
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


def _pit_payload_types_for_event_kind_v2(event_kind: PITEventKindV2) -> tuple[type, ...]:
    if event_kind is PITEventKindV2.BOOK_SNAPSHOT:
        return (_PITBookSnapshotPayloadV2,)
    if event_kind is PITEventKindV2.BOOK_DELTA:
        return (
            _PITBookAbsoluteUpdatePayloadV2,
            _PITBookDeltaPayloadV2,
        )
    if event_kind is PITEventKindV2.BOOK_REPLACEMENT:
        return (_PITBookReplacementPayloadV2,)
    expected_type = _PIT_TYPED_PAYLOAD_TYPE_BY_EVENT_KIND_V2.get(event_kind)
    return () if expected_type is None else (expected_type,)


def _pit_payload_matches_event_kind(
    payload: object,
    event_kind: PITEventKindV2,
) -> bool:
    if event_kind in {PITEventKindV2.BOOK_SNAPSHOT, PITEventKindV2.BOOK_DELTA, PITEventKindV2.BOOK_REPLACEMENT}:
        return type(payload) in _pit_payload_types_for_event_kind_v2(event_kind)
    return (
        type(payload) in _pit_payload_types_for_event_kind_v2(event_kind)
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
    price_bands: tuple = (),
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
    if price_bands:
        origin, increment = _public_on_price_grid_v1(price_text, bands=price_bands, origin=None, increment=None)
        price_origin, price_increment = Decimal(origin), Decimal(increment)
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
    price_bands: tuple = (),
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
    price_bands: tuple = (),
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
    price_bands: tuple = (),
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
                    price_bands=price_bands,
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
    price_bands: tuple = (),
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
                price_bands=price_bands,
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
        if price_bands:
            origin, increment = _public_on_price_grid_v1(price_text, bands=price_bands, origin=None, increment=None)
            price_origin, price_increment = Decimal(origin), Decimal(increment)
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
    joined_market_id = _pit_tree_value(message, "market_id", required=False)
    return _pit_candidate(
        contract=contract,
        frame=frame,
        event_kind=event_kind,
        market_id=ticker if joined_market_id is None else _pit_adapter_text(joined_market_id, "joined Kalshi market identity"),
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
    price_bands: tuple = (),
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
    _native_require(not price_bands or frame.profile_id is Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT,
                    "band-grid decoder selected for another profile")
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
        price_bands=price_bands,
    )


def _public_native_tree_v1(raw: bytes, *, maximum_bytes: int = 65536) -> dict:
    """Bounded original-body admission, shared by capture and translation.

    Inspect additive fields too: projecting a private field out later cannot
    make retaining its original bytes lawful. Decimal values stay native here.
    """
    tree = _native_strict_json(raw, max_bytes=maximum_bytes)
    _native_require(type(tree) is dict, "public native body must be an object")

    def inspect(value):
        if type(value) is dict:
            for key, item in value.items():
                _check_key(key)
                if _pit_source_field_class(key) in policy.PIT_PRIVATE_FIELD_DENYLIST_V1:
                    raise PITDataContractErrorV1(PITReasonCodeV1.PIT_PRIVATE_FIELD_CLASS_REJECTED,
                                                 "private field in original public body")
                inspect(item)
        elif type(value) is list:
            for item in value:
                inspect(item)

    inspect(tree)
    return tree


@dataclass(frozen=True, slots=True)
class PublicCanonicalTranslationV1:
    observation_ref: str
    normalized_frame: PITRawFrameV1
    exact_clock_companion: Mapping[str, object]
    canonical_contract_ref: str
    metadata_refs: tuple[str, ...]
    stream_disposition: Mapping[str, object]
    field_lineage: tuple[tuple[str, str, str, str], ...]

    def __post_init__(self):
        from .binding import _public_field_lineage_v1

        _native_ident(self.observation_ref)
        _native_ident(self.canonical_contract_ref)
        _native_require(type(self.normalized_frame) is PITRawFrameV1
                        and self.normalized_frame.frame_id != self.observation_ref
                        and self.normalized_frame.raw_utf8_text_or_none is None,
                        "translation must identify a distinct internal frame")
        self.normalized_frame.__post_init__()
        _public_refs_v1(self.metadata_refs, allow_empty=True)
        _public_field_lineage_v1(self.field_lineage)
        for name in ("exact_clock_companion", "stream_disposition"):
            value = getattr(self, name)
            _native_require(type(value) in (dict, MappingProxyType), "invalid translation companion")
            object.__setattr__(self, name, _public_scalar_tree_v1(value))
        clocks = self.exact_clock_companion
        _native_require(set(clocks) == {"received", "provider_event_or_none", "provider_sending_or_none"}
                        and clocks["received"] is not None, "invalid exact clock companion fields")
        for pair in clocks.values():
            if pair is not None:
                _native_require(type(pair) is MappingProxyType and "source_text" in pair
                                and dict(pair) == _native_utc_receipt_pair(pair["source_text"]),
                                "exact clock companion differs from its source time")
        _native_require(self.normalized_frame.qtt_received_at_utc == _pit_provider_time(
            clocks["received"]["receipt_utc_floor"], "received projection"), "received clock projection differs")
        disposition = self.stream_disposition
        _native_require(disposition.get("kind") in {"CONTROL", "METADATA", "MARKET_DATA", "UNSELECTED_LIFECYCLE", "PUBLIC_REFERENCE"}, "unknown translation disposition")
        if disposition["kind"] == "CONTROL":
            _native_require({"kind", "message_type", "request_id"} <= set(disposition)
                <= {"kind", "message_type", "request_id", "sid", "seq", "channel", "code", "message"}
                and disposition["message_type"] in {"subscribed", "ok", "unsubscribed", "error"},
                "invalid control disposition")
            if self.normalized_frame.profile_id is Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT:
                _native_ident(disposition["request_id"])
            else:
                _public_counter_v1(disposition["request_id"])
            for name in ("sid", "seq", "code"):
                if name in disposition:
                    _public_counter_v1(disposition[name], allow_zero=name != "sid")
            if disposition["message_type"] == "subscribed":
                _native_require({"sid", "channel"} <= set(disposition), "incomplete subscription disposition")
        elif disposition["kind"] == "PUBLIC_REFERENCE":
            if disposition.get("operation_id") == "K_WS":
                _native_require(set(disposition) == {"kind","operation_id","instrument_ids","notification_type","event_id"}
                    and disposition["notification_type"] in {"event_lifecycle","event_fee_update"},
                    "invalid global Event notification disposition")
                _native_ident(disposition["event_id"])
                _public_refs_v1(disposition["instrument_ids"],allow_empty=True)
            else:
                _native_require(set(disposition) == {"kind", "operation_id", "instrument_ids"}
                    and disposition["operation_id"] in {"K_STATUS", "K_HISTORY_CUTOFF", "K_SERIES_FEES", "K_EVENT_FEES",
                                                        "K_HISTORY_TRADES", "P_SETTLEMENT"}, "invalid public reference disposition")
                _public_refs_v1(disposition["instrument_ids"])
        elif disposition["kind"] == "UNSELECTED_LIFECYCLE":
            _native_require(set(disposition) == {"kind", "instrument_id"}, "invalid unselected lifecycle disposition")
            _native_ident(disposition["instrument_id"])
        elif disposition["kind"] == "METADATA":
            if "instrument_generations" in disposition:
                _native_require(set(disposition) == {"kind", "instrument_generations"},
                                "invalid metadata selection disposition")
                rows = disposition["instrument_generations"]
                _native_require(type(rows) is tuple and 0 < len(rows) <= 4096
                                and all(type(row) is tuple and len(row) == 2 for row in rows)
                                and len({row[0] for row in rows}) == len(rows),
                                "metadata selection must name each instrument exactly once")
                for instrument, generation in rows:
                    _native_ident(instrument)
                    _public_counter_v1(generation, allow_zero=True)
            else:
                _native_require(set(disposition) == {"kind", "instrument_id", "metadata_generation"},
                                "invalid metadata disposition")
                _native_ident(disposition["instrument_id"])
                _public_counter_v1(disposition["metadata_generation"], allow_zero=True)
        else:
            _native_require({"kind", "event_kind", "instrument_id", "metadata_generation"} <= set(disposition)
                            <= {"kind", "event_kind", "instrument_id", "metadata_generation", "market_clock", "lifecycle_state"}
                            and disposition["event_kind"] in {"BOOK_SNAPSHOT", "BOOK_DELTA", "BOOK_REPLACEMENT",
                                                              "BBO", "TRADE", "LIFECYCLE"},
                            "invalid market-data disposition")
            _native_ident(disposition["instrument_id"])
            _public_counter_v1(disposition["metadata_generation"], allow_zero=True)
            if "market_clock" in disposition:
                _public_counter_v1(disposition["market_clock"], allow_zero=True)
            if disposition["event_kind"] == "LIFECYCLE":
                _native_require(disposition.get("lifecycle_state") in {
                    "OPEN", "PAUSED", "CLOSED", "UNDER_REVIEW", "RESOLVED", "SETTLED", "VOID", "UNAVAILABLE"},
                    "lifecycle event requires a closed canonical disposition")
            else:
                _native_require("lifecycle_state" not in disposition, "non-lifecycle event cannot change lifecycle")


def _public_translation_from_storage_v1(value) -> PublicCanonicalTranslationV1:
    """Restore an unaccepted translation candidate, never receiving custody."""
    _native_require(type(value) is dict and set(value) == {field.name for field in dataclass_fields(PublicCanonicalTranslationV1)},
                    "stored translation has missing or extra fields")
    row = dict(value)
    frame = row["normalized_frame"]
    _native_require(type(frame) is dict and set(frame) == {field.name for field in dataclass_fields(PITRawFrameV1)},
                    "stored normalized frame has missing or extra fields")
    frame = dict(frame)
    try:
        frame["profile_id"] = Stage1VenueProfileIdV1(frame["profile_id"])
    except (TypeError, ValueError) as exc:
        raise PITDataContractErrorV1(PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED, "unknown stored translation profile") from exc
    frame["qtt_received_at_utc"] = _pit_provider_time(frame["qtt_received_at_utc"], "stored received projection")
    _native_require(type(frame["source_contract_refs"]) is list, "stored frame references must be an array")
    frame["source_contract_refs"] = tuple(frame["source_contract_refs"])
    row["normalized_frame"] = PITRawFrameV1(**frame)
    _native_require(type(row["metadata_refs"]) is list and type(row["field_lineage"]) is list
                    and all(type(item) is list for item in row["field_lineage"]), "invalid stored translation lineage")
    row["metadata_refs"] = tuple(row["metadata_refs"])
    row["field_lineage"] = tuple(tuple(item) for item in row["field_lineage"])
    restored = PublicCanonicalTranslationV1(**row)
    # Only the exact validated frame type may serialize its false safety
    # declarations. Untyped mappings keep the ordinary secret-key rejection.
    _native_require(deterministic_json(restored) == json.dumps(value, ensure_ascii=False, allow_nan=False,
                    separators=(",", ":"), sort_keys=True), "stored translation differs after closed restoration")
    return restored


def _public_candidate_from_translation_v1(*, translation: PublicCanonicalTranslationV1,
        contract: SelectedPITPublicDataContractV2, metadata: tuple[PublicMetadataSnapshotV1, ...],
        parse_completed_at_utc: datetime, parse_completed_monotonic_ns: int) -> PITCanonicalEventCandidateV2:
    """The existing decoder remains the only native candidate payload decoder."""
    _native_require(type(translation) is PublicCanonicalTranslationV1
                    and type(contract) is SelectedPITPublicDataContractV2 and type(metadata) is tuple
                    and all(type(item) is PublicMetadataSnapshotV1 for item in metadata),
                    "native candidate requires exact translation/contract/metadata")
    translation.__post_init__()
    contract.__post_init__()
    _native_require(translation.canonical_contract_ref == contract.contract_id
                    and translation.metadata_refs == tuple(item.metadata_id for item in metadata)
                    and translation.stream_disposition["kind"] == "MARKET_DATA", "native candidate association differs")
    selected = [item for item in metadata if type(item) is PublicMetadataSnapshotV1
                and item.instrument_id == translation.stream_disposition["instrument_id"]]
    _native_require(len(selected) == 1, "native candidate metadata is missing or ambiguous")
    selected = selected[0]
    selected.__post_init__()
    parse_completed_at_utc = _pit_adapter_utc(parse_completed_at_utc, "native parse completed")
    parsed_ns = _native_utc_nanoseconds(parse_completed_at_utc.isoformat())
    _native_require(selected.profile_id is contract.profile_id
                    and selected.generation == translation.stream_disposition["metadata_generation"]
                    and selected.known_at_ns <= parsed_ns < selected.expires_at_ns
                    and selected.effective_from_ns <= parsed_ns
                    and (selected.effective_until_ns_or_none is None or parsed_ns < selected.effective_until_ns_or_none),
                    "native candidate metadata generation changed")
    if selected.price_bands:
        origin, _, increment = selected.price_bands[0]
    else:
        origin, increment = selected.price_origin_or_none, selected.price_increment_or_none
    # An absent quantity origin is not an inferred zero lattice. Retain its
    # explicit metadata limitation; observed sizes aren't new-order minimums.
    quantity_increment = (selected.quantity_increment_or_none if selected.quantity_origin_or_none is not None
                          and Fraction(Decimal(selected.quantity_origin_or_none)) == 0 else None)
    candidate = _decode_pit_frame_v2(contract, translation.normalized_frame,
        event_kind=PITEventKindV2(translation.stream_disposition["event_kind"]),
        parse_completed_at_utc=parse_completed_at_utc, parse_completed_monotonic_ns=parse_completed_monotonic_ns,
        price_increment_text=increment, price_origin_text=origin,
        quantity_increment_text_or_none=quantity_increment, price_bands=selected.price_bands)
    _native_require(candidate.instrument_id == selected.instrument_id and candidate.market_id == selected.market_id,
                    "decoded native candidate market/instrument differs")
    return candidate


def _compile_public_catalog_metadata_v1(*, observation, metadata, source_binding, translation_context):
    """Derive append-only catalog candidates, then verify the exact translation.

    Identity and documentary payoff/origin rules still come from the selected
    upstream inputs. Observable grids and catalog state come from these bytes.
    Only the receiving/publication owner can attach native custody afterwards.
    """
    from dataclasses import replace
    from ..qku_computation_control_plane.receipts import _public_identity_v1
    from ..qku_computation_control_plane.serialization import _native_strict_json

    observed = _translate_public_observation_v1(observation=observation, metadata=metadata,
        source_binding=source_binding, translation_context=translation_context, project_catalog=True)
    request = translation_context["request"]
    payload = observed.normalized_frame.parsed_source_scalar_tree_or_none
    originals = tuple(row for row in observed.field_lineage if row[0] == observation.observation_id)
    _native_require(originals, "catalog metadata has no original material fields")
    successors = []
    for prior in metadata:
        if prior.instrument_id not in request.instrument_ids:
            successors.append(prior)
            continue
        changes = {}
        material = originals
        if request.operation_id == "K_MARKET":
            changes.update(price_bands=tuple((row["start"],row["end"],row["step"])
                for row in payload["market"]["price_ranges"]), price_origin_or_none=None, price_increment_or_none=None)
        elif request.operation_id == "P_MARKET":
            changes.update(price_increment_or_none=payload["orderPriceMinTickSize"],
                           quantity_minimum_or_none=payload["minimumTradeQty"])
            if prior.resolution.get("final") is True:
                _native_require(payload["closed"] or not payload["active"],
                                "catalog reopening conflicts with accepted final resolution")
            elif payload["closed"] or not payload["active"]:
                changes["lifecycle"] = dict(state="CLOSED" if payload["closed"] else "UNAVAILABLE",
                    native_state="closed" if payload["closed"] else "inactive", observation_ref=observation.observation_id,
                    effective_at_ns=observation.received_wall_ns)
        elif request.operation_id in {"G_EVENT", "G_EVENTS"}:
            rows = tuple(row for row in payload["contracts"] if row["instrumentSymbol"] == prior.instrument_id)
            _native_require(len(rows) == 1, "catalog successor has no unique selected contract")
            row = rows[0]
            # Distinguish each contract's source array index; another contract's
            # grid fields cannot become this instrument's material lineage.
            raw = _public_native_tree_v1(base64.urlsafe_b64decode(observation.raw_body_b64
                + "="*(-len(observation.raw_body_b64)%4)), maximum_bytes=1048576)
            prefixes = []
            events = [("",raw)] if request.operation_id == "G_EVENT" else [(f"/data/{i}",event) for i,event in enumerate(raw["data"])]
            for base,event in events:
                if event.get("ticker") == prior.event_id_or_none:
                    prefixes.extend(base+f"/contracts/{i}/" for i,item in enumerate(event["contracts"])
                        if item.get("instrumentSymbol") == prior.instrument_id)
            _native_require(len(prefixes) == 1, "catalog successor contract pointer is ambiguous")
            material = tuple(item for item in originals if item[1].startswith(prefixes[0])
                or item[1] == prefixes[0].split("/contracts/",1)[0]+"/ticker")
            state = ("OPEN" if row["status"] == "active" and row["marketState"] == "open" else
                "SETTLED" if row["status"] == "settled" and row["marketState"] == "closed" else
                "CLOSED" if row["status"] == "closed" and row["marketState"] == "closed" else "UNAVAILABLE")
            _native_require(not (state == "OPEN" and prior.resolution.get("final") is True),
                            "catalog reopening conflicts with accepted final resolution")
            effective = int(_public_exact_clock_v1(row["effectiveDate"],unit="RFC3339")["utc_ns_text"])
            changes.update(price_bands=(), price_origin_or_none=row["priceMinimum"], price_increment_or_none=row["priceIncrement"],
                quantity_increment_or_none=row["quantityIncrement"], quantity_minimum_or_none=row["quantityMinimum"],
                effective_from_ns=effective, lifecycle=dict(state=state,native_state=row["status"]+"/"+row["marketState"],
                    observation_ref=observation.observation_id,effective_at_ns=effective))
        replaced_fields = {item[2] for item in material} | set(changes)
        lineage = tuple(item for item in prior.field_lineage if item[2] not in replaced_fields
            or item[1].startswith("/contract_terms/") and item[2] in {
                "price_origin_or_none", "quantity_origin_or_none", "quantity_increment_or_none"}) + material
        known = max(prior.known_at_ns, observation.received_wall_ns)
        origin_parts = _native_strict_json(observation.observation_id.encode("utf-8"), max_bytes=2048)
        successor = replace(prior, metadata_id=_public_identity_v1("PUBLIC_CATALOG_METADATA_V1",
            *origin_parts[1:], prior.instrument_id, prior.generation+1),
            field_lineage=lineage, known_at_ns=known, generation=prior.generation+1, **changes)
        successors.append(successor)
    successors = tuple(successors)
    projected_request = replace(request, metadata_refs=tuple(row.metadata_id for row in successors))
    projected_context = dict(translation_context, request=projected_request)
    verified = translate_public_observation_v1(observation=observation, metadata=successors,
        source_binding=source_binding, translation_context=projected_context)
    return verified, successors, projected_request


def translate_public_observation_v1(*, observation, metadata: tuple[PublicMetadataSnapshotV1, ...],
                                    source_binding, translation_context: Mapping[str, object]) -> PublicCanonicalTranslationV1:
    return _translate_public_observation_v1(observation=observation, metadata=metadata,
        source_binding=source_binding, translation_context=translation_context, project_catalog=False)


def _translate_public_observation_v1(*, observation, metadata, source_binding, translation_context, project_catalog):
    """Translate original native fields once, under their accepted field bindings.

    The context supplies existing request/contract/clock identities, never an
    event-kind, normalized payload, provider timestamp or success flag.
    """
    from ..qku_computation_control_plane.receipts import (
        PublicNativeObservationV1, _public_identity_v1, _public_canonical_frame_ref_v1,
    )
    from ..qku_computation_control_plane.source_policy import PublicDataSourceBindingV1

    _native_require(type(observation) is PublicNativeObservationV1
                    and type(source_binding) is PublicDataSourceBindingV1,
                    "translation requires exact original and source binding")
    observation.__post_init__()
    _native_require(observation.observation_id == _public_identity_v1("PUBLIC_NATIVE_CAPTURE_V1",
        observation.profile_id.value, observation.source_use_action_ref, observation.capture_session_id,
        observation.connection_epoch, observation.receive_ordinal), "original observation identity differs from capture tuple")
    source_binding.__post_init__()
    _native_require(type(translation_context) in (dict, MappingProxyType)
                    and {"request", "contract", "wall_clock_source_id"} <= set(translation_context)
                    <= {"request", "contract", "wall_clock_source_id", "original_prefix", "source_bindings"},
                    "translation context has missing or extra inputs")
    request, contract = translation_context["request"], translation_context["contract"]
    _native_require(type(contract) is SelectedPITPublicDataContractV2, "missing selected canonical contract")
    contract.__post_init__()
    _native_ident(translation_context["wall_clock_source_id"])
    compile_public_read_request_v1(request=request, source_binding=source_binding, metadata=metadata)
    _native_require(observation.profile_id is request.profile_id is contract.profile_id is source_binding.profile_id
                    and observation.request_ref == request.request_id
                    and observation.operation_id == request.operation_id
                    and observation.native_contract_version == request.native_contract_version
                    and observation.source_binding_refs == (source_binding.binding_id,)
                    and (contract.source_contract_version, contract.source_currentization_receipt_ref,
                         contract.rights_receipt_ref) in tuple(zip(source_binding.source_contract_versions,
                             source_binding.source_receipt_refs, source_binding.rights_receipt_refs)),
                    "original/request/source/contract association differs")
    now = observation.received_wall_ns
    _native_require(source_binding.known_at_ns <= now < source_binding.expires_at_ns
                    and source_binding.effective_from_ns <= now
                    and (source_binding.effective_until_ns_or_none is None
                         or now < source_binding.effective_until_ns_or_none), "source binding unavailable at capture")
    _native_require(observation.response_status_or_none in (None, 200), "non-success body is not market data")
    raw = base64.urlsafe_b64decode(observation.raw_body_b64 + "=" * (-len(observation.raw_body_b64) % 4))
    tree = _public_native_tree_v1(raw, maximum_bytes=1048576)
    prefix = translation_context.get("original_prefix", ())
    _native_require(type(prefix) is tuple and len(prefix) <= 4096
                    and all(type(row) is PublicNativeObservationV1 for row in prefix)
                    and len({row.observation_id for row in prefix}) == len(prefix),
                    "invalid bounded original observation prefix")
    for row in prefix:
        row.__post_init__()
        _native_require(row.capture_session_id == observation.capture_session_id
                        and row.profile_id is observation.profile_id and row.scope_generation == observation.scope_generation
                        and row.source_use_action_ref == observation.source_use_action_ref
                        and row.connection_epoch <= observation.connection_epoch
                        and row.received_wall_ns <= observation.received_wall_ns
                        and row.received_monotonic_ns <= observation.received_monotonic_ns,
                        "original prefix is outside the current receiving custody")
    source_bindings = translation_context.get("source_bindings", (source_binding,))
    _native_require(type(source_bindings) is tuple and 0 < len(source_bindings) <= 4096
                    and all(type(row) is PublicDataSourceBindingV1 for row in source_bindings)
                    and len({row.binding_id for row in source_bindings}) == len(source_bindings),
                    "invalid original metadata source selection")
    for row in source_bindings:
        row.__post_init__()
        _native_require(row.profile_id is observation.profile_id, "cross-profile metadata source")
    lineage = []

    def field(pointer, wire, transform="EXACT_IDENTITY", *, original=observation, native_tree=tree, native_source=source_binding, nullable=False):
        value = native_tree
        for segment in pointer[1:].split("/"):
            segment = segment.replace("~1", "/").replace("~0", "~")
            if type(value) is dict:
                _native_require(segment in value, "required native field absent: " + pointer)
                value = value[segment]
            else:
                _native_require(type(value) is list and segment.isascii() and segment.isdigit()
                                and str(int(segment)) == segment and int(segment) < len(value),
                                "invalid native array pointer: " + pointer)
                value = value[int(segment)]
        matches = [row for row in native_source.field_bindings
                   if row[1] == wire and row[4] == pointer and row[5] == transform]
        _native_require(len(matches) == 1, "native field has no unique compatible source binding: " + pointer)
        expected = {"STRING": str, "INTEGER": int, "DECIMAL_TEXT": str,
                    "BOOLEAN": bool, "OBJECT": dict, "ARRAY": list}
        if value is None and nullable:
            pass
        elif wire == "DECIMAL_NUMBER":
            _native_require(type(value) in (int, Decimal), "native decimal number required")
        else:
            _native_require(type(value) is expected[wire], "native field type differs: " + pointer)
        name = matches[0][0]
        row = (original.observation_id, pointer, name, transform)
        if row not in lineage:
            lineage.append(row)
        return value

    def decimal_number(pointer, *, signed=False, **origin):
        from ..qku_computation_control_plane.context import _finite_decimal_text_v1

        value = field(pointer, "DECIMAL_NUMBER", "EXACT_DECIMAL_NUMBER_TO_TEXT", **origin)
        _native_require((signed or value >= 0) and not (type(value) is Decimal and value.is_zero() and value.is_signed()),
                        "invalid native nonnegative decimal number")
        return _finite_decimal_text_v1(Fraction(value))

    def decimal(pointer, *, maximum_scale=None, signed=False):
        text = field(pointer, "DECIMAL_TEXT", "EXACT_DECIMAL_TEXT")
        _, value, scale = _pit_decimal_text(text, pointer)
        _native_require(not (value.is_zero() and value.is_signed())
                        and (signed or value >= 0)
                        and (maximum_scale is None or scale <= maximum_scale), "invalid native decimal domain")
        return text

    def accepted_metadata(instrument):
        matches = [row for row in metadata if row.instrument_id == instrument]
        _native_require(instrument in request.instrument_ids and len(matches) == 1, "native instrument/metadata mismatch")
        result = matches[0]
        _native_require(result.known_at_ns <= now < result.expires_at_ns
                        and result.effective_from_ns <= now
                        and (result.effective_until_ns_or_none is None or now < result.effective_until_ns_or_none),
                        "metadata unavailable at original capture")
        for row in result.field_lineage:
            if row not in lineage:
                lineage.append(row)
        return result

    received = _public_exact_clock_v1(now, unit="NANOSECONDS")
    provider = sending = None
    disposition = {"kind": "MARKET_DATA"}
    normalized = {}
    op = request.operation_id
    _native_require(type(project_catalog) is bool and (not project_catalog or op in {
        "K_MARKET", "K_EVENT", "K_SERIES", "P_MARKET", "G_EVENT", "G_EVENTS"}),
        "metadata projection is restricted to the selected catalog operations")
    wire_dialect = contract.wire_dialect_policy
    if op in {"K_STATUS", "K_HISTORY_CUTOFF", "K_SERIES_FEES", "K_EVENT_FEES", "K_HISTORY_TRADES", "P_SETTLEMENT"}:
        # These are retained observations with their own known-at axis. They
        # never stand in for a current book, private fill, account quota or cash.
        disposition = dict(kind="PUBLIC_REFERENCE", operation_id=op, instrument_ids=request.instrument_ids)
        channel = "PUBLIC_REFERENCE"
        normalized = dict(operation_id=op, known_at_ns=now)
        if op == "K_STATUS":
            normalized.update(exchange_active=field("/exchange_active", "BOOLEAN"),
                              trading_active=field("/trading_active", "BOOLEAN"))
            if "exchange_estimated_resume_time" in tree:
                value = field("/exchange_estimated_resume_time", "STRING", "EXACT_RFC3339", nullable=True)
                normalized["exchange_estimated_resume_time"] = (None if value is None
                    else _public_exact_clock_v1(value, unit="RFC3339")["source_text"])
            if "exchange_index_statuses" in tree:
                indices, seen = [], set()
                for index, row in enumerate(field("/exchange_index_statuses", "ARRAY")):
                    _native_require(type(row) is dict and index < 4096, "invalid exchange status row")
                    base = f"/exchange_index_statuses/{index}"
                    shard = field(base+"/exchange_index", "INTEGER")
                    _public_counter_v1(shard, allow_zero=True)
                    _native_require(shard not in seen, "duplicate exchange status index")
                    seen.add(shard)
                    indices.append(dict(exchange_index=shard, exchange_active=field(base+"/exchange_active", "BOOLEAN"),
                                        trading_active=field(base+"/trading_active", "BOOLEAN")))
                normalized["exchange_index_statuses"] = tuple(indices)
            # Top-level status is only index zero. No account or selected-market
            # shard is inferred from its mere presence.
            normalized["top_level_exchange_index"] = 0
        elif op == "K_HISTORY_CUTOFF":
            for name in ("market_settled_ts", "trades_created_ts", "orders_updated_ts"):
                value = field("/"+name, "STRING", "EXACT_RFC3339")
                normalized[name] = _public_exact_clock_v1(value, unit="RFC3339")["source_text"]
            if "market_positions_last_updated_ts" in tree:
                value = field("/market_positions_last_updated_ts", "STRING", "EXACT_RFC3339")
                normalized["market_positions_last_updated_ts"] = _public_exact_clock_v1(value, unit="RFC3339")["source_text"]
        elif op in {"K_SERIES_FEES", "K_EVENT_FEES"}:
            event_override = op == "K_EVENT_FEES"
            key = "event_fee_changes" if event_override else "series_fee_change_arr"
            projected, seen = [], set()
            native_rows = field("/"+key, "ARRAY")
            _native_require(len(native_rows) <= (request.request_options["limit"] if event_override else 4096),
                            "fee history exceeds its bounded requested response")
            for index, row in enumerate(native_rows):
                _native_require(type(row) is dict, "fee change must be an object")
                base = f"/{key}/{index}"
                identity, series = field(base+"/id", "STRING"), field(base+"/series_ticker", "STRING")
                _native_ident(identity)
                _native_require(identity not in seen and series in {row.series_id_or_none for row in metadata},
                                "duplicate or unselected Series fee history")
                seen.add(identity)
                result = dict(id=identity, series_ticker=series)
                if event_override:
                    event = field(base+"/event_ticker", "STRING")
                    _native_require(event == request.request_options["event_ticker"] and any(
                        row.event_id_or_none == event and row.series_id_or_none == series for row in metadata),
                        "Event fee history parent identity differs")
                    result["event_ticker"] = event
                else:
                    _native_require(series == request.request_options["series_ticker"], "Series fee history request identity differs")
                suffix = "_override" if event_override else ""
                family = field(base+"/fee_type"+suffix, "STRING", nullable=event_override)
                multiplier = field(base+"/fee_multiplier"+suffix, "DECIMAL_NUMBER", "EXACT_DECIMAL_NUMBER_TO_TEXT", nullable=event_override)
                _native_require((family is None) == (multiplier is None), "Event fee clear requires an exact null/null pair")
                if family is not None:
                    _native_ident(family)
                    _native_require(multiplier >= 0 and not (type(multiplier) is Decimal and multiplier.is_zero() and multiplier.is_signed()),
                                    "invalid native fee multiplier")
                    multiplier = _native_retail_finite_decimal_text_v1(Fraction(multiplier))
                result.update(fee_type=family, fee_multiplier=multiplier,
                    override_cleared=event_override and family is None,
                    scheduled_at=_public_exact_clock_v1(field(base+"/scheduled_ts", "STRING", "EXACT_RFC3339"), unit="RFC3339"))
                projected.append(result)
            normalized["fee_changes"] = tuple(projected)
            if event_override:
                normalized["cursor"] = field("/cursor", "STRING")
        elif op == "K_HISTORY_TRADES":
            rows = field("/trades", "ARRAY")
            _native_require(len(rows) <= request.request_options["limit"], "historical response exceeds selected page size")
            projected, seen = [], set()
            for index, row in enumerate(rows):
                _native_require(type(row) is dict, "historical trade must be an object")
                base = f"/trades/{index}"
                ticker, identity = field(base+"/ticker", "STRING"), field(base+"/trade_id", "STRING")
                _native_ident(identity)
                _native_require(ticker == request.request_options["ticker"] and identity not in seen,
                                "historical trade identity differs or is duplicated")
                seen.add(identity)
                selected = accepted_metadata(ticker)
                yes, no = decimal(base+"/yes_price_dollars", maximum_scale=4), decimal(base+"/no_price_dollars", maximum_scale=4)
                _native_require(selected.payout_basis_or_none == "USD_PER_CONTRACT" and selected.payout_amount_or_none is not None
                    and Fraction(yes)+Fraction(no) == Fraction(selected.payout_amount_or_none), "historical trade payout basis differs")
                for price in (yes,no):
                    _public_on_price_grid_v1(price, bands=selected.price_bands,
                        origin=selected.price_origin_or_none, increment=selected.price_increment_or_none)
                count = decimal(base+"/count_fp", maximum_scale=2)
                side = field(base+"/taker_side", "STRING")
                _native_require(Fraction(count) > 0 and side in {"yes", "no"}, "invalid historical trade quantity/side")
                clock = _public_exact_clock_v1(field(base+"/created_time", "STRING", "EXACT_RFC3339"), unit="RFC3339")
                _native_require(request.time_bounds_or_none[0]*1_000_000_000 <= int(clock["utc_ns_text"])
                    <= request.time_bounds_or_none[1]*1_000_000_000, "historical trade lies outside requested time bounds")
                projected.append(dict(ticker=ticker, trade_id=identity, yes_price_dollars=yes, no_price_dollars=no,
                    count_fp=count, taker_side=side, provider_event_clock=clock))
            normalized.update(trades=tuple(projected), cursor=field("/cursor", "STRING"))
        else:
            instrument = field("/slug", "STRING")
            _native_require(instrument == request.request_options["slug"], "settlement slug differs from requested market")
            selected = accepted_metadata(instrument)
            normalized.update(instrument_id=instrument, market_id=selected.market_id,
                observed_settlement=decimal_number("/settlement", signed=True), finality="UNAVAILABLE_SEPARATE_ACCEPTED_RESOLUTION_REQUIRED",
                accounting_class="PUBLIC_OBSERVATION_NOT_ACCOUNT_CASH")
        if "cursor" in normalized:
            cursor = normalized["cursor"]
            _native_require(len(cursor) <= 1024 and all(ord(char) >= 32 and ord(char) != 127 for char in cursor),
                            "invalid bounded response cursor")
    elif op in {"P_MARKET", "P_BOOK", "P_WS"}:
        wire_dialect = "POLYMARKET_RETAIL_CAMEL_STRING_V1"
        retail_trade = op == "P_WS" and request.request_options["subscribe"]["subscriptionType"] == "SUBSCRIPTION_TYPE_TRADE"
        if op == "P_MARKET":
            instrument = field("/market/slug", "STRING")
        else:
            instrument = field("/trade/marketSlug" if retail_trade else "/marketData/marketSlug", "STRING")
        selected = accepted_metadata(instrument)
        if op in {"P_MARKET", "P_BOOK"}:
            _native_require(request.request_options["slug"] == instrument, "Retail returned slug differs from request")
        else:
            sub = request.request_options["subscribe"]
            _native_require(field("/requestId", "STRING") == sub["requestId"]
                            and field("/subscriptionType", "STRING") == sub["subscriptionType"]
                            and instrument in sub["marketSlugs"], "Retail book is outside the selected subscription")
        if op == "P_MARKET":
            metadata_original, metadata_tree, metadata_source = observation, tree, source_binding
        else:
            original_refs = {row[0] for row in selected.field_lineage if row[1] == "/market/marketSides"}
            originals = [row for row in prefix if row.observation_id in original_refs and row.operation_id == "P_MARKET"]
            _native_require(len(originals) == 1, "Retail book requires its retained exact market metadata original")
            metadata_original = originals[0]
            metadata_tree = _public_native_tree_v1(base64.urlsafe_b64decode(metadata_original.raw_body_b64
                + "=" * (-len(metadata_original.raw_body_b64) % 4)), maximum_bytes=1048576)
            sources = [row for row in source_bindings if metadata_original.source_binding_refs == (row.binding_id,)]
            _native_require(len(sources) == 1, "Retail metadata original has no unique admitted source")
            metadata_source = sources[0]
        _native_require("P_MARKET" in metadata_source.allowed_operation_ids
                        and metadata_original.response_status_or_none == 200
                        and metadata_original.native_contract_version in metadata_source.source_contract_versions
                        and metadata_source.known_at_ns <= now < metadata_source.expires_at_ns
                        and metadata_source.effective_from_ns <= now
                        and (metadata_source.effective_until_ns_or_none is None or now < metadata_source.effective_until_ns_or_none),
                        "Retail metadata original source unavailable")
        origin = dict(original=metadata_original, native_tree=metadata_tree, native_source=metadata_source)
        market = field("/market/id", "STRING", **origin)
        slug = field("/market/slug", "STRING", **origin)
        sides = field("/market/marketSides", "ARRAY", **origin)
        tick = decimal_number("/market/orderPriceMinTickSize", **origin)
        minimum = decimal_number("/market/minimumTradeQty", **origin)
        # The Boolean flags are retained facts, not a replacement for the
        # separately source-bound complete lifecycle/finality policy.
        active = field("/market/active", "BOOLEAN", **origin)
        closed = field("/market/closed", "BOOLEAN", **origin)
        required_pointers = {"/market/id", "/market/slug", "/market/marketSides",
                             "/market/orderPriceMinTickSize", "/market/minimumTradeQty"}
        required_lineage = [row for row in lineage if row[0] == metadata_original.observation_id and row[1] in required_pointers]
        _native_require(len(required_lineage) == len(required_pointers)
                        and (project_catalog or all(row in selected.field_lineage for row in required_lineage))
                        and market == selected.market_id and slug == selected.instrument_id
                        and (project_catalog or tick == selected.price_increment_or_none and minimum == selected.quantity_minimum_or_none)
                        and len(sides) >= 2 and all(type(side) is dict and side for side in sides),
                        "Retail metadata fields differ from their exact accepted identity/grid/side lineage")
        normalized = dict(marketId=market, marketSlug=slug, marketSides=sides, orderPriceMinTickSize=tick)
        if op == "P_MARKET":
            normalized.update(minimumTradeQty=minimum, active=active, closed=closed)
            disposition = dict(kind="METADATA", instrument_id=instrument, metadata_generation=selected.generation)
            channel = "PUBLIC_METADATA"
        elif retail_trade:
            _native_require("marketData" not in tree and "marketDataLite" not in tree,
                            "ambiguous Retail trade/book envelope")
            _native_require(field("/trade/price/currency", "STRING") == "USD", "Retail trade currency is not USD")
            price = decimal("/trade/price/value")
            _public_on_price_grid_v1(price, bands=selected.price_bands,
                origin=selected.price_origin_or_none, increment=selected.price_increment_or_none)
            provider = _public_exact_clock_v1(field("/trade/tradeTime", "STRING", "EXACT_RFC3339"), unit="RFC3339")
            normalized.update(price=price, transactTime=provider["receipt_utc_floor"],
                quantityUnavailableReason="PIT_NATIVE_QUANTITY_BASIS_UNAVAILABLE")
            quantity_bindings = [row for row in source_binding.field_bindings
                if row[4] == "/trade/quantity/value" and row[1] == "DECIMAL_TEXT"
                and row[2] == "CONTRACT_COUNT" and row[5] == "EXACT_DECIMAL_TEXT"]
            if quantity_bindings:
                _native_require(len(quantity_bindings) == 1, "ambiguous Retail trade quantity basis")
                normalized["quantity"] = decimal("/trade/quantity/value")
                del normalized["quantityUnavailableReason"]
            channel = "markets"
            disposition.update(event_kind="TRADE", instrument_id=instrument, metadata_generation=selected.generation)
        else:
            _native_require("trade" not in tree and "marketDataLite" not in tree, "ambiguous Retail book envelope")
            normalized["state"] = field("/marketData/state", "STRING")
            # This optional field limits settlement finality, never book access.
            # An absent/unbound field stays unknown; false is not finality proof.
            preliminary_pointer = "/marketData/stats/settlementPreliminaryFlag"
            stats = tree["marketData"].get("stats")
            preliminary = None
            if type(stats) is dict and "settlementPreliminaryFlag" in stats:
                matching = tuple(row for row in source_binding.field_bindings
                    if row[1] == "BOOLEAN" and row[4] == preliminary_pointer and row[5] == "EXACT_IDENTITY")
                if len(matching) == 1:
                    preliminary = field(preliminary_pointer, "BOOLEAN")
            normalized["settlement_preliminary_or_none"] = preliminary
            provider = _public_exact_clock_v1(field("/marketData/transactTime", "STRING", "EXACT_RFC3339"), unit="RFC3339")
            normalized["transactTime"] = provider["receipt_utc_floor"]
            for side in ("bids", "offers"):
                pointer = "/marketData/"+side
                levels = field(pointer, "ARRAY")
                converted = []
                for index, _level in enumerate(levels):
                    base = pointer+"/"+str(index)
                    _native_require(field(base+"/px/currency", "STRING") == "USD", "Retail native book currency is not USD")
                    price = decimal_number(base+"/px/value") if op == "P_BOOK" else decimal(base+"/px/value")
                    quantity = decimal(base+"/qty")
                    _public_on_price_grid_v1(price, bands=selected.price_bands,
                        origin=selected.price_origin_or_none, increment=selected.price_increment_or_none)
                    converted.append((price, quantity))
                normalized[side] = tuple(converted)
            channel = "REST_BOOK" if op == "P_BOOK" else "markets"
            disposition.update(event_kind="BOOK_REPLACEMENT", instrument_id=instrument, metadata_generation=selected.generation)
    elif op in {"K_MARKET", "K_EVENT", "K_SERIES"}:
        base = {"K_MARKET": "/market", "K_EVENT": "/event", "K_SERIES": "/series"}[op]
        envelope = field(base, "OBJECT")
        identity_name = "event_ticker" if op == "K_EVENT" else "ticker"
        identity = field(base + "/" + identity_name, "STRING")
        expected = request.request_options[{"K_MARKET": "ticker", "K_EVENT": "event_ticker",
                                            "K_SERIES": "series_ticker"}[op]]
        _native_require(identity == expected, "Kalshi metadata identity differs from the request")
        rows = tuple(accepted_metadata(instrument) for instrument in request.instrument_ids)
        if op == "K_MARKET":
            _native_require(len(rows) == 1 and rows[0].instrument_id == identity,
                            "Kalshi market response has an ambiguous selected instrument")
            selected = rows[0]
            event = field(base + "/event_ticker", "STRING")
            _native_require(event == selected.event_id_or_none, "Kalshi market/event metadata join differs")
            if "market_id" in envelope:
                _native_require(field(base + "/market_id", "STRING") == selected.market_id,
                                "Kalshi metadata market id differs")
            ranges = field(base + "/price_ranges", "ARRAY", "SOURCE_PRICE_BAND")
            _native_require(0 < len(ranges) <= 256, "Kalshi market price bands unavailable")
            bands = tuple(tuple(decimal(base + f"/price_ranges/{index}/" + key, maximum_scale=4)
                                for key in ("start", "end", "step")) for index, row in enumerate(ranges))
            from ..qku_computation_control_plane.context import _public_price_bands_v1
            _public_price_bands_v1(bands)
            _native_require(project_catalog or bands == selected.price_bands, "Kalshi metadata bands changed; refresh required")
            required = {base + "/ticker", base + "/event_ticker", base + "/price_ranges",
                        *(base + f"/price_ranges/{index}/" + key for index in range(len(bands))
                          for key in ("start", "end", "step"))}
            material = tuple(row for row in lineage if row[0] == observation.observation_id and row[1] in required)
            _native_require(len(material) == len(required) and (project_catalog or all(row in selected.field_lineage for row in material)),
                            "Kalshi metadata lacks exact original band/identity lineage")
            normalized = {"market": dict(ticker=identity, event_ticker=event,
                price_ranges=tuple(dict(start=low, end=high, step=step) for low, high, step in bands))}
        elif op == "K_EVENT":
            series = field(base + "/series_ticker", "STRING")
            _native_require(all(row.event_id_or_none == identity and row.series_id_or_none == series for row in rows),
                            "Kalshi event/Series metadata join differs")
            normalized = {"event": dict(event_ticker=identity, series_ticker=series)}
            required = {base + "/event_ticker", base + "/series_ticker"}
        else:
            _native_require(all(row.series_id_or_none == identity for row in rows), "Kalshi Series metadata join differs")
            normalized = {"series": dict(ticker=identity)}
            required = {base + "/ticker"}
        material = tuple(row for row in lineage if row[0] == observation.observation_id and row[1] in required)
        _native_require(len(material) == len(required) and (project_catalog or all(
            all(fact in row.field_lineage for fact in material) for row in rows)),
            "Kalshi metadata lacks exact original identity lineage")
        # Fee fields remain fee-selector inputs. A catalog does not supply an
        # account schedule, a default multiplier or a cashflow on its own.
        channel = "PUBLIC_METADATA"
        disposition = dict(kind="METADATA", instrument_generations=tuple((row.instrument_id,row.generation) for row in rows))
    elif op in {"G_EVENT", "G_EVENTS"}:
        # One catalog response can cover several selected contracts. Keep their
        # distinct generations; a first-row projection cannot stand for them all.
        events = [("", tree)] if op == "G_EVENT" else [
            (f"/data/{index}", row) for index, row in enumerate(field("/data", "ARRAY"))]
        selected_events = {row.event_id_or_none for row in metadata if row.instrument_id in request.instrument_ids}
        _native_require(None not in selected_events, "Gemini event identity is unavailable")
        projected, seen = [], set()
        for base, event in events:
            _native_require(type(event) is dict, "Gemini event must be an object")
            # Unselected discovery rows and nested sibling events remain inert.
            if op == "G_EVENTS" and event.get("ticker") not in selected_events:
                continue
            ticker = field(base + "/ticker", "STRING")
            _native_require(ticker in selected_events and (op != "G_EVENT"
                            or ticker == request.request_options["eventTicker"]),
                            "Gemini root event identity differs from the request")
            contracts = field(base + "/contracts", "ARRAY")
            for index, native in enumerate(contracts):
                _native_require(type(native) is dict, "Gemini contract must be an object")
                if native.get("instrumentSymbol") not in request.instrument_ids:
                    continue
                pointer = base + f"/contracts/{index}"
                instrument = field(pointer + "/instrumentSymbol", "STRING")
                selected = accepted_metadata(instrument)
                _native_require(instrument not in seen and selected.event_id_or_none == ticker,
                                "duplicate or cross-event Gemini contract")
                seen.add(instrument)
                identity = field(pointer + "/id", "STRING")
                contract_ticker = field(pointer + "/ticker", "STRING")
                facts = {key: decimal(pointer + "/" + key) for key in (
                    "quantityIncrement", "quantityMinimum", "priceIncrement", "priceMinimum")}
                _native_require(identity == selected.market_id and (project_catalog or not selected.price_bands
                    and facts["priceMinimum"] == selected.price_origin_or_none
                    and facts["priceIncrement"] == selected.price_increment_or_none
                    and facts["quantityIncrement"] == selected.quantity_increment_or_none
                    and facts["quantityMinimum"] == selected.quantity_minimum_or_none),
                    "Gemini metadata identity/grid differs from its accepted version")
                status = field(pointer + "/status", "STRING")
                market_state = field(pointer + "/marketState", "STRING")
                state = ("OPEN" if status == "active" and market_state == "open" else
                         "SETTLED" if status == "settled" and market_state == "closed" else
                         "CLOSED" if status == "closed" and market_state == "closed" else
                         "UNAVAILABLE")
                _native_require(project_catalog or selected.lifecycle["state"] == state,
                                "Gemini lifecycle changed; accepted metadata refresh required")
                effective = _public_exact_clock_v1(field(pointer + "/effectiveDate", "STRING", "EXACT_RFC3339"),
                                                  unit="RFC3339")
                _native_require(project_catalog or int(effective["utc_ns_text"]) == selected.effective_from_ns,
                                "Gemini metadata effective time differs")
                result = dict(instrumentSymbol=instrument, marketId=identity, ticker=contract_ticker,
                    eventTicker=ticker, status=status, marketState=market_state,
                    effectiveDate=effective["source_text"], **facts)
                for key in ("resolutionSide", "resolvedAt"):
                    if native.get(key) is not None:
                        value = field(pointer + "/" + key, "STRING",
                                      "EXACT_RFC3339" if key == "resolvedAt" else "EXACT_IDENTITY")
                        if key == "resolvedAt":
                            value = _public_exact_clock_v1(value, unit="RFC3339")["source_text"]
                        else:
                            _native_require(value in {"yes", "no"}, "Gemini resolution outcome unavailable")
                        result[key] = value
                # SettlementValue is the underlying observation, never payout.
                required = {base + "/ticker", *(pointer + "/" + key for key in (
                    "instrumentSymbol", "id", "ticker", "quantityIncrement", "quantityMinimum",
                    "priceIncrement", "priceMinimum", "status", "marketState", "effectiveDate"))}
                material = tuple(row for row in lineage if row[0] == observation.observation_id and row[1] in required)
                _native_require(len(material) == len(required) and (project_catalog or all(row in selected.field_lineage for row in material)),
                                "Gemini metadata lacks exact original field lineage")
                projected.append(result)
        _native_require(seen == set(request.instrument_ids), "Gemini selected contract is absent from the root catalog")
        normalized, channel = {"contracts": tuple(projected)}, "PUBLIC_METADATA"
        disposition = dict(kind="METADATA", instrument_generations=tuple(
            (row.instrument_id, row.generation) for row in metadata if row.instrument_id in seen))
    elif op == "G_WS" and tree.get("e") == "contractStatus":
        options = request.request_options
        _native_require(options["method"] == "SUBSCRIBE" and "contractStatus" in options["params"],
                        "Gemini lifecycle message is outside the global subscription")
        _native_require(field("/e", "STRING") == "contractStatus", "invalid Gemini lifecycle discriminator")
        instrument = field("/s", "STRING")
        event_ticker, contract_ticker = field("/k", "STRING"), field("/c", "STRING")
        identity = field("/i", "INTEGER", "METADATA_IDENTITY_JOIN")
        _public_counter_v1(identity, allow_zero=True)
        previous_status, native_status = field("/o", "STRING"), field("/n", "STRING")
        provider = _public_exact_clock_v1(field("/E", "INTEGER", "DECLARED_MILLISECONDS_TO_NS"), unit="MILLISECONDS")
        normalized = dict(instrumentSymbol=instrument, marketId=str(identity), eventTicker=event_ticker,
            contractTicker=contract_ticker, previousStatus=previous_status, status=native_status,
            E=provider["receipt_utc_floor"])
        if "p" in tree:
            normalized["underlyingStrike"] = decimal("/p")
        channel = "prediction_markets.contractStatus"
        if instrument not in request.instrument_ids:
            _native_require(all(row.market_id != str(identity) for row in metadata),
                            "Gemini lifecycle symbol differs for a selected contract identity")
            disposition = dict(kind="UNSELECTED_LIFECYCLE", instrument_id=instrument)
        else:
            selected = accepted_metadata(instrument)
            _native_require(str(identity) == selected.market_id and event_ticker == selected.event_id_or_none,
                            "Gemini lifecycle event/contract identity differs from accepted metadata")
            ticker_lineage = tuple(row for row in selected.field_lineage
                                  if "/contracts/" in row[1] and row[1].endswith("/ticker"))
            _native_require(len(ticker_lineage) == 1, "Gemini lifecycle contract ticker binding unavailable")
            original_id, pointer, _name, transform = ticker_lineage[0]
            originals = tuple(row for row in prefix if row.observation_id == original_id and row.operation_id in {"G_EVENT", "G_EVENTS"})
            _native_require(len(originals) == 1, "Gemini lifecycle lacks its retained catalog original")
            original = originals[0]
            matching_sources = tuple(row for row in source_bindings if row.binding_id in original.source_binding_refs)
            _native_require(len(matching_sources) == 1, "Gemini catalog source association unavailable")
            catalog = _public_native_tree_v1(base64.urlsafe_b64decode(original.raw_body_b64+"="*(-len(original.raw_body_b64)%4)),
                                            maximum_bytes=1048576)
            bound_ticker = field(pointer, "STRING", transform, original=original, native_tree=catalog,
                                 native_source=matching_sources[0])
            _native_require(bound_ticker == contract_ticker, "Gemini lifecycle contract ticker differs")
            state = {"Active": "OPEN", "Closed": "CLOSED", "Under Review": "UNDER_REVIEW",
                     "Settled": "SETTLED", "Invalid": "VOID"}.get(native_status, "UNAVAILABLE")
            disposition.update(event_kind="LIFECYCLE", instrument_id=instrument,
                               metadata_generation=selected.generation, lifecycle_state=state)
    elif op == "G_WS":
        options = request.request_options
        if "id" in tree or "status" in tree or "result" in tree or "error" in tree:
            identifier = field("/id", "STRING")
            status = field("/status", "INTEGER")
            _native_require(identifier == options["id"] and status == 200 and "result" in tree
                            and "error" not in tree, "unmatched or failed Gemini control response")
            # The documented result is retained inert in the original, never an
            # economic value or proof that a full book has already arrived.
            disposition = {"kind": "CONTROL", "message_type": "ok", "request_id": identifier}
            normalized, channel = dict(disposition), "PUBLIC_CONTROL"
        else:
            _native_require(options["method"] == "SUBSCRIBE", "Gemini data does not belong to a subscription")
            instrument = field("/s", "STRING")
            selected = accepted_metadata(instrument)
            normalized = {"instrumentSymbol": instrument, "marketId": selected.market_id}
            variants = []
            if {"U", "u", "b", "a"} <= tree.keys() and type(tree["b"]) is list and type(tree["a"]) is list:
                variants.append("depth")
            if {"u", "b", "B", "a", "A"} <= tree.keys() and type(tree["b"]) is str and type(tree["a"]) is str:
                variants.append("bookTicker")
            if {"t", "p", "q", "m"} <= tree.keys():
                variants.append("trade")
            _native_require(len(variants) == 1, "Gemini public message has no unique admitted field shape")
            variant = variants[0]
            _native_require(instrument+"@"+variant in options["params"], "Gemini message is outside the selected channel")
            provider = _public_exact_clock_v1(field("/E", "INTEGER", "DECLARED_NANOSECONDS"), unit="NANOSECONDS")
            normalized["E"] = provider["receipt_utc_floor"]
            if variant == "depth":
                epoch_prefix = tuple(row for row in prefix if row.connection_epoch == observation.connection_epoch)
                _native_require("original_prefix" in translation_context
                                and tuple(row.receive_ordinal for row in epoch_prefix) == tuple(range(1, observation.receive_ordinal))
                                and all(row.request_ref == request.request_id for row in epoch_prefix),
                                "Gemini anchor requires the complete original connection prefix")
                anchor_range = None
                for row in epoch_prefix:
                    prior = _public_native_tree_v1(base64.urlsafe_b64decode(row.raw_body_b64+"="*(-len(row.raw_body_b64)%4)),
                                                  maximum_bytes=1048576)
                    if prior.get("s") == instrument and {"U", "u", "b", "a"} <= prior.keys():
                        _native_require(type(prior["b"]) is list and type(prior["a"]) is list,
                                        "ambiguous Gemini prefix depth shape")
                        if anchor_range is None:
                            anchor_range = (prior["U"], prior["u"])
                for name in ("U", "u"):
                    normalized[name] = field("/"+name, "INTEGER")
                    _public_counter_v1(normalized[name], allow_zero=True)
                _native_require(normalized["U"] <= normalized["u"], "Gemini depth range is inverted")
                for native_side in ("b", "a"):
                    levels = field("/"+native_side, "ARRAY")
                    _native_require(all(type(level) is list and len(level) == 2 for level in levels),
                                    "Gemini depth requires exact price/quantity pairs")
                    normalized[native_side] = tuple((decimal(f"/{native_side}/{index}/0"),
                                                     decimal(f"/{native_side}/{index}/1"))
                        for index, _level in enumerate(levels))
                    for price, _quantity in normalized[native_side]:
                        _public_on_price_grid_v1(price, bands=selected.price_bands,
                            origin=selected.price_origin_or_none, increment=selected.price_increment_or_none)
                # Repeated or conflicting reuse of the first range retains the
                # original snapshot payload kind for the reducer's comparison.
                event_kind = ("BOOK_SNAPSHOT" if anchor_range is None
                    or anchor_range == (normalized["U"], normalized["u"]) else "BOOK_DELTA")
            elif variant == "bookTicker":
                normalized.update(u=field("/u", "INTEGER"), best_bid=decimal("/b"),
                    bid_quantity=decimal("/B"), best_ask=decimal("/a"), ask_quantity=decimal("/A"))
                _public_counter_v1(normalized["u"], allow_zero=True)
                _native_require(Fraction(normalized["best_bid"]) <= Fraction(normalized["best_ask"]), "crossed Gemini BBO")
                for name in ("best_bid", "best_ask"):
                    _public_on_price_grid_v1(normalized[name], bands=selected.price_bands,
                        origin=selected.price_origin_or_none, increment=selected.price_increment_or_none)
                event_kind = "BBO"
            else:
                identifier = field("/t", "INTEGER")
                _public_counter_v1(identifier, allow_zero=True)
                normalized.update(tradeId=str(identifier), price=decimal("/p"), quantity=decimal("/q"),
                                  buyer_is_maker=field("/m", "BOOLEAN"))
                _public_on_price_grid_v1(normalized["price"], bands=selected.price_bands,
                    origin=selected.price_origin_or_none, increment=selected.price_increment_or_none)
                event_kind = "TRADE"
            # The internal frame uses the established canonical surface; the
            # exact native subscription remains in the retained request/original.
            channel = {"depth": "prediction_markets.depth", "bookTicker": "prediction_markets.bookTicker",
                       "trade": "prediction_markets.trades"}[variant]
            disposition.update(event_kind=event_kind, instrument_id=instrument, metadata_generation=selected.generation)
    elif op == "K_WS" and tree.get("type") in {"event_lifecycle","event_fee_update"}:
        _native_require(request.request_options["cmd"] == "subscribe"
            and "market_lifecycle_v2" in request.request_options["params"]["channels"],
            "Kalshi Event notification is outside the global subscription")
        kind = field("/type","STRING")
        event = field("/msg/event_ticker","STRING")
        _native_ident(event)
        selected = tuple(accepted_metadata(instrument) for instrument in request.instrument_ids
            if any(row.instrument_id == instrument and row.event_id_or_none == event for row in metadata))
        message = dict(event_ticker=event)
        if kind == "event_lifecycle":
            series = field("/msg/series_ticker","STRING")
            _native_ident(series)
            _native_require(all(row.series_id_or_none == series for row in selected),
                            "Event lifecycle Series parent differs from selected metadata")
            message["series_ticker"] = series
        else:
            family = field("/msg/fee_type_override","STRING",nullable=True)
            multiplier = field("/msg/fee_multiplier_override","DECIMAL_NUMBER","EXACT_DECIMAL_NUMBER_TO_TEXT",nullable=True)
            _native_require((family is None) == (multiplier is None), "Event fee notification clear requires null/null")
            if family is not None:
                _native_ident(family)
                _native_require(multiplier >= 0 and not (type(multiplier) is Decimal and multiplier.is_zero() and multiplier.is_signed()),
                                "invalid Event fee notification multiplier")
                multiplier = _native_retail_finite_decimal_text_v1(Fraction(multiplier))
            message.update(fee_type_override=family,fee_multiplier_override=multiplier)
        normalized = dict(type=kind,msg=message)
        for name in ("sid","seq"):
            normalized[name] = field("/"+name,"INTEGER")
            _public_counter_v1(normalized[name],allow_zero=name == "seq")
            _native_require(name not in tree["msg"] or type(tree["msg"][name]) is int and tree["msg"][name] == normalized[name],
                            "conflicting root/nested Event notification sequence")
        if "sending_ts_ms" in tree:
            sending = _public_exact_clock_v1(field("/sending_ts_ms","INTEGER","DECLARED_MILLISECONDS_TO_NS"),unit="MILLISECONDS")
        channel = "market_lifecycle_v2"
        disposition = dict(kind="PUBLIC_REFERENCE",operation_id="K_WS",notification_type=kind,event_id=event,
            instrument_ids=tuple(row.instrument_id for row in selected))
    elif op == "K_WS" and tree.get("type") == "market_lifecycle_v2":
        _native_require(request.request_options["cmd"] == "subscribe"
                        and "market_lifecycle_v2" in request.request_options["params"]["channels"],
                        "Kalshi lifecycle message is outside the global subscription")
        _native_require(field("/type", "STRING") == "market_lifecycle_v2", "invalid Kalshi lifecycle discriminator")
        instrument, event_type = field("/msg/market_ticker", "STRING"), field("/msg/event_type", "STRING")
        message = tree["msg"]
        normalized_message = dict(market_ticker=instrument, event_type=event_type)
        normalized = dict(type="market_lifecycle_v2", msg=normalized_message)
        for name in ("sid", "seq"):
            normalized[name] = field("/"+name, "INTEGER")
            _public_counter_v1(normalized[name], allow_zero=name == "seq")
            _native_require(name not in message or type(message[name]) is int and message[name] == normalized[name],
                            "conflicting root/nested lifecycle sequence alias")
        if "sending_ts_ms" in tree:
            sending = _public_exact_clock_v1(field("/sending_ts_ms", "INTEGER", "DECLARED_MILLISECONDS_TO_NS"), unit="MILLISECONDS")
        for name in ("open_ts", "close_ts", "determination_ts", "settlement_ts"):
            if name in message:
                value = field("/msg/"+name, "INTEGER", "DECLARED_SECONDS_TO_NS")
                normalized_message[name] = _public_exact_clock_v1(value, unit="SECONDS")["source_text"]
        channel = "market_lifecycle_v2"
        if instrument not in request.instrument_ids:
            disposition = dict(kind="UNSELECTED_LIFECYCLE", instrument_id=instrument)
        else:
            selected = accepted_metadata(instrument)
            normalized_message["market_id"] = selected.market_id
            if "market_id" in message:
                _native_require(field("/msg/market_id", "STRING") == selected.market_id, "native lifecycle market id differs")
            if "market_ticker" in tree:
                _native_require(field("/market_ticker", "STRING") == instrument, "native lifecycle root identity differs")
            state = {"activated": "OPEN", "deactivated": "PAUSED", "determined": "RESOLVED",
                     "settled": "SETTLED"}.get(event_type, "UNAVAILABLE")
            disposition.update(event_kind="LIFECYCLE", instrument_id=instrument,
                               metadata_generation=selected.generation, lifecycle_state=state)
    elif op == "K_WS":
        message_type = field("/type", "STRING")
        _native_require(type(tree.get("msg")) is dict, "Kalshi native msg object required")
        message = tree["msg"]
        for alias in ("sid", "seq"):
            if alias in tree and alias in message:
                _native_require(type(tree[alias]) is type(message[alias]) and tree[alias] == message[alias],
                                "conflicting root/nested native alias")
        if message_type in {"subscribed", "ok", "unsubscribed", "error"}:
            identifier = field("/id", "INTEGER")
            _native_require(identifier == request.request_options["id"], "unmatched Kalshi control id")
            _native_require((message_type != "subscribed" or request.request_options["cmd"] == "subscribe")
                            and (message_type != "unsubscribed" or request.request_options["cmd"] == "unsubscribe"),
                            "control acknowledgement does not match the pending command")
            disposition = {"kind": "CONTROL", "message_type": message_type, "request_id": identifier}
            for key in ("sid", "seq"):
                pointer = "/" + key if key in tree else "/msg/" + key
                if key in tree or key in message:
                    disposition[key] = field(pointer, "INTEGER")
            if message_type == "subscribed":
                channel = field("/msg/channel", "STRING")
                _native_require(channel in request.request_options["params"].get("channels", ()), "control channel mismatch")
                _native_require("sid" in disposition, "subscription acknowledgement has no sid")
                disposition["channel"] = channel
            if message_type == "error":
                disposition["code"] = field("/msg/code", "INTEGER")
                disposition["message"] = field("/msg/msg", "STRING")
            normalized, channel = dict(disposition), "PUBLIC_CONTROL"
        else:
            _native_require(message_type in {"orderbook_snapshot", "orderbook_delta", "trade", "market_lifecycle_v2"},
                            "unknown Kalshi application message")
            instrument = field("/msg/market_ticker", "STRING")
            selected = accepted_metadata(instrument)
            if "market_ticker" in tree:
                _native_require(field("/market_ticker", "STRING") == instrument, "root/nested market identity mismatch")
            if "market_id" in message:
                _native_require(field("/msg/market_id", "STRING") == selected.market_id, "native market id mismatch")
            normalized_message = {"market_ticker": instrument, "market_id": selected.market_id}
            normalized = {"type": message_type, "msg": normalized_message}
            native_channel = "orderbook_delta" if message_type.startswith("orderbook_") else message_type
            _native_require(request.request_options["cmd"] == "subscribe"
                            and native_channel in request.request_options["params"]["channels"],
                            "Kalshi data is outside the acknowledged operation/channel")
            channel = "/historical/trades" if message_type == "trade" else native_channel
            for key in ("sid", "seq"):
                if key in tree:
                    normalized[key] = field("/" + key, "INTEGER")
                    _public_counter_v1(normalized[key], allow_zero=True)
            if message_type.startswith("orderbook_"):
                _native_require({"sid", "seq"} <= set(normalized), "native book has no root sid/seq")
            if message_type == "orderbook_snapshot":
                for side in ("yes", "no"):
                    pointer = "/msg/" + side + "_dollars_fp"
                    levels = field(pointer, "ARRAY")
                    converted = []
                    for index, level in enumerate(levels):
                        _native_require(type(level) is list and len(level) == 2, "native snapshot requires exact decimal pairs")
                        price = decimal(pointer + f"/{index}/0", maximum_scale=4)
                        quantity = decimal(pointer + f"/{index}/1", maximum_scale=2)
                        _public_on_price_grid_v1(price, bands=selected.price_bands,
                            origin=selected.price_origin_or_none, increment=selected.price_increment_or_none)
                        converted.append((price, quantity))
                    normalized_message[side + "_dollars"] = tuple(converted)
                disposition["event_kind"] = "BOOK_SNAPSHOT"
            elif message_type == "orderbook_delta":
                side = field("/msg/side", "STRING", "LOWERCASE_OUTCOME_TO_CANONICAL_SIDE")
                _native_require(side in {"yes", "no"}, "unselected native outcome side")
                price = decimal("/msg/price_dollars", maximum_scale=4)
                _public_on_price_grid_v1(price, bands=selected.price_bands,
                    origin=selected.price_origin_or_none, increment=selected.price_increment_or_none)
                normalized_message.update(side=side.upper(), price_dollars=price,
                                          delta_fp=decimal("/msg/delta_fp", maximum_scale=2, signed=True))
                disposition["event_kind"] = "BOOK_DELTA"
            elif message_type == "trade":
                _native_require({"sid", "seq"} <= set(normalized), "native trade has no root sid/seq")
                yes_price = decimal("/msg/yes_price_dollars", maximum_scale=4)
                no_price = decimal("/msg/no_price_dollars", maximum_scale=4)
                _native_require(selected.payout_amount_or_none is not None
                                and selected.payout_basis_or_none == "USD_PER_CONTRACT"
                                and Fraction(yes_price) + Fraction(no_price) == Fraction(selected.payout_amount_or_none),
                                "native trade side prices do not conserve the accepted payout")
                for price in (yes_price, no_price):
                    _public_on_price_grid_v1(price, bands=selected.price_bands,
                        origin=selected.price_origin_or_none, increment=selected.price_increment_or_none)
                side = field("/msg/taker_side", "STRING")
                _native_require(side in {"yes", "no"}, "unknown native trade outcome side")
                normalized_message.update(trade_id=field("/msg/trade_id", "STRING"),
                    yes_price_dollars=yes_price, no_price_dollars=no_price,
                    count_fp=decimal("/msg/count_fp", maximum_scale=2), taker_side=side)
                seconds = field("/msg/ts", "INTEGER", "DECLARED_SECONDS_TO_NS")
                provider = _public_exact_clock_v1(seconds, unit="SECONDS")
                if "ts_ms" in message:
                    milliseconds = field("/msg/ts_ms", "INTEGER", "DECLARED_MILLISECONDS_TO_NS")
                    _native_require(milliseconds // 1000 == seconds, "native trade coarse clocks disagree")
                    provider = _public_exact_clock_v1(milliseconds, unit="MILLISECONDS")
                normalized_message["created_time"] = provider["receipt_utc_floor"]
                disposition["event_kind"] = "TRADE"
            else:
                _native_require(False, "Kalshi lifecycle translation unavailable")
            if "clock" in message:
                disposition["market_clock"] = field("/msg/clock", "INTEGER")
                _public_counter_v1(disposition["market_clock"], allow_zero=True)
            if "ts" in message and message_type != "trade":
                timestamp = field("/msg/ts", "STRING", "EXACT_RFC3339")
                provider = _public_exact_clock_v1(timestamp, unit="RFC3339")
                normalized_message["created_time"] = provider["receipt_utc_floor"]
            if "sending_ts_ms" in tree or "sending_ts_ms" in message:
                if "sending_ts_ms" in tree and "sending_ts_ms" in message:
                    _native_require(type(tree["sending_ts_ms"]) is type(message["sending_ts_ms"])
                                    and tree["sending_ts_ms"] == message["sending_ts_ms"],
                                    "conflicting native sending-clock aliases")
                sending_pointer = "/sending_ts_ms" if "sending_ts_ms" in tree else "/msg/sending_ts_ms"
                sending = _public_exact_clock_v1(field(sending_pointer, "INTEGER", "DECLARED_MILLISECONDS_TO_NS"),
                                                unit="MILLISECONDS")
            disposition.update(instrument_id=instrument, metadata_generation=selected.generation)
    else:
        _native_require(False, "public native operation translation unavailable")
    frame = PITRawFrameV1(frame_id=_public_canonical_frame_ref_v1(observation.observation_id),
        profile_id=observation.profile_id, connection_epoch=str(observation.connection_epoch),
        capture_session_id=observation.capture_session_id, wire_dialect=wire_dialect,
        channel=channel, raw_utf8_text_or_none=None, parsed_source_scalar_tree_or_none=normalized,
        qtt_received_at_utc=_pit_provider_time(received["receipt_utc_floor"], "received projection"),
        qtt_received_monotonic_ns=observation.received_monotonic_ns, process_epoch_id=observation.process_epoch_id,
        monotonic_clock_id=observation.monotonic_clock_id, wall_clock_source_id=translation_context["wall_clock_source_id"],
        clock_quality_receipt_ref=observation.clock_quality_ref, wall_clock_uncertainty_ns=observation.wall_uncertainty_ns,
        source_contract_refs=(contract.contract_id,))
    return PublicCanonicalTranslationV1(observation.observation_id, frame,
        dict(received=received, provider_event_or_none=provider, provider_sending_or_none=sending),
        contract.contract_id, tuple(row.metadata_id for row in metadata), disposition, tuple(lineage))
