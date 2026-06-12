from .conftest import assert_rows


def test_pr166_sf_capacity_crowding_controls_are_materialized(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_RepairCapacityControl.report.json")
    for row in rows[:100]:
        assert row["max_order_size_before_edge_decay"] >= row["min_order_size"]
        assert 0 <= row["expected_fill_probability"] <= 1
        assert 0 <= row["crowding_penalty_after_repair"] <= 1
