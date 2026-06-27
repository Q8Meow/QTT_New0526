from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr168_rp5d_executability.models import OPTIMIZER_FAMILIES

from ._helpers import report, rows


def test_optimizer_readiness_is_metadata_only_for_future_prs() -> None:
    ledger = rows("rp5d_optimizer_readiness.jsonl")
    run = report("rp5d_run_receipt.report.json")

    assert len(ledger) == run["optimizer_readiness_row_count"]
    assert all(row["candidate_optimizer_family"] == "OPTIMIZER_FAMILY_MENU" for row in ledger)
    assert all(set(row["candidate_optimizer_families"]) == set(OPTIMIZER_FAMILIES) for row in ledger)
    assert all(row["default_policy"].startswith("READINESS_METADATA_ONLY") for row in ledger)
    assert all(row["future_consumer_pr_refs"] for row in ledger)
