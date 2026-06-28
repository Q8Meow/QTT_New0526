from ._helpers import read_jsonl


def test_stack_feature_vectors_have_execution_agent_and_quantum_surfaces() -> None:
    rows = read_jsonl("features.jsonl")
    assert rows
    for row in rows[:10]:
        assert row["role_features"]
        assert row["tca_features"]
        assert row["agent_route_features"]
        assert row["no_orphan_features"]["artifact_orphan_flag"] is False
        assert row["future_rank4_consumer_flag"] is True
        assert row["future_qopt1_consumer_flag"] is True
