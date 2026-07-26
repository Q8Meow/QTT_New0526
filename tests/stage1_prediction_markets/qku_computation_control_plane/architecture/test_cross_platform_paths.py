import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ReasonCode,
    SerializationSafetyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    deterministic_json,
    validate_relative_path,
)


def test_paths_are_normalized_relative_and_traversal_safe() -> None:
    assert validate_relative_path(r"reports\contract.json") == "reports/contract.json"
    assert validate_relative_path("reports/β–contract.json") == (
        "reports/β–contract.json"
    )
    assert deterministic_json({"punctuation": "β–contract\r\nline"}) == (
        '{"punctuation":"β–contract\\r\\nline"}'
    )
    for unsafe in (
        "../escape",
        "/absolute",
        r"C:\absolute",
        r"c:relative",
        r"\\server\share\file.json",
        r"a\..\escape",
        "a//file.json",
        "a/./file.json",
        "a/NUL.txt",
        "a/COM1",
        "a/trailing.",
        "a/trailing ",
        "a/stream:name",
        "a/\x1fcontrol",
    ):
        with pytest.raises(SerializationSafetyError) as caught:
            validate_relative_path(unsafe)
        assert caught.value.reason_code is ReasonCode.PATH_UNSAFE
