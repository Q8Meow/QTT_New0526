from __future__ import annotations


PERMANENT_QTT_LAWS = (
    "IMMUTABLE_FORMULA_AND_QKU_SEMANTICS",
    "TRADE_PLAN_CANDIDATE_IS_MUTABLE_OPTIMIZATION_OBJECT",
    "NO_TRADE_PRESERVES_CAPITAL_AND_ROUTES_BOUNDED_RECOVERY",
    "MEMORY_IS_CONDITION_SCOPED_PRIOR_NOT_PROOF",
    "LLM_HAS_NO_NUMERIC_SOURCE_OR_ORDER_AUTHORITY",
    "OWNER_COMMANDS_USE_CURRENT_ACTION_AND_APPROVAL_PLANE",
    "ONE_OWNER_STATE_AND_ACTION_PLANE",
    "NO_RAW_JSONL_OR_UNBOUNDED_LIBRARY_SCAN",
    "EVERY_VALUE_TASK_AND_HANDOFF_TERMINATES",
    "NO_PROFIT_OR_QUANTUM_ADVANTAGE_GUARANTEE",
    "SHADOW_IS_OBSERVATION_NOT_EXECUTION_AUTHORITY",
    "EXECUTION_ROUTER_IS_FINAL_REAL_ORDER_RELEASE_AUTHORITY",
)

GENERIC_TOOL_OPERATIONS = (
    "query_applicable_qkus",
    "resolve_formula_inputs",
    "evaluate_formula",
    "evaluate_qku_dag",
    "evaluate_trade_plan_scenarios",
)

ERROR_STATES = (
    "MISSING_REQUIRED_INPUT", "STALE_INPUT", "UNIT_MISMATCH", "BASIS_MISMATCH",
    "DOMAIN_VIOLATION", "CONFLICTING_INPUTS", "FORMULA_INAPPLICABLE",
    "INSUFFICIENT_EVIDENCE", "ORIGINAL_MODEL_INFEASIBLE", "RESULT_EXPIRED",
    "DETERMINISTIC_NO_TRADE", "NUMERICAL_ERROR",
)

STABLE_VALIDATOR_RULE_IDS = (
    "midpoint_or_last_trade_cannot_create_realized_profit",
    "exit_profit_remains_projected_until_exit_fill",
    "spread_slippage_impact_cannot_be_double_counted",
    "one_positive_trade_cannot_authorize_unrestricted_scaling",
    "hold_until_breakeven_cannot_be_the_default_loss_policy",
    "reentry_requires_a_new_positive_edge_determination",
    "campaign_children_share_aggregate_capacity_and_exposure",
    "trade_frequency_cannot_be_used_as_an_objective_without_net_cash_utility",
    "fixed_seven_day_duration_cannot_be_universal",
    "paper_loop_cannot_submit_live_orders",
    "quantum_output_cannot_bypass_execution_router",
)

STRATEGY_TEMPLATES = (
    "Net-cash harvest scalping", "Maker-first spread capture", "Queue-aware maker/taker switch",
    "Maker-entry/taker-exit", "Partial profit harvest", "Liquidity-shock mean reversion",
    "Order-flow impulse trading", "Spread-regime switching", "Complete-set candidate arbitrage",
    "Outcome-sum overpricing candidate", "Logical implication arbitrage", "Date-monotonicity arbitrage",
    "Subset/superset arbitrage", "Cross-venue parity", "Complement/negative-risk consistency",
    "Capital-time rotation", "Event-exposure netting", "Inventory-skew quoting",
    "Resolution-time diversification", "Venue diversification", "Capacity laddering",
    "Regime champion/challenger", "Contextual order-policy bandit", "Condition-scoped negative memory",
    "Sequential evidence stopping", "Agent disagreement arbitration", "No-trade recovery search",
    "Quantum logical-arbitrage hypergraph", "Quantum short-horizon harvest-policy optimizer",
    "Quantum market-making quote-grid optimizer", "Quantum capital-time allocation",
    "Quantum experiment-design portfolio", "Quantum no-trade recovery search",
    "Dual-informed quantum active-set optimizer", "Quantum large-neighborhood refinement",
    "Feasible-subspace mixer tournament", "Coefficient-robust formulation race",
    "Backend/TTL-aware quantum compute allocator",
)

DOWNSTREAM_OWNERS = (
    "READINESS", "PRETRADE", "AGENT_ORCH", "SVC", "PAPER", "METRICS", "MEM",
    "QMAP", "QBENCH", "HOTPATH", "ALLOW", "SHADOW", "LIVE_DRYRUN", "POSTLAUNCH",
)

SHORT_HORIZON_FIELDS = (
    "strategy_mode", "parent_campaign_id", "child_order_id", "minimum_cash_profit",
    "minimum_profit_bps", "cost_uncertainty_hurdle", "capital_opportunity_hurdle",
    "entry_executable_price", "exit_executable_price", "exit_depth_quantity",
    "exit_fill_probability", "partial_exit_quantity", "entry_cash_basis", "exit_cash_candidate",
    "explicit_entry_fee", "explicit_exit_fee", "maker_rebate_candidate", "other_cash_costs",
    "expected_net_cash", "net_cash_lcb", "capital_at_risk", "expected_hold_seconds",
    "net_cash_velocity", "capital_time_efficiency", "profit_harvest_trigger",
    "model_invalidation_trigger", "time_stop", "liquidity_stop", "latency_decay_stop",
    "adverse_selection_stop", "portfolio_stop", "hard_loss_stop", "reentry_edge_hurdle",
    "reentry_cooldown", "fresh_state_change_required", "campaign_child_order_limit",
    "campaign_turnover_limit", "campaign_loss_limit", "campaign_drawdown_limit",
    "remaining_capacity", "paper_result_ref", "replay_result_ref", "dual_review_route_ref",
    "hotpath_handoff_ref", "live_dryrun_handoff_ref", "fast_canary_handoff_ref",
    "execution_router_consumer_ref",
)

UNIT_POLICY = {
    "cash_boundary": "DECIMAL_EXACT_CALLER_BOUNDARY",
    "internal_numeric": "FINITE_FLOAT64_EQUIVALENT_WITH_EXPLICIT_TOLERANCE",
    "probability": "CLOSED_UNIT_INTERVAL",
    "time": "EVENT_TIME_AND_EXPLICIT_CLOCK_BASIS",
    "rounding": "EXPLICIT_PROVIDER_OR_POLICY_DEPENDENCY",
    "implicit_conversion_allowed": False,
    "unknown_value_behavior": "TYPED_UNAVAILABLE_NEVER_ZERO",
}
