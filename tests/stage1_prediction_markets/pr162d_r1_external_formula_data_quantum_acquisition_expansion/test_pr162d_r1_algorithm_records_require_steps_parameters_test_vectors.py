from __future__ import annotations


def test_pr162d_r1_algorithm_records_require_steps_parameters_test_vectors(records):
    algorithms = records("PR162D_R1_AlgorithmAcquisitionLedger.report.json")
    assert algorithms
    assert all(record["deterministic_steps"] and record["parameters"] and record["test_vector"] for record in algorithms)
