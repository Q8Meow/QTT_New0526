from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import master_report


def test_pr158_mandatory_orchestration_inputs_consumed():
    receipts = master_report()["input_consumption_receipt"]
    required = [item for item in receipts if item["required_or_optional"] == "required"]
    assert required
    fallback_consumed = any(item["fallback_used"] and item["consumed"] for item in required)
    not_consumed = [
        item
        for item in required
        if not item["consumed"] and "PR136MasterPlanSectionCrosswalk" not in item["path"]
    ]
    assert fallback_consumed
    assert not not_consumed
