def test_quantum_comparator_dataset_binding(summary, records):
    rows = records("PR162R_B_QuantumComparatorDatasetBindingRegistry.report.json")
    assert len(rows) == summary["quantum_comparator_dataset_binding_count"] > 0
