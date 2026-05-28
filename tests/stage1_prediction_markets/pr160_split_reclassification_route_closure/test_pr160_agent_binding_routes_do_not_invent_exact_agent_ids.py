from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report, records, report


def test_pr160_agent_binding_routes_do_not_invent_exact_agent_ids():
    assert report(c.PR163_AGENT_BINDING_ROUTE_PATH)["record_count"] == 0
    assert master_report()["invented_exact_agent_id_count"] == 0
    assert all(item["exact_agent_id_created_flag"] is False for item in records())
