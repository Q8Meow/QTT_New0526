"""Quantum strategy candidate registry construction."""

from __future__ import annotations

from . import constants as c


def build_strategy_candidates(atomicrow_ids: list[str], pr154_ids: list[str]) -> list[dict[str, object]]:
    profile_types = [
        "QUBO_PARAMETER_STACK_SELECTION_CANDIDATE",
        "QUBO_MARKET_SELECTION_CANDIDATE",
        "QUBO_CAPITAL_ALLOCATION_CANDIDATE",
        "VQE_PORTFOLIO_OBJECTIVE_CANDIDATE",
        "QUBO_ARBITRAGE_CANDIDATE",
        "QAOA_SIGNAL_COMBINATION_CANDIDATE",
        "ANNEALING_LATENCY_AWARE_ROUTING_CANDIDATE",
        "HYBRID_QUANTUM_TIEBREAKER_CANDIDATE",
    ]
    return [
        {
            "strategy_candidate_id": f"PR161A_STRATEGY__{strategy_type}",
            "strategy_class": strategy_type,
            "market_type": "PREDICTION_MARKETS_GENERAL",
            "platform_scope": "KALSHI_POLYMARKET_FORECASTEX_IBKR_GENERAL",
            "optimizer_family": profile_types[index].split("_", 1)[0],
            "quantum_profile_type": profile_types[index],
            "objective_template_id": f"PR161A_FORMULA_TEMPLATE__{_template_for(profile_types[index])}",
            "default_parameter_profile_id": f"PR161A_DEFAULT_PROFILE__{_default_family(profile_types[index])}",
            "AtomicRows row IDs": atomicrow_ids[index : index + 8],
            "PR154 target IDs": pr154_ids[index : index + 3],
            "source/prior PR provenance": [
                "PR82_PR86_QUANTUM_SCORING_OPTIMIZER_ARTIFACTS",
                "PR136_ROUTE_TRIAGE",
                "PR159S_OPEN_RESEARCH_CANDIDATES",
            ],
            "QTT agent consumers": list(c.DOWNSTREAM_AGENT_ROLES),
            "replay/paper experiment descriptor": f"PR161A_QEXP__{index+1:04d}",
            "downstream PR route": list(c.PR87_PR92_FLOW),
            "expected latency feasibility class": "REPLAY_PAPER_ONLY_LATENCY_FEASIBILITY_UNKNOWN",
            "expected use lane": "RESEARCH_SCORING_OPTIMIZER_PREP_REPLAY_PAPER",
            "classical baseline comparator": "PR161A_CLASSICAL_BASELINE_GREEDY_LINEAR_COST",
            "hybrid arbitration profile": "PR161A_HYBRID_ARBITRATION_PROFILE",
            "promotion limitations": c.NON_LIVE_PROMOTION_LIMITATION,
        }
        for index, strategy_type in enumerate(c.QUANTUM_STRATEGY_CANDIDATE_TYPES)
    ]


def _template_for(profile_type: str) -> str:
    if profile_type.startswith("QAOA"):
        return "QAOA_CANDIDATE_TEMPLATE"
    if profile_type.startswith("VQE"):
        return "VQE_CANDIDATE_TEMPLATE"
    if profile_type.startswith("ANNEALING"):
        return "ANNEALING_CANDIDATE_TEMPLATE"
    if profile_type.startswith("HYBRID"):
        return "QUANTUM_TIEBREAKER_TEMPLATE"
    return "QUBO_OBJECTIVE_TEMPLATE"


def _default_family(profile_type: str) -> str:
    if profile_type.startswith("HYBRID"):
        return "HYBRID"
    return profile_type.split("_", 1)[0]

