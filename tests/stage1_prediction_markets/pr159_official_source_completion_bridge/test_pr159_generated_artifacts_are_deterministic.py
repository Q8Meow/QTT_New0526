from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge.validator import validate_existing_artifacts
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import ROOT


def test_pr159_generated_artifacts_are_deterministic(tmp_path, monkeypatch):
    assert validate_existing_artifacts(ROOT).ok


    # Byte currentness is stricter than text/JSON equivalence.
    from types import SimpleNamespace
    import pytest
    from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import validator as native

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
