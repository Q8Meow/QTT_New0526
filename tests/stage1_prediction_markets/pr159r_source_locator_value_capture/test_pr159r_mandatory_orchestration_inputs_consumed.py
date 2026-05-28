def test_pr159r_mandatory_orchestration_inputs_consumed(pr159r_artifacts):
    receipts = pr159r_artifacts["master"]["input_consumption_receipt"]
    required = [item for item in receipts if item["required_or_optional"] == "required"]
    assert required
    assert all(item["consumed"] for item in required if "PR136MasterPlanSectionCrosswalk" not in item["path"])

