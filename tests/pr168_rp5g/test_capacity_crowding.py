from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.capacity_crowding import capacity_crowding_summary


def test_capacity_crowding_summary() -> None:
    row = capacity_crowding_summary(10, "LOW", "LOW")
    assert float(row["capacity_crowding_penalty_cash"]) > 0

