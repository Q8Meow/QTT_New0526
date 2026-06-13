from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_result_distribution_has_lcb_and_stress():
    row = assert_report_rows("PR166_S2_ResultDistLedger.report.json", 3215)[0]
    assert "lower_confidence_bound_net_edge" in row
    assert row["stressed_net_edge"] <= row["base_net_edge"] + 1e-9
