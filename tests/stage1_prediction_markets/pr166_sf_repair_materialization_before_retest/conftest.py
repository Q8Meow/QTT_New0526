from __future__ import annotations

from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.pr166_sf_repair_materialization_before_retest import constants as c
from src.qtt.stage1_prediction_markets.pr166_sf_repair_materialization_before_retest.io import load_report_records, read_json

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def pr166_sf_payloads() -> dict[str, dict]:
    return {filename: read_json(REPO_ROOT / c.GENERATED_DIR / filename) for filename in c.REPORT_FILENAMES}


@pytest.fixture(scope="session")
def pr166_sf_records() -> dict[str, list[dict]]:
    return {filename: load_report_records(REPO_ROOT, filename) for filename in c.REPORT_FILENAMES}


@pytest.fixture(scope="session")
def pr166_sf_summary(pr166_sf_records: dict[str, list[dict]]) -> dict:
    return pr166_sf_records["PR166_SF_FinalSummary.report.json"][0]


def assert_rows(records: dict[str, list[dict]], filename: str) -> list[dict]:
    rows = records[filename]
    assert rows, filename
    for row in rows[:25]:
        assert row["created_by_pr"] == "PR166-SF"
        assert row["roadmap_pr_id"] == "PR166-SF"
        assert row["validator_ref"] == c.VALIDATOR_REF
        assert row["manifest_ref"] == c.MANIFEST_REF
        assert row["schema_ref"] == c.REPORT_SCHEMA_REFS[filename]
        assert row["connector_binding_allowed_in_this_pr"] is False
        assert row["private_state_fetch_allowed_in_this_pr"] is False
        assert row["runtime_cash_receipt_allowed_in_this_pr"] is False
        assert row["source_truth_acceptance_allowed_in_this_pr"] is False
    return rows
