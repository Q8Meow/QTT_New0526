from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import report


def test_pr159_rejects_non_authoritative_source_as_fact():
    payload = report(c.NON_AUTHORITATIVE_REJECTION_PATH)
    assert payload["record_count"] > 0
    assert all(item["rejection_decision"] == c.SourceAcceptanceDecision.REJECTED_NOT_OFFICIAL.value for item in payload["records"])

