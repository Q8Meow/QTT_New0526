"""Shared contracts and deterministic JSON helpers for PR168-QOPT1."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, getcontext
import json
from pathlib import Path
from typing import Any, Iterable

getcontext().prec = 28

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_qopt1"
GENERATED_REF_PREFIX = "docs/master_plan/generated/pr168_qopt1"
UPSTREAM_RANK4_REF_PREFIX = "docs/master_plan/generated/pr168_rank4"
UPSTREAM_RP5G_REF_PREFIX = "docs/master_plan/generated/pr168_rp5g"

PR_ID = "PR168-QOPT1"
BRANCH_NAME = "pr168-qopt1-quantum-classical-batch-optimization"
RUN_ID = "PR168_QOPT1_DETERMINISTIC_RUN_20260630T040000Z"
CREATED_AT_UTC = "2026-06-30T04:00:00Z"
REPORT_VERSION = "PR168-QOPT1-v1.0"
BASELINE_MAIN_HEAD = "6046f46ceb00e047c4f781343c35212635535afa"
EXECUTION_AUTHORITY_REF = "QOPT1_EXEC_AUTH::ADVISORY_BATCH_OPTIMIZATION_ONLY_NO_ORDER_AUTHORITY"
AUTHORITY_BOUNDARY_REF = (
    "QOPT1_AUTH_BOUNDARY::NO_FINAL_CHAMPION_NO_PAPER_INTENT_NO_LIVE_NO_CONNECTOR_"
    "NO_TRUE_QUANTUM_BACKEND"
)
BLOCKER_POLICY_REF = (
    "QOPT1_BLOCKER_POLICY::RANK4_NUMERIC_EVIDENCE_CLASSICAL_FALLBACK_"
    "STRUCTURAL_QOPT_AND_REOPTIMIZATION_ONLY"
)
VALIDATOR_REF = "tools/validate_pr168_qopt1_batch_optimization.py"
PRODUCER_TOOL = "tools/build_pr168_qopt1_batch_optimization.py"

JSON_OUTPUTS = ("art_reg.json",)
MARKDOWN_OUTPUTS = ("pr_body.md",)

REPORT_OUTPUTS = (
    "missing_req.report.json",
    "run_receipt.report.json",
    "input_consumption.report.json",
    "optimization_summary.report.json",
    "batch_summary.report.json",
    "classic_solver.report.json",
    "quantum_struct.report.json",
    "vs2_handoff.report.json",
    "mem1_handoff.report.json",
    "agent_route.report.json",
    "no_orphan.report.json",
    "authority_boundary.report.json",
    "validation_summary.report.json",
)

JSONL_OUTPUTS = (
    "read_rec.jsonl",
    "in_cons.jsonl",
    "miss_opt.jsonl",
    "self_audit_pre.jsonl",
    "self_audit_post.jsonl",
    "research_rec.jsonl",
    "source_coverage.jsonl",
    "source_intake.jsonl",
    "source_value_cand.jsonl",
    "institutional_default_cand.jsonl",
    "params.jsonl",
    "policy_prov.jsonl",
    "qopt1_qku_optability.jsonl",
    "qopt1_formula_optability.jsonl",
    "qopt1_candidate_optability.jsonl",
    "qopt1_batchability.jsonl",
    "rank4_input_refs.jsonl",
    "active_set_policy.jsonl",
    "active_set.jsonl",
    "use_dump_universe.jsonl",
    "batch_universe.jsonl",
    "var_map.jsonl",
    "cash_reserve_var.jsonl",
    "notrade_budget.jsonl",
    "obj_terms.jsonl",
    "obj_decomp.jsonl",
    "constraints.jsonl",
    "constraint_mat.jsonl",
    "constraint_check.jsonl",
    "notrade_batch.jsonl",
    "classic_solver_policy.jsonl",
    "greedy_baseline.jsonl",
    "milp_result.jsonl",
    "beam_result.jsonl",
    "local_search_result.jsonl",
    "classic_best.jsonl",
    "classic_compare.jsonl",
    "solver_cascade.jsonl",
    "solver_arb.jsonl",
    "efficient_frontier.jsonl",
    "robust_batch.jsonl",
    "stress_batch.jsonl",
    "null_batch.jsonl",
    "random_base.jsonl",
    "anti_sel_bias.jsonl",
    "constraint_bind.jsonl",
    "shadow_price.jsonl",
    "lagrangian_term.jsonl",
    "opt_runtime_budget.jsonl",
    "solver_budget.jsonl",
    "hotpath_batch.jsonl",
    "coldpath_route.jsonl",
    "diversity_frontier.jsonl",
    "regime_balance.jsonl",
    "batch_xplain.jsonl",
    "downstream_ready.jsonl",
    "exposure_matrix.jsonl",
    "corr_proxy.jsonl",
    "near_clone_pair.jsonl",
    "capacity_matrix.jsonl",
    "portfolio_batch.jsonl",
    "marginal_utility_batch.jsonl",
    "crowding_batch.jsonl",
    "capital_efficiency.jsonl",
    "exec_coupling.jsonl",
    "regret_proxy.jsonl",
    "cvar_proxy.jsonl",
    "tradeability_proof.jsonl",
    "policy_default_prov.jsonl",
    "batch_candidate.jsonl",
    "batch_score.jsonl",
    "batch_select.jsonl",
    "batch_explain.jsonl",
    "batch_frontier.jsonl",
    "batch_champ_prev.jsonl",
    "batch_chall_prev.jsonl",
    "batch_diversity.jsonl",
    "batch_capacity.jsonl",
    "batch_tca.jsonl",
    "batch_fdr.jsonl",
    "batch_scenario.jsonl",
    "batch_memory.jsonl",
    "batch_tail_guard.jsonl",
    "batch_sensitivity.jsonl",
    "memory_prior_batch.jsonl",
    "recipe_batch_use.jsonl",
    "context_similarity_batch.jsonl",
    "negative_memory_batch.jsonl",
    "drift_batch.jsonl",
    "retest_batch.jsonl",
    "mem1_handoff.jsonl",
    "qstruct_universe.jsonl",
    "qproblem.jsonl",
    "qubo.jsonl",
    "bqm.jsonl",
    "cqm.jsonl",
    "quad_prog.jsonl",
    "ising_map.jsonl",
    "qobj_coeff.jsonl",
    "qconstraints.jsonl",
    "qpenalty_policy.jsonl",
    "qcoef_scale.jsonl",
    "qfeas_check.jsonl",
    "qinterp.jsonl",
    "qclassic_fb.jsonl",
    "qstruct_quality.jsonl",
    "qpenalty_sweep.jsonl",
    "objective_sign.jsonl",
    "energy_transform.jsonl",
    "qubo_matrix.jsonl",
    "qubo_symmetry.jsonl",
    "quadratize.jsonl",
    "slack_var_map.jsonl",
    "penalty_dom_audit.jsonl",
    "feas_energy_gap.jsonl",
    "anneal_hint.jsonl",
    "gate_model_hint.jsonl",
    "backend_profile_hint.jsonl",
    "qaoa_seed_hint.jsonl",
    "anneal_schedule_hint.jsonl",
    "class_dom_base.jsonl",
    "qencoding_diag.jsonl",
    "qresource_est.jsonl",
    "qpenalty_audit.jsonl",
    "qbackend_hint.jsonl",
    "penalty_ladder.jsonl",
    "qmemory_use.jsonl",
    "notrade_reopt.jsonl",
    "var_tune_frontier.jsonl",
    "stack_chall_frontier.jsonl",
    "venue_side_rotate.jsonl",
    "adapter_source_refresh.jsonl",
    "next_target_rotate.jsonl",
    "retest_queue.jsonl",
    "tradeable_recovery_batch.jsonl",
    "notrade_opp_cost.jsonl",
    "notrade_not_terminal.jsonl",
    "var_proxy.jsonl",
    "drawdown_proxy.jsonl",
    "pos_edge_search.jsonl",
    "profit_gap_close.jsonl",
    "scenario_trade_frontier.jsonl",
    "latency_profit_frontier.jsonl",
    "cand_ablation.jsonl",
    "agent_work_queue.jsonl",
    "exec_path_hint.jsonl",
    "vs2_handoff.jsonl",
    "paper_handoff.jsonl",
    "live_dry_handoff.jsonl",
    "shadow_handoff.jsonl",
    "auth_block.jsonl",
    "agent_alias_map.jsonl",
    "agent_route.jsonl",
    "agent_consume.jsonl",
    "agent_duty_map.jsonl",
    "agent_no_orphan.jsonl",
    "agent_authority_block.jsonl",
    "artifact_io.jsonl",
    "file_route.jsonl",
    "row_route.jsonl",
    "value_route.jsonl",
    "info_route.jsonl",
    "lineage.jsonl",
    "dag.jsonl",
    "val_lineage.jsonl",
    "downstream.jsonl",
    "completion_route.jsonl",
    "orph_art.jsonl",
    "orph_qku.jsonl",
)

REQUIRED_INPUT_REFS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/generated/PR168_RP5C_FinalSummary.report.json",
    "docs/master_plan/generated/pr168_vs1/vs1_run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5d/rp5d_run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5e/run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5d_r1/run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5f/art_reg.json",
    "docs/master_plan/generated/pr168_rp5f/run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5g/art_reg.json",
    "docs/master_plan/generated/pr168_rp5g/run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5g/trade_candidate.jsonl",
    "docs/master_plan/generated/pr168_rp5g/sim_run.jsonl",
    "docs/master_plan/generated/pr168_rp5g/sim_result.jsonl",
    "docs/master_plan/generated/pr168_rp5g/exec_pnl.jsonl",
    "docs/master_plan/generated/pr168_rp5g/tca_decomp.jsonl",
    "docs/master_plan/generated/pr168_rp5g/fill_latency_cap.jsonl",
    "docs/master_plan/generated/pr168_rp5g/capacity_crowding.jsonl",
    "docs/master_plan/generated/pr168_rp5g/notrade_cmp.jsonl",
    "docs/master_plan/generated/pr168_rp5g/scenario_ladder.jsonl",
    "docs/master_plan/generated/pr168_rp5g/overfit_fdr.jsonl",
    "docs/master_plan/generated/pr168_rp5g/port_marg_util.jsonl",
    "docs/master_plan/generated/pr168_rp5g/calibration_result.jsonl",
    "docs/master_plan/generated/pr168_rp5g/data_prov.jsonl",
    "docs/master_plan/generated/pr168_rp5g/formula_comp.jsonl",
    "docs/master_plan/generated/pr168_rp5g/var_eval.jsonl",
    "docs/master_plan/generated/pr168_rp5g/var_reject.jsonl",
    "docs/master_plan/generated/pr168_rp5g/qstruct_problem.jsonl",
    "docs/master_plan/generated/pr168_rp5g/qobj_coeff.jsonl",
    "docs/master_plan/generated/pr168_rp5g/q_constraints.jsonl",
    "docs/master_plan/generated/pr168_rp5g/q_interp.jsonl",
    "docs/master_plan/generated/pr168_rp5g/q_classic_fb.jsonl",
    "docs/master_plan/generated/pr168_rp5g/qopt_handoff.jsonl",
    "docs/master_plan/generated/pr168_rp5g/agent_route.jsonl",
    "docs/master_plan/generated/pr168_rp5g/agent_consume.jsonl",
    "docs/master_plan/generated/pr168_rp5g/artifact_io.jsonl",
    "docs/master_plan/generated/pr168_rp5g/file_route.jsonl",
    "docs/master_plan/generated/pr168_rp5g/value_route.jsonl",
    "docs/master_plan/generated/pr168_rp5g/row_route.jsonl",
    "docs/master_plan/generated/pr168_rp5g/info_route.jsonl",
    "docs/master_plan/generated/pr168_rp5g/lineage.jsonl",
    "docs/master_plan/generated/pr168_rp5g/dag.jsonl",
    "docs/master_plan/generated/pr168_rp5g/val_lineage.jsonl",
    "docs/master_plan/generated/pr168_rp5g/downstream.jsonl",
    "docs/master_plan/generated/pr168_rp5g/completion_route.jsonl",
    "docs/master_plan/generated/pr168_rp5g/orph_art.jsonl",
    "docs/master_plan/generated/pr168_rp5g/orph_qku.jsonl",
    "docs/master_plan/generated/pr168_rank4/art_reg.json",
    "docs/master_plan/generated/pr168_rank4/run_receipt.report.json",
    "docs/master_plan/generated/pr168_rank4/read_rec.jsonl",
    "docs/master_plan/generated/pr168_rank4/in_cons.jsonl",
    "docs/master_plan/generated/pr168_rank4/miss_opt.jsonl",
    "docs/master_plan/generated/pr168_rank4/self_audit_pre.jsonl",
    "docs/master_plan/generated/pr168_rank4/self_audit_post.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_edge_capture.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_obj_decomp.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_score.jsonl",
    "docs/master_plan/generated/pr168_rank4/score_comp.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_feat.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_order.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_explain.jsonl",
    "docs/master_plan/generated/pr168_rank4/elig_gate.jsonl",
    "docs/master_plan/generated/pr168_rank4/notrade_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/tca_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/fill_lat_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/capacity_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/port_div_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/marg_util_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/near_clone_cluster.jsonl",
    "docs/master_plan/generated/pr168_rank4/pareto_frontier.jsonl",
    "docs/master_plan/generated/pr168_rank4/dominance.jsonl",
    "docs/master_plan/generated/pr168_rank4/fdr_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/scenario_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/calib_rank.jsonl",
    "docs/master_plan/generated/pr168_rank4/champ_prev.jsonl",
    "docs/master_plan/generated/pr168_rank4/chall_prev.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_context_signature.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_similarity_key.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_memory_recipe_handoff.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_recipe_prior_score.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_recipe_batch_policy.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_negative_memory_hint.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_recipe_drift_hint.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_retest_priority.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_qmemory_handoff.jsonl",
    "docs/master_plan/generated/pr168_rank4/qrank_feat.jsonl",
    "docs/master_plan/generated/pr168_rank4/qrank_score.jsonl",
    "docs/master_plan/generated/pr168_rank4/qopt_batch.jsonl",
    "docs/master_plan/generated/pr168_rank4/qopt_frontier.jsonl",
    "docs/master_plan/generated/pr168_rank4/qopt_constraints.jsonl",
    "docs/master_plan/generated/pr168_rank4/qopt_interpret_back_rank_map.jsonl",
    "docs/master_plan/generated/pr168_rank4/vs2_handoff.jsonl",
    "docs/master_plan/generated/pr168_rank4/mem1_handoff.jsonl",
    "docs/master_plan/generated/pr168_rank4/orch1_handoff.jsonl",
    "docs/master_plan/generated/pr168_rank4/paper_handoff.jsonl",
    "docs/master_plan/generated/pr168_rank4/live_dry_handoff.jsonl",
    "docs/master_plan/generated/pr168_rank4/shadow_handoff.jsonl",
    "docs/master_plan/generated/pr168_rank4/agent_alias_map.jsonl",
    "docs/master_plan/generated/pr168_rank4/agent_route.jsonl",
    "docs/master_plan/generated/pr168_rank4/agent_consume.jsonl",
    "docs/master_plan/generated/pr168_rank4/agent_duty_map.jsonl",
    "docs/master_plan/generated/pr168_rank4/agent_no_orphan.jsonl",
    "docs/master_plan/generated/pr168_rank4/agent_authority_block.jsonl",
    "docs/master_plan/generated/pr168_rank4/artifact_io.jsonl",
    "docs/master_plan/generated/pr168_rank4/file_route.jsonl",
    "docs/master_plan/generated/pr168_rank4/row_route.jsonl",
    "docs/master_plan/generated/pr168_rank4/value_route.jsonl",
    "docs/master_plan/generated/pr168_rank4/info_route.jsonl",
    "docs/master_plan/generated/pr168_rank4/lineage.jsonl",
    "docs/master_plan/generated/pr168_rank4/dag.jsonl",
    "docs/master_plan/generated/pr168_rank4/val_lineage.jsonl",
    "docs/master_plan/generated/pr168_rank4/downstream.jsonl",
    "docs/master_plan/generated/pr168_rank4/completion_route.jsonl",
    "docs/master_plan/generated/pr168_rank4/orph_art.jsonl",
    "docs/master_plan/generated/pr168_rank4/orph_qku.jsonl",
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
)

OPTIONAL_INPUT_REFS = (
    "docs/master_plan/generated/pr168_rank4/rank_port_basket.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_hotpath.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_next_action.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_source_rights.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_constraint_tightness.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_rank_stability.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_sensitivity_surface.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_micro_regime.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_tail_guard.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_auto_trading_path.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_live_ladder.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_realization_receipt_req.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_access_mode.jsonl",
    "docs/master_plan/generated/pr168_rank4/rank_stack_synergy.jsonl",
    "docs/master_plan/generated/pr168_rp5g/nonofficial_cand.jsonl",
    "docs/master_plan/generated/pr168_rp5g/source_cov_max.jsonl",
    "docs/master_plan/generated/pr166_q_shards/PR166_Q_FinalSummary.part_0001_of_0001.report.json",
)

PARAM_DEFAULTS: dict[str, Decimal | int] = {
    "active_set_max_candidates_default": 5,
    "batch_size_min_default": 1,
    "batch_size_max_default": 3,
    "capital_budget_cash_proxy_default": Decimal("20.000000"),
    "min_no_trade_margin_cash_default": Decimal("0.000000"),
    "min_lcb_cash_default": Decimal("0.000000"),
    "min_fill_probability_default": Decimal("0.500000"),
    "max_latency_ms_default": 1000,
    "max_capacity_crowding_cash_default": Decimal("0.250000"),
    "max_tca_to_edge_ratio_default": Decimal("0.500000"),
    "max_model_risk_reserve_cash_default": Decimal("0.500000"),
    "max_fdr_penalty_cash_default": Decimal("0.250000"),
    "scenario_floor_cash_default": Decimal("-0.500000"),
    "near_clone_similarity_threshold_default": Decimal("0.850000"),
    "penalty_weight_base_default": Decimal("5.000000"),
    "solver_beam_width_default": 8,
    "deterministic_seed_default": 16801,
}

FALSE_AUTHORITY_FIELDS = (
    "optimized_batch_advisory_only_flag",
    "final_champion_selected_flag",
    "final_trade_rank_for_execution_flag",
    "paper_order_intent_created_flag",
    "paper_submit_authority_created_flag",
    "live_authority_created_flag",
    "connector_write_created_flag",
    "private_state_read_created_flag",
    "cash_account_read_created_flag",
    "true_quantum_backend_execution_flag",
    "cloud_quantum_job_created_flag",
    "quantum_credential_used_flag",
    "quantum_advantage_claim_flag",
    "profit_guarantee_flag",
    "memory_prior_as_current_profit_proof_flag",
    "durable_MEM1_storage_created_flag",
    "MEM1_query_api_created_flag",
    "exit_sell_close_authority_created_flag",
    "realized_pnl_receipt_created_flag",
    "external_candidate_as_source_fact_flag",
    "non_official_value_as_live_default_flag",
    "live_canary_promotion_created_by_qopt1_flag",
    "shadow_execution_authority_created_by_qopt1_flag",
    "qTT_SHA_authority_created_flag",
    "atomicrows_hash_authority_created_flag",
    "accepted_source_fact_flag",
    "connector_semantic_binding_flag",
    "connector_write_flag",
    "private_state_fetch_flag",
    "cash_account_read_flag",
    "formula_mutation_flag",
    "formula_deletion_flag",
    "qku_mutation_flag",
    "qku_deletion_flag",
    "global_ban_flag",
    "formula_global_ban_flag",
    "qku_global_ban_flag",
    "order_authority_created_flag",
    "paper_order_authority_created_flag",
    "live_order_authority_created_flag",
    "buy_sell_open_close_logic_created_flag",
    "buy_sell_open_close_created_flag",
    "shadow_execution_authority_created_flag",
    "live_order_authority_created_flag",
    "real_order_authority_created_flag",
    "runtime_authority_created_flag",
    "paper_submit_ready_flag",
    "live_submit_ready_flag",
    "order_submit_ready_flag",
    "real_market_profit_proof_flag",
    "real_market_loss_proof_flag",
    "profit_proof_flag",
    "proprietary_claim_flag",
    "fake_profit_forcing_flag",
    "source_fact_acceptance_flag",
    "live_default_flag",
    "backend_execution_created_flag",
    "credential_required_flag",
    "current_profit_proof_flag",
)

TRUE_AUTHORITY_GUARD_FIELDS = (
    "advisory_only_flag",
    "qopt1_batch_is_advisory_only",
    "vs2_required_before_paper_intent",
    "paper_loop_required_before_paper_execution",
    "mem1_required_for_durable_memory",
    "live_dryrun_required_before_live_pilot",
    "live_pilot_required_before_launch",
    "execution_router_required_before_any_buy_sell_open_close",
    "current_snapshot_revalidation_required",
    "connector_state_required_future_only",
    "cash_account_state_required_future_only",
    "kill_switch_required_future_only",
    "owner_enablement_required_future_only",
)

FORBIDDEN_STATE_VALUES = (
    "FINAL_CHAMPION",
    "FINAL_TRADE_RANK_FOR_EXECUTION",
    "LIVE_CANDIDATE",
    "ORDER_READY",
    "PAPER_ORDER_INTENT",
    "PAPER_ORDER_SUBMIT_READY",
    "PROFIT_GUARANTEE",
    "QUANTUM_ADVANTAGE_PROVEN",
    "TRUE_QUANTUM_BACKEND_EXECUTION",
    "CLOUD_QUANTUM_JOB",
    "PAID_QUANTUM_SERVICE_JOB",
    "QUANTUM_CREDENTIAL_USE",
    "SHADOW_EXECUTABLE_NOW",
    "LIVE_EXECUTABLE_NOW",
    "BUY_SELL_OPEN_CLOSE_READY",
    "EXIT_SELL_CLOSE_AUTHORITY",
    "REALIZED_PNL_RECEIPT_CREATED",
    "DURABLE_MEM1_STORAGE_CREATED",
    "MEM1_QUERY_API_CREATED",
    "SOURCE_FACT_ACCEPTED",
    "CONNECTOR_SEMANTIC_BOUND",
    "QOPT_EXECUTED",
    "QUANTUM_BACKEND_EXECUTED",
)

RESEARCH_SOURCES = (
    (
        "https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.QuadraticProgram.html",
        "Qiskit Optimization QuadraticProgram",
        "OFFICIAL_DOC",
        "QUADRATIC_PROGRAM_STRUCTURE",
        "QuadraticProgram variable/objective/constraint structural design candidate",
    ),
    (
        "https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html",
        "Qiskit Optimization converters",
        "OFFICIAL_DOC",
        "QUBO_CONVERSION",
        "max-to-min and converter diagnostics for future structural compatibility",
    ),
    (
        "https://docs.dwavequantum.com/en/latest/concepts/models.html",
        "D-Wave Ocean model concepts",
        "OFFICIAL_DOC",
        "BQM_CQM_QUBO_STRUCTURE",
        "BQM/CQM/QUBO model-family candidate only",
    ),
    (
        "https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html",
        "SciPy optimize.milp",
        "OFFICIAL_DOC",
        "CLASSICAL_MILP_BASELINE",
        "optional local MILP baseline interface when scipy is already available",
    ),
    (
        "https://www.jstor.org/stable/2346101",
        "Benjamini-Hochberg false discovery rate",
        "PAPER",
        "FDR_CONTROL",
        "multiple-testing control candidate",
    ),
    (
        "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551",
        "The deflated Sharpe ratio",
        "PAPER",
        "SELECTION_BIAS_CONTROL",
        "selection-bias/backtest-overfit candidate only when inputs support it",
    ),
    (
        "https://jmlr.org/papers/v18/16-558.html",
        "Hyperband: A Novel Bandit-Based Approach to Hyperparameter Optimization",
        "PAPER",
        "BOUNDED_SEARCH",
        "successive-halving and bounded active-set search inspiration",
    ),
    (
        "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/trading-costs-electronic-markets",
        "CFA Institute trading costs and electronic markets",
        "PUBLIC_RESEARCH",
        "IMPLEMENTATION_SHORTFALL_TCA",
        "transaction-cost and implementation-shortfall decomposition candidate",
    ),
    (
        "https://docs.kalshi.com/api-reference/market/get-market-orderbook",
        "Kalshi market orderbook API",
        "OFFICIAL_DOC",
        "VENUE_ORDERBOOK_CANDIDATE",
        "candidate-only orderbook source route, not connector binding",
    ),
    (
        "https://docs.polymarket.com/developers/CLOB/introduction",
        "Polymarket CLOB API documentation",
        "OFFICIAL_DOC",
        "VENUE_ORDERBOOK_CANDIDATE",
        "candidate-only CLOB source route, not connector binding",
    ),
)


def dec(value: Any, default: str = "0") -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None or value == "":
        return Decimal(default)
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def score(value: Any) -> str:
    return str(dec(value).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def bounded(value: Any, low: Decimal = Decimal("0"), high: Decimal = Decimal("1")) -> Decimal:
    raw = dec(value)
    return max(low, min(high, raw))


def stable_unique(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            out.extend(stable_unique(value))
            continue
        text = str(value).strip()
        if text:
            out.append(text)
    return sorted(dict.fromkeys(out), key=lambda item: (item.casefold(), item))


def generated_ref(filename: str) -> str:
    return f"{GENERATED_REF_PREFIX}/{filename}"


def upstream_rank4_ref(filename: str) -> str:
    return f"{UPSTREAM_RANK4_REF_PREFIX}/{filename}"


def upstream_rp5g_ref(filename: str) -> str:
    return f"{UPSTREAM_RP5G_REF_PREFIX}/{filename}"


def manifest_name(filename: str) -> str:
    return f"{Path(filename).stem}.manifest.json"


def all_artifact_filenames(include_manifests: bool = True) -> tuple[str, ...]:
    base = tuple(dict.fromkeys((*JSON_OUTPUTS, *REPORT_OUTPUTS, *JSONL_OUTPUTS, *MARKDOWN_OUTPUTS)))
    if not include_manifests:
        return base
    manifests = tuple(manifest_name(name) for name in JSONL_OUTPUTS)
    return tuple(dict.fromkeys((*base, *manifests)))


def stable_json(payload: Any, *, compact: bool = False) -> str:
    separators = (",", ":") if compact else None
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=None if compact else 2, separators=separators) + "\n"


def read_json(path: Path) -> Any:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows_tuple = tuple(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(stable_json(row, compact=True) for row in rows_tuple), encoding="utf-8")
    manifest = {
        "schema_version": REPORT_VERSION,
        "row_id": f"MANIFEST::{path.name}",
        "producer_pr": PR_ID,
        "source_pr": PR_ID,
        "producer_tool": PRODUCER_TOOL,
        "created_at_utc": CREATED_AT_UTC,
        "artifact_filename": path.name,
        "row_count": len(rows_tuple),
        "manual_edit_allowed_flag": False,
        "authority_boundary_ref": AUTHORITY_BOUNDARY_REF,
        "execution_authority_ref": EXECUTION_AUTHORITY_REF,
        "validation_refs": [VALIDATOR_REF],
        "orphan_flag": False,
        "advisory_only_flag": True,
        "optimized_batch_advisory_only_flag": True,
    }
    for flag in FALSE_AUTHORITY_FIELDS:
        if flag != "optimized_batch_advisory_only_flag":
            manifest[flag] = False
    write_json(path.with_name(manifest_name(path.name)), manifest)


def common_row(
    row: dict[str, Any],
    *,
    row_id: str,
    owner_agent: str,
    consumer_agents: Iterable[str],
    upstream_refs: Iterable[str],
    downstream_refs: Iterable[str],
    source_artifact_refs: Iterable[str] | None = None,
    validation_refs: Iterable[str] = (VALIDATOR_REF,),
    provenance_tier: str = "QOPT1_ADVISORY_BATCH_OPTIMIZATION_EVIDENCE",
    intelligence_classes: Iterable[str] = ("SEARCH_INTELLIGENCE",),
) -> dict[str, Any]:
    out = dict(row)
    upstream = stable_unique(upstream_refs)
    downstream = stable_unique(downstream_refs)
    source_artifacts = stable_unique(source_artifact_refs or upstream)
    consumers = stable_unique(consumer_agents)
    validations = stable_unique(validation_refs)
    out.setdefault("schema_version", REPORT_VERSION)
    out.setdefault("row_id", row_id)
    out.setdefault("run_id", RUN_ID)
    out.setdefault("producer_pr", PR_ID)
    out.setdefault("source_pr", PR_ID)
    out.setdefault("producer_tool", PRODUCER_TOOL)
    out.setdefault("created_at_utc", CREATED_AT_UTC)
    out.setdefault("source_artifact_refs", source_artifacts)
    out.setdefault("upstream_refs", upstream)
    out.setdefault("downstream_refs", downstream)
    out.setdefault("owner_agent", owner_agent)
    out.setdefault("producer_agent", owner_agent)
    out.setdefault("consumer_agents", consumers)
    out.setdefault("consumer_agent_refs", consumers)
    out.setdefault("validation_refs", validations)
    out.setdefault("authority_boundary_ref", AUTHORITY_BOUNDARY_REF)
    out.setdefault("execution_authority_ref", EXECUTION_AUTHORITY_REF)
    out.setdefault("blocker_policy_ref", BLOCKER_POLICY_REF)
    out.setdefault("connector_refs_or_future_connector_status", "FUTURE_CONNECTOR_STATUS_ONLY_NO_BIND_WRITE_READ")
    out.setdefault("provenance_tier", provenance_tier)
    out.setdefault("intelligence_classes", stable_unique(intelligence_classes))
    out.setdefault("orphan_flag", False)
    out.setdefault("advisory_only_flag", True)
    out.setdefault("optimized_batch_advisory_only_flag", True)
    out.setdefault("qopt1_batch_is_advisory_only", True)
    for flag in TRUE_AUTHORITY_GUARD_FIELDS:
        out.setdefault(flag, True)
    for flag in FALSE_AUTHORITY_FIELDS:
        if flag != "optimized_batch_advisory_only_flag":
            out.setdefault(flag, False)
    return out


def common_report(
    payload: dict[str, Any],
    *,
    report_name: str,
    owner_agent: str,
    upstream_refs: Iterable[str],
    downstream_refs: Iterable[str],
) -> dict[str, Any]:
    return common_row(
        {"report_name": report_name, "manual_edit_allowed_flag": False, **payload},
        row_id=f"QOPT1_REPORT::{report_name}",
        owner_agent=owner_agent,
        consumer_agents=["CommanderAgent", "GovernanceAgent", "QOPTAgent"],
        upstream_refs=upstream_refs,
        downstream_refs=downstream_refs,
        provenance_tier="QOPT1_COMPACT_REPORT",
        intelligence_classes=("KNOWLEDGE_INTELLIGENCE", "SEARCH_INTELLIGENCE"),
    )
