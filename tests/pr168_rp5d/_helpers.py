from __future__ import annotations

from functools import lru_cache

from src.qtt.stage1_prediction_markets.pr168_rp5d_executability.models import (
    GENERATED_DIR,
    read_json,
    read_jsonl,
)
from src.qtt.stage1_prediction_markets.pr168_rp5d_executability.runner import run_layer
from src.qtt.stage1_prediction_markets.pr168_rp5d_executability.validator import (
    run_validation,
)


@lru_cache(maxsize=1)
def assert_rp5d_valid() -> dict[str, object]:
    if not (GENERATED_DIR / "rp5d_run_receipt.report.json").is_file():
        run_layer(offline=True)
    return run_validation("pytest")


def rows(name: str) -> list[dict[str, object]]:
    assert_rp5d_valid()
    return read_jsonl(GENERATED_DIR / name)


def report(name: str) -> dict[str, object]:
    assert_rp5d_valid()
    return read_json(GENERATED_DIR / name)
