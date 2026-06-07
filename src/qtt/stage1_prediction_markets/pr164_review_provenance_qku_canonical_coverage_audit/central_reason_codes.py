"""Central enums and reason codes for PR164.

Every blocker, route, disposition, source class, and authority decision used by
the PR164 pipeline is declared here. Other modules import these values instead
of inventing local vocabularies.
"""

from __future__ import annotations

from typing import Final


REVIEW_STATUSES: Final[tuple[str, ...]] = (
    "REVIEW_READY_FOR_PR165",
    "REVIEW_PARTIAL_WITH_EXACT_REASON",
    "REVIEW_REPAIR_REQUIRED_BEFORE_PR165",
    "REVIEW_DORMANT_NON_STAGE1",
    "REVIEW_SOURCE_ENRICHMENT_REQUIRED",
    "REVIEW_FORMULA_COVERAGE_REPAIR_REQUIRED",
    "REVIEW_MARKET_SCOPE_REPAIR_REQUIRED",
    "REVIEW_OWNER_REVIEW_REQUIRED",
)

COMPUTABILITY_DISPOSITIONS: Final[tuple[str, ...]] = (
    "COMPUTABLE_NOW",
    "COMPUTABLE_WITH_CANDIDATE_VALUES_FOR_REPLAY_PAPER",
    "COMPUTABLE_AFTER_EXACT_MISSING_VALUE_FILL",
    "COMPUTABLE_AFTER_FORMULA_FAMILY_EXPANSION",
    "COMPUTABLE_AFTER_MARKET_SCOPE_REPAIR",
    "DORMANT_NON_STAGE1_BUT_COMPUTABLE",
    "QUARANTINED_UNSAFE",
    "QUARANTINED_DUPLICATE",
    "QUARANTINED_IRRELEVANT",
    "QUARANTINED_IMPOSSIBLE_TO_MAP",
)

PROHIBITED_DISPOSITIONS: Final[tuple[str, ...]] = (
    "METADATA_ONLY",
    "PLACEHOLDER_ONLY",
    "FUTURE_CONSUMER_ONLY",
    "SOLVER_COMPATIBLE_LABEL_ONLY",
    "UNKNOWN_WITHOUT_ROUTE",
    "BLOCKED_WITHOUT_EXACT_REASON",
    "EMPTY_FORMULA_REF",
    "EMPTY_AGENT_ROUTE",
    "EMPTY_REPLAY_PAPER_ROUTE",
)

MARKET_SCOPES: Final[tuple[str, ...]] = (
    "PREDICTION_MARKET_BINARY_EVENT_CONTRACT",
    "PREDICTION_MARKET_MULTIOUTCOME_EVENT_CONTRACT",
    "PREDICTION_MARKET_SCALAR_RANGE_CONTRACT",
    "MARKET_AGNOSTIC_MATH",
    "MARKET_AGNOSTIC_RISK",
    "MARKET_AGNOSTIC_OPTIMIZER",
    "MARKET_AGNOSTIC_GOVERNANCE",
    "EQUITY",
    "OPTIONS",
    "FUTURES",
    "CRYPTO",
    "FX",
    "RATES",
    "COMMODITIES",
    "NON_STAGE1_OTHER",
    "UNKNOWN_MARKET_SCOPE_OWNER_REVIEW",
)

ACTIVATION_STATES: Final[tuple[str, ...]] = (
    "STAGE1_ACTIVE_PREDICTION_MARKET",
    "STAGE1_ACTIVE_MARKET_AGNOSTIC",
    "DORMANT_NON_STAGE1_MARKET",
    "DORMANT_RESEARCH_ONLY",
    "OWNER_REVIEW_REQUIRED",
    "REPAIR_REQUIRED_BEFORE_ACTIVATION",
)

DOWNSTREAM_ROUTES: Final[tuple[str, ...]] = (
    "ROUTE_TO_PR165_SCORING",
    "ROUTE_TO_PR165_B_NEGATIVE_MEMORY",
    "ROUTE_TO_PR165_C_ROLE_SLICE_AUDIT",
    "ROUTE_TO_PR163_C_INFRA_REPAIR",
    "ROUTE_TO_PR162B_R_MARKET_SCOPE_REPAIR",
    "ROUTE_TO_PR162D_R3_ACQUISITION_REPAIR",
    "ROUTE_TO_PR162E_PLUGIN_INTAKE_LATER",
    "ROUTE_TO_PR166_L_LLM_REVIEW_LATER",
    "ROUTE_TO_PR162E_Q_QUANTUM_MAPPER_LATER",
    "ROUTE_TO_DORMANT_NON_STAGE1",
    "ROUTE_TO_OWNER_REVIEW",
)

EVIDENCE_TIERS: Final[tuple[str, ...]] = (
    "EVIDENCE_TIER_0_REPO_LOCAL_DETERMINISTIC",
    "EVIDENCE_TIER_1_OFFICIAL_SOURCE_CANDIDATE",
    "EVIDENCE_TIER_2_NONOFFICIAL_SOURCE_CANDIDATE",
    "EVIDENCE_TIER_3_SYNTHETIC_FIXTURE",
    "EVIDENCE_TIER_4_OWNER_POLICY",
    "EVIDENCE_TIER_5_MISSING_REPAIR_REQUIRED",
)

DIVERGENCE_MATERIALITY: Final[tuple[str, ...]] = (
    "BENIGN_EXPECTED_SYNTHETIC_DIVERGENCE",
    "TRADING_MATERIAL_DIVERGENCE",
    "EXECUTION_COST_MATERIAL_DIVERGENCE",
    "SOURCE_QUALITY_MATERIAL_DIVERGENCE",
    "LATENCY_MATERIAL_DIVERGENCE",
    "LIQUIDITY_MATERIAL_DIVERGENCE",
    "REPAIRABLE_INFRASTRUCTURE_DIVERGENCE",
    "DORMANT_OR_INVALID_STRATEGY_DIVERGENCE",
)

SOURCE_CLASSES: Final[tuple[str, ...]] = (
    "OFFICIAL_VENUE_OR_REGULATORY",
    "OFFICIAL_API_DOC",
    "ACADEMIC_RESEARCH",
    "INSTITUTIONAL_RESEARCH",
    "OPEN_SOURCE_REPO_RESEARCH_ONLY",
    "SOCIAL_SIGNAL_RESEARCH_ONLY",
    "NEWS_RESEARCH_ONLY",
    "OWNER_PROVIDED",
    "LOCAL_REPO_DERIVED",
    "SYNTHETIC_REPLAY_PAPER_DERIVED",
    "UNSAFE_REJECTED",
)

SOURCE_POLICY_DISPOSITIONS: Final[tuple[str, ...]] = (
    "ACCEPT_CANDIDATE_REPLAY_PAPER_OFFICIAL",
    "ACCEPT_CANDIDATE_REPLAY_PAPER_NONOFFICIAL",
    "ACCEPT_RESEARCH_ONLY_NONOFFICIAL",
    "REJECT_UNSAFE",
    "REJECT_DUPLICATE",
    "REJECT_IRRELEVANT",
    "REJECT_IMPOSSIBLE_TO_MAP",
)

LATENCY_CLASSES: Final[tuple[str, ...]] = (
    "HOT_PATH_SAFE_PRECOMPUTED_ONLY",
    "CONTROL_PLANE_ONLY",
    "REPLAY_PAPER_ONLY",
    "REQUIRES_CACHE_BEFORE_RUNTIME",
    "NOT_LATENCY_SAFE_FOR_STAGE1",
)

QUANTUM_MODEL_FAMILIES: Final[tuple[str, ...]] = (
    "QUBO",
    "BQM",
    "CQM",
    "DQM",
    "ISING",
    "QAOA",
    "VQE",
    "NONE",
)

VARIABLE_DOMAINS: Final[tuple[str, ...]] = (
    "binary",
    "integer",
    "discrete",
    "continuous",
    "mixed",
)

EXACT_REASON_CODES: Final[dict[str, str]] = {
    "CURRENT_CANDIDATE_CANONICAL": (
        "QKU maps to one current CandidatePacketV1 row and PR163-B paired evidence."
    ),
    "HISTORICAL_QKU_NOT_IN_CURRENT_PACKET": (
        "QKU is present in PR161C historical inventory but has no current CandidatePacketV1 row."
    ),
    "MISSING_CANDIDATE_PACKET_FILL_REQUIRED": (
        "Create or reconcile a CandidatePacketV1 row before replay/paper scoring."
    ),
    "DORMANT_NON_STAGE1_MARKET": (
        "Market scope is outside Stage-1 prediction-market or market-agnostic coverage."
    ),
    "ARTIFICIAL_INFRA_REJECTION_REPAIR": (
        "PR163-B classified the rejection as repairable infrastructure behavior."
    ),
    "NONOFFICIAL_SOURCE_ALLOWED_AS_CANDIDATE": (
        "Non-official material is useful for research/provisional replay-paper lanes only."
    ),
    "NO_SOURCE_TRUTH_CREATED": (
        "PR164 records candidate provenance and does not create accepted source truth."
    ),
}


def as_schema_enum_payload() -> dict[str, object]:
    """Return a stable payload for the central reason-code schema/report."""

    return {
        "review_status": list(REVIEW_STATUSES),
        "computability_disposition": list(COMPUTABILITY_DISPOSITIONS),
        "prohibited_disposition": list(PROHIBITED_DISPOSITIONS),
        "market_scope": list(MARKET_SCOPES),
        "activation_state": list(ACTIVATION_STATES),
        "downstream_route": list(DOWNSTREAM_ROUTES),
        "evidence_tier": list(EVIDENCE_TIERS),
        "divergence_materiality": list(DIVERGENCE_MATERIALITY),
        "source_class": list(SOURCE_CLASSES),
        "source_policy_disposition": list(SOURCE_POLICY_DISPOSITIONS),
        "latency_class": list(LATENCY_CLASSES),
        "quantum_model_family": list(QUANTUM_MODEL_FAMILIES),
        "variable_domain": list(VARIABLE_DOMAINS),
        "exact_reason_codes": dict(sorted(EXACT_REASON_CODES.items())),
    }


def require_enum(value: str, allowed: tuple[str, ...], field: str) -> str:
    if value not in allowed:
        raise ValueError(f"{field} has non-central PR164 enum value: {value}")
    return value
