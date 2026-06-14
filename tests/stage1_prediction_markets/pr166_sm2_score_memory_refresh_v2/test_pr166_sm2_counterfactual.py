from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_counterfactual_rows_do_not_allow_false_positive_claims():
    rows = assert_report_rows("PR166_SM2_Counterfactual.report.json", 3213)
    assert all(not row["positive_without_retest_allowed"] for row in rows[:100])
