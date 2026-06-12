from src.qtt.stage1_prediction_markets.pr166_sf_repair_materialization_before_retest.report_writer import round6
from .conftest import assert_rows


def test_pr166_sf_tca_reconstructs_post_repair_preview(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_TCATermLedger.report.json")
    for row in rows[:250]:
        expected = round6(row["pre_repair_gross_edge"] - row["repaired_fee_cost_component"] - row["repaired_spread_cost_component"] - row["repaired_slippage_cost_component"] - row["repaired_market_impact_cost_component"] - row["repaired_latency_cost_component"] - row["repaired_liquidity_cost_component"] - row["repaired_settlement_cost_component"])
        assert expected == row["post_repair_preview_net_edge_after_costs"]
        assert row["tca_reconstruction_passed_flag"] is True
