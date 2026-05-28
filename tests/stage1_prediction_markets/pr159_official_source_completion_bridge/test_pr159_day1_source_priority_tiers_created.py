from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import master_report, report


def test_pr159_day1_source_priority_tiers_created():
    counts = master_report()["day1_source_priority_tier_counts"]
    assert set(counts) == c.CENTRAL_ENUM_VALUE_SETS["day1_source_priority_tier"]
    assert sum(counts.values()) == 879
    assert report(c.DAY1_PRIORITY_INDEX_PATH)["record_count"] == 4

