def test_pr166_sm_false_discovery_and_overfit_fields_are_materialized(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_FalseDiscoveryRiskRefreshLedger.report.json"]
    overfit_rows = pr166_sm_records["PR166_SM_OverfitAndRankInstabilityRegistry.report.json"]
    assert len(rows) == 3985
    assert len(overfit_rows) == 3985
    for row in rows[:300]:
        assert row["num_related_trials"] >= 1
        assert row["effective_independent_trial_count"] >= 1
        assert 0.0 <= row["false_discovery_risk_adjustment"] <= 1.0
        assert 0.0 <= row["overfit_risk_adjustment"] <= 1.0
        assert 0.0 <= row["rank_instability_adjustment"] <= 1.0
        assert isinstance(row["reject_as_miracle_singleton_flag"], bool)
        assert row["reason_codes"]
        assert row["downstream_route"] in row["downstream_pr_refs"]


def test_pr166_sm_overfit_registry_routes_high_risk_rows_without_global_rejection(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_OverfitAndRankInstabilityRegistry.report.json"]
    high_risk = [
        row
        for row in rows
        if row["false_discovery_risk_adjustment"] >= 0.65
        or row["overfit_risk_adjustment"] >= 0.60
        or row["rank_instability_adjustment"] >= 0.60
    ]
    assert high_risk
    assert all(row["downstream_route"] in {"PR166-SF", "PR165-D2"} for row in high_risk[:200])
