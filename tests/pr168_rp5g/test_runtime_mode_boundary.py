from ._helpers import assert_rows_have_contract


def test_runtime_modes_forbid_order_authority() -> None:
    rows = assert_rows_have_contract("mode_bound.jsonl")
    assert any(row["order_automation_readiness_handoff_created_flag"] for row in rows)
    assert all(row["buy_sell_open_close_logic_created_flag"] is False for row in rows)

