from __future__ import annotations


def test_real_algorithm_records_are_materialized(records, summary):
    rows = [
        row for row in records("PR162D_R2A_FormulationRecordRegistry.report.json")
        if row["formulation_type"] == "ALGORITHM"
    ]
    assert len(rows) == summary["real_algorithm_callable_count"]
    assert len(rows) >= 25
    assert all(row["algorithm_procedure"] for row in rows)
    assert all(row["callable_ref"] for row in rows)
    assert all(row["inputs"] for row in rows)
    assert all(row["outputs"] for row in rows)
    assert all(row["test_vector_refs"] for row in rows)
