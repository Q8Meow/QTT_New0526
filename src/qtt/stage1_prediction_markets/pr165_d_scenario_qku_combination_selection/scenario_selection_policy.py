"""Scenario-specific selection policy rows and bucket assignment."""

from __future__ import annotations

from typing import Any

from .authority_policy import authority_zero_counts
from .central_vocab import (
    AUTHORITY_BOUNDARY_REF,
    BUCKET_REALLOCATION_PRIORITY,
    DOWNSTREAM_PR_ROUTES,
    NO_ORPHAN_STATUS,
    SCENARIO_SELECTION_BUCKETS,
    SELECTION_BUDGETS,
    UPSTREAM_PR_REFS,
    VALIDATION_STATUS,
)


def build_selection_policy_rows() -> list[dict[str, Any]]:
    return [
        {
            "selection_policy_id": "PR165_D_SELECTION_POLICY::SCENARIO_QKU_COMBINATION_V1",
            "policy_purpose": "Scenario-specific QKU formula algorithm combination selection for future replay paper retest batches",
            "base_score_formula_ref": "PR165_D_SCORE_FORMULA::NORMALIZED_SCENARIO_SELECTION_V1",
            "adjusted_score_formula_ref": "PR165_D_SCORE_FORMULA::DIVERSITY_ADJUSTED_SELECTION_V1",
            "marginal_utility_formula_ref": "PR165_D_SCORE_FORMULA::GREEDY_MARGINAL_UTILITY_V1",
            "exploit_budget_pct_default": SELECTION_BUDGETS["EXPLOIT_HIGH_CONFIDENCE_HIGH_EDGE"],
            "explore_budget_pct_default": SELECTION_BUDGETS["EXPLORE_HIGH_EDGE_LOW_CONFIDENCE"],
            "repair_budget_pct_default": SELECTION_BUDGETS["REPAIR_HIGH_EDGE_BLOCKED"],
            "quantum_repair_budget_pct_default": SELECTION_BUDGETS["QUANTUM_FORMULATION_REPAIR"],
            "watch_backlog_budget_pct_default": SELECTION_BUDGETS["WATCH_FRAGILE_SCENARIO"],
            "deterministic_bucket_reallocation_priority": list(BUCKET_REALLOCATION_PRIORITY),
            "scenario_selection_buckets": list(SCENARIO_SELECTION_BUCKETS),
            "deterministic_tie_breakers": [
                "higher_marginal_candidate_utility",
                "higher_adjusted_selection_score",
                "higher_pr165_c_retest_priority_score",
                "higher_expected_value_score",
                "lower_TCA_drag",
                "lower_latency_drag",
                "lower_liquidity_fragility",
                "higher_evidence_confidence",
                "higher_repair_readiness_if_repair_route",
                "higher_quantum_formulation_readiness_if_quantum_compatible",
                "lexicographic_qku_id",
                "lexicographic_candidate_packet_id",
                "lexicographic_condition_fingerprint_id",
                "lexicographic_combination_fingerprint_id",
            ],
            "ready_retest_and_repair_separation_required": True,
            "quantum_backend_execution_allowed": False,
            "quantum_advantage_claim_allowed": False,
            "replay_execution_allowed": False,
            "paper_execution_allowed": False,
            "live_order_authority_allowed": False,
            "profit_evidence_claim_allowed": False,
            "owning_agent": "selection_agent",
            "challenger_agent": "risk_agent",
            "upstream_source_pr_refs": list(UPSTREAM_PR_REFS),
            "downstream_consumer_pr_refs": list(DOWNSTREAM_PR_ROUTES),
            "validator": "tools/validate_pr165_d_scenario_qku_combination_selection.py",
            "manifest_entry_ref": "PR165_D_ReportManifest.report.json",
            "no_orphan_status": NO_ORPHAN_STATUS,
            "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
            "validation_status": VALIDATION_STATUS,
            **authority_zero_counts(),
        }
    ]


def scenario_bucket(
    *,
    repair_required: bool,
    quantum_repair_required: bool,
    positive_memory: bool,
    fragile_memory: bool,
    expected_value_score: float,
    evidence_confidence_score: float,
) -> str:
    if quantum_repair_required:
        return "QUANTUM_FORMULATION_REPAIR"
    if repair_required:
        return "REPAIR_HIGH_EDGE_BLOCKED"
    if positive_memory and evidence_confidence_score >= 0.55:
        return "EXPLOIT_HIGH_CONFIDENCE_HIGH_EDGE"
    if expected_value_score >= 0.70 and evidence_confidence_score < 0.55:
        return "EXPLORE_HIGH_EDGE_LOW_CONFIDENCE"
    if fragile_memory:
        return "WATCH_FRAGILE_SCENARIO"
    return "LOW_PRIORITY_BACKLOG"
