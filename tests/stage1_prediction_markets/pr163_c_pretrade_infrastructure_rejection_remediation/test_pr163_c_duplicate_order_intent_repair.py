from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_duplicate_order_intent_repair():
    rows = load_records("PR163_C_DuplicateOrderIntentRepairRegistry.report.json")
    assert all(row["duplicate_intent_fingerprint"] for row in rows)
    assert all(row["pretrade_duplicate_check_pass_after_repair"] is True for row in rows)
