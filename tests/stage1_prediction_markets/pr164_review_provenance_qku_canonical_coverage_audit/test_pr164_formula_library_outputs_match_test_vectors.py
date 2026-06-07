from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.qku_formula_test_vectors import build_formula_test_vector_rows


def test_pr164_formula_library_outputs_match_test_vectors():
    rows = build_formula_test_vector_rows()
    assert len(rows) == 12
    assert all(row["test_vector_passed"] for row in rows)
