from __future__ import annotations

from functools import lru_cache

from tools.pr168_rp2_validator import run_validation


@lru_cache(maxsize=1)
def assert_rp2_valid() -> None:
    run_validation("all")
