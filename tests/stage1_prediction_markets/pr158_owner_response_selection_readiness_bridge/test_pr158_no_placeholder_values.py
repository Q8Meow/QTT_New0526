from src.qtt.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.validator import _placeholder_failures
from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import master_report, overlay_registry


def test_pr158_no_placeholder_values():
    assert master_report()["placeholder_value_count"] == 0
    assert _placeholder_failures(master_report()) == []
    assert _placeholder_failures(overlay_registry()) == []

