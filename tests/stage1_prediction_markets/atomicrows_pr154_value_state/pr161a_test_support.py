from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.atomicrows_pr154_value_state.pr161a_materialization_bridge import constants as c

REPO_ROOT = Path(__file__).resolve().parents[3]


@lru_cache(maxsize=None)
def report(name: str) -> dict:
    return json.loads((REPO_ROOT / c.REPORT_PATHS[name]).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def summary() -> dict:
    return report("final_summary")["records"][0]


def records(name: str) -> list[dict]:
    return report(name)["records"]

