from .pr161b_test_support import records, summary


def test_pr161b_online_scout_candidate_enrichment_is_nonblocking():
    assert summary()["online_scout_candidate_enrichment_count"] == len(records("online_scout"))
    assert all(record["online_network_fetch_attempted_flag"] is False for record in records("online_scout"))
