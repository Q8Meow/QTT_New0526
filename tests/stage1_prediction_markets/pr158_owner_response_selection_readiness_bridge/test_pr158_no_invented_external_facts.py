from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import master_report, owner_response


def test_pr158_no_invented_external_facts():
    assert master_report()["invented_external_fact_count"] == 0
    assert all(item["claims_external_fact"] is False for item in owner_response()["response_items"])

