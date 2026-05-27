from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import pr154_report


def test_pr157_mandatory_orchestration_inputs_consumed():
    paths = {
        item["path"]: item
        for item in pr154_report()["input_consumption_receipt"]
    }
    assert paths["docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"]["consumed"]
    assert paths["docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"]["consumed"]
    assert paths["docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json"]["fallback_used"]
