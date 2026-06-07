from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_model_risk_repair_ledger():
    for row in load_records("PR163_C_ModelRiskRepairLedger.report.json"):
        assert row["model_owner_agent"]
        assert row["independent_review_agent"]
        assert row["assumptions"]
        assert row["limitations"]
        assert row["test_vector_refs"]
        assert row["no_live_authority_flag"] is True
        assert row["not_profit_evidence_flag"] is True
