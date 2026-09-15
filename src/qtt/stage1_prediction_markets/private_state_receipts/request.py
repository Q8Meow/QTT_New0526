from __future__ import annotations

from typing import Mapping


DETERMINISTIC_FIXTURE_TIME = "2026-05-20T00:00:00Z"
FIXTURE_AUTHORITY_CLASS = "TEST_FIXTURE_NOT_EXTERNAL_FACT"
ACTIVE_STAGE1_VENUES = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
SHARED_SCOPE_METADATA = ("PREDICTION_MARKETS_GENERAL",)

READY_STATE = "READY_FOR_PR130_FIXTURE_SCOPE_RECEIPT"
REJECTED_MISSING_RUNTIME_CASH_FIELD_MAP = "REJECTED_MISSING_RUNTIME_CASH_FIELD_MAP"
REJECTED_MISSING_CREDENTIAL_ALIAS_PLACEHOLDER = (
    "REJECTED_MISSING_CREDENTIAL_ALIAS_PLACEHOLDER"
)
REJECTED_SECRET_CAPTURE_ATTEMPT = "REJECTED_SECRET_CAPTURE_ATTEMPT"
REJECTED_UNREDACTED_PRIVATE_STATE_PAYLOAD = "REJECTED_UNREDACTED_PRIVATE_STATE_PAYLOAD"
REJECTED_MISSING_REDACTION_ATTESTATION = "REJECTED_MISSING_REDACTION_ATTESTATION"
REJECTED_MISSING_NO_SECRET_CAPTURE_ATTESTATION = (
    "REJECTED_MISSING_NO_SECRET_CAPTURE_ATTESTATION"
)
REJECTED_SCOPE_OR_VENUE_MISMATCH = "REJECTED_SCOPE_OR_VENUE_MISMATCH"
REJECTED_STALE_PRIVATE_STATE_RECEIPT = "REJECTED_STALE_PRIVATE_STATE_RECEIPT"
REJECTED_SUPERSEDED_PRIVATE_STATE_RECEIPT = "REJECTED_SUPERSEDED_PRIVATE_STATE_RECEIPT"
REJECTED_PRODUCTION_PRIVATE_STATE_FETCH_ATTEMPT = (
    "REJECTED_PRODUCTION_PRIVATE_STATE_FETCH_ATTEMPT"
)
REJECTED_NETWORK_IO_ATTEMPT = "REJECTED_NETWORK_IO_ATTEMPT"
REJECTED_PRODUCTION_RUNTIME_CASH_AUTHORITY_ATTEMPT = (
    "REJECTED_PRODUCTION_RUNTIME_CASH_AUTHORITY_ATTEMPT"
)
REJECTED_CREDENTIAL_ALIAS_AUTHORITY_ATTEMPT = (
    "REJECTED_CREDENTIAL_ALIAS_AUTHORITY_ATTEMPT"
)
REJECTED_ATOMICROWS_AUTHORITY_ATTEMPT = "REJECTED_ATOMICROWS_AUTHORITY_ATTEMPT"

REQUEST_PURPOSE = "PRIVATE_STATE_RECEIPT_GATE_FIXTURE_VALIDATION"
PRIVATE_STATE_SURFACE = "ACCOUNT_WALLET_BALANCE"


def account_scope_id(venue_id: str) -> str:
    return f"PR130_{venue_id}_FIXTURE_ACCOUNT_SCOPE"


def wallet_scope_id(venue_id: str) -> str:
    return f"PR130_{venue_id}_FIXTURE_WALLET_SCOPE"


def credential_alias_placeholder_ref(venue_id: str) -> str:
    return f"PR130_{venue_id}_CREDENTIAL_ALIAS_PLACEHOLDER_REQUIRES_PR113"


def primary_runtime_cash_field_map_id(venue_id: str) -> str:
    return f"PR129_{venue_id}_VERIFIED_AVAILABLE_CASH_FIELD_MAP_V1"


def common_authority_false_flags() -> dict[str, bool]:
    return {
        "account_wallet_balance_private_state_fetch_allowed_flag": False,
        "credential_secret_capture_allowed_flag": False,
        "network_io_allowed_flag": False,
        "production_connector_use_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "order_routing_authority_allowed_flag": False,
        "replay_paper_execution_allowed_flag": False,
        "runtime_resolver_snapshot_creation_allowed_flag": False,
    }


def future_path_flags() -> dict[str, bool]:
    return {
        "future_credential_alias_secret_no_capture_path_preserved": True,
        "future_market_data_ingest_path_preserved": True,
        "future_orderbook_event_snapshot_path_preserved": True,
        "future_runtime_resolver_snapshot_path_preserved": True,
        "future_atomicrows_bridge_path_preserved": True,
        "future_production_launch_path_preserved": True,
    }


def atomicrows_metadata() -> dict[str, object]:
    return {
        "future_atomicrows_parameter_row_refs": [],
        "future_atomicrows_family_refs": ["FUTURE_ATOMICROWS_PRIVATE_STATE_RECEIPT_FAMILY"],
        "future_atomicrows_private_state_receipt_family_ref": (
            "FUTURE_ATOMICROWS_PRIVATE_STATE_RECEIPT_FAMILY"
        ),
        "atomicrows_bundle_consumed": False,
        "atomicrows_bundle_created": False,
        "atomicrows_sha_created": False,
        "atomicrows_row_records_created_count": 0,
        "atomicrows_authority_created": False,
    }


def build_private_state_read_requests(
    field_maps_by_venue: Mapping[str, list[Mapping[str, object]]],
) -> list[dict[str, object]]:
    requests: list[dict[str, object]] = []
    for venue_id in ACTIVE_STAGE1_VENUES:
        field_map_id = primary_runtime_cash_field_map_id(venue_id)
        available_field_map_ids = {
            str(record["runtime_cash_component_field_map_id"])
            for record in field_maps_by_venue.get(venue_id, [])
        }
        if field_map_id not in available_field_map_ids:
            field_map_id = next(iter(sorted(available_field_map_ids)), field_map_id)
        request = {
            "private_state_read_request_id": f"PR130_{venue_id}_PRIVATE_STATE_READ_REQUEST_V1",
            "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
            "private_state_read_request_state": READY_STATE,
            "production_private_state_read_authority": False,
            "venue_id": venue_id,
            "platform_scope": "PREDICTION_MARKETS_GENERAL",
            "account_scope_id": account_scope_id(venue_id),
            "wallet_scope_id": wallet_scope_id(venue_id),
            "requested_private_state_surface": PRIVATE_STATE_SURFACE,
            "requested_field_map_ref": field_map_id,
            "runtime_cash_component_field_map_id": field_map_id,
            "credential_alias_placeholder_ref": credential_alias_placeholder_ref(venue_id),
            "credential_alias_required_future_pr": "PR113",
            "credential_alias_authority_created": False,
            "raw_secret_capture_allowed_flag": False,
            "request_purpose": REQUEST_PURPOSE,
            "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
            "future_production_launch_path_preserved": True,
        }
        request.update(common_authority_false_flags())
        request.update(atomicrows_metadata())
        requests.append(request)
    return requests


# Bounded native observation. Fixture builders above remain independent of
# optional transport/signing packages and retain their original contracts.
from dataclasses import dataclass, field
from types import MappingProxyType
from urllib.parse import urlencode
import base64
import logging
import ssl
import time
import uuid
from ..qku_computation_control_plane.context import _f14_freeze_v1, _f14_plain_v1
from ..qku_computation_control_plane.errors import ContractValidationError, ReasonCode
from ..qku_computation_control_plane.source_policy import (
    RetailPrivateSourceRegistryV1, RetailPrivateSessionBindingV1, RetailPrivateRuntimeGrantV1,
    _f14_ingress_require_v1, _f14_counter_v1)
from ..qku_computation_control_plane.serialization import (
    _F14_MAX_INT, _F14_OPERATIONS, _F14_ROUTES, _native_strict_json, _f14_dumps_v1)
from ..qku_computation_control_plane.receipts import _native_retail_private_v1

_F14_WS_PATH = '/v1/ws/private'
_F14_REST_PATHS = MappingProxyType({op: path for op, path in _F14_ROUTES.items()
    if not op.startswith('WS_')})
_F14_REQUIREMENT_FIELDS = ('requires_cross_clock_comparison', 'requires_provider_event_time',
    'requires_provider_publication_time', 'requires_revision_at_decision', 'requires_finality_at_decision',
    'provider_publication_time_is_source_proven', 'maximum_wall_clock_uncertainty_ns_or_none',
    'required_process_epoch_id_or_none', 'required_monotonic_clock_id_or_none')


def _f14_identifier_v1(value: object) -> str:
    _f14_ingress_require_v1(type(value) is str and 0 < len(value) <= 256 and (value == value.strip()), 'F14_INGRESS_IDENTIFIER')
    _f14_ingress_require_v1(not any((ord(c) < 33 or 127 <= ord(c) < 160 or 55296 <= ord(c) <= 57343 for c in value)), 'F14_INGRESS_IDENTIFIER')
    return value

def _f14_market_list_v1(value: object, maximum: int) -> list[str]:
    _f14_ingress_require_v1(type(value) is list and 0 < len(value) <= maximum, 'F14_INGRESS_MARKETS')
    out = [_f14_identifier_v1(x) for x in value]
    _f14_ingress_require_v1(len(set(out)) == len(out), 'F14_INGRESS_MARKETS')
    return out

def _f14_rest_target_v1(operation: str, *, max_rows: int, request_cursor: str | None, market_or_none: str | None) -> tuple[str, str]:
    """Return signing path and origin-form request target; never a URL override."""
    _f14_ingress_require_v1(type(operation) is str and operation in _F14_REST_PATHS, 'F14_INGRESS_ROUTE')
    limit = _f14_counter_v1(max_rows, 1, 10000)
    if request_cursor is not None:
        _f14_identifier_v1(request_cursor)
    if market_or_none is not None:
        _f14_identifier_v1(market_or_none)
    path = _F14_REST_PATHS[operation]
    if operation == 'BALANCES':
        _f14_ingress_require_v1(request_cursor is None and market_or_none is None, 'F14_INGRESS_UNUSED_FIELD')
        return (path, path)
    pairs = [('limit', str(limit))]
    if request_cursor is not None:
        pairs.append(('cursor', request_cursor))
    if market_or_none is not None:
        pairs.append(('market' if operation == 'POSITIONS' else 'marketSlug', market_or_none))
    if operation == 'ACTIVITY_TRADE':
        pairs.append(('types', 'ACTIVITY_TYPE_TRADE'))
    elif operation == 'ACTIVITY_RESOLUTION':
        pairs.append(('types', 'ACTIVITY_TYPE_POSITION_RESOLUTION'))
    if operation.startswith('ACTIVITY_'):
        pairs.append(('sortOrder', 'SORT_ORDER_DESCENDING'))
    return (path, path + '?' + urlencode(pairs, encoding='utf-8', errors='strict'))

def _f14_subscription_v1(operation: str, request_ref: str, markets: list[str]) -> dict:
    _f14_identifier_v1(request_ref)
    _f14_ingress_require_v1(type(operation) is str and operation in {'WS_POSITION', 'WS_BALANCE'}, 'F14_INGRESS_ROUTE')
    if operation == 'WS_POSITION':
        selected = _f14_market_list_v1(markets, 100)
        return {'subscribe': {'requestId': request_ref, 'subscriptionType': 'SUBSCRIPTION_TYPE_POSITION', 'marketSlugs': selected}}
    _f14_ingress_require_v1(type(markets) is list and (not markets), 'F14_INGRESS_UNUSED_FIELD')
    return {'subscribe': {'requestId': request_ref, 'subscriptionType': 'SUBSCRIPTION_TYPE_ACCOUNT_BALANCE'}}

def _f14_signing_message_v1(timestamp_ms: int, path: str) -> bytes:
    _f14_counter_v1(timestamp_ms)
    _f14_ingress_require_v1(type(path) is str and path in {*_F14_REST_PATHS.values(), _F14_WS_PATH}, 'F14_INGRESS_SIGNING_PATH')
    return (str(timestamp_ms) + 'GET' + path).encode('ascii')

def _f14_validate_rest_envelope_v1(status: int, content_types: list[str], content_encodings: list[str], content_lengths: list[str], transfer_encodings: list[str], raw: bytes, maximum: int) -> None:
    _f14_ingress_require_v1(type(status) is int and status == 200, 'F14_INGRESS_HTTP_STATUS')
    _f14_counter_v1(maximum, 1, 1048576)
    _f14_ingress_require_v1(type(raw) is bytes and 0 < len(raw) <= maximum, 'F14_INGRESS_BODY_BOUND')
    _f14_ingress_require_v1(type(content_types) is list and len(content_types) == 1 and (type(content_types[0]) is str) and (content_types[0].split(';', 1)[0].strip().lower() == 'application/json'), 'F14_INGRESS_CONTENT_TYPE')
    parameters = content_types[0].split(';')[1:]
    seen_charset = False
    for parameter in parameters:
        key, separator, value = parameter.strip().partition('=')
        _f14_ingress_require_v1(separator == '=' and key.strip().lower() == 'charset' and (not seen_charset) and (value.strip().lower() in {'utf-8', '"utf-8"'}), 'F14_INGRESS_CONTENT_TYPE')
        seen_charset = True
    _f14_ingress_require_v1(type(content_encodings) is list and (not content_encodings or (len(content_encodings) == 1 and type(content_encodings[0]) is str and (content_encodings[0].strip().lower() == 'identity'))), 'F14_INGRESS_CONTENT_ENCODING')
    _f14_ingress_require_v1(type(content_lengths) is list and len(content_lengths) <= 1 and (type(transfer_encodings) is list) and (len(transfer_encodings) <= 1), 'F14_INGRESS_HTTP_FRAMING')
    _f14_ingress_require_v1(not (content_lengths and transfer_encodings), 'F14_INGRESS_HTTP_FRAMING')
    if transfer_encodings:
        _f14_ingress_require_v1(type(transfer_encodings[0]) is str and transfer_encodings[0].strip().lower() == 'chunked', 'F14_INGRESS_HTTP_FRAMING')
    if content_lengths:
        v = content_lengths[0]
        _f14_ingress_require_v1(type(v) is str and bool(v) and (len(v) <= 20) and v.isascii() and v.isdecimal(), 'F14_INGRESS_HTTP_FRAMING')
        _f14_ingress_require_v1(int(v) == len(raw), 'F14_INGRESS_HTTP_FRAMING')
    try:
        raw.decode('utf-8', 'strict')
    except UnicodeError as exc:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, 'F14_INGRESS_UTF8') from exc

@dataclass(frozen=True)
class _F14WSStateV1:
    messages_seen: int = 0
    balance_snapshot_seen: bool = False
    completed: bool = False

def _f14_ws_step_v1(state: _F14WSStateV1, *, operation: str, request_ref: str, markets: list[str], max_rows: int, message: str, maximum_raw_bytes: int, message_budget: int) -> tuple[_F14WSStateV1, str, bytes]:
    """Initialization is never promoted into timestamped observation evidence."""
    _f14_ingress_require_v1(type(state) is _F14WSStateV1 and (not state.completed), 'F14_INGRESS_WS_STATE')
    _f14_counter_v1(message_budget, 1)
    _f14_counter_v1(state.messages_seen)
    _f14_ingress_require_v1(type(state.balance_snapshot_seen) is bool and type(state.completed) is bool, 'F14_INGRESS_WS_STATE')
    _f14_ingress_require_v1(state.messages_seen < message_budget, 'F14_INGRESS_MESSAGE_BUDGET')
    _f14_counter_v1(maximum_raw_bytes, 1, 1048576)
    _f14_counter_v1(max_rows, 1, 10000)
    _f14_ingress_require_v1(type(message) is str, 'F14_INGRESS_WS_TEXT_REQUIRED')
    _f14_subscription_v1(operation, request_ref, markets)
    try:
        raw = message.encode('utf-8', 'strict')
    except UnicodeError as exc:
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, 'F14_INGRESS_UTF8') from exc
    _f14_ingress_require_v1(0 < len(raw) <= maximum_raw_bytes, 'F14_INGRESS_BODY_BOUND')
    body = _native_strict_json(raw, maximum_raw_bytes)
    _f14_ingress_require_v1(type(body) is dict, 'F14_INGRESS_WS_ENVELOPE')
    _f14_ingress_require_v1(body.get('requestId') == request_ref, 'F14_INGRESS_WS_REQUEST')
    count = state.messages_seen + 1
    if operation == 'WS_BALANCE' and 'accountBalancesSnapshot' in body:
        _f14_ingress_require_v1(not state.balance_snapshot_seen and state.messages_seen == 0, 'F14_INGRESS_WS_DUPLICATE_INITIALIZATION')
        _f14_ingress_require_v1(set(body) == {'requestId', 'subscriptionType', 'accountBalancesSnapshot'}, 'F14_INGRESS_WS_ENVELOPE')
        _native_retail_private_v1('BALANCE_SNAPSHOT', body, request_ref, [], max_rows)
        return (_F14WSStateV1(count, True, False), 'INITIALIZATION_ONLY_NOT_AN_F14_ROUTE', raw)
    kind = 'POSITION' if operation == 'WS_POSITION' else 'BALANCE_UPDATE'
    root = 'positionSubscription' if kind == 'POSITION' else 'accountBalancesUpdate'
    _f14_ingress_require_v1(set(body) == {'requestId', 'subscriptionType', root}, 'F14_INGRESS_WS_ENVELOPE')
    _native_retail_private_v1(kind, body, request_ref, markets, max_rows)
    return (_F14WSStateV1(count, state.balance_snapshot_seen, True), 'SELECTED_UPDATE', raw)


@dataclass(frozen=True, slots=True, repr=False)
class RetailPrivateCredentialHandleV1:
    binding_ref: str
    ledger_account_ref: str
    session_ref: str
    api_key_id: str
    private_key: object

    def __repr__(self):
        return 'RetailPrivateCredentialHandleV1(<redacted>)'

    def __reduce_ex__(self, protocol):
        raise TypeError('F14 credential handles cannot be serialized')

    def close(self):
        object.__setattr__(self, 'private_key', None)


def bind_private_runtime_credential_v1(*, session_binding, api_key_id, private_key, source_registry):
    _f14_ingress_require_v1(type(source_registry) is RetailPrivateSourceRegistryV1
        and type(session_binding) is RetailPrivateSessionBindingV1, 'F14_INGRESS_SESSION')
    with source_registry._lock:
        source_registry._validate_session_v1(session_binding, time.time_ns())
        _f14_identifier_v1(api_key_id)
        try:
            parsed = uuid.UUID(api_key_id)
        except (ValueError, AttributeError) as exc:
            raise ContractValidationError(ReasonCode.INVALID_CONTRACT, 'F14_INGRESS_KEY_ID') from exc
        _f14_ingress_require_v1(str(parsed) == api_key_id, 'F14_INGRESS_KEY_ID')
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        _f14_ingress_require_v1(isinstance(private_key, Ed25519PrivateKey), 'F14_INGRESS_KEY_TYPE')
        for handle in source_registry._credentials.values():
            if handle.binding_ref == session_binding.credential_binding_ref:
                _f14_ingress_require_v1(handle.ledger_account_ref == session_binding.scope['ledger_account_ref']
                    and handle.session_ref == session_binding.session_ref and handle.api_key_id == api_key_id
                    and handle.private_key is private_key, 'F14_INGRESS_KEY_CONFLICT')
                return handle
        handle = RetailPrivateCredentialHandleV1(session_binding.credential_binding_ref,
            session_binding.scope['ledger_account_ref'], session_binding.session_ref, api_key_id, private_key)
        source_registry._credentials[id(handle)] = handle
        return handle


@dataclass(frozen=True, slots=True)
class RetailPrivateReadRequestV1:
    grant: RetailPrivateRuntimeGrantV1
    operation: str
    consumer: Mapping[str, object]
    market_filter_or_none: str | None
    requirements: Mapping[str, object]
    maximum_raw_bytes: int

    def __post_init__(self):
        _f14_ingress_require_v1(type(self.grant) is RetailPrivateRuntimeGrantV1, 'F14_INGRESS_GRANT')
        _f14_ingress_require_v1(type(self.operation) is str and self.operation in _F14_OPERATIONS,
            'F14_INGRESS_ROUTE')
        _f14_counter_v1(self.maximum_raw_bytes, 1, 1048576)
        _f14_ingress_require_v1(type(self.consumer) is dict and set(self.consumer) == {
            'operation', 'item_key', 'request_ref', 'markets', 'max_rows', 'request_cursor',
            'seen_cursors', 'remaining_requests'}, 'F14_INGRESS_CONSUMER')
        c = dict(self.consumer)
        _f14_ingress_require_v1(type(c['operation']) is str and c['operation'] == self.operation,
            'F14_INGRESS_ROUTE')
        _f14_identifier_v1(c['request_ref'])
        _f14_counter_v1(c['max_rows'], 1, 10000)
        _f14_counter_v1(c['remaining_requests'])
        for name in ('markets', 'seen_cursors'):
            values = c[name]
            _f14_ingress_require_v1(type(values) is list and len(values) <= 10000,
                'F14_INGRESS_CONSUMER')
            for value in values:
                _f14_identifier_v1(value)
            _f14_ingress_require_v1(len(values) == len(set(values)), 'F14_INGRESS_CONSUMER')
            c[name] = list(values)
        if c['request_cursor'] is not None:
            _f14_identifier_v1(c['request_cursor'])
            _f14_ingress_require_v1(c['request_cursor'] not in c['seen_cursors'], 'F14_INGRESS_CURSOR')
        if self.market_filter_or_none is not None:
            _f14_identifier_v1(self.market_filter_or_none)
            _f14_ingress_require_v1(self.market_filter_or_none in c['markets'], 'F14_INGRESS_MARKETS')
        if self.operation.startswith('WS_'):
            _f14_ingress_require_v1(c['item_key'] is None and c['request_cursor'] is None
                and c['seen_cursors'] == [] and c['remaining_requests'] == 0
                and self.market_filter_or_none is None, 'PRIVATE_JOIN_UNUSED_PAGE_CONTEXT')
            _f14_subscription_v1(self.operation, c['request_ref'], c['markets'])
        else:
            _f14_rest_target_v1(self.operation, max_rows=c['max_rows'], request_cursor=c['request_cursor'],
                market_or_none=self.market_filter_or_none)
            if self.operation == 'POSITIONS':
                _f14_identifier_v1(c['item_key'])
                _f14_ingress_require_v1(c['item_key'] in c['markets'], 'F14_INGRESS_MARKETS')
            else:
                _f14_counter_v1(c['item_key'], 0, c['max_rows'] - 1)
        _f14_ingress_require_v1(type(self.requirements) is dict
            and set(self.requirements) == set(_F14_REQUIREMENT_FIELDS), 'F14_INGRESS_REQUIREMENTS')
        req = dict(self.requirements)
        _f14_ingress_require_v1(all(type(req[name]) is bool for name in _F14_REQUIREMENT_FIELDS[:6]),
            'F14_INGRESS_REQUIREMENTS')
        bound = req['maximum_wall_clock_uncertainty_ns_or_none']
        if bound is not None:
            _f14_counter_v1(bound)
            _f14_ingress_require_v1(self.grant.wall_clock_uncertainty_ns <= bound, 'F14_INGRESS_CLOCK_QUALITY')
        for name, expected in (('required_process_epoch_id_or_none', self.grant.process_epoch_id),
            ('required_monotonic_clock_id_or_none', self.grant.monotonic_clock_id)):
            if req[name] is not None:
                _f14_identifier_v1(req[name])
                _f14_ingress_require_v1(req[name] == expected, 'F14_INGRESS_CLOCK_DOMAIN')
        _f14_ingress_require_v1(not req['requires_cross_clock_comparison'] or bound is not None,
            'F14_INGRESS_CLOCK_QUALITY')
        object.__setattr__(self, 'consumer', _f14_freeze_v1(c))
        object.__setattr__(self, 'requirements', _f14_freeze_v1(req))


@dataclass(frozen=True, slots=True, repr=False)
class _F14PreparedV1:
    request: RetailPrivateReadRequestV1
    target: str
    timeout_seconds: float
    tls_context: object
    headers: Mapping[str, str]
    maximum_raw_bytes: int
    maximum_application_messages: int
    quiet_logger: object
    subscription_json: str | None


class RetailPrivateIngressV1:
    def __init__(self, *, source_registry, credential_handle):
        _f14_ingress_require_v1(type(source_registry) is RetailPrivateSourceRegistryV1
            and type(credential_handle) is RetailPrivateCredentialHandleV1
            and source_registry._credentials.get(id(credential_handle)) is credential_handle,
            'F14_INGRESS_KEY_BINDING')
        self.source_registry = source_registry
        self.credential_handle = credential_handle
        self._coordinator_token = None
        self._active_request = None
        self._attempt_id = None
        self._prepared = None
        self._charged = False
        self._response_headers = None
        with source_registry._lock:
            source_registry._receivers[id(self)] = self

    def _validate_request_v1(self, request):
        _f14_ingress_require_v1(type(request) is RetailPrivateReadRequestV1, 'F14_INGRESS_REQUEST')
        self.source_registry._validate_grant_v1(request.grant, request.operation)
        session, handle = request.grant.session_binding, self.credential_handle
        _f14_ingress_require_v1(self.source_registry._credentials.get(id(handle)) is handle
            and handle.private_key is not None and handle.binding_ref == session.credential_binding_ref
            and handle.session_ref == session.session_ref
            and handle.ledger_account_ref == session.scope['ledger_account_ref'], 'F14_INGRESS_KEY_BINDING')

    def _acquire_coordinator_v1(self, request):
        with self.source_registry._lock:
            self._validate_request_v1(request)
            _f14_ingress_require_v1(self._coordinator_token is None and self._active_request is None,
                'F14_INGRESS_ATTEMPT_ACTIVE')
            token = object()
            self._coordinator_token = token
            return token

    def _prepare_v1(self, request, ws):
        with self.source_registry._lock:
            self._validate_request_v1(request)
            _f14_ingress_require_v1(request.operation.startswith('WS_') is ws, 'F14_INGRESS_ROUTE')
            _f14_ingress_require_v1(self._active_request is None, 'F14_INGRESS_ATTEMPT_ACTIVE')
            _f14_ingress_require_v1(self.source_registry._remaining[request.grant.grant_id] > 0,
                'F14_INGRESS_ATTEMPT_BUDGET')
            c = _f14_plain_v1(request.consumer)
            path, target = (_F14_WS_PATH, _F14_WS_PATH) if ws else _f14_rest_target_v1(
                request.operation, max_rows=c['max_rows'], request_cursor=c['request_cursor'],
                market_or_none=request.market_filter_or_none)
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            _f14_ingress_require_v1(type(context) is ssl.SSLContext and context.check_hostname is True
                and context.verify_mode == ssl.CERT_REQUIRED, 'F14_INGRESS_TLS')
            timestamp_ms = time.time_ns() // 1_000_000
            signature = base64.b64encode(self.credential_handle.private_key.sign(
                _f14_signing_message_v1(timestamp_ms, path))).decode('ascii')
            headers = {'X-PM-Access-Key': self.credential_handle.api_key_id,
                'X-PM-Timestamp': str(timestamp_ms), 'X-PM-Signature': signature}
            if not ws:
                headers.update({'Accept': 'application/json', 'Accept-Encoding': 'identity'})
            remaining = request.grant.deadline_monotonic_ns - time.monotonic_ns()
            _f14_ingress_require_v1(remaining > 0, 'F14_INGRESS_DEADLINE')
            attempt = 'F14:' + uuid.uuid4().hex
            logger = logging.Logger(attempt)
            logger.disabled = True
            logger.propagate = False
            prepared = _F14PreparedV1(request, target, min(10.0, remaining / 1_000_000_000),
                context, MappingProxyType(headers), request.maximum_raw_bytes,
                request.grant.maximum_application_messages, logger,
                _f14_dumps_v1(_f14_subscription_v1(request.operation, c['request_ref'], c['markets'])) if ws else None)
            self._active_request, self._attempt_id, self._prepared = request, attempt, prepared
            self._charged, self._response_headers = False, None
            self.source_registry._observe_v1(request.grant)
            return prepared

    def _prepare_rest_v1(self, request):
        return self._prepare_v1(request, False)

    def _prepare_ws_v1(self, request):
        prepared = self._prepare_v1(request, True)
        self._recheck_and_charge_v1(prepared)
        return prepared

    def _recheck_and_charge_v1(self, prepared):
        with self.source_registry._lock:
            self._recheck_prepared_v1(prepared)
            _f14_ingress_require_v1(self._charged is False, 'F14_INGRESS_ATTEMPT_DUPLICATE')
            self.source_registry._charge_v1(prepared.request.grant, prepared.request.operation)
            self._charged = True

    def _recheck_prepared_v1(self, prepared):
        _f14_ingress_require_v1(type(prepared) is _F14PreparedV1 and prepared is self._prepared
            and prepared.request is self._active_request, 'F14_INGRESS_PREPARED')
        self._validate_request_v1(prepared.request)

    def _observe_clock_v1(self):
        return self.source_registry._observe_v1(self._active_request.grant)

    def _validate_response_headers_v1(self, prepared, response):
        self._recheck_prepared_v1(prepared)
        _f14_ingress_require_v1(type(response.status) is int and response.status == 200,
            'F14_INGRESS_HTTP_STATUS')
        headers = response.getheaders()
        _f14_ingress_require_v1(type(headers) is list and all(type(pair) is tuple and len(pair) == 2
            and all(type(value) is str for value in pair) for pair in headers), 'F14_INGRESS_HTTP_FRAMING')
        selected = tuple([value for key, value in headers if key.lower() == name]
            for name in ('content-type', 'content-encoding', 'content-length', 'transfer-encoding'))
        types, encodings, lengths, transfers = selected
        if lengths:
            _f14_ingress_require_v1(len(lengths) == 1 and lengths[0].isascii()
                and lengths[0].isdecimal() and len(lengths[0]) <= 20
                and 0 < int(lengths[0]) <= prepared.maximum_raw_bytes, 'F14_INGRESS_HTTP_FRAMING')
        # The full envelope predicate is reused before any response read. A
        # bounded local byte value supplies only its length-dependent branch.
        length = int(lengths[0]) if lengths else 1
        _f14_validate_rest_envelope_v1(response.status, types, encodings, lengths, transfers,
            b' ' * length, prepared.maximum_raw_bytes)
        self._response_headers = selected

    def _validate_response_body_v1(self, prepared, response, raw):
        self._recheck_prepared_v1(prepared)
        _f14_ingress_require_v1(self._response_headers is not None, 'F14_INGRESS_HTTP_FRAMING')
        _f14_validate_rest_envelope_v1(response.status, *self._response_headers, raw, prepared.maximum_raw_bytes)

    def _verify_handshake_v1(self, prepared, response):
        self._recheck_prepared_v1(prepared)
        _f14_ingress_require_v1(type(response.status_code) is int and response.status_code == 101,
            'F14_INGRESS_HTTP_STATUS')

    def _recheck_subscription_v1(self, prepared):
        self._recheck_prepared_v1(prepared)

    def _initial_ws_state_v1(self):
        return _F14WSStateV1(0, False, False)

    def _remaining_seconds_v1(self, prepared):
        self._recheck_prepared_v1(prepared)
        remaining = prepared.request.grant.deadline_monotonic_ns - time.monotonic_ns()
        _f14_ingress_require_v1(remaining > 0, 'F14_INGRESS_DEADLINE')
        return remaining / 1_000_000_000

    def _classify_ws_message_v1(self, prepared, state, message):
        self._recheck_prepared_v1(prepared)
        c = _f14_plain_v1(prepared.request.consumer)
        return _f14_ws_step_v1(state, operation=c['operation'], request_ref=c['request_ref'], markets=c['markets'],
            max_rows=c['max_rows'], message=message, maximum_raw_bytes=prepared.maximum_raw_bytes,
            message_budget=prepared.maximum_application_messages)

    def _retain_received_v1(self, prepared, raw, received, response_status):
        from .receipt import build_observed_private_capture_v1
        self._recheck_prepared_v1(prepared)
        return build_observed_private_capture_v1(receiver=self, request=prepared.request,
            raw_body=raw, received_clock=received, response_status=response_status)

    def _raise_message_budget_v1(self):
        raise ContractValidationError(ReasonCode.INVALID_CONTRACT, 'F14_INGRESS_MESSAGE_BUDGET')

    def _finish_attempt_v1(self, token):
        with self.source_registry._lock:
            if token is not None and token is self._coordinator_token:
                self._active_request = self._attempt_id = self._prepared = self._response_headers = None
                self._charged = False
                self._coordinator_token = None

    def read_rest_once(self, request):
        prepared = self._prepare_rest_v1(request)
        import http.client
        connection = http.client.HTTPSConnection("api.polymarket.us", 443, timeout=prepared.timeout_seconds, context=prepared.tls_context)
        try:
            self._recheck_and_charge_v1(prepared)
            connection.request("GET", prepared.target, body=None, headers=prepared.headers)
            response = connection.getresponse()
            self._validate_response_headers_v1(prepared, response)
            raw = response.read(prepared.maximum_raw_bytes + 1)
            received = self._observe_clock_v1()
            self._validate_response_body_v1(prepared, response, raw)
            return self._retain_received_v1(prepared, raw, received, 200)
        finally:
            connection.close()

    def read_private_message_once(self, request):
        prepared = self._prepare_ws_v1(request)
        import websockets.sync.client
        with websockets.sync.client.connect("wss://api.polymarket.us/v1/ws/private", ssl=prepared.tls_context, additional_headers=prepared.headers, proxy=None, compression=None, open_timeout=prepared.timeout_seconds, ping_interval=20, ping_timeout=20, close_timeout=10, max_size=prepared.maximum_raw_bytes, max_queue=16, logger=prepared.quiet_logger) as connection:
            self._verify_handshake_v1(prepared, connection.response)
            self._recheck_subscription_v1(prepared)
            connection.send(prepared.subscription_json)
            state = self._initial_ws_state_v1()
            for unused in range(prepared.maximum_application_messages):
                message = connection.recv(timeout=self._remaining_seconds_v1(prepared))
                received = self._observe_clock_v1()
                state, disposition, raw = self._classify_ws_message_v1(prepared, state, message)
                if disposition == "SELECTED_UPDATE":
                    return self._retain_received_v1(prepared, raw, received, 101)
            self._raise_message_budget_v1()
