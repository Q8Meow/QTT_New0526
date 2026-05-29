"""Quantum residual expansion and PR161A quantum coverage projection."""

from __future__ import annotations

from typing import Any

from . import constants as c


def build_quantum_residual_records(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.get("quantum_applicability_class") == c.QuantumApplicabilityClass.NOT_QUANTUM_APPLICABLE.value:
            continue
        family = _family(candidate)
        requires_queue = bool(candidate.get("pr161c_assimilation_required_flag"))
        output.append(
            {
                "quantum_residual_id": f"PR161B_QUANTUM_RESIDUAL__{candidate['residual_candidate_id']}",
                "residual_candidate_id": candidate["residual_candidate_id"],
                "extracted_text": candidate["extracted_text"],
                "normalized_quantum_name": candidate["normalized_candidate_name"],
                "quantum_candidate_family": family,
                "quantum_optimizer_family": candidate.get("optimizer_family_if_available") or family,
                "quantum_profile_type": _profile_type(candidate, family),
                "formula_template_type": _formula_template(family),
                "strategy_candidate_type": _strategy_type(candidate, family),
                "variable_domain": _variable_domain(family),
                "objective_terms": _objective_terms(candidate, family),
                "constraint_terms": _constraint_terms(candidate, family),
                "penalty_terms": _penalty_terms(candidate, family),
                "default_value_if_available": candidate.get("default_value_if_available"),
                "default_range_if_available": _range(candidate),
                "parameter_range_if_available": _range(candidate),
                "unit_if_available": candidate.get("unit_if_available"),
                "scale_if_available": candidate.get("scale_if_available"),
                "source_section_id": candidate["master_plan_section_id"],
                "source_artifact_path": candidate["extraction_source_path"],
                "source_line_or_locator_if_available": candidate.get("source_line_or_locator_if_available"),
                "extraction_pass_ids": candidate.get("extraction_pass_ids", []),
                "upstream_pr82_pr86_mapping": ["PR82_PR86_QUANTUM_SCORING_OPTIMIZER_TAXONOMY"],
                "upstream_pr161a_quantum_candidate_ids": candidate.get("covered_by_quantum_candidate_ids", []),
                "upstream_pr161a_formula_template_ids": _formula_ids(family, candidate),
                "upstream_pr161a_strategy_candidate_ids": _strategy_ids(family, candidate),
                "upstream_pr161a_replay_paper_descriptor_ids": candidate.get("covered_by_replay_paper_route_ids", []),
                "atomicrows_row_ids": candidate.get("covered_by_atomicrows_row_ids", []),
                "pr154_target_ids": candidate.get("covered_by_pr154_target_ids", []),
                "classical_baseline_required_flag": True,
                "hybrid_arbitration_required_flag": True,
                "replay_paper_required_flag": True,
                "downstream_pr87_pr92_route": list(c.PR87_PR92_FLOW),
                "downstream_qtt_agent_roles": candidate.get("downstream_agent_roles", []),
                "coverage_state": _quantum_coverage_state(candidate, family),
                "coverage_match_tier": candidate.get("coverage_match_tier"),
                "residual_gap_type": candidate.get("residual_gap_type"),
                "recommended_fill_lane": candidate.get("recommended_fill_lane") or c.AssimilationFillLane.REJECT_DUPLICATE_ALREADY_COVERED.value,
                "pr161c_quantum_assimilation_required_flag": requires_queue,
                "pr161c_quantum_assimilation_queue_id_if_needed": f"PR161C_QUANTUM_QUEUE__{candidate['residual_candidate_id']}" if requires_queue else None,
                "optimizer_execution_evidence_created_flag": False,
                "quantum_backend_execution_evidence_created_flag": False,
                "quantum_advantage_evidence_created_flag": False,
                "profit_evidence_created_flag": False,
                "live_use_allowed_flag": False,
            }
        )
    return output


def _family(candidate: dict[str, Any]) -> str:
    family = str(candidate.get("candidate_family") or "QUANTUM")
    if family in {"QUBO", "ISING", "QAOA", "VQE", "ANNEALING", "HYBRID"}:
        return family
    if "ANNEAL" in str(candidate.get("candidate_type")):
        return "ANNEALING"
    return "QUANTUM"


def _profile_type(candidate: dict[str, Any], family: str) -> str:
    strategy = str(candidate.get("strategy_class") or "GENERAL").upper()
    return f"{family}_{strategy}_RESIDUAL_CANDIDATE"


def _formula_template(family: str) -> str:
    return {
        "QUBO": "QUBO_OBJECTIVE_TEMPLATE",
        "ISING": "ISING_OBJECTIVE_TEMPLATE",
        "QAOA": "QAOA_CANDIDATE_TEMPLATE",
        "VQE": "VQE_CANDIDATE_TEMPLATE",
        "ANNEALING": "ANNEALING_CANDIDATE_TEMPLATE",
        "HYBRID": "HYBRID_COMPARE_THEN_SELECT_TEMPLATE",
    }.get(family, "QUANTUM_TIEBREAKER_TEMPLATE")


def _strategy_type(candidate: dict[str, Any], family: str) -> str:
    strategy = str(candidate.get("strategy_class") or "GENERAL").upper()
    return f"QUANTUM_{strategy}_CANDIDATE" if family != "HYBRID" else "QUANTUM_OWNER_PRIORITY_TIEBREAKER_CANDIDATE"


def _variable_domain(family: str) -> str:
    if family == "ISING":
        return "SPIN_MINUS_ONE_PLUS_ONE"
    if family in {"QUBO", "QAOA", "ANNEALING"}:
        return "BINARY_ZERO_ONE"
    return "PARAMETERIZED_CONTINUOUS_OR_BINARY_CANDIDATE"


def _objective_terms(candidate: dict[str, Any], family: str) -> list[str]:
    text = str(candidate.get("extracted_text", ""))
    if candidate.get("formula_expression_if_available"):
        return [str(candidate["formula_expression_if_available"])]
    if family == "QUBO":
        return ["linear_reward", "quadratic_interaction", "transaction_cost", "latency_penalty"]
    if family == "ISING":
        return ["h_bias", "j_coupling", "risk_energy", "latency_energy"]
    return [text[:120]]


def _constraint_terms(candidate: dict[str, Any], family: str) -> list[str]:
    terms = ["budget_constraint", "exposure_constraint"]
    if family in {"QUBO", "ISING"}:
        terms.append("penalty_encoded_constraint")
    if candidate.get("constraint_expression_if_available"):
        terms.append(str(candidate["constraint_expression_if_available"]))
    return terms


def _penalty_terms(candidate: dict[str, Any], family: str) -> list[str]:
    terms = ["risk_penalty", "latency_penalty", "liquidity_penalty"]
    if family == "QUBO":
        terms.append("one_hot_penalty")
    return terms


def _range(candidate: dict[str, Any]) -> str | None:
    lower = candidate.get("lower_bound_if_available")
    upper = candidate.get("upper_bound_if_available")
    if lower is None and upper is None:
        return None
    return f"{lower or ''}..{upper or ''}"


def _formula_ids(family: str, candidate: dict[str, Any]) -> list[str]:
    return [f"PR161A_FORMULA_TEMPLATE__{_formula_template(family)}"] if candidate.get("covered_by_quantum_candidate_ids") else []


def _strategy_ids(family: str, candidate: dict[str, Any]) -> list[str]:
    return [f"PR161A_STRATEGY__{_strategy_type(candidate, family)}"] if candidate.get("covered_by_quantum_candidate_ids") else []


def _quantum_coverage_state(candidate: dict[str, Any], family: str) -> str:
    if candidate.get("coverage_state") == c.CoverageState.COVERED_BY_PR161A_QUANTUM_PROFILE.value:
        return c.QuantumResidualCoverageState.QUANTUM_RESIDUAL_COVERED_BY_PR161A_PROFILE.value
    if candidate.get("pr161c_assimilation_required_flag"):
        return c.QuantumResidualCoverageState.QUANTUM_RESIDUAL_NEW_CANDIDATE_REQUIRED.value
    if family == "QUANTUM":
        return c.QuantumResidualCoverageState.QUANTUM_RESIDUAL_COVERED_BY_PR82_PR86_ARTIFACT.value
    return c.QuantumResidualCoverageState.QUANTUM_RESIDUAL_COVERED_BY_CANONICAL_ALIAS.value
