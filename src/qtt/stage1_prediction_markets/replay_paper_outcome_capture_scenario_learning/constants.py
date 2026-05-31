"""Central PR161E constants and authority boundaries.

PR161E creates deterministic replay/paper result capture surfaces and candidate
learning bridges. It does not execute replay, paper, optimizers, quantum
backends, simulators, live trading, or create profit evidence without validated
result packets.
"""

from __future__ import annotations

from pathlib import Path


PR_LABEL = "PR161E"
SEMANTIC_TASK_LABEL = (
    "PR161E — Replay/Paper Outcome Capture and Scenario Learning Bridge"
)
EXPECTED_BRANCH = "pr161e-replay-paper-outcome-capture-scenario-learning-bridge"
SUCCESS_MARKER = (
    "QTT_PR161E_REPLAY_PAPER_OUTCOME_CAPTURE_SCENARIO_LEARNING_OK"
)

PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "replay_paper_outcome_capture_scenario_learning"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr161e_replay_paper_outcome_capture_shards"
SHARD_MANIFEST_REPORT_PATH = GENERATED_DIR / "PR161E_ReportShardManifest.report.json"
SHARED_DICTIONARY_REPORT_FILENAME = "PR161E_SharedDictionary.report.json"
SHARED_DICTIONARY_REPORT_PATH = GENERATED_DIR / SHARED_DICTIONARY_REPORT_FILENAME
MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")
PR152_AUDIT_REPORT_PATH = (
    GENERATED_DIR / "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
)
GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES = 50 * 1024 * 1024
REPORT_SHARD_RECORD_TARGET = 5000
REPORT_SHARD_BYTE_THRESHOLD = 1 * 1024 * 1024
REPORT_SHARD_PREVIEW_RECORD_LIMIT = 0

EXPECTED_PR161C_COUNTS = {
    "primary_qku_count": 9360,
    "graph_node_count": 9360,
    "graph_edge_count": 60375,
    "isolated_non_rejected_nodes": 0,
    "quantum_applicable_primary_qkus": 4525,
    "range_qkus_materialized": 388,
    "optimizer_configs_materialized": 106,
}
EXPECTED_PR161D_COUNTS = {
    "qkus_scored": 9360,
    "category_ranking_records": 255941,
    "result_backed_ranking_slots": 9360,
    "scenario_outcome_matrix_records": 1861,
    "order_condition_scenario_records": 1861,
    "bundle_candidates": 1861,
    "replay_paper_scenario_records": 9360,
    "quantum_priority_queue_records": 4525,
    "classical_baseline_queue_records": 9360,
    "hybrid_arbitration_queue_records": 4525,
    "atomicrows_compatibility_priority_records": 4183,
    "pr154_compatibility_priority_records": 342,
    "combined_atomicrows_pr154_compatibility_records": 4525,
    "agent_task_queue_records": 87461,
    "owner_review_queue_records": 9149,
}
DETERMINISTIC_PENDING_COUNTS = {
    "outcome_capture_registry": 9360,
    "bundle_result_ledger": 1861,
    "profitability_ledger": 9360,
    "scenario_result_attribution": 1861,
    "result_backed_ranking_update_candidates": 9360,
    "future_profitability_pattern_update_candidates": 1861,
    "quantum_classical_hybrid_outcome_comparison": 4525,
    "atomicrows_pr154_result_compatibility_bridge": 4525,
    "agent_outcome_task_queue": 87461,
    "owner_review_result_promotion_queue": 9149,
}

OWNER_APPROVALS = {
    "OWNER_GLOBAL_AUTHORITY": True,
    "OWNER_AUTHORIZES_PR161E_IMPLEMENTATION": True,
    "OWNER_AUTHORIZES_CODEX_ONLINE_SEARCH_FOR_QTT_CANDIDATE_INTAKE": True,
    "OWNER_APPROVES_PR161E_REPLAY_PAPER_OUTCOME_CAPTURE_BRIDGE": True,
    "OWNER_APPROVES_PR161E_SCENARIO_LEARNING_BRIDGE": True,
    "OWNER_APPROVES_QKU_SCENARIO_OUTCOME_UPDATE_BRIDGE": True,
    "OWNER_APPROVES_QKU_BUNDLE_RESULT_LEDGER": True,
    "OWNER_APPROVES_QKU_REPLAY_PAPER_PROFITABILITY_LEDGER": True,
    "OWNER_APPROVES_QKU_SCENARIO_RESULT_ATTRIBUTION": True,
    "OWNER_APPROVES_RESULT_BACKED_RANKING_UPDATE_CANDIDATE_BRIDGE": True,
    "OWNER_APPROVES_FUTURE_PROFITABILITY_PATTERN_UPDATE_CANDIDATE_BRIDGE": True,
    "OWNER_APPROVES_REPLAY_PAPER_AS_PROFIT_FILTER": True,
    "OWNER_APPROVES_OWNER_LIVE_PROMOTION_CONTROL": True,
    "OWNER_APPROVES_NON_OFFICIAL_SOURCE_INTAKE_FOR_CANDIDATE_USE": True,
    "OWNER_REMOVES_OFFICIAL_SOURCE_ONLY_RESTRICTION_FOR_RESEARCH_AND_CANDIDATE_LANES": True,
    "OWNER_APPROVES_QUANTUM_CLASSICAL_HYBRID_OUTCOME_COMPARISON_BRIDGE": True,
    "OWNER_APPROVES_QKU_UPSTREAM_DOWNSTREAM_TRACEABILITY_REQUIRED": True,
    "OWNER_APPROVES_ATOMICROWS_PR154_RESULT_COMPATIBILITY_BRIDGE": True,
    "OWNER_APPROVES_DETERMINISTIC_PENDING_SURFACES_WHEN_NO_RESULTS_EXIST": True,
    "OWNER_APPROVES_MISSING_VALUE_CANDIDATE_MATERIALIZATION": True,
    "OWNER_FORBIDS_QTT_SHA_AUTHORITY": True,
    "OWNER_FORBIDS_QTT_GENERATED_SHA_AUTHORITY": True,
    "OWNER_FORBIDS_QTT_FREEZE_CHECKSUM_GLOBAL_DIGEST_AUTHORITY": True,
    "OWNER_FORBIDS_ATOMICROWS_BUNDLE_SHA_HASH_FREEZE_AUTHORITY": True,
    "OWNER_FORBIDS_ATOMICROWS_BUNDLE_SHA256_REFERENCE_IN_AUTHORITY_ARTIFACTS": True,
    "OWNER_FORBIDS_SCATTERED_HARDCODED_BLOCKERS": True,
    "OWNER_FORBIDS_SCATTERED_NONLIVE_NOPROFIT_NOSHA_WORDING": True,
}

NO_AUTHORITY_CONFIRMATION = {
    "live_trading_created": False,
    "live_order_authority_created": False,
    "shadow_execution_created": False,
    "live_execution_created": False,
    "replay_execution_created": False,
    "paper_execution_created": False,
    "optimizer_execution_created": False,
    "quantum_backend_execution_created": False,
    "quantum_simulator_execution_created": False,
    "connector_semantic_authority_created": False,
    "runtime_cash_receipt_created": False,
    "replay_result_fabricated": False,
    "paper_result_fabricated": False,
    "shadow_result_fabricated": False,
    "live_result_fabricated": False,
    "replay_paper_performance_evidence_fabricated": False,
    "live_profit_evidence_created": False,
    "profit_guarantee_created": False,
    "qtt_sha_authority_created": False,
    "qtt_generated_sha_authority_created": False,
    "qtt_freeze_authority_created": False,
    "qtt_checksum_global_digest_authority_created": False,
    "atomicrows_final_bundle_created": False,
    "atomicrows_bundle_jsonl_created": False,
    "atomicrows_bundle_sha_reference_created": False,
    "atomicrows_bundle_hash_sha_freeze_authority_created": False,
}

RESULT_PACKET_TYPES = ("REPLAY_RESULT_PACKET", "PAPER_RESULT_PACKET")
RESULT_MODES = ("REPLAY", "PAPER")
RESULT_STATES = ("NO_RESULT_YET", "RESULT_PENDING", "RESULT_OBSERVED")
VALIDATION_STATES = (
    "NO_VALIDATED_RESULT_ARTIFACT",
    "VALIDATED_RESULT_PACKET",
    "REJECTED_RESULT_PACKET",
    "RESULT_ARTIFACT_UNMAPPABLE",
)
EVIDENCE_STATES = (
    "NO_EVIDENCE",
    "RESULT_PACKET_REQUIRED",
    "VALIDATED_REPLAY_PAPER_EVIDENCE_CANDIDATE",
)
REPLAY_PAPER_EVIDENCE_CLASSES = (
    "NO_REPLAY_PAPER_EVIDENCE",
    "REPLAY_RESULT_EVIDENCE_CANDIDATE",
    "PAPER_RESULT_EVIDENCE_CANDIDATE",
)
LIVE_PROFIT_EVIDENCE_CLASSES = ("NO_LIVE_PROFIT_EVIDENCE",)
PROFITABILITY_LABELS = (
    "UNOBSERVED",
    "PROFITABLE_AFTER_FEES",
    "UNPROFITABLE_AFTER_FEES",
    "BREAK_EVEN_AFTER_FEES",
)
CONFIDENCE_CLASSES = (
    "UNOBSERVED",
    "LOW_SAMPLE_CANDIDATE",
    "MEDIUM_SAMPLE_CANDIDATE",
    "HIGH_SAMPLE_CANDIDATE",
)
SAMPLE_SIZE_CLASSES = (
    "NO_SAMPLE",
    "SMALL_SAMPLE",
    "MEDIUM_SAMPLE",
    "LARGE_SAMPLE",
)
RISK_DRAWDOWN_CLASSES = (
    "UNOBSERVED_DRAWDOWN",
    "LOW_DRAWDOWN_CANDIDATE",
    "MEDIUM_DRAWDOWN_CANDIDATE",
    "HIGH_DRAWDOWN_CANDIDATE",
)
SLIPPAGE_COST_CLASSES = (
    "UNOBSERVED_COST",
    "LOW_COST_CANDIDATE",
    "MEDIUM_COST_CANDIDATE",
    "HIGH_COST_CANDIDATE",
)
LATENCY_CLASSES = (
    "UNOBSERVED_LATENCY",
    "LOW_LATENCY_CANDIDATE",
    "MEDIUM_LATENCY_CANDIDATE",
    "HIGH_LATENCY_CANDIDATE",
)
TIME_TO_EXPIRY_CLASSES = (
    "UNOBSERVED_TIME_TO_EXPIRY",
    "SHORT_EXPIRY_CANDIDATE",
    "MEDIUM_EXPIRY_CANDIDATE",
    "LONG_EXPIRY_CANDIDATE",
)
LIQUIDITY_CLASSES = (
    "UNOBSERVED_LIQUIDITY",
    "LOW_LIQUIDITY_CANDIDATE",
    "MEDIUM_LIQUIDITY_CANDIDATE",
    "HIGH_LIQUIDITY_CANDIDATE",
)
REGIME_CLASSES = (
    "UNOBSERVED_REGIME",
    "LOW_VOLATILITY_CANDIDATE",
    "HIGH_VOLATILITY_CANDIDATE",
    "EVENT_DRIVEN_CANDIDATE",
)
PREDICTION_MARKET_OUTCOME_METRICS = (
    "net_profit_after_fees",
    "expected_value_after_fees",
    "max_drawdown",
    "win_rate",
    "loss_rate",
    "profit_factor",
    "risk_adjusted_return",
    "fill_quality_metric",
    "fill_rate",
    "latency_observed_ms",
)
CALIBRATION_METRIC_CANDIDATES = (
    "brier_score",
    "log_loss",
    "calibration_error",
    "expected_calibration_error",
    "reliability_curve_bucket_error",
)
QUANTUM_CLASSICAL_HYBRID_COMPARISON_STATES = (
    "RESULT_PACKET_REQUIRED",
    "COMPARISON_PENDING",
    "VALIDATED_REPLAY_PAPER_COMPARISON_CANDIDATE",
)
QUANTUM_APPLICABILITY_CLASSES = (
    "QUANTUM_APPLICABLE",
    "QUANTUM_INSPIRED_QKU",
    "CLASSICAL_BASELINE_ONLY",
    "HYBRID_ARBITRATION_CANDIDATE",
    "UNOBSERVED_QUANTUM_APPLICABILITY",
)
OPTIMIZER_METADATA_CANDIDATE_CLASSES = (
    "QAOA_METADATA_CANDIDATE",
    "VQE_METADATA_CANDIDATE",
    "ANNEALING_METADATA_CANDIDATE",
    "QUBO_METADATA_CANDIDATE",
    "ISING_METADATA_CANDIDATE",
    "CLASSICAL_BASELINE_METADATA_CANDIDATE",
    "HYBRID_ARBITRATION_METADATA_CANDIDATE",
)
ATOMICROWS_PR154_RESULT_COMPATIBILITY_STATES = (
    "RESULT_COMPATIBILITY_PENDING",
    "REPLAY_PAPER_RESULT_PACKET_REQUIRED",
)
OWNER_REVIEW_RESULT_PROMOTION_STATES = (
    "AWAITING_VALIDATED_RESULT_PACKET",
    "NO_VALIDATED_RESULT_ARTIFACT",
    "OWNER_REVIEW_REQUIRED",
)
AUTHORITY_CLASSES = (
    "OWNER_APPROVED_INTERNAL_POLICY",
    "CANDIDATE_DEFAULT",
    "PROVISIONAL_DEFAULT",
    "REPLAY_PAPER_TEST_DEFAULT",
    "SOURCE_REQUIRED_PLACEHOLDER",
    "OWNER_REVIEW_REQUIRED_VALUE",
    "MISSING_RESULT_PLACEHOLDER",
    "PENDING_RESULT_EVIDENCE_STATE",
)
CANDIDATE_SOURCE_CLASSES = (
    "OFFICIAL_SOURCE_CANDIDATE",
    "RESEARCH_CANDIDATE",
    "SOCIAL_SIGNAL_CANDIDATE",
    "WEB_CANDIDATE",
    "INSTITUTIONAL_RESEARCH_CANDIDATE",
    "OWNER_SUBMITTED_CANDIDATE",
    "CLASSICAL_OPTIMIZATION_CANDIDATE",
    "QUANTUM_OPTIMIZATION_CANDIDATE",
    "HYBRID_OPTIMIZATION_CANDIDATE",
    "PROVISIONAL_DEFAULT_CANDIDATE",
    "REPLAY_PAPER_TEST_CANDIDATE",
)
SOURCE_ROUTES = (
    "ONLINE_METRIC_CANDIDATE_INTAKE",
    "OPEN_INTAKE_CANDIDATE_BRIDGE",
    "OWNER_APPROVED_PROVISIONAL_DEFAULT",
    "PR161D_PENDING_RESULT_SLOT",
    "PR161E_MISSING_VALUE_MATERIALIZATION",
)
RESULT_ARTIFACT_CLASSES = (
    "ACTUAL_REPLAY_RESULT_PACKET_CANDIDATE",
    "ACTUAL_PAPER_RESULT_PACKET_CANDIDATE",
    "VALIDATED_REPLAY_RESULT_PACKET",
    "VALIDATED_PAPER_RESULT_PACKET",
    "REJECTED_REPLAY_RESULT_PACKET",
    "REJECTED_PAPER_RESULT_PACKET",
    "SYNTHETIC_TEST_FIXTURE_RESULT_PACKET",
    "SCHEMA_ONLY_ARTIFACT",
    "CONTRACT_ONLY_ARTIFACT",
    "EMPTY_PENDING_CAPTURE_SURFACE",
    "PRE_RESULT_RANKING_ARTIFACT",
    "NO_RESULT_ARTIFACT",
    "UNSAFE_OR_UNMAPPABLE_RESULT_ARTIFACT",
)
RESULT_AUTHENTICITY_CLASSES = (
    "NO_VALIDATED_RESULT_PACKET",
    "SCHEMA_OR_CONTRACT_ONLY",
    "SYNTHETIC_FIXTURE_NOT_PERFORMANCE_EVIDENCE",
    "PRE_RESULT_PRIORITY_NOT_PERFORMANCE_EVIDENCE",
    "UNSAFE_OR_UNMAPPABLE",
    "VALIDATED_REAL_REPLAY_PACKET",
    "VALIDATED_REAL_PAPER_PACKET",
)
PROVENANCE_CLASSES = (
    "LOCAL_REPO_ARTIFACT",
    "SOURCE_EVIDENCE_FIXTURE",
    "ONLINE_CANDIDATE_SOURCE",
)
AGENT_ROLES = (
    "QTT_REPLAY_AGENT",
    "QTT_PAPER_AGENT",
    "QTT_SCORING_AGENT",
    "QTT_RANKING_AGENT",
    "QTT_QUANTUM_ADVISORY_AGENT",
    "QTT_OPTIMIZER_ARBITRATION_AGENT",
    "QTT_RISK_AGENT",
    "QTT_CAPITAL_AGENT",
    "QTT_LATENCY_AGENT",
    "QTT_EXECUTION_PREP_AGENT",
    "QTT_SOURCE_EVIDENCE_AGENT",
    "QTT_RESEARCH_AGENT",
    "QTT_ATOMICROWS_ENRICHMENT_AGENT",
    "QTT_PARAMETER_STACK_AGENT",
    "QTT_OWNER_REVIEW_AGENT",
)
AGENT_TASK_STATES = (
    "RESULT_PACKET_REQUIRED",
    "RESULT_PACKET_VALIDATED",
    "RESULT_PACKET_REJECTED",
    "RESULT_PACKET_PENDING",
    "RESULT_ARTIFACT_UNMAPPABLE",
    "SCENARIO_ATTRIBUTION_REQUIRED",
    "RANKING_UPDATE_CANDIDATE_READY",
    "FUTURE_PROFITABILITY_PATTERN_PENDING",
    "OWNER_REVIEW_REQUIRED",
    "FUTURE_LIVE_GATE_REQUIRED",
    "ONLINE_CANDIDATE_REVIEW_REQUIRED",
    "MISSING_VALUE_CANDIDATE_REVIEW_REQUIRED",
)

RESULT_NUMERIC_FIELDS = (
    "gross_profit",
    "net_profit_after_fees",
    "expected_value_after_fees",
    "fees",
    "slippage",
    "max_drawdown",
    "win_rate",
    "loss_rate",
    "profit_factor",
    "risk_adjusted_return",
    "calibration_error_if_available",
    "brier_score_if_available",
    "log_loss_if_available",
    "latency_observed_ms",
    "fill_quality_metric",
    "fill_rate_if_available",
    "sample_size",
    "result_backed_score",
)
RESULT_PACKET_REQUIRED_FIELDS = (
    "result_packet_id",
    "result_packet_type",
    "result_mode",
    "source_artifact_path",
    "source_artifact_class",
    "result_authenticity_class",
    "provenance_class",
    "qku_ids",
    "qku_bundle_id",
    "scenario_matrix_id",
    "order_condition_scenario_id",
    "replay_paper_scenario_id",
    "market",
    "platform",
    "venue_scope",
    "event_type",
    "prediction_market_category_if_available",
    "time_window",
    "time_to_expiry_class",
    "liquidity_class",
    "order_condition_fingerprint",
    "result_state",
    "validation_state",
    "evidence_state",
    "replay_paper_evidence_class",
    "profitability_label",
    *RESULT_NUMERIC_FIELDS,
    "latency_percentile_class",
    "confidence_class",
    "regime_class",
    "market_microstructure_context",
    "quantum_applicability_class_if_available",
    "quantum_route_id_if_applicable",
    "classical_baseline_route_id_if_applicable",
    "hybrid_arbitration_route_id_if_applicable",
    "optimizer_family_id_if_available",
    "qaoa_metadata_candidate_if_available",
    "vqe_metadata_candidate_if_available",
    "annealing_metadata_candidate_if_available",
    "qubo_metadata_candidate_if_available",
    "ising_metadata_candidate_if_available",
    "atomicrow_id_if_available",
    "pr154_target_id_if_available",
    "owner_review_required_flag",
    "replay_paper_required_flag",
    "future_live_gate_required_flag",
    "promotion_blocker",
    "no_live_authority_created_flag",
    "no_profit_guarantee_created_flag",
    "no_live_profit_evidence_created_flag",
    "no_profit_evidence_created_without_validated_result_packet_flag",
    "no_optimizer_execution_created_flag",
    "no_quantum_backend_execution_created_flag",
    "no_qtt_sha_authority_created_flag",
    "no_atomicrows_bundle_sha_authority_created_flag",
)
TRACEABILITY_FIELDS = (
    "qku_id",
    "qku_ids",
    "qku_graph_node_id",
    "upstream_pr161a_or_pr161b_origin_if_available",
    "pr161c_registry_ref",
    "pr161c_graph_ref",
    "pr161d_score_ref_if_available",
    "pr161d_category_ranking_ref_if_available",
    "pr161d_scenario_matrix_ref_if_available",
    "pr161d_bundle_ref_if_available",
    "pr161d_replay_paper_scenario_ref_if_available",
    "pr161d_agent_task_ref_if_available",
    "pr161d_owner_review_ref_if_available",
    "atomicrows_ref_if_available",
    "pr154_ref_if_available",
    "downstream_agent_roles",
    "downstream_workflow_routes",
    "downstream_process_routes",
    "downstream_future_pr_routes",
    "downstream_owner_review_route",
    "downstream_future_live_gate_route",
    "unmappable_reason_if_any",
)

ALWAYS_READ_MASTER_AUTHORITY_PATHS = (
    MASTER_PLAN_PATH,
    Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"),
    Path("docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"),
    Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"),
    Path(
        "src/qtt/stage1_prediction_markets/launch_readiness/"
        "day1_launch_readiness_roadmap_policy.py"
    ),
)
PR136_CONTROL_PLANE_PATHS = {
    "route_triage": GENERATED_DIR / "PR136RouteTriage.report.json",
    "section_crosswalk": GENERATED_DIR / "PR136MasterPlanSectionCrosswalk.report.json",
    "market_index": GENERATED_DIR / "PR136MarketSpecificLaunchReadinessIndex.report.json",
    "command_action": GENERATED_DIR / "PR136CommandActionMatrix.report.json",
}
PR136_CROSSWALK_FALLBACK_PATH = (
    GENERATED_DIR / "PR136MasterPlanCoverageToReadinessDomainMap.report.json"
)
ATOMICROWS_CONTRACT_PATHS = {
    "pr137r_atomicrows_reconciliation": GENERATED_DIR
    / "PR137R_AtomicRowsBundleReconciliation.report.json",
    "pr138_atomicrows_semantic_contract": GENERATED_DIR
    / "PR138_AtomicRowsSemanticRowContract.report.json",
    "pr161c_atomicrows_bridge": GENERATED_DIR
    / "PR161C_QKUAtomicRowsCompatibilityBridge.report.json",
    "pr161c_pr154_bridge": GENERATED_DIR / "PR161C_QKUPR154CompatibilityBridge.report.json",
    "pr161d_atomicrows_pr154_priority": GENERATED_DIR
    / "PR161D_QKUAtomicRowsPR154PriorityBridge.report.json",
}
PR161B_REQUIRED_PATHS = {
    "assimilation_queue": GENERATED_DIR / "PR161B_PR161CAssimilationQueue.report.json",
    "field_coverage": GENERATED_DIR
    / "PR161B_MasterPlanToPR161AFieldRecordCoverage.report.json",
    "final_summary": GENERATED_DIR / "PR161B_ResidualCoverageFinalSummary.report.json",
    "agent_candidate_consumption": GENERATED_DIR
    / "PR161B_QTTAgentCandidateConsumptionMatrix.report.json",
    "quantum_residual": GENERATED_DIR
    / "PR161B_QuantumOptimizerResidualCoverage.report.json",
    "formula_residual": GENERATED_DIR
    / "PR161B_FormulaAlgorithmResidualCoverage.report.json",
    "parameter_range_residual": GENERATED_DIR
    / "PR161B_ParameterRangeResidualCoverage.report.json",
}
PR161C_REPORT_PATHS = {
    "master_inventory": GENERATED_DIR / "PR161C_QKUMasterInventoryBridge.report.json",
    "canonical_registry": GENERATED_DIR / "PR161C_QKUCanonicalRegistry.report.json",
    "primary_materialization": GENERATED_DIR
    / "PR161C_QKU9360PrimaryMaterializationRegistry.report.json",
    "field_value_facet": GENERATED_DIR / "PR161C_QKU22625FieldValueFacetLinkage.report.json",
    "expanded_accounting": GENERATED_DIR / "PR161C_QKUExpandedRecordAccounting.report.json",
    "graph_nodes": GENERATED_DIR / "PR161C_QKUOrchestrationGraph.report.json",
    "graph_edges": GENERATED_DIR / "PR161C_QKUOrchestrationGraphEdges.report.json",
    "graph_completeness": GENERATED_DIR
    / "PR161C_QKUOrchestrationGraphCompleteness.report.json",
    "graph_quality": GENERATED_DIR / "PR161C_QKUGraphQualityMetrics.report.json",
    "stage1_prediction_market_index": GENERATED_DIR
    / "PR161C_QKUStage1PredictionMarketRetrievalIndex.report.json",
    "stage1_day1_index": GENERATED_DIR / "PR161C_QKUStage1Day1LaunchPrepIndex.report.json",
    "agent_retrieval_index": GENERATED_DIR / "PR161C_QKUAgentRetrievalIndex.report.json",
    "quantum_forward_inventory": GENERATED_DIR
    / "PR161C_QKUQuantumForwardOptimizationInventory.report.json",
    "quantum_residual_trace": GENERATED_DIR / "PR161C_QKUQuantumResidualTrace.report.json",
    "range_optimizer_audit": GENERATED_DIR
    / "PR161C_QKURangeOptimizerMaterializationAudit.report.json",
    "online_retrieval_audit": GENERATED_DIR / "PR161C_QKUOnlineRetrievalAudit.report.json",
    "online_scout_queue": GENERATED_DIR / "PR161C_QKUOnlineScoutQueue.report.json",
    "fallback_default_audit": GENERATED_DIR
    / "PR161C_QKUFallbackDefaultExhaustionAudit.report.json",
    "atomicrows_bridge": GENERATED_DIR / "PR161C_QKUAtomicRowsCompatibilityBridge.report.json",
    "pr154_bridge": GENERATED_DIR / "PR161C_QKUPR154CompatibilityBridge.report.json",
}
PR161D_REPORT_PATHS = {
    "final_summary": GENERATED_DIR / "PR161D_FinalSummary.report.json",
    "quality_score": GENERATED_DIR / "PR161D_QKUQualityScoreRegistry.report.json",
    "score_component": GENERATED_DIR / "PR161D_QKUScoreComponentBreakdown.report.json",
    "quality_lane": GENERATED_DIR / "PR161D_QKUQualityLaneClassification.report.json",
    "category_ranking": GENERATED_DIR / "PR161D_QKUCategoryRankingRegistry.report.json",
    "category_top_list": GENERATED_DIR / "PR161D_QKUCategoryTopListIndex.report.json",
    "category_ranking_breakdown": GENERATED_DIR
    / "PR161D_QKUCategoryRankingBreakdown.report.json",
    "result_backed_slots": GENERATED_DIR
    / "PR161D_QKUResultBackedRankingSlots.report.json",
    "scenario_outcome_matrix": GENERATED_DIR
    / "PR161D_QKUScenarioOutcomeMatrix.report.json",
    "order_condition_scenario": GENERATED_DIR
    / "PR161D_QKUOrderConditionScenarioRegistry.report.json",
    "future_profitability_pattern": GENERATED_DIR
    / "PR161D_QKUFutureProfitabilityPatternFields.report.json",
    "combination_candidate": GENERATED_DIR
    / "PR161D_QKUCombinationCandidateRegistry.report.json",
    "combination_scenario_map": GENERATED_DIR
    / "PR161D_QKUCombinationScenarioMap.report.json",
    "combination_replay_paper_queue": GENERATED_DIR
    / "PR161D_QKUCombinationReplayPaperPriorityQueue.report.json",
    "combination_boundedness": GENERATED_DIR
    / "PR161D_QKUCombinationGenerationBoundedness.report.json",
    "replay_paper_priority_queue": GENERATED_DIR
    / "PR161D_QKUReplayPaperPriorityQueue.report.json",
    "replay_paper_scenario_inputs": GENERATED_DIR
    / "PR161D_QKUReplayPaperScenarioInputs.report.json",
    "quantum_priority_queue": GENERATED_DIR
    / "PR161D_QKUQuantumPriorityQueue.report.json",
    "classical_baseline_queue": GENERATED_DIR
    / "PR161D_QKUClassicalBaselinePriorityQueue.report.json",
    "hybrid_arbitration_queue": GENERATED_DIR
    / "PR161D_QKUHybridArbitrationPriorityQueue.report.json",
    "agent_task_queue": GENERATED_DIR / "PR161D_QKUAgentTaskQueue.report.json",
    "agent_graph_routing": GENERATED_DIR / "PR161D_QKUAgentGraphRoutingMatrix.report.json",
    "agent_layer_coverage": GENERATED_DIR / "PR161D_QKUAgentLayerCoverage.report.json",
    "agent_role_coverage_gaps": GENERATED_DIR
    / "PR161D_QKUAgentRoleCoverageGaps.report.json",
    "agent_role_network": GENERATED_DIR / "PR161D_QTTAgentRoleNetworkRegistry.report.json",
    "market_bundle_activation_policy": GENERATED_DIR
    / "PR161D_QKUMarketBundleActivationPolicy.report.json",
    "market_bundle_dashboard": GENERATED_DIR
    / "PR161D_QKUMarketBundleActivationDashboardOptions.report.json",
    "market_active_bundle_set": GENERATED_DIR
    / "PR161D_QKUMarketActiveBundleSet.report.json",
    "market_bundle_dormancy_queue": GENERATED_DIR
    / "PR161D_QKUMarketBundleDormancyQueue.report.json",
    "agent_role_bundle_fanout": GENERATED_DIR
    / "PR161D_QKUAgentRoleBundleReferenceFanout.report.json",
    "agent_role_bundle_slice": GENERATED_DIR / "PR161D_QKUAgentRoleBundleSlice.report.json",
    "online_enrichment_coverage": GENERATED_DIR
    / "PR161D_QKUOnlineEnrichmentCoverage.report.json",
    "online_enrichment_cluster_map": GENERATED_DIR
    / "PR161D_QKUOnlineEnrichmentClusterMap.report.json",
    "online_source_candidate": GENERATED_DIR
    / "PR161D_QKUOnlineSourceCandidateRegistry.report.json",
    "online_search_capability": GENERATED_DIR
    / "PR161D_QKUOnlineSearchCapabilityReceipt.report.json",
    "report_shard_manifest": GENERATED_DIR / "PR161D_ReportShardManifest.report.json",
    "owner_review_queue": GENERATED_DIR / "PR161D_QKUOwnerReviewQueue.report.json",
}

REPLAY_PAPER_CONTRACT_PATHS = (
    Path("src/qtt/stage1_prediction_markets/replay_paper"),
    Path("src/qtt/stage1_prediction_markets/runtime_resolver"),
    Path("src/qtt/stage1_prediction_markets/runtime_resolver_snapshot"),
    Path("src/qtt/stage1_prediction_markets/dual_result_review"),
    Path("src/qtt/stage1_prediction_markets/owner_live_promotion_review"),
    Path("src/qtt/stage1_prediction_markets/three_venue_canary_eligibility"),
    Path("tests/fixtures/source_evidence/replay_paper"),
    Path("tests/fixtures/replay_paper"),
    Path("tests/fixtures/replay_paper_review"),
    Path("tools/stage1_concurrent_replay_paper_contract_check.py"),
    Path("tools/stage1_dual_result_review_contract_check.py"),
    Path("tools/stage1_owner_live_promotion_review_contract_check.py"),
    Path("tools/stage1_three_venue_canary_eligibility_contract_check.py"),
)
SOURCE_EVIDENCE_OPEN_INTAKE_PATHS = (
    Path("docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"),
    Path("src/qtt/source_evidence"),
    Path("src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake"),
)
QUANTUM_SCORING_PARAMETER_VALIDATOR_PATHS = (
    Path("tools/validate_qtt_algorithm_formula_family_registry.py"),
    Path("tools/validate_qtt_agent_algorithm_binding_registry.py"),
    Path("tools/validate_qtt_agent_algorithm_consumer_gate.py"),
    Path("tools/validate_qtt_agent_algorithm_cumulative_readiness_gate.py"),
    Path("tools/validate_qtt_agent_algorithm_command_matrix.py"),
    Path("tools/validate_quantum_applicability_classification_registry.py"),
    Path("tools/validate_owner_quantum_priority_policy_registry.py"),
    Path("tools/validate_parameter_algorithm_scoring_policy_registry.py"),
    Path("tools/validate_parameter_stack_scoring_and_ranking_gate.py"),
    Path("tools/validate_quantum_classical_optimizer_arbitration_gate.py"),
    Path("tools/validate_candidate_parameter_stack_generation_gate.py"),
    Path("tools/validate_trade_context_parameter_stack_selection_gate.py"),
)
VALIDATION_CI_ANTI_CHURN_PATHS = (
    Path("tools/ci_branch_context.py"),
    Path("tools/run_validation_gates.py"),
    Path("tools/validate_grand_global_debug_logical_consistency_audit.py"),
    PR152_AUDIT_REPORT_PATH,
    Path("tests/tools/test_ci_branch_context.py"),
    Path("tests/fail_closed/test_run_validation_gates.py"),
)

RESULT_DISCOVERY_ROOTS = (
    GENERATED_DIR,
    Path("src/qtt/stage1_prediction_markets/replay_paper"),
    Path("tests/fixtures/source_evidence/replay_paper"),
    Path("tests/fixtures/replay_paper"),
    Path("tests/fixtures/replay_paper_review"),
)

REPORT_FILENAMES = (
    "PR161E_ReplayPaperOutcomeCapturePreflightReceipt.report.json",
    "PR161E_ReplayPaperResultArtifactDiscovery.report.json",
    "PR161E_ResultAuthenticityClassification.report.json",
    "PR161E_ReplayResultPacketValidation.report.json",
    "PR161E_PaperResultPacketValidation.report.json",
    "PR161E_ReplayPaperOutcomeCaptureRegistry.report.json",
    "PR161E_QKUBundleResultLedger.report.json",
    "PR161E_QKUReplayPaperProfitabilityLedger.report.json",
    "PR161E_QKUScenarioResultAttribution.report.json",
    "PR161E_QKUResultBackedRankingUpdateCandidates.report.json",
    "PR161E_QKUFutureProfitabilityPatternUpdateCandidates.report.json",
    "PR161E_QuantumClassicalHybridOutcomeComparison.report.json",
    "PR161E_AtomicRowsPR154ResultCompatibilityBridge.report.json",
    "PR161E_ResultConfidenceGate.report.json",
    "PR161E_OwnerReviewResultPromotionQueue.report.json",
    "PR161E_AgentOutcomeTaskQueue.report.json",
    "PR161E_OnlineMetricCandidateIntake.report.json",
    "PR161E_OpenIntakeCandidateBridge.report.json",
    "PR161E_MissingValueCandidateMaterialization.report.json",
    "PR161E_QKUGraphTraceabilityBridge.report.json",
    "PR161E_QKUCoverageAndOrphanAudit.report.json",
    "PR161E_ForbiddenAuthorityScan.report.json",
    "PR161E_NoScatteredHardcodedAuthorityAudit.report.json",
    SHARED_DICTIONARY_REPORT_FILENAME,
    "PR161E_ReportShardManifest.report.json",
    "PR161E_FinalSummary.report.json",
)

SCHEMA_FILENAMES = (
    "pr161e_replay_result_packet.schema.json",
    "pr161e_paper_result_packet.schema.json",
    "pr161e_result_artifact_discovery_record.schema.json",
    "pr161e_result_authenticity_record.schema.json",
    "pr161e_replay_paper_outcome_capture_record.schema.json",
    "pr161e_qku_bundle_result_ledger_record.schema.json",
    "pr161e_qku_replay_paper_profitability_ledger_record.schema.json",
    "pr161e_qku_scenario_result_attribution_record.schema.json",
    "pr161e_qku_result_backed_ranking_update_candidate_record.schema.json",
    "pr161e_qku_future_profitability_pattern_update_candidate_record.schema.json",
    "pr161e_quantum_classical_hybrid_outcome_comparison_record.schema.json",
    "pr161e_atomicrows_pr154_result_compatibility_record.schema.json",
    "pr161e_result_confidence_gate_record.schema.json",
    "pr161e_owner_review_result_promotion_queue_record.schema.json",
    "pr161e_agent_outcome_task_record.schema.json",
    "pr161e_online_metric_candidate_intake_record.schema.json",
    "pr161e_open_intake_candidate_record.schema.json",
    "pr161e_missing_value_candidate_record.schema.json",
    "pr161e_graph_traceability_record.schema.json",
    "pr161e_qku_coverage_orphan_audit_record.schema.json",
    "pr161e_forbidden_authority_scan.schema.json",
    "pr161e_no_scattered_hardcoded_authority_audit.schema.json",
    "pr161e_final_summary.schema.json",
)

REPORT_SCHEMA_REFS = {
    "PR161E_ReplayPaperResultArtifactDiscovery.report.json": (
        SCHEMA_DIR / "pr161e_result_artifact_discovery_record.schema.json"
    ).as_posix(),
    "PR161E_ResultAuthenticityClassification.report.json": (
        SCHEMA_DIR / "pr161e_result_authenticity_record.schema.json"
    ).as_posix(),
    "PR161E_ReplayResultPacketValidation.report.json": (
        SCHEMA_DIR / "pr161e_replay_result_packet.schema.json"
    ).as_posix(),
    "PR161E_PaperResultPacketValidation.report.json": (
        SCHEMA_DIR / "pr161e_paper_result_packet.schema.json"
    ).as_posix(),
    "PR161E_ReplayPaperOutcomeCaptureRegistry.report.json": (
        SCHEMA_DIR / "pr161e_replay_paper_outcome_capture_record.schema.json"
    ).as_posix(),
    "PR161E_QKUBundleResultLedger.report.json": (
        SCHEMA_DIR / "pr161e_qku_bundle_result_ledger_record.schema.json"
    ).as_posix(),
    "PR161E_QKUReplayPaperProfitabilityLedger.report.json": (
        SCHEMA_DIR / "pr161e_qku_replay_paper_profitability_ledger_record.schema.json"
    ).as_posix(),
    "PR161E_QKUScenarioResultAttribution.report.json": (
        SCHEMA_DIR / "pr161e_qku_scenario_result_attribution_record.schema.json"
    ).as_posix(),
    "PR161E_QKUResultBackedRankingUpdateCandidates.report.json": (
        SCHEMA_DIR / "pr161e_qku_result_backed_ranking_update_candidate_record.schema.json"
    ).as_posix(),
    "PR161E_QKUFutureProfitabilityPatternUpdateCandidates.report.json": (
        SCHEMA_DIR / "pr161e_qku_future_profitability_pattern_update_candidate_record.schema.json"
    ).as_posix(),
    "PR161E_QuantumClassicalHybridOutcomeComparison.report.json": (
        SCHEMA_DIR / "pr161e_quantum_classical_hybrid_outcome_comparison_record.schema.json"
    ).as_posix(),
    "PR161E_AtomicRowsPR154ResultCompatibilityBridge.report.json": (
        SCHEMA_DIR / "pr161e_atomicrows_pr154_result_compatibility_record.schema.json"
    ).as_posix(),
    "PR161E_ResultConfidenceGate.report.json": (
        SCHEMA_DIR / "pr161e_result_confidence_gate_record.schema.json"
    ).as_posix(),
    "PR161E_OwnerReviewResultPromotionQueue.report.json": (
        SCHEMA_DIR / "pr161e_owner_review_result_promotion_queue_record.schema.json"
    ).as_posix(),
    "PR161E_AgentOutcomeTaskQueue.report.json": (
        SCHEMA_DIR / "pr161e_agent_outcome_task_record.schema.json"
    ).as_posix(),
    "PR161E_OnlineMetricCandidateIntake.report.json": (
        SCHEMA_DIR / "pr161e_online_metric_candidate_intake_record.schema.json"
    ).as_posix(),
    "PR161E_OpenIntakeCandidateBridge.report.json": (
        SCHEMA_DIR / "pr161e_open_intake_candidate_record.schema.json"
    ).as_posix(),
    "PR161E_MissingValueCandidateMaterialization.report.json": (
        SCHEMA_DIR / "pr161e_missing_value_candidate_record.schema.json"
    ).as_posix(),
    "PR161E_QKUGraphTraceabilityBridge.report.json": (
        SCHEMA_DIR / "pr161e_graph_traceability_record.schema.json"
    ).as_posix(),
    "PR161E_QKUCoverageAndOrphanAudit.report.json": (
        SCHEMA_DIR / "pr161e_qku_coverage_orphan_audit_record.schema.json"
    ).as_posix(),
    "PR161E_ForbiddenAuthorityScan.report.json": (
        SCHEMA_DIR / "pr161e_forbidden_authority_scan.schema.json"
    ).as_posix(),
    "PR161E_NoScatteredHardcodedAuthorityAudit.report.json": (
        SCHEMA_DIR / "pr161e_no_scattered_hardcoded_authority_audit.schema.json"
    ).as_posix(),
    "PR161E_FinalSummary.report.json": (
        SCHEMA_DIR / "pr161e_final_summary.schema.json"
    ).as_posix(),
}

SCHEMA_ENUM_FIELDS = {
    "result_packet_type": RESULT_PACKET_TYPES,
    "result_mode": RESULT_MODES,
    "source_artifact_class": RESULT_ARTIFACT_CLASSES,
    "result_authenticity_class": RESULT_AUTHENTICITY_CLASSES,
    "provenance_class": PROVENANCE_CLASSES,
    "result_state": RESULT_STATES,
    "validation_state": VALIDATION_STATES,
    "evidence_state": EVIDENCE_STATES,
    "replay_paper_evidence_class": REPLAY_PAPER_EVIDENCE_CLASSES,
    "profitability_label": PROFITABILITY_LABELS,
    "confidence_class": CONFIDENCE_CLASSES,
    "time_to_expiry_class": TIME_TO_EXPIRY_CLASSES,
    "liquidity_class": LIQUIDITY_CLASSES,
    "regime_class": REGIME_CLASSES,
    "comparison_state": QUANTUM_CLASSICAL_HYBRID_COMPARISON_STATES,
    "compatibility_state": ATOMICROWS_PR154_RESULT_COMPATIBILITY_STATES,
    "owner_review_state": OWNER_REVIEW_RESULT_PROMOTION_STATES,
    "value_authority_class": AUTHORITY_CLASSES,
    "candidate_source_class": CANDIDATE_SOURCE_CLASSES,
    "source_route": SOURCE_ROUTES,
    "agent_task_state": AGENT_TASK_STATES,
}

ONLINE_METRIC_CANDIDATE_SOURCES = (
    {
        "candidate_id": "PR161E-ONLINE-METRIC-0001",
        "source_title": "scikit-learn brier_score_loss documentation",
        "source_url": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html",
        "authority_class": "OFFICIAL_SOURCE_CANDIDATE",
        "candidate_metric_fields": ["brier_score"],
        "candidate_use": "probabilistic_calibration_candidate_field",
    },
    {
        "candidate_id": "PR161E-ONLINE-METRIC-0002",
        "source_title": "scikit-learn log_loss documentation",
        "source_url": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html",
        "authority_class": "OFFICIAL_SOURCE_CANDIDATE",
        "candidate_metric_fields": ["log_loss"],
        "candidate_use": "probabilistic_classification_loss_candidate_field",
    },
    {
        "candidate_id": "PR161E-ONLINE-METRIC-0003",
        "source_title": "scikit-learn calibration curve documentation",
        "source_url": "https://scikit-learn.org/stable/modules/calibration.html",
        "authority_class": "OFFICIAL_SOURCE_CANDIDATE",
        "candidate_metric_fields": ["calibration_error", "reliability_curve_bucket_error"],
        "candidate_use": "prediction_market_calibration_candidate_field",
    },
    {
        "candidate_id": "PR161E-ONLINE-METRIC-0004",
        "source_title": "SEC Rule 605 execution quality disclosure",
        "source_url": "https://www.sec.gov/rules-regulations/1997/11/disclosure-order-execution-routing-practices",
        "authority_class": "OFFICIAL_SOURCE_CANDIDATE",
        "candidate_metric_fields": ["fill_quality_metric", "effective_spread", "execution_quality"],
        "candidate_use": "fill_quality_and_cost_candidate_field",
    },
    {
        "candidate_id": "PR161E-ONLINE-METRIC-0005",
        "source_title": "FINRA best execution and order handling guidance",
        "source_url": "https://www.finra.org/rules-guidance/guidance/reports/2023-finras-examination-and-risk-monitoring-program/best-execution",
        "authority_class": "OFFICIAL_SOURCE_CANDIDATE",
        "candidate_metric_fields": ["execution_quality", "slippage", "fill_rate"],
        "candidate_use": "execution_quality_candidate_field",
    },
    {
        "candidate_id": "PR161E-ONLINE-METRIC-0006",
        "source_title": "D-Wave QUBO/Ising model documentation",
        "source_url": "https://docs.dwavequantum.com/en/latest/concepts/models.html",
        "authority_class": "QUANTUM_OPTIMIZATION_CANDIDATE",
        "candidate_metric_fields": ["qubo_metadata_candidate", "ising_metadata_candidate"],
        "candidate_use": "quantum_optimization_metadata_candidate_field",
    },
    {
        "candidate_id": "PR161E-ONLINE-METRIC-0007",
        "source_title": "D-Wave quantum annealing documentation",
        "source_url": "https://docs.dwavequantum.com/en/latest/quantum_research/annealing.html",
        "authority_class": "QUANTUM_OPTIMIZATION_CANDIDATE",
        "candidate_metric_fields": ["annealing_metadata_candidate"],
        "candidate_use": "annealing_metadata_candidate_field",
    },
    {
        "candidate_id": "PR161E-ONLINE-METRIC-0008",
        "source_title": "IBM Qiskit optimization tutorial",
        "source_url": "https://qiskit-community.github.io/qiskit-optimization/tutorials/03_minimum_eigen_optimizer.html",
        "authority_class": "HYBRID_OPTIMIZATION_CANDIDATE",
        "candidate_metric_fields": ["qaoa_metadata_candidate", "vqe_metadata_candidate"],
        "candidate_use": "qaoa_vqe_optimizer_metadata_candidate_field",
    },
    {
        "candidate_id": "PR161E-ONLINE-METRIC-0009",
        "source_title": "Prediction market probabilities and Brier score research",
        "source_url": "https://www.jstor.org/stable/3083277",
        "authority_class": "RESEARCH_CANDIDATE",
        "candidate_metric_fields": ["brier_score", "market_probability_calibration"],
        "candidate_use": "prediction_market_evaluation_candidate_field",
    },
    {
        "candidate_id": "PR161E-ONLINE-METRIC-0010",
        "source_title": "Maximum drawdown definition reference",
        "source_url": "https://www.investopedia.com/terms/m/maximum-drawdown-mdd.asp",
        "authority_class": "WEB_CANDIDATE",
        "candidate_metric_fields": ["max_drawdown"],
        "candidate_use": "risk_drawdown_candidate_field",
    },
)

MISSING_VALUE_CANDIDATE_FIELDS = (
    "gross_profit",
    "net_profit_after_fees",
    "expected_value_after_fees",
    "fees",
    "slippage",
    "max_drawdown",
    "win_rate",
    "loss_rate",
    "profit_factor",
    "risk_adjusted_return",
    "calibration_error_if_available",
    "brier_score_if_available",
    "log_loss_if_available",
    "latency_observed_ms",
    "latency_percentile_class",
    "fill_quality_metric",
    "fill_rate_if_available",
    "sample_size",
    "confidence_class",
    "regime_class",
    "time_to_expiry_class",
    "liquidity_class",
    "qaoa_metadata_candidate_if_available",
    "vqe_metadata_candidate_if_available",
    "annealing_metadata_candidate_if_available",
    "qubo_metadata_candidate_if_available",
    "ising_metadata_candidate_if_available",
)

FORBIDDEN_AUTHORITY_PATTERNS = (
    "QTT SHA authority",
    "QTT-generated SHA authority",
    "QTT freeze authority",
    "QTT checksum/global digest authority",
    "AtomicRows bundle SHA authority",
    "AtomicRows bundle hash authority",
    "AtomicRows bundle freeze authority",
    "AtomicRows.bundle.sha256",
    "fake replay result",
    "fake paper result",
    "fake shadow result",
    "fake live result",
    "fake profit evidence",
    "live trading authority",
    "optimizer execution authority",
    "quantum backend execution authority",
    "quantum simulator execution authority",
    "connector semantic authority",
    "order execution authority",
    "runtime cash receipt fabrication",
)
FORBIDDEN_SCAN_ALLOWED_CONTEXT_MARKERS = (
    "forbidden",
    "no_",
    "not created",
    "without validated result packet",
    "VCS metadata",
    "test strings",
    "policy constants",
    "detect and reject",
    "created_flag",
)
FORBIDDEN_SCAN_PATH_EXEMPTIONS = (
    str(PACKAGE_DIR / "constants.py").replace("\\", "/"),
    "tests/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning/",
)

VALIDATION_COMMAND_LABELS = (
    "compileall",
    "pytest_pr161e",
    "build_pr161e",
    "validate_pr161e",
    "pr152_write_report",
    "pr152_read_only",
    "run_validation_gates",
    "git_diff_check",
    "git_status_short",
)
