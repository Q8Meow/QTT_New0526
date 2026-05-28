from src.qtt.stage1_prediction_markets.pr159_official_source_completion_bridge import constants as c
from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import (
    accepted_records,
    candidate_records,
)


def test_pr159_requires_target_field_scope_match():
    accepted_candidate_ids = {record["candidate_packet_id"] for record in accepted_records()}
    for record in candidate_records():
        if record["candidate_packet_id"] in accepted_candidate_ids:
            assert record["target_field_scope_match_flag"] is True
            assert record["acceptance_decision"] == c.SourceAcceptanceDecision.ACCEPTED_TARGET_FIELD_EXACT.value
        else:
            assert record["target_field_scope_match_flag"] is False
            assert record["acceptance_decision"] == c.SourceAcceptanceDecision.DEFERRED_FUTURE_SOURCE_RETRY.value
