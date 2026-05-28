def test_pr159r_pr82_pr86_quantum_artifacts_consumed(pr159r_artifacts):
    paths = {item["path"] for item in pr159r_artifacts["master"]["input_consumption_receipt"]}
    assert "docs/master_plan/generated/QuantumApplicabilityClassificationRegistry.report.json" in paths
    assert "docs/master_plan/generated/QuantumClassicalOptimizerArbitrationGate.report.json" in paths

