from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_positive_preference_and_negative_avoidance_counts():
    assert_report_rows("PR166_SM2_PosPrefLedger.report.json", 2)
    avoid = assert_report_rows("PR166_SM2_NegAvoidLedger.report.json", 3213)
    assert all(not row["avoidance_is_global_ban"] for row in avoid[:100])
