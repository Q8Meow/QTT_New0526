from ._helpers import read_jsonl


def test_marginal_utility_features_are_future_rank4_inputs_only() -> None:
    rows = read_jsonl("marg_util.jsonl")
    assert rows
    for row in rows[:10]:
        assert row["portfolio_exposure_features"]
        assert row["diversification_features"]
        assert row["capacity_features"]
        assert row["future_rank4_marginal_utility_required_flag"] is True
        assert row["marginal_utility_selected_flag"] is False
