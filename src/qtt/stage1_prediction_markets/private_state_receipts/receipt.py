from __future__ import annotations

from typing import Mapping

from src.qtt.stage1_prediction_markets.private_state_receipts.canonical_redaction import (
    canonical_redacted_payload_digest,
)
from src.qtt.stage1_prediction_markets.private_state_receipts.redaction import (
    no_secret_capture_attestation_id,
    redaction_attestation_id,
)
from src.qtt.stage1_prediction_markets.private_state_receipts.request import (
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    READY_STATE,
    common_authority_false_flags,
    future_path_flags,
)


def receipt_id_for_request(request: Mapping[str, object]) -> str:
    return str(request["private_state_read_request_id"]).replace(
        "_REQUEST_V1", "_RECEIPT_V1"
    )


def build_private_state_read_receipt(
    *, request: Mapping[str, object], redacted_payload: Mapping[str, object]
) -> dict[str, object]:
    receipt_id = receipt_id_for_request(request)
    digest = canonical_redacted_payload_digest(redacted_payload)
    receipt = {
        "private_state_read_receipt_id": receipt_id,
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "private_state_read_receipt_state": READY_STATE,
        "production_private_state_read_authority": False,
        "production_account_balance_authority": False,
        "production_wallet_balance_authority": False,
        "production_runtime_cash_receipt_authority": False,
        "private_state_read_request_id": request["private_state_read_request_id"],
        "venue_id": request["venue_id"],
        "platform_scope": request["platform_scope"],
        "account_scope_id": request["account_scope_id"],
        "wallet_scope_id": request["wallet_scope_id"],
        "runtime_cash_component_field_map_id": request["runtime_cash_component_field_map_id"],
        "observed_private_state_surface": request["requested_private_state_surface"],
        "redacted_payload_digest": digest,
        "canonicalized_redacted_payload_digest": digest,
        "redaction_attestation_id": redaction_attestation_id(receipt_id),
        "no_secret_capture_attestation_id": no_secret_capture_attestation_id(receipt_id),
        "credential_alias_placeholder_ref": request["credential_alias_placeholder_ref"],
        "credential_alias_required_future_pr": "PR113",
        "credential_alias_authority_created": False,
        "private_state_receipt_status": READY_STATE,
        "receipt_staleness_policy": "REJECT_IF_STALE_OR_SUPERSEDED_FIXTURE_RECEIPT",
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
    receipt.update(common_authority_false_flags())
    receipt.update(future_path_flags())
    return receipt


from dataclasses import dataclass
from ..qku_computation_control_plane.context import (
    _f14_freeze_v1, _f14_plain_v1, _native_utc_nanoseconds)
from ..qku_computation_control_plane.source_policy import _f14_ingress_require_v1
from ..qku_computation_control_plane.serialization import _native_strict_json
from ..qku_computation_control_plane.receipts import (
    _native_retail_private_v1, _native_retail_portfolio_v1)


@dataclass(frozen=True, slots=True, repr=False)
class ObservedPrivateCaptureV1:
    session_binding: object
    operation: str
    consumer: Mapping[str, object]
    raw_body: bytes
    response_status: int
    received_clock: Mapping[str, object]
    parsed_clock: Mapping[str, object]
    provider_event_pointer_or_none: str | None
    requirements: Mapping[str, object]

    def __post_init__(self):
        _f14_ingress_require_v1(type(self.raw_body) is bytes, 'F14_INGRESS_BODY_BOUND')
        for name in ('consumer', 'received_clock', 'parsed_clock', 'requirements'):
            object.__setattr__(self, name, _f14_freeze_v1(getattr(self, name)))

    def __repr__(self):
        return 'ObservedPrivateCaptureV1(<retained private body>)'

    def __reduce_ex__(self, protocol):
        raise TypeError('F14 observed captures cannot be serialized as authority')


def _f14_selected_native_v1(raw_body, request):
    _f14_ingress_require_v1(type(raw_body) is bytes and 0 < len(raw_body) <= request.maximum_raw_bytes,
        'F14_INGRESS_BODY_BOUND')
    body = _native_strict_json(raw_body, request.maximum_raw_bytes)
    c = _f14_plain_v1(request.consumer)
    op, key = request.operation, c['item_key']
    if op.startswith('WS_'):
        _native_retail_private_v1('POSITION' if op == 'WS_POSITION' else 'BALANCE_UPDATE',
            body, c['request_ref'], c['markets'], c['max_rows'])
        tokens = ['positionSubscription', 'updateTime'] if op == 'WS_POSITION' else [
            'accountBalancesUpdate', 'balanceChange', 'updateTime']
    else:
        decoded = _native_retail_portfolio_v1('ACTIVITIES' if op.startswith('ACTIVITY_') else op,
            body, c['markets'], c['max_rows'], http_status=200, request_cursor=c['request_cursor'],
            seen_cursors=c['seen_cursors'], remaining_requests=c['remaining_requests'])
        if op == 'POSITIONS':
            _f14_ingress_require_v1(key in body['positions'], 'PRIVATE_JOIN_ITEM')
            tokens = ['positions', key, 'updateTime']
        else:
            field = 'activities' if op.startswith('ACTIVITY_') else 'balances'
            _f14_ingress_require_v1(key < len(body[field]), 'PRIVATE_JOIN_ITEM')
            tokens = [field, str(key)]
            if field == 'activities':
                nested = {'ACTIVITY_TRADE': 'trade', 'ACTIVITY_RESOLUTION': 'positionResolution',
                    'ACTIVITY_FUNDING': 'accountBalanceChange'}[op]
                _f14_ingress_require_v1(nested in body[field][key], 'PRIVATE_JOIN_VARIANT')
                tokens += [nested, 'updateTime']
            else:
                tokens += ['lastUpdated']
    selected = body
    for token in tokens:
        if type(selected) is list:
            selected = selected[int(token)]
        elif type(selected) is dict and token in selected:
            selected = selected[token]
        else:
            selected = None
            break
    pointer = None
    if selected is not None:
        _native_utc_nanoseconds(selected)
        pointer = '/' + '/'.join(token.replace('~', '~0').replace('/', '~1') for token in tokens)
    return pointer, selected


def build_observed_private_capture_v1(*, receiver, request, raw_body, received_clock, response_status):
    from .request import RetailPrivateIngressV1
    _f14_ingress_require_v1(type(receiver) is RetailPrivateIngressV1, 'F14_INGRESS_RECEIVER')
    with receiver.source_registry.fenced(request.grant, request.operation):
        _f14_ingress_require_v1(receiver._active_request is request and receiver._charged is True,
            'F14_INGRESS_CAPTURE_ASSOCIATION')
        pointer, native_time = _f14_selected_native_v1(raw_body, request)
        parsed = receiver._observe_clock_v1()
        _f14_ingress_require_v1(received_clock['monotonic_ns'] <= parsed['monotonic_ns']
            and _native_utc_nanoseconds(received_clock['observed_at'])
                <= _native_utc_nanoseconds(parsed['observed_at']), 'F14_INGRESS_TIME_ORDER')
        expected = 101 if request.operation.startswith('WS_') else 200
        _f14_ingress_require_v1(type(response_status) is int and response_status == expected,
            'F14_INGRESS_HTTP_STATUS')
        observed = ObservedPrivateCaptureV1(request.grant.session_binding, request.operation,
            request.consumer, raw_body, response_status, received_clock, parsed, pointer, request.requirements)
        receiver.source_registry.register_observed_capture(observed, receiver=receiver,
            request=request, attempt_id=receiver._attempt_id)
        return observed
