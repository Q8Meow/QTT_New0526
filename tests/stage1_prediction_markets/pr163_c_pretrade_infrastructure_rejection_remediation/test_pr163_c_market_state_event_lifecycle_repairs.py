from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_market_state_event_lifecycle_repairs():
    assert all(row["market_open_candidate"] is True and row["no_lookahead_flag"] is True for row in load_records("PR163_C_MarketStateRepairRegistry.report.json"))
    assert all(row["replay_paper_lifecycle_eligible"] is True for row in load_records("PR163_C_EventLifecycleRepairRegistry.report.json"))
