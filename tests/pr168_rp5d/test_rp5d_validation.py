from __future__ import annotations

from ._helpers import assert_rp5d_valid


def test_rp5d_validator_passes(tmp_path, monkeypatch) -> None:
    result = assert_rp5d_valid()

    assert result["validation"] == "PR168_RP5D_REPLAY_PAPER_EXECUTABILITY_OK"

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
