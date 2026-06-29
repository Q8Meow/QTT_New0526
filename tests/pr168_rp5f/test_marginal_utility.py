from ._helpers import assert_rows_have_contract


def test_marginal_utility_surfaces_are_inputs_not_selections() -> None:
    rows = assert_rows_have_contract("marg_util.jsonl")

    assert all(row["portfolio_exposure_variables"] for row in rows)
    assert all(row["correlation_proxy_variables"] for row in rows)
    assert all(row["future_rank4_marginal_utility_required_flag"] is True for row in rows)
    assert all(row["marginal_utility_selected_flag"] is False for row in rows)

