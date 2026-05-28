from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report


def test_pr160_mandatory_orchestration_inputs_consumed():
    receipts = {item["path"]: item for item in master_report()["input_consumption_receipt"]}
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            assert receipts[path.as_posix()]["consumed"] or receipts[c.CROSSWALK_FALLBACK_PATH.as_posix()]["consumed"]
        else:
            assert receipts[path.as_posix()]["consumed"] is True
