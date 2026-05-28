from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report


def test_pr160_pr157_pr158_pr159_artifacts_consumed():
    receipts = {item["path"]: item for item in master_report()["input_consumption_receipt"]}
    for path in (
        c.PR157_PR154_REGISTRY_PATH,
        c.PR158_SPLIT_REGISTRY_PATH,
        c.PR159_ACCEPTED_PACKET_REGISTRY_PATH,
        c.PR159_UNRESOLVED_FILL_PATH_PATH,
    ):
        assert receipts[path.as_posix()]["consumed"] is True
