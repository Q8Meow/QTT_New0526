from ._helpers import read_jsonl


def test_quantum_tags_are_structural_and_backend_free() -> None:
    rows = read_jsonl("q_tags.jsonl")
    assert rows
    for row in rows[:10]:
        assert row["q_map_family"] in {"QUBO", "BQM", "CQM", "DQM", "QuadraticProgram", "Ising"}
        assert row["qopt_execution_flag"] is False
        assert row["quantum_backend_execution_flag"] is False
        assert row["quantum_advantage_claim_flag"] is False
        assert row["classical_fallback_ref"]
