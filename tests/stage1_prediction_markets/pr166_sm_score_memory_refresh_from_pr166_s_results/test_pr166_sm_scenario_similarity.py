from src.qtt.stage1_prediction_markets.pr166_sm_score_memory_refresh_from_pr166_s_results import constants as c


def test_pr166_sm_scenario_similarity_policy_weights_are_deterministic():
    assert round(sum(c.SCENARIO_SIMILARITY_WEIGHTS.values()), 6) == 1.10
    assert c.SCENARIO_SIMILARITY_WEIGHTS["venue"] == 0.10
    assert c.SCENARIO_SIMILARITY_WEIGHTS["liquidity_bucket"] == 0.10
    assert c.SCENARIO_SIMILARITY_WEIGHTS["quantum_compatibility_bucket"] == 0.04


def test_pr166_sm_scenario_similarity_scores_are_bounded(pr166_sm_records):
    rows = pr166_sm_records["PR166_SM_RefreshedMemoryLedger.report.json"]
    assert any(row["scenario_similarity_score"] > 0 for row in rows)
    assert all(0.0 <= row["scenario_similarity_score"] <= 1.0 for row in rows[:500])
