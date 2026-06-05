from __future__ import annotations


def test_real_formula_records_are_materialized(records, summary):
    rows = [
        row for row in records("PR162D_R2A_FormulationRecordRegistry.report.json")
        if row["formulation_type"] in {"FORMULA", "FEATURE"}
    ]
    assert len(rows) == summary["real_formula_function_count"]
    assert len(rows) >= 24
    assert all(row["expression"] for row in rows)
    assert all(row["callable_ref"] for row in rows)
    assert all(row["inputs"] for row in rows)
    assert all(row["outputs"] for row in rows)
    assert all(row["test_vector_refs"] for row in rows)
    assert all(row["validator_materiality_status"] == "FORMULATION_FULLY_MATERIALIZED" for row in rows)
