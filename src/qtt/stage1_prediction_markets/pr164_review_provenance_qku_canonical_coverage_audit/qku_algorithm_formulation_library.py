"""Algorithm and solver labels used by PR164 materialization records."""

from __future__ import annotations


def solver_family_for(candidate_type: str, domain_family: str) -> str:
    candidate_type = str(candidate_type or "")
    domain_family = str(domain_family or "")
    if candidate_type == "QUANTUM_FORMULATION" or "quantum" in domain_family:
        return "CLASSICAL_QUBO_CQM_MAPPER_NO_BACKEND"
    if candidate_type == "ALGORITHM":
        return "DETERMINISTIC_PROCEDURAL_SOLVER"
    if candidate_type == "PARAMETER_PACK":
        return "STATIC_PARAMETER_DOMAIN_EVALUATOR"
    return "CLOSED_FORM_DETERMINISTIC_ARITHMETIC"


def algorithm_family_for(candidate: dict[str, object]) -> str:
    return str(
        candidate.get("algorithm_family")
        or candidate.get("formula_family")
        or candidate.get("domain_family_key")
        or "generic_candidate_formula_family"
    )
