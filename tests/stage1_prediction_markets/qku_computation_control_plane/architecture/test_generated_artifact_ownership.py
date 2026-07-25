import pytest

from tools.build_qku_computation_control_plane import (
    REPO_ROOT,
    build_payload,
    resolve_output_path,
)


def test_builder_is_in_memory_and_creates_no_generated_truth() -> None:
    payload = build_payload()
    assert payload["contract_only"] is True
    assert payload["runtime_effect_authorized"] is False
    assert "output_path" not in payload
    assert payload["coverage_denominators"]["total_rows"] == 311
    assert payload["physical_path_denominators"]["total_paths"] == 77
    assert resolve_output_path(".tmp/st12a-builder/result.json") == (
        REPO_ROOT / ".tmp/st12a-builder/result.json"
    ).resolve()
    for unsafe in (
        "build-output.json",
        "src/generated.json",
        "../escape.json",
        ".tmp",
    ):
        with pytest.raises(ValueError):
            resolve_output_path(unsafe)
