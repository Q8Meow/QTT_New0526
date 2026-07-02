from tests.pr169_dash1.conftest import jsonl


def test_positive_net_cash_pipeline_state_requires_all_evidence_refs() -> None:
    positive_rows = [
        row
        for row in jsonl("owner_research_candidate_pipeline_view.generated.jsonl")
        if row["positive_net_cash_evidence_required"]
    ]
    assert positive_rows
    required = {
        "net_expected_pnl_cash_after_TCA",
        "lower_confidence_bound_pnl_cash",
        "candidate_minus_no_trade_cash",
        "fill_adjusted_expected_pnl_cash",
        "latency_adjusted_expected_pnl_cash",
        "capacity_adjusted_expected_pnl_cash",
        "portfolio_marginal_utility",
        "FDR_or_overfit_control",
        "scenario_ladder_pass",
        "calibration_status",
        "replay_paper_validation_receipts",
    }
    for row in positive_rows:
        assert required.issubset(set(row["required_positive_evidence_refs"]))
