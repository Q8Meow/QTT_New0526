"""Quantum default parameter profiles."""

from __future__ import annotations

from . import constants as c


def build_default_profiles() -> list[dict[str, object]]:
    profiles = [
        (
            "QUBO",
            {
                "binary_variable_encoding": "BINARY_0_1",
                "objective_sign_convention": "MINIMIZATION_CANONICAL",
                "linear_term_scale_candidate_range": [0.01, 10.0],
                "quadratic_term_scale_candidate_range": [0.01, 10.0],
                "risk_penalty_weight_candidate_range": [0.1, 100.0],
                "transaction_cost_penalty_weight_candidate_range": [0.1, 50.0],
                "liquidity_penalty_weight_candidate_range": [0.1, 50.0],
                "latency_penalty_weight_candidate_range": [0.1, 25.0],
                "exposure_constraint_penalty_candidate_range": [1.0, 100.0],
                "budget_constraint_penalty_candidate_range": [1.0, 100.0],
                "one_hot_constraint_penalty_candidate_range": [1.0, 100.0],
                "max_position_constraint_penalty_candidate_range": [1.0, 100.0],
                "diversification_penalty_candidate_range": [0.1, 25.0],
                "arbitrage_path_penalty_candidate_range": [0.1, 100.0],
                "candidate_grid_size_class": "SMALL_MEDIUM_LARGE_REPLAY_GRID",
            },
        ),
        (
            "ISING",
            {
                "spin_domain": "{-1,+1}",
                "qubo_to_ising_mapping_candidate_flag": True,
                "h_bias_scale_candidate_range": [0.01, 10.0],
                "J_coupler_scale_candidate_range": [0.01, 10.0],
                "field_normalization_candidate": "MAX_ABS_OR_UNIT_VARIANCE_CANDIDATE",
                "coupling_normalization_candidate": "MAX_ABS_OR_UNIT_VARIANCE_CANDIDATE",
                "penalty_energy_scale_candidate_range": [1.0, 100.0],
                "spin_to_binary_decode_rule": "x=(z+1)/2",
            },
        ),
        (
            "QAOA",
            {
                "qaoa_depth_p_candidate_range": [1, 5],
                "qaoa_depth_profile_classes": ["SHALLOW_P1_P2", "MEDIUM_P3_P5", "DEEP_RESEARCH_ONLY"],
                "gamma_initialization_candidates": ["GRID_0_PI", "SMALL_RANDOM_SEEDED"],
                "beta_initialization_candidates": ["GRID_0_PI_OVER_2", "SMALL_RANDOM_SEEDED"],
                "parameter_initialization_strategy": "GRID_OR_HEURISTIC_CANDIDATE",
                "mixer_type_candidates": ["STANDARD_X_MIXER", "CONSTRAINT_PRESERVING_MIXER_CANDIDATE"],
                "cost_hamiltonian_source": "QUBO_OR_ISING_CANDIDATE",
                "shot_count_candidate_range": [256, 8192],
                "optimizer_iteration_budget_candidate_range": [25, 250],
                "convergence_tolerance_candidate_range": [0.001, 0.000001],
            },
        ),
        (
            "VQE",
            {
                "ansatz_class_candidates": ["HARDWARE_EFFICIENT_CANDIDATE", "PROBLEM_INSPIRED_CANDIDATE"],
                "ansatz_depth_candidate_range": [1, 4],
                "parameter_initialization_candidates": ["ZERO", "SMALL_RANDOM_SEEDED", "WARM_START_FROM_CLASSICAL"],
                "Hamiltonian_source_candidates": [
                    "RISK_OBJECTIVE",
                    "PORTFOLIO_OBJECTIVE",
                    "HYBRID_CALIBRATION_OBJECTIVE",
                ],
                "expectation_estimator_candidate": "SAMPLE_OR_STATEVECTOR_FUTURE_GATED",
                "shot_count_candidate_range": [256, 8192],
                "optimizer_iteration_budget_candidate_range": [25, 250],
                "convergence_tolerance_candidate_range": [0.001, 0.000001],
            },
        ),
        (
            "ANNEALING",
            {
                "annealing_family_candidates": ["SIMULATED_ANNEALING", "QUANTUM_ANNEALING_READY_LATER"],
                "initial_temperature_candidate_range": [1.0, 100.0],
                "final_temperature_candidate_range": [0.001, 1.0],
                "sweep_count_candidate_range": [100, 10000],
                "restart_count_candidate_range": [1, 100],
                "schedule_class_candidates": ["LINEAR", "GEOMETRIC", "ADAPTIVE_CANDIDATE"],
                "constraint_penalty_scale_candidate_range": [1.0, 100.0],
                "embedding_required_future_backend_flag": True,
            },
        ),
        (
            "HYBRID",
            {
                "arbitration_modes": [
                    "CLASSICAL_BASELINE",
                    "QUANTUM_CHALLENGER",
                    "HYBRID_COMPARE_THEN_SELECT",
                    "QUANTUM_FIRST",
                    "OWNER_FORCED_QUANTUM",
                    "OWNER_FORCED_CLASSICAL",
                ],
                "near_tie_threshold_candidate_range": [0.0, 0.05],
                "quantum_priority_boost_candidate_range": [0.0, 0.1],
                "latency_penalty_override_candidate": "APPLY_IF_QUANTUM_LATENCY_EXCEEDS_CLASSICAL_BUDGET",
                "replay_paper_comparison_required_flag": True,
                "owner_quantum_priority_consumed_flag": True,
            },
        ),
    ]
    return [
        {
            "profile_id": f"PR161A_DEFAULT_PROFILE__{family}",
            "optimizer_family": family,
            "applicable_quantum_profile_types": [
                profile_type for profile_type in c.QUANTUM_PROFILE_TYPES if _family_matches(family, profile_type)
            ],
            "default_basis": "QUANTUM_READY_QTT_CANDIDATE_DEFAULT",
            "default_value_candidates": values,
            "default_range_candidates": values,
            "initialization_candidates": values,
            "classical_baseline_link": "PR161A_CLASSICAL_BASELINE_GREEDY_LINEAR_COST",
            "replay_paper_test_grid": values,
            "downstream_agent_roles": list(c.DOWNSTREAM_AGENT_ROLES),
            "latency_feasibility_class": "REPLAY_PAPER_ONLY_LATENCY_FEASIBILITY_UNKNOWN",
            "expected_compute_profile_class": "CONTROL_PLANE_RESEARCH_PREP_ONLY",
            "promotion_limitations": c.NON_LIVE_PROMOTION_LIMITATION,
            "source_or_basis": "QTT_PR161A_OWNER_APPROVED_QUANTUM_CANDIDATE_DEFAULT",
            "owner_pr161a_approval_applied_flag": True,
            "replay_paper_grid_required_flag": True,
        }
        for family, values in profiles
    ]


def _family_matches(family: str, profile_type: str) -> bool:
    if family == "HYBRID":
        return profile_type.startswith("HYBRID_") or profile_type.startswith("OWNER_")
    return profile_type.startswith(family)

