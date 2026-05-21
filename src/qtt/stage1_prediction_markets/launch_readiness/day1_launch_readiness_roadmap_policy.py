"""Central PR136 Day-1 launch-readiness roadmap policy constants."""

from __future__ import annotations

from typing import Any


VALIDATOR_MARKER = "QTT_PR136_DAY1_LAUNCH_READINESS_ROADMAP_OK"

PRODUCER_REPO_PR = 136
PREVIOUS_REPO_PR = 135
PREVIOUS_ROADMAP_PR = 117
OWNER_AUTHORIZED_SCOPE = (
    "PR136_MASTER_PLAN_COVERAGE_TO_DAY1_LAUNCH_READINESS_ROADMAP_CURRENTIZATION"
)
SEQUENCE_AUTHORITY = (
    "CANONICAL_POST_PR135_PLANNING_AUTHORITY_NOT_EXECUTION_AUTHORITY"
)

POLICY_MODULE_PATH = (
    "src/qtt/stage1_prediction_markets/launch_readiness/"
    "day1_launch_readiness_roadmap_policy.py"
)
ROADMAP_MODULE_PATH = (
    "src/qtt/stage1_prediction_markets/launch_readiness/"
    "day1_launch_readiness_roadmap.py"
)
POLICY_SCHEMA_DEFS_PATH = (
    "schemas/roadmap/pr136_day1_launch_readiness_policy.defs.schema.json"
)
POLICY_MANIFEST_PATH = "docs/master_plan/generated/PR136PolicyManifest.report.json"
POLICY_LITERAL_DRIFT_REPORT_PATH = (
    "docs/master_plan/generated/PR136PolicyLiteralDrift.report.json"
)

SEQUENCE_AUTHORITY_CLASSES = (
    "CANONICAL_POST_PR135_PLANNING_AUTHORITY_NOT_EXECUTION_AUTHORITY",
    "OWNER_AUTHORIZATION_REQUIRED_BEFORE_IMPLEMENTATION",
    "OWNER_AUTHORIZATION_REQUIRED_BEFORE_MATERIALIZATION",
    "OWNER_AUTHORIZATION_REQUIRED_BEFORE_LIVE_EXECUTION",
)

CLASSIFICATION_LABELS = (
    "CONFIRMED",
    "SPLIT_OR_REPLACED",
    "MERGED_WITH_OTHER_PR",
    "NEW_INSERTION_REQUIRED_BEFORE_THIS_PR",
    "DEFERRED_AFTER_DAY1",
    "OWNER_AUTHORIZATION_REQUIRED",
)
CONFIRMED = CLASSIFICATION_LABELS[0]
SPLIT_OR_REPLACED = CLASSIFICATION_LABELS[1]
MERGED_WITH_OTHER_PR = CLASSIFICATION_LABELS[2]
NEW_INSERTION_REQUIRED_BEFORE_THIS_PR = CLASSIFICATION_LABELS[3]
DEFERRED_AFTER_DAY1 = CLASSIFICATION_LABELS[4]
OWNER_AUTHORIZATION_REQUIRED = CLASSIFICATION_LABELS[5]

EVIDENCE_CLASSES = (
    "DIRECT_MASTER_PLAN",
    "ROADMAP",
    "BLUEPRINT",
    "GENERATED_REPORT",
    "OWNER_VERIFIED_INPUT",
    "REPO_CONVENTION",
    "CODEX_INFERENCE_REQUIRES_OWNER_REVIEW",
)

READINESS_STATE_CLASSES = (
    "STATIC_CONTRACT_READY",
    "SOURCE_EVIDENCE_READY",
    "CONNECTOR_BINDING_READY",
    "CREDENTIAL_PRIVATE_STATE_CASH_READY",
    "NONLIVE_REPLAY_PAPER_READY",
    "QUANTUM_OPTIMIZER_READY_OWNER_BLOCKED",
    "ATOMICROWS_BRIDGE_READY_OWNER_BLOCKED",
    "OWNER_REVIEW_READY",
    "CANARY_READY_OWNER_COMMAND_REQUIRED",
    "DAY1_LAUNCH_READY_OWNER_COMMAND_REQUIRED",
    "OFFICIAL_DAY1_LIVE_TRADING_STARTED_OWNER_AUTHORIZED_ONLY",
)

READINESS_DOMAIN_TAXONOMY_RULES = (
    "READINESS_DOMAIN_TAXONOMY_MUST_BE_COVERAGE_DERIVED",
    "ARBITRARY_DOMAIN_COUNT_FORCED_FORBIDDEN",
    "FIXED_13_DOMAIN_MODEL_FORBIDDEN",
    "DOMAIN_COUNT_MUST_BE_COMPUTED_FROM_EVIDENCE",
    "EVERY_DOMAIN_REQUIRES_EVIDENCE_BASIS",
    "PARENT_DOMAIN_AND_SUBDOMAIN_HIERARCHY_ALLOWED",
    "UNMAPPED_COVERAGE_ENTRY_BLOCKS_VALIDATION_UNLESS_EXPLICITLY_DEFERRED_WITH_EVIDENCE",
)

CANONICAL_VENUES = (
    "PREDICTION_MARKETS_GENERAL",
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
)
VENUE_SPECIFIC_IDS = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
FORBIDDEN_FORECASTEX_ALIASES = (
    "FORECASTEX",
    "FORECASTX",
    "IBKR_FORECASTX",
    "forecastx",
)

FUTURE_PR_SCOPE_CLASSES = (
    "ROADMAP_MAPPING",
    "ATOMICROWS_READINESS",
    "SOURCE_EVIDENCE_READINESS",
    "CONNECTOR_BINDING_READINESS",
    "CREDENTIAL_PRIVATE_STATE_CASH_READINESS",
    "DATASET_REPLAY_PAPER_READINESS",
    "QUANTUM_OPTIMIZER_READINESS",
    "PARAMETER_STACK_SELECTION_READINESS",
    "OWNER_APPROVAL_DASHBOARD_READINESS",
    "CANARY_LIVE_COMPARISON_READINESS",
    "DAY1_LAUNCH_READINESS",
    "OWNER_AUTHORIZED_EXECUTION_ONLY",
)

FUTURE_PR_NUMBER_STATUS = (
    "FIXED_IF_OWNER_APPROVES",
    "PLACEHOLDER",
    "INSERTION_BEFORE",
    "SPLIT_CHILD",
    "MERGED_CHILD",
    "DEFERRED_AFTER_DAY1",
    "OWNER_AUTHORIZATION_BLOCKED",
)

DOMAIN_TYPES = (
    "PARENT_DOMAIN",
    "SUBDOMAIN",
    "MARKET_SPECIFIC_DOMAIN",
    "OWNER_AUTHORIZATION_DOMAIN",
    "LATENCY_HOT_PATH_DOMAIN",
    "AGENT_ORCHESTRATION_DOMAIN",
)

NO_AUTHORITY_FLAGS = {
    "creates_live_data": False,
    "creates_source_retrieval": False,
    "creates_source_acceptance": False,
    "creates_connector_binding": False,
    "creates_credential_resolution": False,
    "creates_private_state_fetch": False,
    "creates_runtime_cash_authority": False,
    "creates_replay_execution": False,
    "creates_paper_execution": False,
    "creates_replay_result": False,
    "creates_paper_result": False,
    "creates_trading_signal": False,
    "creates_ranking_scoring_arbitration_output": False,
    "creates_order_authority": False,
    "creates_order_execution": False,
    "creates_fill_receipt": False,
    "creates_profit_evidence": False,
    "creates_latency_superiority_evidence": False,
    "creates_execution_superiority_evidence": False,
    "creates_alpha_evidence": False,
    "creates_quantum_execution": False,
    "creates_quantum_optimizer_input": False,
    "creates_quantum_advantage_claim": False,
    "creates_atomicrows_bundle": False,
    "creates_atomicrows_sha": False,
    "creates_atomicrows_rows": False,
    "creates_day1_live_launch": False,
}

BLOCK_CODE_REFS = (
    "BLOCKED_SAME_NUMBER_ROADMAP_INFERENCE",
    "BLOCKED_MISSING_PR135_CURRENTIZATION",
    "BLOCKED_MASTER_PLAN_EDIT_ATTEMPT",
    "BLOCKED_ATOMICROWS_BUNDLE_SHA_ROW_MATERIALIZATION_ATTEMPT",
    "BLOCKED_SOURCE_RETRIEVAL_OR_ACCEPTANCE_ATTEMPT",
    "BLOCKED_CONNECTOR_BINDING_ATTEMPT",
    "BLOCKED_CREDENTIAL_PRIVATE_STATE_CASH_AUTHORITY_ATTEMPT",
    "BLOCKED_LIVE_DATA_OR_RUNTIME_AUTHORITY_ATTEMPT",
    "BLOCKED_REPLAY_PAPER_EXECUTION_ATTEMPT",
    "BLOCKED_TRADING_SIGNAL_ORDER_PROFIT_ATTEMPT",
    "BLOCKED_QUANTUM_EXECUTION_OR_ADVANTAGE_CLAIM_ATTEMPT",
    "BLOCKED_DAY1_LAUNCH_EXECUTION_ATTEMPT",
    "BLOCKED_SCATTERED_POLICY_LITERAL_DRIFT",
    "BLOCKED_UNMAPPED_MASTER_PLAN_COVERAGE_ENTRY",
    "BLOCKED_PROVISIONAL_PR_WITHOUT_CLASSIFICATION",
    "BLOCKED_DUPLICATE_FUTURE_PR_NUMBER",
    "BLOCKED_CYCLIC_DEPENDENCY_GRAPH",
    "BLOCKED_MISSING_MARKET_SPECIFIC_READINESS_ROUTE",
    "BLOCKED_OWNER_AUTHORIZATION_REQUIRED_BUT_NOT_MARKED",
    "BLOCKED_EVIDENCELESS_CLASSIFICATION",
    "BLOCKED_LIVE_HOT_PATH_CONTROL_PLANE_CALL",
    "BLOCKED_AGENT_AUTHORITY_ESCALATION",
    "BLOCKED_ARBITRARY_DOMAIN_COUNT_FORCED",
    "BLOCKED_FIXED_13_DOMAIN_MODEL_USED",
)

REQUIRED_READ_FILES = (
    "docs/roadmap/README.md",
    "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md",
    "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json",
    "docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md",
    "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/master_plan/QTT_MasterPlan_Current.md",
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
)

OPTIONAL_CURRENT_STATE_FILES = (
    "docs/master_plan/generated/MasterPlanSectionCoverageReport.json",
    "docs/master_plan/generated/QttPrIdentityRoster.report.json",
    "docs/master_plan/generated/QttRoadmapExecutionStateController.report.json",
    "docs/master_plan/generated/PR135HistoricalDatasetDigestAndLoader.report.json",
    "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR135MarketSpecificSectionIndex.report.json",
    "docs/master_plan/generated/PR135CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR135HistoricalDatasetPolicyManifest.report.json",
    "docs/master_plan/generated/PR135RouteTriage.report.json",
    "docs/master_plan/generated/PR134GitHubAuditCurrentization.report.json",
    "docs/roadmap/generated/CODEX_PR135_ROUTE_TRIAGE_RECEIPT.json",
    "docs/roadmap/generated/CODEX_PR135_MANDATORY_READ_RECEIPT.json",
)

ANCHORS_INSPECTED = (
    "Stage 1 prediction markets",
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
    "PREDICTION_MARKETS_GENERAL",
    "Day-1 launch",
    "runtime live-order command",
    "limited live canary",
    "three-venue canary eligibility",
    "owner live-promotion review",
    "concurrent replay/paper",
    "dual-result review",
    "historical dataset digest and loader",
    "runtime resolver snapshot",
    "versioned candidate-set snapshot-lock",
    "source evidence",
    "connector semantic binding",
    "credential readiness",
    "private-state receipts",
    "runtime cash",
    "AtomicRows",
    "bundle",
    "SHA/freeze",
    "quantum",
    "QAOA",
    "QUBO",
    "VQE",
    "annealing",
    "quantum kernel",
    "amplitude encoding",
    "optimizer arbitration",
    "parameter-stack selection",
    "owner dashboard",
    "launch rollback",
    "latency hot path",
    "no runtime/no live/no profit boundary",
)

MISSING_ACCEPTED_SOURCE_EVIDENCE_CLASSES = (
    "venue_api_semantics",
    "order_fields",
    "fee_rules",
    "tick_rules",
    "payout_rules",
    "settlement_rules",
    "market_data_semantics",
    "historical_data_availability",
    "account_balance_semantics",
    "private_state_cash_semantics",
    "execution_lifecycle_semantics",
    "fill_integrity_semantics",
    "cashflow_pnl_semantics",
    "latency_component_semantics",
    "settlement_finality_semantics",
    "reconciliation_semantics",
    "cross_venue_normalization_semantics",
)

AGENT_DOMAIN_IDS = (
    "research_source_agent",
    "source_evidence_agent",
    "connector_semantic_agent",
    "credential_private_state_cash_agent",
    "market_data_agent",
    "runtime_resolver_agent",
    "historical_dataset_agent",
    "atomicrows_agent",
    "quantum_optimizer_agent",
    "classical_optimizer_agent",
    "parameter_stack_agent",
    "replay_agent",
    "paper_agent",
    "risk_agent",
    "owner_approval_agent",
    "dashboard_agent",
    "canary_execution_agent",
    "post_trade_reconciliation_agent",
    "launch_runbook_agent",
)

PR136_REPORT_PATHS = (
    "docs/master_plan/generated/PR136OwnerVerifiedInputs.report.json",
    "docs/master_plan/generated/PR135GitHubAuditCurrentization.report.json",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136ReadReceipt.report.json",
    "docs/master_plan/generated/PR136PathDecision.report.json",
    "docs/master_plan/generated/PR136PolicyManifest.report.json",
    "docs/master_plan/generated/PR136MasterPlanCoverageToReadinessDomainMap.report.json",
    "docs/master_plan/generated/PR136ReadinessDomainTaxonomy.report.json",
    "docs/master_plan/generated/PR136Day1LaunchReadinessRoadmap.report.json",
    "docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json",
    "docs/master_plan/generated/PR136LaunchReadinessDependencyGraph.report.json",
    "docs/master_plan/generated/PR136RoadmapReplacementAndInsertionMatrix.report.json",
    "docs/master_plan/generated/PR136ProvisionalPR137ToPR164Classification.report.json",
    "docs/master_plan/generated/PR136FuturePRCardRegistry.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136QuantumAtomicRowsOptimizationReadinessMap.report.json",
    "docs/master_plan/generated/PR136AgentLaunchOrchestrationMap.report.json",
    "docs/master_plan/generated/PR136LatencyControlPlaneVsLivePathMap.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR136ValidationGateIntegration.report.json",
    "docs/master_plan/generated/PR136PolicyLiteralDrift.report.json",
)

PR136_ROADMAP_RECEIPT_PATHS = (
    "docs/roadmap/generated/CODEX_REPO_PR135_GITHUB_AUDIT_CURRENTIZATION_RECEIPT.json",
    "docs/roadmap/generated/CODEX_PR136_MANDATORY_READ_RECEIPT.json",
    "docs/roadmap/generated/CODEX_PR136_ROUTE_TRIAGE_RECEIPT.json",
)

PR136_SCHEMA_PATHS = (
    "schemas/roadmap/pr136_day1_launch_readiness_policy.defs.schema.json",
    "schemas/roadmap/pr136_day1_launch_readiness_roadmap.schema.json",
    "schemas/roadmap/pr136_readiness_domain_taxonomy.schema.json",
    "schemas/roadmap/pr136_post_pr135_sequence.schema.json",
    "schemas/roadmap/pr136_launch_readiness_dependency_graph.schema.json",
    "schemas/roadmap/pr136_roadmap_replacement_insertion_matrix.schema.json",
    "schemas/roadmap/pr136_market_specific_launch_readiness_index.schema.json",
    "schemas/roadmap/pr136_quantum_atomicrows_optimization_readiness_map.schema.json",
    "schemas/roadmap/pr136_agent_launch_orchestration_map.schema.json",
    "schemas/roadmap/pr136_latency_control_plane_vs_live_path_map.schema.json",
    "schemas/roadmap/pr136_future_pr_card.schema.json",
    "schemas/roadmap/pr136_receipt.schema.json",
)


def no_authority_flags() -> dict[str, bool]:
    return dict(NO_AUTHORITY_FLAGS)


def policy_manifest_payload() -> dict[str, Any]:
    return {
        "receipt_type": "PR136_POLICY_MANIFEST",
        "repo_pr_number": PRODUCER_REPO_PR,
        "owner_authorized_scope": OWNER_AUTHORIZED_SCOPE,
        "policy_module_path": POLICY_MODULE_PATH,
        "roadmap_module_path": ROADMAP_MODULE_PATH,
        "policy_schema_defs_path": POLICY_SCHEMA_DEFS_PATH,
        "policy_manifest_path": POLICY_MANIFEST_PATH,
        "validator_marker": VALIDATOR_MARKER,
        "sequence_authority_classes": list(SEQUENCE_AUTHORITY_CLASSES),
        "classification_labels": list(CLASSIFICATION_LABELS),
        "evidence_classes": list(EVIDENCE_CLASSES),
        "readiness_state_classes": list(READINESS_STATE_CLASSES),
        "readiness_domain_taxonomy_rules": list(READINESS_DOMAIN_TAXONOMY_RULES),
        "canonical_venues": list(CANONICAL_VENUES),
        "future_pr_scope_classes": list(FUTURE_PR_SCOPE_CLASSES),
        "future_pr_number_status": list(FUTURE_PR_NUMBER_STATUS),
        "domain_types": list(DOMAIN_TYPES),
        "no_authority_flags": no_authority_flags(),
        "block_code_refs": list(BLOCK_CODE_REFS),
        "definition_locations_approved": [
            POLICY_MODULE_PATH,
            POLICY_SCHEMA_DEFS_PATH,
            POLICY_MANIFEST_PATH,
        ],
        "policy_literal_drift_validator_path": (
            "tools/validate_pr136_roadmap_policy_literal_drift.py"
        ),
        "centralized_classification_labels": True,
        "centralized_block_code_doctrine": True,
        "centralized_readiness_states": True,
        "centralized_evidence_classes": True,
        "centralized_no_authority_flags": True,
        "centralized_domain_derivation_rules": True,
        "arbitrary_domain_count_forced": False,
        "fixed_13_domain_model_used": False,
        "codex_network_access_used": False,
        "gh_command_used_by_codex": False,
    }
