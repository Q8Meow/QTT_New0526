from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.artifact_discovery import discover_inputs
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.tests_support import repo_root, summary


def test_pr164_input_artifact_discovery_records_pr163_b_and_exact_missing_receipt():
    discovery = discover_inputs(repo_root())
    consumed = set(discovery.existing_paths)

    assert "docs/master_plan/generated/PR163_B_FinalSummary.report.json" in consumed
    assert summary()["pr163_b_candidate_packet_universe_count"] == 6502
    assert (
        "docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"
        in discovery.missing_required_paths
    )
