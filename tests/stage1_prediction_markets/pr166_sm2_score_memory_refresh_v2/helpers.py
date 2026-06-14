from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2 import constants as c
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2.io import read_json, records_from_report_payload

REPO_ROOT = Path(__file__).resolve().parents[3]


@lru_cache(maxsize=None)
def payload(filename: str) -> dict:
    return read_json(REPO_ROOT / c.GENERATED_DIR / filename)


@lru_cache(maxsize=None)
def records(filename: str) -> tuple[dict, ...]:
    return tuple(records_from_report_payload(REPO_ROOT, payload(filename)))


def summary() -> dict:
    return records("PR166_SM2_FinalSummary.report.json")[0]


def assert_report_rows(filename: str, expected: int | None = None) -> tuple[dict, ...]:
    path = REPO_ROOT / c.GENERATED_DIR / filename
    assert path.exists(), filename
    rows = records(filename)
    assert payload(filename)["record_count"] == len(rows)
    if expected is not None:
        assert len(rows) == expected
    return rows


def assert_summary_count(field: str, filename: str) -> None:
    assert summary()[field] == len(records(filename))
