from tests.pr169_dash1_ui1.conftest import UI, UI_ARTIFACT_FILES, ui_doc


def test_ui1_generated_projections_not_manual_truth(tmp_path, monkeypatch) -> None:
    for name in UI_ARTIFACT_FILES:
        assert (UI / name).exists(), name
        meta = ui_doc(name)["meta"]
        assert meta["generated_from"].startswith("owner_dashboard_surface_registry.jsonl")
        assert meta["manual_edit_allowed"] is False
        assert meta["runtime_truth_authority"] is False
        assert meta["agent_consumable_authority"] is False

    # Exercise both shared writers inside the original collected test.
    import json
    from pathlib import Path
    import pytest
    from tools import build_pr169_dash1_owner_dashboard_ui as builder

    original_open = Path.open
    for writer, payload, expected in (
        (builder._write_json, {"synthetic": 1},
         (json.dumps({"synthetic": 1}, indent=2, sort_keys=True) + "\n").encode("utf-8")),
        (builder._write_text, "A\nB\n", b"A\nB\n"),
    ):
        operand = tmp_path / (writer.__name__ + ".txt")
        for newline in (b"\r\n", b"\r"):
            operand.write_bytes(expected.replace(b"\n", newline))
            writer(operand, payload)
            assert operand.read_bytes() == expected

        # Exact current bytes must not be reopened for truncating writes.
        operand.write_bytes(expected)
        def observe_open(path, mode="r", *args, **kwargs):
            if path == operand and any(flag in mode for flag in "wax+"):
                raise AssertionError("unchanged canonical output was reopened for writing")
            return original_open(path, mode, *args, **kwargs)
        with monkeypatch.context() as patch:
            patch.setattr(Path, "open", observe_open)
            writer(operand, payload)
        assert operand.read_bytes() == expected

        # Retain the original strict UTF-8 error, without changing failed input.
        operand.write_bytes(b"\xff")
        with pytest.raises(UnicodeDecodeError):
            writer(operand, payload)
        assert operand.read_bytes() == b"\xff"
