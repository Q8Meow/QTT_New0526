from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.report_sharding import ROOT_REPORT_LIMIT_BYTES, SHARD_LIMIT_BYTES
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import load_report, repo_root, summary
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit import paths as p


def test_pr164_report_sharding_limits():
    root = repo_root()
    record = summary()
    assert record["report_shard_count"] > 0
    assert record["largest_root_report_size_bytes"] <= ROOT_REPORT_LIMIT_BYTES
    assert record["largest_shard_size_bytes"] <= SHARD_LIMIT_BYTES
    for manifest_row in load_report("PR164_ReportManifest.report.json")["records"]:
        path = root / p.GENERATED_DIR / manifest_row["report_filename"]
        assert path.stat().st_size <= ROOT_REPORT_LIMIT_BYTES
