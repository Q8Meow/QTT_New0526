from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_venue_normalization_and_order_intent_repairs():
    assert all(row["venue_candidate_not_truth_flag"] is True for row in load_records("PR163_C_VenueNormalizationRepairRegistry.report.json"))
    assert all(row["pretrade_check_pass_after_repair"] is True for row in load_records("PR163_C_OrderIntentRepairRegistry.report.json"))
