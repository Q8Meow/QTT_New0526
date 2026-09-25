def test_pr159r_generated_artifacts_are_deterministic(pr159r_validation_result, tmp_path, monkeypatch):
    assert not pr159r_validation_result.failures


    # Byte currentness is stricter than text/JSON equivalence.
    from types import SimpleNamespace
    import pytest
    from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture import validator as native

    expected = SimpleNamespace(payloads={"currentness.json": {"probe": 1}},
        markdown_payloads={"currentness.md": "first\nsecond\n"}, owner_response={"probe": 2})
    serialized = [("currentness.json", native.json_dump({"probe": 1})),
                  ("currentness.md", expected.markdown_payloads["currentness.md"])]
    with monkeypatch.context() as patch:
        patch.setattr(native, "build_artifacts", lambda root: expected)
        for rel, value in serialized:
            path = tmp_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value.encode("utf-8"))
        failures = []
        native._validate_currentness(tmp_path, failures)
        assert failures == []
        for rel, value in serialized:
            path = tmp_path / rel
            canonical = value.encode("utf-8")
            for replacement in (b"\r\n", b"\r"):
                changed = canonical.replace(b"\n", replacement)
                assert changed != canonical
                path.write_bytes(changed)
                failures = []
                native._validate_currentness(tmp_path, failures)
                assert len(failures) == 1
                assert "NOT_DETERMINISTIC_CURRENT" in failures[0]
                assert path.read_bytes() == changed
            path.write_bytes(b"\xff")
            with pytest.raises(UnicodeDecodeError):
                native._validate_currentness(tmp_path, [])
            assert path.read_bytes() == b"\xff"
            path.write_bytes(canonical)
        failures = []
        native._validate_currentness(tmp_path, failures)
        assert failures == []

    from pathlib import Path
    from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture import io as native_io
    write_options = []
    original_write = Path.write_text
    def observed_write(path, data, **options):
        write_options.append(options)
        return original_write(path, data, **options)
    with monkeypatch.context() as patch:
        patch.setattr(Path, "write_text", observed_write)
        native_io.write_json(tmp_path / "writer.json", {"probe": 1})
        native_io.write_text(tmp_path / "writer.txt", "first\nsecond\n")
    assert len(write_options) == 2
    assert all(options.get("newline") == "\n" for options in write_options)
    assert (tmp_path / "writer.json").read_bytes() == native_io.json_dump({"probe": 1}).encode("utf-8")
    assert (tmp_path / "writer.txt").read_bytes() == b"first\nsecond\n"
