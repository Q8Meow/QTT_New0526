from ._helpers import ensure_built, report


def test_rank4_builder_and_validator_pass(tmp_path, monkeypatch) -> None:
    # Bind this test's real builder/validator helper to its pytest-owned output.
    # Keep any pre-existing helper cache intact; use the same original helper body.
    from functools import lru_cache
    from . import _helpers as artifact_helpers

    original_output_dir = artifact_helpers.GENERATED_DIR
    original_ensure_built = artifact_helpers.ensure_built
    original_cache_info = original_ensure_built.cache_info()
    generated_dir = tmp_path / "native-artifacts"
    assert generated_dir != original_output_dir
    isolated_ensure_built = lru_cache(maxsize=1)(original_ensure_built.__wrapped__)
    with monkeypatch.context() as output_patch:
        output_patch.setattr(artifact_helpers, "GENERATED_DIR", generated_dir)
        output_patch.setattr(artifact_helpers, "ensure_built", isolated_ensure_built)
        ensure_built = isolated_ensure_built
        out_dir = ensure_built()
        assert (out_dir / "art_reg.json").is_file()
        assert report("run_receipt.report.json")["RP5G_outputs_consumed"] is True
        assert isolated_ensure_built() == generated_dir
    assert artifact_helpers.GENERATED_DIR == original_output_dir
    assert artifact_helpers.ensure_built is original_ensure_built
    assert original_ensure_built.cache_info() == original_cache_info

    # Keep the native two-build comparison byte-exact and preserve failure prefixes.
    from src.qtt.ranking.pr168_rank4 import builder, validator

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
                except validator.Rank4ValidationError:
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
