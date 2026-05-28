from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import report


def test_pr159_trade_context_source_readiness_update_metadata_only():
    payload = report(c.TRADE_CONTEXT_SOURCE_UPDATE_PATH)
    assert payload["record_count"] == 845
    assert all(item["metadata_only_no_selection_execution"] is True for item in payload["records"])

