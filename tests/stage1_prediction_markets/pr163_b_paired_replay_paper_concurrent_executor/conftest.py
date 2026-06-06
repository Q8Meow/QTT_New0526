from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.pr163_b_paired_replay_paper_concurrent_executor import paths as p
from src.qtt.stage1_prediction_markets.pr163_b_paired_replay_paper_concurrent_executor.json_io import read_json
from src.qtt.stage1_prediction_markets.pr163_b_paired_replay_paper_concurrent_executor.report_sharding import load_report_records


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def report(repo_root):
    def _load(filename: str):
        return read_json(repo_root / p.GENERATED_DIR / filename)

    return _load


@pytest.fixture(scope="session")
def records(repo_root, report):
    def _records(filename: str):
        return load_report_records(repo_root, report(filename))

    return _records


@pytest.fixture(scope="session")
def summary(records):
    return records("PR163_B_FinalSummary.report.json")[0]
