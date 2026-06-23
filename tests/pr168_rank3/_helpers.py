from __future__ import annotations

from functools import lru_cache
from typing import Any

from tools.pr168_rank3_config import GENERATED_ROOT, ROW_SHARDS, shard_path
from tools.pr168_rank3_report_writer import read_json, read_jsonl
from tools.pr168_rank3_validator import run_validation


@lru_cache(maxsize=1)
def _cached_validation() -> dict[str, Any]:
    return run_validation()


def assert_rank3_valid() -> None:
    result = _cached_validation()
    assert result["status"] == "passed"


def rows(key: str) -> list[dict[str, Any]]:
    assert key in ROW_SHARDS
    return read_jsonl(shard_path(key))


def report(filename: str) -> dict[str, Any]:
    return read_json(GENERATED_ROOT / filename)
