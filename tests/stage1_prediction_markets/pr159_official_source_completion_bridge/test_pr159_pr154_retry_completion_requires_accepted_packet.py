from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import pr154_records


def test_pr159_pr154_retry_completion_requires_accepted_packet():
    for record in pr154_records():
        if record["completion_status"] == c.SourceTargetState.ACCEPTED_COMPLETED.value:
            assert record["accepted_source_packet_ref_or_null"]
        else:
            assert record["accepted_source_packet_ref_or_null"] is None

