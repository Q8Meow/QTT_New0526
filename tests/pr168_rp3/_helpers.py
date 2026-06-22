from __future__ import annotations

from functools import lru_cache
from typing import Any

from tools.pr168_rp3_validator import run_validation


@lru_cache(maxsize=1)
def _cached_validation() -> dict[str, Any]:
    return run_validation()


def assert_rp3_valid() -> None:
    result = _cached_validation()
    assert result["status"] == "passed"
