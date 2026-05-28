from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import accepted_records


def test_pr159_private_or_access_controlled_sources_block_without_attestation():
    assert all(record.get("official_source_class") != c.SourceTargetState.PRIVATE_OR_ACCESS_CONTROLLED_BLOCKED.value for record in accepted_records())

