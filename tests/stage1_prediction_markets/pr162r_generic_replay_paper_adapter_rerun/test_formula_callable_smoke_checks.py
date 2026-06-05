def test_formula_callable_smoke_checks(summary, records):
    rows = records("PR162R_FormulationSmokeExecutionLedger.report.json")
    formula = [row for row in rows if str(row.get("formulation_ref", "")).startswith("FORMULA::")]
    assert summary["formula_callable_smoke_checked_count"] > 0
    assert all(row["smoke_execution_status"] == "SMOKE_EXECUTION_PASSED" for row in formula)
