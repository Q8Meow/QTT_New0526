from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results.scoring import (
    refreshed_net_edge_score,
)


def test_pr166_sm_normalized_score_components_are_bounded(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_RefreshedScoreRegistry.report.json"]
    bounded = [
        "normalized_net_edge_after_costs",
        "result_confidence_score",
        "point_in_time_score",
        "no_lookahead_score",
        "scenario_consistency_score",
        "scenario_transferability_score",
        "fill_quality_score",
        "settlement_confidence_score",
        "capacity_score",
        "quantum_mapping_readiness_score",
    ]
    penalty = [
        "cost_drag_ratio",
        "latency_drag_ratio",
        "liquidity_drag_ratio",
        "adverse_selection_ratio",
        "crowding_penalty",
        "correlation_cluster_penalty",
        "false_discovery_risk_adjustment",
        "overfit_risk_adjustment",
        "rank_instability_adjustment",
    ]
    for row in rows[:300]:
        for key in bounded:
            assert 0.0 <= row[key] <= 1.0
        for key in penalty:
            assert row[key] >= 0.0


def test_pr166_sm_refreshed_score_formula_is_materialized(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_RefreshedScoreRegistry.report.json"]
    for row in rows[:200]:
        components = row["score_formula_component_values"]
        assert row["refreshed_net_edge_score"] == refreshed_net_edge_score(components)
