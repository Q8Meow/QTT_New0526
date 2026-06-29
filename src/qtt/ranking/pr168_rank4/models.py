"""Shared contracts and deterministic JSON helpers for PR168-RANK4."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP, getcontext
import json
from pathlib import Path
from typing import Any, Iterable

getcontext().prec = 28

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rank4"
GENERATED_REF_PREFIX = "docs/master_plan/generated/pr168_rank4"
UPSTREAM_RP5G_REF_PREFIX = "docs/master_plan/generated/pr168_rp5g"

PR_ID = "PR168-RANK4"
BRANCH_NAME = "pr168-rank4-exec-advisory-ranking"
RUN_ID = "PR168_RANK4_DETERMINISTIC_RUN_20260629T180000Z"
CREATED_AT_UTC = "2026-06-29T18:00:00Z"
REPORT_VERSION = "PR168-RANK4-v1.0"
EXECUTION_AUTHORITY_REF = "RANK4_EXEC_AUTH::ADVISORY_RANKING_ONLY_NO_ORDER_AUTHORITY"
AUTHORITY_BOUNDARY_REF = "RANK4_AUTH_BOUNDARY::NO_FINAL_CHAMPION_NO_PAPER_NO_LIVE_NO_CONNECTOR_NO_QOPT_EXECUTION"
BLOCKER_POLICY_REF = "RANK4_BLOCKER_POLICY::NUMERIC_RP5G_EVIDENCE_AND_NON_AUTHORITY_HANDOFF_ONLY"
VALIDATOR_REF = "tools/validate_pr168_rank4_advisory_ranking.py"
PRODUCER_TOOL = "tools/build_pr168_rank4_advisory_ranking.py"
BASELINE_MAIN_HEAD = "56086abc0ae1d918b4ef3898e7f6f12a7ef755c3"

JSON_OUTPUTS = ("art_reg.json",)
MARKDOWN_OUTPUTS = ("pr_body.md",)

REPORT_OUTPUTS = (
    "missing_req.report.json",
    "run_receipt.report.json",
    "input_consumption.report.json",
    "ranking_summary.report.json",
    "champ_chall.report.json",
    "qopt_handoff.report.json",
    "vs2_handoff.report.json",
    "mem1_handoff.report.json",
    "rank4_to_mem1_recipe_handoff.report.json",
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
    "rank_edge_capture.jsonl",
    "rank_obj_decomp.jsonl",
    "rank4_qku_rankability.jsonl",
    "rank4_formula_rankability.jsonl",
    "rank4_candidate_rankability.jsonl",
    "rank_input.jsonl",
    "elig_gate.jsonl",
    "rank_feat.jsonl",
    "score_norm.jsonl",
    "score_comp.jsonl",
    "rank_score.jsonl",
    "rank_order.jsonl",
    "rank_explain.jsonl",
    "rank_tie_break.jsonl",
    "pareto_frontier.jsonl",
    "dominance.jsonl",
    "rank_dominance_explain.jsonl",
    "notrade_rank.jsonl",
    "tca_rank.jsonl",
    "fill_lat_rank.jsonl",
    "capacity_rank.jsonl",
    "port_div_rank.jsonl",
    "marg_util_rank.jsonl",
    "near_clone_cluster.jsonl",
    "fdr_rank.jsonl",
    "search_family_rank.jsonl",
    "false_discovery_rank_audit.jsonl",
    "scenario_rank.jsonl",
    "calib_rank.jsonl",
    "voi_rank.jsonl",
    "retest_rank.jsonl",
    "repair_rank.jsonl",
    "mem_keys.jsonl",
    "rank_context_signature.jsonl",
    "rank_similarity_key.jsonl",
    "rank_memory_recipe_handoff.jsonl",
    "rank_winner_attribution.jsonl",
    "rank_memory_candidate.jsonl",
    "rank_recipe_prior_score.jsonl",
    "rank_recipe_batch_policy.jsonl",
    "rank_negative_memory_hint.jsonl",
    "rank_recipe_drift_hint.jsonl",
    "rank_retest_priority.jsonl",
    "rank_two_speed_hint.jsonl",
    "rank_realization_receipt_req.jsonl",
    "rank_qmemory_handoff.jsonl",
    "rank_ext_cand_intake.jsonl",
    "rank_model_risk.jsonl",
    "rank_uncert_reserve.jsonl",
    "rank_oos_lockbox_hint.jsonl",
    "rank_bandit_alloc_hint.jsonl",
    "rank_ope_hint.jsonl",
    "rank_reward_decomp.jsonl",
    "rank_live_ladder.jsonl",
    "rank_latency_sla.jsonl",
    "rank_cross_market_hint.jsonl",
    "rank_tradeplan_lifecycle.jsonl",
    "rank_decision_intel_map.jsonl",
    "rank_mem1_contract_hint.jsonl",
    "rank_constraint_tightness.jsonl",
    "rank_snapshot_reval_plan.jsonl",
    "rank_auto_trading_path.jsonl",
    "rank_source_rights.jsonl",
    "rank_recipe_cred_tier.jsonl",
    "rank_recipe_ttl_retest.jsonl",
    "rank_next_action.jsonl",
    "rank_user_conn_route.jsonl",
    "rank_shadow_route.jsonl",
    "rank_llm_non_authority.jsonl",
    "rank_learning_loop_contract.jsonl",
    "rank_access_mode.jsonl",
    "rank_stack_synergy.jsonl",
    "rank_rank_stability.jsonl",
    "rank_sensitivity_surface.jsonl",
    "rank_micro_regime.jsonl",
    "rank_tail_guard.jsonl",
    "rank_port_basket.jsonl",
    "rank_hotpath.jsonl",
    "champ_prev.jsonl",
    "chall_prev.jsonl",
    "chall_reason.jsonl",
    "qrank_feat.jsonl",
    "qrank_score.jsonl",
    "qopt_batch.jsonl",
    "qopt_frontier.jsonl",
    "qopt_constraints.jsonl",
    "qopt_interpret_back_rank_map.jsonl",
    "vs2_handoff.jsonl",
    "mem1_handoff.jsonl",
    "orch1_handoff.jsonl",
    "paper_handoff.jsonl",
    "live_dry_handoff.jsonl",
    "shadow_handoff.jsonl",
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
    "rank_auth_block.jsonl",
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
    "docs/master_plan/generated/pr168_rp5g/orph_art.jsonl",
    "docs/master_plan/generated/pr168_rp5g/orph_qku.jsonl",
    "docs/master_plan/generated/pr168_rp5g/downstream.jsonl",
    "docs/master_plan/generated/pr168_rp5g/completion_route.jsonl",
    "docs/master_plan/generated/pr168_rp5g/rank4_handoff.report.json",
    "docs/master_plan/generated/pr168_rp5g/qopt1_handoff.report.json",
    "docs/master_plan/generated/pr168_rp5g/vs2_handoff.report.json",
    "docs/master_plan/generated/pr168_rp5g/mem1_handoff.report.json",
    "docs/master_plan/generated/pr168_rp5g/orch1_handoff.report.json",
    "docs/master_plan/generated/pr168_rp5g/paper_handoff.report.json",
    "docs/master_plan/generated/pr168_rp5g/live_dry_handoff.report.json",
    "docs/master_plan/generated/pr168_rp5g/shadow_handoff.report.json",
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
)

OPTIONAL_INPUT_REFS = (
    "docs/master_plan/generated/pr168_rp5g/owner_q1_edge.jsonl",
    "docs/master_plan/generated/pr168_rp5g/owner_q2_route.jsonl",
    "docs/master_plan/generated/pr168_rp5g/owner_q3_auto_path.jsonl",
    "docs/master_plan/generated/pr168_rp5g/institutional_default_cand.jsonl",
    "docs/master_plan/generated/pr168_rp5g/nonofficial_cand.jsonl",
    "docs/master_plan/generated/pr168_rp5g/model_risk.jsonl",
    "docs/master_plan/generated/pr168_rp5g/lockbox.jsonl",
    "docs/master_plan/generated/pr168_rp5g/near_clone_cluster.jsonl",
    "docs/master_plan/generated/pr168_rp5g/pm_microstructure.jsonl",
)

PARAM_DEFAULTS: dict[str, Decimal | int] = {
    "score_weight_net_expected_pnl_default": Decimal("0.18"),
    "score_weight_lcb_default": Decimal("0.16"),
    "score_weight_no_trade_margin_default": Decimal("0.12"),
    "score_weight_fill_probability_default": Decimal("0.08"),
    "score_weight_latency_quality_default": Decimal("0.06"),
    "score_weight_capacity_quality_default": Decimal("0.08"),
    "score_weight_portfolio_marginal_utility_default": Decimal("0.08"),
    "score_weight_scenario_robustness_default": Decimal("0.06"),
    "score_weight_calibration_quality_default": Decimal("0.04"),
    "score_weight_data_provenance_quality_default": Decimal("0.04"),
    "score_weight_agent_no_orphan_quality_default": Decimal("0.04"),
    "score_weight_quantum_structural_handoff_default": Decimal("0.03"),
    "score_weight_paper_readiness_default": Decimal("0.03"),
    "fdr_q_default": Decimal("0.10"),
    "lcb_z_one_sided_default": Decimal("1.645"),
    "lcb_z_conservative_default": Decimal("1.96"),
    "min_fill_probability_for_champion_preview_default": Decimal("0.50"),
    "min_fill_probability_for_learning_retest_default": Decimal("0.35"),
    "max_candidate_per_market_cluster_topK_default": 2,
    "max_candidate_per_event_cluster_topK_default": 2,
    "max_formula_family_share_topK_default": Decimal("0.40"),
    "max_venue_share_topK_default": Decimal("0.60"),
    "near_clone_similarity_threshold_default": Decimal("0.85"),
    "value_of_information_min_score_default": Decimal("0.30"),
    "successive_halving_eta_default": 3,
    "min_portfolio_utility_for_champion_preview_default": Decimal("-0.050000"),
    "max_capacity_crowding_penalty_cash_default": Decimal("0.500000"),
    "max_calibration_gap_default": Decimal("0.050000"),
    "lcb_min_cash_default": Decimal("0.000000"),
}

FALSE_AUTHORITY_FIELDS = (
    "final_champion_selected_flag",
    "final_trade_rank_for_execution_flag",
    "paper_order_intent_created_flag",
    "paper_submit_authority_created_flag",
    "live_authority_created_flag",
    "connector_write_created_flag",
    "private_state_read_created_flag",
    "cash_account_read_created_flag",
    "qopt_execution_flag",
    "quantum_backend_execution_flag",
    "quantum_advantage_claim_flag",
    "profit_guarantee_flag",
    "memory_prior_as_current_profit_proof_flag",
    "durable_MEM1_storage_created_flag",
    "MEM1_query_api_created_flag",
    "exit_sell_close_authority_created_flag",
    "realized_pnl_receipt_created_flag",
    "external_candidate_as_source_fact_flag",
    "non_official_value_as_live_default_flag",
    "contextual_bandit_runtime_policy_created_flag",
    "off_policy_evaluation_as_profit_proof_flag",
    "live_canary_promotion_created_by_rank4_flag",
    "shadow_execution_authority_created_by_rank4_flag",
    "constraint_tightness_fabricated_flag",
    "source_rights_restricted_input_accepted_flag",
    "LLM_rank_proof_without_numeric_evidence_flag",
    "auto_trading_path_treated_as_current_authority_flag",
    "qTT_SHA_authority_created_flag",
    "atomicrows_hash_authority_created_flag",
    "metadata_is_proof_flag",
    "accepted_source_fact_flag",
    "paper_authority_flag",
    "paper_submit_authority_flag",
    "shadow_authority_flag",
    "live_submit_authority_flag",
    "order_authority_flag",
    "profit_proof_flag",
    "qtt_sha_authority_flag",
    "atomicrows_sha_ref_flag",
    "connector_write_flag",
    "private_state_fetch_flag",
    "cash_account_read_flag",
    "formula_mutation_flag",
    "formula_deletion_flag",
    "qku_mutation_flag",
    "qku_deletion_flag",
    "global_ban_flag",
    "source_fact_acceptance_flag",
    "connector_semantic_binding_flag",
    "live_default_flag",
    "real_order_authority_created_flag",
    "paper_order_authority_created_flag",
    "live_order_authority_created_flag",
    "buy_sell_open_close_logic_created_flag",
    "buy_sell_open_close_created_flag",
    "live_or_shadow_authority_created_flag",
    "order_authority_created_flag",
    "runtime_authority_created_flag",
    "live_submit_ready_flag",
    "paper_submit_ready_flag",
    "order_submit_ready_flag",
    "real_market_profit_proof_flag",
    "real_market_loss_proof_flag",
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
    "SHADOW_EXECUTABLE_NOW",
    "LIVE_EXECUTABLE_NOW",
    "BUY_SELL_OPEN_CLOSE_READY",
    "EXIT_SELL_CLOSE_AUTHORITY",
    "REALIZED_PNL_RECEIPT_CREATED",
    "DURABLE_MEM1_STORAGE_CREATED",
    "MEM1_QUERY_API_CREATED",
    "RECIPE_PERMANENT_PROFITABILITY_CLAIM",
    "MEMORY_PRIOR_AS_CURRENT_PROFIT_PROOF",
    "EXTERNAL_CANDIDATE_AS_ACCEPTED_SOURCE_FACT",
    "NON_OFFICIAL_VALUE_AS_LIVE_DEFAULT",
    "CONTEXTUAL_BANDIT_RUNTIME_POLICY_CONTROL",
    "OFF_POLICY_EVALUATION_AS_PROFIT_PROOF",
    "LIVE_CANARY_PROMOTION_CREATED_BY_RANK4",
    "LLM_RANK_PROOF_WITHOUT_NUMERIC_EVIDENCE",
    "SOURCE_FACT_ACCEPTED",
    "CONNECTOR_SEMANTIC_BOUND",
    "QOPT_EXECUTED",
    "QUANTUM_BACKEND_EXECUTED",
)

RESEARCH_SOURCES = (
    ("https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/trading-costs-and-electronic-markets", "CFA Institute trading costs and electronic markets", "RESEARCH", "TCA", "implementation shortfall and transaction-cost attribution candidates"),
    ("https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/trade-strategy-execution", "CFA Institute trade strategy execution", "RESEARCH", "TCA", "execution strategy, opportunity cost, and implementation shortfall candidates"),
    ("https://www.jstor.org/stable/2346101", "Benjamini-Hochberg false discovery rate", "PAPER", "FDR", "multiple-testing adjusted ranking control"),
    ("https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551", "The deflated Sharpe ratio", "PAPER", "OVERFIT", "selection-bias correction candidate only when inputs support it"),
    ("https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253", "The probability of backtest overfitting", "PAPER", "OVERFIT", "backtest-overfitting control completion route"),
    ("https://scikit-learn.org/stable/modules/grid_search.html", "scikit-learn successive halving", "DOC", "SEARCH", "resource allocation and VOI search hint"),
    ("https://qiskit-community.github.io/qiskit-optimization/stubs/qiskit_optimization.QuadraticProgram.html", "Qiskit QuadraticProgram", "DOC", "QUANTUM_STRUCTURE", "QuadraticProgram structure and interpret-back candidate"),
    ("https://qiskit-community.github.io/qiskit-optimization/tutorials/02_converters_for_quadratic_programs.html", "Qiskit converters for QuadraticPrograms", "DOC", "QUANTUM_STRUCTURE", "QUBO conversion structural candidate"),
    ("https://docs.dwavequantum.com/en/latest/concepts/models.html", "D-Wave Ocean model concepts", "DOC", "QUANTUM_STRUCTURE", "BQM/CQM/QUBO structural candidate"),
    ("https://docs.kalshi.com/api-reference/market/get-market-orderbook", "Kalshi market orderbook API", "OFFICIAL_DOC", "VENUE_CANDIDATE", "yes/no orderbook microstructure candidate surface"),
    ("https://docs.polymarket.com/developers/CLOB/introduction", "Polymarket CLOB API documentation", "OFFICIAL_DOC", "VENUE_CANDIDATE", "CLOB orderbook microstructure candidate surface"),
    ("https://www.interactivebrokers.com/campus/ibkr-api-page/event-contracts/", "Interactive Brokers event contracts API", "OFFICIAL_DOC", "VENUE_CANDIDATE", "ForecastEx/IBKR event-contract candidate surface"),
    ("https://arxiv.org/abs/1406.2294", "Limit order book queue and adverse selection research", "PAPER", "FILL_QUEUE", "queue position and adverse-selection model candidates"),
    ("https://arxiv.org/abs/1803.00943", "Doubly robust off-policy evaluation for contextual bandits", "PAPER", "OPE_BANDIT", "future OPE and exploration-allocation hint"),
    ("https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm", "Federal Reserve SR 11-7 model risk management", "OFFICIAL_GUIDANCE", "MODEL_RISK", "model-risk and validation control candidates"),
)

SELF_AUDIT_FLAWS = (
    ("flaw_01_RP5G_simulation_rank_preview_is_not_RANK4_advisory_rank", "rank_order.jsonl"),
    ("flaw_02_RP5G_champion_preview_has_no_final_authority", "champ_prev.jsonl"),
    ("flaw_03_scalar_score_alone_can_hide_dominated_candidates", "pareto_frontier.jsonl"),
    ("flaw_04_raw_PnL_can_overselect_thin_book_false_positives", "fill_lat_rank.jsonl"),
    ("flaw_05_topK_can_be_near_duplicate_cluster", "port_div_rank.jsonl"),
    ("flaw_06_multiple_testing_can_select_overfit_candidate", "fdr_rank.jsonl"),
    ("flaw_07_no_trade_can_be_misread_as_global_blocker", "notrade_rank.jsonl"),
    ("flaw_08_quantum_compatible_labels_can_pass_without_useful_QOPT_batch_priority", "qopt_batch.jsonl"),
    ("flaw_09_generated_values_can_orphan_downstream", "value_route.jsonl"),
    ("flaw_10_RANK4_can_accidentally_create_order_authority", "rank_auth_block.jsonl"),
    ("flaw_11_winning_combo_memory_can_be_misread_as_current_profit_proof", "rank_memory_recipe_handoff.jsonl"),
    ("flaw_12_historical_winners_can_overfit_or_decay", "rank_recipe_prior_score.jsonl"),
    ("flaw_13_RANK4_memory_handoff_can_accidentally_become_MEM1_storage", "rank_mem1_contract_hint.jsonl"),
    ("flaw_14_live_profit_materialization_can_be_misread_as_rank_selection", "rank_realization_receipt_req.jsonl"),
    ("flaw_15_memory_batch_can_exploit_only_old_winners", "rank_recipe_batch_policy.jsonl"),
)

INTELLIGENCE_CLASSES = (
    "KNOWLEDGE_INTELLIGENCE",
    "SEARCH_INTELLIGENCE",
    "SIMULATION_INTELLIGENCE",
    "LEARNING_INTELLIGENCE",
    "REASONING_INTELLIGENCE",
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
    }
    for flag in FALSE_AUTHORITY_FIELDS:
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
    provenance_tier: str = "RANK4_ADVISORY_RANKING_EVIDENCE",
    intelligence_classes: Iterable[str] = ("SIMULATION_INTELLIGENCE",),
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
    for flag in FALSE_AUTHORITY_FIELDS:
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
        {
            "report_name": report_name,
            "manual_edit_allowed_flag": False,
            **payload,
        },
        row_id=f"RANK4_REPORT::{report_name}",
        owner_agent=owner_agent,
        consumer_agents=["CommanderAgent", "GovernanceAgent", "RankerAgent"],
        upstream_refs=upstream_refs,
        downstream_refs=downstream_refs,
        provenance_tier="RANK4_COMPACT_REPORT",
        intelligence_classes=("KNOWLEDGE_INTELLIGENCE", "SIMULATION_INTELLIGENCE"),
    )

