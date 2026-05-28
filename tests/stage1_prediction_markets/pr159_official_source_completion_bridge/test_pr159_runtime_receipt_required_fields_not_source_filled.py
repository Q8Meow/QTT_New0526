from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_runtime_receipt_required_fields_not_source_filled():
    assert master_report()["runtime_private_receipt_required_count"] == 0
    assert master_report()["no_authority_confirmation"]["runtime_cash_receipt_created"] is False

