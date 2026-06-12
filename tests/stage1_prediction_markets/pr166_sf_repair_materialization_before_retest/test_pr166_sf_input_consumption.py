from .conftest import assert_rows


def test_pr166_sf_consumes_sharded_inputs(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_InputConsumptionAudit.report.json")
    by_report = {row["expected_input_report"]: row for row in rows}
    assert by_report["PR165_D2_RepairAwareSelectionQueue.report.json"]["observed_row_count"] == 3985
    assert by_report["PR165_D2_RepairAwareSelectionQueue.report.json"]["input_consumption_mode"] == "ROOT_REPORT_PLUS_ALL_SHARDS"
    assert by_report["PR165_D2_ScoreComponentProvenanceLedger.report.json"]["observed_row_count"] == 91655
