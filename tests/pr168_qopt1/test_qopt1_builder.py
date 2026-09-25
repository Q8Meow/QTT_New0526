from ._helpers import report, rows


def test_builder_creates_primary_artifacts(tmp_path, monkeypatch) -> None:
    run_report = report("run_receipt.report.json")
    assert run_report["branch_created_by_codex"] is True
    assert run_report["RANK4_outputs_consumed"] is True
    assert run_report["RP5G_refs_preserved"] is True
    assert run_report["candidate_count"] >= 1
    assert rows("batch_select.jsonl")

    # Keep the native two-build comparison byte-exact and preserve failure prefixes.
    from src.qtt.optimization.pr168_qopt1 import builder, validator

    for case in ("stable", "first_newline", "second_newline", "first_failure", "second_failure"):
        directory = tmp_path / case
        directory.mkdir()
        artifact = directory / "sample.json"
        artifact.write_bytes(b"{}\r\n")
        calls = []

        def controlled_build(*, out_dir):
            assert out_dir == directory
            calls.append(len(calls) + 1)
            if case == "first_failure" and len(calls) == 1:
                artifact.write_bytes(b"first-failure-prefix")
                raise OSError("intentional first build failure")
            if case == "second_failure" and len(calls) == 2:
                artifact.write_bytes(b"second-failure-prefix")
                raise OSError("intentional second build failure")
            content = b"{}\r\n"
            if case == "first_newline" or (case == "second_newline" and len(calls) == 2):
                content = b"{}\n"
            artifact.write_bytes(content)

        with monkeypatch.context() as patch:
            patch.setattr(builder, "run_layer", controlled_build)
            if case == "stable":
                validator._assert_deterministic(directory)
            elif case.endswith("newline"):
                try:
                    validator._assert_deterministic(directory)
                except validator.Qopt1ValidationError:
                    pass
                else:
                    raise AssertionError("newline-only byte drift was accepted")
            else:
                try:
                    validator._assert_deterministic(directory)
                except OSError as error:
                    assert "intentional" in str(error)
                else:
                    raise AssertionError("native builder failure was suppressed")
        assert len(calls) == (1 if case == "first_failure" else 2)
        if case.endswith("failure"):
            assert artifact.read_bytes().endswith(b"failure-prefix")
