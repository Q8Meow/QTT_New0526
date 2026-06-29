"""Shared contracts and deterministic JSON helpers for PR168-RP5F."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, getcontext
import json
from pathlib import Path
from typing import Any, Iterable

getcontext().prec = 28

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "docs" / "master_plan" / "generated" / "pr168_rp5f"
GENERATED_REF_PREFIX = "docs/master_plan/generated/pr168_rp5f"

PR_ID = "PR168-RP5F"
BRANCH_NAME = "pr168-rp5f-dynamic-target-order-grid"
BASELINE_SHA_VCS_METADATA_ONLY = "802125895ec0e469bdf8c856178d97805c0b8a9d"
RUN_ID = "PR168_RP5F_DETERMINISTIC_RUN_20260628T120000Z"
CREATED_AT_UTC = "2026-06-28T12:00:00Z"
REPORT_VERSION = "PR168-RP5F-v1.0"
STAGE_PROFILE_ID = "STAGE1_PREDICTION_MARKETS"
MARKET_FAMILY = "PREDICTION_MARKETS"
EXECUTION_AUTHORITY_REF = "RP5F_EXEC_AUTH::DYNAMIC_TARGET_GRID_SEED_HANDOFF_ONLY_NO_ORDER_AUTHORITY"
BLOCKER_POLICY_REF = "RP5F_BLOCKER_POLICY::PRECISE_INVALIDATABLE_DYNAMIC_TARGETS_ONLY"
VALIDATOR_REF = "tools/validate_pr168_rp5f_dynamic_targets.py"

JSON_OUTPUTS = ("art_reg.json",)

REPORT_OUTPUTS = (
    "missing_req.report.json",
    "exec_auth.report.json",
    "to_rp5g.report.json",
    "to_rank4.report.json",
    "to_qopt1.report.json",
    "to_vs2.report.json",
    "to_mem1.report.json",
    "to_orch1.report.json",
    "to_paper.report.json",
    "to_live_dry.report.json",
    "to_shadow.report.json",
    "future.report.json",
    "run_receipt.report.json",
)

JSONL_OUTPUTS = (
    "read_rec.jsonl",
    "in_cons.jsonl",
    "miss_opt.jsonl",
    "self_audit_pre.jsonl",
    "self_audit_post.jsonl",
    "mode_bound.jsonl",
    "blockers.jsonl",
    "params.jsonl",
    "policy_prov.jsonl",
    "master_trace.jsonl",
    "roadmap_trace.jsonl",
    "research_rec.jsonl",
    "source_intake.jsonl",
    "source_value_cand.jsonl",
    "qku_access.jsonl",
    "library_query.jsonl",
    "agent_duty_map.jsonl",
    "owner_audit.jsonl",
    "owner_enable.jsonl",
    "live_shadow_route.jsonl",
    "source_coverage.jsonl",
    "qku_compute_route.jsonl",
    "qku_target_use.jsonl",
    "pm_edge_hints.jsonl",
    "yes_no_parity.jsonl",
    "cross_venue_hints.jsonl",
    "orderbook_imbalance.jsonl",
    "liquidity_decay.jsonl",
    "event_news_hints.jsonl",
    "learning_hooks.jsonl",
    "context_similarity_keys.jsonl",
    "target_failure_taxonomy.jsonl",
    "retest_policy_hints.jsonl",
    "snap_ctx.jsonl",
    "md_truth.jsonl",
    "src_fresh.jsonl",
    "venue_state.jsonl",
    "ctx_filter.jsonl",
    "targets.jsonl",
    "target_disc.jsonl",
    "target_score.jsonl",
    "target_utility.jsonl",
    "target_family.jsonl",
    "event_lifecycle.jsonl",
    "exec_target.jsonl",
    "var_template.jsonl",
    "var_grid.jsonl",
    "var_bounds.jsonl",
    "var_policy.jsonl",
    "grid_frontier.jsonl",
    "frontier_policy.jsonl",
    "vof_grid.jsonl",
    "grid_fdr.jsonl",
    "tca_inputs.jsonl",
    "fill_inputs.jsonl",
    "queue_fill_inputs.jsonl",
    "adverse_select.jsonl",
    "lat_inputs.jsonl",
    "capacity_inputs.jsonl",
    "cash_settle_inputs.jsonl",
    "trade_seed.jsonl",
    "fresh_policy.jsonl",
    "ttl_policy.jsonl",
    "stale_rules.jsonl",
    "snapshot_reval.jsonl",
    "pre_submit_reval.jsonl",
    "no_stale_candidate.jsonl",
    "notrade_hints.jsonl",
    "edge_alpha_inputs.jsonl",
    "regime_sim_hints.jsonl",
    "port_cap.jsonl",
    "champ_prev.jsonl",
    "regime_keys.jsonl",
    "marg_util.jsonl",
    "q_grid.jsonl",
    "q_constraints.jsonl",
    "q_interp.jsonl",
    "classic_fallback.jsonl",
    "agent_route.jsonl",
    "agent_consume.jsonl",
    "artifact_io.jsonl",
    "file_route.jsonl",
    "lineage.jsonl",
    "dag.jsonl",
    "val_lineage.jsonl",
    "orph_art.jsonl",
    "orph_qku.jsonl",
    "no_meta.jsonl",
    "no_mut.jsonl",
    "no_sha.jsonl",
    "no_auth.jsonl",
    "no_hardcode.jsonl",
    "downstream.jsonl",
    "completion_route.jsonl",
    "exec_now_delta_hint.jsonl",
    "edge_capture_map.jsonl",
)

REQUIRED_INPUT_REFS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/generated/PR168_RP5C_FinalSummary.report.json",
    "docs/master_plan/generated/pr168_vs1/vs1_run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5d/rp5d_run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5e/run_receipt.report.json",
    "docs/master_plan/generated/pr168_rp5d_r1/run_receipt.report.json",
    "docs/master_plan/generated/rp5c/immutable_qku_formula_library.jsonl",
    "docs/master_plan/generated/rp5c/immutable_qku_library.jsonl",
    "docs/master_plan/generated/rp5c/immutable_formula_library.jsonl",
    "docs/master_plan/generated/rp5c/formula_ontology.jsonl",
    "docs/master_plan/generated/rp5c/qku_market_applicability_matrix.jsonl",
    "docs/master_plan/generated/rp5c/market_stage_activation_profile_registry.jsonl",
    "docs/master_plan/generated/rp5c/agent_qku_access_policy_registry.jsonl",
    "docs/master_plan/generated/rp5c/stage_agent_qku_universe_resolver.jsonl",
    "tools/pr168_rp5c_library_reader.py",
    "docs/master_plan/generated/pr168_vs1/selected_computable_qku_formula_bindings.jsonl",
    "docs/master_plan/generated/pr168_vs1/temporary_stack_candidate_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/order_variable_candidate_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/tca_breakdown_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/expected_cash_pnl_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/execution_adjusted_ranking_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/champion_challenger_selection_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/quantum_structural_readiness_receipts.jsonl",
    "docs/master_plan/generated/pr168_vs1/paper_intent_candidate_previews.jsonl",
    "docs/master_plan/generated/pr168_vs1/no_orphan_qku_formula_proof.jsonl",
    "docs/master_plan/generated/pr168_vs1/vs1_to_rp5d_rp5e_rp5f_rp5g_rank4_qopt_mem1_agent_orch_handoff.report.json",
    "docs/master_plan/generated/pr168_rp5d/rp5d_artifact_name_registry.json",
    "docs/master_plan/generated/pr168_rp5d/rp5d_comp_materialization.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_contract_bundles.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_exec_tiers.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_computable_universe.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_agent_exec_resolver.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_stage_agent_exec_view.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_adapter_family_registry.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_input_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_formula_pnl_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_unit_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_market_data_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_tca_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_fill_liquidity_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_latency_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_capacity_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_portfolio_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_scenario_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_overfit_fdr_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_no_trade_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_rank_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_champion_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_regime_memory_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_alpha_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_hot_path_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_agent_route_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_quantum_map_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_classical_fb_queue.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_alpha_readiness.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_hot_path_readiness.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_rank_readiness.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_tca_readiness.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_quantum_compat.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_optimizer_readiness.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_artifact_dag.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_no_orphan_qku_formula.jsonl",
    "docs/master_plan/generated/pr168_rp5d/rp5d_future_pr_handoff.report.json",
    "docs/master_plan/generated/pr168_rp5e/art_reg.json",
    "docs/master_plan/generated/pr168_rp5e/ctx_univ.jsonl",
    "docs/master_plan/generated/pr168_rp5e/ctx_pools.jsonl",
    "docs/master_plan/generated/pr168_rp5e/qku_guard.jsonl",
    "docs/master_plan/generated/pr168_rp5e/topk.jsonl",
    "docs/master_plan/generated/pr168_rp5e/edge_feats.jsonl",
    "docs/master_plan/generated/pr168_rp5e/tca_ready.jsonl",
    "docs/master_plan/generated/pr168_rp5e/exec_prev.jsonl",
    "docs/master_plan/generated/pr168_rp5e/capacity.jsonl",
    "docs/master_plan/generated/pr168_rp5e/fdr_ctrl.jsonl",
    "docs/master_plan/generated/pr168_rp5e/port_div.jsonl",
    "docs/master_plan/generated/pr168_rp5e/q_obj.jsonl",
    "docs/master_plan/generated/pr168_rp5e/q_interp.jsonl",
    "docs/master_plan/generated/pr168_rp5e/classic.jsonl",
    "docs/master_plan/generated/pr168_rp5e/unlock_pri.jsonl",
    "docs/master_plan/generated/pr168_rp5e/gap_rank.jsonl",
    "docs/master_plan/generated/pr168_rp5e/triage52.jsonl",
    "docs/master_plan/generated/pr168_rp5e/queue_dedupe.jsonl",
    "docs/master_plan/generated/pr168_rp5e/artifact_io.jsonl",
    "docs/master_plan/generated/pr168_rp5e/file_route.jsonl",
    "docs/master_plan/generated/pr168_rp5e/agent_route.jsonl",
    "docs/master_plan/generated/pr168_rp5e/agent_consume.jsonl",
    "docs/master_plan/generated/pr168_rp5e/downstream.jsonl",
    "docs/master_plan/generated/pr168_rp5e/to_live_dry.report.json",
    "docs/master_plan/generated/pr168_rp5e/to_shadow.report.json",
    "docs/master_plan/generated/pr168_rp5d_r1/art_reg.json",
    "docs/master_plan/generated/pr168_rp5d_r1/exec_now_proof.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/promote.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/nonpromote.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/tier_overlay.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/count_integrity.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/proof_tier.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/contract_matrix.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/calc_smoke.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/promote_audit.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/edge_profit_map.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/artifact_io.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/file_route.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/orph_art.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/orph_qku.jsonl",
    "docs/master_plan/generated/pr168_rp5d_r1/downstream.jsonl",
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
)

OPTIONAL_INPUT_REFS = (
    "docs/master_plan/generated/PR168_RP_RouteTriage.report.json",
    "docs/master_plan/generated/PR168_RP_FullMasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR168_RP_MarketSpecificSectionIndexes.report.json",
    "docs/master_plan/generated/PR168_RP_CommandActionMatrix.report.json",
)

PARAM_DEFAULTS: dict[str, object] = {
    "snapshot_ttl_ms_default": 2500,
    "snapshot_ttl_ms_range": "250..10000",
    "max_targets_per_run_default": 25,
    "max_targets_per_run_range": "5..200",
    "max_grids_per_target_default": 10,
    "max_grid_values_per_variable_default": 7,
    "max_total_seed_rows_default": 500,
    "price_bucket_count_default": 7,
    "size_bucket_count_default": 5,
    "hold_duration_bucket_count_default": 5,
    "entry_offset_ticks_default_values": [-2, -1, 0, 1, 2],
    "spread_filter_default_buckets": ["TIGHT", "NORMAL", "WIDE", "BLOCKED"],
    "liquidity_filter_default_buckets": ["HIGH", "MEDIUM", "LOW", "BLOCKED"],
    "latency_budget_ms_default_values": [100, 250, 500, 1000, 2500],
    "maker_taker_split_default_values": ["MAKER_ONLY", "TAKER_ONLY", "MAKER_THEN_TAKER", "SPLIT_50_50"],
    "exit_rule_default_values": ["HOLD_TO_RESOLUTION", "TAKE_PROFIT", "EDGE_DECAY", "STOP_LOSS", "TIME_STOP"],
    "fdr_grid_family_q_default": "0.10",
    "successive_halving_eta_default": 3,
    "max_persisted_grid_rows_default": 500,
    "use_and_dump_required_default": True,
    "pre_submit_revalidation_required_default": True,
    "yes_no_parity_hint_enabled_default": True,
    "cross_venue_hint_enabled_default": True,
    "orderbook_imbalance_hint_enabled_default": True,
    "liquidity_decay_hint_enabled_default": True,
    "event_news_hint_enabled_default": True,
    "owner_enablement_handoff_required_default": True,
    "qku_compute_route_required_default": True,
    "target_utility_stage1_weight_default": "0.15",
    "target_utility_executable_now_weight_default": "0.15",
    "target_utility_source_freshness_weight_default": "0.10",
    "target_utility_market_truth_weight_default": "0.10",
    "target_utility_execution_readiness_weight_default": "0.15",
    "target_utility_quantum_structural_weight_default": "0.10",
    "target_utility_downstream_rp5g_weight_default": "0.15",
    "target_utility_no_orphan_weight_default": "0.10",
    "adverse_selection_penalty_default": "0.10",
    "queue_fill_proxy_weight_default": "0.10",
    "value_of_information_min_score_default": "0.30",
    "candidate_source_max_rows_default": 100,
    "candidate_source_accepts_non_official_default": True,
    "candidate_source_live_authority_default": False,
    "DEFAULT_COMPUTE_requires_agent_duty_allowed_default": True,
    "AVAILABLE_ON_DEMAND_requires_resolver_receipt_default": True,
}

BLOCKER_CODES = (
    "MISSING_RP5D_R1_EXEC_NOW_OVERLAY",
    "MISSING_RP5E_CONTEXT_POOL",
    "MISSING_RP5E_STACK_PREVIEW",
    "MISSING_MARKET_SNAPSHOT_CONTEXT",
    "MISSING_MARKET_DATA_TRUTH_STATE",
    "MISSING_SOURCE_FRESHNESS_STATE",
    "MISSING_VENUE_OPERATIONAL_STATE",
    "MISSING_ORDER_VARIABLE_DOMAIN",
    "MISSING_TCA_INPUT_SURFACE",
    "MISSING_FILL_LATENCY_CAPACITY_INPUT",
    "MISSING_CASHFLOW_SETTLEMENT_INPUT",
    "MISSING_FRESHNESS_POLICY",
    "MISSING_TTL_POLICY",
    "MISSING_STALE_INVALIDATION_RULE",
    "MISSING_PRE_SUBMIT_REVALIDATION_REQUIREMENT",
    "FIXED_TRADE_PLAN_ATTEMPT",
    "NON_EXPIRING_TRADE_PLAN_ATTEMPT",
    "STALE_CANDIDATE_AUTHORITY_ATTEMPT",
    "FULL_CARTESIAN_GRID_PERSISTENCE_ATTEMPT",
    "METADATA_ONLY_ROW",
    "FORMULA_MUTATION_ATTEMPT",
    "QKU_MUTATION_ATTEMPT",
    "GLOBAL_BAN_ATTEMPT",
    "PAPER_SUBMIT_AUTHORITY_ATTEMPT",
    "LIVE_DRYRUN_EXECUTION_ATTEMPT",
    "SHADOW_AUTHORITY_ATTEMPT",
    "LIMITED_LIVE_CANARY_ATTEMPT",
    "LIVE_AUTHORITY_ATTEMPT",
    "CONNECTOR_WRITE_ATTEMPT",
    "PRIVATE_STATE_FETCH_ATTEMPT",
    "CASH_ACCOUNT_READ_ATTEMPT",
    "PROFIT_PROOF_ATTEMPT",
    "FINAL_RANK_ATTEMPT",
    "CHAMPION_SELECTION_ATTEMPT",
    "QOPT_EXECUTION_ATTEMPT",
    "QUANTUM_BACKEND_ATTEMPT",
    "PROPRIETARY_DEFAULT_CLAIM_ATTEMPT",
    "CONFIDENTIAL_INPUT_ATTEMPT",
    "QTT_SHA_AUTHORITY_ATTEMPT",
    "ATOMICROWS_SHA_REF_ATTEMPT",
    "ORPHAN_ARTIFACT_ATTEMPT",
    "HARDCODED_THRESHOLD_ATTEMPT",
)

FALSE_FLAG_FIELDS = (
    "metadata_is_proof_flag",
    "accepted_source_fact_flag",
    "paper_authority_flag",
    "shadow_authority_flag",
    "live_authority_flag",
    "order_authority_flag",
    "profit_proof_flag",
    "qopt_execution_flag",
    "quantum_backend_execution_flag",
    "quantum_advantage_claim_flag",
    "proprietary_claim_flag",
    "qtt_sha_authority_flag",
    "atomicrows_sha_ref_flag",
    "paper_submit_authority_flag",
    "connector_write_flag",
    "private_state_fetch_flag",
    "cash_account_read_flag",
    "formula_mutation_flag",
    "formula_deletion_flag",
    "qku_mutation_flag",
    "qku_deletion_flag",
    "global_ban_flag",
)

FORBIDDEN_STATE_VALUES = (
    "REAL_POSITIVE",
    "REAL_NEGATIVE",
    "CHAMPION",
    "LIVE_CANDIDATE",
    "ORDER_READY",
    "FINAL_TRADE_RANK",
    "PROFIT_PROVEN",
    "QUANTUM_ADVANTAGE_PROVEN",
    "PAPER_ORDER_SUBMIT_READY",
    "SHADOW_EXECUTABLE_NOW",
    "LIVE_EXECUTABLE_NOW",
    "ORDER_SUBMIT_READY",
    "BUY_SELL_OPEN_CLOSE_READY",
    "CONNECTOR_WRITE_READY",
    "PRIVATE_STATE_READY",
    "CASH_ACCOUNT_READY",
    "LIVE_DRYRUN_EXECUTION_READY",
    "LIMITED_LIVE_CANARY_READY",
    "FIXED_TRADE_PLAN",
    "NON_EXPIRING_TRADE_PLAN",
    "STALE_CANDIDATE_APPROVED",
)


@dataclass(frozen=True)
class CommonEnvelopeV1:
    schema_version: str = REPORT_VERSION
    row_id: str = ""
    run_id: str = RUN_ID
    created_at_utc: str = CREATED_AT_UTC
    source_pr: str = PR_ID
    upstream_refs: tuple[str, ...] = ()
    downstream_refs: tuple[str, ...] = ()
    owner_agent: str = ""
    consumer_agents: tuple[str, ...] = ()
    validation_refs: tuple[str, ...] = (VALIDATOR_REF,)
    execution_authority_ref: str = EXECUTION_AUTHORITY_REF
    blocker_policy_ref: str = BLOCKER_POLICY_REF
    connector_refs_or_future_connector_status: str = "FUTURE_CONNECTOR_STATUS_ONLY_NO_WRITE"
    provenance_tier: str = "RP5F_DYNAMIC_TARGET_GRID_SEED_NOT_PROOF"


ROW_MODEL_NAMES = (
    "MasterPlanTraceV1",
    "RoadmapTraceV1",
    "QKUAccessModeV1",
    "LibraryQueryReceiptV1",
    "AgentDutyMapV1",
    "SourceIntakeCandidateV1",
    "MarketSnapshotContextV1",
    "MarketDataTruthStateV1",
    "SourceFreshnessStateV1",
    "VenueOperationalStateV1",
    "DynamicTradeTargetV1",
    "TradeTargetDiscoveryReceiptV1",
    "TargetScoringPreviewV1",
    "TargetUtilitySurfaceV1",
    "TargetFamilyClassificationV1",
    "EventLifecycleStateV1",
    "ExecutionTargetReadinessV1",
    "OrderVariableGridTemplateV1",
    "EphemeralOrderVariableGridV1",
    "VariableBoundsPolicyV1",
    "GridFrontierControlV1",
    "GridFDRControlV1",
    "FrontierPolicyV1",
    "ValueOfInformationGridV1",
    "TCAInputReadinessV1",
    "FillLatencyCapacityInputV1",
    "QueueFillInputSurfaceV1",
    "AdverseSelectionInputSurfaceV1",
    "CashflowSettlementInputV1",
    "SnapshotConditionedTradePlanSeedV1",
    "TradePlanFreshnessPolicyV1",
    "TradePlanTTLPolicyV1",
    "StaleCandidateInvalidationV1",
    "SnapshotRevalidationMatrixV1",
    "PreSubmitRevalidationRequirementV1",
    "NoStaleCandidateProofV1",
    "NoTradeHintV1",
    "EdgeAlphaInputSurfaceV1",
    "RegimeSimulationHintV1",
    "PortfolioCapacityContextV1",
    "ChampionChallengerTargetPreviewV1",
    "RegimeMemoryKeyV1",
    "MarginalUtilityInputSurfaceV1",
    "QuantumGridEncodingReadinessV1",
    "QuantumConstraintReadinessV1",
    "QuantumInterpretBackMapV1",
    "ClassicalFallbackGridOptimizerReadinessV1",
    "CompletionRouteV1",
    "ExecutableNowDeltaHintV1",
    "ArtifactIOMatrixV1",
    "FileRouteRegistryV1",
    "OwnerAuditAnswerV1",
    "OwnerEnablementHandoffV1",
    "LiveShadowFutureRouteV1",
    "SourceCoverageReceiptV1",
    "QKUComputeRouteV1",
    "QKUTargetUseV1",
    "PredictionMarketEdgeHintV1",
    "YesNoParityHintV1",
    "CrossVenueHintV1",
    "OrderbookImbalanceHintV1",
    "LiquidityDecayHintV1",
    "EventNewsHintV1",
    "LearningHookV1",
    "ContextSimilarityKeyV1",
    "TargetFailureTaxonomyV1",
    "RetestPolicyHintV1",
)


def _make_row_model(name: str) -> type[CommonEnvelopeV1]:
    cls = type(name, (CommonEnvelopeV1,), {"__module__": __name__})
    return dataclass(frozen=True)(cls)


for _row_model_name in ROW_MODEL_NAMES:
    globals()[_row_model_name] = _make_row_model(_row_model_name)


def dec(value: str | int | float | Decimal) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def score(value: str | int | float | Decimal) -> str:
    return str(dec(value).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def rel_ref(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        p = p.relative_to(REPO_ROOT)
    return p.as_posix()


def generated_ref(filename: str) -> str:
    return f"{GENERATED_REF_PREFIX}/{filename}"


def manifest_name(filename: str) -> str:
    return f"{Path(filename).stem}.manifest.json"


def all_artifact_filenames(include_manifests: bool = True) -> tuple[str, ...]:
    base = tuple(dict.fromkeys((*JSON_OUTPUTS, *REPORT_OUTPUTS, *JSONL_OUTPUTS)))
    if not include_manifests:
        return base
    manifests = tuple(manifest_name(name) for name in JSONL_OUTPUTS)
    return tuple(dict.fromkeys((*base, *manifests)))


def stable_json(payload: Any, *, compact: bool = False) -> str:
    separators = (",", ":") if compact else None
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=None if compact else 2, separators=separators) + "\n"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


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


def with_common(
    row: dict[str, Any],
    *,
    row_id: str,
    owner_agent: str,
    consumer_agents: Iterable[str],
    upstream_refs: Iterable[str],
    downstream_refs: Iterable[str],
    validation_refs: Iterable[str] = (VALIDATOR_REF,),
    blocker_policy_ref: str = BLOCKER_POLICY_REF,
    execution_authority_ref: str = EXECUTION_AUTHORITY_REF,
    provenance_tier: str = "RP5F_DYNAMIC_TARGET_GRID_SEED_NOT_PROOF",
) -> dict[str, Any]:
    upstream = stable_unique(upstream_refs)
    downstream = stable_unique(downstream_refs)
    consumers = stable_unique(consumer_agents)
    validation = stable_unique(validation_refs)
    out = dict(row)
    out.setdefault("schema_version", REPORT_VERSION)
    out.setdefault("row_id", row_id)
    out.setdefault("run_id", RUN_ID)
    out.setdefault("created_at_utc", CREATED_AT_UTC)
    out.setdefault("source_pr", PR_ID)
    out.setdefault("upstream_refs", upstream)
    out.setdefault("downstream_refs", downstream)
    out.setdefault("owner_agent", owner_agent)
    out.setdefault("consumer_agents", consumers)
    out.setdefault("validation_refs", validation)
    out.setdefault("execution_authority_ref", execution_authority_ref)
    out.setdefault("blocker_policy_ref", blocker_policy_ref)
    out.setdefault("connector_refs_or_future_connector_status", "FUTURE_CONNECTOR_STATUS_ONLY_NO_WRITE")
    out.setdefault("provenance_tier", provenance_tier)
    for flag in FALSE_FLAG_FIELDS:
        out.setdefault(flag, False)
    out.setdefault("candidate_only_flag", False)
    out.setdefault("orphan_flag", False)
    out.setdefault("fixed_trade_instruction_flag", False)
    out.setdefault("non_expiring_trade_plan_flag", False)
    out.setdefault("stale_candidate_authority_flag", False)
    out.setdefault("producer_agent", owner_agent)
    out.setdefault("consumer_agent_refs", consumers)
    out.setdefault("upstream_artifact_refs", upstream)
    out.setdefault("downstream_artifact_refs", downstream)
    return out


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]], *, schema_version_name: str) -> None:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(stable_json(row, compact=True) for row in materialized), encoding="utf-8")
    manifest = with_common(
        {
            "manifest_id": f"{path.stem.upper()}_MANIFEST",
            "physical_filename": rel_ref(path),
            "schema_version_name": schema_version_name,
            "row_count": len(materialized),
            "shard_file_path": rel_ref(path),
            "generated_surface_authority_class": "RP5F_GENERATED_DYNAMIC_TARGET_GRID_SEED_NOT_SOURCE_TRUTH",
        },
        row_id=f"{path.stem.upper()}_MANIFEST",
        owner_agent="GovernanceAgent",
        consumer_agents=["RP5FValidator", "ArtifactNameAgent", "PathSafetyAgent"],
        upstream_refs=[generated_ref(path.name)],
        downstream_refs=[generated_ref("run_receipt.report.json")],
    )
    write_json(path.with_name(manifest_name(path.name)), manifest)


def schema_name(filename: str) -> str:
    stem = filename.removesuffix(".jsonl").removesuffix(".json").replace(".report", "")
    return "".join(part.capitalize() for part in stem.split("_") if part) + "V1"
