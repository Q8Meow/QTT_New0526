from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report


def test_pr159_mandatory_orchestration_inputs_consumed():
    receipts = {item["path"]: item for item in master_report()["input_consumption_receipt"]}
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            requested = receipts[path.as_posix()]
            fallback = receipts[c.CROSSWALK_FALLBACK_PATH.as_posix()]
            assert requested["consumed"] or fallback["consumed"]
        else:
            assert receipts[path.as_posix()]["consumed"] is True

