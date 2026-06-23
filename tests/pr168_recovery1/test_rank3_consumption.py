from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_rank3_consumption_counts_match_rank3_universe() -> None:
    assert_recovery1_valid()
    final = report("PR168_RECOVERY1_FinalSummary.report.json")["records"]
    assert final["rank3_repair_queue_rows_consumed"] == 35
    assert final["rank3_expression_repair_rows_consumed"] == 7
    assert final["rank3_source_provenance_rows_consumed"] == 5
