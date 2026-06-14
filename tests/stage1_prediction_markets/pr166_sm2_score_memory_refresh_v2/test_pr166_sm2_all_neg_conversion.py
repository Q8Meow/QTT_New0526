from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_sm2_all_negative_conversion_covers_3213_rows():
    rows = assert_report_rows("PR166_SM2_AllNegConvPlan.report.json", 3213)
    assert summary()["non_terminal_negative_conversion_candidate_rows"] == 3213
    assert all(row["conversion_candidate_label"] == "positive_conversion_candidate" for row in rows[:100])
