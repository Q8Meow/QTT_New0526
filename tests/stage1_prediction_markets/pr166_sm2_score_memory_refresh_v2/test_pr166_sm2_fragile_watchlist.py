from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_fragile_watchlist_has_routes():
    rows = assert_report_rows("PR166_SM2_FragileWatchlist.report.json", 27)
    assert all(row["watchlist_route"] == "DASHBOARD_GOVERNANCE_COMMANDER_REVIEW" for row in rows)
