from __future__ import annotations

from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2 import constants as c
from src.qtt.stage1_prediction_markets.pr165_d2_score_refreshed_scenario_selection_v2.io import (
    load_report_records,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def pr165_d2_records() -> dict[str, list[dict]]:
    return {filename: load_report_records(REPO_ROOT, filename) for filename in c.REPORT_FILENAMES}


@pytest.fixture(scope="session")
def pr165_d2_summary(pr165_d2_records: dict[str, list[dict]]) -> dict:
    return pr165_d2_records["PR165_D2_FinalSummary.report.json"][0]
