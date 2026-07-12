from __future__ import annotations

"""Compact table-driven fixtures used by both runtime tests and the validator.

The validator derives expectations from execution; these fixtures contain
inputs and applicability contexts only, never expected final results.
"""

from copy import deepcopy
from typing import Any


_DIFFERENCE_CARDS = {"F25"}
_RATIO_CARDS = {"B11", "D10", "F39", "F40", "G09"}


def _j_fixture(card_id: str) -> dict[str, Any]:
    if card_id == "J01":
        return {"support": [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]], "utilities": [0.0, 1.0, 0.5], "weights": [0.2, 0.5, 0.3], "transport_cost_matrix": [[0.0, 1.0, 1.0], [1.0, 0.0, 1.4], [1.0, 1.4, 0.0]], "ambiguity_radius": 0.2, "transport_metric": "DECLARED_FINITE_COST_MATRIX", "sensitivity_radii": [0.0, 0.1, 0.2], "no_trade_utility": 0.0}
    if card_id == "J02":
        return {"constraint_id": "fill_ttl", "constraint_residuals": [-1.0, -0.5, 0.2, -0.1], "target_violation_probability": 0.6, "confidence_level": 0.8, "confidence_method": "EXACT_BINOMIAL_IID", "threshold_provenance": "FIXTURE_POLICY"}
    if card_id == "J03":
        return {"reference_samples": [[0.0], [0.1], [0.2], [0.3]], "current_samples": [[1.0], [1.1], [1.2], [1.3]], "bandwidth": 0.5, "permutations": 31, "seed": 7, "alpha": 0.1, "resampling_method": "IID_PERMUTATION", "trial_family_id": "FIXTURE_SHIFT_FAMILY"}
    if card_id == "J04":
        return {"kernel": [[2.0, 0.2], [0.2, 1.0]], "jitter": 1e-9, "jitter_provenance": "NUMERICAL_FIXTURE", "tolerance": 1e-12, "raw_economic_utility_ref": "FIXTURE_UTILITY", "opportunity_cost_ref": "FIXTURE_OPPORTUNITY"}
    if card_id == "J05":
        return {"outcomes": [0.0, 1.0, 1.0, 0.0], "log_target_density": [0.0, 0.0, 0.0, 0.0], "log_proposal_density": [0.0, 0.0, 0.0, 0.0], "target_samples": [0.0, 1.0, 1.0, 0.0], "seed": 11}
    if card_id == "J06":
        return {"objective_sense": "MINIMIZE", "objective_coefficients": [1.0, 2.0], "constraint_matrix": [[1.0, 1.0]], "constraint_senses": [">="], "constraint_rhs": [1.0], "primal_solution": [1.0, 0.0], "dual_solution": [1.0], "dual_bound": 1.0, "input_lock_ref": "LOCK-1", "dual_input_lock_ref": "LOCK-1", "formulation_ref": "FORM-1", "dual_formulation_ref": "FORM-1", "tolerance": 1e-9}
    if card_id == "J07":
        return {"linear": [-2.02, 1.01], "quadratic": {"0,1": 0.19}, "offset": 0.0, "prune_threshold": 0.01, "quantization_step": 0.1, "candidate_assignments": {"champion": [1, 0], "runner_up": [0, 0], "no_trade": [0, 0]}, "penalty_terms": [], "feasibility_constraints": [], "inverse_economic_map": {"scale": 1.0, "offset": 0.0}, "exhaustive_variable_limit": 16}
    objective = {"00": 0.0, "01": 1.0, "10": 1.0, "11": 2.0}
    return {"variable_count": 2, "generators": [[1, 0]], "objective_values": objective, "feasible_values": {key: True for key in objective}, "objective_sense": "MINIMIZE", "source_formulation_ref": "FORM-ORIGINAL", "reduced_formulation_ref": "FORM-REDUCED"}


def valid_fixture(card_id: str) -> dict[str, Any]:
    if card_id.startswith("J"):
        return _j_fixture(card_id)
    overrides: dict[str, dict[str, Any]] = {
        "A01": {"realized_net_cash": ["1.10", "-0.20", "0.40"]},
        "A02": {"exit_or_settlement_cash": 10, "entry_cash": 7, "unique_costs": [1], "unique_rebates": [0.5]},
        "A03": {"probabilities": [0.25, 0.75], "branch_net_cash": [-1, 2]},
        "A04": {"admissible_expected_net_cash": [-1, 0.5, 2]},
        "A05": {"estimator_samples": [-1, 0, 1, 2, 3], "lower_quantile": 0.2, "upper_quantile": 0.8, "confidence_method": "DEPENDENCE_AWARE_BOOTSTRAP"},
        "A06": {"net_cash_lcb": 2, "expected_holding_seconds": 4},
        "A07": {"net_cash_lcb": 2, "capital_at_risk": 5, "expected_holding_seconds": 4},
        "A08": {"owner_minimum_cash_profit": 1, "round_trip_cost_uncertainty_hurdle": 2, "capital_opportunity_cost_hurdle": 1.5, "risk_reserve_hurdle": 1.25, "minimum_profit_bps": 10, "deployed_capital": 1000},
        "A09": {"quantity": 3, "levels": [{"price": 0.6, "quantity": 2}, {"price": 0.5, "quantity": 2}]},
        "A10": {"quantity": 3, "levels": [{"price": 0.4, "quantity": 2}, {"price": 0.5, "quantity": 2}]},
        "A11": {"executable_liquidation_cash": 10, "position_cash_basis": 7, "unique_exit_fees": 0.5, "earned_rebates": 0.1, "remaining_unique_cash_costs": 0.2, "fillable_quantity": 3},
        "A12": {"fill_branch_probabilities": [0.5,0.3,0.2], "fill_branch_net_cash": [2,1,-0.5]},
        "A13": {"harvested_quantity_net_cash": 1.5, "residual_position_continuation_value": 0.75},
        "A14": {"amount": 1.25, "executable_quote_available": True, "exit_fill_final": False, "settlement_final": False, "ledger_reconciled": False},
        "A15": {"executable_liquidation_cash": 10, "immediate_exit_costs": 1, "residual_obligations": 0.5},
        "A16": {"future_liquidation_or_settlement_cash": [9,11,12], "remaining_costs": 1, "capital_lock_cost": 0.5, "tail_risk_reserve": 0.75, "model_risk_reserve": 0.25},
        "A17": {"settlement_cash_scenarios": [8,10,12], "remaining_fees": 0.5, "capital_lock_cost": 0.25, "settlement_delay_risk": 0.5, "resolution_risk_reserve": 0.75},
        "A18": {"executable_combined_cash_after_hedge": 12, "incremental_costs": 1, "basis_risk_reserve": 0.5, "residual_exposure_cost": 0.25},
        "A19": {"exit_now_value": 8, "opposite_position_robust_value": 3, "incremental_switching_costs": 1},
        "A20": {"action_values": {"EXIT": 2, "HOLD": 1, "NO_ACTION": 0}},
        "A21": {"exit_now_value": 3, "continue_value": 2, "continuation_hysteresis": 0.5},
        "A22": {"fresh_state_change": True, "cooldown_complete": True, "new_entry_net_cash_lcb": 3, "new_entry_hurdle": 2, "exit_hurdle": 1},
        "A23": {"best_alternative_robust_utility": 3, "current_position_robust_utility": 2},
        "A24": {"reserve_components": [{"component_id":"tail","amount":1},{"component_id":"model","amount":0.5}]},
        "A25": {"candidate_robust_utility": 3, "no_trade_robust_utility": 1},
        "A26": {"child_rows": [{"economic_event_id":"fill-1","gross_cash":10,"realized_net_cash":2,"fees":0.5,"rebates":0.1,"impact":0.2,"capital_seconds":100,"drawdown":0},{"economic_event_id":"fill-2","gross_cash":5,"realized_net_cash":1,"fees":0.25,"rebates":0,"impact":0.1,"capital_seconds":50,"drawdown":0.5}]},
        "A27": {"size_ladder": [1,2,3], "robust_utilities": [1,1.6,1.8]},
        "A28": {"candidate_additions": [{"additional_size":1,"marginal_net_cash_lcb":0.5,"constraints_satisfied":True},{"additional_size":2,"marginal_net_cash_lcb":-0.1,"constraints_satisfied":True}]},
        "A29": {"indicators": {"SUCCESS":True,"FAILURE":False,"FUTILITY":False,"EXPIRY":False,"OWNER_STOP":False,"INVALIDATION":False}, "evidence_time": 10},
        "A30": {"quantity": 10, "price": 0.4, "fee_rate": 0.02, "fee_rule": "P_X_ONE_MINUS_P", "fee_schedule_version": "SYNTHETIC_FIXTURE_V1"},
        "A31": {"shares": 10, "price": 0.4, "fee_rate": 0.02},
        "A32": {"own_fee_equivalent": 2, "total_fee_equivalent": 5, "rebate_pool": 10},
        "A33": {"branch_probabilities": [0.5,0.5], "branch_net_cash": [2,-1], "inventory_reserve": 0.1, "adverse_selection_reserve": 0.1, "latency_model_reserve": 0.05, "model_reserve": 0.05},
        "B01": {"side_sign": 1, "filled_quantity": 10, "average_fill_price": 0.55, "decision_price": 0.5, "explicit_fees": 0.1, "rebates": 0.02, "opportunity_cost_unfilled": 0.05},
        "B02": {"components": {"spread_cost":0.2,"delay_cost":0.1,"market_impact":0.3,"fees":0.1,"negative_rebates":-0.02,"opportunity_cost":0.05,"residual":0}, "total_execution_cost":0.73},
        "B03": {"decision_time": 10, "arrival_latency_seconds": 0.2, "quantity": 3, "arrival_book_levels": [{"price":0.5,"quantity":2},{"price":0.55,"quantity":2}]},
        "B04": {"side_sign":1,"fill_price":0.55,"future_reference_price":0.5},
        "B05": {"side_sign":1,"fill_price":0.55,"future_reference_price":0.5},
        "B06": {"side_sign":1,"quantity":10,"fill_price":0.55,"reference_price":0.5},
        "B07": {"side_sign":1,"quantity":10,"depth_walk_vwap":0.55,"top_of_book_price":0.5},
        "B08": {"robust_value_at_decision":2,"robust_value_at_arrival":1.5},
        "B09": {"hazard_increments": [0.1, 0.2]},
        "B10": {"queue_ahead":5,"order_remaining":4,"depletion_scenarios":[3,6,10]},
        "B11": {"bid_size": 60, "ask_size": 40},
        "B12": {"best_bid": 0.4, "best_ask": 0.5, "bid_size": 60, "ask_size": 40},
        "B13": {"book_events":[{"bid_price":0.4,"bid_quantity":10,"ask_price":0.5,"ask_quantity":8},{"bid_price":0.4,"bid_quantity":12,"ask_price":0.5,"ask_quantity":7}]},
        "B14": {"baseline_intensity":0.1,"evaluation_time":2,"events":[{"event_time":1,"alpha":0.2,"beta":1.0}]},
        "B15": {"route_branches":[{"route_id":"MAKER","probabilities":[0.6,0.4],"branch_net_cash":[2,-0.5],"inventory_reserve":0.1,"adverse_selection_reserve":0.1,"latency_reserve":0.05,"model_reserve":0.05},{"route_id":"TAKER","probabilities":[1],"branch_net_cash":[0.5],"inventory_reserve":0,"adverse_selection_reserve":0,"latency_reserve":0,"model_reserve":0}]},
        "B16": {"new_order_after_priority_loss_utility":2,"keep_existing_order_utility":1.5,"cancel_replace_cost":0.1},
        "B17": {"reference_price":0.5,"inventory":2,"risk_aversion":0.1,"variance_horizon":0.05},
        "B18": {"risk_aversion":0.1,"variance_horizon":0.05,"kappa":2},
        "B19": {"inventory":2,"risk_aversion":0.1,"variance_horizon":0.05},
        "B20": {"capacity":100,"available_tokens":20,"refill_rate":5,"elapsed_seconds":2,"request_cost":3},
        "B21": {"window_fills":[{"matched_contracts":3},{"matched_contracts":4}],"rolling_limit":10},
        "C01": {"probabilities": [0.2, 0.8], "outcomes": [0, 1]},
        "C02": {"probabilities": [0.2, 0.8], "outcomes": [0, 1]},
        "C03": {"probabilities":[0.1,0.4,0.6,0.9],"outcomes":[0,0,1,1],"bins":[[0,0.5],[0.5,1]]},
        "C04": {"probabilities":[0.2,0.4,0.6,0.8],"outcomes":[0,0,1,1]},
        "C05": {"weights": [1, 2, 1]},
        "C06": {"sample_count":100,"autocorrelations":[0.2,0.1],"truncation_rule":"FINITE_LAG_2"},
        "C07": {"cluster_weights":[[1,1],[1],[1,1,1]]},
        "C08": {"bootstrap_statistics":[-1,0,0.5,1,2],"alpha":0.2,"resampling_plan":"EVENT_CLUSTER_BOOTSTRAP","seed":7},
        "C09": {"e_value_increments":[1.2,1.1,2.0],"alpha":0.1,"e_process_family":"FIXED_BETTING_E_PROCESS"},
        "C10": {"p_values": [0.01, 0.2, 0.03], "q": 0.1},
        "C11": {"p_values": [0.01, 0.2, 0.03], "q": 0.1},
        "C12": {"sharpe":0.5,"reference_sharpe":0,"sample_count":100,"skewness":0,"kurtosis":3},
        "C13": {"sharpe":0.5,"trial_sharpe_variance":0.04,"effective_trial_count":10,"effective_sample_length":100,"skewness":0,"kurtosis":3},
        "C14": {"oos_rank_logits":[-1,0.5,-0.2,1]},
        "C15": {"observed_max_statistic":2,"bootstrap_max_statistics":[0.5,1,1.5,2.5]},
        "C16": {"observed_max_statistic":2,"bootstrap_max_statistics":[0.5,1,1.5,2.5]},
        "C17": {"stepdown_p_values":[0.01,0.04,0.03],"alpha":0.05},
        "C18": {"model_ids":["a","b","c"],"equal_predictive_ability_p_values":[0.01,0.2,0.1],"alpha":0.05,"elimination_rule":"MAX_T"},
        "C19": {"paired_utility_deltas":[0.2,0.3,0.1,0.5],"alpha":0.25},
        "C20": {"rankings":[["a","b","c"],["a","c","b"],["a","b","c"]]},
        "C21": {"net_cash_samples":[1,-1,2,3],"alpha":0.05},
        "C22": {"sharpe":0.5,"reference_sharpe":0,"confidence_target":0.95,"skewness":0,"kurtosis":3},
        "C23": {"nonconformity_scores":[0.1,0.2,0.3,0.4],"alpha":0.2,"point_prediction":0.6},
        "C24": {"dependence_eigenvalues":[2,1,0.5],"raw_trial_count":4},
        "C25": {"previous_mean": 0.1, "previous_second_moment": 0.05, "return_value": 0.2, "eta": 0.1},
        "D01": {"losses": [1, 2, 5], "alpha": 0.8, "weights": [0.2, 0.3, 0.5]},
        "D02": {"alpha":0.8,"weighted_loss_scenarios":[{"losses":[1,2,5],"weights":[0.2,0.3,0.5]},{"losses":[2,3,6],"weights":[0.2,0.3,0.5]}]},
        "D03": {"weights":[0.6,0.4],"expected_returns":[0.1,0.2],"covariance":[[0.04,0.01],[0.01,0.09]],"risk_aversion":1},
        "D04": {"weights":[0.6,0.4],"covariance":[[0.04,0.01],[0.01,0.09]]},
        "D05": {"shares": [0.5, 0.3, 0.2]},
        "D06": {"shares": [0.5, 0.3, 0.2]},
        "D07": {"pair_interactions":[{"coefficient":1,"correlation":0.5,"weight_a":0.6,"weight_b":0.4}]},
        "D08": {"return_scenarios":[-0.5,0.2,0.5],"probabilities":[0.2,0.5,0.3],"owner_cap":0.5,"shrink_factor":0.5},
        "D09": {"equity": [10, 12, 9, 11]},
        "D10": {"capital_used": 2, "capital_budget": 5},
        "D11": {"portfolio_utility_with_candidate":3,"current_portfolio_utility":2},
        "D12": {"new_opportunity_marginal_utility":3,"current_position_continuation_value":2,"switching_cost":0.25},
        "D13": {"payoff_sensitivities":[1,-0.5],"positions":[10,4]},
        "D14": {"capital_buckets":[[{"capital":10,"weight":1}],[{"capital":5,"weight":1},{"capital":3,"weight":1}]],"budgets":[12,10]},
        "D15": {"losses":[1,2,3],"probabilities":[0.2,0.5,0.3],"theta":0.5},
        "D16": {"scenario_utilities":[1,2,3],"tail_penalty":0.2,"capital_lock_penalty":0.1,"model_risk_penalty":0.1},
        "D17": {"hard_constraints":[True,True],"net_cash_lcb":1,"tail_loss":0.5,"capital_time_efficiency":0.1,"turnover_compute_burden":0.2},
        "D18": {"candidates":[{"id":"a","primary_objective":2,"risk":0.5},{"id":"b","primary_objective":3,"risk":2}],"epsilon_bounds":{"risk":1}},
        "D19": {"prior_mean":1,"prior_strength":2,"effective_sample_size":3,"sample_mean":2},
        "D20": {"champion_utility":3,"selected_utility":2.5},
        "D21": {"conditional_action_utilities":[[1,2],[3,1]],"outcome_probabilities":[0.5,0.5],"current_action_utilities":[1,1.5],"compute_and_delay_cost":0.1},
        "D22": {"expected_information_gain":1,"expected_economic_improvement":2,"coverage_diversity_value":0.5,"cost":0.25},
        "D23": {"rewards":[1,0,2],"target_probabilities":[0.5,0.4,0.6],"behavior_probabilities":[0.5,0.5,0.5]},
        "D24": {"rewards":[1,0,2],"target_probabilities":[0.5,0.4,0.6],"behavior_probabilities":[0.5,0.5,0.5]},
        "D25": {"rewards":[1,0,2],"target_probabilities":[0.5,0.4,0.6],"behavior_probabilities":[0.5,0.5,0.5],"reward_model_observed_action":[0.8,0.2,1.5],"reward_model_target_policy":[0.9,0.3,1.6]},
        "D26": {"no_trade_hurdle":1,"candidate_changes":[{"id":"smaller","change_cost":1,"net_cash_lcb":1.5,"constraints_satisfied":True},{"id":"venue","change_cost":2,"net_cash_lcb":2,"constraints_satisfied":True}]},
        "D27": {"regimes":[{"weight":0.5,"feasible":True,"utility_lcb":2,"hurdle":1},{"weight":0.5,"feasible":True,"utility_lcb":0.5,"hurdle":1}]},
        "D28": {"comparisons":[{"metric":"cash","kind":"numeric","left":2,"right":1,"scale":1,"hard_veto":False},{"metric":"authority","kind":"categorical","left":"ALLOW","right":"BLOCK","hard_veto":True}]},
        "D30": {"experiments":[{"experiment_id":"a","eligible":True,"expected_marginal_voi":2,"resource_cost":1},{"experiment_id":"b","eligible":True,"expected_marginal_voi":3,"resource_cost":2}]},
        "E03": {"probabilities": [0.4, 0.6]},
        "E01": {"guaranteed_payout":10,"executable_acquisition_costs":[4,5],"all_unique_costs":0.2,"atomicity_partial_fill_reserve":0.3},
        "E02": {"executable_sale_proceeds":[6,5],"guaranteed_liability":10,"all_unique_costs":0.2,"borrow_token_inventory_reserve":0.3},
        "E04": {"probabilities": [0.4, 0.6]},
        "E05": {"probability_subset": 0.3, "probability_superset": 0.6},
        "E06": {"probability_intersection": 0.2, "probability_a": 0.4, "probability_b": 0.5},
        "E07": {"probability_subset": 0.3, "probability_superset": 0.6},
        "E08": {"probability_subset": 0.3, "probability_superset": 0.6},
        "E09": {"rich_venue_sale_proceeds":10,"cheap_venue_buy_cost":8,"fees":0.5,"transfer_finality_reserve":0.2,"basis_settlement_reserve":0.1,"asynchronous_fill_reserve":0.2},
        "E10": {"joint_all_fill_observations":[True,False,True,True],"joint_dependence_model":"EMPIRICAL_JOINT"},
        "E11": {"fill_adjusted_net_cash":2,"tail_reserve":0.2,"partial_fill_reserve":0.1,"settlement_reserve":0.1,"capital_lock_reserve":0.1},
        "E12": {"decision_variables":["leg_a","leg_b"],"semantic_payoff_proof_refs":["synthetic-proof"],"constraints":["capital","joint_fill","settlement"]},
        "F01": {"net_cash_lcbs":[2,1],"tail_penalties":[0.2,0.1],"inventory_penalties":[0.1,0.1],"turnover_penalties":[0.05,0.05],"interaction_coefficients":{"0,1":0.2},"hard_constraints":["capital","one_policy"],"no_trade_variable":"x_no_trade"},
        "F02": {"scenario_profit_values":[1,2,3],"tail_penalty":0.2,"capital_lock_penalty":0.1,"model_risk_penalty":0.1,"coefficient_map_ref":"synthetic-map"},
        "F03": {"linear": [1.0, -2.0], "quadratic_upper": {"0,1": 0.5}, "offset": 0.25},
        "F04": {"vartype":"BINARY","linear":{"0":1,"1":-2},"quadratic":{"0,1":0.5},"offset":0.25},
        "F05": {"linear":[1,-2],"quadratic_upper":{"0,1":0.5},"offset":0.25},
        "F06": {"linear": [1.0, -2.0], "quadratic_upper": {"0,1": 0.5}, "offset": 0.25, "scale": 2.0, "centering_constant": 0.25},
        "F07": {"objective_improvement_bound":2,"minimum_positive_violation":1,"penalty":3},
        "F08": {"lambda_onehot": 2.0, "selections": [1.0, 0.0, 0.0]},
        "F09": {"selections":[1,0,1],"cardinality":2},
        "F10": {"lower":0,"upper":5,"bits":[1,0,1]},
        "F11": {"lower":0,"bits":[1,1,0]},
        "F12": {"lower":0,"digits":[1,2],"radices":[2,3]},
        "F13": {"binary_index":3,"domain_size":8},
        "F14": {"state":2,"state_count":4},
        "F15": {"sample_probabilities":[0.2,0.3,0.5],"energies":[1,2,3],"objective_sense":"MINIMIZE"},
        "F16": {"relaxation_values":[0,0.25,1],"epsilon":0.01},
        "F17": {"sampled_objectives":[1,2,3,4],"alpha":0.5,"objective_sense":"MINIMIZE"},
        "F18": {"feasible_samples":[[1,0],[1,1],[0,1]]},
        "F19": {"feasible_samples":[[1,0],[1,1],[0,1]],"pairs":[[0,1]]},
        "F20": {"probabilities": [0.2, 0.3, 0.5]},
        "F21": {"bitstrings": [[0,0],[0,1],[1,1]]},
        "F22": {"samples":[{"bits":[0,0],"utility":2},{"bits":[0,1],"utility":1.9},{"bits":[1,1],"utility":1}],"distance_tolerance":1,"utility_tolerance":0.2},
        "F23": {"left": ["a", "b"], "right": ["b", "c"]},
        "F24": {"objective_candidate": 3.0, "objective_classical_champion": 2.0, "objective_sense": "MINIMIZE"},
        "F26": {"residuals_a":[0,0.1],"residuals_b":[0.1,0],"status_a":["PASS","FAIL"],"status_b":["PASS","PASS"]},
        "F27": {"exposure_a":[1,2],"exposure_b":[0,1],"scales":[1,2]},
        "F28": {"plan_a":{"market":"m","side":"YES","size":2,"venue":"v1","policy":"maker","horizon":10},"plan_b":{"market":"m","side":"NO","size":1,"venue":"v2","policy":"taker","horizon":20},"size_scale":2,"time_scale":20},
        "F29": {"utilities":[1,1.5,2],"coefficients":[0,1,2]},
        "F30": {"one_minus_selection_consensus":0.2,"infeasible_rate":0.1,"utility_standard_deviation":0.3,"worst_utility_drop":0.4,"maximum_coefficient_sensitivity":0.5,"backend_seed_disagreement":0.2},
        "F31": {"regimes":[{"weight":0.5,"original_model_feasible":True,"qeu_lcb":1},{"weight":0.5,"original_model_feasible":True,"qeu_lcb":-1}]},
        "F32": {"utility_quantum":3,"utility_classical":2,"compute_cost":0.2,"latency_cost":0.1,"infeasibility_penalty":0,"instability_penalty":0.1,"model_risk_reserve":0.1},
        "F33": {"expected_economic_improvement":2,"qpu_monetary_cost":4},
        "F34": {"expected_economic_improvement":2,"total_end_to_end_seconds":4},
        "F35": {"expected_decision_improvement":2,"information_gain":1,"compute_cost":0.5,"opportunity_cost_of_waiting":0.2,"expiry_risk":0.1},
        "F36": {"probabilities":[0.5,0.5],"normalized_values":[0.2,0.8],"inverse_scale":10,"inverse_offset":0},
        "F37": {"probabilities":[0.2,0.5,0.3],"losses":[1,2,3],"threshold":2},
        "F38": {"probabilities":[0.2,0.5,0.3],"losses":[1,2,3],"alpha":0.8,"eta_candidates":[1,2,3]},
        "F39": {"numerator": 3, "denominator": 4},
        "F40": {"sample_chain_broken": [[False,True],[False,False]]},
        "F41": {"time_basis":10,"records":[{"timestamp":12,"original_model_feasible":False},{"timestamp":15,"original_model_feasible":True}]},
        "F42": {"time_basis":10,"records":[{"timestamp":12,"original_model_feasible":True,"utility":1},{"timestamp":15,"original_model_feasible":True,"utility":2}]},
        "F43": {"runs":[{"selection":[1,0],"utility":1,"feasible":True},{"selection":[1,1],"utility":2,"feasible":True},{"selection":[0,1],"utility":1.5,"feasible":False}]},
        "F44": {"best_reverse_utility":3,"initial_incumbent_utility":2},
        "F45": {"postprocessed_utility":3,"raw_decoded_utility":2.5},
        "F46": {"logical_qubits":10,"physical_qubits":20,"depth":100,"two_qubit_gates":50,"shots_or_reads":1000,"embedding_chains":5,"queue_seconds":2,"preparation_seconds":1,"wall_seconds":5,"monetary_cost":0},
        "G01": {"sample_covariance":[[2,0.5],[0.5,1]],"target_covariance":[[1.5,0],[0,1.5]],"shrinkage_intensity":0.25},
        "G02": {"scenario_losses":[1,4,2],"scenario_probabilities":[0.3,0.2,0.5],"portfolio_weights":[0.6,0.4],"asset_loss_contributions":[[0.6,0.4],[2.4,1.6],[1.2,0.8]],"alpha":0.8},
        "G03": {"component_risk_contributions":[0.6,0.4],"risk_budgets":[0.5,0.5]},
        "G04": {"quantity":"100","daily_volume":"10000","volatility":"0.02","impact_coefficient":"0.5"},
        "G05": {"schedule_quantities":[1,2],"expected_unit_costs":[0.1,0.2],"cost_covariance":[[0.04,0.01],[0.01,0.09]],"risk_aversion":0.5},
        "G06": {"observations":[0,0.1,1,1.2],"reference_mean":0,"allowance":0.05},
        "G07": {"log_model_evidence":[-2,-1],"prior_weights":[0.5,0.5]},
        "G08": {"utilities":[1,2,0],"temperature":0.5},
        "G09": {"valid_runs": 4, "successful_valid_runs": 3},
        "G10": {"p_success": 0.5, "p_target": 0.95, "run_seconds": 2},
        "G11": {"raw_estimator_variance":1,"mitigated_estimator_variance":2},
        "G12": {"stratum_standard_deviations":[1,2],"per_shot_costs":[1,4],"total_shots":10},
        "G13": {"current_calibration":[0.1,0.3],"baseline_calibration":[0.05,0.2]},
        "G14": {"frontier": [[1.0,1.0]], "candidate": [2.0,0.5], "reference_point": [0.0,0.0], "objective_senses": ["MAXIMIZE","MAXIMIZE"]},
        "H01": {"raw_probabilities":[0.2,0.7,0.3],"equality_groups":[{"indices":[0,1],"target_sum":1.0}]},
        "H02": {"probabilities":[0.2,0.6,0.4,0.8],"weights":[1,1,1,1]},
        "H03": {"success_branch_net_cash":"8","failure_branch_net_cash":"-2"},
        "H04": {"calibrated_probabilities":[0.7,0.6,0.8],"break_even_probabilities":[0.5,0.55,0.6],"lower_quantile":0.1},
        "H05": {"losses": [1, 2, 5], "alpha": 0.8, "weights": [0.2, 0.3, 0.5]},
        "H06": {"candidate_utilities":[1,2,0],"best_available_utilities":[2,2.5,1]},
        "H07": {"fill_hazards":[0.2,0.3],"competing_hazards":{"cancel":[0.1,0.1],"adverse":[0.05,0.05]}},
        "H08": {"original_objective_values":[3,5],"inverse_mapped_objective_values":[1,2],"positive_scale":2,"offset":1,"tolerance":1e-9},
        "H09": {"minimum_infeasible_penalty":12,"maximum_feasible_objective_range":10},
        "H10": {"classical_presolve_utility":"1","qpu_search_utility":"1.5","repair_utility":"1.7","postprocessed_utility":"1.8"},
        "H14": {"exit_or_settlement_cash": 10, "entry_cash": 7, "unique_costs": [1], "unique_rebates": [0.5], "branch_net_cash": 2.5},
        "H11": {"features": [{"kind":"numeric","left":1,"right":2,"range":4,"weight":1,"valid":True},{"kind":"categorical","left":"a","right":"b","weight":1,"valid":True}]},
        "H12": {"gradient_samples":[[1,2],[2,1],[1.5,2.5]]},
        "H13": {"end_to_end_latency_samples":[1,2,4,8],"economic_ttl_seconds":3},
        "I01": {"access_policy_qkus":["Q1","Q2"],"stage_qkus":["Q1","Q2","Q3"],"agent_duty_qkus":["Q2","Q4"]},
        "I02": {"agent_stage_qkus":["Q1","Q2"],"executable_qkus":["Q2","Q3"],"input_ready_qkus":["Q2"]},
        "I03": {"agent_executable_qkus":["Q1","Q2"],"market_applicable_qkus":["Q2"],"mode_applicable_qkus":["Q1","Q2"],"capacity_applicable_qkus":["Q2","Q3"]},
        "I04": {"requirements": [{"name": "x", "required": True, "critical": True, "resolved_valid": True}]},
        "I05": {"fields": [{"kind":"numeric","left":1,"right":2,"range":4,"weight":1,"valid":True},{"kind":"categorical","left":"a","right":"a","weight":1,"valid":True}]},
        "I06": {"prior_components":{"historical_utility":0.7,"recency":0.8,"similarity":0.9},"policy_coefficients":{"historical_utility":0.4,"recency":0.3,"similarity":0.3}},
        "I07": {"reference_time": 10, "windows": [{"valid_from": 0, "valid_until": 20}]},
        "I08": {"components": {"feature_snapshot_ms": 1, "formula_compute_ms": 2}},
        "I09": {"total_decision_latency_ms": 3, "latency_budget_ms": 10, "min_material_valid_until_ms": 30, "input_lock_time_ms": 10},
        "I10": {"severity_desc": 1, "economic_ttl_asc": 2, "hard_dependency_block_count_desc": 0, "downstream_blocked_value_desc": 3, "value_of_information_per_compute_desc": 4, "queue_age_desc": 5, "deterministic_tie_break_key_asc": "A"},
    }
    if card_id in _DIFFERENCE_CARDS:
        return {"left": 2.0, "right": 1.0, "__problem_size__": 2}
    if card_id == "F23":
        return overrides[card_id]
    if card_id == "D29":
        return {"left": [2.0, 1.0], "right": [1.0, 2.0], "senses": ["MAXIMIZE", "MINIMIZE"]}
    if card_id not in overrides:
        raise KeyError(f"no card-specific fixture for {card_id}")
    return deepcopy(overrides[card_id])


def missing_fixture(card_id: str) -> dict[str, Any]:
    del card_id
    return {}


def boundary_fixture(card_id: str) -> dict[str, Any]:
    fixture = valid_fixture(card_id)
    fixture["__problem_size__"] = 65
    return fixture


def applicability_context(card_id: str, *, positive: bool) -> dict[str, Any]:
    return {"card_ids": [card_id] if positive else [], "stage": "PRETRADE" if not card_id.startswith(("F", "J")) else "QBENCH", "mode": "OFFLINE", "market": "prediction_market"}
