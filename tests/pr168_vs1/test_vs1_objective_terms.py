from __future__ import annotations

from ._helpers import rows


def test_vs1_objective_terms_cover_ranking_and_quantum_term_families():
    terms = rows("objective_term_ledger.jsonl")
    names = {row["term_name"] for row in terms}

    assert {
        "expected_edge",
        "fill_adjusted_edge",
        "fees",
        "spread",
        "slippage",
        "queue_fill_shortfall",
        "cancel_replace_cost",
        "latency_decay",
        "capital_lock",
        "capacity_cost",
        "crowding_cost",
        "uncertainty",
        "overfit_fdr",
        "scenario_tail",
        "portfolio_overlap",
        "marginal_utility",
        "diversification_bonus",
        "correlation_overlap_penalty",
        "no_trade_margin",
    }.issubset(names)
    assert any(row["included_in_ranking_flag"] is True for row in terms)
    assert any(row["included_in_quantum_encoding_flag"] is True for row in terms)
