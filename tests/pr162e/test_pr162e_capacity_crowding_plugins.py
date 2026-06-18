from tests.pr162e.helpers import plugin_rows


def test_capacity_crowding_fields_are_materialized():
    row = plugin_rows()[0]
    capacity = row["capacity_crowding"]
    assert "max_candidate_order_size" in capacity
    assert "crowding_penalty" in capacity
