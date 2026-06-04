from __future__ import annotations


def test_pr162r_a_latency_classification_prevents_remote_quantum_hot_path(summary, records):
    latency = records("PR162R_A_LatencyClassCompatibilityMatrix.report.json")
    quantum = [row for row in latency if row["candidate_type"] == "QUANTUM"]
    assert summary["remote_quantum_hot_path_count"] == 0
    assert quantum
    assert all(row["latency_class"] == "QUANTUM_BATCH_ONLY" for row in quantum)
    assert all(row["remote_quantum_hot_path_flag"] is False for row in latency)
