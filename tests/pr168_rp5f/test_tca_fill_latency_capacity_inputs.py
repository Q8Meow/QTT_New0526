from ._helpers import assert_rows_have_contract


def test_tca_fill_latency_capacity_and_cashflow_inputs_exist() -> None:
    tca = assert_rows_have_contract("tca_inputs.jsonl")
    fill = assert_rows_have_contract("fill_inputs.jsonl")
    latency = assert_rows_have_contract("lat_inputs.jsonl")
    capacity = assert_rows_have_contract("capacity_inputs.jsonl")
    cash = assert_rows_have_contract("cash_settle_inputs.jsonl")

    assert all(row["fee_model"] == "SOURCE_REQUIRED" for row in tca)
    assert all(row["spread_model"] == "SOURCE_REQUIRED" for row in tca)
    assert all(row["future_rp5g_fill_model_required_flag"] for row in fill)
    assert all(row["latency_budget_ms"] for row in latency)
    assert all(row["capacity_fit"] == "SOURCE_REQUIRED" for row in capacity)
    assert all(row["crowding_risk"] == "SOURCE_REQUIRED" for row in capacity)
    assert all(row["cashflow_semantics"] == "SOURCE_REQUIRED" for row in cash)
    assert all(row["settlement_semantics"] == "SOURCE_REQUIRED" for row in cash)
