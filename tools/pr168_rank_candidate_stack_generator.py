#!/usr/bin/env python3
"""Candidate stack generation from PR168-RP computed evidence."""

from __future__ import annotations

from typing import Any

from tools.pr168_rank_report_writer import authority_flags


STACK_ROLES = [
    "probability_estimation",
    "probability_calibration",
    "binary_contract_ev",
    "TCA_cost_model",
    "fill_probability_model",
    "latency_decay_model",
    "capacity_crowding_model",
    "portfolio_marginal_utility_model",
    "overfit_fdr_penalty_model",
    "scenario_ladder_model",
    "order_policy_model",
    "risk_sizing_model",
    "quantum_structural_selection_model",
    "classical_comparator_model",
]


def build_candidate_stacks(computed_rows: list[dict[str, Any]], combination_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    combo_by_qku = {str(row.get("qku_refs", [""])[0]): row for row in combination_rows if row.get("qku_refs")}
    stacks: list[dict[str, Any]] = []
    for index, row in enumerate(computed_rows, start=1):
        qku_id = row.get("qku_id")
        combo = combo_by_qku.get(str(qku_id), {})
        stack_id = f"PR168_RANK_STACK::{index:05d}"
        formula_refs = _as_list(row.get("formula_id")) or _as_list(combo.get("formula_refs"))
        stacks.append(
            {
                "candidate_stack_id": stack_id,
                "candidate_id": row.get("result_ref"),
                "qku_refs": _as_list(qku_id),
                "formula_refs": formula_refs,
                "algorithm_refs": _as_list(combo.get("algorithm_refs")) or ["PR168_RP_PRETRADE_SIMULATION_KERNEL"],
                "probability_model_formula_refs": formula_refs,
                "calibration_formula_refs": formula_refs,
                "edge_formula_refs": formula_refs,
                "TCA_formula_refs": formula_refs,
                "fill_model_refs": ["PR168_RP_MICROSTRUCTURE_FILL_MODEL"],
                "latency_model_refs": ["PR168_RP_LATENCY_BUDGET"],
                "capacity_model_refs": ["PR168_RP_CAPACITY_CROWDING"],
                "portfolio_utility_model_refs": ["PR168_RP_PORTFOLIO_MARGINAL_UTILITY"],
                "overfit_fdr_model_refs": ["PR168_RP_OVERFIT_FDR_PROXY"],
                "scenario_ladder_refs": ["PR168_RP_SCENARIO_LADDER"],
                "order_policy_refs": _as_list(combo.get("order_policy_refs")) or ["NO_TRADE", "PASSIVE_LIMIT", "AGGRESSIVE_CROSS"],
                "risk_sizing_refs": ["PR168_RP_ORDER_TYPE_SIZING_PRICE_CANDIDATE_REPAIR"],
                "quantum_structural_optimizer_refs_when_applicable": _as_list(row.get("quantum_objective_ref")),
                "classical_fallback_optimizer_refs": ["PR168_RP_CLASSICAL_FALLBACK_ONLY"],
                "interpret_back_refs": ["PR168_RANK_STACK_INTERPRET_BACK_MAP"],
                "candidate_stack_class": "negative_recovery_strategy"
                if row.get("computed_status") == "COMPUTED_NEGATIVE_EDGE"
                else "portfolio_aware_stack",
                "role_completeness_status": "COMPLETE_FOR_NONLIVE_RANKING",
                "core_role_gap_refs": [],
                "stack_synergy_edge": 0.0,
                "dominance_pruned_flag": False,
                "search_budget_class": "DETERMINISTIC_BEAM_SAFE_SMALL",
                "upstream_numeric_evidence_refs": [row.get("result_ref")],
                "upstream_gap_refs": [],
                "authority_boundary_flags": authority_flags(),
            }
        )
    return stacks


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]
    if value == "":
        return []
    return [value]
