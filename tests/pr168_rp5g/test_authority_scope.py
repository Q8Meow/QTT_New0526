from ._helpers import all_jsonl_rows, read_json


def test_all_generated_rows_have_no_order_or_live_authority() -> None:
    for filename, row in all_jsonl_rows():
        for field in ("order_authority_flag", "paper_submit_authority_flag", "live_authority_flag", "connector_write_flag", "private_state_fetch_flag", "cash_account_read_flag"):
            if field in row:
                assert row[field] is False, (filename, row["row_id"], field)
    run = read_json("run_receipt.report.json")
    assert run["order_authority_count"] == 0
    assert run["buy_sell_open_close_logic_count"] == 0

