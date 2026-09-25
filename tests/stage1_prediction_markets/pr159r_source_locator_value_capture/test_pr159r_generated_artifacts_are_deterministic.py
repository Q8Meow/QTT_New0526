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

    # The existing central branch owner, not a test-only validator bypass,
    # admits local cumulative PR159R validation only with original ancestry.
    branch_owner = native.ci_branch_context
    cumulative = "repair/main-cumulative-v35-final-r5-local-20260922"
    for branch_name in (cumulative, "repair/main-cumulative-contract-test"):
        assert branch_owner.is_branch_allowed_for_upstream_pr_gate(
            branch_name, "PR159R", ancestry_present=True, include_main=True) is True
        for ancestry, include in ((False, True), (True, False), (1, True),
                                  (True, 1), (None, True), (True, None)):
            assert branch_owner.is_branch_allowed_for_upstream_pr_gate(
                branch_name, "PR159R", ancestry_present=ancestry,
                include_main=include) is False
        assert branch_owner.is_branch_allowed_for_upstream_pr_gate(
            branch_name, "PR159R", ancestry_present=True) is False
        assert branch_owner.is_pull_request_detached_head_context_allowed_for_upstream_pr_gate(
            branch_name, "PR159R") is False
        for gate_id in branch_owner.BRANCH_CONTEXT_GATE_POLICIES:
            if gate_id != "PR159R":
                assert branch_owner.is_branch_allowed_for_upstream_pr_gate(
                    branch_name, gate_id, ancestry_present=True,
                    include_main=True) is False
    for branch_name in ("", "HEAD", "repair/unrelated", "repair/main-cumulative-"):
        assert branch_owner.is_branch_allowed_for_upstream_pr_gate(
            branch_name, "PR159R", ancestry_present=True, include_main=True) is False
    assert branch_owner.is_branch_allowed_for_upstream_pr_gate(
        "main", "PR159R", ancestry_present=True, include_main=True) is True
    assert branch_owner.is_branch_allowed_for_upstream_pr_gate(
        "main", "PR159R", ancestry_present=False, include_main=True) is False
    assert branch_owner.is_branch_allowed_for_upstream_pr_gate(
        native.c.EXPECTED_BRANCH, "PR159R") is True

    # Original caller with explicitly synthetic Git and ancestry ports.
    # No native repository ancestry or CI permission is manufactured here.
    for ancestry_result in (False, True):
        git_calls = []
        ancestry_calls = []
        def recorded_git(root, arguments):
            git_calls.append(tuple(arguments))
            assert tuple(arguments) == ("branch", "--show-current")
            return (0, cumulative, "")
        def recorded_ancestry(root, branch_context="", *, refresh_shallow=False):
            ancestry_calls.append((root, branch_context, refresh_shallow))
            return ancestry_result
        with monkeypatch.context() as patch:
            for environment_key in (*branch_owner.BRANCH_CONTEXT_ENV_CANDIDATES,
                                    "GITHUB_ACTIONS", "GITHUB_EVENT_NAME", "GITHUB_HEAD_REF",
                                    "GITHUB_REF_NAME", "GITHUB_REF", "QTT_BRANCH_CONTEXT"):
                patch.delenv(environment_key, raising=False)
            patch.setattr(native, "_git_stdout", recorded_git)
            patch.setattr(native, "_pr159r_or_repair_ancestry_present", recorded_ancestry)
            failures, receipts = [], []
            native._validate_branch(tmp_path, failures, receipts)
        assert failures == ([] if ancestry_result else ["PR159R_BLOCKED_WRONG_BRANCH:" + cumulative])
        assert receipts == []
        assert git_calls == [("branch", "--show-current"), ("branch", "--show-current")]
        assert ancestry_calls == [(tmp_path, "", False)]
