"""Central PR159S vocabulary, paths, counts, and authority boundaries."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any


PR_ID = "PR159S"
SEMANTIC_TASK_ID = (
    "PR159S_OPEN_SOURCE_INTELLIGENCE_OFFICIAL_RESEARCH_REPLAY_PAPER_CANDIDATE_"
    "SOURCE_PROFIT_PROVENANCE_ATOMICROWS_COMPLETION"
)
IMPLEMENTATION_CLASS = (
    "DETERMINISTIC_CONTROL_PLANE_OPEN_INTAKE_SOURCE_PROFIT_PROVENANCE_AND_"
    "REPLAY_PAPER_CANDIDATE_ROUTE_COMPLETION_ONLY"
)
AUTHORITY_CLASS = (
    "OPEN_RESEARCH_AND_OFFICIAL_FACT_CLASSIFICATION_ONLY_NOT_RUNTIME_NOT_LIVE_"
    "NOT_CONNECTOR_BINDING_NOT_PRIVATE_STATE_NOT_REPLAY_NOT_PAPER_NOT_SCORING_"
    "EXECUTION_NOT_RANKING_EXECUTION_NOT_SELECTION_EXECUTION_NOT_OPTIMIZER_"
    "EXECUTION_NOT_QUANTUM_BACKEND_NOT_ORDER_FILL_PROFIT_NOT_QTT_CHECKSUM_"
    "FREEZE_GLOBAL_DIGEST_NOT_ATOMICROWS_BUNDLE_CHECKSUM_HASH_AUTHORITY"
)

EXPECTED_BRANCH = "pr159s-open-source-intelligence-candidate-completion"
BRANCH_CONTEXT_RELAXATION_REPAIR_BRANCH = "repair/pr159s-open-intake-branch-context-relaxation"
SUCCESS_MARKER = "QTT_PR159S_OPEN_INTAKE_COMPLETION_OK"
VALIDATION_MARKER = "QTT_VALIDATION_GATES_OK"
PR159S_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY = (
    "PR159S_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY"
)
PR159S_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY = (
    "PR159S_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY"
)
RETRIEVAL_TIMESTAMP_UTC = "2026-05-29T00:00:00Z"

EXPECTED_INPUT_TOTAL = 868
EXPECTED_ATOMICROWS_INPUT = 845
EXPECTED_PR154_INPUT = 23
EXPECTED_PR154_UNIVERSE = 342
EXPECTED_ATOMICROWS_UNIVERSE = 4183
EXPECTED_PR159_ACCEPTED_PACKETS = 10
EXPECTED_PR159R_ACCEPTED_PACKETS = 1
EXPECTED_PRIOR_ACCEPTED_OFFICIAL_TOTAL = 11
EXPECTED_PR159R_UNRESOLVED_AFTER_REPAIR = 868

GENERATED_DIR = Path("docs/master_plan/generated")
MASTER_PLAN_PATH = Path("docs/master_plan/QTT_MasterPlan_Current.md")
SOURCE_EVIDENCE_PACKET_PATH = Path(
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
)

PR159R_UNRESOLVED_FILL_PATH = GENERATED_DIR / "PR159R_UnresolvedExactSourceFillPath.report.json"
PR159R_TARGET_RECONCILIATION_REGISTRY = (
    GENERATED_DIR / "PR159R_UnresolvedSourceTargetReconciliation.registry.json"
)
PR159R_ACCEPTED_PACKET_REGISTRY = (
    GENERATED_DIR / "PR159R_AcceptedSourceEvidencePacketRegistry.registry.json"
)
PR159R_TARGET_FIELD_LEDGER_REGISTRY = (
    GENERATED_DIR / "PR159R_TargetFieldAcceptanceLedger.registry.json"
)
PR159_ACCEPTED_PACKET_REGISTRY = (
    GENERATED_DIR / "PR159_AcceptedSourceEvidencePacketRegistry.registry.json"
)
PR159_TARGET_FIELD_LEDGER_REGISTRY = GENERATED_DIR / "PR159_TargetFieldAcceptanceLedger.registry.json"
PR160_REQUEUE_REPORT = GENERATED_DIR / "PR160_PR159RSourceTargetRequeue.report.json"
PR160_ROUTE_CLOSURE_REPORT = GENERATED_DIR / "PR160_PR154SplitReclassificationRouteClosure.report.json"
PR157_ATOMICROWS_REGISTRY = GENERATED_DIR / "PR157_AtomicRows4183CompletionMaterialization.registry.json"
PR157_PR154_REGISTRY = GENERATED_DIR / "PR157_PR154BlockedRecordCompletionBridge.registry.json"
PR152_AUDIT_REPORT = GENERATED_DIR / "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"

ORCHESTRATION_PREFLIGHT_PATH = (
    GENERATED_DIR / "PR159S_OpenIntakeOrchestrationPreflight.report.json"
)
INPUT_TARGET_INVENTORY_PATH = GENERATED_DIR / "PR159S_InputTargetInventory.report.json"
SOURCE_TAXONOMY_PATH = GENERATED_DIR / "PR159S_SourceTaxonomy.report.json"
OPEN_RESEARCH_SOURCE_INTAKE_PATH = GENERATED_DIR / "PR159S_OpenResearchSourceIntake.report.json"
OFFICIAL_EXTERNAL_FACT_DELTA_PATH = GENERATED_DIR / "PR159S_OfficialExternalFactDelta.report.json"
ALGORITHM_FORMULA_CANDIDATE_DELTA_PATH = (
    GENERATED_DIR / "PR159S_AlgorithmFormulaCandidateDelta.report.json"
)
ATOMICROWS_CANDIDATE_READINESS_DELTA_PATH = (
    GENERATED_DIR / "PR159S_AtomicRowsCandidateReadinessDelta.report.json"
)
REPLAY_PAPER_CANDIDATE_ROUTE_PATH = GENERATED_DIR / "PR159S_ReplayPaperCandidateRoute.report.json"
QUANTUM_CANDIDATE_READINESS_DELTA_PATH = (
    GENERATED_DIR / "PR159S_QuantumCandidateReadinessDelta.report.json"
)
SOURCE_PROFIT_PROVENANCE_CLASSIFICATION_PATH = (
    GENERATED_DIR / "PR159S_SourceProfitProvenanceClassification.report.json"
)
OFFICIAL_CONFIRMED_BACKFILL_PATH = GENERATED_DIR / "PR159S_OfficialConfirmedBackfill.report.json"
PROFIT_VALIDATION_STATE_REGISTRY_PATH = (
    GENERATED_DIR / "PR159S_ProfitValidationStateRegistry.report.json"
)
ATOMICROWS_SOURCE_PROFIT_READINESS_DELTA_PATH = (
    GENERATED_DIR / "PR159S_AtomicRowsSourceProfitReadinessDelta.report.json"
)
TERMINAL_COMPLETION_SUMMARY_PATH = GENERATED_DIR / "PR159S_TerminalCompletionSummary.report.json"
BRANCH_CONTEXT_AND_DETERMINISTIC_AUDIT_PATH = (
    GENERATED_DIR / "PR159S_BranchContextAndDeterministicAudit.report.json"
)

ALL_JSON_ARTIFACT_PATHS = (
    ORCHESTRATION_PREFLIGHT_PATH,
    INPUT_TARGET_INVENTORY_PATH,
    SOURCE_TAXONOMY_PATH,
    OPEN_RESEARCH_SOURCE_INTAKE_PATH,
    OFFICIAL_EXTERNAL_FACT_DELTA_PATH,
    ALGORITHM_FORMULA_CANDIDATE_DELTA_PATH,
    ATOMICROWS_CANDIDATE_READINESS_DELTA_PATH,
    REPLAY_PAPER_CANDIDATE_ROUTE_PATH,
    QUANTUM_CANDIDATE_READINESS_DELTA_PATH,
    SOURCE_PROFIT_PROVENANCE_CLASSIFICATION_PATH,
    OFFICIAL_CONFIRMED_BACKFILL_PATH,
    PROFIT_VALIDATION_STATE_REGISTRY_PATH,
    ATOMICROWS_SOURCE_PROFIT_READINESS_DELTA_PATH,
    TERMINAL_COMPLETION_SUMMARY_PATH,
    BRANCH_CONTEXT_AND_DETERMINISTIC_AUDIT_PATH,
)

SCHEMA_DIR = Path("src/qtt/stage1_prediction_markets/source_intelligence/schemas")
SCHEMA_PATHS = (
    SCHEMA_DIR / "pr159s_source_taxonomy.schema.json",
    SCHEMA_DIR / "pr159s_open_research_source_intake.schema.json",
    SCHEMA_DIR / "pr159s_algorithm_formula_candidate.schema.json",
    SCHEMA_DIR / "pr159s_replay_paper_candidate_route.schema.json",
    SCHEMA_DIR / "pr159s_quantum_candidate_readiness.schema.json",
    SCHEMA_DIR / "pr159s_source_profit_provenance.schema.json",
    SCHEMA_DIR / "pr159s_official_confirmed_backfill.schema.json",
    SCHEMA_DIR / "pr159s_profit_validation_state.schema.json",
    SCHEMA_DIR / "pr159s_atomicrows_source_profit_readiness.schema.json",
    SCHEMA_DIR / "pr159s_terminal_completion_summary.schema.json",
)

MANDATORY_ORCHESTRATION_INPUTS = (
    Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json"),
    Path("docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"),
    Path("docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md"),
    Path("src/qtt/stage1_prediction_markets/launch_readiness/day1_launch_readiness_roadmap_policy.py"),
    Path("docs/master_plan/generated/PR136RouteTriage.report.json"),
    Path("docs/master_plan/generated/PR136MasterPlanSectionCrosswalk.report.json"),
    Path("docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json"),
    Path("docs/master_plan/generated/PR136CommandActionMatrix.report.json"),
    Path("docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"),
    Path("docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"),
)
CROSSWALK_FALLBACK_PATH = GENERATED_DIR / "PR136MasterPlanCoverageToReadinessDomainMap.report.json"

MANDATORY_CONTEXT_INPUTS = (
    MASTER_PLAN_PATH,
    SOURCE_EVIDENCE_PACKET_PATH,
    PR159R_UNRESOLVED_FILL_PATH,
    PR159R_TARGET_RECONCILIATION_REGISTRY,
    PR159_ACCEPTED_PACKET_REGISTRY,
    PR159_TARGET_FIELD_LEDGER_REGISTRY,
    PR159R_ACCEPTED_PACKET_REGISTRY,
    PR159R_TARGET_FIELD_LEDGER_REGISTRY,
    PR160_REQUEUE_REPORT,
    PR160_ROUTE_CLOSURE_REPORT,
    PR157_ATOMICROWS_REGISTRY,
    PR157_PR154_REGISTRY,
    PR152_AUDIT_REPORT,
    Path("docs/master_plan/generated/PR157_AtomicRows4183CompletionMaterialization.report.json"),
    Path("docs/master_plan/generated/PR158_MasterPlanOwnerResponseSelectionReadinessBridge.report.json"),
    Path("docs/master_plan/generated/PR159R_QuantumApplicabilityReconciliationWithPR82_PR86.report.json"),
    Path("docs/master_plan/generated/PR159R_QuantumForwardOptimizerReadinessBridge.report.json"),
    Path("docs/master_plan/generated/PR159R_QuantumReplayPaperComparisonReadiness.report.json"),
    Path("tools/ci_branch_context.py"),
)

PR157_SHARD_DIR = GENERATED_DIR / "pr157_atomicrows_completion_shards"


class OfficialSourceClass(StrEnum):
    OFFICIAL_VENUE_DOCS = "OFFICIAL_VENUE_DOCS"
    OFFICIAL_API_DOCS = "OFFICIAL_API_DOCS"
    OFFICIAL_SDK_DOCS = "OFFICIAL_SDK_DOCS"
    OFFICIAL_RULEBOOKS = "OFFICIAL_RULEBOOKS"
    OFFICIAL_FEE_TICK_SETTLEMENT_DOCS = "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS"
    OFFICIAL_PROVIDER_DOCS = "OFFICIAL_PROVIDER_DOCS"
    OFFICIAL_REGULATORY_FILINGS = "OFFICIAL_REGULATORY_FILINGS"
    OFFICIAL_STATUS_OR_CHANGELOG_DOCS = "OFFICIAL_STATUS_OR_CHANGELOG_DOCS"


class OpenResearchSourceClass(StrEnum):
    SOCIAL_POST = "SOCIAL_POST"
    X_POST = "X_POST"
    FORUM_THREAD = "FORUM_THREAD"
    BLOG_POST = "BLOG_POST"
    NEWS_ARTICLE = "NEWS_ARTICLE"
    NEWSLETTER = "NEWSLETTER"
    ACADEMIC_PAPER = "ACADEMIC_PAPER"
    PREPRINT = "PREPRINT"
    GITHUB_REPOSITORY = "GITHUB_REPOSITORY"
    CODE_SNIPPET_REFERENCE = "CODE_SNIPPET_REFERENCE"
    RESEARCH_NOTE = "RESEARCH_NOTE"
    THIRD_PARTY_ANALYSIS = "THIRD_PARTY_ANALYSIS"
    TRADING_ARTICLE = "TRADING_ARTICLE"
    MICROSTRUCTURE_WRITEUP = "MICROSTRUCTURE_WRITEUP"
    STRATEGY_WRITEUP = "STRATEGY_WRITEUP"
    OWNER_SUBMITTED_LINK = "OWNER_SUBMITTED_LINK"
    OWNER_SUBMITTED_TEXT = "OWNER_SUBMITTED_TEXT"
    PRIVATE_DOC_WITH_OWNER_ATTESTATION = "PRIVATE_DOC_WITH_OWNER_ATTESTATION"
    OTHER_EXTERNAL_RESEARCH_INPUT = "OTHER_EXTERNAL_RESEARCH_INPUT"


class ProhibitedExecutableTrustInput(StrEnum):
    UNKNOWN_PACKAGE_INSTALL_SCRIPTS = "UNKNOWN_PACKAGE_INSTALL_SCRIPTS"
    EXTERNAL_REPO_CODE_EXECUTION = "EXTERNAL_REPO_CODE_EXECUTION"
    SECRET_HANDLING_EXAMPLES = "SECRET_HANDLING_EXAMPLES"
    CREDENTIAL_EXAMPLES = "CREDENTIAL_EXAMPLES"
    PRIVATE_ACCOUNT_SCREENSHOTS_WITHOUT_OWNER_ATTESTATION = (
        "PRIVATE_ACCOUNT_SCREENSHOTS_WITHOUT_OWNER_ATTESTATION"
    )
    MALWARE_OR_SUSPICIOUS_CODE = "MALWARE_OR_SUSPICIOUS_CODE"


class AuthorityClass(StrEnum):
    ACCEPTED_OFFICIAL_EXTERNAL_FACT = "ACCEPTED_OFFICIAL_EXTERNAL_FACT"
    ACCEPTED_OPEN_RESEARCH_INPUT = "ACCEPTED_OPEN_RESEARCH_INPUT"
    ACCEPTED_ALGORITHM_CANDIDATE = "ACCEPTED_ALGORITHM_CANDIDATE"
    ACCEPTED_FORMULA_CANDIDATE = "ACCEPTED_FORMULA_CANDIDATE"
    ACCEPTED_PARAMETER_CANDIDATE = "ACCEPTED_PARAMETER_CANDIDATE"
    ACCEPTED_EDGE_HYPOTHESIS_CANDIDATE = "ACCEPTED_EDGE_HYPOTHESIS_CANDIDATE"
    ACCEPTED_MICROSTRUCTURE_CANDIDATE = "ACCEPTED_MICROSTRUCTURE_CANDIDATE"
    ACCEPTED_QUANTUM_CANDIDATE = "ACCEPTED_QUANTUM_CANDIDATE"
    ACCEPTED_CLASSICAL_CANDIDATE = "ACCEPTED_CLASSICAL_CANDIDATE"
    ACCEPTED_HYBRID_CANDIDATE = "ACCEPTED_HYBRID_CANDIDATE"
    ACCEPTED_REPLAY_PAPER_TEST_CANDIDATE = "ACCEPTED_REPLAY_PAPER_TEST_CANDIDATE"
    ACCEPTED_OWNER_POLICY_INPUT = "ACCEPTED_OWNER_POLICY_INPUT"
    QUARANTINED_SECURITY_RISK_INPUT = "QUARANTINED_SECURITY_RISK_INPUT"
    REJECTED_DUPLICATE_OR_IRRELEVANT_INPUT = "REJECTED_DUPLICATE_OR_IRRELEVANT_INPUT"


class SourceProvenanceTag(StrEnum):
    OFFICIAL_CONFIRMED = "OFFICIAL_CONFIRMED"
    OFFICIAL_CONFIRMED_REUSED_FROM_PREVIOUS_PR = "OFFICIAL_CONFIRMED_REUSED_FROM_PREVIOUS_PR"
    OFFICIAL_CANDIDATE_PENDING_EXACT_FIELD = "OFFICIAL_CANDIDATE_PENDING_EXACT_FIELD"
    OPEN_RESEARCH_INPUT_UNTESTED = "OPEN_RESEARCH_INPUT_UNTESTED"
    OPEN_RESEARCH_INPUT_TESTABLE = "OPEN_RESEARCH_INPUT_TESTABLE"
    OWNER_SUPPLIED_INTERNAL_POLICY = "OWNER_SUPPLIED_INTERNAL_POLICY"
    OWNER_SUPPLIED_RESEARCH_INPUT = "OWNER_SUPPLIED_RESEARCH_INPUT"
    PRIVATE_DOC_ATTESTED_INPUT = "PRIVATE_DOC_ATTESTED_INPUT"
    MIXED_OFFICIAL_AND_RESEARCH = "MIXED_OFFICIAL_AND_RESEARCH"
    NON_OFFICIAL_RESEARCH_CANDIDATE = "NON_OFFICIAL_RESEARCH_CANDIDATE"
    NON_OFFICIAL_ALGORITHM_CANDIDATE = "NON_OFFICIAL_ALGORITHM_CANDIDATE"
    NON_OFFICIAL_FORMULA_CANDIDATE = "NON_OFFICIAL_FORMULA_CANDIDATE"
    NON_OFFICIAL_PARAMETER_CANDIDATE = "NON_OFFICIAL_PARAMETER_CANDIDATE"
    NON_OFFICIAL_MICROSTRUCTURE_CANDIDATE = "NON_OFFICIAL_MICROSTRUCTURE_CANDIDATE"
    NON_OFFICIAL_QUANTUM_CANDIDATE = "NON_OFFICIAL_QUANTUM_CANDIDATE"
    NON_OFFICIAL_CLASSICAL_CANDIDATE = "NON_OFFICIAL_CLASSICAL_CANDIDATE"
    NON_OFFICIAL_HYBRID_CANDIDATE = "NON_OFFICIAL_HYBRID_CANDIDATE"
    QUARANTINED_SECURITY_RISK = "QUARANTINED_SECURITY_RISK"
    REJECTED_DUPLICATE_IRRELEVANT_OR_UNSAFE = "REJECTED_DUPLICATE_IRRELEVANT_OR_UNSAFE"


class ProfitValidationTag(StrEnum):
    PROFIT_NOT_TESTED = "PROFIT_NOT_TESTED"
    REPLAY_PROFITABLE = "REPLAY_PROFITABLE"
    PAPER_PROFITABLE = "PAPER_PROFITABLE"
    REPLAY_AND_PAPER_PROFITABLE = "REPLAY_AND_PAPER_PROFITABLE"
    REPLAY_NON_PROFITABLE = "REPLAY_NON_PROFITABLE"
    PAPER_NON_PROFITABLE = "PAPER_NON_PROFITABLE"
    REPLAY_AND_PAPER_NON_PROFITABLE = "REPLAY_AND_PAPER_NON_PROFITABLE"
    REPLAY_PAPER_CONFLICTING = "REPLAY_PAPER_CONFLICTING"
    REPLAY_PAPER_INCONCLUSIVE = "REPLAY_PAPER_INCONCLUSIVE"
    WALK_FORWARD_REQUIRED = "WALK_FORWARD_REQUIRED"
    OWNER_REVIEW_REQUIRED_AFTER_PROFIT_TEST = "OWNER_REVIEW_REQUIRED_AFTER_PROFIT_TEST"
    RETIRED_NON_PROFITABLE = "RETIRED_NON_PROFITABLE"
    PROMOTION_EVIDENCE_NOT_IN_SCOPE_FOR_THIS_PR = "PROMOTION_EVIDENCE_NOT_IN_SCOPE_FOR_THIS_PR"


class RowLevelAggregateProvenanceTag(StrEnum):
    ROW_ALL_REQUIRED_FIELDS_OFFICIAL_CONFIRMED = "ROW_ALL_REQUIRED_FIELDS_OFFICIAL_CONFIRMED"
    ROW_PARTIAL_OFFICIAL_CONFIRMED = "ROW_PARTIAL_OFFICIAL_CONFIRMED"
    ROW_RESEARCH_CANDIDATE_ONLY = "ROW_RESEARCH_CANDIDATE_ONLY"
    ROW_MIXED_OFFICIAL_AND_RESEARCH = "ROW_MIXED_OFFICIAL_AND_RESEARCH"
    ROW_REPLAY_PAPER_PROFIT_PROVEN = "ROW_REPLAY_PAPER_PROFIT_PROVEN"
    ROW_REPLAY_PAPER_NON_PROFITABLE = "ROW_REPLAY_PAPER_NON_PROFITABLE"
    ROW_REPLAY_PAPER_CONFLICTING = "ROW_REPLAY_PAPER_CONFLICTING"
    ROW_PENDING_PROFIT_TEST = "ROW_PENDING_PROFIT_TEST"
    ROW_QUARANTINED = "ROW_QUARANTINED"
    ROW_REJECTED_OR_RETIRED = "ROW_REJECTED_OR_RETIRED"


class AtomicRowsReadinessState(StrEnum):
    ATOMICROWS_OFFICIAL_SOURCE_READY = "atomicrows_official_source_ready"
    ATOMICROWS_RESEARCH_CANDIDATE_READY = "atomicrows_research_candidate_ready"
    ATOMICROWS_REPLAY_PAPER_CANDIDATE_READY = "atomicrows_replay_paper_candidate_ready"
    ATOMICROWS_PROFIT_PROVEN_READY = "atomicrows_profit_proven_ready"
    ATOMICROWS_NON_PROFITABLE_RETIRED = "atomicrows_non_profitable_retired"
    ATOMICROWS_QUANTUM_CANDIDATE_READY = "atomicrows_quantum_candidate_ready"
    ATOMICROWS_OWNER_POLICY_READY = "atomicrows_owner_policy_ready"
    ATOMICROWS_CONNECTOR_FACT_PENDING = "atomicrows_connector_fact_pending"
    ATOMICROWS_LIVE_USE_PENDING = "atomicrows_live_use_pending"


class TerminalCompletionState(StrEnum):
    COMPLETED_AS_OFFICIAL_EXTERNAL_FACT = "completed_as_official_external_fact"
    COMPLETED_AS_OFFICIAL_CONFIRMED_REUSE_FROM_PREVIOUS_PR = (
        "completed_as_official_confirmed_reuse_from_previous_pr"
    )
    COMPLETED_AS_OPEN_RESEARCH_INPUT = "completed_as_open_research_input"
    COMPLETED_AS_ALGORITHM_CANDIDATE = "completed_as_algorithm_candidate"
    COMPLETED_AS_FORMULA_CANDIDATE = "completed_as_formula_candidate"
    COMPLETED_AS_PARAMETER_CANDIDATE = "completed_as_parameter_candidate"
    COMPLETED_AS_EDGE_HYPOTHESIS_CANDIDATE = "completed_as_edge_hypothesis_candidate"
    COMPLETED_AS_MICROSTRUCTURE_CANDIDATE = "completed_as_microstructure_candidate"
    COMPLETED_AS_QUANTUM_CANDIDATE = "completed_as_quantum_candidate"
    COMPLETED_AS_CLASSICAL_CANDIDATE = "completed_as_classical_candidate"
    COMPLETED_AS_HYBRID_CANDIDATE = "completed_as_hybrid_candidate"
    COMPLETED_AS_REPLAY_PAPER_TEST_CANDIDATE = "completed_as_replay_paper_test_candidate"
    COMPLETED_AS_PROFIT_PROVEN_REPLAY_PAPER_CANDIDATE = (
        "completed_as_profit_proven_replay_paper_candidate"
    )
    COMPLETED_AS_NON_PROFITABLE_RETIRED_CANDIDATE = (
        "completed_as_non_profitable_retired_candidate"
    )
    COMPLETED_AS_OWNER_POLICY_INPUT = "completed_as_owner_policy_input"
    COMPLETED_AS_PRIVATE_DOC_ATTESTATION_ROUTE = "completed_as_private_doc_attestation_route"
    COMPLETED_AS_RUNTIME_FUTURE_ROUTE = "completed_as_runtime_future_route"
    COMPLETED_AS_CONNECTOR_FUTURE_ROUTE = "completed_as_connector_future_route"
    COMPLETED_AS_DUPLICATE_IRRELEVANT_OR_SUPERSEDED = (
        "completed_as_duplicate_irrelevant_or_superseded"
    )
    COMPLETED_AS_SECURITY_QUARANTINE = "completed_as_security_quarantine"
    COMPLETED_AS_EXACT_SCOPE_REPAIR_ROUTE = "completed_as_exact_scope_repair_route"


class ReplayPaperRouteState(StrEnum):
    REPLAY_PAPER_ROUTE_CREATED_NOT_EXECUTED = "REPLAY_PAPER_ROUTE_CREATED_NOT_EXECUTED"
    REPLAY_REQUIRED_BEFORE_PROMOTION = "REPLAY_REQUIRED_BEFORE_PROMOTION"
    PAPER_REQUIRED_BEFORE_PROMOTION = "PAPER_REQUIRED_BEFORE_PROMOTION"
    WALK_FORWARD_REVIEW_REQUIRED = "WALK_FORWARD_REVIEW_REQUIRED"
    OWNER_REVIEW_REQUIRED_AFTER_DUAL_RESULT = "OWNER_REVIEW_REQUIRED_AFTER_DUAL_RESULT"
    LIVE_USE_FORBIDDEN_UNTIL_PROMOTED = "LIVE_USE_FORBIDDEN_UNTIL_PROMOTED"


class SourceQualityTier(StrEnum):
    TIER_0_OFFICIAL_FACT_SOURCE = "TIER_0_OFFICIAL_FACT_SOURCE"
    TIER_1_PEER_REVIEWED_OR_FORMAL_RESEARCH = "TIER_1_PEER_REVIEWED_OR_FORMAL_RESEARCH"
    TIER_2_REPRODUCIBLE_RESEARCH_OR_CODE = "TIER_2_REPRODUCIBLE_RESEARCH_OR_CODE"
    TIER_3_MARKET_ANALYSIS_OR_NEWS = "TIER_3_MARKET_ANALYSIS_OR_NEWS"
    TIER_4_SOCIAL_FORUM_SIGNAL = "TIER_4_SOCIAL_FORUM_SIGNAL"
    TIER_5_OWNER_SUBMITTED_OR_PRIVATE_ATTESTED = "TIER_5_OWNER_SUBMITTED_OR_PRIVATE_ATTESTED"


class SourceClaimType(StrEnum):
    VENUE_FACT_CLAIM = "VENUE_FACT_CLAIM"
    API_FIELD_CLAIM = "API_FIELD_CLAIM"
    FEE_TICK_SETTLEMENT_CLAIM = "FEE_TICK_SETTLEMENT_CLAIM"
    MARKET_MICROSTRUCTURE_CLAIM = "MARKET_MICROSTRUCTURE_CLAIM"
    STRATEGY_CLAIM = "STRATEGY_CLAIM"
    ALGORITHM_CLAIM = "ALGORITHM_CLAIM"
    FORMULA_CLAIM = "FORMULA_CLAIM"
    PARAMETER_RANGE_CLAIM = "PARAMETER_RANGE_CLAIM"
    SIGNAL_FEATURE_CLAIM = "SIGNAL_FEATURE_CLAIM"
    LATENCY_HEURISTIC_CLAIM = "LATENCY_HEURISTIC_CLAIM"
    RISK_HEURISTIC_CLAIM = "RISK_HEURISTIC_CLAIM"
    QUANTUM_OPTIMIZATION_CLAIM = "QUANTUM_OPTIMIZATION_CLAIM"
    ARBITRAGE_PATTERN_CLAIM = "ARBITRAGE_PATTERN_CLAIM"
    PORTFOLIO_OPTIMIZATION_CLAIM = "PORTFOLIO_OPTIMIZATION_CLAIM"
    EXECUTION_GUARDRAIL_CLAIM = "EXECUTION_GUARDRAIL_CLAIM"


class QuantumApplicabilityClass(StrEnum):
    CLASSICAL_ONLY = "CLASSICAL_ONLY"
    QUANTUM_INSPIRED = "QUANTUM_INSPIRED"
    HYBRID_CLASSICAL_QUANTUM = "HYBRID_CLASSICAL_QUANTUM"
    TRUE_QUANTUM_READY_LATER = "TRUE_QUANTUM_READY_LATER"
    QUBO_COMPATIBLE = "QUBO_COMPATIBLE"
    ISING_COMPATIBLE = "ISING_COMPATIBLE"
    QAOA_COMPATIBLE = "QAOA_COMPATIBLE"
    VQE_COMPATIBLE = "VQE_COMPATIBLE"
    ANNEALING_COMPATIBLE = "ANNEALING_COMPATIBLE"
    QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE = (
        "QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE"
    )
    NOT_QUANTUM_RELEVANT = "NOT_QUANTUM_RELEVANT"


class SourceRiskTier(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    QUARANTINE = "QUARANTINE"


NO_AUTHORITY_CONFIRMATION = {
    "runtime_execution_created": False,
    "live_execution_created": False,
    "connector_semantic_binding_created": False,
    "private_state_fetch_created": False,
    "runtime_cash_receipt_created": False,
    "replay_execution_created": False,
    "paper_execution_created": False,
    "scoring_execution_created": False,
    "ranking_execution_created": False,
    "selection_execution_created": False,
    "optimizer_execution_created": False,
    "quantum_backend_execution_created": False,
    "quantum_simulator_execution_created": False,
    "order_authority_created": False,
    "fill_evidence_created": False,
    "profit_evidence_created": False,
    "latency_superiority_claim_created": False,
    "execution_superiority_claim_created": False,
    "quantum_advantage_claim_created": False,
    "qtt_checksum_freeze_global_digest_authority_created": False,
    "atomicrows_bundle_checksum_hash_authority_created": False,
    "final_atomicrows_bundle_created": False,
}

ZERO_AUTHORITY_COUNTS = {
    "runtime_live_order_profit_authority_count": 0,
    "replay_paper_execution_count": 0,
    "scoring_ranking_selection_execution_count": 0,
    "optimizer_execution_count": 0,
    "quantum_backend_execution_count": 0,
    "quantum_simulator_execution_count": 0,
    "quantum_advantage_claim_count": 0,
    "latency_superiority_claim_count": 0,
    "execution_superiority_claim_count": 0,
    "profit_evidence_count": 0,
    "qtt_checksum_freeze_global_digest_authority_count": 0,
    "atomicrows_bundle_checksum_hash_authority_count": 0,
    "final_atomicrows_bundle_count": 0,
}

FORBIDDEN_PLACEHOLDER_VALUES = frozenset(
    {
        "TBD",
        "TODO",
        "UNKNOWN",
        "PLACEHOLDER",
        "FILL_LATER",
        "OWNER_WILL_PROVIDE",
        "SOURCE_NEEDED",
        "BLOCKED",
        "UNRESOLVED",
        "N/A",
    }
)


def enum_values(enum_type: type[StrEnum]) -> tuple[str, ...]:
    return tuple(item.value for item in enum_type)


CENTRAL_ENUM_VALUE_SETS = {
    "official_source_class": enum_values(OfficialSourceClass),
    "open_research_source_class": enum_values(OpenResearchSourceClass),
    "prohibited_executable_trust_input": enum_values(ProhibitedExecutableTrustInput),
    "authority_class": enum_values(AuthorityClass),
    "source_provenance_tag": enum_values(SourceProvenanceTag),
    "profit_validation_tag": enum_values(ProfitValidationTag),
    "row_level_aggregate_provenance_tag": enum_values(RowLevelAggregateProvenanceTag),
    "atomicrows_readiness_state": enum_values(AtomicRowsReadinessState),
    "terminal_completion_state": enum_values(TerminalCompletionState),
    "replay_paper_route_state": enum_values(ReplayPaperRouteState),
    "source_quality_tier": enum_values(SourceQualityTier),
    "source_claim_type": enum_values(SourceClaimType),
    "quantum_applicability_class": enum_values(QuantumApplicabilityClass),
    "source_risk_tier": enum_values(SourceRiskTier),
}

TERMINAL_COMPLETION_STATES = frozenset(enum_values(TerminalCompletionState))
SOURCE_PROVENANCE_TAGS = frozenset(enum_values(SourceProvenanceTag))
PROFIT_VALIDATION_TAGS = frozenset(enum_values(ProfitValidationTag))
AUTHORITY_CLASSES = frozenset(enum_values(AuthorityClass))
SOURCE_CLASSES = frozenset(enum_values(OfficialSourceClass) + enum_values(OpenResearchSourceClass))

RESEARCH_SOURCE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "source_id": "PR159S_RESEARCH_SOURCE_HANSON_LMSR",
        "source_class": OpenResearchSourceClass.ACADEMIC_PAPER.value,
        "source_quality_tier": SourceQualityTier.TIER_1_PEER_REVIEWED_OR_FORMAL_RESEARCH.value,
        "source_locator": "https://hanson.gmu.edu/mktscore.pdf",
        "title": "Logarithmic Market Scoring Rules",
        "author_or_handle": "Robin Hanson",
        "publication_time_if_available": None,
        "claim_types": [
            SourceClaimType.FORMULA_CLAIM.value,
            SourceClaimType.ALGORITHM_CLAIM.value,
        ],
        "candidate_family": "lmsr_market_maker_formula",
        "reproducibility_level": "formal_formula_source",
        "evidence_strength": "FORMAL_RESEARCH_SOURCE",
        "hallucination_risk": "LOW",
        "manipulation_risk": "LOW",
    },
    {
        "source_id": "PR159S_RESEARCH_SOURCE_POLYMARKET_MICROSTRUCTURE_PREPRINT",
        "source_class": OpenResearchSourceClass.PREPRINT.value,
        "source_quality_tier": SourceQualityTier.TIER_1_PEER_REVIEWED_OR_FORMAL_RESEARCH.value,
        "source_locator": "https://arxiv.org/abs/2604.24366",
        "title": "The Anatomy of a Decentralized Prediction Market",
        "author_or_handle": None,
        "publication_time_if_available": None,
        "claim_types": [
            SourceClaimType.MARKET_MICROSTRUCTURE_CLAIM.value,
            SourceClaimType.SIGNAL_FEATURE_CLAIM.value,
        ],
        "candidate_family": "orderbook_microstructure_feature_candidate",
        "reproducibility_level": "paper_with_described_data_method",
        "evidence_strength": "FORMAL_RESEARCH_SOURCE",
        "hallucination_risk": "LOW",
        "manipulation_risk": "MEDIUM",
    },
    {
        "source_id": "PR159S_RESEARCH_SOURCE_AGENTBETS_MICROSTRUCTURE",
        "source_class": OpenResearchSourceClass.MICROSTRUCTURE_WRITEUP.value,
        "source_quality_tier": SourceQualityTier.TIER_3_MARKET_ANALYSIS_OR_NEWS.value,
        "source_locator": "https://agentbets.ai/guides/prediction-market-microstructure/",
        "title": "Market Microstructure for Prediction Markets",
        "author_or_handle": "AgentBets.ai",
        "publication_time_if_available": None,
        "claim_types": [
            SourceClaimType.MARKET_MICROSTRUCTURE_CLAIM.value,
            SourceClaimType.LATENCY_HEURISTIC_CLAIM.value,
        ],
        "candidate_family": "spread_depth_slippage_vwap_feature_candidate",
        "reproducibility_level": "market_analysis_writeup",
        "evidence_strength": "ANALYST_SOURCE_REQUIRES_REPLAY",
        "hallucination_risk": "MEDIUM",
        "manipulation_risk": "MEDIUM",
    },
    {
        "source_id": "PR159S_RESEARCH_SOURCE_TENPOLY_ARBITRAGE",
        "source_class": OpenResearchSourceClass.TRADING_ARTICLE.value,
        "source_quality_tier": SourceQualityTier.TIER_3_MARKET_ANALYSIS_OR_NEWS.value,
        "source_locator": "https://tenpoly.com/blog/how-polymarket-arbitrage-works",
        "title": "How Polymarket Arbitrage Works",
        "author_or_handle": "Tenpoly",
        "publication_time_if_available": None,
        "claim_types": [
            SourceClaimType.STRATEGY_CLAIM.value,
            SourceClaimType.ARBITRAGE_PATTERN_CLAIM.value,
            SourceClaimType.RISK_HEURISTIC_CLAIM.value,
        ],
        "candidate_family": "cross_venue_arbitrage_route_candidate",
        "reproducibility_level": "strategy_writeup_requires_independent_test",
        "evidence_strength": "TRADING_ARTICLE_REQUIRES_REPLAY",
        "hallucination_risk": "MEDIUM",
        "manipulation_risk": "HIGH",
    },
    {
        "source_id": "PR159S_RESEARCH_SOURCE_PMXT_UNIFIED_API",
        "source_class": OpenResearchSourceClass.THIRD_PARTY_ANALYSIS.value,
        "source_quality_tier": SourceQualityTier.TIER_3_MARKET_ANALYSIS_OR_NEWS.value,
        "source_locator": "https://www.pmxt.dev/",
        "title": "pmxt Prediction Market API",
        "author_or_handle": "PMXT",
        "publication_time_if_available": None,
        "claim_types": [
            SourceClaimType.STRATEGY_CLAIM.value,
            SourceClaimType.API_FIELD_CLAIM.value,
        ],
        "candidate_family": "multi_venue_normalization_research_candidate",
        "reproducibility_level": "third_party_product_docs_not_qtt_authority",
        "evidence_strength": "THIRD_PARTY_SOURCE_REQUIRES_OFFICIAL_FIELD_CHECK",
        "hallucination_risk": "MEDIUM",
        "manipulation_risk": "HIGH",
    },
    {
        "source_id": "PR159S_RESEARCH_SOURCE_GITHUB_POLYMARKET_KALSHI_ARB",
        "source_class": OpenResearchSourceClass.GITHUB_REPOSITORY.value,
        "source_quality_tier": SourceQualityTier.TIER_2_REPRODUCIBLE_RESEARCH_OR_CODE.value,
        "source_locator": "https://github.com/terauss/Polymarket-Kalshi-Arbitrage-bot",
        "title": "Polymarket Kalshi Arbitrage bot",
        "author_or_handle": "terauss",
        "publication_time_if_available": None,
        "claim_types": [
            SourceClaimType.CODE_SNIPPET_REFERENCE.value
            if hasattr(SourceClaimType, "CODE_SNIPPET_REFERENCE")
            else SourceClaimType.STRATEGY_CLAIM.value,
            SourceClaimType.ARBITRAGE_PATTERN_CLAIM.value,
        ],
        "candidate_family": "external_code_reference_quarantined_execution_candidate",
        "reproducibility_level": "repository_reference_not_executed",
        "evidence_strength": "CODE_REFERENCE_REQUIRES_SECURITY_REVIEW",
        "hallucination_risk": "MEDIUM",
        "manipulation_risk": "HIGH",
    },
    {
        "source_id": "PR159S_RESEARCH_SOURCE_PREDICTIONMARKETBENCH",
        "source_class": OpenResearchSourceClass.PREPRINT.value,
        "source_quality_tier": SourceQualityTier.TIER_1_PEER_REVIEWED_OR_FORMAL_RESEARCH.value,
        "source_locator": "https://arxiv.org/abs/2602.00133",
        "title": "PredictionMarketBench",
        "author_or_handle": None,
        "publication_time_if_available": None,
        "claim_types": [
            SourceClaimType.ALGORITHM_CLAIM.value,
            SourceClaimType.SIGNAL_FEATURE_CLAIM.value,
        ],
        "candidate_family": "event_driven_replay_benchmark_candidate",
        "reproducibility_level": "benchmark_method_source",
        "evidence_strength": "FORMAL_RESEARCH_SOURCE",
        "hallucination_risk": "LOW",
        "manipulation_risk": "MEDIUM",
    },
    {
        "source_id": "PR159S_RESEARCH_SOURCE_QUBO_PORTFOLIO_ANNEALING",
        "source_class": OpenResearchSourceClass.PREPRINT.value,
        "source_quality_tier": SourceQualityTier.TIER_1_PEER_REVIEWED_OR_FORMAL_RESEARCH.value,
        "source_locator": "https://arxiv.org/abs/2303.12601",
        "title": "A real world test of Portfolio Optimization with Quantum Annealing",
        "author_or_handle": None,
        "publication_time_if_available": None,
        "claim_types": [
            SourceClaimType.QUANTUM_OPTIMIZATION_CLAIM.value,
            SourceClaimType.PORTFOLIO_OPTIMIZATION_CLAIM.value,
        ],
        "candidate_family": "qubo_portfolio_optimizer_candidate",
        "reproducibility_level": "formal_quantum_optimization_source",
        "evidence_strength": "FORMAL_RESEARCH_SOURCE",
        "hallucination_risk": "LOW",
        "manipulation_risk": "LOW",
    },
    {
        "source_id": "PR159S_RESEARCH_SOURCE_REDDIT_ORDERBOOK_TICKS",
        "source_class": OpenResearchSourceClass.FORUM_THREAD.value,
        "source_quality_tier": SourceQualityTier.TIER_4_SOCIAL_FORUM_SIGNAL.value,
        "source_locator": "https://www.reddit.com/r/Polymarket/comments/1rsi01o/i_collected_19_billion_orderbook_ticks_from/",
        "title": "Polymarket orderbook tick collection discussion",
        "author_or_handle": None,
        "publication_time_if_available": None,
        "claim_types": [
            SourceClaimType.SIGNAL_FEATURE_CLAIM.value,
            SourceClaimType.MARKET_MICROSTRUCTURE_CLAIM.value,
        ],
        "candidate_family": "social_orderbook_signal_scouting_candidate",
        "reproducibility_level": "forum_claim_requires_independent_dataset",
        "evidence_strength": "SOCIAL_SIGNAL_ONLY_REQUIRES_REPLAY",
        "hallucination_risk": "HIGH",
        "manipulation_risk": "HIGH",
    },
)
