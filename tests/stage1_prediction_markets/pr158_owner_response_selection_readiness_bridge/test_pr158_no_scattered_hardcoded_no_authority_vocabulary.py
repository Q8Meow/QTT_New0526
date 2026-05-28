from src.qtt.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge import constants as c
from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import master_report, overlay_records


def test_pr158_no_scattered_hardcoded_no_authority_vocabulary():
    assert set(master_report()["no_authority_confirmation"].values()) == {False}
    for record in overlay_records()[:25]:
        assert record["blocker_class"] in c.CENTRAL_ENUM_VALUE_SETS["blocker_class"]
        assert record["future_route"] in c.CENTRAL_ENUM_VALUE_SETS["future_route"]

