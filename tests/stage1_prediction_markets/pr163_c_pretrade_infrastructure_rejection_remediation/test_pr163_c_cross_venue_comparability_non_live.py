from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records


def test_pr163_c_cross_venue_comparability_non_live():
    rows = load_records("PR163_C_CrossVenueComparabilityRepairRegistry.report.json")
    assert all(row["cross_venue_live_authority_flag"] is False for row in rows)
    assert all(row["normalized_event_key_candidate"] for row in rows)
