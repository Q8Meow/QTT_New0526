from .test_support import read_jsonl


def test_qku_formula_routes_preserve_refs_without_mutation() -> None:
    for row in read_jsonl("qku_formula_route_bundle.jsonl"):
        assert row["qku_refs"]
        assert row["formula_refs"]
        assert row["qku_formula_mutation_flag"] is False


def test_qstruct_carry_preserves_qopt1_refs_without_backend_execution() -> None:
    for row in read_jsonl("qstruct_carry.jsonl"):
        assert row["qopt1_qubo_ref"].endswith("qubo.jsonl")
        assert row["qopt1_bqm_ref"].endswith("bqm.jsonl")
        assert row["qopt1_cqm_ref"].endswith("cqm.jsonl")
        assert row["true_quantum_backend_execution_flag"] is False
        assert row["quantum_advantage_claim_flag"] is False
