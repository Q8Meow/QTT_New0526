#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import pathlib
import subprocess
import sys
import tempfile
import inspect
import json
import os
import time
from typing import Sequence

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SUCCESS_MARKER = "QTT_VALIDATION_GATES_OK"
PYTEST_FRESH_BASETEMP_SCRIPT = "run_pytest_fresh_basetemp.py"
PHASE_SUCCESS_MARKER_PREFIX = "QTT_VALIDATION_PHASE_OK"
TIMING_SCHEMA_VERSION = 1
SLOWEST_ENTRY_LIMIT = 20
PYTEST_BASETEMP_PARENT = "qtt_run_validation_gates_pytest"
PYTEST_DURATIONS_ARG = "--durations=50"
PYTEST_SHARD_TARGET_SECONDS = 20 * 60
PYTEST_SHARD_WARNING_SECONDS = 25 * 60
PYTEST_SHARD_HARD_REVIEW_SECONDS = 30 * 60
PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS = 8 * 60
PYTEST_SUBPROCESS_GROUP_WARNING_SECONDS = 10 * 60
PYTEST_FILE_WARNING_SECONDS = 120
PYTEST_FILE_HARD_REVIEW_SECONDS = 300
PYTEST_IDEMPOTENCE_WARNING_SECONDS = 120
PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS = 180
NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV = "QTT_NO_RUNTIME_ARTIFACT_SCAN_CACHE"
NO_RUNTIME_ARTIFACT_SCAN_CACHE_KIND = "qtt_no_runtime_artifact_scan"
NO_RUNTIME_ARTIFACT_SCAN_CACHE_SCHEMA_VERSION = 1
PR152_BUILD_REPORT_CACHE_ENV = "QTT_PR152_BUILD_REPORT_CACHE"
PR152_BUILD_REPORT_CACHE_KIND = "qtt_pr152_build_report"
PR152_BUILD_REPORT_CACHE_SCHEMA_VERSION = 1
FAST_PREFLIGHT_PHASE = "fast-preflight"
DETERMINISTIC_VALIDATORS_PHASE = "deterministic-validators"
PYTEST_SHARD_PHASES = (
    "pytest-shard-1",
    "pytest-shard-2",
    "pytest-shard-3",
    "pytest-shard-4",
    "pytest-shard-5",
    "pytest-shard-6",
    "pytest-shard-7",
    "pytest-shard-8",
)
POST_VALIDATION_PHASE = "post-validation"
ALL_PHASE = "all"
ORDERED_PHASES = (
    FAST_PREFLIGHT_PHASE,
    DETERMINISTIC_VALIDATORS_PHASE,
    *PYTEST_SHARD_PHASES,
    POST_VALIDATION_PHASE,
)
VALIDATION_PHASES = (*ORDERED_PHASES, ALL_PHASE)
PYTEST_SHARD_RUNTIME_BUDGETS = {
    phase: {
        "target_seconds": PYTEST_SHARD_TARGET_SECONDS,
        "warning_seconds": PYTEST_SHARD_WARNING_SECONDS,
        "hard_review_seconds": PYTEST_SHARD_HARD_REVIEW_SECONDS,
    }
    for phase in PYTEST_SHARD_PHASES
}
RUNTIME_BUDGET_POLICY = {
    "pytest_shard_target_seconds": PYTEST_SHARD_TARGET_SECONDS,
    "pytest_shard_warning_seconds": PYTEST_SHARD_WARNING_SECONDS,
    "pytest_shard_hard_review_seconds": PYTEST_SHARD_HARD_REVIEW_SECONDS,
    "pytest_subprocess_group_target_seconds": PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
    "pytest_subprocess_group_warning_seconds": PYTEST_SUBPROCESS_GROUP_WARNING_SECONDS,
    "pytest_file_warning_seconds": PYTEST_FILE_WARNING_SECONDS,
    "pytest_file_hard_review_seconds": PYTEST_FILE_HARD_REVIEW_SECONDS,
    "pytest_idempotence_warning_seconds": PYTEST_IDEMPOTENCE_WARNING_SECONDS,
    "pytest_idempotence_hard_review_seconds": PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS,
}
FAST_PREFLIGHT_SCRIPT_NAMES = frozenset(
    {
        "validate_grand_global_debug_logical_consistency_audit.py",
        "validate_ci_branch_context_matrix.py",
        "validate_repair_pr_changed_file_scope.py",
        "validate_nested_validator_contracts.py",
        "validate_validation_inventory.py",
        "validate_validation_scope_registry.py",
        "changed_area_validation_router.py",
        "cross_platform_path_invariant.py",
    }
)
ISOLATED_SOURCE_EVIDENCE_PYTEST = (
    "tests/source_evidence/"
    "test_controlled_official_source_capture_candidate_packets.py"
)
_PR152_BUILD_REPORT_MEMORY_CACHE: dict[tuple[str, str], dict[str, object]] = {}


@dataclass(frozen=True)
class PytestShardCommand:
    paths: tuple[str, ...]
    ignores: tuple[str, ...] = ()
    reason: str = ""
    runtime_budget_seconds: int | None = None
    historical_runtime_seconds: float | None = None
    known_historical_heavy: bool = False
    bounded_idempotence: bool = False


@dataclass(frozen=True)
class TimingEntry:
    phase: str
    command_index: int
    command: list[str]
    elapsed_seconds: float
    returncode: int


PR166_SM2_TEST_ROOT = (
    "tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2"
)
PR166_SF_R2_TEST_ROOT = (
    "tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest"
)
PR166_SM3_TEST_ROOT = (
    "tests/stage1_prediction_markets/pr166_sm3_score_memory_refresh_v3"
)
PR166_Q_TEST_ROOT = (
    "tests/stage1_prediction_markets/pr166_q_quantum_classical_hybrid_comparator"
)
PR166_QB_TEST_ROOT = (
    "tests/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark"
)
PR166_QC_TEST_ROOT = (
    "tests/stage1_prediction_markets/"
    "pr166_qc_quantum_selected_replay_paper_retest"
)
PR162E_Q_TEST_ROOT = (
    "tests/stage1_prediction_markets/pr162e_q_quantum_automapper"
)
PR162E_TEST_ROOT = "tests/pr162e"
PR167_TEST_ROOT = (
    "tests/stage1_prediction_markets/pr167_open_trade_simulator_integration"
)
PR166_SM2_PYTEST_FILE_GROUPS = (
    (
        "test_pr166_sm2_ablation.py",
        "test_pr166_sm2_agent_duty.py",
        "test_pr166_sm2_agent_kpi.py",
        "test_pr166_sm2_agent_task_queue.py",
        "test_pr166_sm2_all_neg_conversion.py",
        "test_pr166_sm2_alt_exec_memory.py",
        "test_pr166_sm2_authority_boundaries.py",
        "test_pr166_sm2_break_even_gap.py",
        "test_pr166_sm2_build_outputs.py",
        "test_pr166_sm2_calib_boost.py",
        "test_pr166_sm2_calibration.py",
        "test_pr166_sm2_candidate_family.py",
        "test_pr166_sm2_capacity_crowding.py",
    ),
    (
        "test_pr166_sm2_champion_challenger.py",
        "test_pr166_sm2_compact_names.py",
        "test_pr166_sm2_condition_winners_losers.py",
        "test_pr166_sm2_connector_ref_routing.py",
        "test_pr166_sm2_conversion_agent_queue.py",
        "test_pr166_sm2_conversion_math.py",
        "test_pr166_sm2_convertible_queue.py",
        "test_pr166_sm2_cost_cut.py",
        "test_pr166_sm2_counterfactual.py",
        "test_pr166_sm2_diversity.py",
        "test_pr166_sm2_edge_decay.py",
        "test_pr166_sm2_edge_uplift.py",
    ),
    (
        "test_pr166_sm2_evidence_depth.py",
        "test_pr166_sm2_expansion_policy.py",
        "test_pr166_sm2_external_dedupe.py",
        "test_pr166_sm2_external_signal_registry.py",
        "test_pr166_sm2_fill_boost.py",
        "test_pr166_sm2_fragile_watchlist.py",
        "test_pr166_sm2_handoff_intake.py",
        "test_pr166_sm2_idempotence.py",
        "test_pr166_sm2_input_consumption.py",
        "test_pr166_sm2_lat_liq_impact.py",
        "test_pr166_sm2_latent_edge.py",
        "test_pr166_sm2_lcb_confidence.py",
    ),
    (
        "test_pr166_sm2_marginal_utility.py",
        "test_pr166_sm2_memory_dag.py",
        "test_pr166_sm2_memory_ledger.py",
        "test_pr166_sm2_microstructure.py",
        "test_pr166_sm2_no_bad_status_tokens.py",
        "test_pr166_sm2_no_fill_memory.py",
        "test_pr166_sm2_no_orphans.py",
        "test_pr166_sm2_no_profit_evidence.py",
        "test_pr166_sm2_orthogonal_edge.py",
        "test_pr166_sm2_overfit_fdr.py",
        "test_pr166_sm2_param_uplift.py",
        "test_pr166_sm2_pos_seed_driver.py",
    ),
    (
        "test_pr166_sm2_positive_expansion.py",
        "test_pr166_sm2_positive_negative_edge.py",
        "test_pr166_sm2_pr152_pr208_routing_contract.py",
        "test_pr166_sm2_pref_avoid_memory.py",
        "test_pr166_sm2_provenance_supersession_drift.py",
        "test_pr166_sm2_quantum_priority.py",
        "test_pr166_sm2_rank_aggregation.py",
        "test_pr166_sm2_rank_delta.py",
        "test_pr166_sm2_rank_stability.py",
        "test_pr166_sm2_regime_memory.py",
        "test_pr166_sm2_repair_priority.py",
        "test_pr166_sm2_result_intake.py",
    ),
    (
        "test_pr166_sm2_retest_boost_queue.py",
        "test_pr166_sm2_route_crosswalk_cmd.py",
        "test_pr166_sm2_row_count_reconciliation.py",
        "test_pr166_sm2_score_explain.py",
        "test_pr166_sm2_score_registry.py",
        "test_pr166_sm2_selection_pressure.py",
        "test_pr166_sm2_selection_ready_queue.py",
        "test_pr166_sm2_settlement_adverse.py",
        "test_pr166_sm2_shard_input_audit.py",
        "test_pr166_sm2_shrinkage.py",
        "test_pr166_sm2_status_enum_drift.py",
        "test_pr166_sm2_tca_cost_roots.py",
        "test_pr166_sm2_tt_risk.py",
        "test_pr166_sm2_validator.py",
    ),
)
PR166_SF_R2_IDEMPOTENCE_TEST_FILE = "test_pr166_sf_r2_idempotence.py"
PR166_SM3_IDEMPOTENCE_TEST_FILE = "test_pr166_sm3_idempotence.py"
PR166_Q_IDEMPOTENCE_TEST_FILE = "test_pr166_q_idempotence.py"
PR166_QB_IDEMPOTENCE_TEST_FILE = "test_pr166_qb_idempotence.py"
PR166_QC_IDEMPOTENCE_TEST_FILE = "test_pr166_qc_idempotence.py"
PR162E_Q_IDEMPOTENCE_TEST_FILE = "test_pr162e_q_idempotence.py"
PR162E_IDEMPOTENCE_TEST_FILE = "test_pr162e_idempotence_bounded.py"
PR167_IDEMPOTENCE_TEST_FILE = "test_pr167_idempotence.py"
BOUNDED_DEFAULT_IDEMPOTENCE_TEST_PATHS = frozenset(
    {
        f"{PR166_SF_R2_TEST_ROOT}/{PR166_SF_R2_IDEMPOTENCE_TEST_FILE}",
        f"{PR166_SM3_TEST_ROOT}/{PR166_SM3_IDEMPOTENCE_TEST_FILE}",
        f"{PR166_Q_TEST_ROOT}/{PR166_Q_IDEMPOTENCE_TEST_FILE}",
        f"{PR166_QB_TEST_ROOT}/{PR166_QB_IDEMPOTENCE_TEST_FILE}",
        f"{PR166_QC_TEST_ROOT}/{PR166_QC_IDEMPOTENCE_TEST_FILE}",
        f"{PR162E_Q_TEST_ROOT}/{PR162E_Q_IDEMPOTENCE_TEST_FILE}",
        f"{PR162E_TEST_ROOT}/{PR162E_IDEMPOTENCE_TEST_FILE}",
        f"{PR167_TEST_ROOT}/{PR167_IDEMPOTENCE_TEST_FILE}",
    }
)
PR166_SF_R2_PYTEST_FILE_GROUPS = (
    (
        "test_pr166_sf_r2_agent_duty.py",
        "test_pr166_sf_r2_agent_kpi.py",
        "test_pr166_sf_r2_agent_task_queue.py",
        "test_pr166_sf_r2_all_negative_intake.py",
        "test_pr166_sf_r2_alt_exec_repair.py",
        "test_pr166_sf_r2_authority_boundaries.py",
        "test_pr166_sf_r2_before_after.py",
        "test_pr166_sf_r2_break_even_gap.py",
        "test_pr166_sf_r2_build_outputs.py",
        "test_pr166_sf_r2_calib_uplift_proof.py",
        "test_pr166_sf_r2_calibration.py",
        "test_pr166_sf_r2_calibration_repair.py",
        "test_pr166_sf_r2_capacity_crowding.py",
    ),
    (
        "test_pr166_sf_r2_champion_challenger.py",
        "test_pr166_sf_r2_compact_names.py",
        "test_pr166_sf_r2_computable_payload.py",
        "test_pr166_sf_r2_connectivity.py",
        "test_pr166_sf_r2_connector_routing.py",
        "test_pr166_sf_r2_conversion_attribution.py",
        "test_pr166_sf_r2_conversion_frontier.py",
        "test_pr166_sf_r2_conversion_proof.py",
        "test_pr166_sf_r2_cost_floor.py",
        "test_pr166_sf_r2_cost_repair.py",
        "test_pr166_sf_r2_downstream_handoffs.py",
        "test_pr166_sf_r2_episode_plan.py",
    ),
    (
        "test_pr166_sf_r2_external_signals.py",
        "test_pr166_sf_r2_fill_probability_model.py",
        "test_pr166_sf_r2_fill_repair.py",
        "test_pr166_sf_r2_fills_no_fills.py",
        "test_pr166_sf_r2_formula_qku_repair.py",
        "test_pr166_sf_r2_handoff_intake.py",
        "test_pr166_sf_r2_holdout_replay.py",
    ),
    (
        PR166_SF_R2_IDEMPOTENCE_TEST_FILE,
    ),
    (
        "test_pr166_sf_r2_impl_shortfall.py",
        "test_pr166_sf_r2_input_consumption.py",
        "test_pr166_sf_r2_launch_candidate_filter.py",
        "test_pr166_sf_r2_lcb_confidence.py",
    ),
    (
        "test_pr166_sf_r2_marginal_utility.py",
        "test_pr166_sf_r2_microstructure.py",
        "test_pr166_sf_r2_net_edge.py",
        "test_pr166_sf_r2_no_bad_status_tokens.py",
        "test_pr166_sf_r2_no_orphans.py",
        "test_pr166_sf_r2_no_profit_evidence.py",
        "test_pr166_sf_r2_order_intents.py",
        "test_pr166_sf_r2_overfit_fdr.py",
        "test_pr166_sf_r2_parameter_bound_audit.py",
        "test_pr166_sf_r2_parameter_repair.py",
        "test_pr166_sf_r2_positive_capacity.py",
        "test_pr166_sf_r2_positive_conversion.py",
    ),
    (
        "test_pr166_sf_r2_pr152_pr208_routing_contract.py",
        "test_pr166_sf_r2_quantum_handoff.py",
        "test_pr166_sf_r2_quantum_objective_map.py",
        "test_pr166_sf_r2_quantum_repair.py",
        "test_pr166_sf_r2_rank_stability.py",
        "test_pr166_sf_r2_regime_memory.py",
        "test_pr166_sf_r2_repair_ablation.py",
        "test_pr166_sf_r2_repair_failure.py",
        "test_pr166_sf_r2_repair_feasibility.py",
        "test_pr166_sf_r2_repair_frontier.py",
        "test_pr166_sf_r2_repair_portfolio.py",
        "test_pr166_sf_r2_repair_priority.py",
    ),
    (
        "test_pr166_sf_r2_repair_sensitivity.py",
        "test_pr166_sf_r2_repair_universe.py",
        "test_pr166_sf_r2_repaired_packet_registry.py",
        "test_pr166_sf_r2_retest_policy.py",
        "test_pr166_sf_r2_retest_universe.py",
        "test_pr166_sf_r2_route_crosswalk_cmd.py",
        "test_pr166_sf_r2_row_count_reconciliation.py",
        "test_pr166_sf_r2_runtime_safety_handoff.py",
        "test_pr166_sf_r2_shard_input_audit.py",
        "test_pr166_sf_r2_status_enum_drift.py",
        "test_pr166_sf_r2_still_negative.py",
        "test_pr166_sf_r2_tca_cost_roots.py",
        "test_pr166_sf_r2_terminal_rows.py",
        "test_pr166_sf_r2_validator.py",
    ),
)


def _pr166_sm2_pytest_paths(file_names: Sequence[str]) -> tuple[str, ...]:
    return tuple(f"{PR166_SM2_TEST_ROOT}/{file_name}" for file_name in file_names)


def _pr166_sf_r2_pytest_paths(file_names: Sequence[str]) -> tuple[str, ...]:
    return tuple(f"{PR166_SF_R2_TEST_ROOT}/{file_name}" for file_name in file_names)


PYTEST_SHARD_COMMANDS: dict[str, tuple[PytestShardCommand, ...]] = {
    "pytest-shard-1": (
        PytestShardCommand(
            paths=("tests/tools", "tests/fail_closed"),
            reason="CI tooling and fail-closed runner policy tests",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=29.0,
        ),
    ),
    "pytest-shard-2": (
        PytestShardCommand(
            paths=(
                "tests/stage1_prediction_markets/agent_consumable_parameter_default_registry",
                "tests/stage1_prediction_markets/agent_default_binding_universal_intake_gate",
                "tests/stage1_prediction_markets/aggressive_qku_candidate_materialization_agent_routing",
                "tests/stage1_prediction_markets/atomicrows_bundle_reconciliation",
                "tests/stage1_prediction_markets/atomicrows_pr154_value_state",
                "tests/stage1_prediction_markets/latency_hot_path_snapshot_boundary",
            ),
            reason="Stage 1 prediction-market foundational lightweight tests",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=16.0,
        ),
        PytestShardCommand(
            paths=(
                "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure",
                "tests/stage1_prediction_markets/pr162d_r1_external_formula_data_quantum_acquisition_expansion",
                "tests/stage1_prediction_markets/pr162d_r2a_real_formulations",
                "tests/stage1_prediction_markets/pr162r_a_replay_paper_executability_classification_audit",
                "tests/stage1_prediction_markets/pr162r_b_replay_paper_data_binding_completion",
                "tests/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun",
                "tests/stage1_prediction_markets/pr163_b_paired_replay_paper_concurrent_executor",
                "tests/stage1_prediction_markets/pr163_c_pretrade_infrastructure_rejection_remediation",
            ),
            reason="Stage 1 PR160/PR162/PR163 medium replay-paper infrastructure tests",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=24.0,
        ),
        PytestShardCommand(
            paths=(
                "tests/atomicrows",
            ),
            reason="AtomicRows tests moved out of residual shards for stable runtime budget",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=70.0,
        ),
        PytestShardCommand(
            paths=("tests/pr168_gfp",),
            reason="PR168-GFP executable formula and truth-overlay focused tests",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=2.0,
        ),
        PytestShardCommand(
            paths=("tests/pr168_rp",),
            reason="PR168-RP replay/paper recompute and pretrade focused tests",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=65.0,
        ),
    ),
    "pytest-shard-3": (
        PytestShardCommand(
            paths=(
                "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage",
                "tests/stage1_prediction_markets/multisource_safe_nonlive_dataset_expansion_strict_qku_coverage",
                "tests/stage1_prediction_markets/nonlive_replay_paper_data_adapter_quantum_forward_bridge",
                "tests/stage1_prediction_markets/pr157_completion_materialization_bridge",
                "tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge",
                "tests/stage1_prediction_markets/pr159_official_source_completion_bridge",
                "tests/stage1_prediction_markets/pr159r_source_locator_value_capture",
            ),
            reason=(
                "Stage 1 prediction-market legacy source-resolution block "
                "isolated from PR166 heavy groups"
            ),
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=160.0,
            known_historical_heavy=True,
        ),
        PytestShardCommand(
            paths=(
                "tests/stage1_prediction_markets/pr163_generic_paper_adapter_capture_framework",
                "tests/stage1_prediction_markets/pr164_review_provenance_qku_canonical_coverage_audit",
                "tests/stage1_prediction_markets/pr165_b_condition_scoped_negative_memory",
                "tests/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration",
                "tests/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection",
                "tests/stage1_prediction_markets/pr165_d2_score_refreshed_scenario_selection_v2",
                "tests/stage1_prediction_markets/pr165_evidence_backed_scoring_ranking",
                "tests/stage1_prediction_markets/pr166_s_replay_paper_scenario_retest_execution",
                "tests/stage1_prediction_markets/pr166_s2_replay_paper_retest_loop_v2",
            ),
            reason=(
                "Stage 1 PR164/PR165/PR166-S replay retest block isolated from "
                "PR166-SM2 and PR166-SF-R2 idempotence-heavy groups"
            ),
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=258.0,
            known_historical_heavy=True,
        ),
        PytestShardCommand(
            paths=(
                "tests/stage1_prediction_markets/qku_candidate_quality_replay_paper_prioritization",
                "tests/stage1_prediction_markets/qku_formula_algorithm_solver_market_scope_materialization",
                "tests/stage1_prediction_markets/qku_residual_candidate_assimilation",
                "tests/stage1_prediction_markets/replay_paper_executor_input_run_artifact_generation",
                "tests/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning",
                "tests/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate",
                "tests/stage1_prediction_markets/source_intelligence",
                "tests/stage1_prediction_markets/test_validate_stage1_packet_schema_gate_static.py",
            ),
            reason=(
                "Stage 1 residual QKU/source-intelligence group split out of "
                "the former shard-2 aggregation"
            ),
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=53.0,
        ),
    ),
    "pytest-shard-4": (
        PytestShardCommand(
            paths=(
                "tests/stage1_prediction_markets/pr166_sf_repair_materialization_before_retest",
                "tests/stage1_prediction_markets/pr166_sm_score_memory_refresh_from_pr166_s_results",
            ),
            reason=(
                "PR166-SF and PR166-SM heavy historical tests isolated under "
                "the canonical runtime budget"
            ),
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=137.0,
            known_historical_heavy=True,
        ),
        PytestShardCommand(
            paths=_pr166_sf_r2_pytest_paths(PR166_SF_R2_PYTEST_FILE_GROUPS[3]),
            reason=(
                "Bounded PR166-SF-R2 idempotence proof kept as its own early "
                "subgroup so timeout-inconclusive failures classify cleanly"
            ),
            runtime_budget_seconds=PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS,
            historical_runtime_seconds=115.0,
            known_historical_heavy=True,
            bounded_idempotence=True,
        ),
    ),
    "pytest-shard-5": (
        PytestShardCommand(
            paths=_pr166_sm2_pytest_paths(PR166_SM2_PYTEST_FILE_GROUPS[0]),
            reason="PR166-SM2 split subgroup 1 preserving full test coverage",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=17.0,
        ),
        PytestShardCommand(
            paths=_pr166_sm2_pytest_paths(PR166_SM2_PYTEST_FILE_GROUPS[1]),
            reason="PR166-SM2 split subgroup 2 preserving full test coverage",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=4.0,
        ),
        PytestShardCommand(
            paths=_pr166_sm2_pytest_paths(PR166_SM2_PYTEST_FILE_GROUPS[2]),
            reason=(
                "PR166-SM2 idempotence-heavy subgroup isolated from other "
                "historical heavy families"
            ),
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=124.0,
            known_historical_heavy=True,
        ),
        PytestShardCommand(
            paths=_pr166_sm2_pytest_paths(PR166_SM2_PYTEST_FILE_GROUPS[3]),
            reason="PR166-SM2 split subgroup 4 preserving full test coverage",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=3.0,
        ),
        PytestShardCommand(
            paths=_pr166_sm2_pytest_paths(PR166_SM2_PYTEST_FILE_GROUPS[4]),
            reason="PR166-SM2 split subgroup 5 preserving full test coverage",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=4.0,
        ),
        PytestShardCommand(
            paths=_pr166_sm2_pytest_paths(PR166_SM2_PYTEST_FILE_GROUPS[5]),
            reason="PR166-SM2 split subgroup 6 preserving full test coverage",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=28.0,
        ),
    ),
    "pytest-shard-6": (
        PytestShardCommand(
            paths=_pr166_sf_r2_pytest_paths(PR166_SF_R2_PYTEST_FILE_GROUPS[0]),
            reason="PR166-SF-R2 non-idempotence split subgroup 1",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=8.0,
        ),
        PytestShardCommand(
            paths=_pr166_sf_r2_pytest_paths(PR166_SF_R2_PYTEST_FILE_GROUPS[1]),
            reason="PR166-SF-R2 non-idempotence split subgroup 2",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=2.0,
        ),
        PytestShardCommand(
            paths=_pr166_sf_r2_pytest_paths(PR166_SF_R2_PYTEST_FILE_GROUPS[2]),
            reason=(
                "PR166-SF-R2 heavy non-idempotence subgroup isolated from "
                "bounded idempotence and PR166-SM2"
            ),
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=115.0,
            known_historical_heavy=True,
        ),
        PytestShardCommand(
            paths=_pr166_sf_r2_pytest_paths(PR166_SF_R2_PYTEST_FILE_GROUPS[4]),
            reason="PR166-SF-R2 non-idempotence split subgroup 4",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=1.0,
        ),
        PytestShardCommand(
            paths=_pr166_sf_r2_pytest_paths(PR166_SF_R2_PYTEST_FILE_GROUPS[5]),
            reason="PR166-SF-R2 non-idempotence split subgroup 5",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=2.0,
        ),
        PytestShardCommand(
            paths=_pr166_sf_r2_pytest_paths(PR166_SF_R2_PYTEST_FILE_GROUPS[6]),
            reason="PR166-SF-R2 non-idempotence split subgroup 6",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=2.0,
        ),
        PytestShardCommand(
            paths=_pr166_sf_r2_pytest_paths(PR166_SF_R2_PYTEST_FILE_GROUPS[7]),
            reason="PR166-SF-R2 non-idempotence split subgroup 7",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=28.0,
        ),
    ),
    "pytest-shard-7": (
        PytestShardCommand(
            paths=(
                "tests/stage1_prediction_markets/pr165_d3_quantum_aware_scenario_selection_v3",
            ),
            reason=(
                "Current PR165-D3 test group kept first so current PR failures "
                "are not buried behind historical families"
            ),
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=154.0,
            known_historical_heavy=True,
        ),
        PytestShardCommand(
            paths=(
                f"{PR166_SM3_TEST_ROOT}/{PR166_SM3_IDEMPOTENCE_TEST_FILE}",
            ),
            reason=(
                "Bounded PR166-SM3 idempotence proof kept explicit so default "
                "PR CI does not run the exhaustive byte-for-byte rebuild mode"
            ),
            runtime_budget_seconds=PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS,
            historical_runtime_seconds=100.0,
            known_historical_heavy=True,
            bounded_idempotence=True,
        ),
        PytestShardCommand(
            paths=(PR166_SM3_TEST_ROOT,),
            ignores=(
                f"{PR166_SM3_TEST_ROOT}/{PR166_SM3_IDEMPOTENCE_TEST_FILE}",
            ),
            reason="PR166-SM3 downstream score-memory non-idempotence group",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=55.0,
        ),
    ),
    "pytest-shard-8": (
        PytestShardCommand(
            paths=(
                f"{PR166_Q_TEST_ROOT}/{PR166_Q_IDEMPOTENCE_TEST_FILE}",
            ),
            reason=(
                "Bounded PR166-Q idempotence proof kept explicit so default "
                "PR CI does not run the exhaustive byte-for-byte rebuild mode"
            ),
            runtime_budget_seconds=PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS,
            historical_runtime_seconds=15.0,
            bounded_idempotence=True,
        ),
        PytestShardCommand(
            paths=(PR166_Q_TEST_ROOT,),
            ignores=(
                f"{PR166_Q_TEST_ROOT}/{PR166_Q_IDEMPOTENCE_TEST_FILE}",
            ),
            reason="PR166-Q quantum/classical/hybrid comparator non-idempotence group",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=15.0,
        ),
        PytestShardCommand(
            paths=(
                f"{PR166_QB_TEST_ROOT}/{PR166_QB_IDEMPOTENCE_TEST_FILE}",
            ),
            reason=(
                "Bounded PR166-QB idempotence proof kept explicit so default "
                "PR CI does not run the exhaustive byte-for-byte rebuild mode"
            ),
            runtime_budget_seconds=PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS,
            historical_runtime_seconds=5.0,
            bounded_idempotence=True,
        ),
        PytestShardCommand(
            paths=(PR166_QB_TEST_ROOT,),
            ignores=(
                f"{PR166_QB_TEST_ROOT}/{PR166_QB_IDEMPOTENCE_TEST_FILE}",
            ),
            reason="PR166-QB bounded non-live quantum benchmark non-idempotence group",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=5.0,
        ),
        PytestShardCommand(
            paths=(
                f"{PR166_QC_TEST_ROOT}/{PR166_QC_IDEMPOTENCE_TEST_FILE}",
            ),
            reason=(
                "Bounded PR166-QC idempotence proof kept explicit so default "
                "PR CI does not run the exhaustive byte-for-byte rebuild mode"
            ),
            runtime_budget_seconds=PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS,
            historical_runtime_seconds=5.0,
            bounded_idempotence=True,
        ),
        PytestShardCommand(
            paths=(PR166_QC_TEST_ROOT,),
            ignores=(
                f"{PR166_QC_TEST_ROOT}/{PR166_QC_IDEMPOTENCE_TEST_FILE}",
            ),
            reason="PR166-QC quantum-selected replay/paper retest non-idempotence group",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=5.0,
        ),
        PytestShardCommand(
            paths=(
                f"{PR162E_Q_TEST_ROOT}/{PR162E_Q_IDEMPOTENCE_TEST_FILE}",
            ),
            reason=(
                "Bounded PR162E-Q idempotence proof kept explicit so default "
                "PR CI does not run the exhaustive byte-for-byte rebuild mode"
            ),
            runtime_budget_seconds=PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS,
            historical_runtime_seconds=5.0,
            bounded_idempotence=True,
        ),
        PytestShardCommand(
            paths=(PR162E_Q_TEST_ROOT,),
            ignores=(
                f"{PR162E_Q_TEST_ROOT}/{PR162E_Q_IDEMPOTENCE_TEST_FILE}",
            ),
            reason="PR162E-Q quantum automapper non-idempotence group",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=5.0,
        ),
        PytestShardCommand(
            paths=(
                f"{PR167_TEST_ROOT}/{PR167_IDEMPOTENCE_TEST_FILE}",
            ),
            reason=(
                "Bounded PR167 open-trade simulator idempotence proof kept explicit "
                "so default PR CI does not run an exhaustive rebuild mode"
            ),
            runtime_budget_seconds=PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS,
            historical_runtime_seconds=18.0,
            bounded_idempotence=True,
        ),
        PytestShardCommand(
            paths=(PR167_TEST_ROOT,),
            ignores=(
                f"{PR167_TEST_ROOT}/{PR167_IDEMPOTENCE_TEST_FILE}",
            ),
            reason="PR167 open-trade simulator integration non-idempotence group",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=20.0,
        ),
        PytestShardCommand(
            paths=(
                f"{PR162E_TEST_ROOT}/{PR162E_IDEMPOTENCE_TEST_FILE}",
            ),
            reason=(
                "Bounded PR162E plugin framework idempotence proof kept explicit "
                "so default PR CI does not run an exhaustive rebuild mode"
            ),
            runtime_budget_seconds=PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS,
            historical_runtime_seconds=4.0,
            bounded_idempotence=True,
        ),
        PytestShardCommand(
            paths=(PR162E_TEST_ROOT,),
            ignores=(
                f"{PR162E_TEST_ROOT}/{PR162E_IDEMPOTENCE_TEST_FILE}",
            ),
            reason="PR162E plugin framework focused tests",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=4.0,
        ),
        PytestShardCommand(
            paths=(ISOLATED_SOURCE_EVIDENCE_PYTEST,),
            reason="Preserves the existing isolated source-evidence pytest invocation",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=52.0,
        ),
        PytestShardCommand(
            paths=(
                "tests/agent_algorithm",
                "tests/agents",
                "tests/algorithms",
                "tests/connectors",
            ),
            reason="Shard 4 residual tests, subprocess group 1",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=8.0,
        ),
        PytestShardCommand(
            paths=(
                "tests/core",
                "tests/dashboard",
                "tests/edge",
                "tests/external_repo",
                "tests/governance",
                "tests/launch",
                "tests/master_plan",
            ),
            reason="Shard 4 residual tests, subprocess group 2",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=37.0,
        ),
        PytestShardCommand(
            paths=("tests/global_debug",),
            reason="Shard 4 PR152 global-debug residual tests, subprocess group 3",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=215.0,
            known_historical_heavy=True,
        ),
        PytestShardCommand(
            paths=(
                "tests/neural_signal",
                "tests/quantum",
                "tests/replay_paper",
                "tests/replay_paper_review",
                "tests/research",
                "tests/roadmap",
            ),
            reason="Shard 4 residual tests, subprocess group 4",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=10.0,
        ),
        PytestShardCommand(
            paths=(
                "tests/runtime_cash",
                "tests/runtime_orchestration",
                "tests/runtime_resolver",
                "tests/scoring",
                "tests/selection",
                "tests/venue_neutral_prediction_adapter",
            ),
            reason="Shard 4 residual tests, subprocess group 5",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=10.0,
        ),
        PytestShardCommand(
            paths=("tests/source_evidence",),
            ignores=(ISOLATED_SOURCE_EVIDENCE_PYTEST,),
            reason="Shard 4 source-evidence residual tests, subprocess group 6",
            runtime_budget_seconds=PYTEST_SUBPROCESS_GROUP_TARGET_SECONDS,
            historical_runtime_seconds=10.0,
        ),
    ),
}
PRE_VALIDATION_FINALIZATION_GUIDANCE = (
    {
        "command_id": "pr152_currentize_after_generated_artifacts",
        "command": (
            ".\\.venv\\Scripts\\python.exe "
            "tools\\currentize_pr152_after_generated_artifacts.py"
        ),
        "when": "after final generated artifacts settle and before validation gates",
        "ci_tracked_report_mutation_allowed": False,
    },
)
PR142_HANDOFF_READINESS_VALIDATOR_SCRIPT = (
    "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
)
PR143_OWNER_OVERRIDE_CURRENTIZATION_VALIDATOR_SCRIPT = (
    "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
)
_RUN_COMMANDS_CLEANUP_REPO_ROOT: pathlib.Path | None = None
TRACKED_GENERATED_PATH_PREFIXES = (
    "docs/master_plan/generated/",
    "docs/master_plan/source_evidence/generated/",
    "docs/roadmap/generated/",
)
VOLATILE_GENERATED_REPORT_CURRENTNESS_FIELDS = frozenset(
    {
        "branch",
        "base_head",
    }
)
GENERATED_REPORT_CURRENTNESS_IGNORED_FIELDS = (
    VOLATILE_GENERATED_REPORT_CURRENTNESS_FIELDS | {"report_path"}
)
CHECK_ONLY_VALIDATOR_SCRIPTS = frozenset(
    {
        "validate_source_evidence_retrieval_executor.py",
        "validate_source_evidence_acceptance.py",
        "validate_source_revalidation_scheduler.py",
        "validate_connector_semantic_binding_implementation_gate.py",
        "validate_per_venue_execution_lifecycle_model.py",
        "validate_cross_venue_execution_normalization_binding.py",
        "runtime_cash_component_field_map_validate.py",
        "private_state_read_receipt_gate_validate.py",
        "credential_alias_secret_no_capture_readiness_validate.py",
        "venue_market_data_ingest_adapters_validate.py",
        "orderbook_event_state_snapshot_builder_validate.py",
        "runtime_resolver_snapshot_executor_validate.py",
    }
)
DEFAULT_GENERATED_OUTPUT_ARGS = {
    "validate_qtt_owner_global_override_authority.py": (
        "--out",
        "docs/master_plan/generated/QTTOwnerGlobalOverrideAuthority.report.json",
    ),
    "validate_qtt_agent_role_operating_charter_registry.py": (
        "--out",
        "docs/master_plan/generated/QTTAgentRoleOperatingCharterReport.json",
    ),
    "validate_qtt_algorithm_formula_family_registry.py": (
        "--out",
        "docs/master_plan/generated/QTTAlgorithmFormulaFamilyReport.json",
    ),
    "validate_qtt_agent_algorithm_binding_registry.py": (
        "--out",
        "docs/master_plan/generated/QTTAgentAlgorithmBindingReport.json",
    ),
    "validate_qtt_agent_algorithm_consumer_gate.py": (
        "--out",
        "docs/master_plan/generated/QTTAgentAlgorithmConsumerGate.report.json",
    ),
    "validate_qtt_agent_algorithm_cumulative_readiness_gate.py": (
        "--out",
        "docs/master_plan/generated/QTTAgentAlgorithmCumulativeReadinessGate.report.json",
    ),
    "validate_accepted_source_to_connector_semantic_binding.py": (
        "--out",
        "docs/master_plan/source_evidence/generated/CODEX_PR124_ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE_REPORT.json",
    ),
    "validate_source_revalidation_scheduler.py": (
        "--out",
        "docs/master_plan/source_evidence/generated/CODEX_PR125_SOURCE_REVALIDATION_SUPERSESSION_MATERIALITY_SCHEDULER_REPORT.json",
    ),
    "validate_qtt_agent_algorithm_command_matrix.py": (
        "--out",
        "docs/master_plan/generated/QTTAgentAlgorithmCommandMatrix.json",
    ),
    "build_atomicrows_parameter_lifecycle_report.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterLifecycleReport.json",
    ),
    "validate_atomicrows_lifecycle_consumer_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsLifecycleConsumerGate.report.json",
    ),
    "validate_atomicrows_lifecycle_promotion_receipt_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsLifecyclePromotionReceiptGate.report.json",
    ),
    "validate_atomicrows_lifecycle_registry_mutation_guard.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsLifecycleRegistryMutationGuard.report.json",
    ),
    "validate_atomicrows_lifecycle_cumulative_readiness_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsLifecycleCumulativeReadinessGate.report.json",
    ),
    "validate_atomicrows_lifecycle_gate_command_matrix.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsLifecycleGateCommandMatrix.json",
    ),
    "validate_atomicrows_parameter_agent_binding_registry.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterAgentBindingReport.json",
    ),
    "validate_atomicrows_parameter_agent_binding_consumer_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterAgentBindingConsumerGate.report.json",
    ),
    "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json",
    ),
    "validate_atomicrows_parameter_agent_binding_command_matrix.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterAgentBindingCommandMatrix.json",
    ),
    "validate_atomicrows_research_provenance_evidence_tier_classification.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsResearchProvenanceEvidenceTierClassification.report.json",
    ),
    "validate_atomicrows_owner_submitted_research_source_intake_registry.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.report.json",
    ),
    "validate_atomicrows_research_source_to_candidate_family_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsResearchSourceToCandidateFamilyGate.report.json",
    ),
    "validate_atomicrows_parameter_stack_role_taxonomy.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterStackRoleTaxonomy.report.json",
    ),
    "validate_atomicrows_parameter_stack_completeness_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterStackCompletenessGate.report.json",
    ),
    "validate_atomicrows_parameter_stack_compatibility_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterStackCompatibilityGate.report.json",
    ),
    "validate_edge_parameter_stack_selection_packet.py": (
        "--out",
        "docs/master_plan/generated/EDGEParameterStackSelectionPacket.report.json",
    ),
    "validate_qtt_trade_context_packet.py": (
        "--out",
        "docs/master_plan/generated/QTTTradeContextPacket.report.json",
    ),
    "validate_atomicrows_parameter_selection_universe_registry.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterSelectionUniverseRegistry.report.json",
    ),
    "validate_atomicrows_parameter_selection_universe_consumer_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsParameterSelectionUniverseConsumerGate.report.json",
    ),
    "validate_trade_context_selection_universe_routing_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsTradeContextSelectionUniverseRoutingGate.report.json",
    ),
    "validate_quantum_applicability_classification_registry.py": (
        "--out",
        "docs/master_plan/generated/QuantumApplicabilityClassificationRegistry.report.json",
    ),
    "validate_owner_quantum_priority_policy_registry.py": (
        "--out",
        "docs/master_plan/generated/OwnerQuantumPriorityPolicyRegistry.report.json",
    ),
    "validate_parameter_algorithm_scoring_policy_registry.py": (
        "--out",
        "docs/master_plan/generated/ParameterAlgorithmScoringPolicyRegistry.report.json",
    ),
    "validate_parameter_stack_scoring_and_ranking_gate.py": (
        "--out",
        "docs/master_plan/generated/ParameterStackScoringAndRankingGate.report.json",
    ),
    "validate_quantum_classical_optimizer_arbitration_gate.py": (
        "--out",
        "docs/master_plan/generated/QuantumClassicalOptimizerArbitrationGate.report.json",
    ),
    "validate_candidate_parameter_stack_generation_gate.py": (
        "--out",
        "docs/master_plan/generated/CandidateParameterStackGenerationGate.report.json",
    ),
    "validate_trade_context_parameter_stack_selection_gate.py": (
        "--out",
        "docs/master_plan/generated/TradeContextParameterStackSelectionGate.report.json",
    ),
    "validate_selected_parameter_stack_handoff_packet.py": (
        "--out",
        "docs/master_plan/generated/SelectedParameterStackHandoffPacket.report.json",
    ),
    "validate_replay_paper_candidate_stack_competition_gate.py": (
        "--out",
        "docs/master_plan/generated/ReplayPaperCandidateStackCompetitionGate.report.json",
    ),
    "validate_dual_result_review_for_parameter_stacks.py": (
        "--out",
        "docs/master_plan/generated/DualResultReviewForParameterStacks.report.json",
    ),
    "validate_owner_live_promotion_review_for_parameter_stacks.py": (
        "--out",
        "docs/master_plan/generated/OwnerLivePromotionReviewForParameterStacks.report.json",
    ),
    "validate_owner_approval_request_queue_registry.py": (
        "--out",
        "docs/master_plan/generated/OwnerApprovalRequestQueueRegistry.report.json",
    ),
    "validate_owner_override_receipt_authoring_gate.py": (
        "--out",
        "docs/master_plan/generated/OwnerOverrideReceiptAuthoringGate.report.json",
    ),
    "validate_owner_dashboard_approval_menu_schema.py": (
        "--out",
        "docs/master_plan/generated/OwnerDashboardApprovalMenuSchema.report.json",
    ),
    "validate_owner_dashboard_approval_static_screen_contract.py": (
        "--out",
        "docs/master_plan/generated/OwnerDashboardApprovalStaticScreenContract.report.json",
    ),
    "validate_atomicrows_full_bundle_row_expansion_plan.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsFullBundleRowExpansionPlan.report.json",
    ),
    "validate_atomicrows_bundle_row_family_source_files.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsBundleRowFamilySourceFiles.report.json",
    ),
    "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py": (
        "--out",
        "docs/master_plan/generated/AtomicRowsBundleBuilderDeterministicAssemblyGate.report.json",
    ),
    "validate_atomicrows_sha_system_dormancy_state_contract.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsShaSystemDormancyStateContract.report.json",
    ),
    "validate_qtt_final_readiness_dependency_policy_contract.py": (
        "--report-out",
        "docs/master_plan/generated/QttFinalReadinessDependencyPolicy.report.json",
    ),
    "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py": (
        "--report-out",
        "docs/master_plan/generated/QttActiveNonShaDay1GateStateRegistry.report.json",
    ),
    "validate_qtt_pr_identity_roster.py": (
        "--report-out",
        "docs/master_plan/generated/QttPrIdentityRoster.report.json",
    ),
    "validate_qtt_roadmap_execution_state_controller.py": (
        "--report-out",
        "docs/master_plan/generated/QttRoadmapExecutionStateController.report.json",
    ),
    "validate_atomicrows_bundle_sha_freeze_authority_gate.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsBundleShaFreezeAuthorityGate.report.json",
    ),
    "validate_atomicrows_exact_row_authority_classifier_bridge.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsExactRowAuthorityClassifierBridge.report.json",
    ),
    "validate_atomicrows_exact_row_expansion_manifest.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsExactRowExpansionManifest.report.json",
    ),
    "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsOwnerApprovedExact15FamilyCountDistribution.report.json",
    ),
    "validate_atomicrows_exact_row_generator_dry_run_manifest.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsExactRowGeneratorDryRun.report.json",
    ),
    "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsRepairChainGrandDebugLogicAudit.report.json",
    ),
    "validate_atomicrows_exact_row_source_materialization_manifest.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsExactRowSourceMaterialization.report.json",
    ),
    "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsExactRowAgentFamilyEligibilityMatrix.report.json",
    ),
    "validate_atomicrows_bundle_materialization_manifest.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsBundleMaterialization.report.json",
    ),
    "validate_atomicrows_bundle_boundary_state_contract.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsBundleBoundaryStateContract.report.json",
    ),
    "validate_atomicrows_sha_freeze_final_readiness_state_contract.py": (
        "--report-out",
        "docs/master_plan/generated/AtomicRowsShaFreezeFinalReadinessStateContract.report.json",
    ),
    "stage1_connector_semantic_binding_ledger_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1ConnectorSemanticBindingLedgerCheck.report.json",
    ),
    "stage1_runtime_resolver_snapshot_contract_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1RuntimeResolverSnapshotContractCheck.report.json",
    ),
    "stage1_runtime_resolver_to_replay_paper_handoff_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1RuntimeResolverToReplayPaperHandoff.report.json",
    ),
    "stage1_concurrent_replay_paper_contract_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1ConcurrentReplayPaperContractCheck.report.json",
    ),
    "stage1_dual_result_review_contract_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1DualResultReviewContractCheck.report.json",
    ),
    "stage1_owner_live_promotion_review_contract_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1OwnerLivePromotionReviewContractCheck.report.json",
    ),
    "stage1_three_venue_canary_eligibility_contract_check.py": (
        "--out",
        "docs/master_plan/generated/Stage1ThreeVenueCanaryEligibilityContractCheck.report.json",
    ),
    "qtt_test_gate.py": (
        "--out",
        "docs/master_plan/generated/QTTTestGate.report.json",
    ),
    "local_gate_command_matrix.py": (
        "--out",
        "docs/master_plan/generated/LocalGateCommandMatrix.json",
    ),
    "pr_handoff_check.py": (
        "--out",
        "docs/master_plan/generated/FirstCodingPRHandoff.packet.json",
    ),
    "build_master_plan_section_coverage_report.py": (
        "--out",
        "docs/master_plan/generated/MasterPlanSectionCoverageReport.json",
    ),
}
GENERATED_REPORT_CURRENTNESS_OUTPUT_ARGS: dict[str, tuple[str, str]] = {}
PR138_NON_MUTATING_VALIDATION_SCRIPT = (
    "from pathlib import Path\n"
    "from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.report "
    "import build_report\n"
    "from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.validator "
    "import validate_report_payload, validate_repository_artifacts\n"
    "root = Path('.').resolve()\n"
    "report = build_report(root)\n"
    "failures = list(validate_repository_artifacts(root))\n"
    "outcome = validate_report_payload(\n"
    "    report,\n"
    "    repo_root=root,\n"
    "    enforce_environment=True,\n"
    "    enforce_protected_diff=True,\n"
    ")\n"
    "failures.extend(outcome.failures)\n"
    "unique_failures = tuple(sorted(set(failures)))\n"
    "if unique_failures:\n"
    "    print('\\n'.join(unique_failures))\n"
    "    raise SystemExit(1)\n"
    "for receipt in outcome.receipts:\n"
    "    print(receipt)\n"
)
ATOMICROWS_BUNDLE_CHECK_SCRIPT = (
    "import json\n"
    "from pathlib import Path\n"
    "\n"
    "bundle = Path('docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl')\n"
    "sidecar = Path('docs/master_plan/atomic_rows') / ('AtomicRows' + '.bundle' + '.' + 'sha256')\n"
    "if not bundle.is_file():\n"
    "    raise SystemExit('AtomicRows bundle is missing')\n"
    "if sidecar.exists():\n"
    "    raise SystemExit('AtomicRows bundle SHA sidecar must be absent')\n"
    "data = bundle.read_bytes()\n"
    "assert data, 'AtomicRows bundle is empty'\n"
    "assert not data.startswith(b'\\xef\\xbb\\xbf'), 'AtomicRows bundle has a UTF-8 BOM'\n"
    "assert b'\\r' not in data, 'AtomicRows bundle contains CR or CRLF line endings'\n"
    "assert data.endswith(b'\\n'), 'AtomicRows bundle must end with LF'\n"
    "lines = data.decode('utf-8').splitlines()\n"
    "assert len(lines) == 4183, f'expected 4183 AtomicRows rows, found {len(lines)}'\n"
    "assert all(line.strip() for line in lines), 'AtomicRows bundle contains blank rows'\n"
    "for line_number, line in enumerate(lines, start=1):\n"
    "    json.loads(line)\n"
)


def _path(*parts: str) -> str:
    return str(pathlib.Path(*parts))


def _default_validation_dir() -> pathlib.Path:
    return pathlib.Path(tempfile.gettempdir()) / "qtt_validation_gates"


def _default_pytest_basetemp() -> pathlib.Path:
    return (
        pathlib.Path(tempfile.gettempdir())
        / PYTEST_BASETEMP_PARENT
        / f"run_validation_gates_pytest_{os.getpid()}"
    )


def _repo_root() -> pathlib.Path:
    return REPO_ROOT


def _is_final_pytest_command(command: Sequence[str]) -> bool:
    return (
        len(command) > 1
        and pathlib.PurePath(command[1]).name == PYTEST_FRESH_BASETEMP_SCRIPT
    )


def build_pre_validation_finalization_guidance() -> list[dict[str, object]]:
    return [dict(record) for record in PRE_VALIDATION_FINALIZATION_GUIDANCE]


def _command_script_name(command: Sequence[str]) -> str:
    if len(command) <= 1:
        return ""
    return pathlib.PurePath(command[1]).name


def _command_uses_pytest_helper(command: Sequence[str]) -> bool:
    return _command_script_name(command) == PYTEST_FRESH_BASETEMP_SCRIPT


def _normal_repo_path_text(value: pathlib.Path | str) -> str:
    return str(value).replace("\\", "/")


def _is_pytest_file(path: pathlib.Path) -> bool:
    return path.is_file() and path.suffix == ".py" and path.name.startswith("test_")


def discover_pytest_files(repo_root: pathlib.Path | str | None = None) -> tuple[str, ...]:
    root = _repo_root() if repo_root is None else pathlib.Path(repo_root)
    tests_root = root / "tests"
    if not tests_root.exists():
        return ()
    return tuple(
        sorted(
            _normal_repo_path_text(path.relative_to(root))
            for path in tests_root.rglob("*.py")
            if _is_pytest_file(path)
        )
    )


def _path_contains(parent: str, child: str) -> bool:
    normalized_parent = parent.rstrip("/")
    normalized_child = child.rstrip("/")
    return normalized_child == normalized_parent or normalized_child.startswith(
        f"{normalized_parent}/"
    )


def _pytest_files_for_command(
    command: PytestShardCommand,
    repo_root: pathlib.Path | str | None = None,
) -> tuple[str, ...]:
    root = _repo_root() if repo_root is None else pathlib.Path(repo_root)
    all_files = discover_pytest_files(root)
    selected: set[str] = set()
    for path_text in command.paths:
        normalized = _normal_repo_path_text(path_text)
        path = root / normalized
        if path.is_file():
            selected.add(normalized)
            continue
        selected.update(
            test_file for test_file in all_files if _path_contains(normalized, test_file)
        )
    for ignore_text in command.ignores:
        normalized_ignore = _normal_repo_path_text(ignore_text)
        selected = {
            test_file
            for test_file in selected
            if not _path_contains(normalized_ignore, test_file)
        }
    return tuple(sorted(selected))


def pytest_shard_manifest(
    repo_root: pathlib.Path | str | None = None,
) -> dict[str, tuple[str, ...]]:
    manifest: dict[str, list[str]] = {phase: [] for phase in PYTEST_SHARD_PHASES}
    for phase in PYTEST_SHARD_PHASES:
        for command in PYTEST_SHARD_COMMANDS[phase]:
            manifest[phase].extend(_pytest_files_for_command(command, repo_root))
    return {phase: tuple(sorted(paths)) for phase, paths in manifest.items()}


def pytest_shard_membership(
    repo_root: pathlib.Path | str | None = None,
) -> dict[str, str]:
    membership: dict[str, str] = {}
    duplicates: list[str] = []
    for phase, paths in pytest_shard_manifest(repo_root).items():
        for path in paths:
            if path in membership:
                duplicates.append(path)
                continue
            membership[path] = phase
    if duplicates:
        duplicate_text = ", ".join(sorted(duplicates))
        raise ValueError(f"pytest shard duplicate test files: {duplicate_text}")
    return membership


def pytest_runtime_budget_plan() -> dict[str, object]:
    return {
        "policy": dict(RUNTIME_BUDGET_POLICY),
        "shard_budgets": deepcopy(PYTEST_SHARD_RUNTIME_BUDGETS),
        "pytest_shards": {
            phase: [
                {
                    "paths": list(command.paths),
                    "ignores": list(command.ignores),
                    "reason": command.reason,
                    "runtime_budget_seconds": command.runtime_budget_seconds,
                    "historical_runtime_seconds": command.historical_runtime_seconds,
                    "known_historical_heavy": command.known_historical_heavy,
                    "bounded_idempotence": command.bounded_idempotence,
                }
                for command in PYTEST_SHARD_COMMANDS[phase]
            ]
            for phase in PYTEST_SHARD_PHASES
        },
    }


def pytest_runtime_budget_failures(
    repo_root: pathlib.Path | str | None = None,
) -> tuple[str, ...]:
    root = _repo_root() if repo_root is None else pathlib.Path(repo_root)
    failures: list[str] = []
    if set(PYTEST_SHARD_COMMANDS) != set(PYTEST_SHARD_PHASES):
        failures.append("PYTEST_SHARD_COMMAND_PHASE_MISMATCH")
    if set(PYTEST_SHARD_RUNTIME_BUDGETS) != set(PYTEST_SHARD_PHASES):
        failures.append("PYTEST_SHARD_BUDGET_PHASE_MISMATCH")

    all_tests = set(discover_pytest_files(root))
    manifest = pytest_shard_manifest(root)
    flattened = [
        path
        for phase_paths in manifest.values()
        for path in phase_paths
    ]
    missing = sorted(all_tests - set(flattened))
    duplicates = sorted({path for path in flattened if flattened.count(path) > 1})
    if missing:
        failures.append("PYTEST_SHARD_UNASSIGNED_TESTS: " + ", ".join(missing))
    if duplicates:
        failures.append("PYTEST_SHARD_DUPLICATE_TESTS: " + ", ".join(duplicates))

    idempotence_placements: dict[
        str, list[tuple[str, int, PytestShardCommand]]
    ] = {
        path: []
        for path in sorted(BOUNDED_DEFAULT_IDEMPOTENCE_TEST_PATHS)
    }
    for phase in PYTEST_SHARD_PHASES:
        commands = PYTEST_SHARD_COMMANDS.get(phase, ())
        if not commands:
            failures.append(f"PYTEST_SHARD_EMPTY: {phase}")
            continue
        estimated_total = 0.0
        heavy_indices: list[int] = []
        for index, command in enumerate(commands, start=1):
            expanded_command_paths = _pytest_files_for_command(command, root)
            if command.runtime_budget_seconds is None:
                failures.append(f"PYTEST_GROUP_MISSING_RUNTIME_BUDGET: {phase}:{index}")
            elif command.runtime_budget_seconds <= 0:
                failures.append(f"PYTEST_GROUP_BAD_RUNTIME_BUDGET: {phase}:{index}")
            if not command.reason:
                failures.append(f"PYTEST_GROUP_MISSING_REASON: {phase}:{index}")
            if command.historical_runtime_seconds is None:
                failures.append(f"PYTEST_GROUP_MISSING_HISTORICAL_RUNTIME: {phase}:{index}")
            else:
                estimated_total += command.historical_runtime_seconds
            if command.known_historical_heavy:
                heavy_indices.append(index)
            contains_idempotence = any(
                path.endswith("_idempotence.py") or path.endswith("idempotence.py")
                for path in command.paths
            )
            if (
                contains_idempotence
                and not command.bounded_idempotence
                and command.historical_runtime_seconds is not None
                and command.historical_runtime_seconds
                > PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS
            ):
                failures.append(f"PYTEST_UNBOUNDED_IDEMPOTENCE_OVER_HARD_REVIEW: {phase}:{index}")
            for idempotence_path in BOUNDED_DEFAULT_IDEMPOTENCE_TEST_PATHS:
                if idempotence_path not in expanded_command_paths:
                    continue
                idempotence_placements[idempotence_path].append((phase, index, command))
                if not command.bounded_idempotence:
                    failures.append(f"PYTEST_IDEMPOTENCE_GROUP_NOT_BOUNDED: {idempotence_path}")
                if (
                    command.runtime_budget_seconds is None
                    or command.runtime_budget_seconds
                    > PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS
                ):
                    failures.append(f"PYTEST_IDEMPOTENCE_GROUP_BUDGET_TOO_HIGH: {idempotence_path}")
        shard_budget = PYTEST_SHARD_RUNTIME_BUDGETS.get(phase, {})
        target = float(shard_budget.get("target_seconds", 0))
        if estimated_total > target:
            failures.append(
                f"PYTEST_SHARD_ESTIMATE_OVER_TARGET: {phase} {estimated_total:.1f}"
            )
            if any(index > 2 for index in heavy_indices):
                failures.append(f"PYTEST_HEAVY_GROUP_LATE_IN_OVERLOADED_SHARD: {phase}")
        if len(heavy_indices) > 2:
            failures.append(f"PYTEST_HEAVY_GROUPS_CONCENTRATED: {phase}")

    for idempotence_path, placements in idempotence_placements.items():
        if len(placements) != 1:
            failures.append(
                f"PYTEST_IDEMPOTENCE_GROUP_PLACEMENT_COUNT: {idempotence_path}"
            )
    return tuple(failures)


def _is_pr142_handoff_readiness_validator_command(command: Sequence[str]) -> bool:
    return (
        len(command) > 1
        and pathlib.PurePath(command[1]).name == PR142_HANDOFF_READINESS_VALIDATOR_SCRIPT
    )


def _is_pr143_owner_override_currentization_validator_command(
    command: Sequence[str],
) -> bool:
    return (
        len(command) > 1
        and pathlib.PurePath(command[1]).name
        == PR143_OWNER_OVERRIDE_CURRENTIZATION_VALIDATOR_SCRIPT
    )


def _normal_path_text(value: pathlib.Path | str) -> str:
    return str(value).replace("\\", "/")


def _is_tracked_generated_output_path(value: pathlib.Path | str) -> bool:
    normalized = _normal_path_text(value)
    return any(
        normalized.startswith(prefix) for prefix in TRACKED_GENERATED_PATH_PREFIXES
    )


def _validation_generated_output(
    validation_dir: pathlib.Path,
    tracked_path: pathlib.Path | str,
) -> pathlib.Path:
    normalized = _normal_path_text(tracked_path)
    bucket = (
        "roadmap_generated"
        if normalized.startswith("docs/roadmap/generated/")
        else "master_plan_generated"
    )
    return validation_dir / bucket / pathlib.PurePosixPath(normalized).name


def _route_command_generated_outputs_to_temp(
    command: Sequence[str],
    validation_dir: pathlib.Path,
) -> list[str]:
    routed = [str(part) for part in command]
    for index, token in enumerate(routed[:-1]):
        if (
            token in {"--out", "--report-out"}
            or token.endswith("-out")
        ) and _is_tracked_generated_output_path(routed[index + 1]):
            routed[index + 1] = str(
                _validation_generated_output(validation_dir, routed[index + 1])
            )

    if len(routed) > 1:
        script_name = pathlib.PurePath(routed[1]).name
        if script_name in CHECK_ONLY_VALIDATOR_SCRIPTS and "--check-only" not in routed:
            routed.append("--check-only")
        if script_name in DEFAULT_GENERATED_OUTPUT_ARGS:
            flag, tracked_path = DEFAULT_GENERATED_OUTPUT_ARGS[script_name]
            if flag not in routed:
                routed.extend(
                    [
                        flag,
                        str(_validation_generated_output(validation_dir, tracked_path)),
                    ]
                )
    return routed


def _resolved_repo_path(repo_root: pathlib.Path, path_text: str) -> pathlib.Path:
    path = pathlib.Path(path_text)
    return path if path.is_absolute() else repo_root / path


def _json_currentness_payload(path: pathlib.Path) -> object:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return {
            key: value
            for key, value in payload.items()
            if key not in GENERATED_REPORT_CURRENTNESS_IGNORED_FIELDS
        }
    return payload


def _tracked_report_has_volatile_currentness_context(path: pathlib.Path) -> bool:
    if path.suffix.lower() != ".json":
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and any(
        key in payload for key in VOLATILE_GENERATED_REPORT_CURRENTNESS_FIELDS
    )


def _generated_reports_match_for_currentness(
    output_path: pathlib.Path,
    tracked_path: pathlib.Path,
) -> bool:
    if output_path.read_bytes() == tracked_path.read_bytes():
        return True
    if output_path.suffix.lower() != ".json" or tracked_path.suffix.lower() != ".json":
        return False
    try:
        return _json_currentness_payload(output_path) == _json_currentness_payload(
            tracked_path
        )
    except (OSError, json.JSONDecodeError):
        return False


def _routed_generated_output_currentness_failures(
    command: Sequence[str],
    repo_root: pathlib.Path,
) -> list[str]:
    if "--check-only" in command or len(command) <= 1:
        return []
    script_name = pathlib.PurePath(command[1]).name
    output_arg = GENERATED_REPORT_CURRENTNESS_OUTPUT_ARGS.get(script_name)
    if output_arg is None:
        return []
    flag, tracked_path_text = output_arg
    command_list = [str(part) for part in command]
    if flag not in command_list:
        return []
    output_index = command_list.index(flag) + 1
    if output_index >= len(command_list):
        return [f"TRACKED_GENERATED_REPORT_OUTPUT_ARG_MISSING: {script_name} {flag}"]

    output_text = command_list[output_index]
    if _is_tracked_generated_output_path(output_text):
        return []

    output_path = _resolved_repo_path(repo_root, output_text)
    tracked_path = _resolved_repo_path(repo_root, tracked_path_text)
    if not output_path.exists():
        return [
            "TRACKED_GENERATED_REPORT_TEMP_OUTPUT_MISSING: "
            f"{_normal_path_text(output_path)}"
        ]
    if not tracked_path.exists():
        return [
            "TRACKED_GENERATED_REPORT_MISSING: "
            f"{_normal_path_text(tracked_path_text)}"
        ]
    if _tracked_report_has_volatile_currentness_context(tracked_path):
        return []
    if not _generated_reports_match_for_currentness(output_path, tracked_path):
        return [
            "TRACKED_GENERATED_REPORT_STALE: "
            f"{_normal_path_text(tracked_path_text)} differs from validation temp output "
            f"{_normal_path_text(output_path)}"
        ]
    return []


def _git_stdout(repo_root: pathlib.Path, args: Sequence[str]) -> tuple[int, str, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout, completed.stderr


def _json_cache_bytes(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _path_is_relative_to(path: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _no_runtime_scanner_module():
    from tools import validate_no_runtime_artifacts

    return validate_no_runtime_artifacts


def _no_runtime_scan_cache_path(root: pathlib.Path) -> pathlib.Path | None:
    cache_text = os.environ.get(NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV)
    if not cache_text:
        return None
    cache_path = pathlib.Path(cache_text)
    if not cache_path.is_absolute():
        cache_path = root / cache_path
    return cache_path.resolve()


def _validate_no_runtime_scan_cache_path(
    root: pathlib.Path,
    cache_path: pathlib.Path,
) -> None:
    if not _path_is_relative_to(cache_path, root):
        return
    scanner = _no_runtime_scanner_module()
    rel = cache_path.relative_to(root)
    if rel.parts and rel.parts[0] in scanner.SKIP_DIR_PARTS:
        return
    raise RuntimeError(
        f"{NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV} must point outside the scanned tree "
        f"or under a skipped directory such as .tmp: {rel.as_posix()}"
    )


def _no_runtime_options_cache_payload(options) -> dict[str, bool]:
    fields = getattr(options, "__dataclass_fields__")
    return {field: bool(getattr(options, field)) for field in sorted(fields)}


def _no_runtime_scanner_source_digest() -> str:
    scanner = _no_runtime_scanner_module()
    return hashlib.sha256(pathlib.Path(scanner.__file__).read_bytes()).hexdigest()


def _git_tracked_blob_by_path(root: pathlib.Path) -> dict[str, str]:
    git_marker = root / ".git"
    if not git_marker.exists():
        return {}
    returncode, stdout, _stderr = _git_stdout(root, ["ls-files", "-s", "-z"])
    if returncode != 0:
        return {}

    tracked: dict[str, str] = {}
    for record in stdout.split("\0"):
        if not record:
            continue
        try:
            metadata, path_text = record.split("\t", 1)
        except ValueError:
            continue
        metadata_parts = metadata.split()
        if len(metadata_parts) >= 2:
            tracked[path_text] = metadata_parts[1]
    return tracked


def _no_runtime_scan_fingerprint(
    root: pathlib.Path,
    options,
) -> dict[str, object]:
    scanner = _no_runtime_scanner_module()
    paths = scanner._iter_paths(root)
    tracked_blobs = _git_tracked_blob_by_path(root)
    path_hasher = hashlib.sha256()
    for path in paths:
        rel = scanner._rel_path(path, root).as_posix()
        try:
            stat = path.stat()
            kind = "file" if path.is_file() else "dir"
            entry = {
                "kind": kind,
                "mtime_ns": stat.st_mtime_ns,
                "path": rel,
                "size": stat.st_size if kind == "file" else None,
                "tracked_blob": tracked_blobs.get(rel, ""),
            }
        except OSError as exc:
            entry = {
                "error": exc.__class__.__name__,
                "path": rel,
                "tracked_blob": tracked_blobs.get(rel, ""),
            }
        path_hasher.update(_json_cache_bytes(entry))
        path_hasher.update(b"\n")

    return {
        "cache_kind": NO_RUNTIME_ARTIFACT_SCAN_CACHE_KIND,
        "options": _no_runtime_options_cache_payload(options),
        "path_count": len(paths),
        "paths_digest": path_hasher.hexdigest(),
        "repo_root": str(root),
        "schema_version": NO_RUNTIME_ARTIFACT_SCAN_CACHE_SCHEMA_VERSION,
        "source_digest": _no_runtime_scanner_source_digest(),
    }


def _load_no_runtime_scan_cache(
    cache_path: pathlib.Path,
    fingerprint: dict[str, object],
) -> list[str] | None:
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("schema_version") != NO_RUNTIME_ARTIFACT_SCAN_CACHE_SCHEMA_VERSION:
        return None
    if payload.get("cache_kind") != NO_RUNTIME_ARTIFACT_SCAN_CACHE_KIND:
        return None
    if payload.get("fingerprint") != fingerprint:
        return None
    violations = payload.get("violations")
    if not isinstance(violations, list) or not all(
        isinstance(item, str) for item in violations
    ):
        return None
    return list(violations)


def _write_no_runtime_scan_cache(
    cache_path: pathlib.Path,
    fingerprint: dict[str, object],
    violations: Sequence[str],
) -> None:
    payload = {
        "cache_kind": NO_RUNTIME_ARTIFACT_SCAN_CACHE_KIND,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "fingerprint": fingerprint,
        "schema_version": NO_RUNTIME_ARTIFACT_SCAN_CACHE_SCHEMA_VERSION,
        "violations": list(violations),
    }
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = cache_path.with_name(f"{cache_path.name}.{os.getpid()}.tmp")
        temp_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temp_path, cache_path)
    except OSError:
        return


def scan_no_runtime_artifacts_with_run_cache(
    root: pathlib.Path,
    options,
) -> list[str]:
    scanner = _no_runtime_scanner_module()
    resolved_root = root.resolve()
    cache_path = _no_runtime_scan_cache_path(resolved_root)
    if cache_path is None:
        return scanner.scan_repository(resolved_root, options)

    _validate_no_runtime_scan_cache_path(resolved_root, cache_path)
    fingerprint = _no_runtime_scan_fingerprint(resolved_root, options)
    cached_violations = _load_no_runtime_scan_cache(cache_path, fingerprint)
    if cached_violations is not None:
        return cached_violations

    violations = scanner.scan_repository(resolved_root, options)
    _write_no_runtime_scan_cache(cache_path, fingerprint, violations)
    return violations


def _is_no_runtime_scan_command(command: Sequence[str]) -> bool:
    return any(
        pathlib.PurePath(str(part)).name == "validate_no_runtime_artifacts.py"
        for part in command
    )


def _no_runtime_options_from_command(command: Sequence[str]):
    scanner = _no_runtime_scanner_module()
    flags = {str(part) for part in command}
    return scanner.ScanOptions(
        forbid_source_retrieval="--forbid-source-retrieval" in flags,
        forbid_source_acceptance="--forbid-source-acceptance" in flags,
        forbid_connector_binding="--forbid-connector-binding" in flags,
        forbid_private_state_fetch="--forbid-private-state-fetch" in flags,
        forbid_order_execution="--forbid-order-execution" in flags,
        forbid_neural_training="--forbid-neural-training" in flags,
        forbid_neural_inference="--forbid-neural-inference" in flags,
        forbid_external_repo_clone="--forbid-external-repo-clone" in flags,
        forbid_package_install_scripts="--forbid-package-install-scripts" in flags,
    )


def _no_runtime_root_from_command(
    command: Sequence[str],
    fallback_root: pathlib.Path | None,
) -> pathlib.Path:
    root = pathlib.Path(".")
    command_parts = [str(part) for part in command]
    if "--repo-root" in command_parts:
        index = command_parts.index("--repo-root")
        if index + 1 < len(command_parts):
            root = pathlib.Path(command_parts[index + 1])
    if not root.is_absolute():
        root = (fallback_root or pathlib.Path.cwd()) / root
    return root.resolve()


def _record_no_runtime_scan_success(
    command: Sequence[str],
    repo_root: pathlib.Path | None,
) -> None:
    if not os.environ.get(NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV):
        return
    if not _is_no_runtime_scan_command(command):
        return
    root = _no_runtime_root_from_command(command, repo_root)
    cache_path = _no_runtime_scan_cache_path(root)
    if cache_path is None:
        return
    _validate_no_runtime_scan_cache_path(root, cache_path)
    options = _no_runtime_options_from_command(command)
    fingerprint = _no_runtime_scan_fingerprint(root, options)
    _write_no_runtime_scan_cache(cache_path, fingerprint, [])


def _validate_run_local_cache_path(
    root: pathlib.Path,
    cache_path: pathlib.Path,
    env_name: str,
) -> None:
    if not _path_is_relative_to(cache_path, root):
        return
    rel = cache_path.relative_to(root)
    if rel.parts and rel.parts[0] == ".tmp":
        return
    raise RuntimeError(
        f"{env_name} must point outside the repo or under .tmp: {rel.as_posix()}"
    )


def _pr152_build_report_cache_path(root: pathlib.Path) -> pathlib.Path | None:
    cache_text = os.environ.get(PR152_BUILD_REPORT_CACHE_ENV)
    if not cache_text:
        return None
    cache_path = pathlib.Path(cache_text)
    if not cache_path.is_absolute():
        cache_path = root / cache_path
    return cache_path.resolve()


def _pr152_report_source_digest() -> str:
    from src.qtt.stage1_prediction_markets.grand_global_debug_logical_consistency_audit import (  # noqa: E501
        constants,
        report,
    )

    hasher = hashlib.sha256()
    for path in (
        pathlib.Path(report.__file__),
        pathlib.Path(constants.__file__),
        pathlib.Path(__file__),
    ):
        hasher.update(path.name.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")
    return hasher.hexdigest()


def _git_stdout_or_empty(
    repo_root: pathlib.Path,
    args: Sequence[str],
) -> tuple[int, str]:
    returncode, stdout, _stderr = _git_stdout(repo_root, args)
    return returncode, stdout if returncode == 0 else ""


def _status_paths_from_porcelain(status_stdout: str) -> tuple[tuple[str, str], ...]:
    records = [record for record in status_stdout.split("\0") if record]
    parsed: list[tuple[str, str]] = []
    index = 0
    while index < len(records):
        record = records[index]
        code = record[:2]
        path = record[3:] if len(record) > 3 and record[2] == " " else record[2:].strip()
        if path:
            parsed.append((code, path.replace("\\", "/")))
        index += 2 if code[:1] in {"R", "C"} or code[1:] in {"R", "C"} else 1
    return tuple(sorted(parsed, key=lambda item: (item[1].casefold(), item[1], item[0])))


def _dirty_path_fingerprints(
    root: pathlib.Path,
    status_stdout: str,
) -> tuple[dict[str, object], ...]:
    fingerprints: list[dict[str, object]] = []
    for code, rel_path in _status_paths_from_porcelain(status_stdout):
        path = root / rel_path
        entry: dict[str, object] = {"code": code, "path": rel_path}
        try:
            stat = path.stat()
        except OSError as exc:
            entry["error"] = exc.__class__.__name__
            fingerprints.append(entry)
            continue
        entry["mtime_ns"] = stat.st_mtime_ns
        entry["size"] = stat.st_size
        if path.is_file() and not code.startswith("??"):
            try:
                entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError as exc:
                entry["error"] = exc.__class__.__name__
        fingerprints.append(entry)
    return tuple(fingerprints)


def _path_traversal_cache_fingerprint(root: pathlib.Path) -> dict[str, object]:
    hasher = hashlib.sha256()
    count = 0
    if root.exists():
        for path in sorted(
            root.rglob("*"),
            key=lambda item: str(item.relative_to(root)).replace("\\", "/").casefold(),
        ):
            rel_path = str(path.relative_to(root)).replace("\\", "/")
            if rel_path == ".tmp" or rel_path.startswith(".tmp/"):
                continue
            try:
                stat = path.stat()
            except OSError as exc:
                entry = {"error": exc.__class__.__name__, "path": rel_path}
            else:
                entry = {
                    "is_file": path.is_file(),
                    "mtime_ns": stat.st_mtime_ns,
                    "path": rel_path,
                    "size": stat.st_size,
                }
            hasher.update(_json_cache_bytes(entry))
            hasher.update(b"\n")
            count += 1
    return {"path_count": count, "paths_digest": hasher.hexdigest()}


def _pr152_build_report_fingerprint(root: pathlib.Path) -> dict[str, object]:
    ls_returncode, ls_stdout = _git_stdout_or_empty(root, ["ls-files", "-s", "-z"])
    status_returncode, status_stdout = _git_stdout_or_empty(
        root,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
    )
    branch_returncode, branch_stdout = _git_stdout_or_empty(
        root,
        ["branch", "--show-current"],
    )
    if ls_returncode != 0:
        fallback = _path_traversal_cache_fingerprint(root)
    else:
        fallback = {"path_count": None, "paths_digest": ""}
    return {
        "branch": branch_stdout.strip() if branch_returncode == 0 else "",
        "cache_kind": PR152_BUILD_REPORT_CACHE_KIND,
        "dirty_paths": list(_dirty_path_fingerprints(root, status_stdout)),
        "fallback": fallback,
        "git_ls_files_s_z": ls_stdout,
        "git_status_porcelain_z": status_stdout,
        "repo_root": str(root),
        "schema_version": PR152_BUILD_REPORT_CACHE_SCHEMA_VERSION,
        "source_digest": _pr152_report_source_digest(),
    }


def _load_pr152_build_report_cache(
    cache_path: pathlib.Path,
    fingerprint: dict[str, object],
) -> dict[str, object] | None:
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("schema_version") != PR152_BUILD_REPORT_CACHE_SCHEMA_VERSION:
        return None
    if payload.get("cache_kind") != PR152_BUILD_REPORT_CACHE_KIND:
        return None
    if payload.get("fingerprint") != fingerprint:
        return None
    report = payload.get("report")
    if not isinstance(report, dict):
        return None
    return deepcopy(report)


def _write_pr152_build_report_cache(
    cache_path: pathlib.Path,
    fingerprint: dict[str, object],
    report: dict[str, object],
) -> None:
    payload = {
        "cache_kind": PR152_BUILD_REPORT_CACHE_KIND,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "fingerprint": fingerprint,
        "report": report,
        "schema_version": PR152_BUILD_REPORT_CACHE_SCHEMA_VERSION,
    }
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = cache_path.with_name(f"{cache_path.name}.{os.getpid()}.tmp")
        temp_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temp_path, cache_path)
    except OSError:
        return


def build_pr152_report_with_run_cache(
    repo_root: pathlib.Path | str,
    builder,
) -> dict[str, object]:
    root = pathlib.Path(repo_root).resolve()
    cache_path = _pr152_build_report_cache_path(root)
    if cache_path is None:
        return builder(root)
    _validate_run_local_cache_path(root, cache_path, PR152_BUILD_REPORT_CACHE_ENV)
    fingerprint = _pr152_build_report_fingerprint(root)
    fingerprint_key = hashlib.sha256(_json_cache_bytes(fingerprint)).hexdigest()
    memory_key = (str(cache_path), fingerprint_key)

    if memory_key in _PR152_BUILD_REPORT_MEMORY_CACHE:
        return deepcopy(_PR152_BUILD_REPORT_MEMORY_CACHE[memory_key])
    cached_report = _load_pr152_build_report_cache(cache_path, fingerprint)
    if cached_report is not None:
        _PR152_BUILD_REPORT_MEMORY_CACHE[memory_key] = deepcopy(cached_report)
        return deepcopy(cached_report)

    report = builder(root)
    if not isinstance(report, dict):
        raise RuntimeError("PR152 build_report cache builder returned a non-dict payload")
    _write_pr152_build_report_cache(cache_path, fingerprint, report)
    _PR152_BUILD_REPORT_MEMORY_CACHE[memory_key] = deepcopy(report)
    return deepcopy(report)


def _tracked_modified_paths(repo_root: pathlib.Path) -> set[str]:
    returncode, stdout, stderr = _git_stdout(repo_root, ["ls-files", "-m"])
    if returncode != 0:
        detail = stderr.strip() or stdout.strip() or "git ls-files -m failed"
        raise RuntimeError(detail)
    return {
        path.strip().replace("\\", "/")
        for path in stdout.splitlines()
        if path.strip()
    }


def _modified_file_snapshots(
    repo_root: pathlib.Path,
    paths: set[str],
) -> dict[str, bytes | None]:
    snapshots: dict[str, bytes | None] = {}
    for path_text in sorted(paths):
        path = repo_root / path_text
        snapshots[path_text] = path.read_bytes() if path.exists() else None
    return snapshots


def _restore_modified_file_snapshots(
    repo_root: pathlib.Path,
    snapshots: dict[str, bytes | None],
) -> tuple[str, ...]:
    restored: list[str] = []
    for path_text, content in sorted(snapshots.items()):
        path = repo_root / path_text
        if content is None:
            if path.exists() and path.is_file():
                path.unlink()
                restored.append(path_text)
            continue
        if path.exists() and path.read_bytes() == content:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        restored.append(path_text)
    return tuple(restored)


def _restore_tracked_gate_side_effects(
    repo_root: pathlib.Path,
    initially_modified_paths: set[str],
) -> tuple[str, ...]:
    restore_paths = sorted(_tracked_modified_paths(repo_root) - initially_modified_paths)
    if not restore_paths:
        return ()

    returncode, stdout, stderr = _git_stdout(
        repo_root,
        [
            "restore",
            "--source=HEAD",
            "--worktree",
            "--",
            *restore_paths,
        ],
    )
    if returncode != 0:
        detail = stderr.strip() or stdout.strip() or "git restore failed"
        raise RuntimeError(detail)
    return tuple(restore_paths)


def build_validation_commands(
    validation_dir: pathlib.Path | str | None = None,
    pytest_basetemp: pathlib.Path | str | None = None,
) -> list[list[str]]:
    validation_dir = (
        _default_validation_dir()
        if validation_dir is None
        else pathlib.Path(validation_dir)
    )
    pytest_basetemp = (
        _default_pytest_basetemp()
        if pytest_basetemp is None
        else pathlib.Path(pytest_basetemp)
    )
    section_manifest = validation_dir / "SectionManifest.json"
    traceability_report = validation_dir / "TraceabilityReport.json"
    first_pr_scope_report = validation_dir / "FirstPrScopeReport.json"
    row_family_currentization_report = (
        validation_dir / "AtomicRowsRowFamilySourceManifestCurrentization.report.json"
    )
    master_plan = pathlib.Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"

    commands = [
        [
            sys.executable,
            _path("tools", "master_plan_ingest.py"),
            "--input",
            str(master_plan),
            "--section-manifest-out",
            str(section_manifest),
            "--traceability-out",
            str(traceability_report),
            "--scope-report-out",
            str(first_pr_scope_report),
        ],
        [
            sys.executable,
            _path("tools", "master_plan_traceability_check.py"),
            "--master-plan",
            str(master_plan),
            "--section-manifest",
            str(section_manifest),
            "--traceability-report",
            str(traceability_report),
        ],
        [
            sys.executable,
            _path("tools", "validate_first_pr_scope.py"),
            "--repo-root",
            ".",
            "--scope-report",
            str(first_pr_scope_report),
            "--block-runtime",
            "--block-live",
            "--block-sha",
            "--block-companion-package",
            "--block-profit-claims",
            "--block-source-retrieval",
            "--block-source-acceptance",
            "--block-connector-binding",
            "--block-private-state-fetch",
            "--block-order-execution",
            "--block-neural-training",
            "--block-neural-inference",
            "--block-external-repo-clone",
            "--block-package-install-scripts",
        ],
        [
            sys.executable,
            "-c",
            PR138_NON_MUTATING_VALIDATION_SCRIPT,
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_row_family_source_manifest_currentization.py",
            ),
            "--repo-root",
            ".",
            "--out",
            str(row_family_currentization_report),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_semantic_field_coverage_enrichment_plan.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_idempotence_runtime_containment.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_owner_global_override_authority.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "QTTOwnerGlobalOverrideAuthority.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_semantic_value_materialization_implementation_bridge.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_source_backed_classical_quantum_parameter_default_target_matrix.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_official_source_retrieval_target_pack_parameter_defaults.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_grand_global_debug_logical_consistency_audit.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_controlled_official_source_capture_candidate_packets.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr153r_redo_external_source_value_capture_targets.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr153s_source_value_capture_closure_classifier.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_default_value_materialization_gate.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_agent_consumable_parameter_default_registry.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_agent_default_binding_universal_intake_gate.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr157_pr154_atomicrows_completion_materialization_bridge.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr158_owner_response_selection_readiness_bridge.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr159_official_source_completion_bridge.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr160_split_reclassification_route_closure.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr159r_source_locator_value_capture.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr159s_open_intake_completion.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr161a_atomicrows_pr154_value_state_materialization.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr161b_master_plan_residual_candidate_coverage.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr161c_qku_residual_candidate_assimilation.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr161e_replay_paper_outcome_capture_scenario_learning.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr161f_replay_paper_executor_input_run_artifact_generation.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162r_a_replay_paper_executability_classification_audit.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162d_r2a_real_formulations.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162r_generic_replay_paper_adapter_rerun.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162r_b_replay_paper_data_binding_completion.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr163_generic_paper_adapter_capture_framework.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr163_b_paired_replay_paper_concurrent_executor.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr164_review_provenance_qku_canonical_coverage_audit.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr163_c_pretrade_infrastructure_rejection_remediation.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr165_evidence_backed_scoring_ranking.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr165_b_condition_scoped_negative_memory.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr165_c_replay_paper_memory_consumer_integration.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr165_d_scenario_qku_combination_selection.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr166_s_replay_paper_scenario_retest_execution.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr166_sf_repair_materialization_before_retest.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr166_s2_replay_paper_retest_loop_v2.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr166_sm2_score_memory_refresh_v2.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr166_sf_r2_targeted_conversion_repair_retest.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr166_sm3_score_memory_refresh_v3.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr166_q_quantum_classical_hybrid_comparator.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr166_qb_bounded_quantum_benchmark.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr166_qc_quantum_selected_replay_paper_retest.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162e_q_quantum_automapper.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr167_open_trade_simulator_integration.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162e_plugin_framework.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162e_negative_repair_factory.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr162e_no_orphan_lineage.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "build_pr168_gfp_global_formula_discovery_real_computation.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_baseline_count_reconcile.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_no_fake_positive_negative_labels.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_formula_assignment_coverage.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_real_formula_computation.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_formula_registry_integrity.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_atomicrows_computation_coverage.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_qku_computation_coverage.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_candidate_packet_v1_coverage.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_quantum_objective_coefficients.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_metadata_placeholder_demotions.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_truth_overlay_required.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_report_compactness.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_formula_source_arbitration.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_master_plan_formula_catalog_diff.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_minimum_tradability_formula_set.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_forbidden_bundle_terminology.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_no_orphan_lineage.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr168_gfp_authority_boundaries.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "build_pr168_rp_formula_based_replay_paper_recompute.py",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_authority_reason_code_registry.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_formula_execution.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_replay_paper_results.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_no_fake_computed_labels.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_tca_pnl_math.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_microstructure_fill_model.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_pretrade_simulation_kernel.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_order_policy_candidate_ranking.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_no_trade_candidate.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_scenario_ladder.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_latency_budget.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_live_candidate_handoff_no_order_authority.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_probability_calibration.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_overfit_fdr.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_quantum_objective_recompute.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_quantum_structural_readiness.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_portfolio_marginal_utility.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_capacity_crowding.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_regime_memory.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_champion_challenger.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_combination_selection.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_negative_recovery.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_edge_attribution.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_agent_duty_orchestration.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_connector_candidate_routing.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_strict_input_consumption.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_no_orphan_lineage.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_artifact_information_value_dag.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_authority_boundaries.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_report_compactness.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_validation_scope_registry_integration.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_windows_linux_compatibility.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_no_metadata_only_pass.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_no_forced_negative_to_positive.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_pr168_rp_no_scattered_authority_wording.py"),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr165_d2_score_refreshed_scenario_selection_v2.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_pr165_d3_quantum_aware_scenario_selection_v3.py",
            ),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_agent_role_operating_charter_registry.py",
            ),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "QTTAgentRoleOperatingCharterReport.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_algorithm_formula_family_registry.py",
            ),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "QTTAlgorithmFormulaFamilyReport.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_agent_algorithm_binding_registry.py",
            ),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "QTTAgentAlgorithmBindingReport.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_agent_algorithm_consumer_gate.py",
            ),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "QTTAgentAlgorithmConsumerGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_agent_algorithm_cumulative_readiness_gate.py",
            ),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "QTTAgentAlgorithmCumulativeReadinessGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_agent_algorithm_command_matrix.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_source_evidence_static.py"),
            "--schema",
            _path("schemas", "source_evidence", "source_evidence.schema.json"),
            "--owner-packet",
            _path(
                "docs",
                "master_plan",
                "source_evidence",
                "QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
            ),
            "--registry-fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "synthetic_acceptance_registry.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_source_evidence_gate_confirmation_static.py"),
            "--repo-root",
            ".",
            "--schema",
            _path(
                "schemas",
                "source_evidence",
                "source_evidence_gate_confirmation.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "synthetic_source_evidence_gate_confirmation_blocked.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_source_evidence_retrieval_executor.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_source_evidence_acceptance.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_accepted_source_to_connector_semantic_binding.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_source_revalidation_scheduler.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_connector_semantic_binding_implementation_gate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_per_venue_execution_lifecycle_model.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_cross_venue_execution_normalization_binding.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "runtime_cash_component_field_map_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "private_state_read_receipt_gate_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "credential_alias_secret_no_capture_readiness_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "venue_market_data_ingest_adapters_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "orderbook_event_state_snapshot_builder_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "runtime_resolver_snapshot_executor_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_historical_dataset_policy_literal_drift.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_historical_dataset_digest_and_loader.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_pr136_roadmap_policy_literal_drift.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_pr136_day1_launch_readiness_roadmap.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_pr137_generated_integrity_authority_boundary.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_pr137_launch_readiness_dependency_controller.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_connector_capability_static.py"),
            "--schema",
            _path("schemas", "connectors", "connector_capability_registry.schema.json"),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "connectors",
                "synthetic_connector_capability_registry.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_runtime_orchestration_static.py"),
            "--schema",
            _path(
                "schemas",
                "runtime_orchestration",
                "runtime_orchestration_skeleton.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "runtime_orchestration",
                "synthetic_runtime_orchestration_skeleton.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_replay_paper_execution_graph_static.py"),
            "--schema",
            _path(
                "schemas",
                "replay_paper_review",
                "replay_paper_execution_graph.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "replay_paper_review",
                "synthetic_replay_paper_execution_graph.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_venue_abstraction_layer_static.py"),
            "--schema",
            _path("schemas", "connectors", "venue_abstraction_layer.schema.json"),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "connectors",
                "synthetic_venue_abstraction_layer.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_order_intent_execution_router_static.py"),
            "--schema",
            _path(
                "schemas",
                "connectors",
                "order_intent_execution_router_scaffolding.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "connectors",
                "synthetic_order_intent_execution_router_scaffolding.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_readiness_static.py"),
            "--repo-root",
            ".",
            "--schema",
            _path("schemas", "atomicrows", "atomicrows_readiness_audit.schema.json"),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "atomicrows",
                "synthetic_atomicrows_readiness_blocked.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_unblocking_requirements_static.py"),
            "--repo-root",
            ".",
            "--schema",
            _path(
                "schemas",
                "atomicrows",
                "atomicrows_unblocking_requirements_audit.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "atomicrows",
                "synthetic_atomicrows_unblocking_requirements_required.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_canonical_row_specification_static.py"),
            "--repo-root",
            ".",
            "--schema",
            _path(
                "schemas",
                "atomicrows",
                "atomicrows_canonical_row_specification_audit.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "atomicrows",
                "synthetic_atomicrows_canonical_row_specification_required.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_bundle_schema_checker_static.py"),
            "--repo-root",
            ".",
            "--row-schema",
            _path("schemas", "atomicrows", "atomic_parameter_row.schema.json"),
            "--bundle-schema",
            _path("schemas", "atomicrows", "atomic_row_bundle.schema.json"),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "atomicrows",
                "synthetic_atomicrows_bundle_bootstrap_absent.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "build_atomicrows_parameter_lifecycle_report.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_parameter_lifecycle.py"),
            "--mode",
            "dev",
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_lifecycle_consumer_gate.py"),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsLifecycleConsumerGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_lifecycle_promotion_receipt_gate.py"),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsLifecyclePromotionReceiptGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_lifecycle_registry_mutation_guard.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsLifecycleRegistryMutationGuard.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_lifecycle_cumulative_readiness_gate.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsLifecycleCumulativeReadinessGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_lifecycle_gate_command_matrix.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsLifecycleGateCommandMatrix.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_agent_binding_registry.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsParameterAgentBindingReport.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_agent_binding_consumer_gate.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsParameterAgentBindingConsumerGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_agent_binding_command_matrix.py",
            ),
            "--mode",
            "dev",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "AtomicRowsParameterAgentBindingCommandMatrix.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_research_provenance_evidence_tier_classification.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_research_source_to_candidate_family_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_stack_role_taxonomy.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_stack_completeness_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_stack_compatibility_gate.py",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_edge_parameter_stack_selection_packet.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_trade_context_packet.py"),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_selection_universe_registry.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_parameter_selection_universe_consumer_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_trade_context_selection_universe_routing_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_quantum_applicability_classification_registry.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_owner_quantum_priority_policy_registry.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_parameter_algorithm_scoring_policy_registry.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_parameter_stack_scoring_and_ranking_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_quantum_classical_optimizer_arbitration_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_candidate_parameter_stack_generation_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_trade_context_parameter_stack_selection_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_selected_parameter_stack_handoff_packet.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_replay_paper_candidate_stack_competition_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_dual_result_review_for_parameter_stacks.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_owner_live_promotion_review_for_parameter_stacks.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_owner_approval_request_queue_registry.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_owner_override_receipt_authoring_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_owner_dashboard_approval_menu_schema.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_owner_dashboard_approval_static_screen_contract.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_full_bundle_row_expansion_plan.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_bundle_row_family_source_files.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_sha_system_dormancy_state_contract.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_final_readiness_dependency_policy_contract.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_pr_identity_roster.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_roadmap_execution_state_controller.py"),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_bundle_sha_freeze_authority_gate.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_exact_row_authority_classifier_bridge.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_exact_row_expansion_manifest.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_exact_row_generator_dry_run_manifest.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_exact_row_source_materialization_manifest.py",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_bundle_materialization_manifest.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_atomicrows_bundle_boundary_state_contract.py"),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_atomicrows_sha_freeze_final_readiness_state_contract.py",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_generated_derivative_bootstrap_gate_static.py"),
            "--repo-root",
            ".",
            "--schema",
            _path(
                "schemas",
                "master_plan",
                "generated_derivative_bootstrap_gate.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "master_plan",
                "synthetic_generated_derivative_bootstrap_gate.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_stage1_packet_schema_gate_static.py"),
            "--repo-root",
            ".",
            "--schema-dir",
            _path("schemas", "stage1_prediction_markets"),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "stage1_prediction_markets",
                "synthetic_stage1_packet_schema_gate_blocked.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_venue_neutral_prediction_adapter_gate_static.py"),
            "--repo-root",
            ".",
            "--schema-dir",
            _path("schemas", "venue_neutral_prediction_adapter"),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "venue_neutral_prediction_adapter",
                "synthetic_venue_neutral_prediction_adapter_gate_blocked.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_connector_scaffold_source_required_gate_static.py",
            ),
            "--repo-root",
            ".",
            "--schema",
            _path(
                "schemas",
                "connectors",
                "connector_scaffold_source_required_gate.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "connectors",
                "synthetic_connector_scaffold_source_required_blocked.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_stage1_runtime_scaffold_gate_static.py"),
            "--repo-root",
            ".",
            "--schema",
            _path(
                "schemas",
                "runtime_orchestration",
                "stage1_runtime_scaffold_gate.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "runtime_orchestration",
                "synthetic_stage1_runtime_scaffold_gate_blocked.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "validate_source_fact_binding_connector_semantic_readiness_static.py",
            ),
            "--repo-root",
            ".",
            "--source-to-connector-schema",
            _path(
                "schemas",
                "source_fact_binding_readiness",
                "stage1_source_to_connector_field_binding_matrix.schema.json",
            ),
            "--source-to-connector-fixture",
            _path(
                "tests",
                "fixtures",
                "source_fact_binding_readiness",
                "synthetic_stage1_source_to_connector_field_binding_matrix.v1.fixture.json",
            ),
            "--connector-target-schema",
            _path(
                "schemas",
                "source_fact_binding_readiness",
                "stage1_connector_semantic_target_field_matrix.schema.json",
            ),
            "--connector-target-fixture",
            _path(
                "tests",
                "fixtures",
                "source_fact_binding_readiness",
                "synthetic_stage1_connector_semantic_target_field_matrix.v1.fixture.json",
            ),
            "--gate-report-schema",
            _path(
                "schemas",
                "source_fact_binding_readiness",
                "stage1_connector_semantic_readiness_gate_report.schema.json",
            ),
            "--gate-report-fixture",
            _path(
                "tests",
                "fixtures",
                "source_fact_binding_readiness",
                "synthetic_stage1_connector_semantic_readiness_gate_report.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "source_evidence_acceptance_consumer_contract_check.py"),
            "--repo-root",
            ".",
            "--consumer-contract-schema",
            _path(
                "src",
                "qtt",
                "source_evidence",
                "acceptance",
                "accepted_source_evidence_consumer_contract.schema.json",
            ),
            "--target-field-ledger-schema",
            _path(
                "src",
                "qtt",
                "source_evidence",
                "acceptance",
                "stage1_target_field_acceptance_ledger_record.schema.json",
            ),
            "--export-record-schema",
            _path(
                "src",
                "qtt",
                "source_evidence",
                "acceptance",
                "stage1_accepted_source_evidence_export_record.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "acceptance_consumer_contract",
                "synthetic_accepted_source_evidence_consumer_contract_records.v1.fixture.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "stage1_connector_semantic_binding_ledger_check.py"),
            "--repo-root",
            ".",
            "--ledger-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "connector_semantic_binding",
                "stage1_connector_semantic_binding_ledger_record.schema.json",
            ),
            "--canonicalization-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "connector_semantic_binding",
                "stage1_connector_semantic_value_canonicalization.schema.json",
            ),
            "--consumer-contract-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "connector_semantic_binding",
                "stage1_connector_semantic_binding_consumer_contract.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "connector_semantic_binding",
                "synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1ConnectorSemanticBindingLedgerCheck.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "stage1_runtime_resolver_snapshot_contract_check.py"),
            "--repo-root",
            ".",
            "--input-lock-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver",
                "stage1_runtime_resolver_snapshot_input_lock.schema.json",
            ),
            "--manifest-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver",
                "stage1_runtime_resolver_snapshot_manifest.schema.json",
            ),
            "--consumer-contract-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver",
                "stage1_runtime_resolver_consumer_contract.schema.json",
            ),
            "--gate-report-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver",
                "stage1_runtime_resolver_snapshot_gate_report.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "runtime_resolver",
                "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1RuntimeResolverSnapshotContractCheck.report.json",
            ),
        ],
        [
            sys.executable,
            _path(
                "tools",
                "stage1_runtime_resolver_to_replay_paper_handoff_check.py",
            ),
            "--repo-root",
            ".",
            "--consumer-allowlist-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver_snapshot",
                "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json",
            ),
            "--handoff-contract-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver_snapshot",
                "stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json",
            ),
            "--handoff-report-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "runtime_resolver_snapshot",
                "stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "runtime_resolver_snapshot",
                "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1RuntimeResolverToReplayPaperHandoff.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "stage1_concurrent_replay_paper_contract_check.py"),
            "--repo-root",
            ".",
            "--input-identity-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "replay_paper",
                "concurrent_replay_paper_input_identity.schema.json",
            ),
            "--replay-lane-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "replay_paper",
                "concurrent_replay_lane_contract.schema.json",
            ),
            "--paper-lane-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "replay_paper",
                "concurrent_paper_lane_contract.schema.json",
            ),
            "--replay-result-boundary-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "replay_paper",
                "replay_result_packet_boundary.schema.json",
            ),
            "--paper-result-boundary-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "replay_paper",
                "paper_result_packet_boundary.schema.json",
            ),
            "--gate-report-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "replay_paper",
                "concurrent_replay_paper_execution_gate_report.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "replay_paper",
                "synthetic_concurrent_replay_paper_contracts.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1ConcurrentReplayPaperContractCheck.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "stage1_dual_result_review_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "dual_result_review",
                "stage1_dual_result_review_input_contract.schema.json",
            ),
            "--comparison-matrix-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "dual_result_review",
                "stage1_replay_paper_comparison_matrix.schema.json",
            ),
            "--gate-report-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "dual_result_review",
                "stage1_dual_result_review_gate_report.schema.json",
            ),
            "--owner-handoff-block-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "dual_result_review",
                "stage1_owner_live_promotion_handoff_block.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "dual_result_review",
                "synthetic_stage1_dual_result_review_contracts.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1DualResultReviewContractCheck.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "stage1_owner_live_promotion_review_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "owner_live_promotion_review",
                "stage1_owner_live_promotion_review_input_contract.schema.json",
            ),
            "--owner-approval-receipt-boundary-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "owner_live_promotion_review",
                "stage1_owner_approval_receipt_boundary.schema.json",
            ),
            "--gate-report-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "owner_live_promotion_review",
                "stage1_owner_live_promotion_review_gate_report.schema.json",
            ),
            "--handoff-block-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "owner_live_promotion_review",
                "stage1_three_venue_canary_eligibility_handoff_block.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "owner_live_promotion_review",
                "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1OwnerLivePromotionReviewContractCheck.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "stage1_three_venue_canary_eligibility_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "three_venue_canary_eligibility",
                "stage1_three_venue_canary_eligibility_input_contract.schema.json",
            ),
            "--readiness-matrix-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "three_venue_canary_eligibility",
                "stage1_three_venue_platform_readiness_matrix.schema.json",
            ),
            "--handoff-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "three_venue_canary_eligibility",
                "stage1_owner_review_to_canary_eligibility_handoff.schema.json",
            ),
            "--gate-report-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "three_venue_canary_eligibility",
                "stage1_three_venue_canary_eligibility_gate_report.schema.json",
            ),
            "--execution-block-schema",
            _path(
                "src",
                "qtt",
                "stage1_prediction_markets",
                "three_venue_canary_eligibility",
                "stage1_limited_live_canary_execution_block.schema.json",
            ),
            "--fixture",
            _path(
                "tests",
                "fixtures",
                "source_evidence",
                "three_venue_canary_eligibility",
                "synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json",
            ),
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "Stage1ThreeVenueCanaryEligibilityContractCheck.report.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "build_master_plan_section_coverage_report.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_master_plan_section_coverage.py"),
            "--mode",
            "dev",
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_master_plan_section_coverage_triage_routes.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_master_plan_section_roadmap_crosswalk.py"),
        ],
        [
            sys.executable,
            _path("tools", "validate_qtt_master_plan_section_coverage_command_matrix.py"),
        ],
        [
            sys.executable,
            _path("tools", "qtt_test_gate.py"),
            "--phase",
            "first-coding-runbook",
            "--repo-root",
            ".",
            "--strict-no-claim",
            "--out",
            _path("docs", "master_plan", "generated", "QTTTestGate.report.json"),
        ],
        [
            sys.executable,
            _path("tools", "local_gate_command_matrix.py"),
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "LocalGateCommandMatrix.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "pr_handoff_check.py"),
            "--repo-root",
            ".",
            "--out",
            _path(
                "docs",
                "master_plan",
                "generated",
                "FirstCodingPRHandoff.packet.json",
            ),
        ],
        [
            sys.executable,
            _path("tools", "validate_no_runtime_artifacts.py"),
            "--repo-root",
            ".",
            "--forbid-source-retrieval",
            "--forbid-source-acceptance",
            "--forbid-connector-binding",
            "--forbid-private-state-fetch",
            "--forbid-order-execution",
            "--forbid-neural-training",
            "--forbid-neural-inference",
            "--forbid-external-repo-clone",
            "--forbid-package-install-scripts",
        ],
        [
            sys.executable,
            _path("tools", "run_pytest_fresh_basetemp.py"),
            _path(
                "tests",
                "source_evidence",
                "test_controlled_official_source_capture_candidate_packets.py",
            ),
            "-q",
            PYTEST_DURATIONS_ARG,
            "--basetemp",
            str(pytest_basetemp),
        ],
        [
            sys.executable,
            _path("tools", "run_pytest_fresh_basetemp.py"),
            "tests",
            "-q",
            "--ignore",
            _path(
                "tests",
                "source_evidence",
                "test_controlled_official_source_capture_candidate_packets.py",
            ),
            PYTEST_DURATIONS_ARG,
            "--basetemp",
            str(pytest_basetemp),
        ],
    ]
    return [
        _route_command_generated_outputs_to_temp(command, pathlib.Path(validation_dir))
        for command in commands
    ]


def build_fast_preflight_commands() -> list[list[str]]:
    return [
        [
            sys.executable,
            _path("tools", "validate_grand_global_debug_logical_consistency_audit.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_ci_branch_context_matrix.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_repair_pr_changed_file_scope.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_nested_validator_contracts.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_validation_inventory.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "validate_validation_scope_registry.py"),
        ],
        [
            sys.executable,
            _path("tools", "changed_area_validation_router.py"),
            "--repo-root",
            ".",
        ],
        [
            sys.executable,
            _path("tools", "cross_platform_path_invariant.py"),
            "--repo-root",
            ".",
        ],
    ]


def build_deterministic_validator_commands(
    validation_dir: pathlib.Path | str | None = None,
    pytest_basetemp: pathlib.Path | str | None = None,
) -> list[list[str]]:
    return [
        command
        for command in build_validation_commands(validation_dir, pytest_basetemp)
        if not _command_uses_pytest_helper(command)
        and _command_script_name(command) not in FAST_PREFLIGHT_SCRIPT_NAMES
    ]


def _build_pytest_command(
    command: PytestShardCommand,
    pytest_basetemp: pathlib.Path,
) -> list[str]:
    built = [
        sys.executable,
        _path("tools", PYTEST_FRESH_BASETEMP_SCRIPT),
        *command.paths,
        "-q",
    ]
    for ignored in command.ignores:
        built.extend(["--ignore", ignored])
    built.extend([PYTEST_DURATIONS_ARG, "--basetemp", str(pytest_basetemp)])
    return built


def build_pytest_shard_commands(
    phase: str,
    pytest_basetemp: pathlib.Path | str | None = None,
) -> list[list[str]]:
    if phase not in PYTEST_SHARD_COMMANDS:
        raise ValueError(f"unknown pytest shard phase: {phase}")
    basetemp = (
        _default_pytest_basetemp()
        if pytest_basetemp is None
        else pathlib.Path(pytest_basetemp)
    )
    return [_build_pytest_command(command, basetemp) for command in PYTEST_SHARD_COMMANDS[phase]]


def build_post_validation_commands() -> list[list[str]]:
    return [
        [sys.executable, "-m", "compileall", "-q", "tools", "tests", "src"],
        ["git", "diff", "--check"],
        [
            "git",
            "diff",
            "--exit-code",
            "--",
            _path("docs", "master_plan", "QTT_MasterPlan_Current.md"),
        ],
        [sys.executable, "-c", ATOMICROWS_BUNDLE_CHECK_SCRIPT],
    ]


def build_phase_commands(
    phase: str = ALL_PHASE,
    validation_dir: pathlib.Path | str | None = None,
    pytest_basetemp: pathlib.Path | str | None = None,
) -> list[list[str]]:
    if phase == ALL_PHASE:
        commands: list[list[str]] = []
        for ordered_phase in ORDERED_PHASES:
            commands.extend(
                build_phase_commands(
                    ordered_phase,
                    validation_dir=validation_dir,
                    pytest_basetemp=pytest_basetemp,
                )
            )
        return commands
    if phase == FAST_PREFLIGHT_PHASE:
        return build_fast_preflight_commands()
    if phase == DETERMINISTIC_VALIDATORS_PHASE:
        return build_deterministic_validator_commands(validation_dir, pytest_basetemp)
    if phase in PYTEST_SHARD_PHASES:
        return build_pytest_shard_commands(phase, pytest_basetemp)
    if phase == POST_VALIDATION_PHASE:
        return build_post_validation_commands()
    raise ValueError(f"unknown validation phase: {phase}")


def build_phase_manifest(
    validation_dir: pathlib.Path | str | None = None,
    pytest_basetemp: pathlib.Path | str | None = None,
) -> list[dict[str, object]]:
    manifest: list[dict[str, object]] = []
    for phase in ORDERED_PHASES:
        commands = build_phase_commands(
            phase,
            validation_dir=validation_dir,
            pytest_basetemp=pytest_basetemp,
        )
        manifest.append(
            {
                "phase": phase,
                "command_count": len(commands),
                "commands": [list(command) for command in commands],
            }
        )
    return manifest


def _timing_entry_payload(entry: TimingEntry) -> dict[str, object]:
    return {
        "phase": entry.phase,
        "command_index": entry.command_index,
        "command": entry.command,
        "elapsed_seconds": entry.elapsed_seconds,
        "returncode": entry.returncode,
    }


def _pytest_path_args(command: Sequence[str]) -> tuple[str, ...]:
    path_args: list[str] = []
    skip_next = False
    for part in command[2:]:
        if skip_next:
            skip_next = False
            continue
        if part in {"--ignore", "--basetemp"}:
            skip_next = True
            continue
        if part.startswith("-"):
            continue
        path_args.append(part)
    return tuple(path_args)


def _runtime_budget_warning_payloads(
    entries: Sequence[TimingEntry],
    *,
    phase: str,
    total_elapsed_seconds: float,
) -> list[dict[str, object]]:
    warnings: list[dict[str, object]] = []
    if phase in PYTEST_SHARD_PHASES:
        if total_elapsed_seconds > PYTEST_SHARD_HARD_REVIEW_SECONDS:
            warnings.append(
                {
                    "level": "hard_review",
                    "kind": "pytest_shard_total",
                    "phase": phase,
                    "elapsed_seconds": total_elapsed_seconds,
                    "threshold_seconds": PYTEST_SHARD_HARD_REVIEW_SECONDS,
                }
            )
        elif total_elapsed_seconds > PYTEST_SHARD_WARNING_SECONDS:
            warnings.append(
                {
                    "level": "warning",
                    "kind": "pytest_shard_total",
                    "phase": phase,
                    "elapsed_seconds": total_elapsed_seconds,
                    "threshold_seconds": PYTEST_SHARD_WARNING_SECONDS,
                }
            )

    for entry in entries:
        if not _command_uses_pytest_helper(entry.command):
            continue
        path_args = _pytest_path_args(entry.command)
        idempotence_paths = [
            path
            for path in path_args
            if path.endswith("_idempotence.py") or path.endswith("idempotence.py")
        ]
        if entry.elapsed_seconds > PYTEST_SUBPROCESS_GROUP_WARNING_SECONDS:
            warnings.append(
                {
                    "level": "warning",
                    "kind": "pytest_subprocess_group",
                    "phase": entry.phase,
                    "command_index": entry.command_index,
                    "elapsed_seconds": entry.elapsed_seconds,
                    "threshold_seconds": PYTEST_SUBPROCESS_GROUP_WARNING_SECONDS,
                    "paths": list(path_args),
                }
            )
        if idempotence_paths:
            if entry.elapsed_seconds > PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS:
                warnings.append(
                    {
                        "level": "hard_review",
                        "kind": "pytest_idempotence_group",
                        "phase": entry.phase,
                        "command_index": entry.command_index,
                        "elapsed_seconds": entry.elapsed_seconds,
                        "threshold_seconds": PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS,
                        "paths": idempotence_paths,
                    }
                )
            elif entry.elapsed_seconds > PYTEST_IDEMPOTENCE_WARNING_SECONDS:
                warnings.append(
                    {
                        "level": "warning",
                        "kind": "pytest_idempotence_group",
                        "phase": entry.phase,
                        "command_index": entry.command_index,
                        "elapsed_seconds": entry.elapsed_seconds,
                        "threshold_seconds": PYTEST_IDEMPOTENCE_WARNING_SECONDS,
                        "paths": idempotence_paths,
                    }
                )
        if len(path_args) == 1 and path_args[0].endswith(".py"):
            hard_threshold = PYTEST_FILE_HARD_REVIEW_SECONDS
            warning_threshold = PYTEST_FILE_WARNING_SECONDS
            if path_args[0] in BOUNDED_DEFAULT_IDEMPOTENCE_TEST_PATHS:
                hard_threshold = PYTEST_IDEMPOTENCE_HARD_REVIEW_SECONDS
                warning_threshold = PYTEST_IDEMPOTENCE_WARNING_SECONDS
            if entry.elapsed_seconds > hard_threshold:
                warnings.append(
                    {
                        "level": "hard_review",
                        "kind": "pytest_file",
                        "phase": entry.phase,
                        "command_index": entry.command_index,
                        "elapsed_seconds": entry.elapsed_seconds,
                        "threshold_seconds": hard_threshold,
                        "path": path_args[0],
                    }
                )
            elif entry.elapsed_seconds > warning_threshold:
                warnings.append(
                    {
                        "level": "warning",
                        "kind": "pytest_file",
                        "phase": entry.phase,
                        "command_index": entry.command_index,
                        "elapsed_seconds": entry.elapsed_seconds,
                        "threshold_seconds": warning_threshold,
                        "path": path_args[0],
                    }
                )
    return warnings


def _slowest_timing_entries(entries: Sequence[TimingEntry]) -> list[TimingEntry]:
    return sorted(entries, key=lambda entry: entry.elapsed_seconds, reverse=True)[
        :SLOWEST_ENTRY_LIMIT
    ]


def _print_timing_summary(
    entries: Sequence[TimingEntry],
    *,
    phase: str,
    total_elapsed_seconds: float,
) -> None:
    print(
        f"QTT_VALIDATION_TIMING_TOTAL phase={phase} "
        f"elapsed_seconds={total_elapsed_seconds:.3f}",
        flush=True,
    )
    print(
        f"QTT_VALIDATION_TIMING_SLOWEST_TOP_{SLOWEST_ENTRY_LIMIT} phase={phase}",
        flush=True,
    )
    for rank, entry in enumerate(_slowest_timing_entries(entries), start=1):
        print(
            "QTT_VALIDATION_TIMING_SLOWEST "
            f"rank={rank} phase={entry.phase} "
            f"command_index={entry.command_index} "
            f"elapsed_seconds={entry.elapsed_seconds:.3f} "
            f"returncode={entry.returncode} "
            f"command={subprocess.list2cmdline(entry.command)}",
            flush=True,
        )
    for warning in _runtime_budget_warning_payloads(
        entries,
        phase=phase,
        total_elapsed_seconds=total_elapsed_seconds,
    ):
        detail = " ".join(
            f"{key}={value}"
            for key, value in warning.items()
            if key != "paths"
        )
        paths = ",".join(str(path) for path in warning.get("paths", ()))
        if paths:
            detail = f"{detail} paths={paths}"
        print(
            f"QTT_VALIDATION_RUNTIME_BUDGET_{str(warning['level']).upper()} {detail}",
            flush=True,
        )


def _timing_report_path_allowed(
    report_path: pathlib.Path,
    *,
    repo_root: pathlib.Path | None,
) -> bool:
    normalized = _normal_path_text(report_path)
    if repo_root is not None:
        try:
            normalized = _normal_path_text(report_path.resolve().relative_to(repo_root))
        except ValueError:
            normalized = _normal_path_text(report_path)
    return not any(
        normalized.startswith(prefix) for prefix in TRACKED_GENERATED_PATH_PREFIXES
    )


def _write_timing_report(
    report_path: pathlib.Path,
    *,
    phase: str,
    entries: Sequence[TimingEntry],
    total_elapsed_seconds: float,
    repo_root: pathlib.Path | None,
) -> None:
    if not _timing_report_path_allowed(report_path, repo_root=repo_root):
        raise ValueError(
            "timing report path is inside a tracked generated authority path: "
            f"{_normal_path_text(report_path)}"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": TIMING_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "phase": phase,
        "runtime_budget_policy": dict(RUNTIME_BUDGET_POLICY),
        "runtime_budget_warnings": _runtime_budget_warning_payloads(
            entries,
            phase=phase,
            total_elapsed_seconds=total_elapsed_seconds,
        ),
        "command_entries": [_timing_entry_payload(entry) for entry in entries],
        "total_elapsed_seconds": total_elapsed_seconds,
        "slowest_entries": [
            _timing_entry_payload(entry) for entry in _slowest_timing_entries(entries)
        ],
    }
    report_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_commands(
    commands: Sequence[Sequence[str]],
    repo_root: pathlib.Path | None = None,
    *,
    phase: str = ALL_PHASE,
    timing_report_path: pathlib.Path | None = None,
) -> int:
    cleanup_repo_root = (
        _RUN_COMMANDS_CLEANUP_REPO_ROOT if repo_root is None else repo_root
    )
    timing_entries: list[TimingEntry] = []
    total_started = time.perf_counter()

    def finish(returncode: int) -> int:
        total_elapsed_seconds = time.perf_counter() - total_started
        _print_timing_summary(
            timing_entries,
            phase=phase,
            total_elapsed_seconds=total_elapsed_seconds,
        )
        if timing_report_path is not None:
            try:
                _write_timing_report(
                    timing_report_path,
                    phase=phase,
                    entries=timing_entries,
                    total_elapsed_seconds=total_elapsed_seconds,
                    repo_root=cleanup_repo_root,
                )
            except ValueError as exc:
                print(str(exc), file=sys.stderr, flush=True)
                return 2
        if returncode == 0:
            print(f"{PHASE_SUCCESS_MARKER_PREFIX} phase={phase}", flush=True)
            print(SUCCESS_MARKER, flush=True)
        return returncode

    initially_modified_paths: set[str] = set()
    initially_modified_snapshots: dict[str, bytes | None] = {}
    if cleanup_repo_root is not None:
        initially_modified_paths = _tracked_modified_paths(cleanup_repo_root)
        initially_modified_snapshots = _modified_file_snapshots(
            cleanup_repo_root,
            initially_modified_paths,
        )

    def restore_gate_side_effects() -> None:
        if cleanup_repo_root is None:
            return
        _restore_tracked_gate_side_effects(
            cleanup_repo_root,
            initially_modified_paths,
        )
        _restore_modified_file_snapshots(
            cleanup_repo_root,
            initially_modified_snapshots,
        )

    for command_index, command in enumerate(commands, start=1):
        command_list = list(command)
        if cleanup_repo_root is not None and (
            _is_pr142_handoff_readiness_validator_command(command_list)
            or _is_pr143_owner_override_currentization_validator_command(command_list)
            or _is_final_pytest_command(command_list)
        ):
            try:
                restore_gate_side_effects()
            except RuntimeError as exc:
                print(str(exc), file=sys.stderr, flush=True)
                return finish(1)
        print(subprocess.list2cmdline(command_list), flush=True)
        command_started = time.perf_counter()
        completed = subprocess.run(command_list)
        elapsed_seconds = time.perf_counter() - command_started
        timing_entries.append(
            TimingEntry(
                phase=phase,
                command_index=command_index,
                command=command_list,
                elapsed_seconds=elapsed_seconds,
                returncode=completed.returncode,
            )
        )
        print(
            "QTT_VALIDATION_TIMING_COMMAND "
            f"phase={phase} command_index={command_index} "
            f"elapsed_seconds={elapsed_seconds:.3f} "
            f"returncode={completed.returncode}",
            flush=True,
        )
        if completed.returncode != 0:
            if cleanup_repo_root is not None and _is_final_pytest_command(
                command_list
            ):
                try:
                    restore_gate_side_effects()
                except RuntimeError as exc:
                    print(str(exc), file=sys.stderr, flush=True)
            return finish(completed.returncode)
        try:
            _record_no_runtime_scan_success(command_list, cleanup_repo_root)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr, flush=True)
            return finish(1)
        if cleanup_repo_root is not None and _is_final_pytest_command(command_list):
            try:
                restore_gate_side_effects()
            except RuntimeError as exc:
                print(str(exc), file=sys.stderr, flush=True)
                return finish(1)
        if cleanup_repo_root is not None:
            currentness_failures = _routed_generated_output_currentness_failures(
                command_list,
                cleanup_repo_root,
            )
            if currentness_failures:
                for failure in currentness_failures:
                    print(failure, file=sys.stderr, flush=True)
                return finish(1)

    return finish(0)


def _run_commands_accepts_repo_root() -> bool:
    try:
        signature = inspect.signature(run_commands)
    except (TypeError, ValueError):
        return True
    parameters = signature.parameters.values()
    return any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        or parameter.name == "repo_root"
        for parameter in parameters
    )


def _github_event_name() -> str:
    import os

    return os.getenv("GITHUB_EVENT_NAME", "")


def _changed_area_routing_active(
    *,
    validation_mode: str,
    changed_files: Sequence[str],
) -> bool:
    if validation_mode == "full":
        return False
    if validation_mode == "reduced":
        return True
    if changed_files:
        return True
    return _github_event_name() == "pull_request"


def _router_result_for_current_context(
    repo_root: pathlib.Path,
    *,
    changed_files: Sequence[str],
    base_ref: str | None,
    head_ref: str | None,
    force_full: bool,
    manual_mode: str,
):
    from tools.changed_area_validation_router import (
        build_router_result,
        router_input_from_environment,
    )

    router_input = router_input_from_environment(
        repo_root,
        changed_files=changed_files,
        base_ref=base_ref,
        head_ref=head_ref,
        force_full_flag=force_full,
        manual_mode=manual_mode,
    )
    return build_router_result(router_input)


def _filter_commands_for_router_result(
    commands: Sequence[Sequence[str]],
    *,
    phase: str,
    router_result,
) -> list[list[str]]:
    from tools.validation_inventory import canonical_command, validator_id_for_command

    required = set(router_result.required_validators)
    phase_by_command: dict[tuple[str, ...], str] = {}
    if phase == ALL_PHASE:
        for phase_record in build_phase_manifest():
            record_phase = str(phase_record["phase"])
            for record_command in phase_record["commands"]:
                phase_by_command[canonical_command(record_command)] = record_phase
    kept: list[list[str]] = []
    skipped: list[str] = []
    for command in commands:
        command_list = list(command)
        command_phase = phase_by_command.get(canonical_command(command_list), phase)
        validator_id = validator_id_for_command(command_list, command_phase)
        if validator_id in required:
            kept.append(command_list)
        else:
            skipped.append(validator_id)
    if skipped:
        print(
            "QTT_CHANGED_AREA_ROUTER_SKIPPED "
            f"phase={phase} validators={','.join(sorted(skipped))}",
            flush=True,
        )
    return kept


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=VALIDATION_PHASES,
        default=ALL_PHASE,
        help="Validation phase to run; default runs the full split validation plan.",
    )
    parser.add_argument(
        "--timing-report",
        type=pathlib.Path,
        help="Optional untracked JSON timing report path.",
    )
    parser.add_argument(
        "--validation-mode",
        choices=("auto", "full", "reduced"),
        default="auto",
        help=(
            "auto keeps local/default validation full and uses changed-area "
            "routing for GitHub pull_request contexts"
        ),
    )
    parser.add_argument("--base-ref")
    parser.add_argument("--head-ref")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--force-full", action="store_true")
    parser.add_argument("--manual-mode", default="")
    parser.add_argument(
        "--router-report",
        type=pathlib.Path,
        help="Optional untracked JSON changed-area router report path.",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else list(argv))
    repo_root = _repo_root()
    timing_report_path = args.timing_report
    if timing_report_path is not None and not timing_report_path.is_absolute():
        timing_report_path = repo_root / timing_report_path
    if timing_report_path is not None and not _timing_report_path_allowed(
        timing_report_path,
        repo_root=repo_root,
    ):
        print(
            "timing report path is inside a tracked generated authority path: "
            f"{_normal_path_text(timing_report_path)}",
            file=sys.stderr,
        )
        return 2
    tmp_parent = repo_root / ".tmp"
    tmp_parent.mkdir(parents=True, exist_ok=True)
    global _RUN_COMMANDS_CLEANUP_REPO_ROOT
    previous_cleanup_repo_root = _RUN_COMMANDS_CLEANUP_REPO_ROOT
    _RUN_COMMANDS_CLEANUP_REPO_ROOT = repo_root
    previous_scan_cache_env = os.environ.get(NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV)
    installed_scan_cache_env = False
    previous_pr152_cache_env = os.environ.get(PR152_BUILD_REPORT_CACHE_ENV)
    installed_pr152_cache_env = False
    try:
        with tempfile.TemporaryDirectory(prefix="qtt_validation_gates_") as temp_dir:
            if previous_scan_cache_env is None:
                os.environ[NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV] = str(
                    pathlib.Path(temp_dir) / "NoRuntimeArtifactScanCache.json"
                )
                installed_scan_cache_env = True
            if previous_pr152_cache_env is None:
                os.environ[PR152_BUILD_REPORT_CACHE_ENV] = str(
                    pathlib.Path(temp_dir) / "PR152BuildReportCache.json"
                )
                installed_pr152_cache_env = True
            with tempfile.TemporaryDirectory(
                prefix="run_validation_gates_pytest_",
            ) as pytest_temp_dir:
                commands = build_phase_commands(
                    args.phase,
                    pathlib.Path(temp_dir),
                    pathlib.Path(pytest_temp_dir),
                )
                router_result = None
                if _changed_area_routing_active(
                    validation_mode=args.validation_mode,
                    changed_files=args.changed_file,
                ):
                    router_result = _router_result_for_current_context(
                        repo_root,
                        changed_files=args.changed_file,
                        base_ref=args.base_ref,
                        head_ref=args.head_ref,
                        force_full=args.force_full,
                        manual_mode=args.manual_mode,
                    )
                    router_report_path = args.router_report
                    if router_report_path is not None:
                        if not router_report_path.is_absolute():
                            router_report_path = repo_root / router_report_path
                        router_report_path.parent.mkdir(parents=True, exist_ok=True)
                        router_report_path.write_text(
                            json.dumps(
                                router_result.to_json_dict(),
                                indent=2,
                                sort_keys=True,
                            )
                            + "\n",
                            encoding="utf-8",
                        )
                    print(
                        "QTT_CHANGED_AREA_ROUTER_MODE "
                        f"phase={args.phase} "
                        f"full_validation_required={router_result.full_validation_required} "
                        f"reason={router_result.full_validation_reason!r}",
                        flush=True,
                    )
                    if router_result.fail_closed_reasons:
                        for reason in router_result.fail_closed_reasons:
                            print(reason, file=sys.stderr, flush=True)
                        return 2
                    if not router_result.full_validation_required:
                        commands = _filter_commands_for_router_result(
                            commands,
                            phase=args.phase,
                            router_result=router_result,
                        )
                if _run_commands_accepts_repo_root():
                    return run_commands(
                        commands,
                        repo_root=repo_root,
                        phase=args.phase,
                        timing_report_path=timing_report_path,
                    )
                return run_commands(commands)
    finally:
        if installed_scan_cache_env:
            os.environ.pop(NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV, None)
        if installed_pr152_cache_env:
            os.environ.pop(PR152_BUILD_REPORT_CACHE_ENV, None)
        _RUN_COMMANDS_CLEANUP_REPO_ROOT = previous_cleanup_repo_root


if __name__ == "__main__":
    raise SystemExit(main())
