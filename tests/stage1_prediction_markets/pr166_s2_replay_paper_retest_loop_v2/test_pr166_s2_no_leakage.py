from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_no_leakage_audit_is_point_in_time():
    rows = assert_report_rows("PR166_S2_NoLeakageAudit.report.json", 3215)
    assert all(row["no_lookahead_flag"] is True for row in rows[:200])
    assert all(row["post_settlement_feature_leakage_flag"] is False for row in rows[:200])
