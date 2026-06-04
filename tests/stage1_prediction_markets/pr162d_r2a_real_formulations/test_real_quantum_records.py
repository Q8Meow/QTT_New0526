from __future__ import annotations


def test_real_quantum_records_are_materialized(records):
    rows = [
        row for row in records("PR162D_R2A_FormulationRecordRegistry.report.json")
        if row["formulation_type"] == "QUANTUM_FORMULATION"
    ]
    assert len(rows) >= 25
    assert all(row["objective"] for row in rows)
    assert all(row["variables"] for row in rows)
    assert all(row["domains"] for row in rows)
    assert all(row["constraints"] or row["penalties"] for row in rows)
    assert all(row["classical_comparator_ref"] for row in rows)
    assert all(row["quantum_backend_execution_flag"] is False for row in rows)
    assert all(row["quantum_advantage_claim_flag"] is False for row in rows)
