def test_classical_comparator_smoke_checks(summary, records):
    rows = records("PR162R_FormulationSmokeExecutionLedger.report.json")
    comparators = [row for row in rows if row["callable_family"] == "CLASSICAL_COMPARATOR"]
    assert summary["classical_comparator_smoke_checked_count"] > 0
    assert all(row["smoke_execution_status"] == "SMOKE_EXECUTION_PASSED" for row in comparators)
    assert all(row["comparator_output_shape"] for row in comparators)
