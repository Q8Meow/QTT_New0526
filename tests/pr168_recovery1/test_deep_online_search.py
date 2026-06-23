from tests.pr168_recovery1._helpers import assert_recovery1_valid, report


def test_deep_online_search_has_pass_ledger_or_no_trigger() -> None:
    assert_recovery1_valid()
    coverage = report("PR168_RECOVERY1_DeepOnlineSearchCoverage.report.json")["records"]
    assert coverage["deep_online_search_incomplete_flag"] is False
    assert coverage["source_rows_mapped_to_inputs_or_repairs_count"] >= 12
