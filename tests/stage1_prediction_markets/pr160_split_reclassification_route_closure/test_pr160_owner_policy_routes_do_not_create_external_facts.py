from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import master_report, report


def test_pr160_owner_policy_routes_do_not_create_external_facts():
    assert report(c.OWNER_POLICY_ROUTE_PATH)["record_count"] == 0
    assert master_report()["invented_external_fact_count"] == 0
