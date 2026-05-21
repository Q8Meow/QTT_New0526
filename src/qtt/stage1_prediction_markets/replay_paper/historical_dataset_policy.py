"""Central PR135 historical dataset digest and loader policy constants."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VALIDATOR_MARKER = "QTT_HISTORICAL_DATASET_DIGEST_AND_LOADER_OK"

PRODUCER_REPO_PR = 135
PRODUCER_ROADMAP_PR = 117
PREVIOUS_REPO_PR = 134
PREVIOUS_ROADMAP_PR = 116
SCHEMA_VERSION = "PR135_HISTORICAL_DATASET_DIGEST_AND_LOADER_SCHEMA_V1"
REPORT_SCHEMA_VERSION = "PR135_HISTORICAL_DATASET_DIGEST_AND_LOADER_REPORT_V1"
CREATED_BY = "CODEX_PR135_FIXTURE_OR_VALIDATOR"
FIXTURE_TIMESTAMP = "2026-05-21T00:00:00Z"

POLICY_MODULE_PATH = (
    "src/qtt/stage1_prediction_markets/replay_paper/historical_dataset_policy.py"
)
POLICY_SCHEMA_DEFS_PATH = "schemas/replay_paper/historical_dataset_policy.defs.schema.json"
POLICY_MANIFEST_PATH = (
    "docs/master_plan/generated/PR135HistoricalDatasetPolicyManifest.report.json"
)

CANONICAL_VENUE_IDS = (
    "PREDICTION_MARKETS_GENERAL",
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
)
VENUE_SPECIFIC_IDS = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
SHARED_SCOPE_IDS = ("PREDICTION_MARKETS_GENERAL",)
FORBIDDEN_VENUE_IDENTITIES = ("FORECASTEX", "FORECASTX", "IBKR_FORECASTX", "forecastx")

DATASET_RECORD_SCOPES = (
    "FIXTURE_ONLY",
    "CONTRACT_METADATA_ONLY",
    "SOURCE_GATED_REFERENCE_ONLY",
)
DIGEST_ALGORITHMS = ("SHA256",)
LOADER_MANIFEST_MODES = ("FIXTURE_MANIFEST_ONLY", "CONTRACT_DECLARATION_ONLY")

INPUT_LOCK_STATES = (
    "LOCKED_FIXTURE_INPUT",
    "BLOCKED_MISSING_RUNTIME_RESOLVER_HANDOFF",
    "BLOCKED_MISSING_CANDIDATE_SET_SNAPSHOT_LOCK",
    "BLOCKED_MISSING_REPLAY_PAPER_INPUT_IDENTITY",
    "BLOCKED_MISSING_SOURCE_LINEAGE",
    "BLOCKED_MUTABLE_DATASET",
    "BLOCKED_LIVE_DATA_ATTEMPT",
    "BLOCKED_SOURCE_ACCEPTANCE_ATTEMPT",
    "BLOCKED_REPLAY_EXECUTION_ATTEMPT",
    "BLOCKED_PAPER_EXECUTION_ATTEMPT",
    "BLOCKED_FEATURE_VECTOR_ATTEMPT",
    "BLOCKED_TRADING_SIGNAL_ATTEMPT",
    "BLOCKED_RANKING_SCORING_ARBITRATION_ATTEMPT",
    "BLOCKED_ORDER_AUTHORITY_ATTEMPT",
    "BLOCKED_RUNTIME_CASH_AUTHORITY_ATTEMPT",
    "BLOCKED_PROFIT_EVIDENCE_ATTEMPT",
    "BLOCKED_QUANTUM_EXECUTION_ATTEMPT",
    "BLOCKED_QUANTUM_OPTIMIZER_INPUT_ATTEMPT",
    "BLOCKED_QUANTUM_ADVANTAGE_CLAIM_ATTEMPT",
    "BLOCKED_ATOMICROWS_MATERIALIZATION_ATTEMPT",
    "BLOCKED_NONCANONICAL_FORECASTEX_IBKR_IDENTITY",
    "BLOCKED_GLOBAL_PERMANENT_CANDIDATE_FREEZE_LANGUAGE",
    "BLOCKED_SAME_NUMBER_ROADMAP_INFERENCE",
    "BLOCKED_MISSING_PR134_CURRENTIZATION",
    "BLOCKED_POLICY_LITERAL_DRIFT",
    "BLOCKED_UNAUTHORIZED_MASTER_PLAN_EDIT",
    "BLOCKED_ATOMICROWS_BUNDLE_OR_SHA_DIFF",
    "BLOCKED_PLACEHOLDER_OWNER_VERIFIED_INPUT",
    "BLOCKED_SOURCE_FACT_RETRIEVAL_OR_ACCEPTANCE",
    "BLOCKED_CONNECTOR_SEMANTIC_BINDING",
)

BLOCKED_SOURCE_RETRIEVAL_ATTEMPT = "BLOCKED_SOURCE_FACT_RETRIEVAL_OR_ACCEPTANCE"
BLOCKED_CONNECTOR_BINDING_ATTEMPT = "BLOCKED_CONNECTOR_SEMANTIC_BINDING"
LOCKED_FIXTURE_INPUT = "LOCKED_FIXTURE_INPUT"
BLOCKED_MISSING_RUNTIME_RESOLVER_HANDOFF = "BLOCKED_MISSING_RUNTIME_RESOLVER_HANDOFF"
BLOCKED_MISSING_CANDIDATE_SET_SNAPSHOT_LOCK = (
    "BLOCKED_MISSING_CANDIDATE_SET_SNAPSHOT_LOCK"
)
BLOCKED_MISSING_REPLAY_PAPER_INPUT_IDENTITY = (
    "BLOCKED_MISSING_REPLAY_PAPER_INPUT_IDENTITY"
)
BLOCKED_MISSING_SOURCE_LINEAGE = "BLOCKED_MISSING_SOURCE_LINEAGE"
BLOCKED_MUTABLE_DATASET = "BLOCKED_MUTABLE_DATASET"
BLOCKED_LIVE_DATA_ATTEMPT = "BLOCKED_LIVE_DATA_ATTEMPT"
BLOCKED_SOURCE_ACCEPTANCE_ATTEMPT = "BLOCKED_SOURCE_ACCEPTANCE_ATTEMPT"
BLOCKED_REPLAY_EXECUTION_ATTEMPT = "BLOCKED_REPLAY_EXECUTION_ATTEMPT"
BLOCKED_PAPER_EXECUTION_ATTEMPT = "BLOCKED_PAPER_EXECUTION_ATTEMPT"
BLOCKED_FEATURE_VECTOR_ATTEMPT = "BLOCKED_FEATURE_VECTOR_ATTEMPT"
BLOCKED_TRADING_SIGNAL_ATTEMPT = "BLOCKED_TRADING_SIGNAL_ATTEMPT"
BLOCKED_RANKING_SCORING_ARBITRATION_ATTEMPT = (
    "BLOCKED_RANKING_SCORING_ARBITRATION_ATTEMPT"
)
BLOCKED_ORDER_AUTHORITY_ATTEMPT = "BLOCKED_ORDER_AUTHORITY_ATTEMPT"
BLOCKED_RUNTIME_CASH_AUTHORITY_ATTEMPT = "BLOCKED_RUNTIME_CASH_AUTHORITY_ATTEMPT"
BLOCKED_PROFIT_EVIDENCE_ATTEMPT = "BLOCKED_PROFIT_EVIDENCE_ATTEMPT"
BLOCKED_QUANTUM_EXECUTION_ATTEMPT = "BLOCKED_QUANTUM_EXECUTION_ATTEMPT"
BLOCKED_QUANTUM_OPTIMIZER_INPUT_ATTEMPT = "BLOCKED_QUANTUM_OPTIMIZER_INPUT_ATTEMPT"
BLOCKED_QUANTUM_ADVANTAGE_CLAIM_ATTEMPT = "BLOCKED_QUANTUM_ADVANTAGE_CLAIM_ATTEMPT"
BLOCKED_ATOMICROWS_MATERIALIZATION_ATTEMPT = "BLOCKED_ATOMICROWS_MATERIALIZATION_ATTEMPT"
BLOCKED_NONCANONICAL_FORECASTEX_IBKR_IDENTITY = (
    "BLOCKED_NONCANONICAL_FORECASTEX_IBKR_IDENTITY"
)
BLOCKED_GLOBAL_PERMANENT_CANDIDATE_FREEZE_LANGUAGE = (
    "BLOCKED_GLOBAL_PERMANENT_CANDIDATE_FREEZE_LANGUAGE"
)
BLOCKED_SAME_NUMBER_ROADMAP_INFERENCE = "BLOCKED_SAME_NUMBER_ROADMAP_INFERENCE"
BLOCKED_MISSING_PR134_CURRENTIZATION = "BLOCKED_MISSING_PR134_CURRENTIZATION"
BLOCKED_POLICY_LITERAL_DRIFT = "BLOCKED_POLICY_LITERAL_DRIFT"
BLOCKED_UNAUTHORIZED_MASTER_PLAN_EDIT = "BLOCKED_UNAUTHORIZED_MASTER_PLAN_EDIT"
BLOCKED_ATOMICROWS_BUNDLE_OR_SHA_DIFF = "BLOCKED_ATOMICROWS_BUNDLE_OR_SHA_DIFF"
BLOCKED_PLACEHOLDER_OWNER_VERIFIED_INPUT = "BLOCKED_PLACEHOLDER_OWNER_VERIFIED_INPUT"
BLOCKED_DUPLICATE_DATASET_DIGEST_ID = "BLOCKED_DUPLICATE_DATASET_DIGEST_ID"
BLOCKED_CREDENTIAL_RESOLUTION_ATTEMPT = "BLOCKED_CREDENTIAL_RESOLUTION_ATTEMPT"
BLOCKED_PRIVATE_STATE_FETCH_ATTEMPT = "BLOCKED_PRIVATE_STATE_FETCH_ATTEMPT"
BLOCKED_REPLAY_RESULT_ATTEMPT = "BLOCKED_REPLAY_RESULT_ATTEMPT"
BLOCKED_PAPER_RESULT_ATTEMPT = "BLOCKED_PAPER_RESULT_ATTEMPT"
BLOCKED_LATENCY_OR_EXECUTION_SUPERIORITY_CLAIM = (
    "BLOCKED_LATENCY_OR_EXECUTION_SUPERIORITY_CLAIM"
)
BLOCKED_ALPHA_EVIDENCE_ATTEMPT = "BLOCKED_ALPHA_EVIDENCE_ATTEMPT"
BLOCKED_MISSING_DATASET_DIGEST_ID = "BLOCKED_MISSING_DATASET_DIGEST_ID"
BLOCKED_MISSING_FIXTURE_ARTIFACTS = "BLOCKED_MISSING_FIXTURE_ARTIFACTS"
BLOCKED_MISSING_VALID_FIXTURE_CASE = "BLOCKED_MISSING_VALID_FIXTURE_CASE"
BLOCKED_MISSING_PR135_FIXTURE = "BLOCKED_MISSING_PR135_FIXTURE"
BLOCKED_MISSING_PR135_REPORT = "BLOCKED_MISSING_PR135_REPORT"
BLOCKED_MISSING_READ_INPUT = "BLOCKED_MISSING_READ_INPUT"
BLOCKED_NETWORK_OR_GITHUB_ACTION = "BLOCKED_NETWORK_OR_GITHUB_ACTION"

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
    "creates_feature_vector": False,
    "creates_trading_signal": False,
    "creates_ranking_scoring_arbitration": False,
    "creates_order_authority": False,
    "creates_order_execution": False,
    "creates_profit_evidence": False,
    "creates_latency_superiority_evidence": False,
    "creates_execution_superiority_evidence": False,
    "creates_alpha_evidence": False,
    "creates_quantum_execution": False,
    "creates_quantum_optimizer_input": False,
    "creates_quantum_trading_signal": False,
    "creates_quantum_advantage_claim": False,
    "creates_atomicrows_materialization": False,
}

RECORD_NO_AUTHORITY_FLAGS = {
    "live_data_used_flag": False,
    "source_retrieval_created_flag": False,
    "source_acceptance_created_flag": False,
    "connector_binding_created_flag": False,
    "credential_resolution_created_flag": False,
    "private_state_fetch_created_flag": False,
    "runtime_cash_authority_created_flag": False,
    "replay_execution_created_flag": False,
    "paper_execution_created_flag": False,
    "replay_result_created_flag": False,
    "paper_result_created_flag": False,
    "feature_vector_created_flag": False,
    "trading_signal_created_flag": False,
    "ranking_scoring_arbitration_created_flag": False,
    "order_authority_created_flag": False,
    "order_execution_created_flag": False,
    "profit_evidence_created_flag": False,
    "latency_superiority_evidence_created_flag": False,
    "execution_superiority_evidence_created_flag": False,
    "alpha_evidence_created_flag": False,
    "quantum_execution_created_flag": False,
    "quantum_optimizer_input_created_flag": False,
    "quantum_trading_signal_created_flag": False,
    "quantum_advantage_claim_created_flag": False,
    "atomicrows_materialization_created_flag": False,
}

SOURCE_BOUNDARY_CONSTANTS = (
    "SOURCE_REQUIRED_REFERENCE_ONLY",
    "ACCEPTED_SOURCE_PACKET_REQUIRED_FOR_REAL_HISTORICAL_AVAILABILITY",
    "OWNER_DEFINITIONS_PACKET_NOT_EXTERNAL_FACT_AUTHORITY",
    "FIXTURE_SHAPE_ONLY_NOT_VENUE_FACT_TRUTH",
)
SOURCE_REQUIRED_REFERENCE_ONLY = "SOURCE_REQUIRED_REFERENCE_ONLY"
ACCEPTED_SOURCE_PACKET_REQUIRED_FOR_REAL_HISTORICAL_AVAILABILITY = (
    "ACCEPTED_SOURCE_PACKET_REQUIRED_FOR_REAL_HISTORICAL_AVAILABILITY"
)
OWNER_DEFINITIONS_PACKET_NOT_EXTERNAL_FACT_AUTHORITY = (
    "OWNER_DEFINITIONS_PACKET_NOT_EXTERNAL_FACT_AUTHORITY"
)
FIXTURE_SHAPE_ONLY_NOT_VENUE_FACT_TRUTH = "FIXTURE_SHAPE_ONLY_NOT_VENUE_FACT_TRUTH"
SOURCE_BOUNDARY_LANGUAGE = (
    "fixture can test schema shape and deterministic digest behavior only, "
    "not venue fact truth."
)

CANDIDATE_SET_CONSTANTS = (
    "VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK",
    "FUTURE_CANDIDATE_ADDITIONS_ALLOWED_BY_NEW_SNAPSHOT_VERSIONS",
    "GLOBAL_PERMANENT_CANDIDATE_FREEZE_FORBIDDEN",
)
VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK = "VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK"
FUTURE_CANDIDATE_ADDITIONS_ALLOWED_BY_NEW_SNAPSHOT_VERSIONS = (
    "FUTURE_CANDIDATE_ADDITIONS_ALLOWED_BY_NEW_SNAPSHOT_VERSIONS"
)
GLOBAL_PERMANENT_CANDIDATE_FREEZE_FORBIDDEN = (
    "GLOBAL_PERMANENT_CANDIDATE_FREEZE_FORBIDDEN"
)

ALLOWED_FUTURE_CONSUMERS = (
    "PR118_REPLAY_ENGINE_EXECUTOR",
    "FUTURE_PAPER_ENGINE_AFTER_OWNER_AUTHORIZATION",
    "FUTURE_OPTIMIZER_PRECOMPUTE_AFTER_OWNER_AUTHORIZATION",
    "FUTURE_ATOMICROWS_BRIDGE_AFTER_OWNER_AUTHORIZATION",
)
FORBIDDEN_CONSUMERS = (
    "LIVE_ORDER_AUTHORITY",
    "RUNTIME_CASH_AUTHORITY",
    "DIRECT_SIGNAL_GENERATION",
    "QUANTUM_BACKEND_EXECUTION",
    "ATOMICROWS_BUNDLE_MATERIALIZATION",
)

REQUIRED_REPORTS = (
    "docs/master_plan/generated/PR135OwnerVerifiedInputs.report.json",
    "docs/master_plan/generated/PR135HistoricalDatasetPolicyManifest.report.json",
    "docs/master_plan/generated/PR135HistoricalDatasetDigestAndLoader.report.json",
    "docs/master_plan/generated/PR135RouteTriage.report.json",
    "docs/master_plan/generated/PR134GitHubAuditCurrentization.report.json",
    "docs/master_plan/generated/PR135HistoricalDatasetDigestAndLoaderReadReceipt.report.json",
    "docs/master_plan/generated/PR135RoadmapBlueprintExtraction.report.json",
    "docs/master_plan/generated/PR135MasterPlanSectionCrosswalk.report.json",
    "docs/master_plan/generated/PR135MarketSpecificSectionIndex.report.json",
    "docs/master_plan/generated/PR135CommandActionMatrix.report.json",
    "docs/master_plan/generated/PR135PathDecision.report.json",
    "docs/master_plan/generated/PR135PolicyLiteralDrift.report.json",
)

REQUIRED_ROADMAP_RECEIPTS = (
    "docs/roadmap/generated/CODEX_REPO_PR134_GITHUB_AUDIT_CURRENTIZATION_RECEIPT.json",
    "docs/roadmap/generated/CODEX_PR135_ROUTE_TRIAGE_RECEIPT.json",
    "docs/roadmap/generated/CODEX_PR135_MANDATORY_READ_RECEIPT.json",
)

PR134_OWNER_VERIFIED_FIELDS = {
    "repo_pr_number": 134,
    "roadmap_pr_number": 116,
    "repo_pr_title": "PR134 implement runtime resolver snapshot executor contracts",
    "head_branch_commit": "7db7f7f",
    "repo_pr_state": "MERGED",
    "baseRefName": "main",
    "headRefName": "pr134-runtime-resolver-snapshot-executor",
    "url": "https://github.com/Q8Meow/QTT_New0526/pull/134",
    "mergedAt": "2026-05-21T02:05:49Z",
    "mergeCommit_full": "6d18db0ccb1d4b3d27a9b1ee267b06a269c1c350",
    "mergeCommit_short": "6d18db0",
}

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

PRE_EDIT_REQUIRED_FILE_METADATA = {
    "docs/roadmap/README.md": {
        "bytes": 3818,
        "lines": 55,
        "sha256": "161C10DFE1F8A170B24C979164D706799B4532E6620D63C23E014672C860432E",
    },
    "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md": {
        "bytes": 126612,
        "lines": 1318,
        "sha256": "8D7D270E39BFF05198C09F1563A901CBE82B6C3FE5734034290C3585FDB8CB2E",
    },
    "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json": {
        "bytes": 113997,
        "lines": 1625,
        "sha256": "47B99ACBAAFE13FC082759731EEFB09BAF29FAEC084A1F699E41820B37AE8067",
    },
    "docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md": {
        "bytes": 1277334,
        "lines": 19651,
        "sha256": "6C0DD350014851DAE8BEA4EB8EBE74FDFA3C7B991BA2E0EBCC285A55B0D846E6",
    },
    "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json": {
        "bytes": 632000,
        "lines": 9686,
        "sha256": "CE55E09C4DA597DE46364D1B820A251E453CF10587E162309AF8A2B86A3FCDDD",
    },
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json": {
        "bytes": 123377,
        "lines": 2626,
        "sha256": "9A346736DF5C3F42B96EFCE450BF224A2752BA6BAA19DF43D07BEDF303E57027",
    },
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json": {
        "bytes": 26945,
        "lines": 467,
        "sha256": "8DBA0BE9EE2E0D75786784A831BAEA41F44803693EF824557C8B342241D5723B",
    },
    "docs/master_plan/QTT_MasterPlan_Current.md": {
        "bytes": 10855077,
        "lines": 146398,
        "sha256": "1588C6A2D045605A25967E3568CFA353F64938423A41685BA6AAABCE0E2A8F2B",
    },
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md": {
        "bytes": 15747,
        "lines": 252,
        "sha256": "24E9325D45BFCAC3AD872A591860160E7D999D5DE143B913E70CF9EEEF7FFCA7",
    },
}

REPO_CONVENTION_FILES_INSPECTED = (
    "git ls-files",
    "git ls-files schemas",
    "git ls-files src/qtt",
    "git ls-files tools",
    "git ls-files tests",
    "git ls-files docs/master_plan/generated",
    "git ls-files docs/roadmap",
)

MASTER_PLAN_ANCHORS_INSPECTED = (
    "concurrent replay and paper",
    "shared input lock",
    "result immutability",
    "dual-result review",
    "Historical dataset digest and loader",
    VALIDATOR_MARKER,
    "Stage 1 prediction markets",
    "Kalshi",
    "Polymarket",
    "FORECASTEX_IBKR",
    "versioned candidate-set snapshot-lock",
    "replay/paper input identity",
    "AtomicRows pre-bridge compatibility",
    "quantum state encoding",
    "quantum optimizer",
    "source evidence owner definitions packet",
)

REQUIRED_FIXTURE_CASE_BLOCKS = {
    "missing_runtime_resolver_handoff_ref": BLOCKED_MISSING_RUNTIME_RESOLVER_HANDOFF,
    "missing_versioned_candidate_set_snapshot_lock_ref": (
        BLOCKED_MISSING_CANDIDATE_SET_SNAPSHOT_LOCK
    ),
    "missing_replay_paper_input_identity_ref": (
        BLOCKED_MISSING_REPLAY_PAPER_INPUT_IDENTITY
    ),
    "missing_source_lineage_ref": BLOCKED_MISSING_SOURCE_LINEAGE,
    "duplicate_dataset_digest_id": BLOCKED_DUPLICATE_DATASET_DIGEST_ID,
    "mutable_dataset_flag_true": BLOCKED_MUTABLE_DATASET,
    "live_data_used_flag_true": BLOCKED_LIVE_DATA_ATTEMPT,
    "source_retrieval_created_flag_true": BLOCKED_SOURCE_RETRIEVAL_ATTEMPT,
    "source_acceptance_created_flag_true": BLOCKED_SOURCE_ACCEPTANCE_ATTEMPT,
    "connector_binding_created_flag_true": BLOCKED_CONNECTOR_BINDING_ATTEMPT,
    "credential_resolution_created_flag_true": BLOCKED_CREDENTIAL_RESOLUTION_ATTEMPT,
    "private_state_fetch_created_flag_true": BLOCKED_PRIVATE_STATE_FETCH_ATTEMPT,
    "runtime_cash_authority_created_flag_true": BLOCKED_RUNTIME_CASH_AUTHORITY_ATTEMPT,
    "replay_execution_created_flag_true": BLOCKED_REPLAY_EXECUTION_ATTEMPT,
    "paper_execution_created_flag_true": BLOCKED_PAPER_EXECUTION_ATTEMPT,
    "replay_result_created_flag_true": BLOCKED_REPLAY_RESULT_ATTEMPT,
    "paper_result_created_flag_true": BLOCKED_PAPER_RESULT_ATTEMPT,
    "feature_vector_created_flag_true": BLOCKED_FEATURE_VECTOR_ATTEMPT,
    "trading_signal_created_flag_true": BLOCKED_TRADING_SIGNAL_ATTEMPT,
    "ranking_scoring_arbitration_created_flag_true": (
        BLOCKED_RANKING_SCORING_ARBITRATION_ATTEMPT
    ),
    "order_authority_created_flag_true": BLOCKED_ORDER_AUTHORITY_ATTEMPT,
    "profit_evidence_created_flag_true": BLOCKED_PROFIT_EVIDENCE_ATTEMPT,
    "latency_superiority_evidence_created_flag_true": (
        BLOCKED_LATENCY_OR_EXECUTION_SUPERIORITY_CLAIM
    ),
    "quantum_execution_created_flag_true": BLOCKED_QUANTUM_EXECUTION_ATTEMPT,
    "quantum_optimizer_input_created_flag_true": BLOCKED_QUANTUM_OPTIMIZER_INPUT_ATTEMPT,
    "quantum_advantage_claim_created_flag_true": BLOCKED_QUANTUM_ADVANTAGE_CLAIM_ATTEMPT,
    "atomicrows_materialization_created_flag_true": (
        BLOCKED_ATOMICROWS_MATERIALIZATION_ATTEMPT
    ),
    "noncanonical_forecastex_identity": BLOCKED_NONCANONICAL_FORECASTEX_IBKR_IDENTITY,
    "global_permanent_candidate_freeze_language": (
        BLOCKED_GLOBAL_PERMANENT_CANDIDATE_FREEZE_LANGUAGE
    ),
    "same_number_roadmap_inference": BLOCKED_SAME_NUMBER_ROADMAP_INFERENCE,
    "missing_pr134_currentization": BLOCKED_MISSING_PR134_CURRENTIZATION,
    "policy_literal_drift_fixture": BLOCKED_POLICY_LITERAL_DRIFT,
}

FORBIDDEN_RECORD_FLAG_TO_BLOCK_CODE = {
    "live_data_used_flag": BLOCKED_LIVE_DATA_ATTEMPT,
    "source_retrieval_created_flag": BLOCKED_SOURCE_RETRIEVAL_ATTEMPT,
    "source_acceptance_created_flag": BLOCKED_SOURCE_ACCEPTANCE_ATTEMPT,
    "connector_binding_created_flag": BLOCKED_CONNECTOR_BINDING_ATTEMPT,
    "credential_resolution_created_flag": BLOCKED_CREDENTIAL_RESOLUTION_ATTEMPT,
    "private_state_fetch_created_flag": BLOCKED_PRIVATE_STATE_FETCH_ATTEMPT,
    "runtime_cash_authority_created_flag": BLOCKED_RUNTIME_CASH_AUTHORITY_ATTEMPT,
    "replay_execution_created_flag": BLOCKED_REPLAY_EXECUTION_ATTEMPT,
    "paper_execution_created_flag": BLOCKED_PAPER_EXECUTION_ATTEMPT,
    "replay_result_created_flag": BLOCKED_REPLAY_RESULT_ATTEMPT,
    "paper_result_created_flag": BLOCKED_PAPER_RESULT_ATTEMPT,
    "feature_vector_created_flag": BLOCKED_FEATURE_VECTOR_ATTEMPT,
    "trading_signal_created_flag": BLOCKED_TRADING_SIGNAL_ATTEMPT,
    "ranking_scoring_arbitration_created_flag": BLOCKED_RANKING_SCORING_ARBITRATION_ATTEMPT,
    "order_authority_created_flag": BLOCKED_ORDER_AUTHORITY_ATTEMPT,
    "order_execution_created_flag": BLOCKED_ORDER_AUTHORITY_ATTEMPT,
    "profit_evidence_created_flag": BLOCKED_PROFIT_EVIDENCE_ATTEMPT,
    "latency_superiority_evidence_created_flag": (
        BLOCKED_LATENCY_OR_EXECUTION_SUPERIORITY_CLAIM
    ),
    "execution_superiority_evidence_created_flag": (
        BLOCKED_LATENCY_OR_EXECUTION_SUPERIORITY_CLAIM
    ),
    "alpha_evidence_created_flag": BLOCKED_ALPHA_EVIDENCE_ATTEMPT,
    "quantum_execution_created_flag": BLOCKED_QUANTUM_EXECUTION_ATTEMPT,
    "quantum_optimizer_input_created_flag": BLOCKED_QUANTUM_OPTIMIZER_INPUT_ATTEMPT,
    "quantum_trading_signal_created_flag": BLOCKED_QUANTUM_OPTIMIZER_INPUT_ATTEMPT,
    "quantum_advantage_claim_created_flag": BLOCKED_QUANTUM_ADVANTAGE_CLAIM_ATTEMPT,
    "atomicrows_materialization_created_flag": BLOCKED_ATOMICROWS_MATERIALIZATION_ATTEMPT,
}


@dataclass(frozen=True)
class ScopeRef:
    canonical_venue_id: str
    is_shared_scope: bool

    @property
    def market_scope_id(self) -> str:
        return f"PR135_{self.canonical_venue_id}_HISTORICAL_DATASET_SCOPE"

    @property
    def record_prefix(self) -> str:
        return f"PR135_{self.canonical_venue_id}"


def scope_refs() -> tuple[ScopeRef, ...]:
    return tuple(
        ScopeRef(canonical_venue_id=value, is_shared_scope=value in SHARED_SCOPE_IDS)
        for value in CANONICAL_VENUE_IDS
    )


def no_authority_record_fields() -> dict[str, bool]:
    return dict(RECORD_NO_AUTHORITY_FLAGS)


def no_authority_report_fields() -> dict[str, bool]:
    return dict(NO_AUTHORITY_FLAGS)


def policy_manifest_payload() -> dict[str, Any]:
    return {
        "receipt_type": "PR135_HISTORICAL_DATASET_POLICY_MANIFEST",
        "repo_pr_number": PRODUCER_REPO_PR,
        "roadmap_pr_number": PRODUCER_ROADMAP_PR,
        "policy_module_path": POLICY_MODULE_PATH,
        "policy_schema_defs_path": POLICY_SCHEMA_DEFS_PATH,
        "policy_manifest_path": POLICY_MANIFEST_PATH,
        "validator_marker": VALIDATOR_MARKER,
        "canonical_venues": list(CANONICAL_VENUE_IDS),
        "forbidden_venue_identities": list(FORBIDDEN_VENUE_IDENTITIES),
        "dataset_record_scopes": list(DATASET_RECORD_SCOPES),
        "digest_algorithms": list(DIGEST_ALGORITHMS),
        "loader_manifest_modes": list(LOADER_MANIFEST_MODES),
        "input_lock_states": list(INPUT_LOCK_STATES),
        "no_authority_flags": no_authority_report_fields(),
        "record_no_authority_flags": no_authority_record_fields(),
        "source_boundary_constants": list(SOURCE_BOUNDARY_CONSTANTS),
        "source_boundary_language": SOURCE_BOUNDARY_LANGUAGE,
        "candidate_set_constants": list(CANDIDATE_SET_CONSTANTS),
        "allowed_future_consumers": list(ALLOWED_FUTURE_CONSUMERS),
        "forbidden_consumers": list(FORBIDDEN_CONSUMERS),
        "definition_locations_approved": [
            POLICY_MODULE_PATH,
            POLICY_SCHEMA_DEFS_PATH,
            POLICY_MANIFEST_PATH,
        ],
        "policy_literal_drift_validator_path": (
            "tools/validate_historical_dataset_policy_literal_drift.py"
        ),
        "centralized_block_code_doctrine": true_value(),
        "codex_network_access_used": False,
        "gh_command_used_by_codex": False,
    }


def true_value() -> bool:
    return True
