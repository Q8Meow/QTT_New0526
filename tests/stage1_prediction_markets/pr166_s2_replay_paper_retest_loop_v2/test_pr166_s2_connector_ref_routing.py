from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_connector_routes_are_reference_only():
    rows = assert_report_rows("PR166_S2_ConnectorRefRouting.report.json", 3215)
    assert all(row["connector_binding_allowed_in_this_pr"] is False for row in rows[:200])
    assert all(row["future_connector_pr_refs"] for row in rows[:200])
