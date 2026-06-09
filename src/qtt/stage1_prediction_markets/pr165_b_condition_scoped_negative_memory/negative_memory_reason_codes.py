"""Central PR165-B reason codes and literal-scan policy."""

from __future__ import annotations


NEGATIVE_MEMORY_REASON_CODES = (
    "PR165_B_COST_DEGRADATION",
    "PR165_B_LATENCY_DEGRADATION",
    "PR165_B_LIQUIDITY_DEGRADATION",
    "PR165_B_ADVERSE_SELECTION_DEGRADATION",
    "PR165_B_MODEL_RISK_DEGRADATION",
    "PR165_B_SOURCE_PROVENANCE_WEAKNESS",
    "PR165_B_REPAIR_CONFIDENCE_WEAKNESS",
    "PR165_B_YES_NO_COMPLEMENT_INCONSISTENCY",
    "PR165_B_CAPITAL_LOCK_COST",
    "PR165_B_PORTFOLIO_CROWDING",
    "PR165_B_DUPLICATE_EDGE",
    "PR165_B_FALSE_DISCOVERY_RISK",
    "PR165_B_SPARSE_REGIME_EVIDENCE",
    "PR165_B_QUANTUM_FORMULATION_WEAKNESS",
    "PR165_B_QUANTUM_CLASSICAL_COMPARATOR_WEAKNESS",
    "PR165_B_POSITIVE_CONDITION_SCOPED_MEMORY",
    "PR165_B_FRAGILE_CONDITION_SCOPED_MEMORY",
    "PR165_B_REPLAY_PAPER_RETEST_ROUTE",
    "PR165_B_REPAIR_ROUTE_REQUIRED",
)

COUNTERFACTUAL_ATTRIBUTION_FAMILIES = (
    "fees",
    "spread",
    "slippage",
    "latency_adverse_selection",
    "queue_nonfill",
    "maker_taker_route_error",
    "liquidity_depth",
    "time_to_resolution",
    "settlement_delay",
    "stale_data",
    "probability_calibration",
    "replay_paper_divergence",
    "stress_failure",
    "model_risk",
    "source_provenance",
    "repair_confidence",
    "formula_complexity",
    "portfolio_crowding",
    "duplicate_edge",
    "yes_no_complement_inconsistency",
    "capital_lock",
    "false_discovery_adjustment",
    "sparse_regime_uncertainty",
    "quantum_objective_gap",
    "quantum_constraint_gap",
    "quantum_penalty_model_gap",
    "quantum_binary_expansion_gap",
    "quantum_classical_comparator_gap",
)

SCATTERED_LITERAL_SCAN_EXCLUDED_PATH_NAMES = (
    "negative_memory_reason_codes.py",
    "negative_memory_status_vocab.py",
    "negative_memory_action_policy.py",
    "condition_scope_vocab.py",
    "retest_cooldown_vocab.py",
    "evidence_sufficiency_vocab.py",
    "false_discovery_vocab.py",
    "memory_decay_vocab.py",
    "negative_memory_authority_policy.py",
)

FORBIDDEN_SCATTERED_LITERALS = (
    "blocked",
    "unknown",
    "future work",
    "metadata only",
    "placeholder only",
    "permanent ban",
    "not ready",
)
