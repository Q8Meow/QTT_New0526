from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_marginal_utility_records_information_gain():
    rows = assert_report_rows("PR166_S2_MarginalUtilityLedger.report.json", 3215)
    assert all(0 <= row["marginal_utility_score"] <= 1 for row in rows[:200])
    assert all(row["expected_information_gain"] >= 0 for row in rows[:200])
