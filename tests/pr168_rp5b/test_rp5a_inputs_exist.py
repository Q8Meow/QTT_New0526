from tests.pr168_rp5b._helpers import load_report, load_rows


def test_rp5a_inputs_exist(monkeypatch, tmp_path) -> None:
    report = load_report("PR168_RP5B_RP5AInputIntegrity.report.json")
    rows = load_rows("rp5a_input_integrity_rows")
    assert report["rp5a_input_integrity_passed"] is True
    assert rows
    assert all(row["integrity_status"] == "PASS" for row in rows)

    from types import SimpleNamespace
    from tools import pr168_rp5b_validator as validator

    # Preserve real report assertions; these scoped ports test query propagation.
    for exits in ((0, 0), (1, 0), (128, 0), (0, 1), (0, 128), (0, 2)):
        calls = []

        def run(args, **kwargs):
            index = len(calls)
            calls.append(args)
            return SimpleNamespace(returncode=exits[index], stdout="", stderr="diagnostic")

        with monkeypatch.context() as patch:
            patch.setattr(validator.subprocess, "run", run)
            try:
                result = validator._git_deleted_files()
            except RuntimeError:
                assert exits != (0, 0)
            else:
                assert exits == (0, 0) and result == set()
        assert len(calls) == (1 if exits[0] else 2)

    import json
    import pytest
    from tools import pr168_rp5b_rp5a_loader as loader

    path = tmp_path / "offline-preflight-fixture.json"
    requests = []
    def unexpected_request(*args, **kwargs):
        requests.append((args, kwargs))
        raise AssertionError("offline lookup attempted a command")
    with monkeypatch.context() as patch:
        patch.setattr(loader, "report_path", lambda _name: path)
        patch.setattr(loader, "_run_text", unexpected_request)
        patch.setattr(loader, "_run_json", unexpected_request)
        with pytest.raises(RuntimeError, match="RP5B_OFFLINE_PREFLIGHT_MISSING"):
            loader.collect_preflight(offline=True)
        for value in ({}, {"records": None}, {"records": []}, []):
            path.write_text(json.dumps(value), encoding="utf-8")
            with pytest.raises(RuntimeError, match="RP5B_OFFLINE_PREFLIGHT_RECORDS_INVALID"):
                loader.collect_preflight(offline=True)
        for records in ({}, {"unchanged": [1, 2]}):
            path.write_text(json.dumps({"records": records}), encoding="utf-8")
            assert loader.collect_preflight(offline=True) == records
        failure = OSError("original offline acquisition failure")
        def read_failure(_path):
            raise failure
        patch.setattr(loader, "read_json", read_failure)
        with pytest.raises(OSError) as raised:
            loader.collect_preflight(offline=True)
        assert raised.value is failure
        for value in (None, 0, 1, "true"):
            with pytest.raises(TypeError):
                loader.collect_preflight(offline=value)
    assert requests == []
