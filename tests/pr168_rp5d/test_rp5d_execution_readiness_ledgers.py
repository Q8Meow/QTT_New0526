from __future__ import annotations

from src.qtt.stage1_prediction_markets.pr168_rp5d_executability.models import READINESS_FILES

from ._helpers import report, rows


def test_execution_readiness_ledgers_exist_without_decisions() -> None:
    total = 0
    for filename in READINESS_FILES.values():
        ledger = rows(filename)
        total += len(ledger)
        assert ledger
        assert all(row["no_live_authority_created_flag"] is True for row in ledger)
        assert all(row["future_consumer_pr_refs"] for row in ledger)

    run = report("rp5d_run_receipt.report.json")
    assert total == run["execution_readiness_row_count"]
    assert run["ranking_count"] == 0
    assert run["champion_selection_count"] == 0
