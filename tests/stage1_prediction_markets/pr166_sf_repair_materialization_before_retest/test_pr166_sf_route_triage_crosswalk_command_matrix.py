from .conftest import assert_rows


def test_pr166_sf_route_triage_crosswalk_and_command_matrix(pr166_sf_records):
    routes = assert_rows(pr166_sf_records, "PR166_SF_RouteTriageMatrix.report.json")
    crosswalk = assert_rows(pr166_sf_records, "PR166_SF_MasterPlanSectionCrosswalk.report.json")
    commands = assert_rows(pr166_sf_records, "PR166_SF_CommandActionMatrix.report.json")
    assert any(row["route"] == "PR166-S2" for row in routes)
    assert len(crosswalk) == 58
    assert any(row["command"] == "BUILD_REPAIRED_RETEST_QUEUE" for row in commands)
