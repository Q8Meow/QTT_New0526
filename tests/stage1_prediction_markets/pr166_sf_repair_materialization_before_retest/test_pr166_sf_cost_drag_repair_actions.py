from .conftest import assert_rows


def test_pr166_sf_cost_drag_frontier_is_materialized(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_CostDragRepairLedger.report.json")
    for row in rows[:100]:
        assert row["repair_frontier"]
        assert row["best_repair_action"] == row["repair_frontier"][0]["repair_action"]
        assert row["cost_drag_repair_materialized_flag"] is True
