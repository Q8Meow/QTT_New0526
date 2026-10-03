from __future__ import annotations

from ._helpers import assert_rp5d_valid


def test_rp5d_validator_passes(tmp_path, monkeypatch) -> None:
    # Keep real inputs at their original repository root. RP5D records physical
    # output paths relative to that root, so use the existing admitted local
    # disposable-run owner rather than changing input roots or path semantics.
    from functools import lru_cache
    from pathlib import Path
    from . import _helpers as helpers
    from src.qtt.stage1_prediction_markets.pr168_rp5d_executability import (
        models, runner, validator,
    )
    from tools import validation_reliability as reliability

    original_helper = helpers.assert_rp5d_valid
    original_validation = validator._validation_result
    helper_cache = original_helper.cache_info()
    validation_cache = original_validation.cache_info()
    output_bindings = (helpers.GENERATED_DIR, runner.GENERATED_DIR, validator.GENERATED_DIR)
    isolated_helper = lru_cache(maxsize=1)(original_helper.__wrapped__)
    isolated_validation = lru_cache(maxsize=1)(original_validation.__wrapped__)
    owned, probe = reliability.resolve_validation_run_paths(
        models.REPO_ROOT,
        explicit_process_root=models.REPO_ROOT / ".qtt" / "runs",
        projected_relative_paths=tuple(
            "validation-output/" + name for name in models.all_artifact_filenames()
        ),
    )
    body_error = None
    try:
        assert owned.process_root_is_external_to_repo is False
        assert probe.failure_operation is None
        assert owned.validation_output_root.is_relative_to(models.REPO_ROOT)
        assert not any(owned.validation_output_root.iterdir())
        with monkeypatch.context() as patch:
            patch.setattr(helpers, "GENERATED_DIR", owned.validation_output_root)
            patch.setattr(runner, "GENERATED_DIR", owned.validation_output_root)
            patch.setattr(validator, "GENERATED_DIR", owned.validation_output_root)
            patch.setattr(helpers, "assert_rp5d_valid", isolated_helper)
            patch.setattr(validator, "_validation_result", isolated_validation)
            assert_rp5d_valid = isolated_helper
            result = assert_rp5d_valid()

            assert result["validation"] == "PR168_RP5D_REPLAY_PAPER_EXECUTABILITY_OK"
            assert Path(result["artifact_dir"]) == owned.validation_output_root.relative_to(models.REPO_ROOT)
            assert isolated_helper.cache_info().misses == 1
            assert isolated_validation.cache_info().misses == 1
        assert helpers.assert_rp5d_valid is original_helper
        assert validator._validation_result is original_validation
        assert original_helper.cache_info() == helper_cache
        assert original_validation.cache_info() == validation_cache
        assert (helpers.GENERATED_DIR, runner.GENERATED_DIR, validator.GENERATED_DIR) == output_bindings
    except BaseException as error:
        body_error = error
        raise
    finally:
        try:
            cleanup_state = reliability.cleanup_validation_run(owned)
        except BaseException as cleanup_error:
            if body_error is not None:
                raise BaseExceptionGroup(
                    "RP5D isolated validation and owned cleanup both failed",
                    [body_error, cleanup_error],
                ) from None
            raise
    assert cleanup_state == "PASS_REMOVED_EXACT_RUN_ROOT"
    assert not owned.process_root.exists()

    # Original real-input assertion above stays mandatory in the full test.
    from src.qtt.stage1_prediction_markets.pr168_rp5d_executability import runner, validator

    for case in ("same", "newline", "first_failure", "second_failure"):
        root = tmp_path / case
        root.mkdir()
        target = root / "one.json"
        target.write_bytes(b"original\n")
        calls = []

        def build(*, offline):
            assert offline is True
            calls.append(None)
            target.write_bytes(b"changed\r\n" if case == "newline" and len(calls) == 2 else b"changed\n")
            if case == "first_failure" or (case == "second_failure" and len(calls) == 2):
                raise RuntimeError(case)

        with monkeypatch.context() as patch:
            patch.setattr(validator, "GENERATED_DIR", root)
            patch.setattr(runner, "run_layer", build)
            try:
                validator._assert_deterministic()
            except validator.RP5DValidationError:
                assert case == "newline"
            except RuntimeError as exc:
                assert case in {"first_failure", "second_failure"} and str(exc) == case
            else:
                assert case == "same"
        assert len(calls) == (1 if case == "first_failure" else 2)
        assert target.read_bytes() != b"original\n"
