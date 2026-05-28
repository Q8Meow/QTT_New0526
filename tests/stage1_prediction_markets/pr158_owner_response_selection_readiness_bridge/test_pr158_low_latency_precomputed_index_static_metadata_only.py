from src.qtt.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge import constants as c
from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import load_json


def test_pr158_low_latency_precomputed_index_static_metadata_only():
    payload = load_json(c.LOW_LATENCY_INDEX_PATH)
    assert payload["live_pretrade_path_parse_large_json_allowed"] is False
    assert payload["live_pretrade_path_parse_master_plan_allowed"] is False
    assert payload["runtime_live_authority_created"] is False

