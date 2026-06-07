from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_future_live_fields_no_live_authority():
    rows = load_records("PR163_C_FutureLiveReadinessFieldPrep.report.json")
    assert summary()["future_live_authority_created_count"] == 0
    assert all(row["live_authority_created"] is False for row in rows)
    assert all(row["future_kill_switch_state_field_present"] for row in rows)
