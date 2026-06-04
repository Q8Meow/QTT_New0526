from __future__ import annotations


def test_pr162r_a_quantum_backend_missing_is_noncritical_when_local_or_classical_comparator_exists(records):
    classifications = records("PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json")
    quantum_rows = [row for row in classifications if row["candidate_type"] == "QUANTUM"]
    assert quantum_rows
    assert all("QUANTUM_COMPARATOR_READY" in row["secondary_tags"] for row in quantum_rows)
    assert all("QUANTUM_BACKEND_OPTIONAL" in row["secondary_tags"] for row in quantum_rows)
    assert all(not row["critical_missing_info"] for row in quantum_rows)
