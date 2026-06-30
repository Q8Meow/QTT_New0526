from ._helpers import rows


def test_canonical_quantum_diagnostics_are_complete() -> None:
    assert rows("objective_sign.jsonl")[0]["target_energy_direction"] == "minimize_energy"
    assert rows("energy_transform.jsonl")[0]["canonical_variable_order"]
    assert all(row["upper_triangle_canonical_flag"] for row in rows("qubo_matrix.jsonl"))
    assert rows("qresource_est.jsonl")[0]["backend_execution_created_flag"] is False
    assert rows("class_dom_base.jsonl")[0]["future_quantum_path_must_beat_classical_baseline"] is True
