from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import report


def test_pr159_official_domain_discovery_created():
    payload = report(c.OFFICIAL_DOMAIN_DISCOVERY_PATH)
    assert payload["record_count"] >= 6
    assert all(item["official_source_refs"] for item in payload["records"])

