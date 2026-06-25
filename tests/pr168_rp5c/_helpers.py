from __future__ import annotations

from functools import lru_cache
import json

from tools.pr168_rp5c_config import HARD_ZERO_COUNTERS, REPORT_NAMES, ROW_SHARDS, report_path, shard_path
from tools.pr168_rp5c_validator import run_validation


@lru_cache(maxsize=None)
def load_report(name: str) -> dict:
    return json.loads(report_path(name).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_rows(key: str) -> list[dict]:
    path = shard_path(key)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def final_summary() -> dict:
    return load_report("PR168_RP5C_FinalSummary.report.json")


def assert_rp5c_valid() -> None:
    assert run_validation()["validation"] == "PR168_RP5C_IMMUTABLE_QKU_FORMULA_LIBRARY_OK"


def assert_hard_zero_report(report: dict) -> None:
    for field, expected in HARD_ZERO_COUNTERS.items():
        assert report.get(field) == expected


__all__ = [
    "HARD_ZERO_COUNTERS",
    "REPORT_NAMES",
    "ROW_SHARDS",
    "assert_hard_zero_report",
    "assert_rp5c_valid",
    "final_summary",
    "load_report",
    "load_rows",
]
