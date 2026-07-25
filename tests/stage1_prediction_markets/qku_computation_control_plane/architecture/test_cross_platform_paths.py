import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ReasonCode,
    SerializationSafetyError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.serialization import (
    validate_relative_path,
)


def test_paths_are_normalized_relative_and_traversal_safe() -> None:
    assert validate_relative_path(r"reports\contract.json") == "reports/contract.json"
    for unsafe in (
        "../escape",
        "/absolute",
        r"C:\absolute",
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
