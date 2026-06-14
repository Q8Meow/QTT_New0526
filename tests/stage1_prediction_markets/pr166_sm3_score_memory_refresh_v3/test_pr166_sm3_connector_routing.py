from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_connector_routing_report_contract():
    rows = assert_report_contract("PR166_SM3_ConnectorRouting.report.json", 9)
    assert rows
