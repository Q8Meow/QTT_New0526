from __future__ import annotations

import math
import pytest

from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.family_j import (
    FormulaDomainError, chance_constrained_feasibility,
    certified_qubo_sparsification_quantization, distribution_shift_test,
    log_determinant_diversity, primal_dual_optimality_certificate,
    rare_event_importance_sampling, symmetry_breaking_orbit_reduction,
    wasserstein_robust_utility,
)


def test_j01_zero_radius_nominal_and_radius_monotonic() -> None:
    base={"support":[0,1],"utilities":[0,1],"weights":[0.5,0.5],"transport_metric":"absolute_1d","no_trade_utility":0}
    nominal=wasserstein_robust_utility({**base,"ambiguity_radius":0})
    stressed=wasserstein_robust_utility({**base,"ambiguity_radius":0.25})
    assert nominal["robust_utility"]==pytest.approx(0.5)
    assert stressed["robust_utility"]<=nominal["robust_utility"]
    assert stressed["no_trade_margin"]==pytest.approx(stressed["robust_utility"])


@pytest.mark.parametrize("violations", [[-1,-1,-1],[1,-1,-1]])
def test_j02_zero_violations_never_means_zero_risk(violations: list[float]) -> None:
    result=chance_constrained_feasibility({"constraint_residuals":violations,"target_violation_probability":0.9,"confidence_level":0.95,"confidence_method":"EXACT_BINOMIAL_IID"})
    assert result["violation_probability_upper_confidence_bound"]>0
    assert 0<=result["estimated_violation_probability"]<=1


def test_j02_rejects_iid_method_for_clustered_rows() -> None:
    with pytest.raises(FormulaDomainError,match="DEPENDENT_SAMPLE_METHOD_REQUIRED"):
        chance_constrained_feasibility({"constraint_residuals":[-1,-1],"cluster_ids":["campaign","campaign"],"target_violation_probability":0.1,"confidence_level":0.95,"confidence_method":"EXACT_BINOMIAL_IID"})


def test_j03_seeded_shift_test_detects_separation() -> None:
    result=distribution_shift_test({"reference_samples":[0,0.1,0.2,0.3],"current_samples":[3,3.1,3.2,3.3],"bandwidth":0.5,"permutations":99,"seed":17,"alpha":0.1})
    assert result["seed"]==17
    assert result["shift_statistic"]>0
    assert result["p_value_or_e_value"]<=0.1


def test_j04_psd_and_permutation_invariance() -> None:
    left=log_determinant_diversity({"kernel":[[2,0.2],[0.2,1]],"jitter":0,"tolerance":1e-12})
    right=log_determinant_diversity({"kernel":[[1,0.2],[0.2,2]],"jitter":0,"tolerance":1e-12})
    assert left["log_determinant_diversity"]==pytest.approx(right["log_determinant_diversity"])
    with pytest.raises(FormulaDomainError,match="kernel_not_symmetric"):
        log_determinant_diversity({"kernel":[[1,1],[0,1]],"jitter":0})


def test_j05_likelihood_ratio_identity_and_support() -> None:
    result=rare_event_importance_sampling({"outcomes":[0,1,1,0],"log_target_density":[0]*4,"log_proposal_density":[0]*4})
    assert result["unnormalized_IS_estimate"]==pytest.approx(0.5)
    assert result["self_normalized_IS_estimate"]==pytest.approx(0.5)
    assert result["weight_effective_sample_size"]==pytest.approx(4)


@pytest.mark.parametrize("sense,primal,dual,gap",[("MINIMIZE",10,9,1),("MAXIMIZE",9,10,1)])
def test_j06_objective_sense_safe_gap(sense: str, primal: float, dual: float, gap: float) -> None:
    result=primal_dual_optimality_certificate({"objective_sense":sense,"primal_feasible_value":primal,"dual_bound":dual,"same_formulation_input_lock_proof":"same-lock"})
    assert result["absolute_gap"]==gap
    assert result["certificate_state"]=="VALID"


def test_j07_distortion_margin_certificate_passes_and_fails_closed() -> None:
    base={"linear":[-2.02,1.01],"quadratic":{"0,1":0.19},"offset":0,"prune_threshold":0.01,"quantization_step":0.1,"penalty_sufficiency_revalidated":True,"original_model_feasibility_preserved":True,"inverse_economic_map_ref":"identity"}
    passed=certified_qubo_sparsification_quantization({**base,"relevant_decision_margin":1})
    failed=certified_qubo_sparsification_quantization({**base,"relevant_decision_margin":0.01})
    assert passed["certificate_state"]=="VALID"
    assert passed["exhaustive_observed_maximum_distortion"]<=passed["maximum_objective_distortion_bound"]+1e-9
    assert failed["certificate_state"]=="REJECT_NO_CHANGE"


def test_j08_orbit_reduction_preserves_optimum_and_rejects_false_symmetry() -> None:
    objective={"00":0,"01":1,"10":1,"11":2}; feasible={key:True for key in objective}
    result=symmetry_breaking_orbit_reduction({"variable_count":2,"permutations":[[0,1],[1,0]],"objective_values":objective,"feasible_values":feasible,"objective_sense":"MINIMIZE"})
    assert result["representative_per_feasible_orbit_proof"]
    assert result["optimum_equivalence_preserved"]
    broken={**objective,"10":3}
    with pytest.raises(FormulaDomainError,match="objective_not_symmetric"):
        symmetry_breaking_orbit_reduction({"variable_count":2,"permutations":[[0,1],[1,0]],"objective_values":broken,"feasible_values":feasible})
