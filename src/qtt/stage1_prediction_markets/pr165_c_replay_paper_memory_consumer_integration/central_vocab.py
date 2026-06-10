"""Central PR165-C vocabulary and deterministic default weights."""

from __future__ import annotations

PR_ID = "PR165-C"
EXPECTED_BRANCH = "pr165-c-replay-paper-memory-consumer-integration"
AUTHORITY_CLASS = "PR165_C_REPLAY_PAPER_MEMORY_CONSUMER_ONLY"
AUTHORITY_BOUNDARY_REF = "PR165_C_AUTHORITY_BOUNDARY::REPLAY_PAPER_MEMORY_CONSUMER_ONLY"
VALIDATION_STATUS = "PASS"

UPSTREAM_PR_REFS = (
    "PR161D",
    "PR163",
    "PR163-B",
    "PR164",
    "PR163-C",
    "PR165",
    "PR165-B",
)
DOWNSTREAM_PR_ROUTES = (
    "PR162D-R3",
    "PR162E",
    "PR162E-Q",
    "PR165-D",
    "PR166-S",
    "PR166-Q",
    "PR171/PR172",
    "dashboard_agent",
    "governance_agent",
    "commander_agent",
)

INTERNAL_WORKFLOW_ROLES = (
    "PRODUCER",
    "CONSUMER",
    "VALIDATOR",
    "REVIEWER",
    "INDEPENDENT_CHALLENGER",
    "ESCALATION_OWNER",
    "DASHBOARD_VIEWER",
    "COMMANDER_COORDINATOR",
    "FALLBACK_OWNER",
    "MATERIALIZATION_OWNER",
    "RETEST_OWNER",
    "REPAIR_OWNER",
    "REFRESH_OWNER",
    "TASK_OWNER",
    "TASK_RECEIPT_OWNER",
)

AGENT_IDS = (
    "scoring_agent",
    "memory_agent",
    "risk_agent",
    "tca_agent",
    "latency_agent",
    "liquidity_agent",
    "quantum_mapper_advisory_agent",
    "replay_agent",
    "paper_agent",
    "repair_agent",
    "dashboard_agent",
    "governance_agent",
    "commander_agent",
)

SCENARIO_MEMORY_ROUTES = (
    "POSITIVE_CONDITION_SCOPED_PREFERENCE",
    "NEGATIVE_CONDITION_SCOPED_AVOIDANCE",
    "FRAGILE_WATCHLIST",
    "CONTRADICTORY_EVIDENCE_RETEST",
    "STALE_MEMORY_RETEST",
    "REPAIR_DEPENDENT_MEMORY",
    "QUANTUM_FORMULATION_DEPENDENT_MEMORY",
    "INSUFFICIENT_EVIDENCE_MATERIALIZATION",
)

TASK_TYPES = (
    "COMPUTABLE_PAYLOAD_REVIEW",
    "FORMULA_TEST_VECTOR_REVIEW",
    "MISSING_VALUE_MATERIALIZATION",
    "REPLAY_RETEST_QUEUE",
    "PAPER_RETEST_QUEUE",
    "REPAIR_BEFORE_RETEST",
    "TCA_REPAIR",
    "LATENCY_REPAIR",
    "LIQUIDITY_REPAIR",
    "QUANTUM_FORMULATION_REPAIR",
    "MODEL_QUALITY_CHALLENGE",
    "DASHBOARD_REVIEW",
    "GOVERNANCE_REVIEW",
    "COMMANDER_ESCALATION",
    "SCORE_MEMORY_REFRESH_HANDOFF",
)

RETEST_PRIORITY_BUCKETS = (
    "URGENT_RETEST_HIGH_VALUE_LOW_CONFIDENCE",
    "REPAIR_THEN_RETEST",
    "MISSING_VALUE_MATERIALIZATION_THEN_RETEST",
    "QUANTUM_FORMULATION_REPAIR_THEN_RETEST",
    "WATCH_RETEST",
    "LOW_PRIORITY_RETEST",
    "NO_RETEST_REQUIRED_WITH_REASON",
)

REFRESH_TRIGGERS = (
    "NEW_REPLAY_RETEST_RESULT",
    "NEW_PAPER_RETEST_RESULT",
    "REPAIR_COMPLETED",
    "TCA_COMPONENT_REPAIRED",
    "LATENCY_BUCKET_CHANGED",
    "LIQUIDITY_BUCKET_CHANGED",
    "MODEL_QUALITY_REVIEW_COMPLETED",
    "SOURCE_PROVENANCE_IMPROVED",
    "MISSING_VALUE_MATERIALIZED",
    "QUANTUM_FORMULATION_REPAIRED",
    "MEMORY_DECAY_EXPIRED",
    "REGIME_CHANGED",
)

NO_ORPHAN_STATUS = "NO_ORPHAN_ROUTE_COMPLETE"
PROVENANCE_LABEL = "UPSTREAM_PR165_PR165_B_DERIVED"
CONFIDENCE_TIER = "INTERNAL_CANDIDATE_HIGH"
REPLAY_PAPER_ROUTE = "REPLAY_PAPER_RETEST_OR_REVIEW_QUEUE"

RETEST_PRIORITY_WEIGHTS = {
    "W_GLOBAL_RANK": 0.14,
    "W_REGIME_RANK": 0.10,
    "W_EV": 0.15,
    "W_NET_EDGE": 0.12,
    "W_RECURRENCE": 0.08,
    "W_CONFIDENCE_DECAY": 0.08,
    "W_REPAIR_READY": 0.07,
    "W_PROVENANCE": 0.07,
    "W_QUANTUM_PRIORITY": 0.06,
    "W_TCA_DRAG": 0.04,
    "W_LATENCY_DRAG": 0.03,
    "W_LIQUIDITY_FRAGILITY": 0.03,
    "W_ADVERSE_SELECTION": 0.03,
    "W_MODEL_QUALITY": 0.03,
    "W_QUANTUM_WEAKNESS": 0.03,
}

FORMULA_TEMPLATE_IDS = (
    "implied_yes_probability_mid",
    "implied_no_probability_mid",
    "yes_expected_value",
    "no_expected_value",
    "fee_adjusted_edge",
    "slippage_adjusted_edge",
    "tca_adjusted_edge",
    "latency_adjusted_edge",
    "liquidity_fragility_score",
    "scenario_memory_adjusted_priority",
    "fractional_kelly_research_sizing_candidate",
    "calibration_error_candidate",
    "cross_venue_discrepancy_candidate",
    "retest_priority_score",
)
