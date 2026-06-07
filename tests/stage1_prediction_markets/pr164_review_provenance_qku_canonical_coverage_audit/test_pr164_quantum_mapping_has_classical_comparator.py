from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_quantum_mapping_has_classical_comparator():
    rows = load_records("PR164_QuantumCompatibilityRouter.report.json")
    assert summary()["quantum_rows_with_classical_comparator"] == len(rows)
    assert all(row["classical_comparator_required_flag"] is True for row in rows)
    assert all(row["classical_comparator_formula_ref"] for row in rows)
