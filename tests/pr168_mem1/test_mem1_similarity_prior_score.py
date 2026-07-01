from .test_support import read_jsonl


def test_similarity_and_prior_scores_are_decomposed() -> None:
    sim = read_jsonl("context_similarity_score.jsonl")[0]
    for field in ("venue_match_weight", "spread_depth_liquidity_similarity", "drift_penalty", "provenance_penalty"):
        assert field in sim
    prior = read_jsonl("recipe_prior_score.jsonl")[0]
    assert prior["shrinkage_adjusted_mean_net_pnl"]
    assert prior["hierarchical_pool_key"]
    assert prior["off_policy_evaluation_required_flag"] is True
    assert prior["oos_lockbox_required_flag"] is True
    assert prior["fdr_q_value_or_proxy"]
