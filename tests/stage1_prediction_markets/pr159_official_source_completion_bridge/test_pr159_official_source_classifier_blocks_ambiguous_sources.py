from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import report


def test_pr159_official_source_classifier_blocks_ambiguous_sources():
    records = report(c.OFFICIAL_CLASSIFIER_AUDIT_PATH)["records"]
    assert any(item.get("official_source_confidence") == c.OfficialSourceConfidence.OFFICIAL_AMBIGUOUS_BLOCKED.value for item in records)

