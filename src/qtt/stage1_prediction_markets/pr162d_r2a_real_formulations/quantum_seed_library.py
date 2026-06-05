"""Deterministic local quantum formulation shape builders for PR162D-R2A."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ShapeBuilder = Callable[[dict[str, Any]], dict[str, Any]]


def _candidate_ids(inputs: dict[str, Any]) -> list[str]:
    return [str(item["candidate_id"]) for item in inputs["candidates"]]


def _binary_variables(ids: list[str]) -> list[dict[str, str]]:
    return [{"name": f"x_{candidate_id}", "domain": "binary", "meaning": f"select candidate {candidate_id}"} for candidate_id in ids]


def build_qubo_market_bundle_selection(inputs: dict[str, Any]) -> dict[str, Any]:
    ids = _candidate_ids(inputs)
    return {
        "shape_type": "QUBO",
        "objective": "-sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j) + lambda_budget*(sum(cost_i*x_i)-budget)^2 + lambda_exposure*(sum(exposure_i*x_i)-max_exposure)^2",
        "variables": _binary_variables(ids),
        "domains": {
            "x_i": "binary",
            "reward_i": "real",
            "cost_i": "nonnegative_real",
            "covariance_ij": "real",
            "budget": "positive_real",
            "exposure_i": "nonnegative_real",
        },
        "constraints": [],
        "no_constraint_reason": "Budget and exposure are represented as quadratic penalty terms in the QUBO objective.",
        "penalties": ["budget_penalty", "exposure_penalty", "risk_covariance_penalty"],
        "mapping_rationale": {
            "QUBO_COMPATIBLE": True,
            "BQM_COMPATIBLE": True,
            "ISING_COMPATIBLE": True,
            "CQM_COMPATIBLE": True,
            "ising_transform": "x=(1+s)/2",
        },
        "coefficients": {
            "rewards": [float(item["reward"]) for item in inputs["candidates"]],
            "costs": [float(item["cost"]) for item in inputs["candidates"]],
            "covariance": inputs["covariance"],
            "budget": float(inputs["budget"]),
            "max_exposure": float(inputs["max_exposure"]),
        },
        "classical_comparator_ref": "CLASSICAL_COMPARATOR::GREEDY_MARKET_BUNDLE_SELECTION",
        "backend_execution": False,
        "quantum_advantage_claim": False,
    }


def build_cqm_constrained_capital_allocation(inputs: dict[str, Any]) -> dict[str, Any]:
    ids = _candidate_ids(inputs)
    variables = _binary_variables(ids) + [
        {"name": f"size_{candidate_id}", "domain": "nonnegative_real", "meaning": f"capital size for {candidate_id}"}
        for candidate_id in ids
    ]
    return {
        "shape_type": "CQM",
        "objective": "maximize sum(x_i*expected_net_value_i) - lambda_drawdown*drawdown_risk(x) - lambda_latency*latency_cost(x) - lambda_slippage*slippage_cost(x)",
        "variables": variables,
        "domains": {"x_i": "binary", "size_i": "nonnegative_real", "expected_net_value_i": "real"},
        "constraints": [
            "sum(size_i) <= capital_budget",
            "sum(exposure_i*size_i) <= max_exposure",
            "x_i in {0,1}",
            "size_i >= 0",
        ],
        "penalties": [],
        "no_penalty_reason": "Capital and exposure are represented as explicit CQM constraints.",
        "mapping_rationale": {
            "CQM_COMPATIBLE": True,
            "QUBO_COMPATIBLE": True,
            "QUBO_COMPATIBLE_REASON": "Explicit constraints can be converted to penalties for a QUBO candidate.",
        },
        "coefficients": {
            "expected_net_values": [float(item["expected_net_value"]) for item in inputs["candidates"]],
            "capital_budget": float(inputs["capital_budget"]),
            "max_exposure": float(inputs["max_exposure"]),
        },
        "classical_comparator_ref": "CLASSICAL_COMPARATOR::MIXED_INTEGER_PROGRAMMING_COMPARATOR",
        "backend_execution": False,
        "quantum_advantage_claim": False,
    }


def build_qubo_parameter_stack_selection(inputs: dict[str, Any]) -> dict[str, Any]:
    ids = _candidate_ids(inputs)
    return {
        "shape_type": "QUBO",
        "objective": "-sum(stack_score_i*x_i) + lambda_onehot*(sum(x_i)-1)^2 + lambda_incompat*sum(incompatibility_ij*x_i*x_j)",
        "variables": _binary_variables(ids),
        "domains": {"x_i": "binary", "stack_score_i": "real", "incompatibility_ij": "nonnegative_real"},
        "constraints": [],
        "no_constraint_reason": "One stack selected by one-hot penalty.",
        "penalties": ["one_hot_penalty", "incompatibility_penalty"],
        "mapping_rationale": {"QUBO_COMPATIBLE": True, "BQM_COMPATIBLE": True, "ISING_COMPATIBLE": True},
        "coefficients": {
            "stack_scores": [float(item["stack_score"]) for item in inputs["candidates"]],
            "incompatibility": inputs["incompatibility"],
        },
        "classical_comparator_ref": "CLASSICAL_COMPARATOR::DETERMINISTIC_CANDIDATE_RANKING",
        "backend_execution": False,
        "quantum_advantage_claim": False,
    }


def build_latency_adjusted_opportunity_selection(inputs: dict[str, Any]) -> dict[str, Any]:
    ids = _candidate_ids(inputs)
    return {
        "shape_type": "QUBO",
        "objective": "-sum(expected_net_value_i*x_i) + lambda_latency*sum(latency_cost_i*x_i) + lambda_slippage*sum(slippage_cost_i*x_i) + lambda_risk*portfolio_risk(x)",
        "variables": _binary_variables(ids),
        "domains": {"x_i": "binary", "expected_net_value_i": "real", "latency_cost_i": "nonnegative_real"},
        "constraints": [],
        "no_constraint_reason": "Opportunity selection is represented as a penalty objective for batch scoring.",
        "penalties": ["latency_penalty", "slippage_penalty", "portfolio_risk_penalty"],
        "mapping_rationale": {"QUBO_COMPATIBLE": True, "BQM_COMPATIBLE": True, "ISING_COMPATIBLE": True},
        "coefficients": {
            "expected_net_values": [float(item["expected_net_value"]) for item in inputs["candidates"]],
            "latency_costs": [float(item["latency_cost"]) for item in inputs["candidates"]],
        },
        "classical_comparator_ref": "CLASSICAL_COMPARATOR::RISK_ADJUSTED_SCORE_RANKING",
        "backend_execution": False,
        "quantum_advantage_claim": False,
    }


def build_ising_binary_selection(inputs: dict[str, Any]) -> dict[str, Any]:
    ids = _candidate_ids(inputs)
    return {
        "shape_type": "ISING",
        "objective": "sum(h_i*s_i) + sum(J_ij*s_i*s_j), where s_i in {-1,1}",
        "variables": [{"name": f"s_{candidate_id}", "domain": "spin", "meaning": f"spin select candidate {candidate_id}"} for candidate_id in ids],
        "domains": {"s_i": "spin_minus_one_plus_one", "h_i": "real", "J_ij": "real"},
        "constraints": [],
        "no_constraint_reason": "Binary selection is encoded directly in spin variables.",
        "penalties": ["pairwise_interaction_penalty"],
        "mapping_rationale": {"ISING_COMPATIBLE": True, "QUBO_COMPATIBLE": True, "binary_spin_transform": "x=(1+s)/2"},
        "coefficients": {"h": inputs["h"], "J": inputs["J"]},
        "classical_comparator_ref": "CLASSICAL_COMPARATOR::BRUTE_FORCE_BINARY_ENUMERATION",
        "backend_execution": False,
        "quantum_advantage_claim": False,
    }


def build_qaoa_candidate_selection_shape(inputs: dict[str, Any]) -> dict[str, Any]:
    shape = build_qubo_market_bundle_selection(inputs)
    shape["shape_type"] = "QAOA_QUBO_SHAPE"
    shape["qaoa_suitability_rationale"] = "Binary quadratic objective can be represented as a cost Hamiltonian candidate for QAOA research routing."
    shape["classical_comparator_ref"] = "CLASSICAL_COMPARATOR::GREEDY_MARKET_BUNDLE_SELECTION"
    return shape


def build_annealing_candidate_selection_shape(inputs: dict[str, Any]) -> dict[str, Any]:
    shape = build_qubo_market_bundle_selection(inputs)
    shape["shape_type"] = "ANNEALING_BQM_SHAPE"
    shape["annealing_suitability_rationale"] = "QUBO/BQM candidate shape can be sampled by an annealing-style backend in later research, but PR162D-R2A does not execute one."
    return shape


def build_bqm_risk_balanced_selection(inputs: dict[str, Any]) -> dict[str, Any]:
    shape = build_qubo_market_bundle_selection(inputs)
    shape["shape_type"] = "BQM"
    shape["objective"] = "-sum(reward_i*x_i) + lambda_risk*sum(covariance_ij*x_i*x_j)"
    shape["penalties"] = ["risk_covariance_penalty"]
    shape["classical_comparator_ref"] = "CLASSICAL_COMPARATOR::MEAN_VARIANCE_GREEDY_COMPARATOR"
    return shape


def build_cqm_route_fill_allocation(inputs: dict[str, Any]) -> dict[str, Any]:
    ids = _candidate_ids(inputs)
    return {
        "shape_type": "CQM",
        "objective": "maximize sum(route_unlock_score_i*x_i) - lambda_complexity*sum(complexity_i*x_i)",
        "variables": _binary_variables(ids),
        "domains": {"x_i": "binary", "route_unlock_score_i": "real", "complexity_i": "nonnegative_real"},
        "constraints": ["sum(route_fill_cost_i*x_i) <= route_fill_budget"],
        "penalties": [],
        "no_penalty_reason": "Route-fill budget is kept as an explicit CQM constraint.",
        "mapping_rationale": {"CQM_COMPATIBLE": True, "QUBO_COMPATIBLE": True},
        "coefficients": {
            "route_unlock_scores": [float(item["route_unlock_score"]) for item in inputs["candidates"]],
            "route_fill_budget": float(inputs["route_fill_budget"]),
        },
        "classical_comparator_ref": "CLASSICAL_COMPARATOR::ROUTE_FILL_PRIORITY_ORDER",
        "backend_execution": False,
        "quantum_advantage_claim": False,
    }


@dataclass(frozen=True)
class QuantumSpec:
    quantum_formulation_id: str
    objective: str
    build_shape: ShapeBuilder
    domain_family_key: str
    subfamily_key: str
    variant_key: str
    variables: tuple[str, ...]
    domains: dict[str, str]
    constraints: tuple[str, ...]
    penalties: tuple[str, ...]
    mapping_rationale: dict[str, Any]
    classical_comparator_ref: str
    test_inputs: dict[str, Any]
    compute_tier: str = "TIER_4_QUANTUM_OR_HYBRID_BATCH_OPTIMIZER"
    latency_class: str = "QUANTUM_BATCH_ONLY"

    @property
    def callable_ref(self) -> str:
        return f"{__name__}:{self.build_shape.__name__}"

    def test_vector(self) -> dict[str, Any]:
        shape = self.build_shape(dict(self.test_inputs))
        return {
            "test_vector_id": f"PR162D_R2A_TV_QUANTUM::{self.quantum_formulation_id}",
            "callable_ref": self.callable_ref,
            "inputs": self.test_inputs,
            "expected_shape_keys": ["objective", "variables", "domains", "classical_comparator_ref"],
            "expected_outputs": {
                "shape_type": shape["shape_type"],
                "variable_count": len(shape["variables"]),
                "classical_comparator_ref": shape["classical_comparator_ref"],
            },
            "tolerance": 0.0,
            "source_truth_status": "OWNER_TEMPLATE",
            "candidate_truth_status": "CANDIDATE",
            "live_order_authority": False,
        }


@dataclass(frozen=True)
class ClassicalComparatorSpec:
    comparator_id: str
    comparator_family: str
    callable_ref: str
    procedure: str
    compared_quantum_family: str
    test_vector_ref: str


def _bundle_inputs() -> dict[str, Any]:
    return {
        "budget": 60.0,
        "max_exposure": 50.0,
        "covariance": [[0.1, 0.02], [0.02, 0.2]],
        "candidates": [
            {"candidate_id": "A", "reward": 0.2, "cost": 20.0, "expected_net_value": 0.1, "latency_cost": 0.01, "route_unlock_score": 0.8, "stack_score": 0.7},
            {"candidate_id": "B", "reward": 0.1, "cost": 30.0, "expected_net_value": 0.08, "latency_cost": 0.02, "route_unlock_score": 0.6, "stack_score": 0.5},
        ],
        "capital_budget": 60.0,
        "incompatibility": [[0, 1], [1, 0]],
        "h": [0.1, -0.2],
        "J": [[0, 0.05], [0.05, 0]],
        "route_fill_budget": 3.0,
    }


def quantum_specs() -> list[QuantumSpec]:
    base = _bundle_inputs()
    definitions = [
        ("QUBO_MARKET_BUNDLE_SELECTION", "QUBO_market_bundle_selection", "owner_template_v1", build_qubo_market_bundle_selection, "CLASSICAL_COMPARATOR::GREEDY_MARKET_BUNDLE_SELECTION"),
        ("CQM_CONSTRAINED_CAPITAL_ALLOCATION", "CQM_capital_allocation", "owner_template_v1", build_cqm_constrained_capital_allocation, "CLASSICAL_COMPARATOR::MIXED_INTEGER_PROGRAMMING_COMPARATOR"),
        ("QUBO_PARAMETER_STACK_SELECTION", "QUBO_parameter_stack_selection", "owner_template_v1", build_qubo_parameter_stack_selection, "CLASSICAL_COMPARATOR::DETERMINISTIC_CANDIDATE_RANKING"),
        ("LATENCY_ADJUSTED_OPPORTUNITY_SELECTION", "QUBO_latency_adjusted_opportunity", "owner_template_v1", build_latency_adjusted_opportunity_selection, "CLASSICAL_COMPARATOR::RISK_ADJUSTED_SCORE_RANKING"),
        ("ISING_BINARY_SELECTION", "Ising_binary_selection", "owner_template_v1", build_ising_binary_selection, "CLASSICAL_COMPARATOR::BRUTE_FORCE_BINARY_ENUMERATION"),
        ("QAOA_CANDIDATE_SELECTION", "QAOA_candidate_selection", "owner_template_v1", build_qaoa_candidate_selection_shape, "CLASSICAL_COMPARATOR::GREEDY_MARKET_BUNDLE_SELECTION"),
        ("ANNEALING_CANDIDATE_SELECTION", "annealing_candidate_selection", "owner_template_v1", build_annealing_candidate_selection_shape, "CLASSICAL_COMPARATOR::GREEDY_MARKET_BUNDLE_SELECTION"),
        ("BQM_RISK_BALANCED_SELECTION", "BQM_risk_balanced_selection", "owner_template_v1", build_bqm_risk_balanced_selection, "CLASSICAL_COMPARATOR::MEAN_VARIANCE_GREEDY_COMPARATOR"),
        ("CQM_ROUTE_FILL_ALLOCATION", "CQM_route_fill_allocation", "owner_template_v1", build_cqm_route_fill_allocation, "CLASSICAL_COMPARATOR::ROUTE_FILL_PRIORITY_ORDER"),
    ]
    extras = [
        ("QUBO_STAGE1_SIGNAL_BUNDLE", "QUBO_market_bundle_selection", "stage1_signal_bundle_v1", build_qubo_market_bundle_selection, "CLASSICAL_COMPARATOR::GREEDY_MARKET_BUNDLE_SELECTION"),
        ("QUBO_LIQUIDITY_BUNDLE", "QUBO_market_bundle_selection", "liquidity_bundle_v1", build_qubo_market_bundle_selection, "CLASSICAL_COMPARATOR::GREEDY_MARKET_BUNDLE_SELECTION"),
        ("QUBO_RISK_CAPPED_BUNDLE", "QUBO_market_bundle_selection", "risk_capped_v1", build_qubo_market_bundle_selection, "CLASSICAL_COMPARATOR::MEAN_VARIANCE_GREEDY_COMPARATOR"),
        ("QUBO_CROSS_MARKET_BUNDLE", "QUBO_market_bundle_selection", "cross_market_v1", build_qubo_market_bundle_selection, "CLASSICAL_COMPARATOR::DIVERSIFIED_GREEDY_COMPARATOR"),
        ("QUBO_REPLAY_VALUE_BUNDLE", "QUBO_market_bundle_selection", "replay_value_v1", build_qubo_market_bundle_selection, "CLASSICAL_COMPARATOR::REPLAY_VALUE_RANKING_COMPARATOR"),
        ("QUBO_PAPER_VALUE_BUNDLE", "QUBO_market_bundle_selection", "paper_value_v1", build_qubo_market_bundle_selection, "CLASSICAL_COMPARATOR::PAPER_VALUE_RANKING_COMPARATOR"),
        ("CQM_CAPITAL_BUDGET_STRICT", "CQM_capital_allocation", "capital_budget_strict_v1", build_cqm_constrained_capital_allocation, "CLASSICAL_COMPARATOR::MIXED_INTEGER_PROGRAMMING_COMPARATOR"),
        ("CQM_EXPOSURE_BUDGET_STRICT", "CQM_capital_allocation", "exposure_budget_strict_v1", build_cqm_constrained_capital_allocation, "CLASSICAL_COMPARATOR::MIXED_INTEGER_PROGRAMMING_COMPARATOR"),
        ("QUBO_STACK_ONEHOT", "QUBO_parameter_stack_selection", "onehot_v1", build_qubo_parameter_stack_selection, "CLASSICAL_COMPARATOR::DETERMINISTIC_CANDIDATE_RANKING"),
        ("QUBO_STACK_INCOMPATIBILITY", "QUBO_parameter_stack_selection", "incompatibility_v1", build_qubo_parameter_stack_selection, "CLASSICAL_COMPARATOR::PARAMETER_STACK_SELECTOR"),
        ("QUBO_LATENCY_ONLY", "QUBO_latency_adjusted_opportunity", "latency_only_v1", build_latency_adjusted_opportunity_selection, "CLASSICAL_COMPARATOR::RISK_ADJUSTED_SCORE_RANKING"),
        ("QUBO_SLIPPAGE_ONLY", "QUBO_latency_adjusted_opportunity", "slippage_only_v1", build_latency_adjusted_opportunity_selection, "CLASSICAL_COMPARATOR::RISK_ADJUSTED_SCORE_RANKING"),
        ("ISING_OPPORTUNITY_SPIN", "Ising_binary_selection", "opportunity_spin_v1", build_ising_binary_selection, "CLASSICAL_COMPARATOR::BRUTE_FORCE_BINARY_ENUMERATION"),
        ("QAOA_RISK_SELECTION", "QAOA_candidate_selection", "risk_selection_v1", build_qaoa_candidate_selection_shape, "CLASSICAL_COMPARATOR::MEAN_VARIANCE_GREEDY_COMPARATOR"),
        ("ANNEALING_ROUTE_SELECTION", "annealing_candidate_selection", "route_selection_v1", build_annealing_candidate_selection_shape, "CLASSICAL_COMPARATOR::ROUTE_FILL_PRIORITY_ORDER"),
        ("BQM_LOW_CORRELATION_SELECTION", "BQM_risk_balanced_selection", "low_correlation_v1", build_bqm_risk_balanced_selection, "CLASSICAL_COMPARATOR::MEAN_VARIANCE_GREEDY_COMPARATOR"),
    ]
    specs: list[QuantumSpec] = []
    for quantum_id, subfamily, variant, builder, comparator in [*definitions, *extras]:
        shape = builder(dict(base))
        specs.append(
            QuantumSpec(
                quantum_formulation_id=quantum_id,
                objective=shape["objective"],
                build_shape=builder,
                domain_family_key="quantum_bundle_selection_optimizer",
                subfamily_key=subfamily,
                variant_key=variant,
                variables=tuple(variable["name"] for variable in shape["variables"]),
                domains=dict(shape["domains"]),
                constraints=tuple(shape.get("constraints", [])),
                penalties=tuple(shape.get("penalties", [])),
                mapping_rationale=dict(shape["mapping_rationale"]),
                classical_comparator_ref=comparator,
                test_inputs=base,
            )
        )
    return specs


def classical_comparator_specs() -> list[ClassicalComparatorSpec]:
    callables = [
        ("GREEDY_MARKET_BUNDLE_SELECTION", "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:greedy_market_bundle_selection", "Greedy EV/capital baseline for QUBO bundle selection."),
        ("MIXED_INTEGER_PROGRAMMING_COMPARATOR", "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:greedy_market_bundle_selection", "MIP-style comparator placeholder using deterministic greedy local baseline until PR162R/PR163 solver wiring."),
        ("DETERMINISTIC_CANDIDATE_RANKING", "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:deterministic_candidate_ranking", "Stable ranking comparator for one-hot stack selection."),
        ("RISK_ADJUSTED_SCORE_RANKING", "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.formula_seed_library:compute_risk_adjusted_score", "Risk-adjusted score baseline comparator."),
        ("BRUTE_FORCE_BINARY_ENUMERATION", "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:top_k_candidate_filter", "Local deterministic enumeration candidate baseline."),
        ("MEAN_VARIANCE_GREEDY_COMPARATOR", "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:market_bundle_diversifier", "Mean-variance-style diversified greedy comparator."),
        ("DIVERSIFIED_GREEDY_COMPARATOR", "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:market_bundle_diversifier", "Family-diversified greedy comparator."),
        ("REPLAY_VALUE_RANKING_COMPARATOR", "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:deterministic_candidate_ranking", "Replay-value deterministic ranking comparator."),
        ("PAPER_VALUE_RANKING_COMPARATOR", "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:deterministic_candidate_ranking", "Paper-value deterministic ranking comparator."),
        ("PARAMETER_STACK_SELECTOR", "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:parameter_stack_selector", "Parameter-stack selector comparator."),
        ("ROUTE_FILL_PRIORITY_ORDER", "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:route_fill_priority_order", "Route-fill priority comparator."),
    ]
    specs: list[ClassicalComparatorSpec] = []
    for index in range(25):
        name, callable_ref, procedure = callables[index % len(callables)]
        specs.append(
            ClassicalComparatorSpec(
                comparator_id=f"CLASSICAL_COMPARATOR::{name}::VARIANT_{index + 1:02d}",
                comparator_family=name,
                callable_ref=callable_ref,
                procedure=procedure,
                compared_quantum_family=quantum_specs()[index % len(quantum_specs())].quantum_formulation_id,
                test_vector_ref=f"PR162D_R2A_TV_COMPARATOR::{name}::{index + 1:02d}",
            )
        )
    return specs


def quantum_by_id() -> dict[str, QuantumSpec]:
    return {spec.quantum_formulation_id: spec for spec in quantum_specs()}
