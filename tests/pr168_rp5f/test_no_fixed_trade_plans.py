from ._helpers import all_jsonl_rows, read_json


def test_no_fixed_or_non_expiring_trade_plan_rows_exist() -> None:
    for name, row in all_jsonl_rows():
        assert row.get("fixed_trade_instruction_flag") is False, (name, row.get("row_id"))
        assert row.get("non_expiring_trade_plan_flag") is False, (name, row.get("row_id"))

    receipt = read_json("run_receipt.report.json")
    assert receipt["fixed_trade_plan_count"] == 0
    assert receipt["non_expiring_trade_plan_count"] == 0

