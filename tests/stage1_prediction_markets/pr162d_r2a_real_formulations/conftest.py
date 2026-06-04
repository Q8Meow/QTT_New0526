from __future__ import annotations

from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.json_io import records_from_payload
from src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.report_builder import build_payloads


REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def payloads():
    payload_map, _md = build_payloads(REPO_ROOT, "pr162d-r2a-real-computable-formulations-redo")
    return payload_map


@pytest.fixture(scope="session")
def records(payloads):
    def _records(filename: str):
        return records_from_payload(payloads[filename])

    return _records


@pytest.fixture(scope="session")
def summary(payloads):
    return payloads["PR162D_R2A_FinalSummary.report.json"]
