from src.qtt.stage1_prediction_markets.pr162r_b_replay_paper_data_binding_completion import feature_calculators as fc
import math


def test_feature_calculators(records):
    assert fc.midprice(0.4, 0.5) == 0.45
    assert math.isclose(fc.spread(0.4, 0.5), 0.1)
    assert fc.simple_fill_probability(5, 10) == 0.5
    rows = records("PR162R_B_FeatureCalculatorBindingRegistry.report.json")
    assert len(rows) >= 20
