from ._helpers import read_jsonl


def test_quantum_carry_forward_has_structure_without_backend() -> None:
    rows = read_jsonl("q_struct_carry.jsonl")
    assert rows
    assert all(row["objective_terms"] and row["variable_domains"] and row["classical_fallback"] for row in rows)
    assert all(row["quantum_backend_execution_flag"] is False for row in rows)
