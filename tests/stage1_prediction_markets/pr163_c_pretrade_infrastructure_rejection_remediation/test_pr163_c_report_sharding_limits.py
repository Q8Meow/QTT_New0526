from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation import paths as p
from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.report_sharding import ROOT_REPORT_LIMIT_BYTES, SHARD_LIMIT_BYTES
from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.tests_support import load_records, repo_root, summary


def test_pr163_c_report_sharding_limits():
    root = repo_root()
    assert summary()["total_shard_count"] > 0
    for row in load_records("PR163_C_ReportManifest.report.json"):
        path = root / p.GENERATED_DIR / row["report_filename"]
        assert path.stat().st_size <= ROOT_REPORT_LIMIT_BYTES
        for shard in row["shard_paths"]:
            assert (root / shard).stat().st_size <= SHARD_LIMIT_BYTES
