from .test_support import all_rows, assert_no_authority, read_json


def test_every_row_and_authority_report_blocks_profit_and_execution_authority() -> None:
    for row in all_rows():
        assert_no_authority(row)
    report = read_json("authority_boundary.report.json")
    assert report["paper_submit_authority_created_flag"] is False
    assert report["live_authority_created_flag"] is False
    assert report["connector_write_created_flag"] is False
    assert report["private_state_read_created_flag"] is False
    assert report["cash_account_read_created_flag"] is False
    assert report["profit_guarantee_flag"] is False
