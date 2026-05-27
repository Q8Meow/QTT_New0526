"""Future scoring, optimizer, and replay/paper routing hints for PR156."""

from __future__ import annotations

from . import constants as c


def optimizer_hint_for_template(template_type: str) -> str:
    if template_type == c.CLASSICAL_OPTIMIZER_METHOD_TEMPLATE:
        return c.CLASSICAL_OPTIMIZER_CANDIDATE_FOR_FUTURE_ADAPTER
    if template_type == c.QUANTUM_INSPIRED_OPTIMIZER_TEMPLATE:
        return c.QUANTUM_INSPIRED_OPTIMIZER_CANDIDATE_FOR_FUTURE_ADAPTER
    if template_type in {
        c.TRUE_QUANTUM_OPTIMIZER_TEMPLATE,
        c.QUBO_COMPATIBLE_TEMPLATE,
        c.ISING_COMPATIBLE_TEMPLATE,
        c.QAOA_COMPATIBLE_TEMPLATE,
        c.VQE_COMPATIBLE_TEMPLATE,
        c.ANNEALING_COMPATIBLE_TEMPLATE,
        c.QUANTUM_PORTFOLIO_OPTIMIZATION_TEMPLATE,
    }:
        return c.TRUE_QUANTUM_OPTIMIZER_CANDIDATE_FOR_FUTURE_BACKEND_GATE
    if template_type == c.HYBRID_CLASSICAL_QUANTUM_ALGORITHM_TEMPLATE:
        return c.HYBRID_COMPARE_CANDIDATE_FOR_FUTURE_ARBITRATION
    if template_type == c.UNKNOWN_RESEARCH_CANDIDATE_BLOCKED_TEMPLATE:
        return c.OPTIMIZER_ROUTING_BLOCKED
    return c.OPTIMIZER_NOT_EXECUTED_IN_PR156


def population_optimizer_hint(applicability_class: str) -> str:
    if applicability_class == c.CLASSICAL_ONLY:
        return c.OPTIMIZER_NOT_EXECUTED_IN_PR156
    if applicability_class in {
        c.QUANTUM_APPLICABLE,
        c.QUANTUM_INSPIRED,
        c.TRUE_QUANTUM,
        c.QUBO_COMPATIBLE,
        c.ISING_COMPATIBLE,
        c.QAOA_COMPATIBLE,
        c.VQE_COMPATIBLE,
        c.ANNEALING_COMPATIBLE,
        c.QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE,
    }:
        return c.OPTIMIZER_ROUTING_PENDING_CLASSIFICATION
    return c.OPTIMIZER_NOT_EXECUTED_IN_PR156


def replay_paper_hint_for_template(template_type: str) -> str:
    if template_type == c.UNKNOWN_RESEARCH_CANDIDATE_BLOCKED_TEMPLATE:
        return c.REPLAY_PAPER_BLOCKED
    return c.REPLAY_PAPER_PENDING_SOURCE_EVIDENCE


def scoring_readiness_for_template(template_type: str) -> str:
    if template_type == c.UNKNOWN_RESEARCH_CANDIDATE_BLOCKED_TEMPLATE:
        return c.SCORING_RANKING_BLOCKED
    return c.SCORING_RANKING_PENDING_SOURCE_EVIDENCE
