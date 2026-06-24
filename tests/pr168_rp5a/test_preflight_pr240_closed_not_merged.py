from tests.pr168_rp5a._helpers import load_report


def test_preflight_pr240_closed_not_merged() -> None:
    report = load_report("PR168_RP5A_Preflight.report.json")
    assert report["pr240_closed_not_merged_preflight_passed"] is True
    assert report["recovery1_branch_not_active"] is True
