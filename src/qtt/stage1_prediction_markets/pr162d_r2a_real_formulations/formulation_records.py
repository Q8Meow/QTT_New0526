"""Build executable formulation records from seed libraries."""

from __future__ import annotations

from typing import Any

from .algorithm_seed_library import algorithm_specs
from .formula_seed_library import formula_specs
from .quantum_seed_library import classical_comparator_specs, quantum_specs


PARAMETER_PACKS = (
    ("PARAMETER_PACK_RISK_PARAMETERS", "risk_parameters", {"max_fraction_cap": 0.10, "drawdown_penalty_lambda": 0.50}, {"max_fraction_cap": [0.0, 0.25], "drawdown_penalty_lambda": [0.0, 2.0]}),
    ("PARAMETER_PACK_CAPITAL_PARAMETERS", "capital_parameters", {"capital_budget_fraction": 0.25, "max_exposure_fraction": 0.40}, {"capital_budget_fraction": [0.0, 1.0], "max_exposure_fraction": [0.0, 1.0]}),
    ("PARAMETER_PACK_LIQUIDITY_PARAMETERS", "liquidity_parameters", {"min_liquidity_score": 5.0, "max_relative_spread": 0.12}, {"min_liquidity_score": [0.0, 1000.0], "max_relative_spread": [0.0, 1.0]}),
    ("PARAMETER_PACK_LATENCY_PARAMETERS", "latency_parameters", {"expected_latency_seconds": 2.0, "notional_sensitivity": 100.0}, {"expected_latency_seconds": [0.0, 60.0], "notional_sensitivity": [0.0, 10000.0]}),
    ("PARAMETER_PACK_QUANTUM_PARAMETERS", "quantum_parameters", {"lambda_budget": 0.10, "lambda_exposure": 0.10, "lambda_onehot": 2.0}, {"lambda_budget": [0.0, 100.0], "lambda_exposure": [0.0, 100.0], "lambda_onehot": [0.0, 100.0]}),
    ("PARAMETER_PACK_OPTIMIZER_PARAMETERS", "optimizer_parameters", {"top_k": 25, "batch_size": 100}, {"top_k": [1, 1000], "batch_size": [1, 10000]}),
    ("PARAMETER_PACK_CALIBRATION_PARAMETERS", "calibration_parameters", {"probability_clip_epsilon": 1.0e-9, "calibration_window": 100}, {"probability_clip_epsilon": [1.0e-12, 1.0e-3], "calibration_window": [10, 10000]}),
    ("PARAMETER_PACK_FEATURE_PARAMETERS", "feature_parameters", {"rsi_window": 14, "macd_fast": 12, "macd_slow": 26}, {"rsi_window": [2, 100], "macd_fast": [2, 100], "macd_slow": [3, 200]}),
    ("PARAMETER_PACK_REPLAY_PARAMETERS", "replay_parameters", {"replay_batch_size": 500, "replay_value_weight": 1.0}, {"replay_batch_size": [1, 10000], "replay_value_weight": [0.0, 10.0]}),
    ("PARAMETER_PACK_PAPER_PARAMETERS", "paper_parameters", {"paper_value_weight": 1.0, "paper_duration_days": 7}, {"paper_value_weight": [0.0, 10.0], "paper_duration_days": [1, 365]}),
    ("PARAMETER_PACK_SOURCE_PARAMETERS", "source_parameters", {"source_confidence_floor": 0.25}, {"source_confidence_floor": [0.0, 1.0]}),
    ("PARAMETER_PACK_ROUTE_PARAMETERS", "route_parameters", {"route_fill_need_threshold": 0.50}, {"route_fill_need_threshold": [0.0, 1.0]}),
    ("PARAMETER_PACK_HOTPATH_PARAMETERS", "hotpath_parameters", {"cache_ttl_seconds": 60}, {"cache_ttl_seconds": [0, 86400]}),
    ("PARAMETER_PACK_QAOA_PARAMETERS", "qaoa_parameters", {"qaoa_depth_p": 1}, {"qaoa_depth_p": [1, 10]}),
    ("PARAMETER_PACK_ANNEALING_PARAMETERS", "annealing_parameters", {"anneal_time_candidate_microseconds": 20}, {"anneal_time_candidate_microseconds": [1, 10000]}),
    ("PARAMETER_PACK_CQM_PARAMETERS", "cqm_parameters", {"constraint_penalty_scale": 1.0}, {"constraint_penalty_scale": [0.0, 1000.0]}),
)


def build_formulation_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for spec in formula_specs():
        formulation_type = "FEATURE" if spec.domain_family_key in {"technical_indicator_price_feature", "market_microstructure_liquidity", "latency_slippage_cost"} else "FORMULA"
        records.append(
            {
                "formulation_id": f"FORMULA::{spec.formula_id}",
                "formulation_type": formulation_type,
                "domain_family_key": spec.domain_family_key,
                "subfamily_key": spec.subfamily_key,
                "variant_key": spec.variant_key,
                "source_universe": "OWNER_TEMPLATE_FORMULA_SEED_LIBRARY",
                "source_record_ids": [spec.formula_id],
                "expression": spec.expression,
                "algorithm_procedure": None,
                "objective": None,
                "callable_ref": spec.callable_ref,
                "inputs": list(spec.required_inputs),
                "variables": [],
                "outputs": list(spec.outputs),
                "objective_output_meaning": None,
                "units_or_type_hints": spec.units_or_type_hints,
                "unit_unknown_but_type_known_flag": False,
                "test_vector_refs": [spec.test_vector()["test_vector_id"]],
                "source_truth_status": spec.source_truth_status,
                "candidate_truth_status": spec.candidate_truth_status,
                "live_order_authority": False,
                "replay_paper_candidate_flag": spec.replay_paper_candidate_flag,
                "qku_route_state": "FORMULATION_FIRST_QKU_MAPPING_READY",
                "replay_paper_route_state": "REPLAY_PAPER_ROUTE_READY",
                "exact_fill_action_refs": [],
                "validator_materiality_status": "FORMULATION_FULLY_MATERIALIZED",
                "computability_reason": "Executable Python formula callable with deterministic synthetic test vector.",
                "compute_tier": spec.compute_tier,
                "latency_class": spec.latency_class,
                "source_locator_refs": ["OWNER_TEMPLATE_PR162D_R2A"],
                "official_truth_flag": False,
            }
        )
    for spec in algorithm_specs():
        records.append(
            {
                "formulation_id": f"ALGORITHM::{spec.algorithm_id}",
                "formulation_type": "ALGORITHM",
                "domain_family_key": spec.domain_family_key,
                "subfamily_key": spec.subfamily_key,
                "variant_key": spec.variant_key,
                "source_universe": "OWNER_TEMPLATE_ALGORITHM_SEED_LIBRARY",
                "source_record_ids": [spec.algorithm_id],
                "expression": None,
                "algorithm_procedure": spec.procedure,
                "objective": None,
                "callable_ref": spec.callable_ref,
                "inputs": list(spec.required_inputs),
                "variables": [],
                "outputs": list(spec.outputs),
                "objective_output_meaning": None,
                "units_or_type_hints": {output: "structured_output" for output in spec.outputs},
                "unit_unknown_but_type_known_flag": True,
                "test_vector_refs": [spec.test_vector()["test_vector_id"]],
                "source_truth_status": "OWNER_TEMPLATE",
                "candidate_truth_status": "CANDIDATE",
                "live_order_authority": False,
                "replay_paper_candidate_flag": True,
                "qku_route_state": "FORMULATION_FIRST_QKU_MAPPING_READY",
                "replay_paper_route_state": "REPLAY_PAPER_ROUTE_READY",
                "exact_fill_action_refs": [],
                "validator_materiality_status": "FORMULATION_FULLY_MATERIALIZED",
                "computability_reason": "Executable deterministic algorithm callable with synthetic test case.",
                "failure_modes": list(spec.failure_modes),
                "compute_tier": spec.compute_tier,
                "latency_class": spec.latency_class,
                "source_locator_refs": ["OWNER_TEMPLATE_PR162D_R2A"],
                "official_truth_flag": False,
            }
        )
    for pack_id, subfamily, defaults, ranges in PARAMETER_PACKS:
        records.append(
            {
                "formulation_id": f"PARAMETER_PACK::{pack_id}",
                "formulation_type": "PARAMETER_PACK",
                "domain_family_key": "parameter_default_range_pack",
                "subfamily_key": subfamily,
                "variant_key": "owner_template_v1",
                "source_universe": "OWNER_TEMPLATE_PARAMETER_PACK_LIBRARY",
                "source_record_ids": [pack_id],
                "expression": None,
                "algorithm_procedure": "Return concrete candidate defaults and ranges for replay/paper computation.",
                "objective": None,
                "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:build_parameter_pack_from_defaults",
                "inputs": ["defaults", "ranges", "version"],
                "variables": [],
                "outputs": ["parameter_pack"],
                "objective_output_meaning": None,
                "units_or_type_hints": {"parameter_pack": "dict_with_defaults_and_ranges"},
                "unit_unknown_but_type_known_flag": False,
                "candidate_default_ranges": {"defaults": defaults, "ranges": ranges},
                "test_vector_refs": [f"PR162D_R2A_TV_PARAMETER_PACK::{pack_id}"],
                "source_truth_status": "OWNER_TEMPLATE",
                "candidate_truth_status": "CANDIDATE",
                "live_order_authority": False,
                "replay_paper_candidate_flag": True,
                "qku_route_state": "FORMULATION_FIRST_QKU_MAPPING_READY",
                "replay_paper_route_state": "REPLAY_PAPER_ROUTE_READY",
                "exact_fill_action_refs": [],
                "validator_materiality_status": "FORMULATION_FULLY_MATERIALIZED",
                "computability_reason": "Concrete parameter defaults and ranges can be returned by deterministic callable.",
                "compute_tier": "TIER_0_CONSTANT_OR_CACHED_PARAMETER",
                "latency_class": "CACHE_READ_ELIGIBLE",
                "source_locator_refs": ["OWNER_TEMPLATE_PR162D_R2A"],
                "official_truth_flag": False,
            }
        )
    for spec in quantum_specs():
        records.append(
            {
                "formulation_id": f"QUANTUM::{spec.quantum_formulation_id}",
                "formulation_type": "QUANTUM_FORMULATION",
                "domain_family_key": spec.domain_family_key,
                "subfamily_key": spec.subfamily_key,
                "variant_key": spec.variant_key,
                "source_universe": "OWNER_TEMPLATE_QUANTUM_SEED_LIBRARY",
                "source_record_ids": [spec.quantum_formulation_id],
                "expression": None,
                "algorithm_procedure": None,
                "objective": spec.objective,
                "callable_ref": spec.callable_ref,
                "inputs": [],
                "variables": list(spec.variables),
                "outputs": [],
                "objective_output_meaning": "Deterministic local optimizer-shape payload for replay/paper research candidate construction.",
                "units_or_type_hints": {"shape": "dict", "variables": "binary_or_spin_or_nonnegative_real"},
                "unit_unknown_but_type_known_flag": False,
                "test_vector_refs": [spec.test_vector()["test_vector_id"]],
                "source_truth_status": "OWNER_TEMPLATE",
                "candidate_truth_status": "CANDIDATE",
                "live_order_authority": False,
                "replay_paper_candidate_flag": True,
                "qku_route_state": "FORMULATION_FIRST_QKU_MAPPING_READY",
                "replay_paper_route_state": "REPLAY_PAPER_ROUTE_READY",
                "exact_fill_action_refs": [],
                "validator_materiality_status": "FORMULATION_FULLY_MATERIALIZED",
                "computability_reason": "Local deterministic build_shape callable returns objective, variables, domains, penalties or constraints, and comparator refs without backend execution.",
                "constraints": list(spec.constraints),
                "domains": dict(spec.domains),
                "penalties": list(spec.penalties),
                "mapping_rationale": spec.mapping_rationale,
                "classical_comparator_ref": spec.classical_comparator_ref,
                "compute_tier": spec.compute_tier,
                "latency_class": spec.latency_class,
                "source_locator_refs": ["PR162D_R2A_SOURCE_DWAVE_MODELS", "PR162D_R2A_SOURCE_QISKIT_QAOA"],
                "official_truth_flag": False,
                "quantum_backend_execution_flag": False,
                "quantum_advantage_claim_flag": False,
            }
        )
    return records


def build_test_vectors() -> list[dict[str, Any]]:
    vectors = [spec.test_vector() for spec in formula_specs()]
    vectors.extend(spec.test_vector() for spec in algorithm_specs())
    for pack_id, _subfamily, defaults, ranges in PARAMETER_PACKS:
        vectors.append(
            {
                "test_vector_id": f"PR162D_R2A_TV_PARAMETER_PACK::{pack_id}",
                "callable_ref": "src.qtt.stage1_prediction_markets.pr162d_r2a_real_formulations.algorithm_seed_library:build_parameter_pack_from_defaults",
                "inputs": {"defaults": defaults, "ranges": ranges, "version": "v1"},
                "expected_outputs": {"parameter_pack": {"defaults": defaults, "ranges": ranges, "version": "v1"}},
                "tolerance": 0.0,
                "source_truth_status": "OWNER_TEMPLATE",
                "candidate_truth_status": "CANDIDATE",
                "live_order_authority": False,
            }
        )
    vectors.extend(spec.test_vector() for spec in quantum_specs())
    for spec in classical_comparator_specs():
        vectors.append(
            {
                "test_vector_id": spec.test_vector_ref,
                "callable_ref": spec.callable_ref,
                "inputs": {"comparator_id": spec.comparator_id},
                "expected_outputs": {"callable_importable_flag": True},
                "tolerance": 0.0,
                "source_truth_status": "OWNER_TEMPLATE",
                "candidate_truth_status": "CANDIDATE",
                "live_order_authority": False,
            }
        )
    return vectors


def formulation_by_id(records: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    rows = records if records is not None else build_formulation_records()
    return {row["formulation_id"]: row for row in rows}
