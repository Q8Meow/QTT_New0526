"""Central constants for the PR137R AtomicRows reconciliation audit."""

from __future__ import annotations

from pathlib import Path


PR_ID = "PR137R"
TITLE = "AtomicRows 4,183-row functional bundle reconciliation audit"
BRANCH = "pr137r-atomicrows-functional-bundle-reconciliation-audit"
BASE_HEAD_PREFIX = "f885935"
AUTHORITY_CLASS = (
    "CANONICAL_POST_PR137_ATOMICROWS_FUNCTIONAL_BUNDLE_RECONCILIATION_AUDIT_"
    "NOT_BUNDLE_CREATION_AUTHORITY"
)
SCOPE_CLASS = (
    "REPAIR_AUDIT",
    "ROADMAP_RECONCILIATION",
    "STATIC_CONTRACT_READY",
    "ATOMICROWS_FUNCTIONAL_BUNDLE_TRUTH_RECONCILIATION",
)
REPORT_TYPE = "QTT_PR137R_ATOMICROWS_FUNCTIONAL_BUNDLE_RECONCILIATION_REPORT"
INDEX_TYPE = "QTT_PR137R_ATOMICROWS_FUNCTIONAL_BUNDLE_RECONCILIATION_INDEX"
STATIC_TIME = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"
EXPECTED_ROW_COUNT = 4183

STATUS_PRESENT_AND_STATICALLY_VALIDATED = "PRESENT_AND_STATICALLY_VALIDATED"
STATUS_PRESENT_BUT_INVALID = "PRESENT_BUT_INVALID"
STATUS_NOT_CREATED = "NOT_CREATED"
STATUS_PATH_PRESENT_BUT_EMPTY = "PATH_PRESENT_BUT_EMPTY"
STATUS_ROW_COUNT_NOT_PROVEN = "ROW_COUNT_NOT_PROVEN"
STATUS_ROW_COUNT_MISMATCH = "ROW_COUNT_MISMATCH"
STATUS_ROW_SCHEMA_NOT_PROVEN = "ROW_SCHEMA_NOT_PROVEN"
STATUS_ROW_FAMILY_SOURCES_MISSING = "ROW_FAMILY_SOURCES_MISSING"
STATUS_BUILDER_MISSING = "BUILDER_MISSING"
STATUS_VALIDATOR_MISSING = "VALIDATOR_MISSING"
STATUS_AGENT_CONSUMER_MISSING = "AGENT_CONSUMER_MISSING"
STATUS_READINESS_GATE_MISSING = "READINESS_GATE_MISSING"
STATUS_LEGACY_LABEL_ONLY = "LEGACY_ROADMAP_LABEL_ONLY_NOT_ARTIFACT_PROOF"
STATUS_REQUIRES_OWNER_IMPLEMENTATION = (
    "REQUIRES_OWNER_APPROVED_BUNDLE_IMPLEMENTATION_PR"
)

ATOMICROWS_FUNCTIONAL_BUNDLE_STATUSES = (
    STATUS_PRESENT_AND_STATICALLY_VALIDATED,
    STATUS_PRESENT_BUT_INVALID,
    STATUS_NOT_CREATED,
    STATUS_PATH_PRESENT_BUT_EMPTY,
    STATUS_ROW_COUNT_NOT_PROVEN,
    STATUS_ROW_COUNT_MISMATCH,
    STATUS_ROW_SCHEMA_NOT_PROVEN,
    STATUS_ROW_FAMILY_SOURCES_MISSING,
    STATUS_BUILDER_MISSING,
    STATUS_VALIDATOR_MISSING,
    STATUS_AGENT_CONSUMER_MISSING,
    STATUS_READINESS_GATE_MISSING,
    STATUS_LEGACY_LABEL_ONLY,
    STATUS_REQUIRES_OWNER_IMPLEMENTATION,
)

REASON_PR137R_OK = "PR137R_OK"
REASON_BASELINE_BRANCH_MISMATCH = "PR137R_BASELINE_BRANCH_MISMATCH"
REASON_BASELINE_HEAD_MISMATCH = "PR137R_BASELINE_HEAD_MISMATCH"
REASON_BASELINE_DIRTY_WORKTREE = "PR137R_BASELINE_DIRTY_WORKTREE"
RECEIPT_CI_DETACHED_HEAD_MODE = "CI_DETACHED_HEAD_MODE_ACTIVE"
RECEIPT_CI_SHALLOW_FETCH_ANCESTRY_SKIPPED = (
    "CI_SHALLOW_FETCH_ANCESTRY_CHECK_SKIPPED"
)
RECEIPT_CI_MERGE_REF_BASELINE_ACCEPTED = "PR137R_CI_MERGE_REF_BASELINE_ACCEPTED"
REASON_PR136_SELECTOR_REQUIRED = "PR137R_PR136_SELECTOR_REQUIRED"
REASON_PR137_DEPENDENCY_CONTROLLER_REQUIRED = (
    "PR137R_PR137_DEPENDENCY_CONTROLLER_REQUIRED"
)
REASON_CROSSWALK_CONTEXT_REQUIRED = "PR137R_CROSSWALK_CONTEXT_REQUIRED"
REASON_ATOMICROWS_DISCOVERY_OK = "PR137R_ATOMICROWS_DISCOVERY_OK"
REASON_BUNDLE_NOT_CREATED = (
    "PR137R_ATOMICROWS_FUNCTIONAL_BUNDLE_NOT_CREATED_RECORDED"
)
REASON_BUNDLE_PRESENT = "PR137R_ATOMICROWS_FUNCTIONAL_BUNDLE_PRESENT_RECORDED"
REASON_4183_ROWS_PROVEN = "PR137R_ATOMICROWS_4183_ROWS_PROVEN"
REASON_4183_ROWS_NOT_PROVEN = "PR137R_ATOMICROWS_4183_ROWS_NOT_PROVEN"
REASON_ROW_COUNT_MISMATCH = "PR137R_ATOMICROWS_ROW_COUNT_MISMATCH"
REASON_ROW_SCHEMA_NOT_PROVEN = "PR137R_ATOMICROWS_ROW_SCHEMA_NOT_PROVEN"
REASON_ROW_FAMILY_SOURCES_MISSING = (
    "PR137R_ATOMICROWS_ROW_FAMILY_SOURCES_MISSING"
)
REASON_BUNDLE_BUILDER_MISSING = "PR137R_ATOMICROWS_BUNDLE_BUILDER_MISSING"
REASON_VALIDATOR_MISSING = "PR137R_ATOMICROWS_VALIDATOR_MISSING"
REASON_AGENT_CONSUMER_MISSING = "PR137R_ATOMICROWS_AGENT_CONSUMER_MISSING"
REASON_READINESS_GATE_MISSING = "PR137R_ATOMICROWS_READINESS_GATE_MISSING"
REASON_LEGACY_LABEL_ONLY = (
    "PR137R_LEGACY_ROADMAP_LABEL_ONLY_NOT_ARTIFACT_PROOF"
)
REASON_FALSE_COMPLETION_FORBIDDEN = (
    "PR137R_FALSE_COMPLETION_CLAIM_FORBIDDEN"
)
REASON_SEQUENCE_SLOT_NOT_FOUND = (
    "PR137R_CURRENT_SEQUENCE_ATOMICROWS_BUNDLE_IMPLEMENTATION_SLOT_NOT_FOUND"
)
REASON_OWNER_SEQUENCE_ASSIGNMENT_REQUIRED = (
    "PR137R_OWNER_SEQUENCE_ASSIGNMENT_REQUIRED"
)
REASON_SEQUENCE_INSERTED = "PR137R_SEQUENCE_INSERTED_BEFORE_PR137L"
REASON_SEQUENCE_INSERTION_OWNER_REVIEW = (
    "PR137R_SEQUENCE_INSERTION_REQUIRES_OWNER_REVIEW"
)
REASON_NO_QTT_SHA_DIGEST_AUTHORITY = "PR137R_NO_QTT_SHA_DIGEST_AUTHORITY"
REASON_SHA_SIDECAR_REFERENCE_FORBIDDEN = (
    "PR137R_ATOMICROWS_SHA_SIDE_CAR_REFERENCE_FORBIDDEN"
)
REASON_BUNDLE_GENERATION_FORBIDDEN = (
    "PR137R_ATOMICROWS_BUNDLE_GENERATION_FORBIDDEN"
)
REASON_ROW_CREATION_FORBIDDEN = "PR137R_ATOMICROWS_ROW_CREATION_FORBIDDEN"
REASON_QUANTUM_EXECUTION_FORBIDDEN = "PR137R_QUANTUM_EXECUTION_FORBIDDEN"
REASON_QUANTUM_SCHEMA_GAP = (
    "PR137R_QUANTUM_COMPATIBILITY_SCHEMA_GAP_RECORDED"
)
REASON_LIVE_ORDER_PROFIT_FORBIDDEN = (
    "PR137R_LIVE_ORDER_PROFIT_AUTHORITY_FORBIDDEN"
)
REASON_MARKET_ROADMAP_FORK_FORBIDDEN = "PR137R_MARKET_ROADMAP_FORK_FORBIDDEN"
REASON_FORECASTEX_ALIAS_FORBIDDEN = "PR137R_FORECASTEX_ALIAS_FORBIDDEN"
REASON_IDEMPOTENCY_FAILURE = "PR137R_IDEMPOTENCY_FAILURE"
REASON_ALLOWLIST_EXPANSION_REQUIRED = "PR137R_ALLOWLIST_EXPANSION_REQUIRED"

SUCCESS_RECEIPTS = (
    "QTT_PR137R_ATOMICROWS_FUNCTIONAL_BUNDLE_RECONCILIATION_AUDIT_OK",
    "QTT_PR137R_NO_FALSE_ATOMICROWS_COMPLETION_CLAIMS_OK",
    "QTT_PR137R_LEGACY_PR97_PR101_RECONCILIATION_OK",
    "QTT_PR137R_REPO_ARTIFACT_TRUTH_NOT_PR_LABELS_OK",
    "QTT_PR137R_NO_ATOMICROWS_BUNDLE_GENERATION_OK",
    "QTT_PR137R_NO_QTT_SHA_DIGEST_AUTHORITY_OK",
    "QTT_PR137R_NO_RUNTIME_LIVE_ORDER_PROFIT_AUTHORITY_OK",
    "QTT_PR137R_QUANTUM_COMPATIBILITY_AUDIT_ONLY_OK",
    "QTT_PR137R_IDEMPOTENT_REPORT_OK",
)
RECEIPT_BUNDLE_MISSING = (
    "QTT_PR137R_ATOMICROWS_FUNCTIONAL_BUNDLE_NOT_CREATED_RECORDED"
)
RECEIPT_ROWS_NOT_PROVEN = "QTT_PR137R_ATOMICROWS_4183_ROWS_NOT_PROVEN_RECORDED"
RECEIPT_BUNDLE_VALID = (
    "QTT_PR137R_ATOMICROWS_FUNCTIONAL_BUNDLE_PRESENT_STATICALLY_VALIDATED_RECORDED"
)
RECEIPT_ROWS_PROVEN = "QTT_PR137R_ATOMICROWS_4183_ROWS_PROVEN_RECORDED"
RECEIPT_OWNER_SEQUENCE_ASSIGNMENT = (
    "QTT_PR137R_OWNER_SEQUENCE_ASSIGNMENT_REQUIRED_RECORDED"
)

CANONICAL_MARKET_SCOPES = (
    "PREDICTION_MARKETS_GENERAL",
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
)
FORBIDDEN_THIRD_VENUE_ALIASES = (
    "FORECASTEX",
    "FORECASTX",
    "IBKR_FORECASTX",
    "forecastx",
)

REPORT_PATH = Path(
    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"
)
INDEX_PATH = Path(
    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.index.json"
)
BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")
MATERIALIZED_ROW_SCHEMA_PATH = Path(
    "schemas/atomicrows/atomicrows_materialized_bundle_row.schema.json"
)

PR136_SELECTOR_ARTIFACTS = (
    "docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json",
    "docs/master_plan/generated/PR136FuturePRCardRegistry.report.json",
    "docs/master_plan/generated/PR136LaunchReadinessDependencyGraph.report.json",
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "src/qtt/stage1_prediction_markets/launch_readiness/day1_launch_readiness_roadmap.py",
    "tools/validate_pr136_day1_launch_readiness_roadmap.py",
)
PR137_DEPENDENCY_CONTROLLER_ARTIFACTS = (
    "docs/master_plan/generated/PR137LaunchReadinessDependencyController.report.json",
    "docs/master_plan/generated/PR137DependencyGateStateMatrix.report.json",
    "docs/master_plan/generated/PR137ValidationGateIntegration.report.json",
    "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_controller.py",
    "src/qtt/stage1_prediction_markets/launch_readiness/pr137_launch_readiness_dependency_policy.py",
    "tools/validate_pr137_launch_readiness_dependency_controller.py",
)
CROSSWALK_CONTEXT_ARTIFACTS = (
    "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR135MarketSpecificSectionIndex.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/SectionManifest.json",
    "docs/master_plan/generated/MasterPlanSectionCoverageReport.json",
)
ROUTE_TRIAGE_ARTIFACTS = (
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/roadmap/generated/CODEX_PR136_ROUTE_TRIAGE_RECEIPT.json",
    "docs/roadmap/generated/CODEX_PR137_ROUTE_TRIAGE_RECEIPT.json",
)
ROW_FAMILY_SOURCE_GLOB = "docs/master_plan/atomic_rows/pr98_row_family_sources/*.source.jsonl"
EXACT_ROW_SOURCE_GLOB = "docs/master_plan/atomic_rows/exact_row_sources/*.exact_rows.jsonl"
BUNDLE_BUILDER_PATHS = (
    "tools/build_atomicrows_bundle.py",
    "tools/materialize_atomicrows_bundle_from_exact_rows.py",
)
BUNDLE_VALIDATOR_PATHS = (
    "tools/validate_atomicrows_bundle_materialization_manifest.py",
    "tools/validate_atomicrows_bundle_boundary_state_contract.py",
    "tools/validate_atomicrows_bundle_schema_checker_static.py",
    "tools/validate_atomicrows_bundle_builder_deterministic_assembly_gate.py",
)
AGENT_CONSUMER_PATHS = (
    "tools/validate_atomicrows_parameter_agent_binding_consumer_gate.py",
    "schemas/atomicrows/atomicrows_parameter_agent_binding_consumer_gate.schema.json",
    "docs/master_plan/generated/AtomicRowsParameterAgentBindingConsumerGate.report.json",
)
FINAL_READINESS_GATE_PATHS = (
    "tools/validate_atomicrows_full_bundle_final_readiness_gate.py",
    "docs/master_plan/generated/AtomicRowsFullBundleFinalReadinessGate.report.json",
)
NO_RUNTIME_NO_LIVE_VALIDATOR_PATHS = (
    "tools/validate_no_runtime_artifacts.py",
    "tools/validate_pr137_generated_integrity_authority_boundary.py",
    "tools/validate_atomicrows_bundle_boundary_state_contract.py",
)

PR137R_CREATED_PATHS = (
    "src/qtt/stage1_prediction_markets/atomicrows_bundle_reconciliation/__init__.py",
    "src/qtt/stage1_prediction_markets/atomicrows_bundle_reconciliation/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_bundle_reconciliation/model.py",
    "src/qtt/stage1_prediction_markets/atomicrows_bundle_reconciliation/report.py",
    "src/qtt/stage1_prediction_markets/atomicrows_bundle_reconciliation/validator.py",
    "tools/stage1_atomicrows_bundle_reconciliation_gate.py",
    "tests/stage1_prediction_markets/atomicrows_bundle_reconciliation/test_pr137r_atomicrows_bundle_reconciliation.py",
    REPORT_PATH.as_posix(),
    INDEX_PATH.as_posix(),
)
PROTECTED_UNTOUCHED_PATHS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    BUNDLE_PATH.as_posix(),
    "docs/master_plan/atomic_rows/pr98_row_family_sources",
    "docs/master_plan/atomic_rows/exact_row_sources",
    "tools/build_atomicrows_bundle.py",
    "tools/materialize_atomicrows_bundle_from_exact_rows.py",
)

OLD_ROADMAP_TASKS = (
    {
        "old_label": "PR97",
        "semantic_task_name": "AtomicRows full bundle row expansion plan",
        "expected_artifact_family": "ROW_EXPANSION_PLAN",
        "artifact_refs": (
            "docs/master_plan/atomicrows/AtomicRowsFullBundleRowExpansionPlan.yaml",
            "docs/master_plan/generated/AtomicRowsFullBundleRowExpansionPlan.report.json",
            "tools/validate_atomicrows_full_bundle_row_expansion_plan.py",
        ),
    },
    {
        "old_label": "PR98",
        "semantic_task_name": "AtomicRows bundle row-family source files",
        "expected_artifact_family": "ROW_FAMILY_SOURCE_FILES",
        "artifact_refs": (
            "docs/master_plan/atomicrows/AtomicRowsBundleRowFamilySourceFiles.yaml",
            "docs/master_plan/generated/AtomicRowsBundleRowFamilySourceFiles.report.json",
            "tools/validate_atomicrows_bundle_row_family_source_files.py",
        ),
    },
    {
        "old_label": "PR99",
        "semantic_task_name": "AtomicRows bundle builder",
        "expected_artifact_family": "BUNDLE_BUILDER",
        "artifact_refs": (
            "docs/master_plan/atomicrows/AtomicRowsBundleBuilderDeterministicAssemblyGate.yaml",
            "docs/master_plan/generated/AtomicRowsBundleBuilderDeterministicAssemblyGate.report.json",
            "tools/build_atomicrows_bundle.py",
            "tools/validate_atomicrows_bundle_builder_deterministic_assembly_gate.py",
        ),
    },
    {
        "old_label": "PR100",
        "semantic_task_name": "AtomicRows bundle SHA/freeze authority",
        "expected_artifact_family": "SHA_FREEZE_AUTHORITY",
        "artifact_refs": (
            "docs/master_plan/atomicrows/AtomicRowsBundleShaFreezeAuthorityGate.yaml",
            "docs/master_plan/generated/AtomicRowsBundleShaFreezeAuthorityGate.report.json",
            "tools/validate_atomicrows_bundle_sha_freeze_authority_gate.py",
        ),
    },
    {
        "old_label": "PR101",
        "semantic_task_name": "AtomicRows full bundle final readiness gate",
        "expected_artifact_family": "FINAL_READINESS_GATE",
        "artifact_refs": FINAL_READINESS_GATE_PATHS,
    },
)

ROW_CONTRACT_FIELDS = (
    "row_id",
    "row_family",
    "row_type",
    "lifecycle_state",
    "version_state",
    "deprecation_state",
    "parameter_family",
    "algorithm_family",
    "strategy_family",
    "signal_family",
    "scoring_family",
    "normalization_family",
    "risk_family",
    "execution_family",
    "capital_family",
    "latency_family",
    "error_guard_family",
    "quantum_family",
    "agent_role",
    "consumer_class",
    "allowed_consumers",
    "blocked_consumers",
    "command_matrix_binding",
    "market_scope",
    "venue_scope",
    "prediction_market_scope",
    "expected_net_profit_objective_family",
    "execution_cost_model_family",
    "latency_sensitivity_class",
    "capital_intensity_class",
    "risk_mode",
    "drawdown_control_family",
    "exposure_limit_family",
    "liquidity_context_family",
    "replay_required_flag",
    "paper_required_flag",
    "owner_review_required_flag",
    "live_use_allowed_flag",
    "order_authority_created_flag",
    "profit_evidence_created_flag",
    "quantum_applicability_class",
    "classical_only_flag",
    "quantum_inspired_flag",
    "true_quantum_compatible_flag",
    "qubo_compatible_flag",
    "ising_compatible_flag",
    "qaoa_compatible_flag",
    "vqe_compatible_flag",
    "annealing_compatible_flag",
    "quantum_kernel_feature_map_compatible_flag",
    "quantum_backend_execution_allowed_flag",
    "source_evidence_required_flag",
    "accepted_source_packet_required_flag",
    "research_input_only_flag",
    "external_fact_authority_flag",
)

FORBIDDEN_GENERATED_INTEGRITY_KEY = "sha" + "256"
