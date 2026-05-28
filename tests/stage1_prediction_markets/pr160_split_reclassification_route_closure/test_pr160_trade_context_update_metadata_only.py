from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import constants as c
from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import report


def test_pr160_trade_context_update_metadata_only():
    records = report(c.TRADE_CONTEXT_UPDATE_PATH)["records"]
    assert len(records) == 33
    assert all(item["metadata_only_no_trade_context_selection_execution"] is True for item in records)
