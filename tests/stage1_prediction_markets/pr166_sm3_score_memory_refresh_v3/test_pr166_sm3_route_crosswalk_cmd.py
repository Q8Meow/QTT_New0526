from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_route_crosswalk_and_command_matrix_reports():
    assert_report_contract("PR166_SM3_PlanCrosswalk.report.json", 109)
    assert_report_contract("PR166_SM3_CmdActionMatrix.report.json", 109)
    assert_report_contract("PR166_SM3_RouteTriageMatrix.report.json", 109)
