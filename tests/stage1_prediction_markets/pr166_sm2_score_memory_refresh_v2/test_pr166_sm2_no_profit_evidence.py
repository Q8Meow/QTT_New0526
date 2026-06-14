from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_no_profit_evidence_audit():
    row = assert_report_rows("PR166_SM2_NoProfitAudit.report.json", 1)[0]
    assert row["true_positive_replay_paper_rows_from_PR166_S2"] == 2
    assert row["profit_evidence_count"] == 0
    assert row["positive_without_future_retest_count"] == 0
