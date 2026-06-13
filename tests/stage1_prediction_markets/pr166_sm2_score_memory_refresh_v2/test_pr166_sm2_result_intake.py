from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_result_intake_covers_primary_universe():
    rows = assert_report_rows("PR166_SM2_ResultIntake.report.json", 3215)
    assert {row["result_intake_class"] for row in rows} == {"PR166_S2_REPLAY_PAPER_RESULT_CONSUMED_FOR_SCORE_MEMORY_REFRESH"}
