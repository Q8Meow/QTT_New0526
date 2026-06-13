from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_alternative_execution_paths_are_nonlive():
    row = assert_report_rows("PR166_S2_AltExecPathLedger.report.json", 3215)[0]
    assert len(row["alternative_execution_paths"]) >= 5
    assert row["live_order_authority_allowed"] is False
