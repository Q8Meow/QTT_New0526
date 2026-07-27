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
    valid_paths = (
        ("reports/β–contract.json", "reports/β–contract.json"),
        (r"reports\contract.json", "reports/contract.json"),
        ("a/CONTEXT.json", "a/CONTEXT.json"),
        ("a/CONIN$foo.txt", "a/CONIN$foo.txt"),
        ("a/CONOUT$foo.txt", "a/CONOUT$foo.txt"),
        ("a/CLOCKWORK.txt", "a/CLOCKWORK.txt"),
        ("a/COM10.txt", "a/COM10.txt"),
        ("a/LPT10.txt", "a/LPT10.txt"),
    )
    for path, expected in valid_paths:
        assert validate_relative_path(path) == expected, path

    assert deterministic_json({"punctuation": "β–contract\r\nline"}) == (
        '{"punctuation":"β–contract\\r\\nline"}'
    )
    invalid_paths = (
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
        "a/CONIN$.txt",
        "a/CONOUT$.txt",
        "a/CLOCK$.txt",
        "a/clock$.txt",
        "a/\x7fcontrol",
        *(
            f"a/name{character}.json"
            for character in '<>:"|?*'
        ),
    )
    for unsafe in invalid_paths:
        try:
            validate_relative_path(unsafe)
        except SerializationSafetyError as caught:
            assert caught.reason_code is ReasonCode.PATH_UNSAFE, unsafe
        else:
            pytest.fail(f"unsafe path accepted: {unsafe!r}")
