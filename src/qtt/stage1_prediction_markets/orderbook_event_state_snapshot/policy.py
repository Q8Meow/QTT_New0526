from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
    NoEffectFlagsV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PITAnchorStateV1,
    PITAvailabilityStateV2,
    PITContinuityStateV3,
    PITDataContractErrorV1,
    PITDepthClassV2,
    PITEventDispositionV1,
    PITIntegrityStateV1,
    PITReasonCodeV1,
    PITTransportStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    Stage1VenueProfileIdV1,
)


LEGACY_V1_FIXTURE_VENUE_IDS = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
STAGE1_VENUE_IDS = LEGACY_V1_FIXTURE_VENUE_IDS
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

SCHEMA_COMMON_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "record_type",
        "created_by",
        "authority_class",
    }
)

LEGACY_PR133_V1_SHARED_REQUIRED_FIELDS = frozenset(
    {
        *SCHEMA_COMMON_REQUIRED_FIELDS,
        "venue_id",
        "scope_id",
        *AUTHORITY_ZERO_FLAGS,
        *QUANTUM_FORWARD_SNAPSHOT_METADATA_FIELDS,
        *ATOMICROWS_PRE_BRIDGE_METADATA_FIELDS,
    }
)

LEGACY_PR133_V1_REQUIRED_FIELDS_BY_RECORD_TYPE = MappingProxyType(
    {
        "ORDERBOOK_EVENT_STATE_SNAPSHOT_INPUT_LOCK": frozenset(
            {
                *LEGACY_PR133_V1_SHARED_REQUIRED_FIELDS,
                "input_lock_id",
                "market_data_ingest_handoff_ref",
                "canonical_market_data_ingest_event_refs",
                "accepted_source_dependency_refs",
                "connector_semantic_dependency_refs",
                "credential_readiness_dependency_ref",
                "source_dependency_state",
                "snapshot_input_class",
                "input_payload_is_synthetic",
                "input_contains_live_market_data",
                "input_contains_official_venue_semantic_values",
                "deterministic_sequence_id",
                "snapshot_build_allowed",
                "live_snapshot_build_allowed",
                "runtime_resolver_snapshot_allowed",
                "historical_dataset_digest_allowed",
                "input_lock_required_for_each_snapshot",
            }
        ),
        "ORDERBOOK_SNAPSHOT_RECORD": frozenset(
            {
                *LEGACY_PR133_V1_SHARED_REQUIRED_FIELDS,
                "snapshot_id",
                "snapshot_input_lock_ref",
                "snapshot_class",
                "deterministic_sequence_id",
                "synthetic_depth_level_refs",
                "synthetic_depth_level_id",
                "depth_levels",
                "canonical_depth_side",
                "canonical_price_rank",
                "canonical_quantity_rank",
                "canonical_sort_key",
                "qtt_internal_orderbook_side_class",
                "qtt_internal_price_level_class",
                "qtt_internal_quantity_level_class",
                "official_venue_field_value_source_state",
                "fixture_orderbook_snapshot_created",
                "crossed_book_valid_trading_evidence_created",
                "orderbook_snapshot_is_trading_signal",
                "orderbook_snapshot_is_feature_vector",
                "orderbook_snapshot_is_quantum_feature_vector",
                "orderbook_snapshot_is_atomicrows_row",
                "orderbook_snapshot_is_order_authority",
                "orderbook_snapshot_is_runtime_resolver_snapshot",
                "no_live_fetch",
                "no_network_io",
                "no_order_authority",
                "no_profit_evidence",
                "no_quantum_execution",
            }
        ),
        "EVENT_STATE_SNAPSHOT_RECORD": frozenset(
            {
                *LEGACY_PR133_V1_SHARED_REQUIRED_FIELDS,
                "snapshot_id",
                "snapshot_input_lock_ref",
                "snapshot_class",
                "deterministic_sequence_id",
                "synthetic_event_state_refs",
                "synthetic_event_state_id",
                "event_states",
                "canonical_event_state_rank",
                "canonical_sort_key",
                "qtt_internal_event_status_class",
                "qtt_internal_lifecycle_state_class",
                "qtt_internal_settlement_state_class",
                "official_venue_field_value_source_state",
                "fixture_event_state_snapshot_created",
                "event_state_snapshot_is_trading_signal",
                "event_state_snapshot_is_feature_vector",
                "event_state_snapshot_is_quantum_feature_vector",
                "event_state_snapshot_is_atomicrows_row",
                "event_state_snapshot_is_order_authority",
                "event_state_snapshot_is_runtime_resolver_snapshot",
                "no_live_fetch",
                "no_network_io",
                "no_order_authority",
                "no_profit_evidence",
                "no_quantum_execution",
            }
        ),
        "ORDERBOOK_EVENT_STATE_SNAPSHOT_BUILDER_BINDING": frozenset(
            {
                *LEGACY_PR133_V1_SHARED_REQUIRED_FIELDS,
                "binding_id",
                "builder_name",
                "builder_version",
                "builder_scope",
                "input_lock_refs",
                "orderbook_snapshot_refs",
                "event_state_snapshot_refs",
                "market_data_ingest_handoff_ref",
                "credential_readiness_handoff_ref",
                "source_dependency_refs",
                "connector_semantic_dependency_refs",
                "orderbook_canonical_sort_rules_ref",
                "event_state_canonical_sort_rules_ref",
                "allowed_use",
                "disallowed_use",
                "future_live_use_requires_owner_approval",
                "future_live_use_requires_accepted_source_packet",
                "future_live_use_requires_fresh_revalidation_state",
                "future_live_use_requires_connector_semantic_binding",
                "future_live_use_requires_credential_provider_receipt_if_credentials_needed",
                "future_runtime_resolver_use_requires_pr134_authorization",
                "future_historical_dataset_use_requires_pr135_authorization",
                "future_atomicrows_bridge_requires_post_pr135_owner_authorization",
                "future_atomicrows_bundle_sha_requires_explicit_owner_authorization",
                "future_quantum_use_requires_pr116_pr117_data_chain",
                "future_quantum_use_requires_replay_paper_validation",
                "future_quantum_use_requires_owner_approval",
            }
        ),
        "ORDERBOOK_EVENT_STATE_SNAPSHOT_INTEGRITY_RECEIPT": frozenset(
            {
                *LEGACY_PR133_V1_SHARED_REQUIRED_FIELDS,
                "integrity_receipt_id",
                "snapshot_builder_binding_ref",
                "orderbook_snapshot_refs",
                "event_state_snapshot_refs",
                "deterministic_sorting_verified",
                "canonical_sequence_verified",
                "bid_side_sorting_verified",
                "ask_side_sorting_verified",
                "event_state_sorting_verified",
                "duplicate_synthetic_depth_level_id_count",
                "duplicate_synthetic_event_state_id_count",
                "duplicate_orderbook_snapshot_id_count",
                "duplicate_event_state_snapshot_id_count",
                "duplicate_canonical_sort_key_count",
                "invalid_orderbook_side_count",
                "invalid_event_lifecycle_state_count",
                "missing_snapshot_input_lock_count",
                "crossed_book_trading_evidence_created_count",
                "cross_venue_scope_mismatch_count",
                "live_market_payload_count",
                "official_semantics_fabricated_count",
                "runtime_resolver_snapshot_created_count",
                "historical_dataset_digest_created_count",
                "feature_vector_created_count",
                "trading_signal_created_count",
                "quantum_snapshot_feature_computation_created_count",
                "quantum_optimizer_input_created_count",
                "quantum_trading_signal_created_count",
                "atomicrows_bundle_created_count",
                "atomicrows_sha_created_count",
                "atomicrows_4183_completion_claim_created_count",
                "order_authority_count",
                "order_execution_count",
            }
        ),
        "ORDERBOOK_EVENT_STATE_SNAPSHOT_REJECTION": frozenset(
            {
                *LEGACY_PR133_V1_SHARED_REQUIRED_FIELDS,
                "rejection_id",
                "rejected_action_or_payload_class",
                "rejected_reason_code",
                "rejected_artifact_ref",
                "raw_live_payload_stored",
                "live_fetch_performed",
                "source_fact_accepted",
                "connector_semantic_binding_created",
                "official_semantics_fabricated",
                "feature_vector_created",
                "crossed_book_trading_evidence_created",
                "duplicate_depth_level_allowed",
                "duplicate_snapshot_id_allowed",
                "invalid_event_lifecycle_state_allowed",
                "missing_snapshot_input_lock_allowed",
                "validator_fail_closed",
            }
        ),
        "ORDERBOOK_EVENT_STATE_SNAPSHOT_DOWNSTREAM_HANDOFF": frozenset(
            {
                *LEGACY_PR133_V1_SHARED_REQUIRED_FIELDS,
                "handoff_id",
                "producer_pr",
                "producer_roadmap_pr",
                "upstream_prs",
                "downstream_prs",
                "venue_specific_scope",
                "shared_scope",
                "contains_fixture_orderbook_snapshot",
                "contains_fixture_event_state_snapshot",
                "contains_live_orderbook_snapshot",
                "contains_live_event_state_snapshot",
                "contains_live_market_data",
                "contains_live_credentials",
                "contains_private_state_payload",
                "contains_runtime_resolver_snapshot",
                "contains_historical_dataset_digest",
                "contains_feature_vector",
                "contains_trading_signal",
                "contains_quantum_feature_vector",
                "contains_quantum_optimizer_input",
                "contains_quantum_trading_signal",
                "contains_order_authority",
                "contains_profit_evidence",
                "contains_quantum_execution",
                "contains_atomicrows_materialized_rows",
                "contains_atomicrows_bundle",
                "contains_atomicrows_sha",
                "orderbook_canonicalization_verified",
                "event_state_canonicalization_verified",
                "downstream_pr116_contract_prepared",
                "downstream_pr116_execution_authorized",
                "downstream_pr117_contract_prepared",
                "downstream_pr117_execution_authorized",
                "downstream_quantum_feature_computation_authorized",
                "downstream_quantum_optimizer_input_creation_authorized",
                "downstream_quantum_trading_signal_creation_authorized",
                "downstream_atomicrows_bridge_authorized_now",
                "downstream_atomicrows_bridge_recommended_after_pr135",
                "downstream_atomicrows_bundle_sha_authorized_now",
            }
        ),
        "ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_RECORD": frozenset(
            {
                *LEGACY_PR133_V1_SHARED_REQUIRED_FIELDS,
                "compatibility_id",
                "producer_pr",
                "producer_roadmap_pr",
                "snapshot_builder_binding_ref",
                "orderbook_snapshot_refs",
                "event_state_snapshot_refs",
                "compatibility_class",
                "bridge_may_consume_after_pr135",
                "bridge_materialization_authorized_now",
                "bundle_materialization_authorized_now",
                "sha_freeze_authorized_now",
            }
        ),
    }
)

PIT_V2_REQUIRED_FIELDS_BY_RECORD_TYPE = MappingProxyType(
    {
        "PIT_ORDERBOOK_STATE": frozenset(
            {
                *SCHEMA_COMMON_REQUIRED_FIELDS,
                "state_id",
                "profile_id",
                "market_id",
                "instrument_id",
                "capture_session_id",
                "connection_epoch",
                "wire_dialect",
                "levels",
                "last_provider_sequence_start_or_none",
                "last_provider_sequence_end_or_none",
                "provider_subscription_id_or_none",
                "retained_provider_event_content",
                "last_completed_event_ordinal",
                "state_vector",
                "source_receipt_ref",
                "rights_receipt_ref",
                "no_effect_flags",
            }
        ),
        "PIT_EVENT_STATE_SNAPSHOT": frozenset(
            {
                *SCHEMA_COMMON_REQUIRED_FIELDS,
                "state_id",
                "profile_id",
                "market_id",
                "instrument_id",
                "capture_session_id",
                "connection_epoch",
                "wire_dialect",
                "last_completed_event_ordinal",
                "state_vector",
                "source_receipt_ref",
                "rights_receipt_ref",
                "no_effect_flags",
            }
        ),
        "PIT_RECONSTRUCTION_INPUT_LOCK": frozenset(
            {
                *SCHEMA_COMMON_REQUIRED_FIELDS,
                "lock_id",
                "profile_id",
                "market_id",
                "instrument_id",
                "capture_session_id",
                "connection_epoch",
                "wire_dialect",
                "first_completed_event_ordinal",
                "last_completed_event_ordinal",
                "provider_sequence_start_or_none",
                "provider_sequence_end_or_none",
                "process_epoch_id",
                "monotonic_clock_id",
                "source_receipt_ref",
                "rights_receipt_ref",
                "commit_completion_refs",
                "state_ref",
                "state_vector",
                "reconstruction_receipt_ref",
                "capability_context_id",
                "serializer_version",
                "no_effect_flags",
            }
        ),
        "PIT_SNAPSHOT_DOWNSTREAM_HANDOFF": frozenset(
            {
                *SCHEMA_COMMON_REQUIRED_FIELDS,
                "handoff_id",
                "profile_id",
                "state_ref",
                "state",
                "reconstruction_receipt",
                "reconstruction_input_lock",
                "availability_receipt",
                "canonical_event_ref",
                "capture_and_gap_receipt_ref",
                "commit_completion_ref",
                "provider_sequence_available",
                "provider_publication_time_available",
                "change_level_history_available",
                "full_depth_available",
                "durable_strategy_admission_available",
                "no_network_effect",
                "no_outbox_or_order_effect",
                "no_capital_or_private_state_effect",
                "no_llm_or_quantum_effect",
                "no_effect_flags",
            }
        ),
    }
)

PIT_V2_DISCRIMINATOR_BY_LEGACY_V1_RECORD_TYPE = MappingProxyType(
    {
        "ORDERBOOK_SNAPSHOT_RECORD": (
            "PIT_ORDERBOOK_SNAPSHOT_V2",
            "PIT_ORDERBOOK_STATE",
        ),
        "EVENT_STATE_SNAPSHOT_RECORD": (
            "PIT_EVENT_STATE_SNAPSHOT_V2",
            "PIT_EVENT_STATE_SNAPSHOT",
        ),
        "ORDERBOOK_EVENT_STATE_SNAPSHOT_BUILDER_BINDING": (
            "PIT_RECONSTRUCTION_INPUT_LOCK_V2",
            "PIT_RECONSTRUCTION_INPUT_LOCK",
        ),
        "ORDERBOOK_EVENT_STATE_SNAPSHOT_DOWNSTREAM_HANDOFF": (
            "PIT_SNAPSHOT_DOWNSTREAM_HANDOFF_V2",
            "PIT_SNAPSHOT_DOWNSTREAM_HANDOFF",
        ),
    }
)

PIT_V2_SELECTED_PROFILE_IDS = (
    Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT.value,
    Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT.value,
    Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT.value,
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


def _pit_state_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PITDataContractErrorV1(
            PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
            f"{name} must be canonical nonempty text",
        )
    return value


def _derive_pit_availability_v2(
    *,
    transport_state: PITTransportStateV1,
    anchor_state: PITAnchorStateV1,
    continuity_state: PITContinuityStateV3,
    integrity_state: PITIntegrityStateV1,
    depth_class: PITDepthClassV2,
    lifecycle_state: str,
) -> PITAvailabilityStateV2:
    _pit_state_text(lifecycle_state, "lifecycle_state")
    if lifecycle_state != "ADMISSIBLE":
        return PITAvailabilityStateV2.LIFECYCLE_BLOCKED
    if transport_state is PITTransportStateV1.HEARTBEAT_OVERDUE:
        return PITAvailabilityStateV2.STALE
    if transport_state is not PITTransportStateV1.CONNECTED_HEALTHY:
        return PITAvailabilityStateV2.UNAVAILABLE
    if anchor_state is not PITAnchorStateV1.ANCHOR_ACCEPTED:
        return PITAvailabilityStateV2.UNAVAILABLE
    if integrity_state is not PITIntegrityStateV1.VALID:
        return PITAvailabilityStateV2.UNAVAILABLE
    if continuity_state is PITContinuityStateV3.CONTIGUOUS:
        if depth_class is PITDepthClassV2.INCREMENTAL_FROM_COMPLETE_ANCHOR:
            return PITAvailabilityStateV2.AVAILABLE_CHANGE_LEVEL
        return PITAvailabilityStateV2.AVAILABLE_CURRENT_STATE
    if continuity_state in {
        PITContinuityStateV3.NOT_APPLICABLE_CURRENT_STATE_FRAME,
        PITContinuityStateV3.SEQUENCE_UNAVAILABLE,
    }:
        return PITAvailabilityStateV2.AVAILABLE_CURRENT_STATE
    return PITAvailabilityStateV2.UNAVAILABLE


@dataclass(frozen=True, slots=True)
class PITStateVectorV1:
    transport_state: PITTransportStateV1
    anchor_state: PITAnchorStateV1
    continuity_state: PITContinuityStateV3
    integrity_state: PITIntegrityStateV1
    availability_state: PITAvailabilityStateV2
    event_disposition: PITEventDispositionV1
    depth_class: PITDepthClassV2
    lifecycle_state: str

    def __post_init__(self) -> None:
        for name, enum_type in (
            ("transport_state", PITTransportStateV1),
            ("anchor_state", PITAnchorStateV1),
            ("continuity_state", PITContinuityStateV3),
            ("integrity_state", PITIntegrityStateV1),
            ("availability_state", PITAvailabilityStateV2),
            ("event_disposition", PITEventDispositionV1),
            ("depth_class", PITDepthClassV2),
        ):
            if type(getattr(self, name)) is not enum_type:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} has the wrong exact enum type",
                )
        _pit_state_text(self.lifecycle_state, "lifecycle_state")
        expected = _derive_pit_availability_v2(
            transport_state=self.transport_state,
            anchor_state=self.anchor_state,
            continuity_state=self.continuity_state,
            integrity_state=self.integrity_state,
            depth_class=self.depth_class,
            lifecycle_state=self.lifecycle_state,
        )
        if self.availability_state is not expected:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_CAPABILITY_UNAVAILABLE,
                "availability must equal the one canonical state reducer",
            )


@dataclass(frozen=True, slots=True)
class PITBookTransitionPolicyV2:
    policy_id: str
    profile_id: Stage1VenueProfileIdV1
    provider_sequence_required: bool
    current_state_without_sequence_allowed: bool
    absolute_update_semantics: bool
    signed_delta_semantics: bool
    locked_book_allowed: bool
    crossed_book_allowed: bool
    duplicate_requires_canonical_equality: bool
    forward_gap_requires_reanchor: bool
    no_effect_flags: NoEffectFlagsV1 = NO_EFFECTS_V1

    def __post_init__(self) -> None:
        _pit_state_text(self.policy_id, "policy_id")
        if type(self.profile_id) is not Stage1VenueProfileIdV1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCOPE_NOT_SELECTED,
                "transition policy profile has the wrong exact type",
            )
        for name in (
            "provider_sequence_required",
            "current_state_without_sequence_allowed",
            "absolute_update_semantics",
            "signed_delta_semantics",
            "locked_book_allowed",
            "crossed_book_allowed",
            "duplicate_requires_canonical_equality",
            "forward_gap_requires_reanchor",
        ):
            if type(getattr(self, name)) is not bool:
                raise PITDataContractErrorV1(
                    PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                    f"{name} must be an exact boolean",
                )
        if self.crossed_book_allowed or not self.locked_book_allowed:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_BOOK_CROSSED_INVALID,
                "transition policy must accept locked and reject crossed books",
            )
        if (
            self.provider_sequence_required
            == self.current_state_without_sequence_allowed
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_PROVIDER_SEQUENCE_UNAVAILABLE,
                "sequence-required and sequence-unavailable modes must be exclusive",
            )
        if self.absolute_update_semantics and self.signed_delta_semantics:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SCHEMA_OR_WIRE_DIALECT_INVALID,
                "one profile cannot reinterpret absolute updates as signed deltas",
            )
        if (
            not self.duplicate_requires_canonical_equality
            or not self.forward_gap_requires_reanchor
        ):
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_SEQUENCE_GAP,
                "duplicate equality and gap reanchor controls are mandatory",
            )
        if type(self.no_effect_flags) is not NoEffectFlagsV1 or self.no_effect_flags != NO_EFFECTS_V1:
            raise PITDataContractErrorV1(
                PITReasonCodeV1.PIT_EFFECT_AUTHORITY_FORBIDDEN,
                "transition policy must carry exact NO_EFFECTS_V1",
            )


PIT_BOOK_TRANSITION_POLICIES_V2 = MappingProxyType({
    Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: PITBookTransitionPolicyV2(
        policy_id="S1-PIT-BOOK-POLICY::GEMINI-TITAN::V2",
        profile_id=Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT,
        provider_sequence_required=True,
        current_state_without_sequence_allowed=False,
        absolute_update_semantics=True,
        signed_delta_semantics=False,
        locked_book_allowed=True,
        crossed_book_allowed=False,
        duplicate_requires_canonical_equality=True,
        forward_gap_requires_reanchor=True,
    ),
    Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: PITBookTransitionPolicyV2(
        policy_id="S1-PIT-BOOK-POLICY::POLYMARKET-US-RETAIL::V2",
        profile_id=Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT,
        provider_sequence_required=False,
        current_state_without_sequence_allowed=True,
        absolute_update_semantics=False,
        signed_delta_semantics=False,
        locked_book_allowed=True,
        crossed_book_allowed=False,
        duplicate_requires_canonical_equality=True,
        forward_gap_requires_reanchor=True,
    ),
    Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: PITBookTransitionPolicyV2(
        policy_id="S1-PIT-BOOK-POLICY::KALSHI-US-DCM::V2",
        profile_id=Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT,
        provider_sequence_required=True,
        current_state_without_sequence_allowed=False,
        absolute_update_semantics=False,
        signed_delta_semantics=True,
        locked_book_allowed=True,
        crossed_book_allowed=False,
        duplicate_requires_canonical_equality=True,
        forward_gap_requires_reanchor=True,
    ),
})
