from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import report


def test_pr160_route_collision_audit_blocks_unresolved_collisions():
    records = report(c.ROUTE_COLLISION_AUDIT_PATH)["records"]
    assert all(item["unresolved_collision_blocked_flag"] is False for item in records)
