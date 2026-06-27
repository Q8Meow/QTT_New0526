from __future__ import annotations

from ._helpers import rows


def test_vs1_no_pnl_forcing_proofs_have_required_zero_counts():
    zero_fields = (
        "gate_relaxation_attempt_count",
        "formula_mutation_count",
        "qku_deletion_count",
        "formula_deletion_count",
        "global_qku_ban_count",
        "global_formula_ban_count",
        "impossible_price_candidate_count",
        "impossible_fill_candidate_count",
        "hindsight_backsolve_count",
        "post_hoc_exit_selection_count",
        "ignored_fee_count",
        "ignored_spread_count",
        "ignored_slippage_count",
        "ignored_fill_risk_count",
        "ignored_latency_risk_count",
        "ignored_capacity_risk_count",
        "ignored_portfolio_risk_count",
        "ignored_scenario_risk_count",
        "ignored_overfit_fdr_count",
        "raw_edge_promoted_without_tca_count",
        "no_trade_overridden_count",
    )

    for row in rows("no_pnl_forcing_proof.jsonl"):
        assert row["proof_status"].startswith("PASS_NO_PNL_FORCING")
        assert all(row[field] == 0 for field in zero_fields)
