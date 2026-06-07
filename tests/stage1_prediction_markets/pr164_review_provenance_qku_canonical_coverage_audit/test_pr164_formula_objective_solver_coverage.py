from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_formula_objective_solver_coverage_materialized():
    rows = load_records("PR164_QKUFormulaObjectiveSolverCoverageAudit.report.json")
    assert len(rows) == summary()["formula_objective_solver_coverage_rows"]
    assert all(row["qku_formula_id"] and row["formula_expression"] for row in rows)
    assert all(row["objective_expression"] and row["solver_family"] for row in rows)
