from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.pr163_generic_paper_adapter_capture_framework import paths as p
from src.qtt.stage1_prediction_markets.pr163_generic_paper_adapter_capture_framework.json_io import (
    read_json,
    records_from_payload,
)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def report(repo_root):
    def _load(filename: str):
        return read_json(repo_root / p.GENERATED_DIR / filename)

    return _load


@pytest.fixture(scope="session")
def records(report):
    def _records(filename: str):
        return records_from_payload(report(filename))

    return _records


@pytest.fixture(scope="session")
def summary(records):
    return records("PR163_FinalSummary.report.json")[0]
