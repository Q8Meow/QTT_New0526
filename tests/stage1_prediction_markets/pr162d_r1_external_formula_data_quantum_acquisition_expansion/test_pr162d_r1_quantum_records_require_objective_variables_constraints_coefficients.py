from __future__ import annotations


def test_pr162d_r1_quantum_records_require_objective_variables_constraints_coefficients(records):
    quantum = records("PR162D_R1_QuantumFormulaAcquisitionLedger.report.json")
    assert quantum
    assert all(record["mathematical_objective"] and record["variable_definitions"] and record["constraint_definitions"] and record["coefficient_definitions"] for record in quantum)
