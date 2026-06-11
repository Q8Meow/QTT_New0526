from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results.normalization import (
    round6,
)


def test_pr166_sm_scores_use_execution_adjusted_net_edge_not_gross_only(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_RefreshedScoreRegistry.report.json"]
    for row in rows[:200]:
        expected = round6(
            row["gross_edge"]
            - row["spread_cost"]
            - row["maker_taker_fees"]
            - row["slippage_cost"]
            - row["market_impact_cost"]
            - row["latency_drag"]
            - row["liquidity_drag"]
            - row["adverse_selection_drag"]
            - row["settlement_payoff_adjustment"]
        )
        assert row["net_edge_after_costs"] == expected
        assert row["gross_edge_only_score_flag"] is False
        assert row["net_edge_formula_ref"] == "PR166_SM_FORMULA::NET_EDGE_AFTER_COSTS"
