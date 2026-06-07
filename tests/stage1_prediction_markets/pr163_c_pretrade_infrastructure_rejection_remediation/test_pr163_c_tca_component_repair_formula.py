from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.repair_formula_library import expected_net_profit_candidate
from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_tca_component_repair_formula():
    for row in load_records("PR163_C_TCAComponentRepairRegistry.report.json")[:20]:
        actual = expected_net_profit_candidate(
            row["gross_edge_candidate"],
            row["exchange_fee_component"],
            row["spread_cross_component"],
            row["slippage_component"],
            row["latency_adverse_selection_component"],
            row["queue_nonfill_opportunity_cost_component"],
            row["cancel_replace_component"],
            row["capital_lock_component"],
            row["settlement_delay_component"],
            row["stale_data_penalty_component"],
            row["operational_error_component"],
        )
        assert actual == row["expected_net_profit_candidate"]
        assert row["not_profit_evidence_flag"] is True
