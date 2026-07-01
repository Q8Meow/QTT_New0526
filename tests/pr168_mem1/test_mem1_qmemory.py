from .test_support import read_jsonl


def test_qmemory_preserves_structural_refs_without_backend_claims() -> None:
    for row in read_jsonl("qmemory_registry.jsonl"):
        assert row["qubo_ref"]
        assert row["bqm_ref"]
        assert row["cqm_ref"]
        assert row["quadratic_program_ref"]
        assert row["interpret_back_map_ref"]
        assert row["backend_execution_created_flag"] is False
        assert row["quantum_advantage_claim_flag"] is False
        assert row["classical_baseline_required_flag"] is True
