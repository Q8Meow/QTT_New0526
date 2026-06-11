def test_pr166_sm_capacity_crowding_registry_is_computable(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_CapacityAndCrowdingRegistry.report.json"]
    assert len(rows) == 3985
    for row in rows[:300]:
        assert 0.0 <= row["capacity_score"] <= 1.0
        assert row["capacity_bucket"]
        assert row["crowding_penalty"] >= 0.0
        assert row["correlation_cluster_penalty"] >= 0.0
        assert row["marginal_utility_score"] >= 0.0
        assert row["portfolio_selection_note"]


def test_pr166_sm_correlation_clusters_preserve_representatives_and_challengers(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_CorrelationClusterRegistry.report.json"]
    assert len(rows) == 3985
    assert any(row["cluster_representative_flag"] is True for row in rows)
    assert all(row["correlation_cluster_id"].startswith("PR166_SM_CORRELATION_CLUSTER::") for row in rows[:300])
