from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.central_reason_codes import PROHIBITED_DISPOSITIONS
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_qku_computability_materialization_no_metadata_only():
    rows = load_records("PR164_QKUComputabilityMaterializationRegistry.report.json")
    assert len(rows) == summary()["qku_canonical_identity_rows"]
    assert all(row["computability_disposition"] not in PROHIBITED_DISPOSITIONS for row in rows)
    assert summary()["metadata_only_rows_remaining"] == 0
    assert summary()["placeholder_only_rows_remaining"] == 0
    assert summary()["future_consumer_only_rows_remaining"] == 0
