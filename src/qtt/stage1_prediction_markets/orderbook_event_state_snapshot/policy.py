from __future__ import annotations

from dataclasses import dataclass
from typing import Any


STAGE1_VENUE_IDS = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
SHARED_SCOPE_IDS = ("PREDICTION_MARKETS_GENERAL",)

PRODUCER_REPO_PR = "PR133"
PRODUCER_ROADMAP_PR = "PR115"
UPSTREAM_REPO_PR = "PR132"
UPSTREAM_ROADMAP_PR = "PR114"
UPSTREAM_MARKET_DATA_INGEST_PACKAGE = (
    "src/qtt/stage1_prediction_markets/market_data_ingest"
)
DOWNSTREAM_PR_IDS = ("PR116", "PR117")
RECOMMENDED_ATOMICROWS_BRIDGE_AFTER_REPO_PR = "PR135"
RECOMMENDED_ATOMICROWS_BRIDGE_CANDIDATE_REPO_PR = "PR136"

PACKAGE_AUTHORITY_CLASS = (
    "FIXTURE_BACKED_ORDERBOOK_EVENT_STATE_SNAPSHOT_CONTRACT_ONLY_NOT_LIVE_OR_RUNTIME_AUTHORITY"
)
CREATED_BY = "CODEX_PR133_FIXTURE_OR_VALIDATOR"
SCHEMA_VERSION = "PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_SCHEMA_V1"

ALLOWED_SNAPSHOT_INPUT_CLASSES = (
    "SYNTHETIC_FIXTURE_MARKET_DATA_INGEST_INPUT",
    "PR132_MARKET_DATA_INGEST_HANDOFF_INPUT",
    "ACCEPTED_SOURCE_GATED_SNAPSHOT_INPUT_METADATA",
    "SOURCE_REQUIRED_SNAPSHOT_INPUT_PLACEHOLDER",
    "CONNECTOR_SEMANTIC_REQUIRED_SNAPSHOT_INPUT_PLACEHOLDER",
)

ALLOWED_ORDERBOOK_SNAPSHOT_CLASSES = (
    "SYNTHETIC_FIXTURE_ORDERBOOK_SNAPSHOT",
    "QTT_INTERNAL_ORDERBOOK_DEPTH_METADATA_SNAPSHOT",
    "QTT_INTERNAL_BBO_METADATA_SNAPSHOT",
    "QTT_INTERNAL_LIQUIDITY_METADATA_SNAPSHOT",
    "SOURCE_REQUIRED_ORDERBOOK_SNAPSHOT_PLACEHOLDER",
    "CONNECTOR_SEMANTIC_REQUIRED_ORDERBOOK_SNAPSHOT_PLACEHOLDER",
)

ALLOWED_EVENT_STATE_SNAPSHOT_CLASSES = (
    "SYNTHETIC_FIXTURE_EVENT_STATE_SNAPSHOT",
    "QTT_INTERNAL_MARKET_STATUS_METADATA_SNAPSHOT",
    "QTT_INTERNAL_SETTLEMENT_STATUS_METADATA_SNAPSHOT",
    "QTT_INTERNAL_VENUE_HEALTH_METADATA_SNAPSHOT",
    "QTT_INTERNAL_EVENT_LIFECYCLE_METADATA_SNAPSHOT",
    "SOURCE_REQUIRED_EVENT_STATE_SNAPSHOT_PLACEHOLDER",
    "CONNECTOR_SEMANTIC_REQUIRED_EVENT_STATE_SNAPSHOT_PLACEHOLDER",
)

ALLOWED_SOURCE_DEPENDENCY_STATES = (
    "ACCEPTED_SOURCE_GATED",
    "CONNECTOR_SEMANTIC_GATED",
    "SOURCE_REQUIRED",
    "CONNECTOR_SEMANTIC_REQUIRED",
    "BLOCKED_SCOPE_MISMATCH",
)

ALLOWED_CANONICAL_DEPTH_SIDES = (
    "BID_METADATA",
    "ASK_METADATA",
    "UNKNOWN_SOURCE_REQUIRED",
)

ALLOWED_EVENT_LIFECYCLE_STATUS_CLASSES = (
    "OPEN_METADATA",
    "PAUSED_METADATA",
    "CLOSED_METADATA",
    "SETTLED_METADATA",
    "CANCELED_METADATA",
    "UNKNOWN_SOURCE_REQUIRED",
    "CONNECTOR_SEMANTIC_REQUIRED",
)

ORDERBOOK_CANONICAL_SORT_RULES = (
    {
        "canonical_depth_side": "BID_METADATA",
        "sort_rule": (
            "canonical_price_rank descending, then canonical_quantity_rank descending, "
            "then synthetic_depth_level_id ascending"
        ),
        "sort_tuple": (
            "-canonical_price_rank",
            "-canonical_quantity_rank",
            "synthetic_depth_level_id",
        ),
    },
    {
        "canonical_depth_side": "ASK_METADATA",
        "sort_rule": (
            "canonical_price_rank ascending, then canonical_quantity_rank descending, "
            "then synthetic_depth_level_id ascending"
        ),
        "sort_tuple": (
            "canonical_price_rank",
            "-canonical_quantity_rank",
            "synthetic_depth_level_id",
        ),
    },
    {
        "canonical_depth_side": "UNKNOWN_SOURCE_REQUIRED",
        "sort_rule": "synthetic_depth_level_id ascending",
        "sort_tuple": ("synthetic_depth_level_id",),
    },
)

EVENT_STATE_CANONICAL_SORT_RULES = (
    {
        "event_state_class": "KNOWN_LIFECYCLE_STATUS_METADATA",
        "sort_rule": (
            "canonical_event_state_rank ascending, then synthetic_event_state_id ascending"
        ),
        "sort_tuple": ("canonical_event_state_rank", "synthetic_event_state_id"),
    },
    {
        "event_state_class": "UNKNOWN_SOURCE_REQUIRED",
        "sort_rule": "sort after known lifecycle/status classes",
        "sort_after_known_status_classes": True,
    },
    {
        "event_state_class": "CONNECTOR_SEMANTIC_REQUIRED",
        "sort_rule": "sort after known lifecycle/status classes",
        "sort_after_known_status_classes": True,
    },
)

EVENT_LIFECYCLE_RANKS = {
    "OPEN_METADATA": 10,
    "PAUSED_METADATA": 20,
    "CLOSED_METADATA": 30,
    "SETTLED_METADATA": 40,
    "CANCELED_METADATA": 50,
    "UNKNOWN_SOURCE_REQUIRED": 90,
    "CONNECTOR_SEMANTIC_REQUIRED": 91,
}

QUANTUM_FORWARD_SNAPSHOT_METADATA_FIELDS = (
    "quantum_ready_snapshot_contract",
    "future_quantum_orderbook_state_encoding_ref",
    "future_qaoa_qubo_liquidity_state_encoding_ref",
    "future_quantum_kernel_event_state_regime_ref",
    "future_quantum_annealing_depth_imbalance_ref",
    "future_quantum_microstructure_graph_ref",
    "future_quantum_amplitude_encoding_snapshot_ref",
)

QUANTUM_ZERO_AUTHORITY_FLAGS = {
    "quantum_execution_created": False,
    "quantum_backend_called": False,
    "quantum_simulator_called": False,
    "quantum_optimizer_called": False,
    "quantum_snapshot_feature_computation_created": False,
    "quantum_optimizer_input_created": False,
    "quantum_trading_signal_created": False,
    "quantum_advantage_claim_created": False,
}

ATOMICROWS_PRE_BRIDGE_METADATA_FIELDS = (
    "atomicrows_pre_bridge_compatibility_metadata_created",
    "future_atomicrows_snapshot_feature_row_refs",
    "future_atomicrows_orderbook_depth_feature_family_refs",
    "future_atomicrows_event_state_feature_family_refs",
    "future_atomicrows_market_data_feature_row_refs",
    "future_atomicrows_quantum_snapshot_feature_family_refs",
    "future_atomicrows_parameter_row_refs",
    "future_atomicrows_family_refs",
    "future_atomicrows_bridge_after_pr135_ref",
    "future_atomicrows_bridge_recommended_after_repo_pr",
    "future_atomicrows_bridge_candidate_repo_pr",
)

ATOMICROWS_ZERO_AUTHORITY_FLAGS = {
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
    "LIVE_ORDERBOOK_SNAPSHOT_CREATE",
    "LIVE_EVENT_STATE_SNAPSHOT_CREATE",
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
    "QUANTUM_SNAPSHOT_FEATURE_COMPUTE",
    "QUANTUM_OPTIMIZER_INPUT_CREATE",
    "QUANTUM_TRADING_SIGNAL_CREATE",
    "QUANTUM_ADVANTAGE_CLAIM_CREATE",
    "ATOMICROWS_BUNDLE_CREATE",
    "ATOMICROWS_BUNDLE_EDIT",
    "ATOMICROWS_SHA_CREATE",
    "ATOMICROWS_ROW_RECORD_CREATE",
    "ATOMICROWS_BRIDGE_AUTHORITY_CREATE",
    "ATOMICROWS_4183_COMPLETION_CLAIM_CREATE",
)

ALLOWED_ACTION_IDS = (
    "READ_MANDATORY_ROADMAP_MASTER_PLAN_SOURCE_EVIDENCE_FILES",
    "INSPECT_PR105_TO_PR132_ARTIFACTS",
    "INSPECT_ATOMICROWS_AUTHORITY_ARTIFACTS_WITHOUT_MUTATION",
    "CREATE_PR133_SCHEMAS",
    "CREATE_PR133_FIXTURES",
    "CREATE_PR133_VALIDATORS",
    "CREATE_PR133_GENERATED_REPORTS",
    "CREATE_PR133_TESTS",
    "CREATE_FIXTURE_BACKED_SYNTHETIC_ORDERBOOK_SNAPSHOT_RECORDS",
    "CREATE_FIXTURE_BACKED_SYNTHETIC_EVENT_STATE_SNAPSHOT_RECORDS",
    "CREATE_DETERMINISTIC_ORDERBOOK_CANONICALIZATION_METADATA",
    "CREATE_DETERMINISTIC_EVENT_STATE_LIFECYCLE_CANONICALIZATION_METADATA",
    "CREATE_MALFORMED_CROSSED_BOOK_REJECTION_FIXTURE",
    "CREATE_QUANTUM_READY_SNAPSHOT_CONTRACT_METADATA_FIELDS",
    "CREATE_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_METADATA_FIELDS",
    "INTEGRATE_PR133_VALIDATOR_INTO_VALIDATION_GATES",
    "RUN_LOCAL_VALIDATION_COMMANDS",
)

REJECTION_REASON_CODES = (
    "BLOCKED_MISSING_PR132_MARKET_DATA_INGEST_HANDOFF",
    "BLOCKED_MALFORMED_PR132_MARKET_DATA_INGEST_HANDOFF",
    "BLOCKED_SCOPE_MISMATCH",
    "BLOCKED_LIVE_MARKET_DATA_FETCH",
    "BLOCKED_REST_CLIENT_ATTEMPT",
    "BLOCKED_WEBSOCKET_CLIENT_ATTEMPT",
    "BLOCKED_VENUE_API_CALL",
    "BLOCKED_UNACCEPTED_OFFICIAL_ORDERBOOK_EVENT_STATE_SEMANTICS",
    "BLOCKED_CREDENTIAL_PROVIDER_CALL",
    "BLOCKED_LIVE_CREDENTIAL_RESOLUTION",
    "BLOCKED_PRIVATE_STATE_FETCH",
    "BLOCKED_RUNTIME_CASH_AUTHORITY",
    "BLOCKED_LIVE_ORDERBOOK_SNAPSHOT_CREATED",
    "BLOCKED_LIVE_EVENT_STATE_SNAPSHOT_CREATED",
    "BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_CREATED",
    "BLOCKED_HISTORICAL_DATASET_DIGEST_CREATED",
    "BLOCKED_FEATURE_VECTOR_CREATED",
    "BLOCKED_TRADING_SIGNAL_CREATED",
    "BLOCKED_SCORING_RANKING_ARBITRATION_OUTPUT_CREATED",
    "BLOCKED_ORDER_AUTHORITY_OR_EXECUTION",
    "BLOCKED_REPLAY_PAPER_LIVE_RESULT_CREATED",
    "BLOCKED_PROFIT_EVIDENCE_CREATED",
    "BLOCKED_NEURAL_TRAINING_INFERENCE",
    "BLOCKED_QUANTUM_EXECUTION",
    "BLOCKED_QUANTUM_SNAPSHOT_FEATURE_COMPUTATION_CREATED",
    "BLOCKED_QUANTUM_OPTIMIZER_INPUT_CREATED",
    "BLOCKED_QUANTUM_TRADING_SIGNAL_CREATED",
    "BLOCKED_QUANTUM_ADVANTAGE_CLAIM_CREATED",
    "BLOCKED_ATOMICROWS_BUNDLE_SHA_MUTATION",
    "BLOCKED_ATOMICROWS_ROW_RECORD_CREATED",
    "BLOCKED_ATOMICROWS_BRIDGE_AUTHORITY_CREATED",
    "BLOCKED_ATOMICROWS_4183_COMPLETION_CLAIM_CREATED",
    "BLOCKED_DUPLICATE_DEPTH_LEVEL_ID",
    "BLOCKED_DUPLICATE_SNAPSHOT_ID",
    "BLOCKED_CROSSED_BOOK_TRADING_EVIDENCE_CLAIM",
    "BLOCKED_INVALID_EVENT_LIFECYCLE_STATE",
    "BLOCKED_MISSING_SNAPSHOT_INPUT_LOCK",
)

AUTHORITY_ZERO_FLAGS = (
    "source_retrieval_created",
    "source_acceptance_created",
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
    "live_orderbook_snapshot_created",
    "live_event_state_snapshot_created",
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
    *tuple(QUANTUM_ZERO_AUTHORITY_FLAGS),
    *tuple(ATOMICROWS_ZERO_AUTHORITY_FLAGS),
)

ZERO_COUNT_INVARIANTS = (
    "live_orderbook_snapshot_count",
    "live_event_state_snapshot_count",
    "duplicate_synthetic_depth_level_id_count",
    "duplicate_synthetic_event_state_id_count",
    "duplicate_orderbook_snapshot_id_count",
    "duplicate_event_state_snapshot_id_count",
    "duplicate_canonical_sort_key_count",
    "invalid_orderbook_side_count",
    "invalid_event_lifecycle_state_count",
    "missing_snapshot_input_lock_count",
    "crossed_book_trading_evidence_created_count",
    "live_market_data_fetch_count",
    "rest_client_created_count",
    "websocket_client_created_count",
    "venue_api_call_count",
    "network_io_count",
    "credential_provider_call_count",
    "live_credential_resolution_count",
    "private_state_fetch_count",
    "runtime_cash_authority_count",
    "runtime_resolver_snapshot_created_count",
    "historical_dataset_digest_created_count",
    "feature_vector_created_count",
    "trading_signal_created_count",
    "scoring_ranking_arbitration_output_created_count",
    "quantum_snapshot_feature_computation_count",
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
    "order_authority_count",
    "order_execution_count",
    "replay_result_count",
    "paper_result_count",
    "profit_evidence_count",
    "neural_training_inference_count",
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
    "LIVE_ORDERBOOK_SNAPSHOT_CREATE",
    "LIVE_EVENT_STATE_SNAPSHOT_CREATE",
    "RUNTIME_RESOLVER_SNAPSHOT_CREATE",
    "HISTORICAL_DATASET_DIGEST_CREATE",
    "MARKET_DATA_FEATURE_VECTOR_CREATE",
    "TRADING_SIGNAL_CREATE",
    "QUANTUM_SNAPSHOT_FEATURE_COMPUTE",
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


@dataclass(frozen=True)
class ScopeRef:
    scope_kind: str
    value: str

    @property
    def field_name(self) -> str:
        return "venue_id" if self.scope_kind == "venue" else "scope_id"


def stage1_scope_refs() -> tuple[ScopeRef, ...]:
    return tuple(ScopeRef("venue", value) for value in STAGE1_VENUE_IDS) + tuple(
        ScopeRef("shared_scope", value) for value in SHARED_SCOPE_IDS
    )


def zero_authority_flags() -> dict[str, Any]:
    return {
        field: ATOMICROWS_ZERO_AUTHORITY_FLAGS.get(
            field,
            QUANTUM_ZERO_AUTHORITY_FLAGS.get(field, False),
        )
        for field in AUTHORITY_ZERO_FLAGS
    }


def zero_count_invariants() -> dict[str, int]:
    return {field: 0 for field in ZERO_COUNT_INVARIANTS}


def quantum_metadata(scope_value: str = "PREDICTION_MARKETS_GENERAL") -> dict[str, object]:
    return {
        "quantum_ready_snapshot_contract": True,
        "future_quantum_orderbook_state_encoding_ref": (
            f"FUTURE_QUANTUM_ORDERBOOK_STATE_ENCODING_REF_METADATA_ONLY_{scope_value}"
        ),
        "future_qaoa_qubo_liquidity_state_encoding_ref": (
            f"FUTURE_QAOA_QUBO_LIQUIDITY_STATE_ENCODING_REF_METADATA_ONLY_{scope_value}"
        ),
        "future_quantum_kernel_event_state_regime_ref": (
            f"FUTURE_QUANTUM_KERNEL_EVENT_STATE_REGIME_REF_METADATA_ONLY_{scope_value}"
        ),
        "future_quantum_annealing_depth_imbalance_ref": (
            f"FUTURE_QUANTUM_ANNEALING_DEPTH_IMBALANCE_REF_METADATA_ONLY_{scope_value}"
        ),
        "future_quantum_microstructure_graph_ref": (
            f"FUTURE_QUANTUM_MICROSTRUCTURE_GRAPH_REF_METADATA_ONLY_{scope_value}"
        ),
        "future_quantum_amplitude_encoding_snapshot_ref": (
            f"FUTURE_QUANTUM_AMPLITUDE_ENCODING_SNAPSHOT_REF_METADATA_ONLY_{scope_value}"
        ),
    }


def atomicrows_metadata(scope_value: str = "PREDICTION_MARKETS_GENERAL") -> dict[str, object]:
    return {
        "atomicrows_pre_bridge_compatibility_metadata_created": True,
        "future_atomicrows_snapshot_feature_row_refs": [
            f"FUTURE_ATOMICROWS_SNAPSHOT_FEATURE_ROW_REF_METADATA_ONLY_{scope_value}"
        ],
        "future_atomicrows_orderbook_depth_feature_family_refs": [
            f"FUTURE_ATOMICROWS_ORDERBOOK_DEPTH_FEATURE_FAMILY_REF_METADATA_ONLY_{scope_value}"
        ],
        "future_atomicrows_event_state_feature_family_refs": [
            f"FUTURE_ATOMICROWS_EVENT_STATE_FEATURE_FAMILY_REF_METADATA_ONLY_{scope_value}"
        ],
        "future_atomicrows_market_data_feature_row_refs": [
            f"FUTURE_ATOMICROWS_MARKET_DATA_FEATURE_ROW_REF_METADATA_ONLY_{scope_value}"
        ],
        "future_atomicrows_quantum_snapshot_feature_family_refs": [
            f"FUTURE_ATOMICROWS_QUANTUM_SNAPSHOT_FEATURE_FAMILY_REF_METADATA_ONLY_{scope_value}"
        ],
        "future_atomicrows_parameter_row_refs": [
            f"FUTURE_ATOMICROWS_PARAMETER_ROW_REF_METADATA_ONLY_{scope_value}"
        ],
        "future_atomicrows_family_refs": [
            f"FUTURE_ATOMICROWS_FAMILY_REF_METADATA_ONLY_{scope_value}"
        ],
        "future_atomicrows_bridge_after_pr135_ref": (
            f"FUTURE_ATOMICROWS_BRIDGE_AFTER_PR135_REF_METADATA_ONLY_{scope_value}"
        ),
        "future_atomicrows_bridge_recommended_after_repo_pr": (
            RECOMMENDED_ATOMICROWS_BRIDGE_AFTER_REPO_PR
        ),
        "future_atomicrows_bridge_candidate_repo_pr": (
            RECOMMENDED_ATOMICROWS_BRIDGE_CANDIDATE_REPO_PR
        ),
    }


def common_record_fields(record_type: str, scope_value: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": record_type,
        "created_by": CREATED_BY,
        "authority_class": PACKAGE_AUTHORITY_CLASS,
        **zero_authority_flags(),
        **quantum_metadata(scope_value),
        **atomicrows_metadata(scope_value),
    }


def scope_field(scope_ref: ScopeRef) -> dict[str, str]:
    return {scope_ref.field_name: scope_ref.value}
