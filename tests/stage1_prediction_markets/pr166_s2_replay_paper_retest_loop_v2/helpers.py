from __future__ import annotations

import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.pr166_s2_replay_paper_retest_loop_v2 import constants as c

REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED = REPO_ROOT / "docs" / "master_plan" / "generated"


def payload(filename: str) -> dict:
    return json.loads((GENERATED / filename).read_text(encoding="utf-8"))


def records(filename: str) -> list[dict]:
    data = payload(filename)
    rows = list(data.get("records") or [])
    for shard in data.get("shard_files") or []:
        rows.extend(json.loads((REPO_ROOT / shard).read_text(encoding="utf-8")).get("records") or [])
    return rows


def summary() -> dict:
    return records("PR166_S2_FinalSummary.report.json")[0]


def assert_report_rows(filename: str, expected: int | None = None) -> list[dict]:
    data = payload(filename)
    rows = records(filename)
    assert data["roadmap_pr_id"] == c.PR_ID
    assert data["schema_ref"] == c.REPORT_SCHEMA_REFS[filename]
    assert data["record_count"] == len(rows)
    assert rows
    if expected is not None:
        assert len(rows) == expected
    return rows


def first_row(filename: str) -> dict:
    return assert_report_rows(filename)[0]


def assert_common_replay_row(row: dict) -> None:
    assert row["created_by_pr"] == c.PR_ID
    assert row["roadmap_pr_id"] == c.PR_ID
    assert row["simulated_order_authority"] == "NONLIVE_REPLAY_PAPER_ONLY"
    assert row["no_orphan_status"] == "CONNECTED_UPSTREAM_AND_DOWNSTREAM"
    assert row["connector_binding_allowed_in_this_pr"] is False
    assert row["private_state_fetch_allowed_in_this_pr"] is False
    assert row["runtime_cash_receipt_allowed_in_this_pr"] is False
    assert row["source_truth_acceptance_allowed_in_this_pr"] is False
    assert row["profit_evidence_count"] == 0
    assert row["quantum_backend_execution_count"] == 0
    assert row["quantum_advantage_claim_count"] == 0
