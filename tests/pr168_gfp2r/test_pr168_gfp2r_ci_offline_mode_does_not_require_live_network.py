from tests.pr168_gfp2r._helpers import records


def test_pr168_gfp2r_ci_offline_mode_does_not_require_live_network() -> None:
    endpoint_report = records("PR168_GFP2R_EndpointAssumptionDriftHandoff")
    statuses = {row["verification_status"] for row in endpoint_report["rows"]}
    assert statuses == {"OFFLINE_NOT_VERIFIED"}
    assert all(row["endpoint_assumption_drift_flag"] is False for row in endpoint_report["rows"])
