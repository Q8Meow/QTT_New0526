from src.qtt.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge import constants as c
from tests.stage1_prediction_markets.pr158_owner_response_selection_readiness_bridge.pr158_test_support import ROOT


def test_pr158_owner_decision_summary_is_human_readable():
    text = (ROOT / c.OWNER_DECISION_SUMMARY_PATH).read_text(encoding="utf-8")
    assert "Lane A" in text
    assert "Lane F" in text
    assert "Cross-Lane S" in text
    assert "raw JSON" not in text

