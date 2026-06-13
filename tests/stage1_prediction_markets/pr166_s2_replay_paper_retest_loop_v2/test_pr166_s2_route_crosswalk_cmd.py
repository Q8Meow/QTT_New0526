from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_s2_route_crosswalk_and_command_matrix_are_connected():
    assert_report_rows("PR166_S2_RouteTriageMatrix.report.json")
    assert_report_rows("PR166_S2_MasterPlanCrosswalk.report.json")
    commands = assert_report_rows("PR166_S2_CommandActionMatrix.report.json")
    assert any(row["owning_agent"] == "commander_agent" for row in commands)
