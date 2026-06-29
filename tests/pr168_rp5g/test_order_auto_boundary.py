from ._helpers import assert_rows_have_contract


def test_order_auto_path_is_non_authority() -> None:
    rows = assert_rows_have_contract("order_auto_path.jsonl")
    assert all(row["order_submit_ready_flag"] is False for row in rows)
    assert all(row["live_authority_created_flag"] is False for row in rows)

