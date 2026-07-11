from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


FAMILY_NAMES: dict[str, tuple[str, ...]] = {
    "A": (
        "TOTAL_REALIZED_NET_CASH", "BRANCH_NET_CASH", "EXPECTED_NET_CASH_SCENARIO",
        "ROBUST_NET_CASH_INTERVAL", "NET_CASH_LCB_UCB", "NET_CASH_VELOCITY",
        "CAPITAL_TIME_EFFICIENCY", "REQUIRED_EXIT_PROFIT", "DEPTH_WALK_SELL_PROCEEDS",
        "DEPTH_WALK_BUY_COST", "EXECUTABLE_EXIT_NET_CASH", "FILL_ADJUSTED_EXECUTABLE_NET_CASH",
        "PARTIAL_HARVEST_NET_CASH", "PNL_STATE_CLASSIFICATION", "EXIT_NOW_VALUE",
        "CONTINUE_HOLDING_VALUE", "HOLD_TO_SETTLEMENT_VALUE", "HEDGE_OFFSET_VALUE",
        "REVERSE_VALUE", "FORWARD_ACTION_VALUE", "CONTINUATION_HYSTERESIS",
        "REENTRY_EDGE_HURDLE", "CAPITAL_OPPORTUNITY_COST", "RISK_RESERVE_HURDLE",
        "NO_TRADE_MARGIN", "CAMPAIGN_CASH_AGGREGATES", "CAMPAIGN_CAPACITY_FRONTIER",
        "CAMPAIGN_REMAINING_CAPACITY", "EVIDENCE_STOP_STATISTICS", "VENUE_FEE_GENERIC",
        "FEE_CURVE_PRODUCT", "MAKER_REBATE_SHARE", "NET_QUOTE_UTILITY",
    ),
    "B": (
        "IMPLEMENTATION_SHORTFALL", "TCA_DECOMPOSITION_RECONCILIATION", "EFFECTIVE_ARRIVAL_PRICE",
        "REALIZED_SPREAD", "SIGNED_MARKOUT", "SPREAD_COST", "DEPTH_IMPACT",
        "LATENCY_DECAY_COST", "FILL_SURVIVAL_HAZARD", "QUEUE_AHEAD_DEPLETION",
        "ORDERBOOK_IMBALANCE", "MICROPRICE", "ORDER_FLOW_IMBALANCE",
        "HAWKES_INTENSITY_CANDIDATE", "MAKER_TAKER_ROUTE_UTILITY", "CANCEL_REPLACE_VALUE",
        "AVELLANEDA_STOIKOV_RESERVATION_PRICE", "AVELLANEDA_STOIKOV_HALF_SPREAD",
        "INVENTORY_SKEW", "RATE_LIMIT_BUDGET", "ORDER_GROUP_ROLLING_USAGE",
    ),
    "C": (
        "BRIER_SCORE", "LOG_LOSS", "EXPECTED_CALIBRATION_ERROR", "CALIBRATION_SLOPE_INTERCEPT",
        "WEIGHTED_EFFECTIVE_SAMPLE_SIZE", "AUTOCORRELATION_EFFECTIVE_SAMPLE_SIZE",
        "CLUSTER_EVENT_EFFECTIVE_SAMPLE_SIZE", "DEPENDENCE_AWARE_BOOTSTRAP_LCB",
        "ANYTIME_EVIDENCE_PROCESS", "BENJAMINI_HOCHBERG_FDR", "BENJAMINI_YEKUTIEL_FDR",
        "PROBABILISTIC_SHARPE_RATIO", "DEFLATED_SHARPE_RATIO", "PBO_CSCV",
        "WHITE_REALITY_CHECK", "HANSEN_SPA", "STEPM_MULTIPLE_COMPARISON",
        "MODEL_CONFIDENCE_SET", "PAIRED_CHALLENGER_DELTA", "RANK_STABILITY",
        "PROBABILITY_OF_POSITIVE_NET_CASH", "MINIMUM_TRACK_RECORD_LENGTH",
        "CONFORMAL_INTERVAL_CANDIDATE", "TRIAL_FAMILY_EFFECTIVE_COUNT", "DIFFERENTIAL_SHARPE",
    ),
    "D": (
        "FINANCIAL_LOSS_CVAR", "ROBUST_CVAR", "MEAN_VARIANCE_UTILITY",
        "MARGINAL_RISK_CONTRIBUTION", "EXPOSURE_HERFINDAHL", "DIVERSIFICATION_ENTROPY",
        "CORRELATION_INTERACTION_PENALTY", "FRACTIONAL_KELLY_ROBUST", "MAX_DRAWDOWN",
        "CAPITAL_UTILIZATION", "PORTFOLIO_MARGINAL_UTILITY", "CAPITAL_TIME_ROTATION",
        "EVENT_EXPOSURE_NETTING", "TIME_BUCKET_CAPITAL", "ENTROPIC_RISK_CANDIDATE",
        "DISTRIBUTIONALLY_ROBUST_UTILITY", "LEXICOGRAPHIC_ECONOMIC_OBJECTIVE",
        "EPSILON_CONSTRAINED_PARETO", "CONDITION_SCOPED_SHRINKAGE",
        "CHAMPION_CHALLENGER_REGRET", "VALUE_OF_INFORMATION", "EXPERIMENT_DESIGN_UTILITY",
        "IPS_OFF_POLICY_VALUE", "SNIPS_OFF_POLICY_VALUE", "DOUBLY_ROBUST_POLICY_VALUE",
        "NO_TRADE_RECOVERY_DISTANCE", "REGIME_ROBUSTNESS", "AGENT_DISAGREEMENT_VECTOR",
        "PARETO_DOMINANCE", "ADAPTIVE_SEARCH_BUDGET",
    ),
    "E": (
        "COMPLETE_SET_BUY_MARGIN", "COMPLETE_SET_SELL_MARGIN", "OUTCOME_SUM_CONSISTENCY",
        "COMPLEMENT_CONSISTENCY", "LOGICAL_IMPLICATION", "INTERSECTION_BOUND",
        "DATE_MONOTONICITY", "SUBSET_SUPERSET", "CROSS_VENUE_PARITY_MARGIN",
        "SIMULTANEOUS_FILL_PROBABILITY", "BASKET_EXECUTABLE_UTILITY",
        "LOGICAL_ARBITRAGE_HYPERGRAPH_OBJECTIVE",
    ),
    "F": (
        "DISCRETE_TRADE_ALTERNATIVE_SELECTION", "QUANTUM_ROBUST_ECONOMIC_OBJECTIVE",
        "QUBO_CANONICAL", "BQM_CANONICAL", "QUBO_TO_ISING", "COEFFICIENT_SCALING",
        "PENALTY_SUFFICIENCY", "ONE_HOT_CONSTRAINT", "FIXED_CARDINALITY_CONSTRAINT",
        "BOUNDED_BINARY_ENCODING", "UNARY_ENCODING", "MIXED_RADIX_ENCODING",
        "GRAY_CODE_ENCODING", "DOMAIN_WALL_ENCODING", "QAOA_EXPECTATION",
        "WARM_START_QAOA_ANGLE", "VARIATIONAL_CVAR_AGGREGATOR", "SAMPLE_SELECTION_MARGINAL",
        "SAMPLE_PAIRWISE_COSELECTION", "SOLUTION_ENTROPY", "HAMMING_DIVERSITY",
        "NEAR_OPTIMAL_CLUSTER_COUNT", "SELECTION_OVERLAP", "OBJECTIVE_GAP",
        "ECONOMIC_UTILITY_GAP", "CONSTRAINT_DISAGREEMENT", "PORTFOLIO_EXPOSURE_DISAGREEMENT",
        "TRADE_PLAN_DISAGREEMENT", "COEFFICIENT_STRESS_SENSITIVITY",
        "QUANTUM_SOLUTION_FRAGILITY", "QUANTUM_REGIME_ROBUSTNESS", "QUANTUM_ECONOMIC_UTILITY",
        "QPU_IMPROVEMENT_PER_COST", "QPU_IMPROVEMENT_PER_SECOND", "QUANTUM_VALUE_OF_INFORMATION",
        "QAE_NORMALIZED_EXPECTATION", "QAE_TAIL_PROBABILITY", "QAE_CVAR_CANDIDATE",
        "FEASIBLE_SAMPLE_RATE", "CHAIN_BREAK_FRACTION", "TIME_TO_FIRST_FEASIBLE",
        "TIME_TO_BEST", "EMBEDDING_GAUGE_STABILITY", "REVERSE_ANNEAL_IMPROVEMENT",
        "POSTPROCESSING_IMPROVEMENT", "QUANTUM_RESOURCE_ESTIMATE",
    ),
    "G": (
        "SHRINKAGE_COVARIANCE", "COMPONENT_CVAR", "RISK_BUDGET_PARITY_OBJECTIVE",
        "SQUARE_ROOT_MARKET_IMPACT_CANDIDATE", "EXECUTION_SCHEDULE_MEAN_VARIANCE",
        "CUSUM_DRIFT_STATISTIC", "BAYESIAN_MODEL_AVERAGING_WEIGHT",
        "ENTROPY_REGULARIZED_ALLOCATION", "OPTIMIZATION_TARGET_SUCCESS_RATE",
        "QUANTUM_TIME_TO_SOLUTION", "MITIGATION_VARIANCE_OVERHEAD", "NEYMAN_SHOT_ALLOCATION",
        "BACKEND_CALIBRATION_DRIFT_VECTOR", "PARETO_HYPERVOLUME_IMPROVEMENT",
    ),
    "H": (
        "COHERENT_PROBABILITY_QP_PROJECTION", "DATE_LADDER_ISOTONIC_PROJECTION",
        "EXECUTABLE_BREAK_EVEN_PROBABILITY", "CALIBRATED_EXECUTABLE_EDGE_LCB",
        "LIQUIDITY_ADJUSTED_CVAR", "WORST_CASE_REGRET", "COMPETING_RISKS_FILL_CIF",
        "FORMULATION_EQUIVALENCE_RESIDUAL", "PENALTY_DOMINANCE_RATIO",
        "QUANTUM_CONTRIBUTION_ATTRIBUTION", "PROBLEM_FINGERPRINT_DISTANCE",
        "VARIATIONAL_GRADIENT_SNR", "QPU_RESULT_EXPIRY_PROBABILITY",
        "SCENARIO_CASHFLOW_RECONCILIATION_RESIDUAL",
    ),
    "I": (
        "AGENT_STAGE_QKU_UNIVERSE", "AGENT_EXECUTABLE_QKU_UNIVERSE",
        "CONTEXT_CANDIDATE_QKU_UNIVERSE", "FORMULA_INPUT_RESOLUTION_COVERAGE",
        "CONTEXT_RECIPE_SIMILARITY", "RECIPE_PRIOR_UTILITY", "FORMULA_RESULT_FRESHNESS",
        "END_TO_END_DECISION_LATENCY", "LATENCY_BUDGET_SLACK", "FORMULA_WORK_ITEM_PRIORITY_VECTOR",
    ),
    "J": (
        "WASSERSTEIN_ROBUST_UTILITY", "CHANCE_CONSTRAINED_FEASIBILITY",
        "DISTRIBUTION_SHIFT_TEST", "LOG_DETERMINANT_DIVERSITY",
        "RARE_EVENT_IMPORTANCE_SAMPLING", "PRIMAL_DUAL_OPTIMALITY_CERTIFICATE",
        "CERTIFIED_QUBO_SPARSIFICATION_QUANTIZATION", "SYMMETRY_BREAKING_ORBIT_REDUCTION",
    ),
}

EXPECTED_FAMILY_COUNTS = {"A": 33, "B": 21, "C": 25, "D": 30, "E": 12,
                          "F": 46, "G": 14, "H": 14, "I": 10, "J": 8}

CARD_NAMES = tuple(
    (f"{family}{index:02d}", name)
    for family, names in FAMILY_NAMES.items()
    for index, name in enumerate(names, start=1)
)

J_IMPLEMENTATIONS = {
    "J01": "wasserstein_robust_utility",
    "J02": "chance_constrained_feasibility",
    "J03": "distribution_shift_test",
    "J04": "log_determinant_diversity",
    "J05": "rare_event_importance_sampling",
    "J06": "primal_dual_optimality_certificate",
    "J07": "certified_qubo_sparsification_quantization",
    "J08": "symmetry_breaking_orbit_reduction",
}

EXACT_REUSE_ALIASES = {
    "B11": "PR168_GFP2R_FORMULA_ORDERBOOK_IMBALANCE",
    "B12": "PR162D_R2A::DEPTH_WEIGHTED_MID_PRICE",
    "C01": "FORM_MAP3_CALIB_BRIER_001",
    "C02": "FORM_MAP3_CALIB_LOGLOSS_001",
    "D10": "PR162D_R2A::CAPITAL_UTILIZATION",
    "F08": "PR162D_R2A::ONE_HOT_PENALTY",
}

EXACT_TARGET_CALLABLES = {
    "B11": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_orderbook_imbalance",
    "B12": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_depth_weighted_mid_price",
    "C01": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_brier_score",
    "C02": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_log_loss",
    "D10": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_capital_utilization",
    "F08": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_one_hot_penalty",
}


@dataclass(frozen=True)
class Card:
    card_id: str
    semantic_key: str
    canonical_formula_or_procedure_id: str
    version: str
    formula_family: str
    implementation_class: str
    disposition: str
    callable_ref: str
    deterministic: bool
    input_contract_ref: str
    output_contract_ref: str
    objective_sense: str
    unit_policy_ref: str
    error_taxonomy_ref: str
    actual_callable_or_solver_ref: str
    alias_target_formula_id: str | None
    alias_target_version: str | None
    alias_target_callable_ref: str | None
    implementation_state: str
    runtime_context_state: str
    supported_input_domain: str
    supported_problem_size_or_scaling_class: str
    applicability_predicate: str
    eligible_stages: tuple[str, ...]
    eligible_modes: tuple[str, ...]
    trigger_or_scheduling_rule: str
    required_input_provider_classes: tuple[str, ...]
    latency_update_class: str
    timeout_memory_class: str
    execution_lane: str
    deterministic_or_seed_contract: str
    failure_no_trade_fallback: str
    canonical_consumer_class: str
    output_consumer_fields: tuple[str, ...]
    no_order_authority: bool = True
    no_connector_read: bool = True
    no_profit_guarantee: bool = True


def _card(card_id: str, semantic_key: str) -> Card:
    family = card_id[0]
    if card_id in J_IMPLEMENTATIONS:
        disposition = "CREATE_NEW_EXECUTABLE_FORMULA_OR_PROCEDURE"
        implementation = "SOLVER_CERTIFICATE_PROCEDURE" if card_id in {"J06", "J07", "J08"} else "DETERMINISTIC_PROCEDURE"
        canonical = f"QTT_FORMULA::{semantic_key}"
        callable_ref = f"src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.methods:compute_{card_id}"
    elif card_id in EXACT_REUSE_ALIASES:
        disposition = "REUSE_EXISTING_EXECUTABLE"
        implementation = "DIRECT_PURE_FORMULA"
        canonical = EXACT_REUSE_ALIASES[card_id]
        callable_ref = f"src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.methods:compute_{card_id}"
    else:
        disposition = "CREATE_NEW_EXECUTABLE_FORMULA_OR_PROCEDURE"
        implementation = (
            "DETERMINISTIC_PROCEDURE" if family in {"I"} else
            "OPTIMIZATION_PROBLEM_BUILDER" if semantic_key.endswith(("OBJECTIVE", "ALLOCATION", "PROJECTION")) else
            "DIRECT_PURE_FORMULA"
        )
        canonical = f"QTT_FORMULA::{semantic_key}"
        callable_ref = f"src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.methods:compute_{card_id}"
    lane = (
        "CENTRAL_ACCESS_OR_ORCHESTRATION"
        if family == "I"
        else "QMAP_QBENCH_BATCH"
        if family in {"F", "J"}
        else "EVIDENCE_OR_GOVERNANCE_BATCH"
        if family == "C"
        else "PRETRADE_BATCH_OR_HOTPATH_CANDIDATE"
    )
    return Card(
        card_id=card_id,
        semantic_key=semantic_key,
        canonical_formula_or_procedure_id=canonical,
        version="1.0.0",
        formula_family=family,
        implementation_class=implementation,
        disposition=disposition,
        callable_ref=callable_ref,
        deterministic=True,
        input_contract_ref=f"FormulaInputResolutionV1:{card_id}",
        output_contract_ref=f"FormulaEvaluationReceiptV1:{card_id}",
        objective_sense="DECLARED_BY_CARD_OR_NOT_APPLICABLE",
        unit_policy_ref="CentralUnitBasisNumericPolicyV1",
        error_taxonomy_ref="FormulaErrorTaxonomyV1",
        actual_callable_or_solver_ref=callable_ref,
        alias_target_formula_id=EXACT_REUSE_ALIASES.get(card_id),
        alias_target_version="1.0.0" if card_id in EXACT_REUSE_ALIASES else None,
        alias_target_callable_ref=EXACT_TARGET_CALLABLES.get(card_id),
        implementation_state="EXECUTABLE",
        runtime_context_state="EXECUTABLE_REQUIRES_DECLARED_INPUTS",
        supported_input_domain="FINITE_TYPED_CARD_CONTRACT",
        supported_problem_size_or_scaling_class="BOUNDED_SCALAR_VECTOR_OR_SMALL_EXACT_MAX_64",
        applicability_predicate=f"context.card_id == '{card_id}' and context.authority != 'ORDER_RELEASE'",
        eligible_stages=("RESEARCH", "PRETRADE", "REPLAY", "PAPER_PREPARATION", "QMAP", "QBENCH"),
        eligible_modes=("OFFLINE", "REPLAY", "PAPER", "SHADOW_COMPARISON", "LIVE_DRYRUN_CANDIDATE"),
        trigger_or_scheduling_rule=f"ON_APPLICABLE_CONTEXT_OR_DEPENDENCY_CHANGE::{card_id}",
        required_input_provider_classes=("RESOLVED_INPUT_LOCK", "CANONICAL_FORMULA_DEPENDENCY"),
        latency_update_class="BATCH_OR_PRECOMPUTE" if lane != "PRETRADE_BATCH_OR_HOTPATH_CANDIDATE" else "EVENT_DRIVEN_BATCH_HOTPATH_CANDIDATE",
        timeout_memory_class="BOUNDED_5S_64_ITEMS",
        execution_lane=lane,
        deterministic_or_seed_contract="DETERMINISTIC_OR_EXPLICIT_SEED",
        failure_no_trade_fallback="TYPED_FAILURE_THEN_DETERMINISTIC_NO_TRADE_OR_GOVERNED_FALLBACK",
        canonical_consumer_class="SYSTEM_PROCEDURE_CONSUMER" if family == "I" else "QKU_DAG_APPLICABLE",
        output_consumer_fields=("formula_evaluation_receipt", "readiness_state", "pretrade_decision_input"),
    )


def card_rows() -> list[dict[str, Any]]:
    return [asdict(_card(card_id, name)) for card_id, name in CARD_NAMES]


def validate_catalog() -> None:
    actual = {family: len(names) for family, names in FAMILY_NAMES.items()}
    if actual != EXPECTED_FAMILY_COUNTS:
        raise ValueError(f"formula family counts differ: {actual!r}")
    if len(CARD_NAMES) != 213 or len({card_id for card_id, _ in CARD_NAMES}) != 213:
        raise ValueError("formula cards must contain 213 unique IDs")
    if len({name for _, name in CARD_NAMES}) != 213:
        raise ValueError("formula semantic keys must be unique")


validate_catalog()
