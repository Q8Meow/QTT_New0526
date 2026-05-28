from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import accepted_records


def test_pr159_accepted_packets_require_official_confirmed_status():
    assert all(record["official_source_confidence"] == c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value for record in accepted_records())

