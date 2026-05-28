from src.qtt.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge import constants as c
from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import load_json


def test_pr158_trade_context_selection_readiness_no_selection_execution():
    payload = load_json(c.TRADE_CONTEXT_SCORING_MAP_PATH)
    assert payload["record_count"] == 4183
    assert all(record["metadata_only_no_selection_execution"] is True for record in payload["records"])

