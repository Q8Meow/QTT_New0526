from .pr161b_test_support import records, summary


def test_pr161b_quantum_online_scout_is_nonblocking():
    assert summary()["quantum_online_scout_enrichment_count"] == len(records("quantum_online_scout"))
    assert all(record["ci_dependency_flag"] is False for record in records("quantum_online_scout"))
