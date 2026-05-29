from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.master_plan_residual_candidate_coverage import constants as c

REPO_ROOT = Path(__file__).resolve().parents[3]


@lru_cache(maxsize=None)
def report(name: str) -> dict:
    return json.loads((REPO_ROOT / c.REPORT_PATHS[name]).read_text(encoding="utf-8"))


def records(name: str) -> list[dict]:
    return report(name)["records"]


@lru_cache(maxsize=None)
def summary() -> dict:
    return records("final_summary")[0]


def candidate_records() -> list[dict]:
    return records("candidate_inventory")


def quantum_records() -> list[dict]:
    return records("quantum_optimizer")


def assert_no_runtime_authority(payload: dict) -> None:
    assert payload["optimizer_execution_count"] == 0
    assert payload["quantum_backend_execution_count"] == 0
    assert payload["quantum_simulator_execution_count"] == 0
    assert payload["quantum_advantage_claim_count"] == 0
    assert payload["profit_evidence_count"] == 0
    assert payload["replay_paper_execution_count"] == 0
    assert payload["runtime_live_order_profit_authority_count"] == 0
