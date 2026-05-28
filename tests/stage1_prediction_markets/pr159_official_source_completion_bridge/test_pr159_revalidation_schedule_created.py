from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import report


def test_pr159_revalidation_schedule_created():
    payload = report(c.REVALIDATION_SCHEDULE_PATH)
    assert payload["record_count"] == 879
    assert all(item["revalidation_before_connector_binding_required"] is True for item in payload["records"])

