def test_data_binding_requirement_matrix(summary, records):
    rows = records("PR162R_ReplayPaperDataBindingRequirementMatrix.report.json")
    assert len(rows) == summary["data_binding_requirement_rows_count"]
    assert rows
    for row in rows[:25]:
        assert row["synthetic_test_vector_status"] == "SYNTHETIC_TEST_VECTOR_READY"
        assert row["data_binding_status"] == "DATA_BINDING_FILL_REQUIRED"
        assert row["fill_action_refs"]
        assert row["route_ready_treated_as_data_ready_flag"] is False
