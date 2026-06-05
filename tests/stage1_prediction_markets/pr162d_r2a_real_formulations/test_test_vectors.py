from __future__ import annotations


def test_test_vector_registry_covers_callable_records(records, summary):
    vectors = records("PR162D_R2A_TestVectorRegistry.report.json")
    assert len(vectors) == summary["test_vector_count"]
    assert len(vectors) >= (
        summary["real_formula_function_count"]
        + summary["real_algorithm_callable_count"]
        + summary["real_quantum_shape_builder_count"]
    )
    assert all(row["callable_ref"] for row in vectors)
    assert all("inputs" in row for row in vectors)
    assert all(row["live_order_authority"] is False for row in vectors)
