from __future__ import annotations


def test_pr162d_r1_rejects_quantum_metadata_only_labels(records, summary):
    audit = records("PR162D_R1_QuantumMetadataOnlyRejectionAudit.report.json")[0]
    quantum = records("PR162D_R1_QuantumFormulaAcquisitionLedger.report.json")
    assert audit["quantum_metadata_only_count"] == 0
    assert summary["quantum_metadata_only_count"] == 0
    assert all(record["quantum_metadata_only_flag"] is False for record in quantum)
