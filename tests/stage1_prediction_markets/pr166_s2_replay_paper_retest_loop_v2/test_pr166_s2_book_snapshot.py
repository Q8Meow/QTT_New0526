from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_book_snapshots_have_top_of_book():
    row = assert_report_rows("PR166_S2_BookSnapshotLedger.report.json", 3215)[0]
    assert row["best_ask"] >= row["best_bid"]
    assert row["spread"] >= 0
