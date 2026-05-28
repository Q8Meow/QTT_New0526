from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import report


def test_pr160_agent_responsibility_update_no_orphans():
    records = report(c.AGENT_RESPONSIBILITY_UPDATE_PATH)["records"]
    assert len(records) == 33
    assert all(item["orphan_route_flag"] is False for item in records)
