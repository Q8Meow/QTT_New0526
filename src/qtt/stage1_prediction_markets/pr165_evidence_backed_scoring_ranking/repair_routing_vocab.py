"""Central PR165 repair-routing vocabulary."""

from __future__ import annotations


POST_LAUNCH_REPAIR_STATES = (
    "NO_REPAIR_REQUIRED",
    "REPAIR_REQUIRED_REPLAY_PAPER_ONLY",
    "REPAIR_REQUIRED_CACHE_BEFORE_RUNTIME",
    "REPAIR_REQUIRED_CONTROL_PLANE_ONLY",
    "REPAIR_REQUIRED_ACQUISITION_EXPANSION",
    "REPAIR_REQUIRED_FORMULA_MATERIALIZATION",
    "REPAIR_REQUIRED_QUANTUM_FORMULATION",
    "REPAIR_REQUIRED_MODEL_RISK_REVIEW",
    "REPAIR_REQUIRED_CONDITION_SCOPED_NEGATIVE_MEMORY",
    "REPAIRED_PENDING_RETEST",
    "REPAIRED_RETEST_PASSED",
    "REPAIRED_RETEST_FAILED",
    "ARCHIVED_AFTER_REPEATED_FAILURE",
)

REPAIR_REASON_CODES = (
    "MISSING_OR_WEAK_FEE_SPREAD_LIQUIDITY_LATENCY_VALUE",
    "REPLAY_PAPER_ALIGNMENT_WEAK",
    "TCA_WIPES_OUT_RAW_EDGE",
    "LATENCY_NOT_HOT_PATH_SAFE",
    "SOURCE_PROVENANCE_WEAK",
    "FORMULA_OR_TEST_VECTOR_MATERIALIZATION_WEAK",
    "QUANTUM_OBJECTIVE_CONSTRAINTS_NEED_FORMULATION",
    "CONDITION_SCOPED_NEGATIVE_MEMORY_CANDIDATE",
    "MODEL_RISK_REVIEW_REQUIRED",
    "DUPLICATE_OR_CROWDED_EDGE",
    "LOW_REPAIR_CONFIDENCE",
)

REPAIR_AGENTS = (
    "acquisition_repair_agent",
    "formula_materialization_agent",
    "tca_repair_agent",
    "latency_repair_agent",
    "liquidity_repair_agent",
    "model_risk_agent",
    "quantum_mapper_advisory_agent",
    "negative_memory_agent",
    "dashboard_governance_agent",
    "replay_paper_agent",
    "portfolio_cluster_agent",
    "source_candidate_research_agent",
)

BASE_AGENT_ROUTES = (
    "pr165_scoring_agent",
    "risk_agent",
    "latency_agent",
    "tca_agent",
    "replay_agent",
    "paper_agent",
    "quantum_mapper_advisory_agent",
    "pr165b_negative_memory_agent",
    "plugin_future_agent",
    "dashboard_future_consumer",
    "governance_agent",
    "commander_agent",
)

DOWNSTREAM_CONSUMERS = (
    "PR165_B",
    "PR162D-R3",
    "PR162E",
    "PR162E-Q",
    "PR166-L",
    "dashboard_future_consumer",
    "governance_agent",
    "commander_agent",
)
