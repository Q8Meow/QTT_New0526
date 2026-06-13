from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_connector_routing_is_reference_only():
    rows = assert_report_rows("PR166_SM2_ConnectorRouting.report.json", 3215)
    assert all(row["connector_reference_route_only"] for row in rows[:100])
    assert all(not row["connector_binding_allowed_in_this_pr"] for row in rows[:100])
