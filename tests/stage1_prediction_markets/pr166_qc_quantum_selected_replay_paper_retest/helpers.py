from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest import constants as c
from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest.authority import (
    FORBIDDEN_AUTHORITY_FLAGS,
    ZERO_AUTHORITY_KEYS,
)
from src.qtt.stage1_prediction_markets.pr166_qc_quantum_selected_replay_paper_retest.io import (
    read_json,
    records_from_report_payload,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


@lru_cache(maxsize=None)
def payload(filename: str) -> dict:
    return read_json(REPO_ROOT / c.GENERATED_DIR / filename)


@lru_cache(maxsize=None)
def records(filename: str) -> tuple[dict, ...]:
    return tuple(records_from_report_payload(REPO_ROOT, payload(filename)))


def summary() -> dict:
    return records("PR166_QC_FinalSummary.report.json")[0]


def assert_report_rows(filename: str, expected: int | None = None) -> tuple[dict, ...]:
    path = REPO_ROOT / c.GENERATED_DIR / filename
    assert path.exists(), filename
    rows = records(filename)
    assert payload(filename)["record_count"] == len(rows)
    if expected is not None:
        assert len(rows) == expected
    return rows


def assert_zero_authority(filename: str) -> None:
    report = payload(filename)
    for key in ZERO_AUTHORITY_KEYS:
        assert report.get(key, 0) == 0, (filename, key, report.get(key))
    for row in records(filename)[:25]:
        for key in ZERO_AUTHORITY_KEYS:
            assert row.get(key, 0) == 0, (filename, row["row_id"], key, row.get(key))
        for flag in FORBIDDEN_AUTHORITY_FLAGS:
            assert row.get(flag) is False, (filename, row["row_id"], flag, row.get(flag))


def assert_report_contract(filename: str, expected: int | None = None) -> tuple[dict, ...]:
    rows = assert_report_rows(filename, expected)
    assert payload(filename)["roadmap_pr_id"] == "PR166-QC"
    assert payload(filename)["created_by_pr"] == "PR166-QC"
    assert payload(filename)["schema_ref"]
    assert_zero_authority(filename)
    return rows
