from src.qtt.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge import constants as c
from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import load_json


def test_pr158_future_research_addition_intake_compatibility():
    payload = load_json(c.FUTURE_RESEARCH_PATH)
    assert payload["record_count"] == 15
    assert all(record["no_direct_live_authority_flag"] is True for record in payload["records"])
    assert all(record["replay_paper_required_before_live_flag"] is True for record in payload["records"])

