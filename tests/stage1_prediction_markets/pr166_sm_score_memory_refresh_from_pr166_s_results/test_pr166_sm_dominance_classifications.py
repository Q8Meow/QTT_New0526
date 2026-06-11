from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results.enums import (
    ALLOWED_PRIMARY_CLASSIFICATIONS,
)


def test_pr166_sm_every_executed_candidate_has_computable_dominance(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_RefreshedScoreRegistry.report.json"]
    assert len(rows) == 3985
    for row in rows:
        assert row["primary_classification"] in ALLOWED_PRIMARY_CLASSIFICATIONS
        assert row["classification_reason_codes"]
        assert row["classification_numeric_evidence"]


def test_pr166_sm_downgrade_registries_are_conditioned_by_numeric_evidence(pr166_sm_records):
    downgrade_reports = [
        "PR166_SM_CostDominatedDowngradeRegistry.report.json",
        "PR166_SM_LatencyDominatedDowngradeRegistry.report.json",
        "PR166_SM_LiquidityDominatedDowngradeRegistry.report.json",
        "PR166_SM_AdverseSelectionDowngradeRegistry.report.json",
        "PR166_SM_SettlementSensitivityRegistry.report.json",
    ]
    for report in downgrade_reports:
        for row in pr166_sm_records[report][:100]:
            assert row["dominance_evidence"]
            assert row["downstream_route"] in row["downstream_pr_refs"]
