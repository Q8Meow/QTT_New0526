from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_time_to_resolution_risk_rows():
    rows = assert_report_rows("PR166_SM2_TTRiskLedger.report.json", 3215)
    assert all(row["latency_budget_ms_candidate"] > 0 for row in rows[:100])
