from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import (
    accepted_records,
    master_report,
)


def test_pr159_rejects_owner_assertion_as_source_fact():
    assert master_report()["source_required_owner_fill_rejected_count"] > 0
    assert all(
        record["source_population"] == c.PR159TargetPopulation.PR154_PUBLIC_SOURCE_RETRY_34.value
        for record in accepted_records()
    )
