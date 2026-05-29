from .pr161b_test_support import records, summary


def test_pr161b_downstream_agent_mapping_has_no_orphans():
    assert summary()["downstream_qtt_agent_residual_mapping_count"] == len(records("downstream_agent"))
    assert all(record["downstream_agent_roles"] for record in records("downstream_agent")[:25])
