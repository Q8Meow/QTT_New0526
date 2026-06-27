from __future__ import annotations

import pytest


@pytest.fixture(scope="session", autouse=True)
def _build_rp5e_artifacts() -> None:
    from src.qtt.stage1_prediction_markets.pr168_rp5e_stack_generator.runner import run_layer
    from src.qtt.stage1_prediction_markets.pr168_rp5e_stack_generator.validator import (
        RP5EValidationError,
        run_validation,
    )

    try:
        run_validation()
        return
    except (FileNotFoundError, RP5EValidationError):
        pass

    report = run_layer(offline=True, fixture="sample", max_stacks=1000, dump_temp=True)
    assert report["runtime_stack_preview_rows"] > 0
    assert report["retained_topk_preview_rows"] > 0
