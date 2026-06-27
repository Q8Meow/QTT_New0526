from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from typing import Any

from src.qtt.stage1_prediction_markets.pr168_vs1_trading_intelligence.models import (
    GENERATED_DIR,
    read_json,
    read_jsonl,
)
from src.qtt.stage1_prediction_markets.pr168_vs1_trading_intelligence.validator import (
    run_validation,
)


@lru_cache(maxsize=1)
def assert_vs1_valid() -> dict[str, Any]:
    return run_validation("pytest")


def rows(filename: str) -> list[dict[str, Any]]:
    assert_vs1_valid()
    return read_jsonl(GENERATED_DIR / filename)


def report(filename: str) -> dict[str, Any]:
    assert_vs1_valid()
    return read_json(GENERATED_DIR / filename)


def d(value: object) -> Decimal:
    return Decimal(str(value))
