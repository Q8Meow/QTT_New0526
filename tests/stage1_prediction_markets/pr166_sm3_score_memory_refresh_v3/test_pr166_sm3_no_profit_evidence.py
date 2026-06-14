from __future__ import annotations

from .helpers import assert_report_contract, summary


def test_pr166_sm3_replay_paper_positives_are_not_profit_evidence():
    assert_report_contract("PR166_SM3_NoProfitAudit.report.json", 1)
    s = summary()
    assert s["total_positive_evidence_rows"] == 150
    assert s["replay_paper_positive_rows_are_not_live_or_profit_evidence"] is True
    assert s["profit_evidence_count"] == 0
