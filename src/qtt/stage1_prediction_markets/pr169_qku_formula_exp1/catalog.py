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
    "B11": "FORMULA::ORDERBOOK_IMBALANCE",
    "B12": "FORMULA::DEPTH_WEIGHTED_MID_PRICE",
    "C01": "FORMULA::BRIER_SCORE",
    "C02": "FORMULA::LOG_LOSS",
    "D10": "FORMULA::CAPITAL_UTILIZATION",
    "F08": "FORMULA::ONE_HOT_PENALTY",
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
    no_order_authority: bool = True
    no_connector_read: bool = True
    no_profit_guarantee: bool = True


def _card(card_id: str, semantic_key: str) -> Card:
    family = card_id[0]
    if card_id in J_IMPLEMENTATIONS:
        disposition = "CREATE_NEW_EXECUTABLE_FORMULA_OR_PROCEDURE"
        implementation = "SOLVER_CERTIFICATE_PROCEDURE" if card_id in {"J06", "J07", "J08"} else "DETERMINISTIC_PROCEDURE"
        canonical = f"QTT_FORMULA::{semantic_key}"
        callable_ref = (
            "src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.family_j:"
            + J_IMPLEMENTATIONS[card_id]
        )
    elif card_id in EXACT_REUSE_ALIASES:
        disposition = "REUSE_EXACT"
        implementation = "DIRECT_PURE_FORMULA"
        canonical = EXACT_REUSE_ALIASES[card_id]
        callable_ref = "src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime:evaluate_formula"
    else:
        disposition = "REUSE_EQUIVALENT_ALIAS"
        implementation = (
            "DETERMINISTIC_PROCEDURE" if family in {"I"} else
            "OPTIMIZATION_PROBLEM_BUILDER" if semantic_key.endswith(("OBJECTIVE", "ALLOCATION", "PROJECTION")) else
            "DIRECT_PURE_FORMULA"
        )
        canonical = f"QTT_FORMULA::{semantic_key}"
        callable_ref = "src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.runtime:evaluate_formula"
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
