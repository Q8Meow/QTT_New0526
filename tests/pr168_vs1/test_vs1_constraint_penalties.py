from __future__ import annotations

from ._helpers import rows


def test_vs1_constraint_penalties_cover_required_gate_constraints():
    constraints = rows("constraint_penalty_policy_receipts.jsonl")
    names = {row["constraint_name"] for row in constraints}

    assert {
        "min_fill_probability",
        "positive_lcb",
        "positive_no_trade_margin",
        "max_tca_to_edge",
        "max_capacity_used_ratio",
        "portfolio_gate",
        "scenario_gate",
        "agent_route_valid",
        "no_orphan_proof_valid",
        "stage1_identity_eligible",
        "no_unknown_needs_review",
        "ephemeral_stack_only",
        "ex_ante_candidate_only",
        "no_gate_relaxation_to_force_pnl",
        "no_impossible_price",
        "no_impossible_fill",
        "no_hindsight_backsolve",
        "no_backend_execution",
    }.issubset(names)
    assert any(row["violated_flag"] is True for row in constraints)
