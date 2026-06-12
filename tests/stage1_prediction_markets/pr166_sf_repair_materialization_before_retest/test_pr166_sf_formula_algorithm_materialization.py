from .conftest import assert_rows


def test_pr166_sf_formula_algorithm_materialization_has_schema_and_tests(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_FormulaAlgorithmMaterializationRegistry.report.json")
    assert len(rows) == 6502
    for row in rows[:50]:
        assert row["deterministic_callable"] == "repaired_net_edge_after_costs"
        assert row["input_schema"]
        assert row["test_vector_ref"]
        assert row["smoke_test_ref"]
