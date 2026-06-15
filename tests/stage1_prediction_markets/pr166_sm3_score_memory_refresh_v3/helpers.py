from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from src.qtt.stage1_prediction_markets.pr166_sm3_score_memory_refresh_v3 import constants as c
from src.qtt.stage1_prediction_markets.pr166_sm3_score_memory_refresh_v3.authority import ZERO_AUTHORITY_KEYS
from src.qtt.stage1_prediction_markets.pr166_sm3_score_memory_refresh_v3.io import read_json, records_from_report_payload

REPO_ROOT = Path(__file__).resolve().parents[3]


@lru_cache(maxsize=None)
def payload(filename: str) -> dict:
    return read_json(REPO_ROOT / c.GENERATED_DIR / filename)


@lru_cache(maxsize=None)
def records(filename: str) -> tuple[dict, ...]:
    return tuple(records_from_report_payload(REPO_ROOT, payload(filename)))


def summary() -> dict:
    return records("PR166_SM3_FinalSummary.report.json")[0]


def assert_report_rows(filename: str, expected: int | None = None) -> tuple[dict, ...]:
    path = REPO_ROOT / c.GENERATED_DIR / filename
    assert path.exists(), filename
    rows = records(filename)
    assert payload(filename)["record_count"] == len(rows)
    if expected is not None:
        assert len(rows) == expected
    return rows


def assert_summary_count(field: str, filename: str) -> tuple[dict, ...]:
    rows = assert_report_rows(filename)
    assert summary()[field] == len(rows)
    return rows


def assert_zero_authority(filename: str) -> None:
    report = payload(filename)
    for key in ZERO_AUTHORITY_KEYS:
        assert report.get(key, 0) == 0, (filename, key, report.get(key))
    for row in records(filename)[:25]:
        assert row.get("profit_evidence_allowed_in_this_pr") is False
        assert row.get("live_order_authority_allowed_in_this_pr") is False
        assert row.get("connector_binding_allowed_in_this_pr") is False
        assert row.get("quantum_backend_execution_allowed_in_this_pr") is False


def assert_report_contract(filename: str, expected: int | None = None) -> tuple[dict, ...]:
    rows = assert_report_rows(filename, expected)
    assert payload(filename)["roadmap_pr_id"] == "PR166-SM3"
    assert payload(filename)["created_by_pr"] == "PR166-SM3"
    assert payload(filename)["schema_ref"]
    assert_zero_authority(filename)
    return rows
