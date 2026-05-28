from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import accepted_records


def test_pr159_accepted_packets_require_official_source():
    assert all(record["official_source_class"] in c.CENTRAL_ENUM_VALUE_SETS["official_source_class"] for record in accepted_records())

