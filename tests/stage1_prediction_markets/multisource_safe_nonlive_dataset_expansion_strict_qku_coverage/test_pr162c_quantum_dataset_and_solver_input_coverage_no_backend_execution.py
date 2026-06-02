from .test_support import records, report


def test_pr162c_quantum_dataset_and_solver_input_coverage_no_backend_execution():
    summary = report("PR162C_FinalSummary.report.json")
    quantum = records("PR162C_QuantumFeatureDatasetStrictCoverageBridge.report.json")
    solver = records("PR162C_QuantumSolverInputAssemblyCoverageAudit.report.json")

    assert summary["strict_quantum_feature_qku_count"] == 0
    assert quantum
    assert not any(record["quantum_feature_dataset_available_flag"] for record in quantum)
    assert all(record["backend_execution_allowed_flag"] is False for record in quantum + solver)
    assert all(record["simulator_execution_allowed_flag"] is False for record in quantum + solver)
