from tests.pr168_rp5a._helpers import load_report


def test_no_formula_reclaim() -> None:
    report = load_report("PR168_RP5A_FinalSummary.report.json")
    assert report["formula_reclaim_count"] == 0
    assert report["active_registry_authority_created_count"] == 0
