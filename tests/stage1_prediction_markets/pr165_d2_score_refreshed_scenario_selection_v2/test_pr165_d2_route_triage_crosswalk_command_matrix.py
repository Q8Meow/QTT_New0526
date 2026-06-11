from __future__ import annotations


def test_route_triage_crosswalk_and_command_matrix_exist(pr165_d2_records):
    assert pr165_d2_records["PR165_D2_RouteTriageMatrix.report.json"]
    assert len(pr165_d2_records["PR165_D2_MasterPlanSectionCrosswalk.report.json"]) >= 40
    commands = pr165_d2_records["PR165_D2_CommandActionMatrix.report.json"]
    assert any(row["agent_id"] == "commander_agent" for row in commands)
