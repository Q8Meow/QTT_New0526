from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_portfolio_exposure_repair_no_runtime_cash_claim():
    for row in load_records("PR163_C_PortfolioExposureLedgerRepairRegistry.report.json"):
        assert row["no_runtime_cash_receipt_flag"] is True
        assert row["replay_paper_cash_only_flag"] is True
