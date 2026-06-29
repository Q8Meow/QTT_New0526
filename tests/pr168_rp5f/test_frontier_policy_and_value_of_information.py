from ._helpers import assert_rows_have_contract


def test_frontier_policy_and_value_of_information_control_search_space() -> None:
    frontier = assert_rows_have_contract("frontier_policy.jsonl")
    voi = assert_rows_have_contract("vof_grid.jsonl")

    assert all(row["beam_search_ready_flag"] for row in frontier)
    assert all(row["successive_halving_ready_flag"] for row in frontier)
    assert all(row["bayesian_optimization_ready_flag"] for row in frontier)
    assert all(row["frontier_diversity_ready_flag"] for row in frontier)
    assert all(row["full_cartesian_persisted_flag"] is False for row in frontier)
    assert all(row["use_and_dump_required_flag"] is True for row in frontier)
    assert all(row["replay_paper_verification_required"] is True for row in voi)
    assert all(row["live_authority_flag"] is False for row in voi)

