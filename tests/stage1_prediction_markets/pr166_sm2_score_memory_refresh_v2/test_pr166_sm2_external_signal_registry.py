from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_external_signals_are_candidate_provisional():
    rows = assert_report_rows("PR166_SM2_ExternalSignals.report.json", 10)
    receipts = assert_report_rows("PR166_SM2_SearchReceipt.report.json", 10)
    assert all(not row["source_truth_accepted"] for row in rows)
    assert all(row["candidate_signal_not_source_truth"] for row in receipts)
