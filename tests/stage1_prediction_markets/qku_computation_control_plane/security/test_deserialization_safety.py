from types import MappingProxyType

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ReasonCode,
    SerializationSafetyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
    safe_json_loads,
)


def test_json_is_deterministic_and_unsafe_values_fail_closed() -> None:
    assert deterministic_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert safe_json_loads('{"a":[1,true,null]}') == {
        "a": [1, True, None]
    }
    assert deterministic_json(MappingProxyType({"b": 2, "a": 1})) == (
        '{"a":1,"b":2}'
    )
    assert deterministic_json({"burst_tokens": 60}) == '{"burst_tokens":60}'
    for value in ("NaN", "Infinity", '{"value":NaN}'):
        with pytest.raises(SerializationSafetyError) as caught:
            safe_json_loads(value)
        assert caught.value.reason_code is ReasonCode.SERIALIZATION_UNSAFE
    with pytest.raises(SerializationSafetyError):
        safe_json_loads('{"a":1,"a":2}')
    with pytest.raises(SerializationSafetyError):
        safe_json_loads('{"access_token":"forbidden"}')
    with pytest.raises(SerializationSafetyError) as caught:
        deterministic_json({"output_path": r"C:\absolute\result.json"})
    assert caught.value.reason_code is ReasonCode.PATH_UNSAFE
    with pytest.raises(SerializationSafetyError):
        safe_json_loads('{"output_path":"../escape.json"}')
    with pytest.raises(SerializationSafetyError):
        deterministic_json(object())


    # Strict raw decoding retains its own numerical domain and local error tokens.
    from decimal import Decimal, localcontext
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.context import _native_bounded_decimal
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import _native_strict_json

    decoded = _native_strict_json(b'{"integer":2,"fraction":1.20,"exponent":2e0,"text":"  [ ]  ","empty":""}')
    assert type(decoded["integer"]) is int
    assert type(decoded["fraction"]) is Decimal and str(decoded["fraction"]) == "1.20"
    assert type(decoded["exponent"]) is Decimal and decoded["exponent"] == Decimal(2)
    assert decoded["text"] == "  [ ]  " and decoded["empty"] == ""
    with localcontext() as decimal_context:
        decimal_context.prec = 2
        assert _native_strict_json(b'{"n":1.234567890123456789}')["n"] == Decimal("1.234567890123456789")
    for token in ("1e100", "1e-100", "0e128", "0e-128", "1." + "0" * 126):
        assert type(_native_strict_json(('{"n":' + token + '}').encode())["n"]) is Decimal
    assert _native_strict_json(('{"n":1' + "0" * 100 + '}').encode())["n"] == 10 ** 100
    assert _native_bounded_decimal(Decimal("0." + "1" * 128)) == Decimal("0." + "1" * 128)
    for value in (Decimal("0." + "1" * 129), Decimal("0e129"), Decimal("0e-129")):
        with pytest.raises(ContractValidationError, match="NUMBER_BOUND"):
            _native_bounded_decimal(value)
    for value in (1, 1.0, True, Decimal("-0"), Decimal("NaN"), Decimal("Infinity")):
        with pytest.raises(ContractValidationError, match="NUMBER"):
            _native_bounded_decimal(value)

    raw_cases = (
        (b'{"n":-0}', "NUMBER"), (b'{"n":-0.0}', "NUMBER"), (b'{"n":-0e1}', "NUMBER"),
        (b'{"n":NaN}', "NONFINITE"), (b'{"n":Infinity}', "NONFINITE"),
        (b'{"n":-Infinity}', "NONFINITE"),
        (b'{"n":1e101}', "NUMBER_BOUND"), (b'{"n":1e-101}', "NUMBER_BOUND"),
        (b'{"n":0e129}', "NUMBER_BOUND"), (b'{"n":0e-129}', "NUMBER_BOUND"),
        (('{"n":' + "1" * 129 + '}').encode(), "NUMBER_BOUND"),
        (('{"n":1.' + "0" * 127 + '}').encode(), "NUMBER_BOUND"),
        (b'{"n":1,"\\u006e":2}', "DUPLICATE_JSON_KEY"),
        (b'{"":1}', "TEXT"), (b'{" n":1}', "TEXT"), (b'{"n\\u0000":1}', "TEXT"),
        (b'{"n":"\\ud800"}', "SURROGATE"), (b'\xff', "JSON"),
        (b'{"n":[}', "JSON"), (b'{"n":"unterminated}', "JSON"), (b'{} trailing', "JSON"),
        (b'[' * 17 + b'0' + b']' * 17, "JSON_DEPTH"),
        (b'[' + b','.join([b'0'] * 4096) + b']', "JSON_NODES"),
        (b'{"a":[' + b','.join([b'0'] * 4094) + b']}', "JSON_NODES"),
    )
    for raw, reason in raw_cases:
        with pytest.raises(ContractValidationError) as caught:
            _native_strict_json(raw, 1048576)
        assert type(caught.value) is ContractValidationError
        assert caught.value.reason_code is ReasonCode.INVALID_CONTRACT
        assert str(caught.value).endswith(": " + reason)
    assert _native_strict_json(b'[' * 16 + b'0' + b']' * 16) is not None
    assert len(_native_strict_json(b'[' + b','.join([b'0'] * 4095) + b']')) == 4095
    assert len(_native_strict_json(b'{"a":[' + b','.join([b'0'] * 4093) + b']}')["a"]) == 4093
    assert _native_strict_json(b'{"n":"\\u0000"}') == {"n": "\x00"}
    quoted = '{"n":"' + "[" * 32 + '\\"' + "]" * 32 + '"}'
    assert _native_strict_json(quoted.encode())["n"] == "[" * 32 + '"' + "]" * 32
    for budget in (False, 0, 1048577, 1.5, "10"):
        with pytest.raises(ContractValidationError, match="JSON_BUDGET"):
            _native_strict_json(b"{}", budget)
    for raw in ("{}", bytearray(b"{}"), memoryview(b"{}"), None):
        with pytest.raises(ContractValidationError, match="JSON_BOUND"):
            _native_strict_json(raw)
    assert _native_strict_json(b"{}", 2) == {}
    with pytest.raises(ContractValidationError, match="JSON_BOUND"):
        _native_strict_json(b"{}", 1)

    # Exercise shared error routing and decoded-secret protection through the codec.
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import receipts as receipt_owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
        PersistenceContractError, PointInTimeError, SourcePolicyError,
    )
    body = {
        "schema_version": "1", "record_id": "private-clock", "raw_record_ref": "raw-record",
        "scope": dict(profile="POLYMARKET_US_RETAIL_DIRECT", ledger_account_ref="account",
                      source_binding_ref="binding", source_context_ref="context",
                      capture_epoch_ref="capture", partition_ref="partition"),
        "raw_body_utf8": "{}", "raw_byte_limit": 1024, "provider_event_pointer_or_none": None,
        "clock_proof_refs": dict(provider_publication_time_utc_or_none=None,
                                revision_effective_time_utc_or_none=None,
                                settlement_finality_time_utc_or_none=None),
        "clocks": {
            "provider_event_time_utc_or_none": None, "provider_publication_time_utc_or_none": None,
            "qtt_received_at_utc": "2026-01-01T00:00:00Z", "qtt_received_monotonic_ns": 0,
            "qtt_parse_completed_at_utc": "2026-01-01T00:00:00Z", "qtt_parse_completed_monotonic_ns": 0,
            "durable_commit_completed_at_utc": "2026-01-01T00:00:00Z", "durable_commit_completed_monotonic_ns": 0,
            "strategy_available_at_utc": "2026-01-01T00:00:00Z", "strategy_available_monotonic_ns": 0,
            "revision_effective_time_utc_or_none": None, "settlement_finality_time_utc_or_none": None,
            "process_epoch_id": "process", "monotonic_clock_id": "monotonic",
            "wall_clock_source_id": "wall", "clock_quality_receipt_ref": "quality",
            "wall_clock_uncertainty_ns": 0,
        },
        "capture_commit_ref": "capture-commit", "publication_witness_ref": "publication",
        "commit_evidence_class": "COORDINATOR_POST_RETURN_UPPER_BOUND_REFERENCE_ONLY",
        "issued_at": "2026-01-01T00:00:00Z", "issued_monotonic_ns": 0,
    }
    assert receipt_owner._native_retail_clock_companion(body)["source_accepted"] is False
    for raw, reason in raw_cases:
        if len(raw) > 1048576:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeError:
            continue
        expected_type = SerializationSafetyError if reason.startswith("JSON") or reason == "DUPLICATE_JSON_KEY" else ContractValidationError
        with pytest.raises(expected_type) as caught:
            receipt_owner._native_retail_clock_companion({**body, "raw_body_utf8": text, "raw_byte_limit": 1048576})
        assert type(caught.value) is expected_type
        assert str(caught.value).endswith(": " + reason)
    with pytest.raises(SourcePolicyError) as caught:
        receipt_owner._native_retail_clock_companion({
            **body, "raw_body_utf8": '{"nested":{"Api_Key":"synthetic-private-marker"}}',
        })
    assert caught.value.reason_code is ReasonCode.SECRET_MATERIAL_REJECTED
    assert "synthetic-private-marker" not in str(caught.value)
    assert "Api_Key" not in str(caught.value)

    class ForeignContractError(ContractValidationError):
        pass

    for error in (
        ContractValidationError(ReasonCode.INVALID_CONTRACT, "JSON plus unrecognized detail"),
        ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "JSON"),
        ForeignContractError(ReasonCode.INVALID_CONTRACT, "JSON"),
        SourcePolicyError(ReasonCode.SOURCE_RIGHTS_BLOCKED, "synthetic source boundary"),
        PersistenceContractError(ReasonCode.PERSISTENCE_UNAVAILABLE, "synthetic backend boundary"),
        PointInTimeError(ReasonCode.POINT_IN_TIME_VIOLATION, "synthetic existing PIT boundary"),
    ):
        def fail(_raw, _limit):
            raise error
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(receipt_owner, "_native_strict_json", fail)
            with pytest.raises(type(error)) as caught:
                receipt_owner._native_retail_clock_companion(body)
            assert caught.value is error
