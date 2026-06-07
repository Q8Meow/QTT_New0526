from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_master_inventory_reconciliation_counts():
    record = summary()
    residual = load_records("PR164_QKUResidual4835ToAtomicRows4183PR154342MergeAudit.report.json")[0]
    historical = load_records("PR164_QKUHistorical9360VsCurrent6502Reconciliation.report.json")[0]

    assert record["qku_canonical_identity_rows"] == 9360
    assert residual["residual_inventory_rows"] == 4835
    assert residual["atomicrows_compatibility_rows"] == 4183
    assert residual["pr154_compatibility_rows"] == 342
    assert historical["historical_qku_inventory_rows"] == 9360
    assert historical["current_candidate_packet_v1_rows"] == 6502
