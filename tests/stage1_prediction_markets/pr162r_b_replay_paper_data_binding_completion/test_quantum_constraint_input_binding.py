def test_quantum_constraint_input_binding(summary, records):
    rows = records("PR162R_B_QuantumConstraintInputBindingRegistry.report.json")
    assert len(rows) == summary["quantum_constraint_input_binding_count"] > 0
