from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_marginal_utility_rows_have_information_gain():
    rows = assert_report_rows("PR166_SM2_MarginalUtility.report.json", 3215)
    assert all(row["expected_information_gain_score"] >= 0 for row in rows[:100])
