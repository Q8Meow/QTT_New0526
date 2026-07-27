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
