from __future__ import annotations


def test_tca_prompt_formula_holds(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_TCADecompositionSelectionLedger.report.json"]
    for row in rows[:100]:
        expected = round(
            row["gross_edge"]
            - row["fee_cost_component"]
            - row["spread_cost_component"]
            - row["slippage_cost_component"]
            - row["market_impact_cost_component"]
            - row["latency_cost_component"]
            - row["liquidity_cost_component"]
            - row["settlement_cost_component"],
            6,
        )
        assert abs(expected - row["net_edge_after_costs"]) < 0.00001
