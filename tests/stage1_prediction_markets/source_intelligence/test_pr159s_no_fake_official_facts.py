from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import load, summary


def test_pr159s_no_non_official_source_counted_as_official_fact():
    official_delta = load(c.OFFICIAL_EXTERNAL_FACT_DELTA_PATH)
    assert official_delta["accepted_official_external_fact_delta_count"] == 0
    assert all(record["accepted_official_external_fact_created_flag"] is False for record in official_delta["records"])
    assert all(record["official_confirmed_flag"] is False for record in summary()["records"])

