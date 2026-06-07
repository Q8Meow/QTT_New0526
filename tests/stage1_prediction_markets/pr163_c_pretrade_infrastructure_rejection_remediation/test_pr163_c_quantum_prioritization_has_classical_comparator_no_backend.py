from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, summary


def test_pr163_c_quantum_prioritization_has_classical_comparator_no_backend():
    rows = load_records("PR163_C_QuantumRepairPrioritizationLedger.report.json")
    assert len(rows) == summary()["quantum_repair_prioritization_rows"]
    assert all(row["backend_execution_count"] == 0 for row in rows)
    assert all(row["quantum_advantage_claim_count"] == 0 for row in rows)
    assert all(row["deterministic_classical_score_ref"] for row in rows)
