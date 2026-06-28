from ._helpers import assert_rows_have_contract


def test_orderbook_imbalance_and_liquidity_decay_surfaces_exist() -> None:
    imbalance = assert_rows_have_contract("orderbook_imbalance.jsonl")
    decay = assert_rows_have_contract("liquidity_decay.jsonl")

    assert all(row["future_metric_enabled"] == "orderbook_imbalance_metric" for row in imbalance)
    assert all(row["orderbook_imbalance_hint"] == "SOURCE_REQUIRED" for row in imbalance)
    assert all(row["liquidity_decay_hint"] == "SOURCE_REQUIRED" for row in decay)
    assert all(row["depth_evaporation_input"] == "SOURCE_REQUIRED" for row in decay)
