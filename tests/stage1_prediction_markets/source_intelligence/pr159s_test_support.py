from __future__ import annotations

from pathlib import Path

from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake.io import read_json


ROOT = Path(__file__).resolve().parents[3]


def load(rel_path: Path):
    return read_json(ROOT / rel_path)


def records(rel_path: Path):
    return load(rel_path)["records"]


def summary():
    return load(c.TERMINAL_COMPLETION_SUMMARY_PATH)


def count_receipt():
    return summary()["count_invariant_receipt"]

