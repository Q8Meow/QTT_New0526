from .test_support import AUTHORITY_FALSE_FIELDS, read_json, read_jsonl


def test_no_live_submit_and_authority_rows_have_no_runtime_authority() -> None:
    for name in ("no_live_submit.jsonl", "no_connector_write.jsonl", "no_private_state.jsonl", "no_cash_read.jsonl", "no_order_submit.jsonl", "auth_block.jsonl"):
        for row in read_jsonl(name):
            for field in AUTHORITY_FALSE_FIELDS:
                assert row.get(field) is False


def test_authority_boundary_report_blocks_runtime_surfaces() -> None:
    report = read_json("authority_boundary.report.json")
    assert report["authority_boundary_pass_flag"] is True
    assert report["paper_submit_authority_created_flag"] is False
    assert report["live_authority_created_flag"] is False
    assert report["owner_dashboard_runtime_created_flag"] is False
    assert report["telegram_bot_runtime_created_flag"] is False
