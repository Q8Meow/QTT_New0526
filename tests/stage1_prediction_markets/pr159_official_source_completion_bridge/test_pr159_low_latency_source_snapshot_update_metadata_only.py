from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import report


def test_pr159_low_latency_source_snapshot_update_metadata_only():
    payload = report(c.LOW_LATENCY_SOURCE_UPDATE_PATH)
    assert payload["record_count"] == 845
    assert all(item["low_latency_source_snapshot_metadata_only"] is True for item in payload["records"])

