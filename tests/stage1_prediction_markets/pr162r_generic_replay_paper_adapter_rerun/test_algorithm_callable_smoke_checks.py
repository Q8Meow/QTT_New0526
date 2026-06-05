def test_algorithm_callable_smoke_checks(summary, records):
    rows = records("PR162R_FormulationSmokeExecutionLedger.report.json")
    algorithms = [row for row in rows if str(row.get("formulation_ref", "")).startswith("ALGORITHM::")]
    assert summary["algorithm_callable_smoke_checked_count"] > 0
    assert all(row["smoke_execution_status"] == "SMOKE_EXECUTION_PASSED" for row in algorithms)
