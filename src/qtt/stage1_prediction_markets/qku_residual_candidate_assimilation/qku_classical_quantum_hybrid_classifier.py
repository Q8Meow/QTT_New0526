"""Classical, quantum, and hybrid QKU classification."""

from __future__ import annotations


def classify_computation(payload: dict[str, object]) -> dict[str, object]:
    explicit_family = str(
        payload.get("_pr161b_quantum_candidate_family")
        or payload.get("quantum_candidate_family")
        or ""
    ).upper()
    explicit_profile = str(
        payload.get("_pr161b_quantum_profile_type")
        or payload.get("quantum_profile_type")
        or ""
    ).upper()
    qclass = str(payload.get("quantum_applicability_class") or "").upper()
    text = " ".join(
        str(payload.get(key) or "")
        for key in (
            "candidate_family",
            "candidate_type",
            "quantum_profile_type",
            "quantum_candidate_family",
            "formula_template_type",
            "strategy_candidate_type",
            "value_authority_class",
            "aggregate_value_state",
        )
    ).upper()
    pr161a_quantum_ready = bool(payload.get("quantum_relevant_candidate_flag"))
    explicit_not_quantum = qclass == "NOT_QUANTUM_APPLICABLE"
    quantum_text = bool(explicit_family) or pr161a_quantum_ready or (
        not explicit_not_quantum
        and any(token in text for token in ("QUANTUM", "QUBO", "ISING", "QAOA", "VQE", "ANNEAL"))
    )
    hybrid_required = bool(payload.get("hybrid_arbitration_required_flag")) or bool(
        payload.get("optimizer_arbitration_required_flag")
    )
    if explicit_family == "HYBRID":
        klass = "HYBRID_CLASSICAL_QUANTUM_QKU"
    elif pr161a_quantum_ready:
        klass = "QUANTUM_INSPIRED_QKU"
    elif quantum_text:
        klass = "QUANTUM_QKU"
    elif any(token in text for token in ("OPTIMIZER", "ALGORITHM", "SCORING", "RANKING")):
        klass = "CLASSICAL_QKU"
    else:
        klass = "CLASSICAL_QKU"
    subclass = "QUANTUM_ADVISORY_QKU"
    family_profile_text = f"{explicit_family} {explicit_profile} {text}"
    if "QUBO" in family_profile_text:
        subclass = "QUBO_QKU"
    elif "ISING" in family_profile_text:
        subclass = "ISING_QKU"
    elif "QAOA" in family_profile_text:
        subclass = "QAOA_QKU"
    elif "VQE" in family_profile_text:
        subclass = "VQE_QKU"
    elif "ANNEAL" in family_profile_text:
        subclass = "ANNEALING_QKU"
    elif "PORTFOLIO" in family_profile_text:
        subclass = "QUANTUM_PORTFOLIO_QKU"
    elif "CAPITAL" in family_profile_text:
        subclass = "QUANTUM_CAPITAL_ALLOCATION_QKU"
    elif "LATENCY" in family_profile_text:
        subclass = "QUANTUM_LATENCY_ROUTING_QKU"
    elif "ARBITRAGE" in family_profile_text:
        subclass = "QUANTUM_ARBITRAGE_PATH_QKU"
    elif explicit_family == "HYBRID":
        subclass = "HYBRID_QUANTUM_CLASSICAL_QKU"
    return {
        "qku_classical_quantum_hybrid_class": klass,
        "qku_quantum_applicability": "QUANTUM_APPLICABLE" if quantum_text else "CLASSICAL_BASELINE_APPLICABLE",
        "qku_quantum_subclass": subclass if quantum_text else None,
        "qku_classical_baseline_required_flag": True,
        "qku_hybrid_arbitration_required_flag": hybrid_required or quantum_text,
    }
