"""Central PR134 runtime resolver snapshot executor policy constants."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


STAGE1_VENUE_IDS = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
SHARED_SCOPE_IDS = ("PREDICTION_MARKETS_GENERAL",)

PRODUCER_REPO_PR = "PR134"
PRODUCER_ROADMAP_PR = "PR116"
UPSTREAM_REPO_PR = "PR133"
UPSTREAM_ROADMAP_PR = "PR115"
UPSTREAM_ORDERBOOK_EVENT_STATE_PACKAGE = (
    "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot"
)
DOWNSTREAM_PR_IDS = ("PR117",)
RECOMMENDED_ATOMICROWS_BRIDGE_AFTER_REPO_PR = "PR135"
RECOMMENDED_ATOMICROWS_BRIDGE_CANDIDATE_REPO_PR = "PR136"

SCHEMA_VERSION = "PR134_RUNTIME_RESOLVER_SNAPSHOT_EXECUTOR_SCHEMA_V1"
REPORT_SCHEMA_VERSION = "PR134_RUNTIME_RESOLVER_SNAPSHOT_EXECUTOR_REPORT_V1"
CREATED_BY = "CODEX_PR134_FIXTURE_OR_VALIDATOR"
PACKAGE_AUTHORITY_CLASS = (
    "FIXTURE_BACKED_RUNTIME_RESOLVER_SNAPSHOT_CONTRACT_ONLY_NOT_LIVE_RUNTIME_AUTHORITY"
)

PR133_HANDOFF_ID = "PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_DOWNSTREAM_HANDOFF_V1"
PR132_MARKET_DATA_HANDOFF_ID = "PR132_MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF_V1"
PR131_CREDENTIAL_READINESS_HANDOFF_ID = "PR131_CREDENTIAL_READINESS_HANDOFF_V1"
PR134_HANDOFF_ID = "PR134_RUNTIME_RESOLVER_SNAPSHOT_DOWNSTREAM_HANDOFF_V1"

ALLOWED_RUNTIME_RESOLVER_INPUT_CLASSES = (
    "PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_HANDOFF_INPUT",
    "SYNTHETIC_FIXTURE_RUNTIME_RESOLVER_INPUT",
    "ACCEPTED_SOURCE_GATED_RUNTIME_RESOLVER_INPUT_METADATA",
    "SOURCE_REQUIRED_RUNTIME_RESOLVER_INPUT_PLACEHOLDER",
    "CONNECTOR_SEMANTIC_REQUIRED_RUNTIME_RESOLVER_INPUT_PLACEHOLDER",
    "CREDENTIAL_READINESS_REQUIRED_RUNTIME_RESOLVER_INPUT_PLACEHOLDER",
)

ALLOWED_RUNTIME_RESOLVER_SNAPSHOT_CLASSES = (
    "SYNTHETIC_FIXTURE_RUNTIME_RESOLVER_SNAPSHOT",
    "QTT_INTERNAL_RUNTIME_RESOLVER_METADATA_SNAPSHOT",
    "QTT_INTERNAL_VENUE_SCOPE_RUNTIME_STATE_METADATA_SNAPSHOT",
    "QTT_INTERNAL_DEPENDENCY_STATE_METADATA_SNAPSHOT",
    "QTT_INTERNAL_VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK_METADATA_ONLY",
    "QTT_INTERNAL_REPLAY_PAPER_INPUT_READY_METADATA_ONLY",
    "SOURCE_REQUIRED_RUNTIME_RESOLVER_SNAPSHOT_PLACEHOLDER",
    "CONNECTOR_SEMANTIC_REQUIRED_RUNTIME_RESOLVER_SNAPSHOT_PLACEHOLDER",
    "BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_PLACEHOLDER",
)

ALLOWED_RUNTIME_RESOLVER_READINESS_STATES = (
    "READY_METADATA_ONLY",
    "SOURCE_REQUIRED",
    "SOURCE_REVALIDATION_REQUIRED",
    "CONNECTOR_SEMANTIC_REQUIRED",
    "CREDENTIAL_READINESS_REQUIRED",
    "PRIVATE_STATE_REQUIRED",
    "CONTRACT_NORMALIZATION_REQUIRED",
    "COMPARABILITY_SCOPE_REQUIRED",
    "LIQUIDITY_SCOPE_REQUIRED",
    "BLOCKED_SCOPE_MISMATCH",
    "BLOCKED_STALE_DEPENDENCY",
    "BLOCKED_CONFLICT",
    "BLOCKED_SCHEMA_MISMATCH",
    "BLOCKED_LIVE_AUTHORITY_REQUIRED",
)

ALLOWED_SOURCE_DEPENDENCY_STATES = (
    "ACCEPTED_SOURCE_GATED",
    "CONNECTOR_SEMANTIC_GATED",
    "SOURCE_REQUIRED",
    "SOURCE_REVALIDATION_REQUIRED",
    "CONNECTOR_SEMANTIC_REQUIRED",
    "CONTRACT_NORMALIZATION_REQUIRED",
    "COMPARABILITY_SCOPE_REQUIRED",
    "LIQUIDITY_SCOPE_REQUIRED",
    "BLOCKED_SCOPE_MISMATCH",
    "BLOCKED_STALE_DEPENDENCY",
    "BLOCKED_CONFLICT",
)

UNRESOLVED_READY_BLOCKING_STATES = (
    "SOURCE_REQUIRED",
    "SOURCE_REVALIDATION_REQUIRED",
    "CONNECTOR_SEMANTIC_REQUIRED",
    "CREDENTIAL_READINESS_REQUIRED",
    "PRIVATE_STATE_REQUIRED",
    "CONTRACT_NORMALIZATION_REQUIRED",
    "COMPARABILITY_SCOPE_REQUIRED",
    "LIQUIDITY_SCOPE_REQUIRED",
    "BLOCKED_SCOPE_MISMATCH",
    "BLOCKED_STALE_DEPENDENCY",
    "BLOCKED_CONFLICT",
    "BLOCKED_SCHEMA_MISMATCH",
    "BLOCKED_LIVE_AUTHORITY_REQUIRED",
)

VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK_FIELDS = (
    "candidate_set_snapshot_lock_metadata_created",
    "candidate_set_snapshot_version_id",
    "candidate_set_snapshot_parent_version_id",
    "candidate_set_snapshot_created_from_fixture",
    "candidate_set_snapshot_is_global_permanent_freeze",
    "candidate_set_snapshot_allows_future_versions",
    "candidate_set_snapshot_allows_future_candidate_additions",
    "candidate_set_snapshot_immutable_for_replay_audit_only",
    "synthetic_candidate_set_ref",
    "candidate_scope_lock_ref",
    "exact_live_contract_id_created",
    "live_candidate_discovery_created",
    "live_candidate_import_created",
    "live_contract_selection_created",
    "ranking_output_created",
    "trading_signal_created",
    "order_authority_created",
    "profit_evidence_created",
)

REPLAY_PAPER_INPUT_IDENTITY_FIELDS = (
    "future_replay_paper_input_identity_ref",
    "future_replay_paper_same_input_lock_required",
    "future_replay_paper_same_runtime_resolver_snapshot_required",
    "future_replay_paper_same_candidate_set_snapshot_version_required",
    "future_replay_paper_owner_policy_snapshot_ref",
    "replay_execution_created",
    "paper_execution_created",
    "replay_result_created",
    "paper_result_created",
)

QUANTUM_FORWARD_RUNTIME_RESOLVER_METADATA_FIELDS = (
    "quantum_ready_runtime_resolver_snapshot_contract",
    "future_quantum_runtime_state_encoding_ref",
    "future_qaoa_qubo_runtime_constraint_encoding_ref",
    "future_qaoa_qubo_candidate_set_constraint_ref",
    "future_quantum_kernel_runtime_regime_ref",
    "future_quantum_annealing_runtime_constraint_ref",
    "future_quantum_microstructure_runtime_graph_ref",
    "future_quantum_amplitude_runtime_snapshot_ref",
    "future_quantum_dependency_graph_encoding_ref",
)

QUANTUM_ZERO_AUTHORITY_FLAGS = (
    "quantum_execution_created",
    "quantum_backend_called",
    "quantum_simulator_called",
    "quantum_optimizer_called",
    "quantum_runtime_feature_computation_created",
    "quantum_optimizer_input_created",
    "quantum_trading_signal_created",
    "quantum_advantage_claim_created",
)

ATOMICROWS_PRE_BRIDGE_METADATA_FIELDS = (
    "atomicrows_pre_bridge_compatibility_metadata_created",
    "future_atomicrows_runtime_resolver_snapshot_row_refs",
    "future_atomicrows_runtime_state_feature_family_refs",
    "future_atomicrows_candidate_set_snapshot_lock_family_refs",
    "future_atomicrows_replay_paper_input_identity_family_refs",
    "future_atomicrows_snapshot_feature_row_refs",
    "future_atomicrows_market_data_feature_row_refs",
    "future_atomicrows_quantum_runtime_feature_family_refs",
    "future_atomicrows_parameter_row_refs",
    "future_atomicrows_family_refs",
    "future_atomicrows_bridge_after_pr135_ref",
    "future_atomicrows_bridge_recommended_after_repo_pr",
    "future_atomicrows_bridge_candidate_repo_pr",
)

ATOMICROWS_ZERO_AUTHORITY_FLAGS = (
    "atomicrows_bridge_authority_created",
    "atomicrows_full_materialization_authorized",
    "atomicrows_bundle_consumed",
    "atomicrows_bundle_created",
    "atomicrows_bundle_edited",
    "atomicrows_sha_created",
    "atomicrows_row_records_created_count",
    "atomicrows_4183_completion_claim_created",
    "atomicrows_authority_created",
)

AUTHORITY_ZERO_FLAGS = {
    "source_retrieval_created": False,
    "source_acceptance_created": False,
    "connector_semantic_binding_created": False,
    "official_venue_semantics_fabricated": False,
    "exact_live_contract_id_created": False,
    "live_candidate_discovery_created": False,
    "live_candidate_import_created": False,
    "live_contract_selection_created": False,
    "live_market_data_fetch_created": False,
    "rest_client_created": False,
    "websocket_client_created": False,
    "venue_api_call_created": False,
    "network_io_created": False,
    "credential_provider_called": False,
    "live_credential_resolution_performed": False,
    "raw_secret_capture_created": False,
    "production_connector_authority_created": False,
    "private_state_fetch_created": False,
    "runtime_cash_authority_created": False,
    "live_runtime_resolver_authority_created": False,
    "historical_dataset_digest_created": False,
    "market_data_feature_vector_created": False,
    "runtime_feature_vector_created": False,
    "trading_signal_created": False,
    "ranking_output_created": False,
    "scoring_ranking_arbitration_output_created": False,
    "replay_execution_created": False,
    "paper_execution_created": False,
    "replay_result_created": False,
    "paper_result_created": False,
    "live_trading_created": False,
    "order_authority_created": False,
    "order_execution_created": False,
    "profit_evidence_created": False,
    "neural_training_created": False,
    "neural_inference_created": False,
    "quantum_execution_created": False,
    "quantum_backend_called": False,
    "quantum_simulator_called": False,
    "quantum_optimizer_called": False,
    "quantum_runtime_feature_computation_created": False,
    "quantum_optimizer_input_created": False,
    "quantum_trading_signal_created": False,
    "quantum_advantage_claim_created": False,
    "atomicrows_bridge_authority_created": False,
    "atomicrows_full_materialization_authorized": False,
    "atomicrows_bundle_consumed": False,
    "atomicrows_bundle_created": False,
    "atomicrows_bundle_edited": False,
    "atomicrows_sha_created": False,
    "atomicrows_row_records_created_count": 0,
    "atomicrows_4183_completion_claim_created": False,
    "atomicrows_authority_created": False,
}

ZERO_COUNT_INVARIANTS = (
    "duplicate_runtime_resolver_snapshot_id_count",
    "duplicate_runtime_resolver_input_lock_id_count",
    "duplicate_canonical_input_identity_ref_count",
    "duplicate_future_replay_paper_input_identity_ref_count",
    "duplicate_candidate_set_snapshot_version_id_count",
    "missing_pr133_handoff_count",
    "missing_input_lock_count",
    "missing_candidate_scope_lock_count",
    "missing_contract_normalization_dependency_count",
    "missing_comparability_scope_dependency_count",
    "missing_liquidity_scope_dependency_count",
    "cross_venue_scope_mismatch_count",
    "invalid_readiness_state_count",
    "unresolved_dependency_ready_claim_count",
    "stale_dependency_ready_claim_count",
    "conflict_dependency_ready_claim_count",
    "exact_live_contract_id_created_count",
    "global_candidate_universe_freeze_claim_count",
    "future_candidate_addition_blocked_count",
    "live_candidate_discovery_created_count",
    "live_candidate_import_created_count",
    "live_contract_selection_created_count",
    "live_runtime_authority_created_count",
    "historical_dataset_digest_created_count",
    "feature_vector_created_count",
    "trading_signal_created_count",
    "ranking_output_created_count",
    "scoring_ranking_arbitration_output_created_count",
    "replay_execution_created_count",
    "paper_execution_created_count",
    "replay_result_created_count",
    "paper_result_created_count",
    "live_trading_created_count",
    "order_authority_count",
    "order_execution_count",
    "profit_evidence_count",
    "live_market_data_fetch_count",
    "rest_client_created_count",
    "websocket_client_created_count",
    "venue_api_call_count",
    "network_io_count",
    "credential_provider_call_count",
    "live_credential_resolution_count",
    "private_state_fetch_count",
    "runtime_cash_authority_count",
    "quantum_runtime_feature_computation_created_count",
    "quantum_optimizer_input_created_count",
    "quantum_trading_signal_created_count",
    "quantum_backend_simulator_optimizer_execution_count",
    "quantum_advantage_claim_created_count",
    "atomicrows_bridge_authority_created_count",
    "atomicrows_bundle_consumed_count",
    "atomicrows_bundle_created_count",
    "atomicrows_bundle_edited_count",
    "atomicrows_sha_created_count",
    "atomicrows_row_records_created_count",
    "atomicrows_4183_completion_claim_created_count",
)

ALLOWED_ACTION_IDS = (
    "READ_MANDATORY_ROADMAP_MASTER_PLAN_SOURCE_EVIDENCE_FILES",
    "INSPECT_PR105_TO_PR133_ARTIFACTS",
    "INSPECT_ATOMICROWS_AUTHORITY_ARTIFACTS_WITHOUT_MUTATION",
    "CREATE_PR134_SCHEMAS",
    "CREATE_PR134_FIXTURES",
    "CREATE_PR134_VALIDATORS",
    "CREATE_PR134_GENERATED_REPORTS",
    "CREATE_PR134_TESTS",
    "CREATE_FIXTURE_BACKED_RUNTIME_RESOLVER_INPUT_LOCKS",
    "CREATE_FIXTURE_BACKED_RUNTIME_RESOLVER_SNAPSHOT_RECORDS",
    "CREATE_DETERMINISTIC_RUNTIME_RESOLVER_READINESS_STATE_METADATA",
    "CREATE_VERSIONED_CANDIDATE_SET_SNAPSHOT_LOCK_METADATA",
    "CREATE_FUTURE_REPLAY_PAPER_INPUT_IDENTITY_METADATA",
    "CREATE_QUANTUM_READY_RUNTIME_RESOLVER_SNAPSHOT_METADATA_FIELDS",
    "CREATE_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_METADATA_FIELDS",
    "INTEGRATE_PR134_VALIDATOR_INTO_VALIDATION_GATES",
    "RUN_LOCAL_VALIDATION_COMMANDS",
)

BLOCKED_ACTION_IDS = (
    "CALL_VENUE_REST_APIS",
    "OPEN_WEBSOCKET_SUBSCRIPTIONS",
    "IMPORT_NETWORK_CLIENT_LIBRARIES_FOR_PR134_EXECUTOR_EXECUTION",
    "RESOLVE_CREDENTIALS",
    "CALL_CREDENTIAL_PROVIDER",
    "READ_ENVIRONMENT_VARIABLES_FOR_CREDENTIALS",
    "FETCH_LIVE_MARKET_DATA",
    "STORE_LIVE_MARKET_PAYLOADS",
    "ACCEPT_SOURCE_FACTS",
    "CREATE_CONNECTOR_SEMANTIC_BINDINGS",
    "FETCH_ACCOUNT_PRIVATE_STATE",
    "CREATE_GLOBAL_PERMANENT_CANDIDATE_UNIVERSE_FREEZE",
    "BLOCK_FUTURE_CANDIDATE_ADDITIONS",
    "CREATE_LIVE_CANDIDATE_DISCOVERY",
    "CREATE_LIVE_CANDIDATE_IMPORT",
    "CREATE_LIVE_CONTRACT_EVENT_SELECTION",
    "CREATE_EXACT_LIVE_CONTRACT_IDS",
    "CREATE_LIVE_RUNTIME_RESOLVER_AUTHORITY",
    "CREATE_HISTORICAL_DATASET_DIGESTS",
    "CREATE_FEATURE_VECTORS",
    "CREATE_TRADING_SIGNALS",
    "CREATE_RANKING_OUTPUT",
    "CREATE_REPLAY_EXECUTION",
    "CREATE_PAPER_EXECUTION",
    "CREATE_REPLAY_RESULT_PACKETS",
    "CREATE_PAPER_RESULT_PACKETS",
    "CREATE_LIVE_TRADING_EXECUTION",
    "CREATE_SCORING_RANKING_ARBITRATION_OUTPUTS",
    "COMPUTE_QUANTUM_RUNTIME_FEATURES",
    "CREATE_QUANTUM_OPTIMIZER_INPUTS",
    "CREATE_QUANTUM_TRADING_SIGNALS",
    "EXECUTE_QUANTUM_BACKEND_SIMULATOR_OPTIMIZER",
    "CREATE_ATOMICROWS_BRIDGE_AUTHORITY",
    "CREATE_ATOMICROWS_BUNDLE",
    "EDIT_ATOMICROWS_BUNDLE",
    "CREATE_ATOMICROWS_SHA",
    "CREATE_ATOMICROWS_ROW_RECORDS",
    "CLAIM_4183_ATOMICROWS_COMPLETION",
    "SUBMIT_CANCEL_REDUCE_CLOSE_ORDERS",
    "EDIT_MASTER_PLAN_WITHOUT_OWNER_APPROVAL",
)

REJECTION_REASON_CODES = (
    "MISSING_PR133_HANDOFF",
    "MALFORMED_PR133_HANDOFF",
    "VENUE_SCOPE_MISMATCH",
    "LIVE_RUNTIME_AUTHORITY_CREATED",
    "LIVE_MARKET_DATA_FETCH_CREATED",
    "PRIVATE_STATE_FETCH_CREATED",
    "HISTORICAL_DATASET_DIGEST_CREATED",
    "FEATURE_VECTOR_CREATED",
    "TRADING_SIGNAL_CREATED",
    "REPLAY_EXECUTION_CREATED",
    "PAPER_EXECUTION_CREATED",
    "REPLAY_RESULT_CREATED",
    "PAPER_RESULT_CREATED",
    "ORDER_AUTHORITY_CREATED",
    "ORDER_EXECUTION_CREATED",
    "LIVE_TRADING_CREATED",
    "RANKING_OUTPUT_CREATED",
    "SCORING_RANKING_ARBITRATION_OUTPUT_CREATED",
    "NEURAL_TRAINING_CREATED",
    "NEURAL_INFERENCE_CREATED",
    "QUANTUM_RUNTIME_FEATURE_COMPUTATION_CREATED",
    "QUANTUM_OPTIMIZER_INPUT_CREATED",
    "QUANTUM_TRADING_SIGNAL_CREATED",
    "ATOMICROWS_BUNDLE_CREATED",
    "ATOMICROWS_ROW_RECORDS_CREATED",
    "ATOMICROWS_4183_COMPLETION_CLAIM_CREATED",
    "READY_WITH_UNRESOLVED_DEPENDENCY",
    "DUPLICATE_RUNTIME_RESOLVER_SNAPSHOT_ID",
    "MISSING_RUNTIME_RESOLVER_INPUT_LOCK",
    "MISSING_CANDIDATE_SCOPE_LOCK",
    "MISSING_CONTRACT_NORMALIZATION_DEPENDENCY",
    "MISSING_COMPARABILITY_SCOPE_DEPENDENCY",
    "MISSING_LIQUIDITY_SCOPE_DEPENDENCY",
    "STALE_DEPENDENCY_READY_CLAIM",
    "CONFLICT_DEPENDENCY_READY_CLAIM",
    "EXACT_LIVE_CONTRACT_ID_CREATED",
    "GLOBAL_CANDIDATE_UNIVERSE_FREEZE_CLAIM",
    "FUTURE_CANDIDATE_ADDITION_BLOCKED",
    "LIVE_CANDIDATE_DISCOVERY_CREATED",
    "LIVE_CANDIDATE_IMPORT_CREATED",
    "LIVE_CONTRACT_SELECTION_CREATED",
    "REST_CLIENT_CREATED",
    "WEBSOCKET_CLIENT_CREATED",
    "VENUE_API_CALL_CREATED",
    "NETWORK_IO_CREATED",
    "CREDENTIAL_PROVIDER_CALLED",
    "LIVE_CREDENTIAL_RESOLUTION_PERFORMED",
    "RUNTIME_CASH_AUTHORITY_CREATED",
    "PROFIT_EVIDENCE_CREATED",
    "QUANTUM_EXECUTION_CREATED",
    "QUANTUM_ADVANTAGE_CLAIM_CREATED",
    "ATOMICROWS_SHA_CREATED",
    "ATOMICROWS_BRIDGE_AUTHORITY_CREATED",
)

DISALLOWED_USE = (
    "LIVE_RUNTIME_EXECUTION",
    "LIVE_CANDIDATE_DISCOVERY",
    "LIVE_CANDIDATE_IMPORT",
    "LIVE_CONTRACT_SELECTION",
    "LIVE_MARKET_DATA_FETCH",
    "VENUE_API_CALL",
    "PRODUCTION_CONNECTOR_CLIENT",
    "CREDENTIAL_RESOLUTION",
    "PRIVATE_STATE_FETCH",
    "HISTORICAL_DATASET_DIGEST_CREATE",
    "REPLAY_EXECUTION",
    "PAPER_EXECUTION",
    "REPLAY_RESULT_CREATE",
    "PAPER_RESULT_CREATE",
    "LIVE_TRADING",
    "MARKET_DATA_FEATURE_VECTOR_CREATE",
    "TRADING_SIGNAL_CREATE",
    "RANKING_OUTPUT_CREATE",
    "QUANTUM_RUNTIME_FEATURE_COMPUTE",
    "QUANTUM_OPTIMIZER_INPUT_CREATE",
    "QUANTUM_TRADING_SIGNAL_CREATE",
    "ATOMICROWS_BUNDLE_CREATE",
    "ATOMICROWS_ROW_RECORD_CREATE",
    "ATOMICROWS_SHA_CREATE",
    "ORDER_SUBMISSION",
    "ORDER_CANCELLATION",
    "ORDER_REDUCTION",
    "ORDER_CLOSE",
)

BANNED_IMPORT_MODULES = (
    "requests",
    "httpx",
    "aiohttp",
    "urllib.request",
    "urllib3",
    "websockets",
    "websocket",
    "socket",
    "ssl",
    "boto3",
    "botocore",
    "hvac",
    "keyring",
    "secretstorage",
    "azure.identity",
    "google.cloud.secretmanager",
    "kubernetes",
    "dotenv",
    "qiskit",
    "pennylane",
    "dwave",
    "cirq",
)


@dataclass(frozen=True)
class ScopeRef:
    field_name: str
    value: str
    is_shared_scope: bool

    @property
    def token(self) -> str:
        return self.value

    @property
    def record_prefix(self) -> str:
        return f"{PRODUCER_REPO_PR}_{self.token}"


def venue_scope_refs() -> tuple[ScopeRef, ...]:
    return tuple(ScopeRef("venue_id", venue_id, False) for venue_id in STAGE1_VENUE_IDS)


def shared_scope_refs() -> tuple[ScopeRef, ...]:
    return tuple(ScopeRef("scope_id", scope_id, True) for scope_id in SHARED_SCOPE_IDS)


def stage1_scope_refs() -> tuple[ScopeRef, ...]:
    return venue_scope_refs() + shared_scope_refs()


def canonical_scope_refs() -> tuple[ScopeRef, ...]:
    return tuple(sorted(stage1_scope_refs(), key=lambda scope_ref: scope_ref.value))


def scope_identity(scope_ref: ScopeRef) -> dict[str, str]:
    return {scope_ref.field_name: scope_ref.value}


def common_record_fields(record_type: str, scope_ref: ScopeRef | None = None) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "record_type": record_type,
        "schema_version": SCHEMA_VERSION,
        "producer_pr": PRODUCER_REPO_PR,
        "producer_roadmap_pr": PRODUCER_ROADMAP_PR,
        "created_by": CREATED_BY,
        "authority_class": PACKAGE_AUTHORITY_CLASS,
    }
    if scope_ref is not None:
        fields.update(scope_identity(scope_ref))
    fields.update(AUTHORITY_ZERO_FLAGS)
    fields.update(quantum_metadata(scope_ref.token if scope_ref else "GLOBAL"))
    fields.update(atomicrows_metadata(scope_ref.token if scope_ref else "GLOBAL"))
    return fields


def candidate_set_metadata(scope_ref: ScopeRef, sequence_id: int) -> dict[str, Any]:
    return {
        "candidate_set_snapshot_lock_metadata_created": True,
        "candidate_set_snapshot_version_id": (
            f"{scope_ref.record_prefix}_CANDIDATE_SET_SNAPSHOT_VERSION_V1"
        ),
        "candidate_set_snapshot_parent_version_id": (
            f"{scope_ref.record_prefix}_CANDIDATE_SET_SNAPSHOT_VERSION_PARENT_V0"
        ),
        "candidate_set_snapshot_created_from_fixture": True,
        "candidate_set_snapshot_is_global_permanent_freeze": False,
        "candidate_set_snapshot_allows_future_versions": True,
        "candidate_set_snapshot_allows_future_candidate_additions": True,
        "candidate_set_snapshot_immutable_for_replay_audit_only": True,
        "synthetic_candidate_set_ref": f"{scope_ref.record_prefix}_SYNTHETIC_CANDIDATE_SET",
        "candidate_scope_lock_ref": f"{scope_ref.record_prefix}_CANDIDATE_SCOPE_LOCK",
        "exact_live_contract_id_created": False,
        "live_candidate_discovery_created": False,
        "live_candidate_import_created": False,
        "live_contract_selection_created": False,
        "ranking_output_created": False,
        "trading_signal_created": False,
        "order_authority_created": False,
        "profit_evidence_created": False,
        "deterministic_sequence_id": sequence_id,
    }


def replay_paper_identity_metadata(scope_ref: ScopeRef) -> dict[str, Any]:
    return {
        "future_replay_paper_input_identity_ref": (
            f"{scope_ref.record_prefix}_FUTURE_REPLAY_PAPER_INPUT_IDENTITY"
        ),
        "future_replay_paper_same_input_lock_required": True,
        "future_replay_paper_same_runtime_resolver_snapshot_required": True,
        "future_replay_paper_same_candidate_set_snapshot_version_required": True,
        "future_replay_paper_owner_policy_snapshot_ref": (
            f"{scope_ref.record_prefix}_FUTURE_OWNER_POLICY_SNAPSHOT_REF"
        ),
        "replay_execution_created": False,
        "paper_execution_created": False,
        "replay_result_created": False,
        "paper_result_created": False,
    }


def quantum_metadata(scope_token: str) -> dict[str, Any]:
    return {
        "quantum_ready_runtime_resolver_snapshot_contract": True,
        "future_quantum_runtime_state_encoding_ref": (
            f"FUTURE_QUANTUM_RUNTIME_STATE_ENCODING::{scope_token}"
        ),
        "future_qaoa_qubo_runtime_constraint_encoding_ref": (
            f"FUTURE_QAOA_QUBO_RUNTIME_CONSTRAINT_ENCODING::{scope_token}"
        ),
        "future_qaoa_qubo_candidate_set_constraint_ref": (
            f"FUTURE_QAOA_QUBO_CANDIDATE_SET_CONSTRAINT::{scope_token}"
        ),
        "future_quantum_kernel_runtime_regime_ref": (
            f"FUTURE_QUANTUM_KERNEL_RUNTIME_REGIME::{scope_token}"
        ),
        "future_quantum_annealing_runtime_constraint_ref": (
            f"FUTURE_QUANTUM_ANNEALING_RUNTIME_CONSTRAINT::{scope_token}"
        ),
        "future_quantum_microstructure_runtime_graph_ref": (
            f"FUTURE_QUANTUM_MICROSTRUCTURE_RUNTIME_GRAPH::{scope_token}"
        ),
        "future_quantum_amplitude_runtime_snapshot_ref": (
            f"FUTURE_QUANTUM_AMPLITUDE_RUNTIME_SNAPSHOT::{scope_token}"
        ),
        "future_quantum_dependency_graph_encoding_ref": (
            f"FUTURE_QUANTUM_DEPENDENCY_GRAPH_ENCODING::{scope_token}"
        ),
        "quantum_execution_created": False,
        "quantum_backend_called": False,
        "quantum_simulator_called": False,
        "quantum_optimizer_called": False,
        "quantum_runtime_feature_computation_created": False,
        "quantum_optimizer_input_created": False,
        "quantum_trading_signal_created": False,
        "quantum_advantage_claim_created": False,
    }


def atomicrows_metadata(scope_token: str) -> dict[str, Any]:
    return {
        "atomicrows_pre_bridge_compatibility_metadata_created": True,
        "future_atomicrows_runtime_resolver_snapshot_row_refs": [
            f"FUTURE_ATOMICROWS_RUNTIME_RESOLVER_SNAPSHOT_ROW::{scope_token}"
        ],
        "future_atomicrows_runtime_state_feature_family_refs": [
            f"FUTURE_ATOMICROWS_RUNTIME_STATE_FEATURE_FAMILY::{scope_token}"
        ],
        "future_atomicrows_candidate_set_snapshot_lock_family_refs": [
            f"FUTURE_ATOMICROWS_CANDIDATE_SET_SNAPSHOT_LOCK_FAMILY::{scope_token}"
        ],
        "future_atomicrows_replay_paper_input_identity_family_refs": [
            f"FUTURE_ATOMICROWS_REPLAY_PAPER_INPUT_IDENTITY_FAMILY::{scope_token}"
        ],
        "future_atomicrows_snapshot_feature_row_refs": [
            f"FUTURE_ATOMICROWS_SNAPSHOT_FEATURE_ROW::{scope_token}"
        ],
        "future_atomicrows_market_data_feature_row_refs": [
            f"FUTURE_ATOMICROWS_MARKET_DATA_FEATURE_ROW::{scope_token}"
        ],
        "future_atomicrows_quantum_runtime_feature_family_refs": [
            f"FUTURE_ATOMICROWS_QUANTUM_RUNTIME_FEATURE_FAMILY::{scope_token}"
        ],
        "future_atomicrows_parameter_row_refs": [
            f"FUTURE_ATOMICROWS_PARAMETER_ROW::{scope_token}"
        ],
        "future_atomicrows_family_refs": [
            f"FUTURE_ATOMICROWS_RUNTIME_RESOLVER_FAMILY::{scope_token}"
        ],
        "future_atomicrows_bridge_after_pr135_ref": (
            f"FUTURE_ATOMICROWS_BRIDGE_AFTER_{RECOMMENDED_ATOMICROWS_BRIDGE_AFTER_REPO_PR}"
        ),
        "future_atomicrows_bridge_recommended_after_repo_pr": (
            RECOMMENDED_ATOMICROWS_BRIDGE_AFTER_REPO_PR
        ),
        "future_atomicrows_bridge_candidate_repo_pr": (
            RECOMMENDED_ATOMICROWS_BRIDGE_CANDIDATE_REPO_PR
        ),
        "atomicrows_bridge_authority_created": False,
        "atomicrows_full_materialization_authorized": False,
        "atomicrows_bundle_consumed": False,
        "atomicrows_bundle_created": False,
        "atomicrows_bundle_edited": False,
        "atomicrows_sha_created": False,
        "atomicrows_row_records_created_count": 0,
        "atomicrows_4183_completion_claim_created": False,
        "atomicrows_authority_created": False,
    }
