from __future__ import annotations

from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.pr162r_a_replay_paper_executability_classification_audit import constants as c
from src.qtt.stage1_prediction_markets.pr162r_a_replay_paper_executability_classification_audit.json_io import records_from_payload
from src.qtt.stage1_prediction_markets.pr162r_a_replay_paper_executability_classification_audit.report_builder import build_payloads


REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def payloads():
    return build_payloads(REPO_ROOT, c.EXPECTED_BRANCH)


@pytest.fixture(scope="session")
def summary(payloads):
    return payloads["PR162R_A_FinalSummary.report.json"]


@pytest.fixture(scope="session")
def records(payloads):
    def _records(filename: str):
        return records_from_payload(payloads[filename])

    return _records
