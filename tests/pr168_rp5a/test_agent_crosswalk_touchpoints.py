from tests.pr168_rp5a._helpers import load_report


def test_agent_crosswalk_touchpoints() -> None:
    report = load_report("PR168_RP5A_NoOrphanAuditTouchpoints.report.json")
    assert report["documented_equivalent_crosswalk_present"] is True
    assert report["missing_crosswalk_report_required"] is False
