from tests.pr169_dash1.conftest import jsonl


def test_institutional_metric_rows_route_to_upstream_refs() -> None:
    row = jsonl("owner_institutional_metric_view.generated.jsonl")[0]
    for field in (
        "execution_adjusted_rank_ref",
        "TCA_decomposition_ref",
        "portfolio_marginal_utility_ref",
        "overfit_false_discovery_control_ref",
        "no_trade_reoptimization_route_ref",
        "quantum_structural_readiness_ref",
    ):
        assert row[field]
    assert "candidate_minus_no_trade_cash" in row["comparison_classes"]
