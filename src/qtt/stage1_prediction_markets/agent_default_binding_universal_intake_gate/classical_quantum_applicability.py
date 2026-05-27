"""Classical, quantum, and hybrid applicability mapping for PR156."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def applicability_for_pr155_record(record: Mapping[str, Any]) -> str:
    state = str(record.get("quantum_forward_compatibility_state") or "")
    hint = str(record.get("quantum_applicability_hint") or "")
    if state == "QUANTUM_NOT_APPLICABLE_CLASSICAL_ONLY":
        return c.CLASSICAL_ONLY
    if "QUBO" in hint:
        return c.QUBO_COMPATIBLE
    if "ISING" in hint:
        return c.ISING_COMPATIBLE
    if "QAOA" in hint:
        return c.QAOA_COMPATIBLE
    if "VQE" in hint:
        return c.VQE_COMPATIBLE
    if "ANNEAL" in hint:
        return c.ANNEALING_COMPATIBLE
    if "QUANTUM" in state or "QUANTUM" in hint:
        return c.QUANTUM_APPLICABLE
    return c.APPLICABILITY_PENDING_CLASSIFICATION


def applicability_for_template(template_type: str) -> str:
    mapping = {
        c.QUANTUM_INSPIRED_OPTIMIZER_TEMPLATE: c.QUANTUM_INSPIRED,
        c.TRUE_QUANTUM_OPTIMIZER_TEMPLATE: c.TRUE_QUANTUM,
        c.HYBRID_CLASSICAL_QUANTUM_ALGORITHM_TEMPLATE: c.HYBRID_CLASSICAL_QUANTUM,
        c.QUBO_COMPATIBLE_TEMPLATE: c.QUBO_COMPATIBLE,
        c.ISING_COMPATIBLE_TEMPLATE: c.ISING_COMPATIBLE,
        c.QAOA_COMPATIBLE_TEMPLATE: c.QAOA_COMPATIBLE,
        c.VQE_COMPATIBLE_TEMPLATE: c.VQE_COMPATIBLE,
        c.ANNEALING_COMPATIBLE_TEMPLATE: c.ANNEALING_COMPATIBLE,
        c.QUANTUM_PORTFOLIO_OPTIMIZATION_TEMPLATE: (
            c.QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE
        ),
        c.UNKNOWN_RESEARCH_CANDIDATE_BLOCKED_TEMPLATE: (
            c.APPLICABILITY_BLOCKED_INSUFFICIENT_EVIDENCE
        ),
    }
    if template_type in c.CLASSICAL_TEMPLATE_TYPES:
        return c.CLASSICAL_ONLY
    return mapping.get(template_type, c.APPLICABILITY_PENDING_CLASSIFICATION)


def owner_priority_state_for_template(template_type: str) -> str:
    if template_type in c.CLASSICAL_TEMPLATE_TYPES:
        return c.OWNER_CLASSICAL_ALLOWED
    if template_type in c.QUANTUM_TEMPLATE_TYPES:
        return c.OWNER_QUANTUM_ALLOWED
    if template_type in c.HYBRID_TEMPLATE_TYPES:
        return c.OWNER_HYBRID_COMPARE_ALLOWED
    return c.STRATEGY_PRIORITY_PENDING_OWNER_POLICY
