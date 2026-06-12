from src.qtt.stage1_prediction_markets.pr166_sf_repair_materialization_before_retest import constants as c
from .conftest import assert_rows


def test_pr166_sf_row_counts_reconcile(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_RowCountLedger.report.json")
    by_report = {row["artifact_ref"]: row for row in rows}
    for report, expected in c.EXPECTED_ROW_COUNTS.items():
        assert by_report[report]["observed_row_count"] == expected
        assert by_report[report]["row_count_delta"] == 0
        assert by_report[report]["rows_not_invented_flag"] is True
