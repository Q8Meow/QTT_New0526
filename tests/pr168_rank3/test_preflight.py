from tests.pr168_rank3._helpers import assert_rank3_valid, report


def test_pr238_preflight_recorded() -> None:
    assert_rank3_valid()
    final = report("PR168_RANK3_FinalSummary.report.json")["records"]
    assert final["pr238_merged_preflight_passed_flag"] is True
    assert final["rp3_top_level_report_count_observed"] == 106
