from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_liquidity_spread_depth_fill_probability_repairs():
    for row in load_records("PR163_C_LiquiditySpreadDepthRepairRegistry.report.json"):
        assert row["best_bid_candidate"] <= row["mid_candidate"] <= row["best_ask_candidate"]
        assert row["spread_bps"] >= 0
        assert 0.05 <= row["fill_probability_candidate"] <= 0.99
