from tests.pr168_rp5a._helpers import load_report


def test_no_global_ban_authority() -> None:
    report = load_report("PR168_RP5A_FinalSummary.report.json")
    assert report["global_formula_qku_ban_authority_created_count"] == 0
    assert report["source_truth_authority_created_count"] == 0
