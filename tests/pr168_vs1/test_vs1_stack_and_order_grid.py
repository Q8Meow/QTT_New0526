from __future__ import annotations

from ._helpers import rows


def test_vs1_order_grid_links_to_variable_search_and_feasible_candidates():
    searches = {row["variable_search_ref"] for row in rows("trade_plan_variable_search_receipts.jsonl")}
    orders = rows("order_variable_candidate_receipts.jsonl")

    assert orders
    assert all(row["variable_search_ref"] in searches for row in orders)
    assert all(row["ex_ante_candidate_flag"] is True for row in orders)
    assert all(row["feasible_price_flag"] is True for row in orders)
    assert all(row["feasible_fill_flag"] is True for row in orders)
