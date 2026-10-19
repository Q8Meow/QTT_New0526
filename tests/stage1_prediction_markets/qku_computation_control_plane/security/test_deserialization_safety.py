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
    _assert_f14_bounded_witness_codec()
    _assert_kalshi_series_fee_candidate()
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


def _assert_kalshi_series_fee_candidate():
    from dataclasses import FrozenInstanceError, fields
    from decimal import Decimal, Inexact, Rounded, ROUND_CEILING, ROUND_FLOOR, localcontext
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError, SourcePolicyError

    candidate_type = owner.KalshiQuadraticSeriesFeeCandidateV1
    decode = owner.decode_kalshi_quadratic_series_fee_candidate_v1
    ticker = "QTT-SYNTHETIC-SERIES"

    def body(token=b"1"):
        return b'{"series":{"ticker":"QTT-SYNTHETIC-SERIES","fee_type":"quadratic","fee_multiplier":' + token + b'}}'

    raw = body()
    calls, decoded_trees = [], []
    real_parser = owner._native_strict_json

    def parser_spy(*args, **kwargs):
        calls.append((args, kwargs))
        tree = real_parser(*args, **kwargs)
        decoded_trees.append(tree)
        return tree

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(owner, "_native_strict_json", parser_spy)
        for token in (b"0", b"1", b"1.0", b"1e0", b"2", b"2.1", b"0.123456789012345678901234567890123456789"):
            supplied = body(token)
            calls.clear()
            candidate = decode(raw_response=supplied, expected_series_ticker=ticker)
            assert calls == [((supplied,), {})]
            assert calls[0][0][0] is supplied
            assert type(candidate) is candidate_type and candidate.series_ticker == ticker
            assert type(candidate.fee_multiplier) is Decimal
            assert candidate.fee_multiplier.as_tuple() == Decimal(token.decode("ascii")).as_tuple()
            wire_number = decoded_trees[-1]["series"]["fee_multiplier"]
            if token in (b"0", b"1", b"2"):
                assert type(wire_number) is int
            else:
                assert type(wire_number) is Decimal and candidate.fee_multiplier is wire_number
        for invalid in (None, "", " padded", "with space", "x" * 257, 1):
            calls.clear()
            with pytest.raises(ContractValidationError):
                decode(raw_response=b"not JSON", expected_series_ticker=invalid)
            assert calls == []

    candidate = decode(raw_response=raw, expected_series_ticker=ticker)
    assert tuple(field.name for field in fields(candidate)) == ("series_ticker", "fee_multiplier")
    assert candidate.__slots__ == ("series_ticker", "fee_multiplier") and not hasattr(candidate, "__dict__")
    with pytest.raises(FrozenInstanceError):
        candidate.fee_multiplier = Decimal(2)
    for kwargs in ({}, {"series_ticker": ticker}, {"fee_multiplier": Decimal(1)},
                   {"series_ticker": ticker, "fee_multiplier": Decimal(1), "accepted": True}):
        with pytest.raises(TypeError):
            candidate_type(**kwargs)
    for kwargs in ({}, {"raw_response": raw}, {"expected_series_ticker": ticker},
                   {"raw_response": raw, "expected_series_ticker": ticker, "max_bytes": 1048576}):
        with pytest.raises(TypeError):
            decode(**kwargs)
    with pytest.raises(TypeError):
        decode(raw, ticker)

    class DecimalSubclass(Decimal):
        pass

    class StringSubclass(str):
        pass

    class BytesSubclass(bytes):
        pass

    for value in (1, 1.0, True, "1", None, DecimalSubclass("1"), Decimal("-0"), Decimal("sNaN"),
                  Decimal("NaN"), Decimal("Infinity"), Decimal("-1"), Decimal("1e101"),
                  Decimal("1e-101"), Decimal("0e129"), Decimal("0e-129"), Decimal("0." + "1" * 129)):
        with pytest.raises(ContractValidationError):
            candidate_type(ticker, value)
    for value in (StringSubclass(ticker), None, "", " padded", "a\x00b", "x" * 257, "a\x80b", "\ud800"):
        with pytest.raises(ContractValidationError):
            candidate_type(value, Decimal(1))
    for token in (b"1e100", b"1e-100", b"0e128", b"0e-128", b"1" + b"0" * 100):
        assert decode(raw_response=body(token), expected_series_ticker=ticker).fee_multiplier == Decimal(token.decode())

    missing = (b'{}', b'{"series":{}}',
               raw.replace(b'"ticker":"QTT-SYNTHETIC-SERIES",', b''),
               raw.replace(b'"fee_type":"quadratic",', b''),
               raw.replace(b',"fee_multiplier":1', b''))
    for supplied in missing:
        with pytest.raises(ContractValidationError) as caught:
            decode(raw_response=supplied, expected_series_ticker=ticker)
        assert caught.value.reason_code is ReasonCode.INCOMPLETE_CONTRACT
        assert str(caught.value).endswith(": Kalshi series fee fields are missing")
    for supplied in (b'[]', b'null', b'1', b'"root"', b'{"series":null}', b'{"series":[]}', b'{"series":"x"}'):
        with pytest.raises(ContractValidationError, match="response shape is invalid") as caught:
            decode(raw_response=supplied, expected_series_ticker=ticker)
        assert caught.value.reason_code is ReasonCode.INVALID_CONTRACT
    for token in (b'"1"', b'true', b'false', b'null', b'[]', b'{}'):
        with pytest.raises(ContractValidationError, match="must be a JSON number"):
            decode(raw_response=body(token), expected_series_ticker=ticker)
    for family in (b'"flat"', b'"quadratic_with_maker_fees"', b'"Quadratic"', b'"unknown"', b'null', b'true', b'1'):
        with pytest.raises(ContractValidationError, match="outside the selected quadratic scope"):
            decode(raw_response=raw.replace(b'"quadratic"', family), expected_series_ticker=ticker)
    with pytest.raises(ContractValidationError) as caught:
        decode(raw_response=raw, expected_series_ticker=ticker.lower())
    assert caught.value.reason_code is ReasonCode.INPUT_SCOPE_MISMATCH
    for replacement in (b'null', b'true', b'1', b'""', b'" padded"', b'"x y"'):
        with pytest.raises(ContractValidationError):
            decode(raw_response=raw.replace(b'"QTT-SYNTHETIC-SERIES"', replacement), expected_series_ticker=ticker)
    escaped = raw.replace(b'"ticker"', b'"t\\u0069cker"').replace(b'"QTT-', b'"\\u0051TT-')
    assert decode(raw_response=escaped, expected_series_ticker=ticker) == candidate
    for width in (1, 256):
        identity = "\u00e9" * width
        supplied = raw.replace(ticker.encode(), identity.encode("utf-8"))
        assert decode(raw_response=supplied, expected_series_ticker=identity).series_ticker == identity

    for extra in (b',"last_updated_ts":"past","title":"A","exchange_index":0',
                  b',"last_updated_ts":"future","title":"B","exchange_index":12,"accepted":true,"nested":[{},[1,"text"]]'):
        supplied = raw[:-2] + extra + b'},"unrelated":{"current":true}}'
        assert decode(raw_response=supplied, expected_series_ticker=ticker) == candidate
    for supplied in (
        raw[:-1] + b',"Api_Key":"synthetic-private-marker"}',
        raw[:-2] + b',"nested":[{"authorization":"synthetic-private-marker"}]}}',
        b'{"series":null,"password":"synthetic-private-marker"}',
    ):
        with pytest.raises(SourcePolicyError) as caught:
            decode(raw_response=supplied, expected_series_ticker=ticker)
        assert caught.value.reason_code is ReasonCode.SECRET_MATERIAL_REJECTED
        assert "synthetic-private-marker" not in str(caught.value)
        assert all(key not in str(caught.value) for key in ("Api_Key", "authorization", "password"))

    for token, reason in ((b'-1', 'NONNEGATIVE'), (b'-0', 'NUMBER'), (b'-0.0', 'NUMBER'),
                          (b'-0e1', 'NUMBER'), (b'NaN', 'NONFINITE'), (b'Infinity', 'NONFINITE'),
                          (b'-Infinity', 'NONFINITE'), (b'1e101', 'NUMBER_BOUND'), (b'1e-101', 'NUMBER_BOUND'),
                          (b'0e129', 'NUMBER_BOUND'), (b'0e-129', 'NUMBER_BOUND'),
                          (b'1' * 129, 'NUMBER_BOUND'), (b'1.' + b'0' * 127, 'NUMBER_BOUND')):
        with pytest.raises(ContractValidationError) as caught:
            decode(raw_response=body(token), expected_series_ticker=ticker)
        assert str(caught.value).endswith(": " + reason)
    parser_cases = (
        (raw.replace(b'"fee_multiplier":1', b'"fee_multiplier":1,"fee_\\u006dultiplier":2'), 'DUPLICATE_JSON_KEY'),
        (raw[:-1] + b',"unused":{"x":1,"x":2}}', 'DUPLICATE_JSON_KEY'),
        (raw[:-1] + b',"unused":NaN}', 'NONFINITE'),
        (raw[:-1] + b',"unused":-0}', 'NUMBER'),
        (raw[:-1] + b',"unused":1e101}', 'NUMBER_BOUND'),
        (raw[:-1] + b',"unused":"\\ud800"}', 'SURROGATE'),
        (raw[:-1] + b'," bad":1}', 'TEXT'),
        (raw[:-1] + b',"unused":' + b'[' * 16 + b'0' + b']' * 16 + b'}', 'JSON_DEPTH'),
        (raw[:-1] + b',"unused":[' + b','.join([b'0'] * 4096) + b']}', 'JSON_NODES'),
        (b'', 'JSON'), (b'\xff', 'JSON'), (raw + b' trailing', 'JSON'), (b'{', 'JSON'),
    )
    for supplied, reason in parser_cases:
        with pytest.raises(ContractValidationError) as caught:
            decode(raw_response=supplied, expected_series_ticker=ticker)
        assert str(caught.value).endswith(": " + reason)
    for supplied in (raw.decode(), bytearray(raw), memoryview(raw), BytesSubclass(raw), None):
        with pytest.raises(ContractValidationError, match="JSON_BOUND"):
            decode(raw_response=supplied, expected_series_ticker=ticker)
    multibyte = raw[:-1] + b',"title":"' + "\u00e9".encode("utf-8") * 100 + b'"}'
    assert len(multibyte) > len(multibyte.decode("utf-8"))
    for supplied in (raw, multibyte):
        maximum = supplied + b' ' * (65536 - len(supplied))
        assert len(maximum) == 65536
        assert decode(raw_response=maximum, expected_series_ticker=ticker) == candidate
        with pytest.raises(ContractValidationError, match="JSON_BOUND"):
            decode(raw_response=maximum + b' ', expected_series_ticker=ticker)

    for name, error in (("_native_strict_json", ContractValidationError(ReasonCode.INCOMPLETE_CONTRACT, "synthetic parser sentinel")),
                        ("reject_secret_material", SourcePolicyError(ReasonCode.SECRET_MATERIAL_REJECTED, "synthetic secret sentinel"))):
        def fail(*args, **kwargs):
            raise error
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(owner, name, fail)
            with pytest.raises(type(error)) as caught:
                decode(raw_response=raw, expected_series_ticker=ticker)
            assert caught.value is error
    for precision in (1, 7, 28):
        for rounding in (ROUND_CEILING, ROUND_FLOOR):
            with localcontext() as ambient:
                ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax = precision, rounding, -2, 2
                ambient.traps[Inexact] = ambient.traps[Rounded] = True
                ambient.flags[Rounded] = True
                before = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                          ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
                assert decode(raw_response=body(b"2.1"), expected_series_ticker=ticker).fee_multiplier == Decimal("2.1")
                for token in (b"-0", b"-1", b"1e101"):
                    with pytest.raises(ContractValidationError):
                        decode(raw_response=body(token), expected_series_ticker=ticker)
                assert before == (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                                  ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))


    _assert_kalshi_market_link()


def _assert_kalshi_market_link():
    from dataclasses import FrozenInstanceError, fields
    from decimal import Decimal, Inexact, Rounded, ROUND_CEILING, ROUND_FLOOR, localcontext
    from inspect import Parameter, signature
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import source_policy as owner
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ContractValidationError, SourcePolicyError

    market = b'{"market":{"ticker":"SYNTHETIC::MARKET","event_ticker":"QTT-LINK-EVENT"}}'
    event = b'{"event":{"event_ticker":"QTT-LINK-EVENT","series_ticker":"QTT-LINK-SERIES"}}'
    series = b'{"series":{"ticker":"QTT-LINK-SERIES","fee_type":"quadratic","fee_multiplier":1}}'
    supplied = dict(raw_market_response=market, raw_event_response=event,
                    raw_series_response=series, expected_market_ticker="SYNTHETIC::MARKET")
    decode = owner.decode_kalshi_market_linked_series_fee_candidate_v1
    parameters = signature(decode).parameters
    assert tuple(parameters) == tuple(supplied)
    assert all(p.kind is Parameter.KEYWORD_ONLY and p.default is Parameter.empty for p in parameters.values())
    for omitted in supplied:
        with pytest.raises(TypeError):
            decode(**{key: value for key, value in supplied.items() if key != omitted})
    for extra in ("expected_event_ticker", "expected_series_ticker", "fee_multiplier", "max_bytes", "accepted"):
        with pytest.raises(TypeError):
            decode(**supplied, **{extra: None})
    with pytest.raises(TypeError):
        decode(*supplied.values())

    roster_names = ("CERTIFIED_SOURCE_STATES", "SOURCE_CURRENTIZATION_OVERLAYS", "SOURCE_STATE_BY_ID",
                    "SOURCE_OVERLAY_BY_ID", "ST12H_SOURCE_BINDINGS", "ST12H_SOURCE_CURRENTIZATION_RULES")
    rosters_before = tuple(tuple(getattr(owner, name)) for name in roster_names)
    parser_calls, series_calls, results, errors = [], [], [], []
    real_parser, real_series = owner._native_strict_json, owner.decode_kalshi_quadratic_series_fee_candidate_v1

    def parse(*args, **kwargs):
        parser_calls.append((args, kwargs))
        return real_parser(*args, **kwargs)

    def decode_series(**kwargs):
        series_calls.append(kwargs)
        try:
            result = real_series(**kwargs)
        except ContractValidationError as error:
            errors.append(error)
            raise
        results.append(result)
        return result

    class StringSubclass(str):
        pass

    class BytesSubclass(bytes):
        pass

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(owner, "_native_strict_json", parse)
        patch.setattr(owner, "decode_kalshi_quadratic_series_fee_candidate_v1", decode_series)
        for token in (b"0", b"1e0", b"2.1", b"0.123456789012345678901234567890123456789"):
            raw = series.replace(b'"fee_multiplier":1', b'"fee_multiplier":' + token)
            parser_calls.clear(); series_calls.clear()
            candidate = decode(**{**supplied, "raw_series_response": raw})
            assert parser_calls == [((body,), {}) for body in (market, event, raw)]
            assert all(call[0][0] is body for call, body in zip(parser_calls, (market, event, raw)))
            assert series_calls == [{"raw_response": raw, "expected_series_ticker": "QTT-LINK-SERIES"}]
            assert series_calls[0]["raw_response"] is raw and candidate is results[-1]
            assert type(candidate) is owner.KalshiQuadraticSeriesFeeCandidateV1
            assert candidate.fee_multiplier.as_tuple() == Decimal(token.decode()).as_tuple()
        for invalid in (None, 1, True, "", " padded", "a b", "x" * 257, StringSubclass("SYNTHETIC::MARKET")):
            parser_calls.clear(); series_calls.clear()
            with pytest.raises(ContractValidationError):
                decode(**{**supplied, "expected_market_ticker": invalid, "raw_market_response": b"{"})
            assert parser_calls == series_calls == []
        for expected in ("SYNTHETIC::MARKET-X", "synthetic::market", "SYNTHETIC/MARKET"):
            parser_calls.clear(); series_calls.clear()
            with pytest.raises(ContractValidationError, match="Kalshi market ticker does not match expected scope") as caught:
                decode(**{**supplied, "expected_market_ticker": expected, "raw_event_response": b"{"})
            assert caught.value.reason_code is ReasonCode.INPUT_SCOPE_MISMATCH
            assert parser_calls == [((market,), {})] and series_calls == []
        for identity in (b"QTT-LINK-EVENT-X", b"qtt-link-event", b"QTT/LINK/EVENT"):
            wrong_event = event.replace(b"QTT-LINK-EVENT", identity)
            parser_calls.clear(); series_calls.clear()
            with pytest.raises(ContractValidationError, match="Kalshi event ticker does not match market linkage") as caught:
                decode(**{**supplied, "raw_event_response": wrong_event, "raw_series_response": b"{"})
            assert caught.value.reason_code is ReasonCode.INPUT_SCOPE_MISMATCH
            assert parser_calls == [((market,), {}), ((wrong_event,), {})] and series_calls == []
        for raw, reason in (
            (series.replace(b"QTT-LINK-SERIES", b"OTHER-SERIES"), ReasonCode.INPUT_SCOPE_MISMATCH),
            (series.replace(b'"quadratic"', b'"flat"'), ReasonCode.INVALID_CONTRACT),
            (series.replace(b'"fee_multiplier":1', b'"fee_multiplier":-1'), ReasonCode.INVALID_CONTRACT),
        ):
            parser_calls.clear(); series_calls.clear(); errors.clear()
            with pytest.raises(ContractValidationError) as caught:
                decode(**{**supplied, "raw_series_response": raw})
            assert len(parser_calls) == 3 and len(series_calls) == 1
            assert caught.value is errors[0] and caught.value.reason_code is reason

    candidate = decode(**supplied)
    assert tuple(field.name for field in fields(candidate)) == ("series_ticker", "fee_multiplier")
    assert candidate.__slots__ == ("series_ticker", "fee_multiplier") and not hasattr(candidate, "__dict__")
    with pytest.raises(FrozenInstanceError):
        candidate.series_ticker = "OTHER"
    for width in (1, 256):
        identities = ("é" * width, "Z" * width, "y" * width)
        renamed = dict(raw_market_response=market.replace(b"SYNTHETIC::MARKET", identities[0].encode()).replace(b"QTT-LINK-EVENT", identities[1].encode()),
                       raw_event_response=event.replace(b"QTT-LINK-EVENT", identities[1].encode()).replace(b"QTT-LINK-SERIES", identities[2].encode()),
                       raw_series_response=series.replace(b"QTT-LINK-SERIES", identities[2].encode()), expected_market_ticker=identities[0])
        result = decode(**renamed)
        assert result.series_ticker == identities[2] and result.fee_multiplier == candidate.fee_multiplier
    escaped = {key: value.replace(b"SYNTHETIC", b"\\u0053YNTHETIC").replace(b"QTT", b"\\u0051TT") if type(value) is bytes else value
               for key, value in supplied.items()}
    assert decode(**escaped) == candidate

    for argument, root, raw, pairs in (
        ("raw_market_response", b"market", market, ((b"ticker", b"SYNTHETIC::MARKET"), (b"event_ticker", b"QTT-LINK-EVENT"))),
        ("raw_event_response", b"event", event, ((b"event_ticker", b"QTT-LINK-EVENT"), (b"series_ticker", b"QTT-LINK-SERIES"))),
    ):
        for body in (b'{}', b'{"alias":' + raw + b'}', raw.replace(b'"' + root + b'":', b'"other":'),
                     b'{"' + root + b'":{}}', *(raw.replace(b'"' + key + b'":', b'"alias":') for key, _ in pairs)):
            with pytest.raises(ContractValidationError, match="Kalshi linked identity fields are missing") as caught:
                decode(**{**supplied, argument: body})
            assert caught.value.reason_code is ReasonCode.INCOMPLETE_CONTRACT
        for body in (b'[]', b'null', b'1', b'"root"', *(b'{"' + root + b'":' + value + b'}' for value in (b'null', b'[]', b'1', b'"x"'))):
            with pytest.raises(ContractValidationError, match="Kalshi linked identity response shape is invalid") as caught:
                decode(**{**supplied, argument: body})
            assert caught.value.reason_code is ReasonCode.INVALID_CONTRACT
        for key, identity in pairs:
            for token in (b'null', b'true', b'1', b'1.0', b'[]', b'{}', b'""', b'" padded"', b'"a b"', b'"' + b'x' * 257 + b'"'):
                body = raw.replace(b'"' + identity + b'"', token)
                with pytest.raises(ContractValidationError) as caught:
                    decode(**{**supplied, argument: body})
                assert caught.value.reason_code is ReasonCode.INVALID_CONTRACT
            duplicate = raw.replace(b'"' + key + b'":', b'"' + key + b'":"x","' + key.replace(b't', b'\\u0074', 1) + b'":')
            with pytest.raises(ContractValidationError, match="DUPLICATE_JSON_KEY"):
                decode(**{**supplied, argument: duplicate})
        for body, detail in ((b'\xff', "JSON"), (b'{', "JSON"), (raw + b'trailing', "JSON"),
                             (raw[:-1] + b',"unused":NaN}', "NONFINITE")):
            with pytest.raises(ContractValidationError) as caught:
                decode(**{**supplied, argument: body})
            assert str(caught.value).endswith(": " + detail)
        for body in (raw.decode(), bytearray(raw), memoryview(raw), BytesSubclass(raw), None):
            with pytest.raises(ContractValidationError, match="JSON_BOUND"):
                decode(**{**supplied, argument: body})
        maximum = raw + b' ' * (65536 - len(raw))
        assert decode(**{**supplied, argument: maximum}) == candidate
        with pytest.raises(ContractValidationError, match="JSON_BOUND"):
            decode(**{**supplied, argument: maximum + b' '})
        for body in (raw[:-1] + b',"unused":[{"authorization":"synthetic-private-marker"}]}',
                     b'{"' + root + b'":null,"Api_Key":"synthetic-private-marker"}'):
            with pytest.raises(SourcePolicyError) as caught:
                decode(**{**supplied, argument: body})
            assert caught.value.reason_code is ReasonCode.SECRET_MATERIAL_REJECTED
            assert all(text not in str(caught.value) for text in ("synthetic-private-marker", "authorization", "Api_Key"))
        additive = raw[:-2] + b',"markets":[{"ticker":"OTHER"}],"fee_multiplier":99,"override":true,"accepted":true},"markets":[],"current":true}'
        assert decode(**{**supplied, argument: additive}) == candidate

    for precision in (1, 7, 28):
        for rounding in (ROUND_CEILING, ROUND_FLOOR):
            with localcontext() as ambient:
                ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax = precision, rounding, -2, 2
                ambient.traps[Inexact] = ambient.traps[Rounded] = True
                ambient.flags[Rounded] = True
                before = (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                          ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
                assert decode(**{**supplied, "raw_series_response": series.replace(b'"fee_multiplier":1', b'"fee_multiplier":2.1')}).fee_multiplier == Decimal("2.1")
                with pytest.raises(ContractValidationError):
                    decode(**{**supplied, "raw_series_response": series.replace(b'"fee_multiplier":1', b'"fee_multiplier":-0')})
                assert before == (ambient.prec, ambient.rounding, ambient.Emin, ambient.Emax,
                                  ambient.capitals, ambient.clamp, dict(ambient.traps), dict(ambient.flags))
    assert rosters_before == tuple(tuple(getattr(owner, name)) for name in roster_names)
    assert supplied == dict(raw_market_response=market, raw_event_response=event,
                            raw_series_response=series, expected_market_ticker="SYNTHETIC::MARKET")


def _assert_f14_bounded_witness_codec():
    import copy
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane import receipts as r, serialization as s
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import ComputationControlPlaneError
    from src.qtt.stage1_prediction_markets.private_state_receipts.handoff import _f14_spine_v1
    from tests.source_evidence.test_s1_pit_data_phase_a_01 import _f14_reference_cases
    args=_f14_reference_cases()[0][0]
    body,witnesses=args[:2]
    scope=body['scope']
    from collections import UserDict
    from src.qtt.stage1_prediction_markets.private_state_receipts.handoff import _f14_allocation_v1
    from src.qtt.stage1_prediction_markets.qku_computation_control_plane.persistence import PrivateEvidenceReadRequestV1
    read = _f14_allocation_v1(scope, 'closed-phase-roster', ())
    controls = {key: dict(value) for key, value in read.phase_control_refs.items()}
    invalid = []
    for value in (None, False, True, 0, 1, 'extra', [], (), {}, {'claim_ref': 'extra'}):
        invalid.append({**controls, 'EXTRA': value})
    for phase in ('A', 'B', 'C'):
        invalid.append({key: value for key, value in controls.items() if key != phase})
        invalid.append({('OTHER' if key == phase else key): value for key, value in controls.items()})
        for value in (None, False, True, 0, 1, 'phase', [], (), {}):
            invalid.append({**controls, phase: value})
        for field in controls[phase]:
            for value in (None, True, 0, '', [], {}):
                invalid.append({**controls, phase: {**controls[phase], field: value}})
            invalid.append({**controls, phase: {key: value for key, value in controls[phase].items() if key != field}})
        invalid.append({**controls, phase: {**controls[phase], 'extra': 'unlisted'}})
        invalid.append({**controls, phase: {**controls[phase], 'result_binding_ref': 'unbound'}})
        invalid.append({**controls, phase: {**controls[phase], 'transition_ref': controls[phase]['claim_ref']}})
    for malformed in invalid:
        before = copy.deepcopy(malformed)
        with pytest.raises(ComputationControlPlaneError):
            PrivateEvidenceReadRequestV1(read.scope, read.record_refs, malformed)
        assert malformed == before
    for mapping in (dict, MappingProxyType, UserDict):
        supplied = {key: mapping(dict(value)) for key, value in controls.items()}
        restored = PrivateEvidenceReadRequestV1(mapping(dict(read.scope)), mapping(dict(read.record_refs)), mapping(supplied))
        assert restored == read
        with pytest.raises(TypeError): restored.phase_control_refs['A']['claim_ref'] = 'changed'
        supplied['A'] = {'claim_ref': 'detached'}
        assert restored.phase_control_refs['A'] == controls['A']
    phases={'RAW':('raw',dict(scope=scope,raw_body_utf8=body['raw_body_utf8'])),
        'TRANSPORT':('transport',s._native_retail_transport_storage_projection_v1(witnesses['transport'],expected_binding_ref='authentication')),
        'CAPTURE_COMMIT':('capture-commit',witnesses['capture_commit']),
        'PUBLICATION':('publication',witnesses['publication']),
        'COMPANION_COMMIT':('seal',witnesses['companion_commit']),
        'CLOCK_PROOF':('proof',dict(record_id='proof',scope=scope,subject_raw_record_ref='raw',
            source_binding_ref='source',value='2026-09-13T00:00:00.000000000Z'))}
    times={'TRANSPORT':'parse_completed_at','CAPTURE_COMMIT':'completed_at','PUBLICATION':'published_at','COMPANION_COMMIT':'completed_at'}
    for phase,(rid,payload) in phases.items():
        before=copy.deepcopy(payload)
        w=r._f14_witness_v1(rid,phase,payload)
        stamp=payload[times[phase]] if phase in times else '2026-09-13T00:00:00.000000002Z'
        row=_f14_spine_v1(rid,w,scope,stamp,'codec-attempt')
        text=s.deterministic_json(row)
        restored,decoded=s._f14_hydrate_v1(text,rid,phase,scope)
        assert restored == w and decoded == before and payload == before
        decoded['scope']['ledger_account_ref']='detached'
        assert payload == before
        for prefix in (' ','\n'):
            with pytest.raises(SerializationSafetyError,match='F14_STORAGE_NONCANONICAL'):
                s._f14_hydrate_v1(prefix+text,rid,phase,scope)
        for field,value in (('sequence',True),('sequence',2**63),('record_id','foreign'),
                ('aggregate_id','foreign'),('semantic_owner','x'*257),('authority_class','LIVE')):
            data=s.safe_json_loads(text);data[field]=value
            with pytest.raises(ComputationControlPlaneError):
                s._f14_hydrate_v1(s._f14_dumps_v1(data),rid,phase,scope)
    for raw in ('{"authorization":"synthetic"}','{"nested":{"sessionToken":"synthetic"}}',
            '{"password":"synthetic"}','{"x":1,"x":2}','{"x":NaN}'):
        with pytest.raises(ComputationControlPlaneError):
            r._f14_witness_v1('raw','RAW',dict(scope=scope,raw_body_utf8=raw))
    maximum='{}'+'\n'*(1048576-2)
    assert r._f14_witness_v1('raw','RAW',dict(scope=scope,raw_body_utf8=maximum)).record_id == 'raw'
    with pytest.raises(ComputationControlPlaneError):
        r._f14_witness_v1('raw','RAW',dict(scope=scope,raw_body_utf8=maximum+' '))
    with pytest.raises(ComputationControlPlaneError):
        r._f14_witness_v1('transport','TRANSPORT',{**phases['TRANSPORT'][1],'credential_binding_ref':'authentication'})
