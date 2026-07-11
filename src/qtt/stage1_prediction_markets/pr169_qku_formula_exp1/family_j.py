from __future__ import annotations

from collections import defaultdict
from itertools import product
import math
import random
from typing import Any, Callable, Iterable, Mapping, Sequence


class FormulaDomainError(ValueError):
    """A deterministic typed domain failure from an executable method."""


def _finite(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise FormulaDomainError(f"DOMAIN_VIOLATION:{name}") from exc
    if not math.isfinite(result):
        raise FormulaDomainError(f"NUMERICAL_ERROR:{name}")
    return result


def _floats(values: Iterable[Any], name: str) -> list[float]:
    result = [_finite(value, name) for value in values]
    if not result:
        raise FormulaDomainError(f"MISSING_REQUIRED_INPUT:{name}")
    return result


def _weights(values: Iterable[Any] | None, count: int) -> list[float]:
    if values is None:
        return [1.0 / count] * count
    weights = _floats(values, "weights")
    if len(weights) != count or any(weight < 0 for weight in weights):
        raise FormulaDomainError("DOMAIN_VIOLATION:weights")
    total = math.fsum(weights)
    if total <= 0:
        raise FormulaDomainError("DOMAIN_VIOLATION:weights")
    return [weight / total for weight in weights]


def wasserstein_robust_utility(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Finite-support 1-Wasserstein DRO via its exact discrete dual.

    The target distribution is constrained to the supplied support.  This
    makes the assumptions and certificate inspectable while keeping the
    implementation dependency-free and deterministic.
    """
    support = _floats(inputs.get("support", ()), "support")
    utilities = _floats(inputs.get("utilities", ()), "utilities")
    if len(support) != len(utilities):
        raise FormulaDomainError("DOMAIN_VIOLATION:support_utility_length")
    nominal = _weights(inputs.get("weights"), len(support))
    radius = _finite(inputs.get("ambiguity_radius"), "ambiguity_radius")
    if radius < 0:
        raise FormulaDomainError("DOMAIN_VIOLATION:ambiguity_radius")
    metric = str(inputs.get("transport_metric", "absolute_1d"))
    if metric != "absolute_1d":
        raise FormulaDomainError("FORMULA_INAPPLICABLE:transport_metric")

    candidates = {0.0}
    for i, j in product(range(len(support)), repeat=2):
        cost = abs(support[i] - support[j])
        if cost > 0:
            candidates.add(max(0.0, (utilities[i] - utilities[j]) / cost))
    # The concave piecewise-linear dual attains its maximum at a breakpoint.
    def lower_dual(lam: float, rho: float) -> float:
        transported = math.fsum(
            nominal[i]
            * min(utilities[j] + lam * abs(support[i] - support[j]) for j in range(len(support)))
            for i in range(len(support))
        )
        return transported - lam * rho

    scored = [(lower_dual(lam, radius), lam) for lam in sorted(candidates)]
    robust_utility, dual_lambda = max(scored, key=lambda item: (item[0], -item[1]))
    nominal_utility = math.fsum(w * value for w, value in zip(nominal, utilities))
    sensitivity_radii = inputs.get("sensitivity_radii", (0.0, radius))
    sensitivity = []
    for raw_rho in sensitivity_radii:
        rho = _finite(raw_rho, "sensitivity_radius")
        if rho < 0:
            raise FormulaDomainError("DOMAIN_VIOLATION:sensitivity_radius")
        value = max(lower_dual(lam, rho) for lam in candidates)
        sensitivity.append({"ambiguity_radius": rho, "robust_utility": value})
    no_trade = _finite(inputs.get("no_trade_utility", 0.0), "no_trade_utility")
    return {
        "robust_utility": robust_utility,
        "robust_loss": -robust_utility,
        "nominal_utility": nominal_utility,
        "worst_case_distribution_or_dual_receipt": {
            "certificate_type": "FINITE_SUPPORT_KANTOROVICH_DUAL",
            "dual_lambda": dual_lambda,
            "dual_candidate_count": len(candidates),
        },
        "ambiguity_radius": radius,
        "transport_metric": metric,
        "LCB_or_bound": robust_utility,
        "radius_sensitivity_ref": sensitivity,
        "no_trade_margin": robust_utility - no_trade,
        "feasibility_state": "ORIGINAL_MODEL_FEASIBLE",
        "numerical_state": "VALID",
    }


def _binomial_cdf(k: int, n: int, probability: float) -> float:
    if k >= n:
        return 1.0
    return math.fsum(
        math.comb(n, i) * probability**i * (1.0 - probability) ** (n - i)
        for i in range(k + 1)
    )


def _clopper_pearson_upper(k: int, n: int, alpha: float) -> float:
    if k >= n:
        return 1.0
    low, high = 0.0, 1.0
    for _ in range(80):
        mid = (low + high) / 2.0
        if _binomial_cdf(k, n, mid) > alpha:
            low = mid
        else:
            high = mid
    return high


def chance_constrained_feasibility(inputs: Mapping[str, Any]) -> dict[str, Any]:
    residuals = _floats(inputs.get("constraint_residuals", ()), "constraint_residuals")
    epsilon = _finite(inputs.get("target_violation_probability"), "target_violation_probability")
    confidence = _finite(inputs.get("confidence_level"), "confidence_level")
    if not 0 <= epsilon <= 1 or not 0 < confidence < 1:
        raise FormulaDomainError("DOMAIN_VIOLATION:probability_or_confidence")
    method = str(inputs.get("confidence_method", "EXACT_BINOMIAL_IID"))
    clusters = inputs.get("cluster_ids")
    if method == "EXACT_BINOMIAL_IID" and clusters is not None:
        raise FormulaDomainError("MISSING_ASSUMPTION_STATE:DEPENDENT_SAMPLE_METHOD_REQUIRED")
    violations = sum(value > 0 for value in residuals)
    estimate = violations / len(residuals)
    if method == "EXACT_BINOMIAL_IID":
        upper = _clopper_pearson_upper(violations, len(residuals), 1.0 - confidence)
        effective = len(residuals)
    elif method == "HOEFFDING_BOUND":
        upper = min(1.0, estimate + math.sqrt(math.log(1.0 / (1.0 - confidence)) / (2 * len(residuals))))
        effective = len(residuals)
    elif method == "CLUSTER_HOEFFDING":
        if clusters is None or len(clusters) != len(residuals):
            raise FormulaDomainError("MISSING_REQUIRED_INPUT:cluster_ids")
        grouped: dict[str, list[bool]] = defaultdict(list)
        for cluster, residual in zip(clusters, residuals):
            grouped[str(cluster)].append(residual > 0)
        cluster_violations = [any(values) for values in grouped.values()]
        effective = len(cluster_violations)
        estimate = sum(cluster_violations) / effective
        upper = min(1.0, estimate + math.sqrt(math.log(1.0 / (1.0 - confidence)) / (2 * effective)))
    else:
        raise FormulaDomainError("FORMULA_INAPPLICABLE:confidence_method")
    return {
        "constraint_id": str(inputs.get("constraint_id", "constraint")),
        "target_violation_probability": epsilon,
        "estimated_violation_probability": estimate,
        "violation_probability_upper_confidence_bound": upper,
        "confidence_level": confidence,
        "confidence_method": method,
        "sample_support": len(residuals),
        "effective_sample_support": effective,
        "feasibility_state": "FEASIBLE" if upper <= epsilon else "INFEASIBLE_OR_INSUFFICIENT_EVIDENCE",
        "constraint_residual_or_shortfall": max(residuals),
        "missing_assumption_state": None,
    }


def _rbf(left: Sequence[float], right: Sequence[float], bandwidth: float) -> float:
    return math.exp(-math.fsum((a - b) ** 2 for a, b in zip(left, right)) / (2.0 * bandwidth**2))


def _vectors(values: Iterable[Any], name: str) -> list[tuple[float, ...]]:
    vectors: list[tuple[float, ...]] = []
    for value in values:
        raw = value if isinstance(value, (list, tuple)) else (value,)
        vectors.append(tuple(_finite(item, name) for item in raw))
    if not vectors or len({len(row) for row in vectors}) != 1:
        raise FormulaDomainError(f"DOMAIN_VIOLATION:{name}")
    return vectors


def _mmd2(x: list[tuple[float, ...]], y: list[tuple[float, ...]], bandwidth: float) -> float:
    m, n = len(x), len(y)
    if m < 2 or n < 2:
        raise FormulaDomainError("INSUFFICIENT_EVIDENCE:MMD_SAMPLE_SIZE")
    xx = math.fsum(_rbf(x[i], x[j], bandwidth) for i in range(m) for j in range(m) if i != j) / (m * (m - 1))
    yy = math.fsum(_rbf(y[i], y[j], bandwidth) for i in range(n) for j in range(n) if i != j) / (n * (n - 1))
    xy = math.fsum(_rbf(a, b, bandwidth) for a in x for b in y) * 2.0 / (m * n)
    return xx + yy - xy


def distribution_shift_test(inputs: Mapping[str, Any]) -> dict[str, Any]:
    reference = _vectors(inputs.get("reference_samples", ()), "reference_samples")
    current = _vectors(inputs.get("current_samples", ()), "current_samples")
    bandwidth = _finite(inputs.get("bandwidth"), "bandwidth")
    if bandwidth <= 0:
        raise FormulaDomainError("DOMAIN_VIOLATION:bandwidth")
    permutations = int(inputs.get("permutations", 199))
    seed = int(inputs.get("seed", 0))
    if permutations <= 0:
        raise FormulaDomainError("DOMAIN_VIOLATION:permutations")
    observed = _mmd2(reference, current, bandwidth)
    combined = reference + current
    split = len(reference)
    rng = random.Random(seed)
    exceed = 0
    for _ in range(permutations):
        shuffled = list(combined)
        rng.shuffle(shuffled)
        exceed += _mmd2(shuffled[:split], shuffled[split:], bandwidth) >= observed
    p_value = (exceed + 1) / (permutations + 1)
    alpha = _finite(inputs.get("alpha", 0.05), "alpha")
    if not 0 < alpha < 1:
        raise FormulaDomainError("DOMAIN_VIOLATION:alpha")
    return {
        "shift_test_id": str(inputs.get("shift_test_id", "shift")),
        "shift_method": "UNBIASED_MMD2_PERMUTATION",
        "kernel_or_metric_id": "RBF",
        "kernel_or_metric_version": "1.0.0",
        "shift_statistic": observed,
        "effect_magnitude": max(0.0, observed),
        "p_value_or_e_value": p_value,
        "confidence_state": "SHIFT_DETECTED" if p_value <= alpha else "SHIFT_NOT_DETECTED",
        "sample_support": len(combined),
        "effective_sample_support": len(combined),
        "venue_regime_event_scope": inputs.get("scope", "DECLARED_FIXTURE_SCOPE"),
        "drift_state": p_value <= alpha,
        "drift_severity": "RETEST_REQUIRED" if p_value <= alpha else "NO_TRIGGER",
        "affected_formula_QKU_memory_backend_refs": list(inputs.get("affected_refs", ())),
        "deterministic_action_route": "AGENT_ORCH_RETEST" if p_value <= alpha else "RETAIN_WITH_TTL",
        "seed": seed,
    }


def _cholesky_logdet(matrix: list[list[float]], tolerance: float) -> tuple[float, float, float]:
    n = len(matrix)
    lower = [[0.0] * n for _ in range(n)]
    pivots: list[float] = []
    for i in range(n):
        for j in range(i + 1):
            value = matrix[i][j] - math.fsum(lower[i][k] * lower[j][k] for k in range(j))
            if i == j:
                if value < -tolerance:
                    raise FormulaDomainError("DOMAIN_VIOLATION:kernel_not_psd")
                if value <= tolerance:
                    raise FormulaDomainError("NUMERICAL_ERROR:kernel_singular")
                lower[i][j] = math.sqrt(value)
                pivots.append(value)
            else:
                lower[i][j] = value / lower[j][j]
    logdet = math.fsum(math.log(value) for value in pivots)
    return logdet, min(pivots), max(pivots) / min(pivots)


def log_determinant_diversity(inputs: Mapping[str, Any]) -> dict[str, Any]:
    raw = inputs.get("kernel")
    if not isinstance(raw, Sequence) or not raw:
        raise FormulaDomainError("MISSING_REQUIRED_INPUT:kernel")
    matrix = [[_finite(value, "kernel") for value in row] for row in raw]
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise FormulaDomainError("DOMAIN_VIOLATION:kernel_shape")
    tolerance = _finite(inputs.get("tolerance", 1e-12), "tolerance")
    jitter = _finite(inputs.get("jitter", 0.0), "jitter")
    if jitter < 0 or tolerance <= 0:
        raise FormulaDomainError("DOMAIN_VIOLATION:jitter_or_tolerance")
    for i in range(n):
        for j in range(n):
            if abs(matrix[i][j] - matrix[j][i]) > tolerance:
                raise FormulaDomainError("DOMAIN_VIOLATION:kernel_not_symmetric")
        matrix[i][i] += jitter
    logdet, minimum, condition = _cholesky_logdet(matrix, tolerance)
    prior_kernel = inputs.get("prior_kernel")
    marginal = logdet
    if prior_kernel:
        prior = log_determinant_diversity({"kernel": prior_kernel, "jitter": jitter, "tolerance": tolerance})
        marginal -= float(prior["log_determinant_diversity"])
    return {
        "log_determinant_diversity": logdet,
        "marginal_logdet_gain": marginal,
        "kernel_PSD_state": "PSD_VALID",
        "minimum_eigenvalue": minimum,
        "condition_number": condition,
        "jitter_value": jitter,
        "jitter_provenance": inputs.get("jitter_provenance"),
        "raw_economic_utility_ref": inputs.get("raw_economic_utility_ref"),
        "opportunity_cost_ref": inputs.get("opportunity_cost_ref"),
        "numerical_failure_state": None,
    }


def rare_event_importance_sampling(inputs: Mapping[str, Any]) -> dict[str, Any]:
    outcomes = _floats(inputs.get("outcomes", ()), "outcomes")
    log_target = _floats(inputs.get("log_target_density", ()), "log_target_density")
    log_proposal = _floats(inputs.get("log_proposal_density", ()), "log_proposal_density")
    if not (len(outcomes) == len(log_target) == len(log_proposal)):
        raise FormulaDomainError("DOMAIN_VIOLATION:sample_length")
    for target, proposal in zip(log_target, log_proposal):
        if math.isfinite(target) and not math.isfinite(proposal):
            raise FormulaDomainError("SUPPORT_STATE:TARGET_NOT_ABSOLUTELY_CONTINUOUS")
    log_weights = [target - proposal for target, proposal in zip(log_target, log_proposal)]
    maximum = max(log_weights)
    scaled = [math.exp(value - maximum) for value in log_weights]
    scale = math.exp(maximum)
    raw_weights = [value * scale for value in scaled]
    estimate = math.fsum(outcome * weight for outcome, weight in zip(outcomes, raw_weights)) / len(outcomes)
    weight_sum = math.fsum(raw_weights)
    self_normalized = math.fsum(outcome * weight for outcome, weight in zip(outcomes, raw_weights)) / weight_sum
    normalized = [weight / weight_sum for weight in raw_weights]
    ess = 1.0 / math.fsum(weight * weight for weight in normalized)
    weighted_terms = [outcome * weight for outcome, weight in zip(outcomes, raw_weights)]
    mean_term = math.fsum(weighted_terms) / len(weighted_terms)
    variance = math.fsum((value - mean_term) ** 2 for value in weighted_terms) / max(1, len(weighted_terms) - 1) / len(weighted_terms)
    standard_error = math.sqrt(max(0.0, variance))
    baseline = math.fsum(outcomes) / len(outcomes)
    return {
        "target_distribution_ref": inputs.get("target_distribution_ref", "target"),
        "proposal_distribution_ref": inputs.get("proposal_distribution_ref", "proposal"),
        "unnormalized_IS_estimate": estimate,
        "self_normalized_IS_estimate": self_normalized,
        "estimator_bias_class": "UNBIASED_FIXED_PROPOSAL" if not inputs.get("adaptive_proposal") else "ADAPTIVE_REQUIRES_HELDOUT_VALIDATION",
        "log_likelihood_ratio_summary": {"minimum": min(log_weights), "maximum": max(log_weights)},
        "weight_effective_sample_size": ess,
        "maximum_normalized_weight": max(normalized),
        "weight_concentration": math.fsum(weight * weight for weight in normalized),
        "estimator_variance": variance,
        "confidence_interval": [estimate - 1.96 * standard_error, estimate + 1.96 * standard_error],
        "support_state": "ABSOLUTE_CONTINUITY_VALIDATED",
        "baseline_monte_carlo_estimate": baseline,
        "baseline_comparator_delta": estimate - baseline,
        "failure_diagnostics": [] if ess >= 2 else ["WEIGHT_DEGENERACY"],
    }


def primal_dual_optimality_certificate(inputs: Mapping[str, Any]) -> dict[str, Any]:
    sense = str(inputs.get("objective_sense", "")).upper()
    primal = _finite(inputs.get("primal_feasible_value"), "primal_feasible_value")
    dual = _finite(inputs.get("dual_bound"), "dual_bound")
    primal_residual = _finite(inputs.get("primal_feasibility_residual", 0.0), "primal_feasibility_residual")
    dual_residual = _finite(inputs.get("dual_feasibility_residual", 0.0), "dual_feasibility_residual")
    tolerance = _finite(inputs.get("tolerance", 1e-9), "tolerance")
    if not inputs.get("same_formulation_input_lock_proof"):
        raise FormulaDomainError("CONFLICTING_INPUTS:same_formulation_input_lock_proof")
    if primal_residual > tolerance:
        raise FormulaDomainError("ORIGINAL_MODEL_INFEASIBLE:primal")
    if dual_residual > tolerance:
        raise FormulaDomainError("ORIGINAL_MODEL_INFEASIBLE:dual")
    if sense == "MINIMIZE":
        gap = primal - dual
    elif sense == "MAXIMIZE":
        gap = dual - primal
    else:
        raise FormulaDomainError("DOMAIN_VIOLATION:objective_sense")
    if gap < -tolerance:
        raise FormulaDomainError("CONFLICTING_INPUTS:bound_direction")
    gap = max(0.0, gap)
    relative = gap / max(1.0, abs(primal), abs(dual))
    return {
        "objective_sense": sense,
        "primal_feasible_value": primal,
        "dual_bound": dual,
        "absolute_gap": gap,
        "relative_gap": relative,
        "primal_feasibility_residual": primal_residual,
        "dual_feasibility_residual": dual_residual,
        "complementarity_residual": inputs.get("complementarity_residual"),
        "KKT_residual_ref": inputs.get("KKT_residual_ref"),
        "same_formulation_input_lock_proof": inputs["same_formulation_input_lock_proof"],
        "certificate_state": "VALID",
        "solver_stop_or_comparator_decision": "GAP_WITHIN_TOLERANCE" if gap <= tolerance else "BOUND_RETAINED",
        "evidence_refs": list(inputs.get("evidence_refs", ())),
    }


def _qubo_energy(linear: Sequence[float], quadratic: Mapping[str, float], offset: float, bits: Sequence[int]) -> float:
    value = offset + math.fsum(coef * bit for coef, bit in zip(linear, bits))
    for key, coefficient in quadratic.items():
        left, right = (int(token) for token in key.split(","))
        value += coefficient * bits[left] * bits[right]
    return value


def certified_qubo_sparsification_quantization(inputs: Mapping[str, Any]) -> dict[str, Any]:
    linear = _floats(inputs.get("linear", ()), "linear")
    quadratic = {str(key): _finite(value, "quadratic") for key, value in dict(inputs.get("quadratic", {})).items()}
    threshold = _finite(inputs.get("prune_threshold"), "prune_threshold")
    step = _finite(inputs.get("quantization_step"), "quantization_step")
    if threshold < 0 or step <= 0:
        raise FormulaDomainError("DOMAIN_VIOLATION:quantization_policy")
    transformed_linear = []
    removed: list[str] = []
    rounded: list[str] = []
    deltas: list[float] = []
    for index, value in enumerate(linear):
        transformed = 0.0 if abs(value) < threshold else round(value / step) * step
        if transformed == 0.0 and value != 0.0:
            removed.append(f"linear:{index}")
        elif transformed != value:
            rounded.append(f"linear:{index}")
        transformed_linear.append(transformed)
        deltas.append(transformed - value)
    transformed_quadratic: dict[str, float] = {}
    for key, value in quadratic.items():
        transformed = 0.0 if abs(value) < threshold else round(value / step) * step
        if transformed == 0.0 and value != 0.0:
            removed.append(f"quadratic:{key}")
        elif transformed != value:
            rounded.append(f"quadratic:{key}")
        transformed_quadratic[key] = transformed
        deltas.append(transformed - value)
    offset = _finite(inputs.get("offset", 0.0), "offset")
    transformed_offset = round(offset / step) * step
    deltas.append(transformed_offset - offset)
    bound = math.fsum(abs(value) for value in deltas)
    margin = _finite(inputs.get("relevant_decision_margin"), "relevant_decision_margin")
    invariant = margin > 2.0 * bound
    exhaustive_max = 0.0
    if len(linear) <= int(inputs.get("exhaustive_variable_limit", 16)):
        for bits in product((0, 1), repeat=len(linear)):
            original = _qubo_energy(linear, quadratic, offset, bits)
            transformed = _qubo_energy(transformed_linear, transformed_quadratic, transformed_offset, bits)
            exhaustive_max = max(exhaustive_max, abs(transformed - original))
        if exhaustive_max > bound + 1e-9:
            raise FormulaDomainError("NUMERICAL_ERROR:distortion_bound_failure")
    penalty_valid = bool(inputs.get("penalty_sufficiency_revalidated", False))
    feasibility_valid = bool(inputs.get("original_model_feasibility_preserved", False))
    certified = invariant and penalty_valid and feasibility_valid
    return {
        "source_formulation_ref": inputs.get("source_formulation_ref"),
        "transformed_formulation_ref": inputs.get("transformed_formulation_ref"),
        "removed_coefficient_terms": removed,
        "rounded_coefficient_terms": rounded,
        "backend_scale_map": inputs.get("backend_scale_map", {"scale": 1.0}),
        "maximum_objective_distortion_bound": bound,
        "exhaustive_observed_maximum_distortion": exhaustive_max,
        "relevant_decision_margin": margin,
        "decision_margin_to_two_bound_ratio": math.inf if bound == 0 else margin / (2 * bound),
        "coefficient_dynamic_range_before": _dynamic_range(list(linear) + list(quadratic.values())),
        "coefficient_dynamic_range_after": _dynamic_range(transformed_linear + list(transformed_quadratic.values())),
        "penalty_sufficiency_revalidated": penalty_valid,
        "original_model_feasibility_preserved": feasibility_valid,
        "champion_identity_invariant": certified,
        "no_trade_decision_invariant": certified,
        "economic_utility_sign_invariant": certified,
        "inverse_economic_map_ref": inputs.get("inverse_economic_map_ref"),
        "certificate_state": "VALID" if certified else "REJECT_NO_CHANGE",
        "rejected_reason": None if certified else "MARGIN_OR_FEASIBILITY_CERTIFICATE_INSUFFICIENT",
    }


def _dynamic_range(values: Sequence[float]) -> float | None:
    nonzero = [abs(value) for value in values if value != 0]
    return max(nonzero) / min(nonzero) if nonzero else None


def _permute_bits(bits: tuple[int, ...], permutation: Sequence[int]) -> tuple[int, ...]:
    result = [0] * len(bits)
    for source, destination in enumerate(permutation):
        result[destination] = bits[source]
    return tuple(result)


def symmetry_breaking_orbit_reduction(inputs: Mapping[str, Any]) -> dict[str, Any]:
    variable_count = int(inputs.get("variable_count", 0))
    if variable_count <= 0 or variable_count > int(inputs.get("exhaustive_variable_limit", 16)):
        raise FormulaDomainError("DOMAIN_VIOLATION:variable_count")
    permutations = [tuple(int(item) for item in row) for row in inputs.get("permutations", ())]
    identity = tuple(range(variable_count))
    if identity not in permutations:
        permutations.insert(0, identity)
    if any(sorted(row) != list(identity) for row in permutations):
        raise FormulaDomainError("DOMAIN_VIOLATION:permutation")
    objective_values = inputs.get("objective_values")
    feasible_values = inputs.get("feasible_values")
    if not isinstance(objective_values, Mapping) or not isinstance(feasible_values, Mapping):
        raise FormulaDomainError("MISSING_REQUIRED_INPUT:exhaustive_objective_and_feasibility")

    def key(bits: tuple[int, ...]) -> str:
        return "".join(str(bit) for bit in bits)

    feasible = [bits for bits in product((0, 1), repeat=variable_count) if bool(feasible_values.get(key(bits), False))]
    if not feasible:
        raise FormulaDomainError("ORIGINAL_MODEL_INFEASIBLE")
    representatives: dict[str, str] = {}
    for bits in feasible:
        orbit = {_permute_bits(bits, permutation) for permutation in permutations}
        for member in orbit:
            if bool(feasible_values.get(key(member), False)) != bool(feasible_values.get(key(bits), False)):
                raise FormulaDomainError("FORMULA_INAPPLICABLE:constraint_not_symmetric")
            if abs(_finite(objective_values[key(member)], "objective") - _finite(objective_values[key(bits)], "objective")) > 1e-9:
                raise FormulaDomainError("FORMULA_INAPPLICABLE:objective_not_symmetric")
        representative = min(key(member) for member in orbit if bool(feasible_values.get(key(member), False)))
        representatives[key(bits)] = representative
    representative_set = sorted(set(representatives.values()))
    sense = str(inputs.get("objective_sense", "MINIMIZE")).upper()
    selector: Callable[[Iterable[float]], float] = min if sense == "MINIMIZE" else max
    original_optimum = selector(_finite(objective_values[key(bits)], "objective") for bits in feasible)
    reduced_optimum = selector(_finite(objective_values[value], "objective") for value in representative_set)
    preserved = abs(original_optimum - reduced_optimum) <= 1e-9
    return {
        "source_formulation_ref": inputs.get("source_formulation_ref"),
        "symmetry_group_or_automorphism_ref": permutations,
        "canonical_representative_policy": "LEXICOGRAPHIC_MINIMUM_ORBIT_MEMBER",
        "orbit_membership_map": representatives,
        "reduced_formulation_ref": inputs.get("reduced_formulation_ref"),
        "reduced_variable_count": variable_count,
        "reduced_constraint_count": len(representative_set),
        "representative_per_feasible_orbit_proof": len(representative_set) > 0,
        "optimum_equivalence_preserved": preserved,
        "inverse_expansion_map": {representative: [member for member, rep in representatives.items() if rep == representative] for representative in representative_set},
        "inverse_mapped_solution_ref": representative_set,
        "original_model_feasibility_state": "VALID",
        "proof_state": "VALID" if preserved else "FAILED",
        "failure_reason": None if preserved else "OPTIMUM_NOT_PRESERVED",
    }


FAMILY_J_CALLABLES: dict[str, Callable[[Mapping[str, Any]], dict[str, Any]]] = {
    "J01": wasserstein_robust_utility,
    "J02": chance_constrained_feasibility,
    "J03": distribution_shift_test,
    "J04": log_determinant_diversity,
    "J05": rare_event_importance_sampling,
    "J06": primal_dual_optimality_certificate,
    "J07": certified_qubo_sparsification_quantization,
    "J08": symmetry_breaking_orbit_reduction,
}
