from __future__ import annotations

from dataclasses import dataclass


STAGE1_VENUE_IDS = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
SHARED_SCOPE_IDS = ("PREDICTION_MARKETS_GENERAL",)

PRODUCER_REPO_PR = "PR132"
PRODUCER_ROADMAP_PR = "PR114"
UPSTREAM_REPO_PR = "PR131"
UPSTREAM_ROADMAP_PR = "PR113"
DOWNSTREAM_PR_IDS = ("PR115", "PR116", "PR117")

PACKAGE_AUTHORITY_CLASS = (
    "FIXTURE_BACKED_MARKET_DATA_INGEST_CONTRACT_ONLY_NOT_LIVE_MARKET_DATA_AUTHORITY"
)
CREATED_BY = "CODEX_PR132_FIXTURE_OR_VALIDATOR"
SCHEMA_VERSION = "PR132_MARKET_DATA_INGEST_SCHEMA_V1"

ALLOWED_ADAPTER_INPUT_CLASSES = (
    "SYNTHETIC_FIXTURE_MARKET_DATA_INPUT",
    "ACCEPTED_SOURCE_GATED_MARKET_DATA_INPUT_METADATA",
    "SOURCE_REQUIRED_MARKET_DATA_INPUT_PLACEHOLDER",
    "CONNECTOR_SEMANTIC_REQUIRED_MARKET_DATA_INPUT_PLACEHOLDER",
)

ALLOWED_CANONICAL_EVENT_KIND_CLASSES = (
    "MARKET_CATALOG_INPUT_METADATA_ENVELOPE",
    "MARKET_STATUS_INPUT_METADATA_ENVELOPE",
    "PRICE_QUOTE_INPUT_METADATA_ENVELOPE",
    "TRADE_PRINT_INPUT_METADATA_ENVELOPE",
    "ORDERBOOK_INPUT_METADATA_ENVELOPE_FOR_PR115_ONLY",
    "ORDERBOOK_DELTA_INPUT_METADATA_ENVELOPE_FOR_PR115_ONLY",
    "SETTLEMENT_STATUS_INPUT_METADATA_ENVELOPE",
    "VENUE_HEALTH_INPUT_METADATA_ENVELOPE",
)

ALLOWED_SOURCE_DEPENDENCY_STATES = (
    "ACCEPTED_SOURCE_GATED",
    "CONNECTOR_SEMANTIC_GATED",
    "SOURCE_REQUIRED",
    "CONNECTOR_SEMANTIC_REQUIRED",
    "BLOCKED_SCOPE_MISMATCH",
)

QUANTUM_FORWARD_METADATA_FIELDS = (
    "future_quantum_feature_encoding_ref",
    "future_quantum_optimizer_market_data_feature_ref",
    "future_quantum_market_microstructure_feature_family_ref",
    "future_qaoa_qubo_market_state_encoding_ref",
    "future_quantum_kernel_market_regime_feature_ref",
    "future_quantum_annealing_liquidity_state_ref",
    "quantum_ready_market_data_contract",
)

QUANTUM_ZERO_AUTHORITY_FLAGS = {
    "quantum_execution_created": False,
    "quantum_backend_called": False,
    "quantum_simulator_called": False,
    "quantum_optimizer_called": False,
    "quantum_feature_computation_created": False,
    "quantum_optimizer_input_created": False,
    "quantum_trading_signal_created": False,
    "quantum_advantage_claim_created": False,
}

BLOCKED_ACTION_IDS = (
    "LIVE_REST_MARKET_DATA_FETCH",
    "LIVE_WEBSOCKET_MARKET_DATA_SUBSCRIBE",
    "VENUE_API_CALL",
    "NETWORK_IO",
    "CREDENTIAL_PROVIDER_CALL",
    "LIVE_CREDENTIAL_RESOLUTION",
    "RAW_SECRET_READ",
    "OFFICIAL_VENUE_SEMANTICS_FABRICATION",
    "SOURCE_RETRIEVAL_CREATION",
    "SOURCE_ACCEPTANCE_CREATION",
    "CONNECTOR_SEMANTIC_BINDING_CREATION",
    "ORDERBOOK_SNAPSHOT_BUILD",
    "EVENT_STATE_SNAPSHOT_BUILD",
    "RUNTIME_RESOLVER_SNAPSHOT_CREATE",
    "HISTORICAL_DATASET_DIGEST_CREATE",
    "MARKET_DATA_FEATURE_VECTOR_CREATE",
    "TRADING_SIGNAL_CREATE",
    "SCORING_RANKING_ARBITRATION_OUTPUT_CREATE",
    "PRIVATE_STATE_FETCH",
    "RUNTIME_CASH_AUTHORITY_CREATE",
    "ORDER_AUTHORITY_CREATE",
    "ORDER_EXECUTION",
    "REPLAY_PAPER_LIVE_EXECUTION",
    "PROFIT_EVIDENCE_CREATE",
    "QUANTUM_BACKEND_SIMULATOR_OPTIMIZER_EXECUTE",
    "QUANTUM_FEATURE_COMPUTE",
    "QUANTUM_OPTIMIZER_INPUT_CREATE",
    "QUANTUM_TRADING_SIGNAL_CREATE",
    "QUANTUM_ADVANTAGE_CLAIM_CREATE",
    "ATOMICROWS_BUNDLE_SHA_MUTATE",
)

ALLOWED_ACTION_IDS = (
    "READ_MANDATORY_ROADMAP_MASTER_PLAN_SOURCE_EVIDENCE_FILES",
    "INSPECT_PR105_TO_PR131_ARTIFACTS",
    "CREATE_PR132_SCHEMAS",
    "CREATE_PR132_FIXTURES",
    "CREATE_PR132_VALIDATORS",
    "CREATE_PR132_GENERATED_REPORTS",
    "CREATE_PR132_TESTS",
    "CREATE_QUANTUM_READY_MARKET_DATA_CONTRACT_METADATA_FIELDS",
    "INTEGRATE_PR132_VALIDATOR_INTO_VALIDATION_GATES",
    "RUN_LOCAL_VALIDATION_COMMANDS",
)

REJECTION_REASON_CODES = (
    "BLOCKED_MISSING_PR131_CREDENTIAL_HANDOFF",
    "BLOCKED_MALFORMED_PR131_CREDENTIAL_HANDOFF",
    "BLOCKED_SCOPE_MISMATCH",
    "BLOCKED_LIVE_NETWORK_ATTEMPT",
    "BLOCKED_REST_CLIENT_ATTEMPT",
    "BLOCKED_WEBSOCKET_CLIENT_ATTEMPT",
    "BLOCKED_VENUE_API_CALL",
    "BLOCKED_UNACCEPTED_OFFICIAL_VENUE_SEMANTICS_CLAIM",
    "BLOCKED_SOURCE_RETRIEVAL_CREATION",
    "BLOCKED_SOURCE_ACCEPTANCE_CREATION",
    "BLOCKED_CONNECTOR_SEMANTIC_BINDING_CREATION",
    "BLOCKED_PRIVATE_STATE_FETCH",
    "BLOCKED_RUNTIME_CASH_AUTHORITY",
    "BLOCKED_ORDERBOOK_SNAPSHOT_CREATED",
    "BLOCKED_EVENT_STATE_SNAPSHOT_CREATED",
    "BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_CREATED",
    "BLOCKED_HISTORICAL_DATASET_DIGEST_CREATED",
    "BLOCKED_MARKET_DATA_FEATURE_VECTOR_CREATED",
    "BLOCKED_TRADING_SIGNAL_CREATED",
    "BLOCKED_SCORING_RANKING_ARBITRATION_OUTPUT_CREATED",
    "BLOCKED_ORDER_AUTHORITY_OR_EXECUTION",
    "BLOCKED_REPLAY_PAPER_LIVE_RESULT_CREATED",
    "BLOCKED_PROFIT_EVIDENCE_CREATED",
    "BLOCKED_NEURAL_TRAINING_INFERENCE",
    "BLOCKED_QUANTUM_EXECUTION",
    "BLOCKED_QUANTUM_FEATURE_COMPUTATION_CREATED",
    "BLOCKED_QUANTUM_OPTIMIZER_INPUT_CREATED",
    "BLOCKED_QUANTUM_TRADING_SIGNAL_CREATED",
    "BLOCKED_QUANTUM_ADVANTAGE_CLAIM_CREATED",
    "BLOCKED_ATOMICROWS_BUNDLE_SHA_MUTATION",
)

AUTHORITY_ZERO_FLAGS = (
    "source_retrieval_created",
    "source_acceptance_created",
    "connector_semantic_binding_created",
    "official_venue_semantics_fabricated",
    "live_market_data_fetch_created",
    "rest_client_created",
    "websocket_client_created",
    "venue_api_call_created",
    "network_io_created",
    "credential_provider_called",
    "live_credential_resolution_performed",
    "raw_secret_capture_created",
    "production_connector_authority_created",
    "private_state_fetch_created",
    "runtime_cash_authority_created",
    "orderbook_snapshot_created",
    "event_state_snapshot_created",
    "runtime_resolver_snapshot_created",
    "historical_dataset_digest_created",
    "market_data_feature_vector_created",
    "trading_signal_created",
    "scoring_ranking_arbitration_output_created",
    "order_authority_created",
    "order_execution_created",
    "replay_result_created",
    "paper_result_created",
    "profit_evidence_created",
    "neural_training_created",
    "neural_inference_created",
    "atomicrows_bundle_consumed",
    "atomicrows_bundle_created",
    "atomicrows_sha_created",
    *tuple(QUANTUM_ZERO_AUTHORITY_FLAGS),
)

ZERO_COUNT_INVARIANTS = (
    "live_market_data_fetch_count",
    "rest_client_created_count",
    "websocket_client_created_count",
    "venue_api_call_count",
    "network_io_count",
    "credential_provider_call_count",
    "live_credential_resolution_count",
    "private_state_fetch_count",
    "runtime_cash_authority_count",
    "orderbook_snapshot_created_count",
    "event_state_snapshot_created_count",
    "runtime_resolver_snapshot_created_count",
    "historical_dataset_digest_created_count",
    "feature_vector_created_count",
    "trading_signal_created_count",
    "scoring_ranking_arbitration_output_created_count",
    "quantum_feature_computation_count",
    "quantum_optimizer_input_created_count",
    "quantum_trading_signal_created_count",
    "quantum_backend_simulator_optimizer_execution_count",
    "quantum_advantage_claim_created_count",
    "order_authority_count",
    "order_execution_count",
    "replay_result_count",
    "paper_result_count",
    "profit_evidence_count",
    "neural_training_inference_count",
    "atomicrows_bundle_consumed_count",
    "atomicrows_bundle_created_count",
    "atomicrows_bundle_edited_count",
    "atomicrows_sha_created_count",
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

DISALLOWED_USE = (
    "LIVE_MARKET_DATA_FETCH",
    "LIVE_WEBSOCKET_SUBSCRIBE",
    "VENUE_API_CALL",
    "PRODUCTION_CONNECTOR_CLIENT",
    "ORDERBOOK_SNAPSHOT_BUILD",
    "EVENT_STATE_SNAPSHOT_BUILD",
    "RUNTIME_RESOLVER_SNAPSHOT_CREATE",
    "HISTORICAL_DATASET_DIGEST_CREATE",
    "MARKET_DATA_FEATURE_VECTOR_CREATE",
    "TRADING_SIGNAL_CREATE",
    "QUANTUM_FEATURE_COMPUTE",
    "QUANTUM_OPTIMIZER_INPUT_CREATE",
    "QUANTUM_TRADING_SIGNAL_CREATE",
    "ORDER_SUBMISSION",
    "ORDER_CANCELLATION",
    "ORDER_REDUCTION",
    "ORDER_CLOSE",
)


@dataclass(frozen=True)
class ScopeRef:
    scope_kind: str
    value: str

    @property
    def field_name(self) -> str:
        return "venue_id" if self.scope_kind == "venue" else "scope_id"

    @property
    def label(self) -> str:
        return self.value


def stage1_scope_refs() -> tuple[ScopeRef, ...]:
    return tuple(ScopeRef("venue", venue_id) for venue_id in STAGE1_VENUE_IDS) + tuple(
        ScopeRef("shared_scope", scope_id) for scope_id in SHARED_SCOPE_IDS
    )


def zero_authority_flags() -> dict[str, bool]:
    return {field: False for field in AUTHORITY_ZERO_FLAGS}


def zero_count_invariants() -> dict[str, int]:
    return {field: 0 for field in ZERO_COUNT_INVARIANTS}


def quantum_metadata() -> dict[str, object]:
    return {
        "future_quantum_feature_encoding_ref": (
            "FUTURE_PR135_QUANTUM_FEATURE_ENCODING_MARKET_DATA_REF_METADATA_ONLY"
        ),
        "future_quantum_optimizer_market_data_feature_ref": (
            "FUTURE_QTT_QUANTUM_OPTIMIZER_MARKET_DATA_FEATURE_REF_METADATA_ONLY"
        ),
        "future_quantum_market_microstructure_feature_family_ref": (
            "FUTURE_QUANTUM_MARKET_MICROSTRUCTURE_FEATURE_FAMILY_REF_METADATA_ONLY"
        ),
        "future_qaoa_qubo_market_state_encoding_ref": (
            "FUTURE_QAOA_QUBO_MARKET_STATE_ENCODING_REF_METADATA_ONLY"
        ),
        "future_quantum_kernel_market_regime_feature_ref": (
            "FUTURE_QUANTUM_KERNEL_MARKET_REGIME_FEATURE_REF_METADATA_ONLY"
        ),
        "future_quantum_annealing_liquidity_state_ref": (
            "FUTURE_QUANTUM_ANNEALING_LIQUIDITY_STATE_REF_METADATA_ONLY"
        ),
        "quantum_ready_market_data_contract": True,
    }


def atomicrows_metadata() -> dict[str, object]:
    return {
        "future_atomicrows_market_data_feature_row_refs": [],
        "future_atomicrows_parameter_row_refs": [],
        "future_atomicrows_family_refs": [],
        "future_atomicrows_quantum_feature_family_refs": [],
        "atomicrows_row_records_created_count": 0,
        "atomicrows_authority_created": False,
    }


def common_record_fields(record_type: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": record_type,
        "created_by": CREATED_BY,
        "authority_class": PACKAGE_AUTHORITY_CLASS,
        **zero_authority_flags(),
        **quantum_metadata(),
        **atomicrows_metadata(),
    }


def scope_field(scope_ref: ScopeRef) -> dict[str, str]:
    return {scope_ref.field_name: scope_ref.value}
