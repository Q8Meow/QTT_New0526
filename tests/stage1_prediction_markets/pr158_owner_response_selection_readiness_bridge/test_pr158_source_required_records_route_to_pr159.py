from src.qtt.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge import constants as c
from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import overlay_records


def test_pr158_source_required_records_route_to_pr159():
    source_required = [record for record in overlay_records() if record["blocker_class"] == c.BlockerClass.PUBLIC_SOURCE_REQUIRED.value]
    assert len(source_required) == 845
    assert all(record["future_route"] == c.FutureRoute.PR159_PUBLIC_SOURCE_RETRY.value for record in source_required)

