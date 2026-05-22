"""Central constants for PR138 AtomicRows semantic row-contract validation."""

from __future__ import annotations

from pathlib import Path


PR138_ID = "PR138"
PR_ID = PR138_ID
TITLE = "AtomicRows semantic row-contract schema expansion"
BRANCH = "pr138-atomicrows-semantic-row-contract-schema-expansion"
BASELINE_CHECKPOINT = "d1bce40"
PR138_AUTHORITY_CLASS = (
    "ATOMICROWS_SEMANTIC_CONTRACT_ONLY_NOT_BUNDLE_MUTATION_NOT_FINAL_READINESS"
)
AUTHORITY_CLASS = PR138_AUTHORITY_CLASS
REPORT_TYPE = "QTT_PR138_ATOMICROWS_SEMANTIC_ROW_CONTRACT_REPORT"
INDEX_TYPE = "QTT_PR138_ATOMICROWS_SEMANTIC_ROW_CONTRACT_INDEX"
CONTRACT_SCHEMA_ID = "qtt-local-schemas-atomicrows-semantic-row-contract-pr138"
CONTRACT_ID = "QTT_PR138_ATOMICROWS_SEMANTIC_ROW_CONTRACT"
INVENTORY_ID = "QTT_PR138_ATOMICROWS_SEMANTIC_FIELD_INVENTORY"
STATIC_TIME = "STATIC_DETERMINISTIC_NO_WALL_CLOCK"

REQUIRED_FIELD_GROUP_COUNT = 8
REQUIRED_FIELD_COUNT = 59
EXPECTED_ATOMICROWS_ROW_COUNT = 4183
CURRENT_BUNDLE_BASIC_SCHEMA_VALIDATION_STATUS_PASSED = "PASSED"
CURRENT_BUNDLE_BASIC_SCHEMA_VALIDATION_STATUS_UNKNOWN = "UNKNOWN_NOT_INVENTED"

SCHEMA_PATH = Path("schemas/atomicrows/atomicrows_semantic_row_contract.schema.json")
REPORT_PATH = Path(
    "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json"
)
INDEX_PATH = Path(
    "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.index.json"
)
INVENTORY_PATH = Path(
    "docs/master_plan/generated/PR138_AtomicRowsSemanticFieldInventory.json"
)
FIXTURE_PATH = Path(
    "tests/fixtures/atomicrows/pr138_semantic_row_contract/"
    "semantic_contract_fixtures.v1.fixture.json"
)
TEST_PATH = Path("tests/atomicrows/test_pr138_atomicrows_semantic_row_contract.py")
GATE_TOOL_PATH = "tools/stage1_atomicrows_semantic_row_contract_gate.py"

PR137R_REPORT_PATH = Path(
    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json"
)
PR137R_INDEX_PATH = Path(
    "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.index.json"
)
PR137L_REPORT_PATH = Path(
    "docs/master_plan/generated/PR137L_LatencyHotPathSnapshotBoundary.report.json"
)
PR137L_INDEX_PATH = Path(
    "docs/master_plan/generated/PR137L_LatencyHotPathSnapshotBoundary.index.json"
)
ATOMICROWS_BUNDLE_PATH = Path("docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl")

ROUTE_TRIAGE_ARTIFACTS = (
    "docs/master_plan/generated/PR136RouteTriage.report.json",
    "docs/roadmap/generated/CODEX_PR136_ROUTE_TRIAGE_RECEIPT.json",
    "docs/roadmap/generated/CODEX_PR137_ROUTE_TRIAGE_RECEIPT.json",
)
SECTION_CROSSWALK_ARTIFACTS = (
    "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/MasterPlanSectionCoverageReport.json",
    "docs/master_plan/generated/SectionManifest.json",
)
MARKET_INDEX_ARTIFACTS = (
    "docs/master_plan/generated/PR135MarketSpecificSectionIndex.report.json",
    "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
)
COMMAND_ACTION_MATRIX_ARTIFACTS = (
    "docs/master_plan/generated/PR135CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
    "docs/master_plan/generated/LocalGateCommandMatrix.json",
)
ROADMAP_SAFE_ARCHITECTURE_ARTIFACTS = (
    "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md",
    "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    "docs/master_plan/generated/PR136PostPR135RoadmapSequence.report.json",
    "docs/master_plan/generated/PR136LaunchReadinessDependencyGraph.report.json",
    "docs/master_plan/generated/PR136QuantumAtomicRowsOptimizationReadinessMap.report.json",
    "docs/master_plan/generated/PR137LaunchReadinessDependencyController.report.json",
)

ROW_FAMILY_SOURCE_GLOB = "docs/master_plan/atomic_rows/pr98_row_family_sources/*.source.jsonl"
EXACT_ROW_SOURCE_GLOB = "docs/master_plan/atomic_rows/exact_row_sources/*.exact_rows.jsonl"
BUNDLE_BUILDER_PATHS = (
    "tools/build_atomicrows_bundle.py",
    "tools/materialize_atomicrows_bundle_from_exact_rows.py",
)
PROTECTED_UNTOUCHED_PATHS = (
    "docs/master_plan/QTT_MasterPlan_Current.md",
    ATOMICROWS_BUNDLE_PATH.as_posix(),
    "docs/master_plan/atomic_rows/pr98_row_family_sources",
    "docs/master_plan/atomic_rows/exact_row_sources",
    *BUNDLE_BUILDER_PATHS,
)

PR138_CREATED_OR_UPDATED_PATHS = (
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_contract/__init__.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_contract/constants.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_contract/model.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_contract/schema.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_contract/report.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_contract/fixtures.py",
    "src/qtt/stage1_prediction_markets/atomicrows_semantic_contract/validator.py",
    GATE_TOOL_PATH,
    SCHEMA_PATH.as_posix(),
    REPORT_PATH.as_posix(),
    INDEX_PATH.as_posix(),
    INVENTORY_PATH.as_posix(),
    FIXTURE_PATH.as_posix(),
    TEST_PATH.as_posix(),
    "tests/fail_closed/test_run_validation_gates.py",
    "tools/run_validation_gates.py",
)

CANONICAL_STAGE1_MARKET_SCOPES = (
    "PREDICTION_MARKETS_GENERAL",
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
)
CANONICAL_THIRD_VENUE = "FORECASTEX_IBKR"
FORBIDDEN_ALIASES = (
    "FORECASTEX",
    "FORECASTX",
    "IBKR_FORECASTX",
    "forecastx",
)

ALLOWED_PLACEHOLDER_STATES = (
    "UNKNOWN_PENDING_PR139_ENRICHMENT",
    "NOT_APPLICABLE",
    "STATIC_METADATA_ONLY",
    "FUTURE_ACCEPTED_SOURCE_PACKET_REQUIRED",
    "FUTURE_OWNER_REVIEW_REQUIRED",
    "FUTURE_REPLAY_PAPER_REQUIRED",
    "FUTURE_PR141_MATERIALIZATION_REQUIRED",
    "FUTURE_PR142_FINAL_READINESS_GATE_REQUIRED",
    "BLOCKED_PENDING_SEMANTIC_CONTRACT_ENRICHMENT",
    "BLOCKED_PENDING_ROUTE_CROSSWALK_TRACE",
    "BLOCKED_PENDING_MARKET_INDEX_TRACE",
    "BLOCKED_PENDING_COMMAND_ACTION_MATRIX_TRACE",
)
FIXTURE_POLARITY_VALUES = ("VALID_POSITIVE", "INVALID_NEGATIVE_EXPECTED_FAIL")
FUTURE_PR_PHASE_VALUES = ("PR139", "PR140", "PR141", "PR142")
NEXT_REQUIRED_PRS = ["PR139", "PR140", "PR141", "PR142"]

FIELD_GROUPS = (
    {
        "field_group_id": "IDENTITY",
        "field_group_ordinal": 1,
        "title": "Identity",
        "fields": (
            "row_id",
            "row_family",
            "row_type",
            "lifecycle_state",
            "version_state",
            "deprecation_state",
        ),
    },
    {
        "field_group_id": "PARAMETER_ALGORITHM_CLASSIFICATION",
        "field_group_ordinal": 2,
        "title": "Parameter / algorithm classification",
        "fields": (
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
        ),
    },
    {
        "field_group_id": "AGENT_CONSUMER_BINDING",
        "field_group_ordinal": 3,
        "title": "Agent and consumer binding",
        "fields": (
            "agent_role",
            "consumer_class",
            "allowed_consumers",
            "blocked_consumers",
            "command_matrix_binding",
        ),
    },
    {
        "field_group_id": "MARKET_VENUE_SCOPE",
        "field_group_ordinal": 4,
        "title": "Market and venue scope",
        "fields": (
            "market_scope",
            "venue_scope",
            "prediction_market_scope",
            "prediction_markets_general_compatibility",
            "kalshi_compatibility",
            "polymarket_compatibility",
            "forecastex_ibkr_compatibility",
        ),
    },
    {
        "field_group_id": "TRADING_OBJECTIVE_SUPPORT",
        "field_group_ordinal": 5,
        "title": "Trading objective support",
        "fields": (
            "expected_net_profit_objective_family",
            "execution_cost_model_family",
            "latency_sensitivity_class",
            "capital_intensity_class",
            "risk_mode",
            "drawdown_control_family",
            "exposure_limit_family",
            "liquidity_context_family",
        ),
    },
    {
        "field_group_id": "REPLAY_PAPER_LIVE_BOUNDARY",
        "field_group_ordinal": 6,
        "title": "Replay / paper / live boundary",
        "fields": (
            "replay_required_flag",
            "paper_required_flag",
            "owner_review_required_flag",
            "live_use_allowed_flag",
            "order_authority_created_flag",
            "profit_evidence_created_flag",
        ),
    },
    {
        "field_group_id": "QUANTUM_COMPATIBILITY",
        "field_group_ordinal": 7,
        "title": "Quantum compatibility",
        "fields": (
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
        ),
    },
    {
        "field_group_id": "SOURCE_PROVENANCE_BOUNDARY",
        "field_group_ordinal": 8,
        "title": "Source / provenance boundary",
        "fields": (
            "source_evidence_required_flag",
            "accepted_source_packet_required_flag",
            "research_input_only_flag",
            "external_fact_authority_flag",
        ),
    },
)

REQUIRED_FIELD_GROUP_IDS = tuple(group["field_group_id"] for group in FIELD_GROUPS)
REQUIRED_FIELD_IDS = tuple(
    field for group in FIELD_GROUPS for field in group["fields"]
)
REQUIRED_FIELDS_BY_GROUP = tuple(
    (group["field_group_id"], tuple(group["fields"])) for group in FIELD_GROUPS
)

VALUE_KIND_STRING_ID = "STRING_ID"
VALUE_KIND_ENUM_OR_STRING_ID = "ENUM_OR_STRING_ID_BY_REPO_CONVENTION"
VALUE_KIND_ENUM_OR_LIST = "ENUM_OR_LIST_OF_ENUM_BY_REPO_CONVENTION"
VALUE_KIND_LIST = "LIST_OF_STRING_ID_OR_ENUM_BY_REPO_CONVENTION"
VALUE_KIND_STRING_OR_STRUCT = "STRING_ID_OR_STRUCT_REF_BY_REPO_CONVENTION"
VALUE_KIND_BOOLEAN = "BOOLEAN"

VALUE_KIND_BY_FIELD = {
    "row_id": VALUE_KIND_STRING_ID,
    "allowed_consumers": VALUE_KIND_LIST,
    "blocked_consumers": VALUE_KIND_LIST,
    "command_matrix_binding": VALUE_KIND_STRING_OR_STRUCT,
    **{
        field: VALUE_KIND_ENUM_OR_STRING_ID
        for field in (
            "row_family",
            "row_type",
            "lifecycle_state",
            "version_state",
            "deprecation_state",
            "agent_role",
            "consumer_class",
            "latency_sensitivity_class",
            "capital_intensity_class",
            "risk_mode",
            "quantum_applicability_class",
        )
    },
}
for _field in REQUIRED_FIELD_IDS:
    if _field.endswith("_flag") or _field.endswith("_compatibility"):
        VALUE_KIND_BY_FIELD[_field] = VALUE_KIND_BOOLEAN
    elif _field.endswith("_family") or _field.endswith("_scope"):
        VALUE_KIND_BY_FIELD.setdefault(_field, VALUE_KIND_ENUM_OR_LIST)
    else:
        VALUE_KIND_BY_FIELD.setdefault(_field, VALUE_KIND_ENUM_OR_STRING_ID)
del _field

FIELD_GROUP_SECTION_TRACE = {
    "IDENTITY": "0X.5F",
    "PARAMETER_ALGORITHM_CLASSIFICATION": "0X.4K",
    "AGENT_CONSUMER_BINDING": "0X.5L",
    "MARKET_VENUE_SCOPE": "Roadmap",
    "TRADING_OBJECTIVE_SUPPORT": "0X.4Z",
    "REPLAY_PAPER_LIVE_BOUNDARY": "0X.4T",
    "QUANTUM_COMPATIBILITY": "8.1C",
    "SOURCE_PROVENANCE_BOUNDARY": "0X.4Q",
}
FIELD_GROUP_FUTURE_PHASE = {
    "IDENTITY": "PR141",
    "PARAMETER_ALGORITHM_CLASSIFICATION": "PR139",
    "AGENT_CONSUMER_BINDING": "PR139",
    "MARKET_VENUE_SCOPE": "PR139",
    "TRADING_OBJECTIVE_SUPPORT": "PR139",
    "REPLAY_PAPER_LIVE_BOUNDARY": "PR142",
    "QUANTUM_COMPATIBILITY": "PR139",
    "SOURCE_PROVENANCE_BOUNDARY": "PR139",
}

AUTHORITY_BOUNDARY = (
    "STATIC_SEMANTIC_CONTRACT_ONLY_NOT_ROW_VALUE_NOT_RUNTIME_NOT_LIVE_NOT_ORDER"
)
PRECOMPUTED_SNAPSHOT_COMPATIBILITY_CLASS = (
    "STATIC_METADATA_COMPATIBLE_WITH_FUTURE_PRECOMPUTED_SNAPSHOT"
)

CONTRACT_DEFAULT_FALSE_FLAG_FIELDS = (
    "live_use_allowed_flag",
    "order_authority_created_flag",
    "profit_evidence_created_flag",
    "quantum_backend_execution_allowed_flag",
    "external_fact_authority_flag",
)

HOT_PATH_FORBIDDEN_DEPENDENCIES = (
    "source_retrieval",
    "source_acceptance",
    "source_revalidation",
    "connector_semantic_binding",
    "runtime_resolver_snapshot_creation",
    "private_state_first_fetch",
    "cash_component_map_construction",
    "dashboard_rendering",
    "telegram_runtime_calls",
    "llm_calls",
    "replay_execution",
    "paper_execution",
    "quantum_backend_calls",
    "quantum_simulator_calls",
    "atomicrows_materialization",
    "network_io",
    "file_system_document_fetch",
    "unbounded_search",
)

PR138_REASON_SEMANTIC_CONTRACT_ONLY = "PR138_REASON_SEMANTIC_CONTRACT_ONLY"
PR138_REASON_BUNDLE_MUTATION_FORBIDDEN = (
    "PR138_REASON_BUNDLE_MUTATION_FORBIDDEN"
)
PR138_REASON_ROW_FAMILY_SOURCE_MUTATION_FORBIDDEN = (
    "PR138_REASON_ROW_FAMILY_SOURCE_MUTATION_FORBIDDEN"
)
PR138_REASON_BUILDER_MUTATION_FORBIDDEN = (
    "PR138_REASON_BUILDER_MUTATION_FORBIDDEN"
)
PR138_REASON_FINAL_READINESS_NOT_CREATED = (
    "PR138_REASON_FINAL_READINESS_NOT_CREATED"
)
PR138_REASON_DAY1_LIVE_READINESS_NOT_CREATED = (
    "PR138_REASON_DAY1_LIVE_READINESS_NOT_CREATED"
)
PR138_REASON_ORDER_AUTHORITY_FORBIDDEN = (
    "PR138_REASON_ORDER_AUTHORITY_FORBIDDEN"
)
PR138_REASON_PROFIT_EVIDENCE_FORBIDDEN = (
    "PR138_REASON_PROFIT_EVIDENCE_FORBIDDEN"
)
PR138_REASON_SOURCE_RETRIEVAL_FORBIDDEN = (
    "PR138_REASON_SOURCE_RETRIEVAL_FORBIDDEN"
)
PR138_REASON_SOURCE_ACCEPTANCE_FORBIDDEN = (
    "PR138_REASON_SOURCE_ACCEPTANCE_FORBIDDEN"
)
PR138_REASON_CONNECTOR_SEMANTIC_BINDING_FORBIDDEN = (
    "PR138_REASON_CONNECTOR_SEMANTIC_BINDING_FORBIDDEN"
)
PR138_REASON_RUNTIME_CASH_AUTHORITY_FORBIDDEN = (
    "PR138_REASON_RUNTIME_CASH_AUTHORITY_FORBIDDEN"
)
PR138_REASON_REPLAY_EXECUTION_FORBIDDEN = (
    "PR138_REASON_REPLAY_EXECUTION_FORBIDDEN"
)
PR138_REASON_PAPER_EXECUTION_FORBIDDEN = (
    "PR138_REASON_PAPER_EXECUTION_FORBIDDEN"
)
PR138_REASON_SCORING_RANKING_ARBITRATION_FORBIDDEN = (
    "PR138_REASON_SCORING_RANKING_ARBITRATION_FORBIDDEN"
)
PR138_REASON_TRADING_SIGNAL_FORBIDDEN = (
    "PR138_REASON_TRADING_SIGNAL_FORBIDDEN"
)
PR138_REASON_QUANTUM_EXECUTION_FORBIDDEN = (
    "PR138_REASON_QUANTUM_EXECUTION_FORBIDDEN"
)
PR138_REASON_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN = (
    "PR138_REASON_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN"
)
PR138_REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN = (
    "PR138_REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN"
)
PR138_REASON_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN = (
    "PR138_REASON_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN"
)
PR138_REASON_FORBIDDEN_VENUE_ALIAS = (
    "PR138_REASON_FORBIDDEN_VENUE_ALIAS"
)
PR138_REASON_REQUIRED_FIELD_MISSING = (
    "PR138_REASON_REQUIRED_FIELD_MISSING"
)
PR138_REASON_REQUIRED_FIELD_GROUP_MISSING = (
    "PR138_REASON_REQUIRED_FIELD_GROUP_MISSING"
)
PR138_REASON_FIELD_GROUP_DUPLICATE = (
    "PR138_REASON_FIELD_GROUP_DUPLICATE"
)
PR138_REASON_FIELD_DUPLICATE = "PR138_REASON_FIELD_DUPLICATE"
PR138_REASON_FIELD_WITHOUT_AUTHORITY_BOUNDARY = (
    "PR138_REASON_FIELD_WITHOUT_AUTHORITY_BOUNDARY"
)
PR138_REASON_FIELD_WITHOUT_CROSSWALK_TRACE = (
    "PR138_REASON_FIELD_WITHOUT_CROSSWALK_TRACE"
)
PR138_REASON_FIELD_WITHOUT_MARKET_INDEX_TRACE = (
    "PR138_REASON_FIELD_WITHOUT_MARKET_INDEX_TRACE"
)
PR138_REASON_FIELD_WITHOUT_COMMAND_MATRIX_TRACE = (
    "PR138_REASON_FIELD_WITHOUT_COMMAND_MATRIX_TRACE"
)
PR138_REASON_LIVE_USE_FLAG_TRUE_FORBIDDEN = (
    "PR138_REASON_LIVE_USE_FLAG_TRUE_FORBIDDEN"
)
PR138_REASON_ORDER_AUTHORITY_FLAG_TRUE_FORBIDDEN = (
    "PR138_REASON_ORDER_AUTHORITY_FLAG_TRUE_FORBIDDEN"
)
PR138_REASON_PROFIT_EVIDENCE_FLAG_TRUE_FORBIDDEN = (
    "PR138_REASON_PROFIT_EVIDENCE_FLAG_TRUE_FORBIDDEN"
)
PR138_REASON_QUANTUM_BACKEND_EXECUTION_FLAG_TRUE_FORBIDDEN = (
    "PR138_REASON_QUANTUM_BACKEND_EXECUTION_FLAG_TRUE_FORBIDDEN"
)
PR138_REASON_EXTERNAL_FACT_AUTHORITY_TRUE_FORBIDDEN_WITHOUT_ACCEPTED_SOURCE_PACKET = (
    "PR138_REASON_EXTERNAL_FACT_AUTHORITY_TRUE_FORBIDDEN_WITHOUT_ACCEPTED_SOURCE_PACKET"
)
PR138_REASON_PR137R_EVIDENCE_MISSING = (
    "PR138_REASON_PR137R_EVIDENCE_MISSING"
)
PR138_REASON_PR137L_EVIDENCE_MISSING = (
    "PR138_REASON_PR137L_EVIDENCE_MISSING"
)
PR138_REASON_ROUTE_TRIAGE_EVIDENCE_MISSING = (
    "PR138_REASON_ROUTE_TRIAGE_EVIDENCE_MISSING"
)
PR138_REASON_SECTION_CROSSWALK_EVIDENCE_MISSING = (
    "PR138_REASON_SECTION_CROSSWALK_EVIDENCE_MISSING"
)
PR138_REASON_MARKET_INDEX_EVIDENCE_MISSING = (
    "PR138_REASON_MARKET_INDEX_EVIDENCE_MISSING"
)
PR138_REASON_COMMAND_ACTION_MATRIX_EVIDENCE_MISSING = (
    "PR138_REASON_COMMAND_ACTION_MATRIX_EVIDENCE_MISSING"
)
PR138_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY = (
    "PR138_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY"
)
PR138_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY = (
    "PR138_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY"
)
PR138_REASON_LOCAL_BASELINE_NOT_DESCENDANT = (
    "PR138_REASON_LOCAL_BASELINE_NOT_DESCENDANT"
)
PR138_REASON_NEW_ATOMICROWS_BUNDLE_SHA_SIDECAR_REFERENCE_FORBIDDEN = (
    "PR138_REASON_NEW_ATOMICROWS_BUNDLE_SHA_SIDECAR_REFERENCE_FORBIDDEN"
)
PR138_REASON_QTT_GENERATED_CRYPTOGRAPHIC_AUTHORITY_FORBIDDEN = (
    "PR138_REASON_QTT_GENERATED_CRYPTOGRAPHIC_AUTHORITY_FORBIDDEN"
)
PR138_REASON_MASTER_PLAN_EDIT_FORBIDDEN = (
    "PR138_REASON_MASTER_PLAN_EDIT_FORBIDDEN"
)
PR138_REASON_HOT_PATH_FORBIDDEN_DEPENDENCY = (
    "PR138_REASON_HOT_PATH_FORBIDDEN_DEPENDENCY"
)
PR138_REASON_SANDBOX_BOOTSTRAP_FALLBACK_USED = (
    "PR138_REASON_SANDBOX_BOOTSTRAP_FALLBACK_USED"
)
PR138_REASON_SANDBOX_EXECUTION_UNAVAILABLE = (
    "PR138_REASON_SANDBOX_EXECUTION_UNAVAILABLE"
)
PR138_REASON_IDEMPOTENCY_FAILURE = "PR138_REASON_IDEMPOTENCY_FAILURE"
PR138_REASON_BRANCH_MISMATCH = "PR138_REASON_BRANCH_MISMATCH"
PR138_REASON_DIRTY_WORKTREE_FORBIDDEN_BEFORE_EDITS = (
    "PR138_REASON_DIRTY_WORKTREE_FORBIDDEN_BEFORE_EDITS"
)
PR138_REASON_REPORT_CLAIM_FORBIDDEN = "PR138_REASON_REPORT_CLAIM_FORBIDDEN"
PR138_REASON_FUTURE_PHASE_MISSING = "PR138_REASON_FUTURE_PHASE_MISSING"
PR138_REASON_REASON_CODE_NOT_CENTRALIZED = (
    "PR138_REASON_REASON_CODE_NOT_CENTRALIZED"
)
PR138_REASON_OLDER_BASELINE_CHECKPOINT_REFERENCE_FORBIDDEN = (
    "PR138_REASON_OLDER_BASELINE_CHECKPOINT_REFERENCE_FORBIDDEN"
)

REASON_CODES = (
    PR138_REASON_SEMANTIC_CONTRACT_ONLY,
    PR138_REASON_BUNDLE_MUTATION_FORBIDDEN,
    PR138_REASON_ROW_FAMILY_SOURCE_MUTATION_FORBIDDEN,
    PR138_REASON_BUILDER_MUTATION_FORBIDDEN,
    PR138_REASON_FINAL_READINESS_NOT_CREATED,
    PR138_REASON_DAY1_LIVE_READINESS_NOT_CREATED,
    PR138_REASON_ORDER_AUTHORITY_FORBIDDEN,
    PR138_REASON_PROFIT_EVIDENCE_FORBIDDEN,
    PR138_REASON_SOURCE_RETRIEVAL_FORBIDDEN,
    PR138_REASON_SOURCE_ACCEPTANCE_FORBIDDEN,
    PR138_REASON_CONNECTOR_SEMANTIC_BINDING_FORBIDDEN,
    PR138_REASON_RUNTIME_CASH_AUTHORITY_FORBIDDEN,
    PR138_REASON_REPLAY_EXECUTION_FORBIDDEN,
    PR138_REASON_PAPER_EXECUTION_FORBIDDEN,
    PR138_REASON_SCORING_RANKING_ARBITRATION_FORBIDDEN,
    PR138_REASON_TRADING_SIGNAL_FORBIDDEN,
    PR138_REASON_QUANTUM_EXECUTION_FORBIDDEN,
    PR138_REASON_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN,
    PR138_REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN,
    PR138_REASON_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN,
    PR138_REASON_FORBIDDEN_VENUE_ALIAS,
    PR138_REASON_REQUIRED_FIELD_MISSING,
    PR138_REASON_REQUIRED_FIELD_GROUP_MISSING,
    PR138_REASON_FIELD_GROUP_DUPLICATE,
    PR138_REASON_FIELD_DUPLICATE,
    PR138_REASON_FIELD_WITHOUT_AUTHORITY_BOUNDARY,
    PR138_REASON_FIELD_WITHOUT_CROSSWALK_TRACE,
    PR138_REASON_FIELD_WITHOUT_MARKET_INDEX_TRACE,
    PR138_REASON_FIELD_WITHOUT_COMMAND_MATRIX_TRACE,
    PR138_REASON_LIVE_USE_FLAG_TRUE_FORBIDDEN,
    PR138_REASON_ORDER_AUTHORITY_FLAG_TRUE_FORBIDDEN,
    PR138_REASON_PROFIT_EVIDENCE_FLAG_TRUE_FORBIDDEN,
    PR138_REASON_QUANTUM_BACKEND_EXECUTION_FLAG_TRUE_FORBIDDEN,
    PR138_REASON_EXTERNAL_FACT_AUTHORITY_TRUE_FORBIDDEN_WITHOUT_ACCEPTED_SOURCE_PACKET,
    PR138_REASON_PR137R_EVIDENCE_MISSING,
    PR138_REASON_PR137L_EVIDENCE_MISSING,
    PR138_REASON_ROUTE_TRIAGE_EVIDENCE_MISSING,
    PR138_REASON_SECTION_CROSSWALK_EVIDENCE_MISSING,
    PR138_REASON_MARKET_INDEX_EVIDENCE_MISSING,
    PR138_REASON_COMMAND_ACTION_MATRIX_EVIDENCE_MISSING,
    PR138_REASON_CI_DETACHED_HEAD_RELAXATION_BRANCH_ONLY,
    PR138_REASON_CI_MAIN_PUSH_RELAXATION_BRANCH_AND_ANCESTRY,
    PR138_REASON_LOCAL_BASELINE_NOT_DESCENDANT,
    PR138_REASON_NEW_ATOMICROWS_BUNDLE_SHA_SIDECAR_REFERENCE_FORBIDDEN,
    PR138_REASON_QTT_GENERATED_CRYPTOGRAPHIC_AUTHORITY_FORBIDDEN,
    PR138_REASON_MASTER_PLAN_EDIT_FORBIDDEN,
    PR138_REASON_HOT_PATH_FORBIDDEN_DEPENDENCY,
    PR138_REASON_SANDBOX_BOOTSTRAP_FALLBACK_USED,
    PR138_REASON_SANDBOX_EXECUTION_UNAVAILABLE,
    PR138_REASON_IDEMPOTENCY_FAILURE,
    PR138_REASON_BRANCH_MISMATCH,
    PR138_REASON_DIRTY_WORKTREE_FORBIDDEN_BEFORE_EDITS,
    PR138_REASON_REPORT_CLAIM_FORBIDDEN,
    PR138_REASON_FUTURE_PHASE_MISSING,
    PR138_REASON_REASON_CODE_NOT_CENTRALIZED,
    PR138_REASON_OLDER_BASELINE_CHECKPOINT_REFERENCE_FORBIDDEN,
)

FIELD_DEFAULT_REASON_CODES = (
    PR138_REASON_SEMANTIC_CONTRACT_ONLY,
    PR138_REASON_FINAL_READINESS_NOT_CREATED,
    PR138_REASON_DAY1_LIVE_READINESS_NOT_CREATED,
)

REPORT_NO_CLAIM_FLAG_NAMES = (
    "atomicrows_bundle_mutated_by_pr138",
    "row_family_sources_mutated_by_pr138",
    "bundle_builder_mutated_by_pr138",
    "final_readiness_gate_created_by_pr138",
    "final_readiness_claimed_by_pr138",
    "day1_live_readiness_claimed_by_pr138",
    "live_order_authority_created_by_pr138",
    "order_execution_created_by_pr138",
    "profit_evidence_created_by_pr138",
    "latency_superiority_claimed_by_pr138",
    "execution_superiority_claimed_by_pr138",
    "quantum_execution_created_by_pr138",
    "quantum_simulator_execution_created_by_pr138",
    "quantum_optimizer_input_created_by_pr138",
    "quantum_optimizer_output_created_by_pr138",
    "quantum_advantage_claimed_by_pr138",
    "source_retrieval_created_by_pr138",
    "source_acceptance_created_by_pr138",
    "connector_semantic_binding_created_by_pr138",
    "runtime_cash_authority_created_by_pr138",
    "replay_execution_created_by_pr138",
    "paper_execution_created_by_pr138",
    "scoring_ranking_arbitration_output_created_by_pr138",
    "trading_signal_created_by_pr138",
    "qtt_cryptographic_authority_created_by_pr138",
)

SUCCESS_RECEIPTS = (
    "QTT_PR138_ATOMICROWS_SEMANTIC_ROW_CONTRACT_OK",
    "QTT_PR138_EXACT_8_GROUPS_59_FIELDS_OK",
    "QTT_PR138_PR137R_PR137L_STATIC_EVIDENCE_CONSUMED_OK",
    "QTT_PR138_ROUTE_CROSSWALK_MARKET_INDEX_COMMAND_MATRIX_CONSUMED_OK",
    "QTT_PR138_NO_ATOMICROWS_BUNDLE_OR_ROW_FAMILY_MUTATION_OK",
    "QTT_PR138_NO_RUNTIME_LIVE_ORDER_PROFIT_QUANTUM_AUTHORITY_OK",
    "QTT_PR138_FORECASTEX_IBKR_CANONICAL_SCOPE_OK",
    "QTT_PR138_PRECOMPUTED_HOT_PATH_COMPATIBILITY_METADATA_ONLY_OK",
)
