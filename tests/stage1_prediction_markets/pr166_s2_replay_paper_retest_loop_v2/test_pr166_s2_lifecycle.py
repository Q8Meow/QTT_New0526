from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_lifecycle_assigns_every_primary_candidate():
    rows = assert_report_rows("PR166_S2_LifecycleLedger.report.json", 3215)
    assert all(row["candidate_lifecycle_status"] for row in rows)
    assert all(row["live_trading_authorization_created_flag"] is False for row in rows[:200])
