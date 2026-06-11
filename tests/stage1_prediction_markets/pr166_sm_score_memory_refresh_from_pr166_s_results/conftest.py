from __future__ import annotations

from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results import constants as c
from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results.io import (
    load_report_records,
)
from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results.report_writer import (
    build_payloads,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def pr166_sm_payloads() -> dict[str, dict]:
    return build_payloads(REPO_ROOT)


@pytest.fixture(scope="session")
def pr166_sm_records() -> dict[str, list[dict]]:
    return {filename: load_report_records(REPO_ROOT, filename) for filename in c.REPORT_FILENAMES}


@pytest.fixture(scope="session")
def pr166_sm_summary(pr166_sm_records: dict[str, list[dict]]) -> dict:
    return pr166_sm_records["PR166_SM_FinalSummary.report.json"][0]
