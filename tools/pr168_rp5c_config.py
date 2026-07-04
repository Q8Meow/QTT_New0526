#!/usr/bin/env python3
"""Central configuration for PR168-RP5C immutable QKU/formula library reclaim."""

from __future__ import annotations

from pathlib import Path
from typing import Final


REPO_ROOT: Final = Path(__file__).resolve().parents[1]
GENERATED_ROOT: Final = REPO_ROOT / "docs" / "master_plan" / "generated"
SHARD_ROOT: Final = GENERATED_ROOT / "rp5c"

REPORT_VERSION: Final = "PR168-RP5C-v1.0"
CREATED_AT_UTC: Final = "2026-06-25T00:00:00Z"
BRANCH_NAME: Final = "pr168-rp5c-immutable-qku-formula-library"
BASE_BRANCH: Final = "main"
POST_MERGE_REPAIR_BRANCH_NAME: Final = "pr168-rp5c-postmerge-ci-repair"
VS1_CONSUMER_BRANCH_NAME: Final = "pr168-vs1-trading-intelligence-vertical-slice"
RP5D_CONSUMER_BRANCH_NAME: Final = "pr168-rp5d-replay-paper-executability-tiers"
RP5E_CONSUMER_BRANCH_NAME: Final = "pr168-rp5e-stack-gen"
RP5D_R1_CONSUMER_BRANCH_NAME: Final = "pr168-rp5d-r1-exec-now-unlock"
RP5F_CONSUMER_BRANCH_NAME: Final = "pr168-rp5f-dynamic-target-order-grid"
RANK4_CONSUMER_BRANCH_NAME: Final = "pr168-rank4-exec-advisory-ranking"
QOPT1_CONSUMER_BRANCH_NAME: Final = (
    "pr168-qopt1-quantum-classical-batch-optimization"
)
VS2_CONSUMER_BRANCH_NAME: Final = "pr168-vs2-paper-intent-candidate-generator"
MEM1_CONSUMER_BRANCH_NAME: Final = "pr168-mem1-condition-scoped-outcome-memory"
DASH1_UI1_VALIDATION_BRANCH_NAME: Final = "pr169-dash1-ui1-theme-switch-safe-renderer-v9"
DASH1_UI1_R1_VALIDATION_BRANCH_NAME: Final = "pr169-dash1-ui1-r1-v3-owner12"
DASH1_UI1_R2_VALIDATION_BRANCH_NAME: Final = "pr169-dash1-ui1-r2-guided-owner-coach-v7"
ALLOWED_BUILD_BRANCH_NAMES: Final = (
    BRANCH_NAME,
    BASE_BRANCH,
    POST_MERGE_REPAIR_BRANCH_NAME,
    VS1_CONSUMER_BRANCH_NAME,
    RP5D_CONSUMER_BRANCH_NAME,
    RP5E_CONSUMER_BRANCH_NAME,
    RP5D_R1_CONSUMER_BRANCH_NAME,
    RP5F_CONSUMER_BRANCH_NAME,
    RANK4_CONSUMER_BRANCH_NAME,
    QOPT1_CONSUMER_BRANCH_NAME,
    VS2_CONSUMER_BRANCH_NAME,
    MEM1_CONSUMER_BRANCH_NAME,
    DASH1_UI1_VALIDATION_BRANCH_NAME,
    DASH1_UI1_R1_VALIDATION_BRANCH_NAME,
    DASH1_UI1_R2_VALIDATION_BRANCH_NAME,
)
ROADMAP_PR: Final = "PR168-RP5C"
PR_TITLE: Final = "PR168-RP5C: Immutable QKU/formula library reclaim from active registry"

MAX_TOTAL_ROWS_PER_SHARD: Final = 500_000
MAX_JSON_PARSE_BYTES: Final = 8_000_000
MAX_RECORDS_PER_ARTIFACT: Final = 50_000
MAX_TOTAL_PARSED_RECORDS: Final = 250_000

ONTOLOGY_CATEGORIES: Final = (
    "signal_probability",
    "calibration",
    "market_implied_probability",
    "tca_cost",
    "fill_queue_liquidity",
    "latency_staleness",
    "capacity_crowding",
    "portfolio_risk",
    "regime_scenario",
    "exit_timing",
    "quantum_objective_constraint",
    "classical_fallback",
    "governance_source_risk",
    "unknown_needs_review",
)

MARKET_SCOPES: Final = (
    "prediction_market",
    "market_agnostic",
    "equities",
    "options",
    "futures_commodities",
    "crypto",
    "fx_macro",
    "fixed_income",
    "repo_financing",
    "cross_market",
    "unknown_needs_review",
)

MASTER_PLAN_MARKET_FAMILIES: Final = (
    "PREDICTION_MARKETS",
    "EQUITIES_AND_ETFS",
    "CRYPTO_SPOT",
    "CRYPTO_DERIVATIVES",
    "LISTED_OPTIONS",
    "EXCHANGE_TRADED_FUTURES_AND_COMMODITIES",
    "MACRO_FX_EVENT",
    "SECURITIES_FINANCING_AND_REPO",
    "FIXED_INCOME_RFQ",
    "CROSS_MARKET_RELATIVE_VALUE",
)

MARKET_APPLICABILITY_MODES: Final = (
    "MARKET_SPECIFIC",
    "CROSS_MARKET_SHARED",
    "UNKNOWN_NEEDS_REVIEW",
)

STAGE_ACCESS_MODES: Final = (
    "DEFAULT_COMPUTE",
    "AVAILABLE_ON_DEMAND",
    "INACTIVE_FOR_STAGE",
    "UNKNOWN_NEEDS_REVIEW",
)

STAGE1_PROFILE_ID: Final = "STAGE1_PREDICTION_MARKETS"
STAGE1_ENABLED_MARKET_FAMILIES: Final = ("PREDICTION_MARKETS",)
STAGE1_ENABLED_PLATFORMS: Final = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")

LIBRARY_VERSION: Final = "ImmutableQKUFormulaLibraryV1"
APPLICABILITY_MATRIX_VERSION: Final = "QKUMarketApplicabilityMatrixV1"
STAGE_PROFILE_VERSION: Final = "MarketStageActivationProfileRegistryV1"
AGENT_ACCESS_POLICY_VERSION: Final = "AgentQKUAccessPolicyRegistryV1"

AUTHORITATIVE_CENTRAL_LAYER_SHARDS: Final = (
    "immutable_qku_formula_library",
    "qku_market_applicability_matrix",
    "market_stage_activation_profile_registry",
    "agent_qku_access_policy_registry",
)

DEPENDENCY_TYPES: Final = (
    "signal_dependency",
    "calibration_dependency",
    "market_data_dependency",
    "source_evidence_dependency",
    "formula_expression_dependency",
    "formula_to_pnl_dependency",
    "tca_dependency",
    "fill_liquidity_dependency",
    "latency_dependency",
    "capacity_dependency",
    "portfolio_risk_dependency",
    "regime_scenario_dependency",
    "exit_timing_dependency",
    "quantum_objective_dependency",
    "quantum_constraint_dependency",
    "classical_fallback_dependency",
    "governance_dependency",
    "unknown_needs_review",
)

LIBRARY_STATES: Final = (
    "LIBRARY_ELIGIBLE_IMMUTABLE",
    "DUPLICATE_PRESERVED_LOW_PRIORITY",
    "PRESERVED_NEEDS_EXECUTION_CONTRACT",
    "UNSAFE_UNMAPPABLE_PRESERVED_NOT_EXECUTED",
    "NEEDS_FORMULA_EXPRESSION_REF",
    "NEEDS_FORMULA_TO_PNL_MAP",
    "NEEDS_PLUGIN_CONTRACT",
    "NEEDS_AGENT_ROUTE",
    "NEEDS_VALIDATOR_ROUTE",
    "NEEDS_SOURCE_ARTIFACT_ROUTE",
    "NEEDS_FAMILY_CLASSIFICATION",
    "NEEDS_MARKET_SCOPE_CLASSIFICATION",
    "NEEDS_ONTOLOGY_CLASSIFICATION",
    "NEEDS_RP5D_EXECUTABILITY_REVIEW",
)

ROUTE_RESOLUTION_STATES: Final = (
    "ROUTE_RESOLVED_FROM_PR165_D2_AGENT_DUTY",
    "ROUTE_RESOLVED_FROM_EXISTING_AGENT_MANIFEST",
    "ROUTE_RESOLVED_FROM_CENTRAL_RULEBOOK_FALLBACK",
    "ROUTE_PARTIAL_NEEDS_AGENT_DUTY_INPUT",
    "ROUTE_PARTIAL_NEEDS_VALIDATOR_ROUTE",
    "ROUTE_UNRESOLVED_NEEDS_AGENT_ROUTE",
    "ROUTE_UNRESOLVED_NEEDS_MARKET_SCOPE",
    "ROUTE_UNRESOLVED_NEEDS_ONTOLOGY",
    "ROUTE_UNRESOLVED_NEEDS_FAMILY",
    "ROUTE_UNRESOLVED_NEEDS_REVIEW",
)

STAGE1_CLASSIFICATION_STATES: Final = (
    "STAGE1_PREDICTION_MARKET_ACTIVE_CANDIDATE",
    "STAGE1_PREDICTION_MARKET_SUPPORTING_MARKET_AGNOSTIC",
    "THREE_PLATFORM_COMMON",
    "KALSHI_APPLICABLE",
    "POLYMARKET_APPLICABLE",
    "FORECASTEX_IBKR_APPLICABLE",
    "PLATFORM_SPECIFIC_NEEDS_SOURCE_BINDING",
    "FUTURE_MARKET_DORMANT",
    "CROSS_MARKET_REVIEW_REQUIRED",
    "UNKNOWN_MARKET_SCOPE_NEEDS_REVIEW",
)

PLATFORM_APPLICABILITY_STATES: Final = (
    "KALSHI_APPLICABLE",
    "POLYMARKET_APPLICABLE",
    "FORECASTEX_IBKR_APPLICABLE",
    "THREE_PLATFORM_COMMON",
    "PREDICTION_MARKET_GENERIC",
    "PLATFORM_SPECIFIC_NEEDS_SOURCE_BINDING",
    "NOT_STAGE1_PLATFORM_APPLICABLE",
    "UNKNOWN_PLATFORM_SCOPE_NEEDS_REVIEW",
)

PROVENANCE_TIERS: Final = (
    "ACTIVE_CANONICAL_REGISTRY",
    "RP5C_CENTRAL_ACTIVE_SURFACE",
    "RP5B_PRESERVED_ACTIVE_REGISTRY_INPUT",
    "RP5B_LEGACY_KEEP_REASON_PRESERVED",
    "RP5B_SEMANTIC_SUPERSESSION_INPUT",
    "RP5A_IDENTITY_DEPENDENCY",
    "RP5A_IDENTITY_CUSTODY",
    "PR165_D2_AGENT_DUTY_INPUT",
    "UPSTREAM_FORMULA_QKU_REGISTRY",
    "CANDIDATE_PACKET_IDENTITY_SURFACE",
    "GENERATED_REPORT_HISTORICAL_EVIDENCE",
    "RAW_LEGACY_HISTORICAL_EVIDENCE_ONLY",
    "UNKNOWN_NEEDS_REVIEW",
)

CONSUMPTION_STATUSES: Final = (
    "CONSUMED_TO_IDENTITY_ROWS",
    "CONSUMED_AS_ACTIVE_AUTHORITY_LAYER",
    "CONSUMED_AS_SEMANTIC_SUPERSESSION_LAYER",
    "CONSUMED_AS_AGENT_DUTY_ROUTE_LAYER",
    "CONSUMED_AS_VALIDATION_CONTEXT",
    "CONSUMED_AS_HISTORICAL_EVIDENCE_ONLY",
    "NO_QKU_FORMULA_IDENTITY_FOUND_ROUTED_TO_REVIEW",
    "MISSING_EXPECTED_INPUT_RECORDED",
    "DUPLICATE_INPUT_ARTIFACT_PRESERVED",
    "UNSUPPORTED_FORMAT_RECORDED_NEEDS_REVIEW",
)

HARD_ZERO_COUNTERS: Final = {
    "deleted_file_count": 0,
    "archived_file_count": 0,
    "moved_file_count": 0,
    "master_plan_content_deleted_or_shortened_count": 0,
    "formula_expression_mutation_count": 0,
    "qku_identity_deleted_count": 0,
    "formula_identity_deleted_count": 0,
    "global_formula_ban_count": 0,
    "global_qku_ban_count": 0,
    "runtime_stack_generation_count": 0,
    "stack_combination_materialization_count": 0,
    "trade_simulation_count": 0,
    "formula_profit_ranking_count": 0,
    "rank4_ranking_count": 0,
    "qopt_batch_count": 0,
    "paper_loop_runtime_count": 0,
    "live_order_authority_created_count": 0,
    "source_truth_authority_created_count": 0,
    "champion_authority_created_count": 0,
    "launch_readiness_authority_created_count": 0,
    "quantum_backend_execution_count": 0,
    "quantum_advantage_claim_count": 0,
    "qtt_sha_or_atomicrows_hash_authority_count": 0,
    "connector_semantic_binding_count": 0,
    "private_state_fetch_count": 0,
    "runtime_cash_receipt_count": 0,
    "silent_skipped_input_artifact_count": 0,
    "orphan_source_artifact_count": 0,
    "orphan_input_report_count": 0,
    "orphan_identity_count": 0,
    "orphan_generated_shard_count": 0,
    "raw_legacy_direct_agent_consumer_count": 0,
    "manual_per_qku_hardcoded_agent_assignment_count": 0,
    "mutable_agent_ownership_embedded_as_identity_authority_count": 0,
    "generated_path_case_collision_count": 0,
    "absolute_local_path_leak_count": 0,
    "backslash_only_path_leak_count": 0,
    "stage1_default_full_universe_compute_route_count": 0,
    "non_prediction_market_qku_stage1_active_count": 0,
    "dormant_qku_deleted_count": 0,
    "dormant_qku_global_ban_count": 0,
}

REPORT_NAMES: Final = (
    "PR168_RP5C_Input.report.json",
    "PR168_RP5C_Preflight.report.json",
    "PR168_RP5C_RP5BInputIntegrity.report.json",
    "PR168_RP5C_AgentDutyInput.report.json",
    "PR168_RP5C_SourceArtifactConsumptionLedger.report.json",
    "PR168_RP5C_ImmutableQKULibrary.report.json",
    "PR168_RP5C_ImmutableFormulaLibrary.report.json",
    "PR168_RP5C_ImmutableQKUFormulaLibrary.report.json",
    "PR168_RP5C_QKUFormulaFamilyRegistry.report.json",
    "PR168_RP5C_MarketScopeFamilyRegistry.report.json",
    "PR168_RP5C_OntologyRoleRegistry.report.json",
    "PR168_RP5C_FormulaAssignmentLibrary.report.json",
    "PR168_RP5C_QKUFormulaIdentityLineage.report.json",
    "PR168_RP5C_IdentityDeduplicationLedger.report.json",
    "PR168_RP5C_IdentityProvenanceTier.report.json",
    "PR168_RP5C_FormulaOntology.report.json",
    "PR168_RP5C_AgentResponsibilityGroupRegistry.report.json",
    "PR168_RP5C_AgentDutyRoutingRulebook.report.json",
    "PR168_RP5C_DerivedAgentRouteResolutionLedger.report.json",
    "PR168_RP5C_FileToDerivedRouteCrosswalk.report.json",
    "PR168_RP5C_NoGlobalBanProof.report.json",
    "PR168_RP5C_NoOrphanIdentityProof.report.json",
    "PR168_RP5C_NoOrphanSourceArtifactProof.report.json",
    "PR168_RP5C_NoOrphanGeneratedSurfaceProof.report.json",
    "PR168_RP5C_CentralSurfaceManifest.report.json",
    "PR168_RP5C_Stage1PredictionMarketQKUActivationView.report.json",
    "PR168_RP5C_PlatformApplicabilityRegistry.report.json",
    "PR168_RP5C_DormantFutureMarketQKULedger.report.json",
    "PR168_RP5C_Stage1AgentComputationUniverseSeed.report.json",
    "PR168_RP5C_MachineConsumableLibraryAccess.report.json",
    "PR168_RP5C_AgentQKUAccessContract.report.json",
    "PR168_RP5C_StageAgentUniverseResolutionProof.report.json",
    "PR168_RP5C_ToVS1TradingIntelligenceHandoff.report.json",
    "PR168_RP5C_MarketScopeClassificationQualityAudit.report.json",
    "PR168_RP5C_CrossOSPathPortabilityAudit.report.json",
    "PR168_RP5C_PathAudit.report.json",
    "PR168_RP5C_ToRP5DExecutabilityHandoff.report.json",
    "PR168_RP5C_FinalSummary.report.json",
)

ROW_SHARDS: Final = {
    "source_artifact_consumption_ledger": "source_artifact_consumption_ledger.jsonl",
    "input_artifact_to_identity_coverage": "input_artifact_to_identity_coverage.jsonl",
    "immutable_qku_library": "immutable_qku_library.jsonl",
    "immutable_formula_library": "immutable_formula_library.jsonl",
    "immutable_qku_formula_library": "immutable_qku_formula_library.jsonl",
    "qku_formula_family_registry": "qku_formula_family_registry.jsonl",
    "market_scope_family_registry": "market_scope_family_registry.jsonl",
    "ontology_role_registry": "ontology_role_registry.jsonl",
    "formula_assignment_library": "formula_assignment_library.jsonl",
    "qku_formula_identity_lineage": "qku_formula_identity_lineage.jsonl",
    "identity_deduplication_ledger": "identity_deduplication_ledger.jsonl",
    "identity_provenance_tier": "identity_provenance_tier.jsonl",
    "formula_ontology": "formula_ontology.jsonl",
    "agent_responsibility_group_registry": "agent_responsibility_group_registry.jsonl",
    "agent_duty_routing_rulebook": "agent_duty_routing_rulebook.jsonl",
    "derived_agent_route_resolution_ledger": "derived_agent_route_resolution_ledger.jsonl",
    "file_to_derived_route_crosswalk": "file_to_derived_route_crosswalk.jsonl",
    "no_global_ban_rows": "no_global_ban_rows.jsonl",
    "no_orphan_identity_rows": "no_orphan_identity_rows.jsonl",
    "no_orphan_source_artifact_rows": "no_orphan_source_artifact_rows.jsonl",
    "no_orphan_generated_surface_rows": "no_orphan_generated_surface_rows.jsonl",
    "qku_market_applicability_matrix": "qku_market_applicability_matrix.jsonl",
    "market_stage_activation_profile_registry": "market_stage_activation_profile_registry.jsonl",
    "agent_qku_access_policy_registry": "agent_qku_access_policy_registry.jsonl",
    "stage_agent_qku_universe_resolver": "stage_agent_qku_universe_resolver.jsonl",
    "stage_computation_universe_view": "stage_computation_universe_view.jsonl",
    "agent_computation_universe_view": "agent_computation_universe_view.jsonl",
    "library_query_receipts": "library_query_receipts.jsonl",
    "vs1_trading_intelligence_handoff": "vs1_trading_intelligence_handoff.jsonl",
    "stage1_prediction_market_qku_activation_view": "stage1_prediction_market_qku_activation_view.jsonl",
    "platform_applicability_registry": "platform_applicability_registry.jsonl",
    "dormant_future_market_qku_ledger": "dormant_future_market_qku_ledger.jsonl",
    "stage1_agent_computation_universe_seed": "stage1_agent_computation_universe_seed.jsonl",
    "market_family_reclassification_ledger": "market_family_reclassification_ledger.jsonl",
    "shared_cross_market_support_pool": "shared_cross_market_support_pool.jsonl",
    "market_specific_qku_pool_registry": "market_specific_qku_pool_registry.jsonl",
    "rp5d_executability_handoff": "rp5d_executability_handoff.jsonl",
    "identity_quality_gap_queue": "identity_quality_gap_queue.jsonl",
}

EXPECTED_INPUT_ARTIFACTS: Final = (
    "docs/master_plan/generated/PR168_RP5B_ActiveArtifactRegistry.report.json",
    "docs/master_plan/generated/PR168_RP5B_LegacySemanticSupersession.report.json",
    "docs/master_plan/generated/PR168_RP5B_NoRawLegacyDecisionAuthority.report.json",
    "docs/master_plan/generated/PR168_RP5B_LegacyKeepReasonLedger.report.json",
    "docs/master_plan/generated/PR168_RP5B_SafeDeletionVerification.report.json",
    "docs/master_plan/generated/PR168_RP5B_DeletedFromActiveTreeManifest.report.json",
    "docs/master_plan/generated/PR168_RP5B_ValidationScopeReduction.report.json",
    "docs/master_plan/generated/PR168_RP5B_QKUFormulaIdentityPreservation.report.json",
    "docs/master_plan/generated/PR168_RP5B_Input.report.json",
    "docs/master_plan/generated/PR168_RP5B_PathAudit.report.json",
    "docs/master_plan/generated/PR168_RP5B_FinalSummary.report.json",
    "docs/master_plan/generated/PR168_RP5A_LegacyPRSemanticAudit.report.json",
    "docs/master_plan/generated/PR168_RP5A_LegacyFileSemanticAudit.report.json",
    "docs/master_plan/generated/PR168_RP5A_WrongConceptTermIndex.report.json",
    "docs/master_plan/generated/PR168_RP5A_ConsumerGraph.report.json",
    "docs/master_plan/generated/PR168_RP5A_ValidationDependencyGraph.report.json",
    "docs/master_plan/generated/PR168_RP5A_QKUFormulaIdentityDependency.report.json",
    "docs/master_plan/generated/PR168_RP5A_IdentityCustodyGraph.report.json",
    "docs/master_plan/generated/PR168_RP5A_DeleteEligibilityDraft.report.json",
    "docs/master_plan/generated/PR168_RP5A_NoDeletionProof.report.json",
    "docs/master_plan/generated/PR168_RP5A_ScanPerformance.report.json",
    "docs/master_plan/generated/PR168_RP5A_FutureRP5BPlan.report.json",
    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
)

UPSTREAM_IDENTITY_DIRS: Final = (
    "docs/master_plan/generated/map3",
    "docs/master_plan/generated/rp3",
    "docs/master_plan/generated/rank3",
    "docs/master_plan/generated/pr168_gfp2r_candidate_compute",
)

UPSTREAM_IDENTITY_KEYWORDS: Final = (
    "formula",
    "qku",
    "candidatepacket",
    "candidate_packet",
    "assignment",
    "ontology",
    "family",
    "plugin",
    "pnl",
    "identity",
    "lineage",
    "contract",
    "dependency",
)

CENTRAL_SURFACE_SHARDS: Final = (
    "immutable_qku_library",
    "immutable_formula_library",
    "immutable_qku_formula_library",
    "qku_formula_family_registry",
    "market_scope_family_registry",
    "ontology_role_registry",
    "formula_assignment_library",
    "qku_formula_identity_lineage",
    "source_artifact_consumption_ledger",
    "agent_responsibility_group_registry",
    "agent_duty_routing_rulebook",
    "derived_agent_route_resolution_ledger",
    "file_to_derived_route_crosswalk",
    "identity_deduplication_ledger",
    "formula_ontology",
    "identity_provenance_tier",
    "no_global_ban_rows",
    "no_orphan_identity_rows",
    "no_orphan_source_artifact_rows",
    "no_orphan_generated_surface_rows",
    "qku_market_applicability_matrix",
    "market_family_reclassification_ledger",
    "shared_cross_market_support_pool",
    "market_specific_qku_pool_registry",
    "market_stage_activation_profile_registry",
    "agent_qku_access_policy_registry",
    "stage_agent_qku_universe_resolver",
    "stage_computation_universe_view",
    "agent_computation_universe_view",
    "library_query_receipts",
    "vs1_trading_intelligence_handoff",
    "stage1_prediction_market_qku_activation_view",
    "platform_applicability_registry",
    "dormant_future_market_qku_ledger",
    "stage1_agent_computation_universe_seed",
    "rp5d_executability_handoff",
)

STAGE1_ACTIVE_UNIVERSE_SHARDS: Final = (
    "stage1_prediction_market_qku_activation_view",
    "platform_applicability_registry",
    "dormant_future_market_qku_ledger",
    "stage1_agent_computation_universe_seed",
)

FALLBACK_ROUTING_MATRIX: Final = {
    "signal_probability": ("research_signal_probability_group", ("ResearchAgent", "ParameterSelectorAgent"), ("ReplayPaperAgent", "TradePlanSimulationAgent", "Rank4Agent"), ("GovernanceAgent", "ReplayPaperValidator")),
    "calibration": ("calibration_group", ("ResearchAgent", "CalibrationAgent", "ReplayPaperAgent"), ("RP5DExecutabilityAgent", "TradePlanSimulationAgent"), ("GovernanceAgent",)),
    "market_implied_probability": ("market_data_implied_probability_group", ("MarketDataAgent", "ResearchAgent"), ("ReplayPaperAgent", "TradeTargetScoutAgent"), ("SourceEvidenceAgent", "GovernanceAgent")),
    "tca_cost": ("tca_cost_group", ("ExecutionRouterAgent", "TCAAgent"), ("ReplayPaperAgent", "RiskManagerAgent"), ("GovernanceAgent",)),
    "fill_queue_liquidity": ("fill_queue_liquidity_group", ("VenueSpecialistAgent", "ExecutionRouterAgent"), ("ReplayPaperAgent", "RiskManagerAgent"), ("FillIntegrityValidator", "GovernanceAgent")),
    "latency_staleness": ("latency_staleness_group", ("ExecutionRouterAgent", "LatencyMonitorAgent"), ("ReplayPaperAgent", "RiskManagerAgent"), ("GovernanceAgent",)),
    "capacity_crowding": ("capacity_crowding_group", ("RiskManagerAgent", "PortfolioRiskAgent"), ("TradePlanSimulationAgent", "Rank4Agent"), ("GovernanceAgent",)),
    "portfolio_risk": ("portfolio_risk_group", ("RiskManagerAgent", "PortfolioRiskAgent"), ("TradePlanSimulationAgent", "ExecutionRouterAgent"), ("GovernanceAgent",)),
    "regime_scenario": ("regime_scenario_group", ("ResearchAgent", "ScenarioStressAgent"), ("ReplayPaperAgent", "TradePlanSimulationAgent"), ("GovernanceAgent",)),
    "exit_timing": ("exit_timing_group", ("ExecutionRouterAgent", "ResearchAgent"), ("ReplayPaperAgent", "TradePlanSimulationAgent"), ("GovernanceAgent",)),
    "quantum_objective_constraint": ("quantum_objective_constraint_group", ("QuantumOptimizerAgent", "ResearchAgent"), ("QOPTAgent", "ReplayPaperAgent"), ("GovernanceAgent", "ClassicalComparatorAgent")),
    "classical_fallback": ("classical_fallback_group", ("ClassicalOptimizerAgent", "ParameterSelectorAgent"), ("ReplayPaperAgent", "QOPTAgent"), ("GovernanceAgent",)),
    "governance_source_risk": ("governance_source_risk_group", ("GovernanceAgent", "SourceEvidenceAgent"), ("RP5DExecutabilityAgent", "RiskManagerAgent"), ("GovernanceAgent",)),
    "unknown_needs_review": ("unknown_review_group", ("GovernanceAgent", "ResearchAgent"), ("RP5DExecutabilityAgent",), ("GovernanceAgent",)),
}


def normalize_repo_path(path: str | Path) -> str:
    text = str(path).replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def generated_ref(path: str | Path) -> str:
    path_obj = Path(path)
    try:
        return normalize_repo_path(path_obj.relative_to(REPO_ROOT))
    except ValueError:
        return normalize_repo_path(path_obj)


def report_path(name: str) -> Path:
    return GENERATED_ROOT / name


def shard_path(key: str) -> Path:
    return SHARD_ROOT / ROW_SHARDS[key]


def manifest_path_for_shard(path: Path) -> Path:
    return path.with_name(path.stem + ".manifest.json")


def classify_file_kind(path: str | Path) -> str:
    normalized = normalize_repo_path(path)
    name = Path(normalized).name
    if normalized.startswith("docs/master_plan/generated/"):
        if name.endswith(".manifest.json"):
            return "MANIFEST"
        if name.endswith(".jsonl"):
            return "GENERATED_SHARD_JSONL"
        if ".shard_" in name or ".part_" in name:
            return "GENERATED_SHARDED_REPORT"
        if name.endswith(".report.json") or name.endswith(".json"):
            return "GENERATED_REPORT"
    if normalized.startswith("tools/"):
        return "VALIDATOR_OR_TOOL_SOURCE" if name.startswith("validate_") else "TOOL_SOURCE"
    if normalized.startswith("tests/"):
        return "TEST_SOURCE"
    if normalized.startswith("docs/"):
        return "DOC"
    return "UNKNOWN"
