"""Central PR161D policy constants and authority boundaries.

The values in this module are candidate-prioritization policy, not evidence of
profit, execution quality, connector semantics, or live-trading authority.
"""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR161D"
EXPECTED_BRANCH = "pr161d-qku-candidate-quality-scoring-replay-paper-prioritization"
SUCCESS_MARKER = "QTT_PR161D_QKU_CANDIDATE_QUALITY_REPLAY_PAPER_PRIORITIZATION_OK"

EXPECTED_PRIMARY_QKU_COUNT = 9360
EXPECTED_FIELD_VALUE_FACET_COUNT = 22625
EXPECTED_GRAPH_NODE_COUNT = 9360
EXPECTED_GRAPH_EDGE_COUNT = 60375
EXPECTED_ISOLATED_NON_REJECTED_QKU_COUNT = 0
EXPECTED_CANONICAL_AGENT_ROLE_COUNT = 15
GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES = 50 * 1024 * 1024
REPORT_SHARD_TARGET_BYTES = 40 * 1024 * 1024

PACKAGE_DIR = Path(
    "src/qtt/stage1_prediction_markets/"
    "qku_candidate_quality_replay_paper_prioritization"
)
SCHEMA_DIR = PACKAGE_DIR / "schemas"
GENERATED_DIR = Path("docs/master_plan/generated")
SHARD_DIR = GENERATED_DIR / "pr161d_qku_candidate_quality_shards"
MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")
PR152_AUDIT_REPORT_PATH = (
    GENERATED_DIR / "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
)

PR161C_REPORT_PATHS = {
    "master_inventory": GENERATED_DIR / "PR161C_QKUMasterInventoryBridge.report.json",
    "canonical_registry": GENERATED_DIR / "PR161C_QKUCanonicalRegistry.report.json",
    "primary_materialization": GENERATED_DIR
    / "PR161C_QKU9360PrimaryMaterializationRegistry.report.json",
    "field_facet_linkage": GENERATED_DIR
    / "PR161C_QKU22625FieldValueFacetLinkage.report.json",
    "expanded_accounting": GENERATED_DIR / "PR161C_QKUExpandedRecordAccounting.report.json",
    "agent_retrieval_index": GENERATED_DIR / "PR161C_QKUAgentRetrievalIndex.report.json",
    "stage1_prediction_market_index": GENERATED_DIR
    / "PR161C_QKUStage1PredictionMarketRetrievalIndex.report.json",
    "stage1_day1_index": GENERATED_DIR
    / "PR161C_QKUStage1Day1LaunchPrepIndex.report.json",
    "quantum_forward_inventory": GENERATED_DIR
    / "PR161C_QKUQuantumForwardOptimizationInventory.report.json",
    "graph_nodes": GENERATED_DIR / "PR161C_QKUOrchestrationGraph.report.json",
    "graph_edges": GENERATED_DIR / "PR161C_QKUOrchestrationGraphEdges.report.json",
    "graph_completeness": GENERATED_DIR
    / "PR161C_QKUOrchestrationGraphCompleteness.report.json",
    "graph_quality": GENERATED_DIR / "PR161C_QKUGraphQualityMetrics.report.json",
    "online_retrieval_audit": GENERATED_DIR / "PR161C_QKUOnlineRetrievalAudit.report.json",
    "online_scout_queue": GENERATED_DIR / "PR161C_QKUOnlineScoutQueue.report.json",
    "fallback_default_audit": GENERATED_DIR
    / "PR161C_QKUFallbackDefaultExhaustionAudit.report.json",
    "range_optimizer_audit": GENERATED_DIR
    / "PR161C_QKURangeOptimizerMaterializationAudit.report.json",
    "quantum_residual_trace": GENERATED_DIR / "PR161C_QKUQuantumResidualTrace.report.json",
    "supplemental_artifact_scout": GENERATED_DIR
    / "PR161C_QKUSupplementalArtifactScout.report.json",
    "algorithm_formula_strategy": GENERATED_DIR
    / "PR161C_QKUAlgorithmFormulaStrategyInventory.report.json",
    "replay_paper_route": GENERATED_DIR / "PR161C_QKUReplayPaperRouteBridge.report.json",
    "agent_consumption": GENERATED_DIR / "PR161C_QKUAgentConsumptionBridge.report.json",
    "atomicrows_bridge": GENERATED_DIR / "PR161C_QKUAtomicRowsCompatibilityBridge.report.json",
    "pr154_bridge": GENERATED_DIR / "PR161C_QKUPR154CompatibilityBridge.report.json",
}

PR136_CONTROL_PLANE_PATHS = {
    "route_triage": GENERATED_DIR / "PR136RouteTriage.report.json",
    "section_crosswalk_requested": GENERATED_DIR / "PR136MasterPlanSectionCrosswalk.report.json",
    "section_crosswalk_fallback": GENERATED_DIR
    / "PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "market_index": GENERATED_DIR / "PR136MarketSpecificLaunchReadinessIndex.report.json",
    "command_action": GENERATED_DIR / "PR136CommandActionMatrix.report.json",
    "day1_launch_readiness_policy": Path(
        "src/qtt/stage1_prediction_markets/launch_readiness/"
        "day1_launch_readiness_roadmap_policy.py"
    ),
    "pr_identity_roster": Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"),
    "roadmap_execution_state_controller": Path(
        "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"
    ),
    "post_pr135_day1_roadmap": Path(
        "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"
    ),
    "pr137r_atomicrows_reconciliation": GENERATED_DIR
    / "PR137R_AtomicRowsBundleReconciliation.report.json",
    "pr138_atomicrows_contract": GENERATED_DIR
    / "PR138_AtomicRowsSemanticRowContract.report.json",
}

PR82_PR96_ARTIFACT_NAMES = (
    "QuantumApplicabilityClassificationRegistry.report.json",
    "OwnerQuantumPriorityPolicyRegistry.report.json",
    "ParameterAlgorithmScoringPolicyRegistry.report.json",
    "ParameterStackScoringAndRankingGate.report.json",
    "QuantumClassicalOptimizerArbitrationGate.report.json",
    "CandidateParameterStackGenerationGate.report.json",
    "TradeContextParameterStackSelectionGate.report.json",
    "SelectedParameterStackHandoffPacket.report.json",
    "ReplayPaperCandidateStackCompetitionGate.report.json",
    "DualResultReviewForParameterStacks.report.json",
    "OwnerLivePromotionReviewForParameterStacks.report.json",
)

OWNER_APPROVALS = {
    "OWNER_GLOBAL_AUTHORITY": True,
    "OWNER_APPROVES_PR161D_QKU_QUALITY_TRIAGE": True,
    "OWNER_APPROVES_PR161D_QKU_SCORING_POLICY_CONSUMPTION": True,
    "OWNER_APPROVES_PR161D_QKU_CATEGORY_RANKING": True,
    "OWNER_APPROVES_PR161D_QKU_SCENARIO_OUTCOME_MATRIX": True,
    "OWNER_APPROVES_PR161D_QKU_ORDER_CONDITION_SCENARIO_REGISTRY": True,
    "OWNER_APPROVES_PR161D_QKU_BUNDLE_CANDIDATE_GENERATION": True,
    "OWNER_APPROVES_PR161D_QKU_RESULT_BACKED_RANKING_SLOTS": True,
    "OWNER_APPROVES_PR161D_QKU_FUTURE_PROFITABILITY_PATTERN_FIELDS": True,
    "OWNER_APPROVES_PR161D_QKU_ONLINE_ENRICHMENT_COVERAGE": True,
    "OWNER_APPROVES_OPEN_SOURCE_RESEARCH_SOCIAL_WEB_GITHUB_INTAKE_AS_QKU_SOURCES": True,
    "OWNER_APPROVES_NON_OFFICIAL_SOURCE_INTAKE_FOR_QKU_CANDIDATE_USE": True,
    "OWNER_REMOVES_OFFICIAL_SOURCE_ONLY_RESTRICTION_FOR_PR161D": True,
    "OWNER_APPROVES_ONLINE_SEARCH_FOR_ALL_QKU_FAMILIES": True,
    "OWNER_APPROVES_QKU_FAMILY_CLUSTERED_ONLINE_SEARCH": True,
    "OWNER_APPROVES_ALL_USEFUL_EXTERNAL_INFORMATION_INTO_CANDIDATE_LANES": True,
    "OWNER_APPROVES_OWNER_INTERNAL_DEFAULTS_AS_CANDIDATE_VALUES": True,
    "OWNER_APPROVES_AGGRESSIVE_DEFAULT_RANGE_SCALE_FILLING": True,
    "OWNER_APPROVES_QUANTUM_FORWARD_PRIORITIZATION": True,
    "OWNER_APPROVES_CLASSICAL_BASELINE_PRIORITIZATION": True,
    "OWNER_APPROVES_HYBRID_ARBITRATION_PRIORITIZATION": True,
    "OWNER_APPROVES_REPLAY_PAPER_AS_PROFIT_FILTER": True,
    "OWNER_APPROVES_OWNER_LIVE_PROMOTION_CONTROL": True,
    "OWNER_APPROVES_QKU_AGENT_TASK_QUEUE_GENERATION": True,
    "OWNER_APPROVES_QKU_AGENT_NETWORK_ROUTING": True,
    "OWNER_APPROVES_QKU_STAGE1_PREDICTION_MARKET_PRIORITY_SURFACES": True,
}

FORBIDDEN_AUTHORITY_POLICY = {
    "live_trading_created": False,
    "live_order_authority_created": False,
    "replay_execution_created": False,
    "paper_execution_created": False,
    "shadow_execution_created": False,
    "live_execution_created": False,
    "replay_result_created": False,
    "paper_result_created": False,
    "shadow_result_created": False,
    "live_result_created": False,
    "profit_evidence_created": False,
    "optimizer_execution_created": False,
    "quantum_backend_execution_created": False,
    "connector_semantic_binding_created": False,
    "private_state_receipt_created": False,
    "qtt_sha_authority_created": False,
    "qtt_generated_sha_created": False,
    "atomicrows_final_bundle_created": False,
    "atomicrows_bundle_freeze_authority_created": False,
}

SCORE_RANGE_MIN = 0
SCORE_RANGE_MAX = 1000
SCORE_COMPONENT_WEIGHTS = {
    "materialization_quality_component": 0.11,
    "stage1_fit_component": 0.11,
    "replay_paper_testability_component": 0.10,
    "agent_consumption_component": 0.08,
    "graph_component": 0.08,
    "atomicrows_pr154_component": 0.08,
    "source_coverage_component": 0.08,
    "risk_latency_capital_execution_component": 0.10,
    "strategy_algorithm_formula_component": 0.07,
    "quantum_forward_component": 0.07,
    "scenario_matrix_component": 0.04,
    "bundle_candidate_component": 0.04,
    "agent_network_component": 0.04,
}

QUALITY_LANES = (
    "QKU_QUALITY_LANE_A_DAY1_REPLAY_PAPER_PRIORITY",
    "QKU_QUALITY_LANE_B_STAGE1_AGENT_READY",
    "QKU_QUALITY_LANE_C_QUANTUM_FORWARD_COMPARE",
    "QKU_QUALITY_LANE_D_CLASSICAL_BASELINE_COMPARE",
    "QKU_QUALITY_LANE_E_HYBRID_ARBITRATION_COMPARE",
    "QKU_QUALITY_LANE_F_ONLINE_ENRICHMENT_NEEDED",
    "QKU_QUALITY_LANE_G_SOURCE_TRIANGULATION_NEEDED",
    "QKU_QUALITY_LANE_H_FUTURE_MARKET_HOLD",
    "QKU_QUALITY_LANE_I_FUTURE_RUNTIME_ONLY",
    "QKU_QUALITY_LANE_J_REJECTED_UNSAFE_OR_SECRET",
)
REPLAY_PAPER_PRIORITY_LANES = (
    "REPLAY_PAPER_PRIORITY_L0_DAY1_CRITICAL",
    "REPLAY_PAPER_PRIORITY_L1_HIGH",
    "REPLAY_PAPER_PRIORITY_L2_MEDIUM",
    "REPLAY_PAPER_PRIORITY_L3_LOW",
    "REPLAY_PAPER_PRIORITY_L4_ONLINE_ENRICHMENT_FIRST",
    "REPLAY_PAPER_PRIORITY_L5_FUTURE_MARKET_HOLD",
    "REPLAY_PAPER_PRIORITY_L6_NOT_TESTABLE_DOCTRINE_ONLY",
    "REPLAY_PAPER_PRIORITY_L7_REJECTED_UNSAFE_OR_SECRET",
)

SOURCE_CLASSES = (
    "OFFICIAL_VENUE_API_DOCS",
    "OFFICIAL_SDK_DOCS",
    "NON_OFFICIAL_RESEARCH_ARTICLE",
    "ACADEMIC_PAPER",
    "INSTITUTIONAL_RESEARCH",
    "PUBLIC_STRATEGY_NOTE",
    "PUBLIC_BLOG_POST",
    "PUBLIC_FORUM_POST",
    "PUBLIC_GITHUB_REPOSITORY",
    "PUBLIC_CODE_EXAMPLE",
    "PUBLIC_SOCIAL_POST",
    "PUBLIC_NEWS_ARTICLE",
    "PUBLIC_MARKET_COMMENTARY",
    "OPTIMIZER_ML_QUANTUM_DOCUMENTATION",
    "OWNER_PROVIDED_TEXT",
    "PRIOR_QTT_PR_ARTIFACT",
    "MASTER_PLAN_LITERAL",
    "PR136_ORCHESTRATION_ARTIFACT",
    "PR154_TARGET_ARTIFACT",
    "ATOMICROWS_COMPATIBLE_ARTIFACT",
)
SOURCE_ACCEPTANCE_STATES = (
    "SOURCE_ACCEPTED_FOR_QKU_CANDIDATE_SCORING_AND_REPLAY_PAPER_PRIORITIZATION",
    "SOURCE_REJECTED_UNSAFE",
    "SOURCE_REJECTED_IRRELEVANT",
    "SOURCE_REJECTED_UNMAPPABLE",
    "SOURCE_QUEUED_FOR_OWNER_REVIEW",
)
ONLINE_ENRICHMENT_STATES = (
    "ONLINE_ENRICHED_DIRECT_SOURCE_USED",
    "ONLINE_ENRICHED_CLUSTER_SOURCE_USED",
    "ONLINE_ENRICHED_SOURCE_FOUND_NOT_USED",
    "ONLINE_SCOUT_QUEUED",
    "ONLINE_SOURCE_NOT_REQUIRED_LOCAL_ARTIFACT_STRONG",
    "ONLINE_SEARCH_UNAVAILABLE",
    "ONLINE_SOURCE_REJECTED_UNSAFE",
    "ONLINE_SOURCE_REJECTED_IRRELEVANT",
    "ONLINE_SOURCE_REJECTED_UNMAPPABLE",
)

QUANTUM_PRIORITY_SUBCLASSES = (
    "QUBO_PRIORITY",
    "ISING_PRIORITY",
    "QAOA_PRIORITY",
    "VQE_PRIORITY",
    "ANNEALING_PRIORITY",
    "QUANTUM_PORTFOLIO_PRIORITY",
    "QUANTUM_CAPITAL_ALLOCATION_PRIORITY",
    "QUANTUM_MARKET_SELECTION_PRIORITY",
    "QUANTUM_SIGNAL_COMBINATION_PRIORITY",
    "QUANTUM_LATENCY_ROUTING_PRIORITY",
    "QUANTUM_ARBITRAGE_PATH_PRIORITY",
    "HYBRID_QUANTUM_CLASSICAL_PRIORITY",
    "QUANTUM_INSPIRED_PRIORITY",
    "QUANTUM_ADVISORY_PRIORITY",
)
REPLAY_PAPER_SCENARIO_FAMILIES = (
    "STAGE1_PREDICTION_MARKET_DIRECT",
    "STAGE1_PREDICTION_MARKET_INDIRECT",
    "QUANTUM_CLASSICAL_HYBRID_COMPARE",
    "QUBO_VS_CLASSICAL_COMPARE",
    "ISING_VS_CLASSICAL_COMPARE",
    "QAOA_VS_CLASSICAL_COMPARE",
    "VQE_VS_CLASSICAL_COMPARE",
    "ANNEALING_VS_CLASSICAL_COMPARE",
    "QUANTUM_INSPIRED_COMPARE",
    "QUANTUM_ADVISORY_COMPARE",
    "CLASSICAL_BASELINE_ONLY",
    "HYBRID_ARBITRATION_COMPARE",
    "ONLINE_ENRICHMENT_THEN_REPLAY",
    "RANGE_SENSITIVITY_REPLAY",
    "OPTIMIZER_CONFIG_SENSITIVITY_REPLAY",
    "LATENCY_SENSITIVITY_REPLAY",
    "RISK_CAPITAL_SENSITIVITY_REPLAY",
    "QKU_BUNDLE_COMBINATION_REPLAY",
    "QKU_SCENARIO_OUTCOME_MATRIX_REPLAY",
    "FUTURE_MARKET_HOLD",
    "NOT_TESTABLE_DOCTRINE_ONLY",
)
QUANTUM_CLASSICAL_HYBRID_CHILD_SCENARIO_FAMILIES = (
    "QUBO_VS_CLASSICAL_COMPARE",
    "ISING_VS_CLASSICAL_COMPARE",
    "QAOA_VS_CLASSICAL_COMPARE",
    "VQE_VS_CLASSICAL_COMPARE",
    "ANNEALING_VS_CLASSICAL_COMPARE",
    "HYBRID_ARBITRATION_COMPARE",
    "QUANTUM_INSPIRED_COMPARE",
    "QUANTUM_ADVISORY_COMPARE",
)

MARKET_BUNDLE_ACTIVATION_STATES = (
    "MARKET_BUNDLE_ACTIVE_STAGE1_REPLAY_PAPER",
    "MARKET_BUNDLE_ACTIVE_STAGE1_AGENT_SCORING",
    "MARKET_BUNDLE_ACTIVE_RESEARCH_ONLY",
    "MARKET_BUNDLE_DORMANT_FUTURE_STAGE",
    "MARKET_BUNDLE_OWNER_REVIEW_REQUIRED",
    "MARKET_BUNDLE_REJECTED_UNSAFE_OR_SECRET",
)
STAGE1_ACTIVE_BUNDLE_MARKET_STATES = (
    "MARKET_BUNDLE_ACTIVE_STAGE1_REPLAY_PAPER",
    "MARKET_BUNDLE_ACTIVE_STAGE1_AGENT_SCORING",
)
MARKET_BUNDLE_ACTIVATION_POLICY = {
    "PREDICTION_MARKET": "MARKET_BUNDLE_ACTIVE_STAGE1_REPLAY_PAPER",
    "MARKET_AGNOSTIC": "MARKET_BUNDLE_ACTIVE_STAGE1_REPLAY_PAPER",
    "NON_MARKET_SPECIFIC": "MARKET_BUNDLE_ACTIVE_STAGE1_REPLAY_PAPER",
    "MULTI_MARKET": "MARKET_BUNDLE_ACTIVE_RESEARCH_ONLY",
    "EQUITY_MARKET": "MARKET_BUNDLE_DORMANT_FUTURE_STAGE",
    "CRYPTO_MARKET": "MARKET_BUNDLE_DORMANT_FUTURE_STAGE",
    "FX_MARKET": "MARKET_BUNDLE_DORMANT_FUTURE_STAGE",
    "FUTURES_MARKET": "MARKET_BUNDLE_DORMANT_FUTURE_STAGE",
    "OPTIONS_MARKET": "MARKET_BUNDLE_DORMANT_FUTURE_STAGE",
    "FIXED_INCOME_MARKET": "MARKET_BUNDLE_DORMANT_FUTURE_STAGE",
    "COMMODITIES_MARKET": "MARKET_BUNDLE_DORMANT_FUTURE_STAGE",
}
FUTURE_MARKET_CLASSES = (
    "EQUITY_MARKET",
    "CRYPTO_MARKET",
    "FX_MARKET",
    "FUTURES_MARKET",
    "OPTIONS_MARKET",
    "FIXED_INCOME_MARKET",
    "COMMODITIES_MARKET",
)
CAP_EXEMPTION_AGENT_REFERENCE_FANOUT = (
    "AGENT_REFERENCE_FANOUT_NOT_MATERIALIZED_PER_AGENT_BUNDLE"
)
CAP_EXEMPTION_PARENT_AGGREGATE_SCENARIO_FAMILY = (
    "PARENT_AGGREGATE_SCENARIO_FAMILY_NOT_ACTIVE_CHILD_FAMILY"
)

QTT_AGENT_LAYERS = (
    "RESEARCH_KNOWLEDGE_LAYER",
    "SCORING_SELECTION_LAYER",
    "REPLAY_VALIDATION_LAYER",
    "RISK_CAPITAL_LAYER",
    "LATENCY_EXECUTION_PREP_LAYER",
    "OWNER_REVIEW_LAYER",
    "QKU_SERVICE_LAYER",
)
CANONICAL_QTT_AGENT_ROLES = (
    "QTT_RESEARCH_AGENT",
    "QTT_SOURCE_EVIDENCE_AGENT",
    "QTT_ATOMICROWS_ENRICHMENT_AGENT",
    "QTT_PARAMETER_STACK_AGENT",
    "QTT_OWNER_REVIEW_AGENT",
    "QTT_SCORING_AGENT",
    "QTT_RANKING_AGENT",
    "QTT_OPTIMIZER_ARBITRATION_AGENT",
    "QTT_QUANTUM_ADVISORY_AGENT",
    "QTT_REPLAY_AGENT",
    "QTT_PAPER_AGENT",
    "QTT_RISK_AGENT",
    "QTT_CAPITAL_AGENT",
    "QTT_LATENCY_AGENT",
    "QTT_EXECUTION_PREP_AGENT",
)
AGENT_ROLE_LAYER_PURPOSE = {
    "QTT_RESEARCH_AGENT": ("RESEARCH_KNOWLEDGE_LAYER", "discover_classify_enrich"),
    "QTT_SOURCE_EVIDENCE_AGENT": ("RESEARCH_KNOWLEDGE_LAYER", "source_coverage_labeling"),
    "QTT_ATOMICROWS_ENRICHMENT_AGENT": ("RESEARCH_KNOWLEDGE_LAYER", "atomicrows_enrichment"),
    "QTT_PARAMETER_STACK_AGENT": ("RESEARCH_KNOWLEDGE_LAYER", "parameter_stack_preparation"),
    "QTT_OWNER_REVIEW_AGENT": ("OWNER_REVIEW_LAYER", "owner_review_queue_preparation"),
    "QTT_SCORING_AGENT": ("SCORING_SELECTION_LAYER", "candidate_quality_scoring"),
    "QTT_RANKING_AGENT": ("SCORING_SELECTION_LAYER", "category_ranking"),
    "QTT_OPTIMIZER_ARBITRATION_AGENT": (
        "SCORING_SELECTION_LAYER",
        "optimizer_arbitration_preparation",
    ),
    "QTT_QUANTUM_ADVISORY_AGENT": (
        "SCORING_SELECTION_LAYER",
        "quantum_classical_hybrid_compare_preparation",
    ),
    "QTT_REPLAY_AGENT": ("REPLAY_VALIDATION_LAYER", "replay_input_preparation"),
    "QTT_PAPER_AGENT": ("REPLAY_VALIDATION_LAYER", "paper_test_requirements_preparation"),
    "QTT_RISK_AGENT": ("RISK_CAPITAL_LAYER", "risk_limit_preparation"),
    "QTT_CAPITAL_AGENT": ("RISK_CAPITAL_LAYER", "capital_allocation_preparation"),
    "QTT_LATENCY_AGENT": (
        "LATENCY_EXECUTION_PREP_LAYER",
        "latency_sensitivity_preparation",
    ),
    "QTT_EXECUTION_PREP_AGENT": (
        "LATENCY_EXECUTION_PREP_LAYER",
        "order_condition_preparation",
    ),
}
QKU_SERVICE_LAYER_DOMAINS = (
    "QTT_QKU_INVENTORY_SERVICE",
    "QTT_QKU_RETRIEVAL_SERVICE",
    "QTT_MARKET_CLASSIFICATION_SERVICE",
    "QTT_LAUNCH_STAGE_CLASSIFICATION_SERVICE",
    "QTT_QKU_ALIAS_RESOLUTION_SERVICE",
    "QTT_QKU_SCENARIO_MATRIX_SERVICE",
    "QTT_QKU_CATEGORY_RANKING_SERVICE",
    "QTT_QKU_BUNDLE_GENERATION_SERVICE",
    "QTT_QKU_RESULT_BACKED_RANKING_SERVICE",
    "QTT_QKU_AGENT_TASK_QUEUE_SERVICE",
)

AGENT_TASK_QUEUE_TYPES = (
    "QKU_AGENT_TASK_REPLAY_PAPER_PREP",
    "QKU_AGENT_TASK_ONLINE_ENRICHMENT",
    "QKU_AGENT_TASK_QUANTUM_COMPARE_PREP",
    "QKU_AGENT_TASK_CLASSICAL_BASELINE_PREP",
    "QKU_AGENT_TASK_HYBRID_ARBITRATION_PREP",
    "QKU_AGENT_TASK_RANGE_SENSITIVITY_PREP",
    "QKU_AGENT_TASK_OPTIMIZER_CONFIG_PREP",
    "QKU_AGENT_TASK_SOURCE_TRIANGULATION",
    "QKU_AGENT_TASK_SCENARIO_MATRIX_PREP",
    "QKU_AGENT_TASK_CATEGORY_RANKING_REVIEW",
    "QKU_AGENT_TASK_BUNDLE_REPLAY_PAPER_PREP",
    "QKU_AGENT_TASK_OWNER_REVIEW",
    "QKU_AGENT_TASK_FUTURE_MARKET_HOLD",
    "QKU_AGENT_TASK_REJECTED_UNSAFE_OR_SECRET",
)

SCENARIO_RESULT_STATES = (
    "NO_RESULT_YET",
    "REPLAY_RESULT_PENDING",
    "PAPER_RESULT_PENDING",
    "SHADOW_RESULT_PENDING",
    "LIVE_RESULT_PENDING",
    "NOT_TESTABLE_DOCTRINE_ONLY",
    "FUTURE_MARKET_HOLD",
    "REJECTED_UNSAFE_OR_SECRET",
)
FUTURE_PROFITABILITY_LABELS = (
    "UNOBSERVED",
    "PROFITABLE_AFTER_COSTS",
    "NON_PROFITABLE_AFTER_COSTS",
    "BREAK_EVEN_AFTER_COSTS",
    "PROFITABLE_BUT_HIGH_DRAWDOWN",
    "PROFITABLE_BUT_LOW_CONFIDENCE",
    "NON_PROFITABLE_BUT_DIAGNOSTICALLY_USEFUL",
    "INSUFFICIENT_SAMPLE",
    "REGIME_SPECIFIC",
    "REJECTED_UNSAFE_OR_SECRET",
)
QKU_BUNDLE_MIX_CLASSES = (
    "signal_qkus",
    "feature_qkus",
    "risk_qkus",
    "capital_qkus",
    "execution_qkus",
    "latency_qkus",
    "market_microstructure_qkus",
    "strategy_template_qkus",
    "formula_qkus",
    "algorithm_qkus",
    "optimizer_setting_qkus",
    "quantum_candidate_qkus",
    "classical_baseline_qkus",
    "hybrid_arbitration_qkus",
    "atomicrows_qkus",
    "pr154_target_qkus",
)
CATEGORY_RANKING_MODES = ("PRE_RESULT_RANKING", "RESULT_BACKED_RANKING")
RESULT_BACKED_RANKING_SLOT_STATES = (
    "NO_RESULT_YET",
    "RESULT_SLOT_RESERVED",
    "RESULT_ARTIFACT_REQUIRED",
)

FUTURE_PROFITABILITY_PATTERN_FIELD_DEFAULTS = {
    "future_net_profit_total": None,
    "future_net_profit_per_trade": None,
    "future_profit_after_fees": None,
    "future_slippage_cost": None,
    "future_max_drawdown": None,
    "future_win_rate": None,
    "future_loss_rate": None,
    "future_profit_factor": None,
    "future_risk_adjusted_return": None,
    "future_sample_size": 0,
    "future_confidence_class": "UNOBSERVED",
    "future_regime_stability_score": None,
    "future_recent_performance_score": None,
    "future_negative_pattern_flag": False,
    "future_positive_pattern_flag": False,
    "future_scenario_similarity_key": "UNOBSERVED",
    "future_best_qku_combination_for_scenario_flag": False,
    "future_avoid_qku_combination_for_scenario_flag": False,
}

MAX_QKU_BUNDLE_CANDIDATES = 12000
MAX_BUNDLES_PER_SCENARIO_FAMILY = 500
MAX_BUNDLES_PER_AGENT_ROLE = 1500
MAX_QKUS_PER_BUNDLE = 12

REPORT_FILENAMES = (
    "PR161D_QKU_CANDIDATE_QUALITY_PREFLIGHT_RECEIPT.report.json",
    "PR161D_QKUOnlineSearchCapabilityReceipt.report.json",
    "PR161D_QKUQualityScoreRegistry.report.json",
    "PR161D_QKUScoreComponentBreakdown.report.json",
    "PR161D_QKUQualityLaneClassification.report.json",
    "PR161D_QKUReplayPaperPriorityQueue.report.json",
    "PR161D_QKUReplayPaperScenarioInputs.report.json",
    "PR161D_QKUOnlineEnrichmentClusterMap.report.json",
    "PR161D_QKUOnlineEnrichmentCoverage.report.json",
    "PR161D_QKUOnlineSourceCandidateRegistry.report.json",
    "PR161D_QKUQuantumPriorityQueue.report.json",
    "PR161D_QKUClassicalBaselinePriorityQueue.report.json",
    "PR161D_QKUHybridArbitrationPriorityQueue.report.json",
    "PR161D_QKUAtomicRowsPR154PriorityBridge.report.json",
    "PR161D_QKUAgentTaskQueue.report.json",
    "PR161D_QTTAgentRoleNetworkRegistry.report.json",
    "PR161D_QKUAgentGraphRoutingMatrix.report.json",
    "PR161D_QKUAgentLayerCoverage.report.json",
    "PR161D_QKUAgentRoleCoverageGaps.report.json",
    "PR161D_QKUStage1Day1PriorityIndex.report.json",
    "PR161D_QKUOwnerReviewQueue.report.json",
    "PR161D_QKUGraphConsumptionAudit.report.json",
    "PR161D_QKUScoringPolicyConsumptionAudit.report.json",
    "PR161D_QKUScenarioOutcomeMatrix.report.json",
    "PR161D_QKUOrderConditionScenarioRegistry.report.json",
    "PR161D_QKUCombinationCandidateRegistry.report.json",
    "PR161D_QKUCombinationScenarioMap.report.json",
    "PR161D_QKUCombinationReplayPaperPriorityQueue.report.json",
    "PR161D_QKUCombinationGenerationBoundedness.report.json",
    "PR161D_QKUMarketBundleActivationPolicy.report.json",
    "PR161D_QKUMarketBundleActivationDashboardOptions.report.json",
    "PR161D_QKUMarketBundleDormancyQueue.report.json",
    "PR161D_QKUMarketActiveBundleSet.report.json",
    "PR161D_QKUAgentRoleBundleSlice.report.json",
    "PR161D_QKUAgentRoleBundleReferenceFanout.report.json",
    "PR161D_QKUCategoryRankingRegistry.report.json",
    "PR161D_QKUCategoryTopListIndex.report.json",
    "PR161D_QKUCategoryRankingBreakdown.report.json",
    "PR161D_QKUFutureProfitabilityPatternFields.report.json",
    "PR161D_QKUResultBackedRankingSlots.report.json",
    "PR161D_QKUForbiddenAuthorityScan.report.json",
    "PR161D_NoScatteredHardcodedAuthorityAudit.report.json",
    "PR161D_ReportShardManifest.report.json",
    "PR161D_FinalSummary.report.json",
)

SCHEMA_ENUM_FIELDS = {
    "quality_lane": QUALITY_LANES,
    "replay_paper_priority_lane": REPLAY_PAPER_PRIORITY_LANES,
    "online_enrichment_coverage_state": ONLINE_ENRICHMENT_STATES,
    "source_class": SOURCE_CLASSES,
    "source_acceptance_state": SOURCE_ACCEPTANCE_STATES,
    "qku_quantum_priority_subclass": QUANTUM_PRIORITY_SUBCLASSES,
    "assigned_agent_role": CANONICAL_QTT_AGENT_ROLES,
    "agent_role": CANONICAL_QTT_AGENT_ROLES,
    "canonical_agent_layer": QTT_AGENT_LAYERS,
    "agent_layer": QTT_AGENT_LAYERS,
    "task_queue_type": AGENT_TASK_QUEUE_TYPES,
    "result_state": SCENARIO_RESULT_STATES,
    "profitability_label": FUTURE_PROFITABILITY_LABELS,
    "ranking_basis": CATEGORY_RANKING_MODES,
    "bundle_market_activation_state": MARKET_BUNDLE_ACTIVATION_STATES,
    "current_activation_state": MARKET_BUNDLE_ACTIVATION_STATES,
    "default_activation_state": MARKET_BUNDLE_ACTIVATION_STATES,
}

ONLINE_SEARCH_RECORDED_AT_UTC = "2026-05-30T00:00:00Z"
ONLINE_SEARCH_ATTEMPT_COUNT = 8
ONLINE_SEARCH_SUCCESS_COUNT = 8

ONLINE_SOURCE_CANDIDATES = (
    {
        "source_id": "PR161D-ONLINE-SOURCE-0001",
        "source_title": "Polymarket API Reference",
        "source_url": "https://docs.polymarket.com/api-reference",
        "source_class": "OFFICIAL_VENUE_API_DOCS",
        "source_family": "PREDICTION_MARKET_ORDERBOOK_API",
        "cluster_tags": ("PREDICTION_MARKET", "ORDERBOOK", "POLYMARKET", "DIRECT"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0002",
        "source_title": "Polymarket WebSocket Market Data Overview",
        "source_url": "https://docs.polymarket.com/market-data/websocket/overview",
        "source_class": "OFFICIAL_VENUE_API_DOCS",
        "source_family": "PREDICTION_MARKET_WEBSOCKET_ORDERBOOK",
        "cluster_tags": ("PREDICTION_MARKET", "ORDERBOOK", "LATENCY", "DIRECT"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0003",
        "source_title": "Kwery Prediction Market and Crypto Market Data API",
        "source_url": "https://www.kwery.xyz/",
        "source_class": "PUBLIC_MARKET_COMMENTARY",
        "source_family": "NORMALIZED_PREDICTION_MARKET_HISTORICAL_DATA",
        "cluster_tags": ("PREDICTION_MARKET", "BACKTEST", "REPLAY", "NON_OFFICIAL"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0004",
        "source_title": "Oddpool PredictionMarketBench",
        "source_url": "https://github.com/Oddpool/PredictionMarketBench",
        "source_class": "PUBLIC_GITHUB_REPOSITORY",
        "source_family": "PREDICTION_MARKET_BACKTEST_REPLAY",
        "cluster_tags": ("PREDICTION_MARKET", "BACKTEST", "KALSHI", "GITHUB"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0005",
        "source_title": "Polymarket Paper Trader",
        "source_url": "https://github.com/agent-next/polymarket-paper-trader",
        "source_class": "PUBLIC_GITHUB_REPOSITORY",
        "source_family": "PREDICTION_MARKET_PAPER_TRADING",
        "cluster_tags": ("PREDICTION_MARKET", "PAPER", "SLIPPAGE", "GITHUB"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0006",
        "source_title": "HftBacktest",
        "source_url": "https://github.com/nkaz001/hftbacktest",
        "source_class": "PUBLIC_GITHUB_REPOSITORY",
        "source_family": "ORDERBOOK_LATENCY_REPLAY",
        "cluster_tags": ("ORDERBOOK", "LATENCY", "REPLAY", "GITHUB"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0007",
        "source_title": "QuantReplay",
        "source_url": "https://github.com/Quod-Financial/quantreplay",
        "source_class": "PUBLIC_GITHUB_REPOSITORY",
        "source_family": "MARKET_MICROSTRUCTURE_SIMULATION",
        "cluster_tags": ("ORDERBOOK", "SLIPPAGE", "LATENCY", "GITHUB"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0008",
        "source_title": "lobsim L3 Limit Order Book Replay",
        "source_url": "https://github.com/kpetridis24/lobsim",
        "source_class": "PUBLIC_GITHUB_REPOSITORY",
        "source_family": "LIMIT_ORDER_BOOK_PAPER_EXECUTION",
        "cluster_tags": ("ORDERBOOK", "PAPER", "EXECUTION", "GITHUB"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0009",
        "source_title": "Quantum-Assisted Optimal Rebalancing via QUBO Scheduling and QAOA",
        "source_url": "https://arxiv.org/abs/2603.16904",
        "source_class": "ACADEMIC_PAPER",
        "source_family": "QUANTUM_PORTFOLIO_QUBO_QAOA",
        "cluster_tags": ("QUANTUM", "QUBO", "QAOA", "PORTFOLIO"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0010",
        "source_title": "Constrained Portfolio Optimization via QAOA",
        "source_url": "https://arxiv.org/abs/2602.14827",
        "source_class": "ACADEMIC_PAPER",
        "source_family": "QUANTUM_PORTFOLIO_QAOA_CLASSICAL_BASELINE",
        "cluster_tags": ("QUANTUM", "QAOA", "PORTFOLIO", "CLASSICAL_BASELINE"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0011",
        "source_title": "OpenQuantumComputing QAOA",
        "source_url": "https://github.com/OpenQuantumComputing/QAOA",
        "source_class": "PUBLIC_GITHUB_REPOSITORY",
        "source_family": "QAOA_RESEARCH_TOOLING",
        "cluster_tags": ("QUANTUM", "QAOA", "OPTIMIZER", "GITHUB"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0012",
        "source_title": "Hybrid Quantum Classical Simulations",
        "source_url": "https://arxiv.org/abs/2210.02811",
        "source_class": "ACADEMIC_PAPER",
        "source_family": "HYBRID_QUANTUM_CLASSICAL_QAOA_VQE",
        "cluster_tags": ("QUANTUM", "HYBRID", "QAOA", "VQE"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0013",
        "source_title": "Bayesian Kelly Criterion with Parameter Uncertainty",
        "source_url": "https://papers.ssrn.com/sol3/Delivery.cfm/6195358.pdf?abstractid=6195358&mirid=1",
        "source_class": "ACADEMIC_PAPER",
        "source_family": "RISK_CAPITAL_POSITION_SIZING",
        "cluster_tags": ("RISK", "CAPITAL", "KELLY", "POSITION_SIZING"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0014",
        "source_title": "Prediction Market Backtesting",
        "source_url": "https://github.com/evan-kolberg/prediction-market-backtesting",
        "source_class": "PUBLIC_GITHUB_REPOSITORY",
        "source_family": "PREDICTION_MARKET_BACKTESTING_ADAPTERS",
        "cluster_tags": ("PREDICTION_MARKET", "BACKTEST", "POLYMARKET", "GITHUB"),
    },
    {
        "source_id": "PR161D-ONLINE-SOURCE-0015",
        "source_title": "Homerun Prediction Market Trading Platform",
        "source_url": "https://github.com/braedonsaunders/homerun",
        "source_class": "PUBLIC_GITHUB_REPOSITORY",
        "source_family": "PREDICTION_MARKET_REPLAY_PAPER_RISK",
        "cluster_tags": ("PREDICTION_MARKET", "PAPER", "RISK", "GITHUB"),
    },
)
