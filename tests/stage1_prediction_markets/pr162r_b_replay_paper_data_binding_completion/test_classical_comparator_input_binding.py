def test_classical_comparator_input_binding(summary, records):
    rows = records("PR162R_B_ClassicalComparatorInputBindingRegistry.report.json")
    assert len(rows) == summary["classical_comparator_input_binding_count"] > 0
