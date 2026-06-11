from __future__ import annotations


def test_quantum_priority_rows_have_structure_without_backend_execution(pr165_d2_records):
    rows = pr165_d2_records["PR165_D2_QuantumCandidatePriorityV2.report.json"]
    assert len(rows) == 6502
    first = rows[0]
    assert first["objective_terms"]
    assert first["variable_domains"]
    assert first["backend_quantum_execution_created"] is False
    assert first["quantum_advantage_claim_created"] is False
