from tests.stage1_prediction_markets.pr159_official_source_completion_bridge.pr159_test_support import candidate_records


def test_pr159_candidate_packets_are_not_accepted_facts():
    assert candidate_records()
    assert all(record["candidate_is_accepted_fact"] is False for record in candidate_records())

