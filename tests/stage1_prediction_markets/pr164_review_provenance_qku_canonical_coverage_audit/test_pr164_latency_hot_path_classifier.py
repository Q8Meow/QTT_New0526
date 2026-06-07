from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.central_reason_codes import LATENCY_CLASSES
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_records, summary


def test_pr164_latency_hot_path_classifier():
    rows = load_records("PR164_LatencyHotPathClassifier.report.json")
    assert len(rows) == summary()["latency_hot_path_rows"]
    assert all(row["latency_hot_path_class"] in LATENCY_CLASSES for row in rows)
    assert all(row["hot_path_runtime_allowed"] is False for row in rows)
