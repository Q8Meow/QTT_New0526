from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_edge_attribution_explains_edge_components():
    rows = assert_report_rows("PR166_S2_EdgeAttributionLedger.report.json", 3215)
    assert all(row["edge_capture_explanation"] for row in rows[:100])
    assert all(row["component_creating_or_destroying_edge"] for row in rows[:100])
