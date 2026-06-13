from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_expansion_policy_marks_candidates_only():
    rows = assert_report_rows("PR166_SM2_ExpansionPolicy.report.json", 5)
    assert all(row["expansion_rows_are_future_replay_paper_candidates"] for row in rows)
    assert all(not row["counts_as_positive_result"] for row in rows)
