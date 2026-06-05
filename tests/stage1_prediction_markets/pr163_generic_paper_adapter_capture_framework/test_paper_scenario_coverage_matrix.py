def test_scenario_coverage_matrix_has_all_required_cases(records):
    rows = records("PR163_PaperScenarioCoverageMatrix.report.json")
    assert len(rows) == 19
    assert all(row["scenario_rows"] > 0 for row in rows)
    assert any(row["partial_fill_rows"] > 0 for row in rows)
    assert any(row["rejection_rows"] > 0 for row in rows)
