from decimal import Decimal
from src.qtt.stage1_prediction_markets.pr168_rp5g_trade_plan_sim.scenario_ladder import SCENARIO_FAMILIES, scenario_result


def test_scenario_ladder_has_required_cases() -> None:
    assert "combined_conservative_case" in SCENARIO_FAMILIES
    row = scenario_result(Decimal("1"), Decimal("0.5"), "fee_worse_case")
    assert row["scenario_pass_flag"] is True

