from .pr161b_test_support import records, summary


def test_pr161b_qtt_agent_candidate_consumption_matrix_is_complete():
    assert summary()["qtt_agent_candidate_consumption_mapping_count"] == len(records("qtt_agent_consumption"))
    assert all(record["agent_consumption_state"] for record in records("qtt_agent_consumption")[:25])
