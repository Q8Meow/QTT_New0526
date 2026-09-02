from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    NO_EFFECTS_V1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.point_in_time import (
    PITAnchorStateV1,
    PITAvailabilityStateV2,
    PITContinuityStateV3,
    PITDepthClassV2,
    PITEventDispositionV1,
    PITEventKindV2,
    PITInputAvailabilityV2,
    PITIntegrityStateV1,
    PITTransportStateV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stage1_launch_graph import (
    STAGE1_SELECTED_SCOPE_V2,
    Stage1VenueProfileIdV1,
)


LEGACY_V1_FIXTURE_VENUE_IDS = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
STAGE1_VENUE_IDS = LEGACY_V1_FIXTURE_VENUE_IDS
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


LEGACY_V1_FIXTURE_SCOPE_IDS = SHARED_SCOPE_IDS
PIT_SELECTED_SCOPE_V2 = STAGE1_SELECTED_SCOPE_V2
PIT_SELECTED_PROFILE_IDS_V2 = PIT_SELECTED_SCOPE_V2.serialization
PIT_NO_EFFECT_FLAGS_V2 = NO_EFFECTS_V1


class PITAccessClassV1(StrEnum):
    PUBLIC_UNAUTHENTICATED_READ = "PUBLIC_UNAUTHENTICATED_READ"
    AUTHENTICATED_PUBLIC_MARKET_DATA_READ = (
        "AUTHENTICATED_PUBLIC_MARKET_DATA_READ"
    )


class PITReadActionV1(StrEnum):
    GET = "GET"
    WEBSOCKET_SUBSCRIBE = "WEBSOCKET_SUBSCRIBE"
    WEBSOCKET_UNSUBSCRIBE = "WEBSOCKET_UNSUBSCRIBE"
    WEBSOCKET_RECOVERY = "WEBSOCKET_RECOVERY"
    WEBSOCKET_PONG = "WEBSOCKET_PONG"


PIT_PRIVATE_FIELD_DENYLIST_V1 = frozenset(
    {
        "account",
        "account_balance",
        "account_id",
        "account_orders",
        "account_positions",
        "api_key",
        "authorization",
        "authorization_header",
        "balance",
        "client_order_id",
        "cookie",
        "credential",
        "fill",
        "fills",
        "order",
        "orders",
        "payment",
        "payment_method",
        "position",
        "positions",
        "private_fill",
        "private_key",
        "secret",
        "secret_key",
        "signature",
        "wallet",
        "wallet_address",
    }
)


_PIT_PROFILE_PROTOCOL_POLICY_V2: Mapping[
    Stage1VenueProfileIdV1, Mapping[str, object]
] = MappingProxyType(
    {
        Stage1VenueProfileIdV1.GEMINI_TITAN_DIRECT: MappingProxyType(
            {
                "production_rest_base": "https://api.gemini.com",
                "websocket_url": "wss://ws.gemini.com?snapshot=-1",
                "allowed_access_classes": (
                    PITAccessClassV1.PUBLIC_UNAUTHENTICATED_READ,
                ),
                "allowed_methods": (
                    PITReadActionV1.GET,
                    PITReadActionV1.WEBSOCKET_SUBSCRIBE,
                    PITReadActionV1.WEBSOCKET_UNSUBSCRIBE,
                ),
                "allowed_paths": ("/v1/prediction-markets/events",),
                "allowed_channels": (
                    "prediction_markets.depth",
                    "prediction_markets.bookTicker",
                    "prediction_markets.trades",
                ),
                "wire_dialect_policy": "GEMINI_TITAN_DIFFERENTIAL_DEPTH_V1",
                "sequence_model": "INTEGER_INCLUSIVE_RANGE_U_u",
                "snapshot_model": "FIRST_DIFFERENTIAL_DEPTH_FRAME_COMPLETE_ANCHOR",
                "recovery_model": "NEW_CONNECTION_EPOCH_AND_FRESH_FIRST_FRAME",
                "heartbeat_model": "QTT_MONOTONIC_TRANSPORT_WATCHDOG",
                "depth_class": PITDepthClassV2.INCREMENTAL_FROM_COMPLETE_ANCHOR,
                "credential_alias_required": False,
                "provider_publication_time_available": False,
            }
        ),
        Stage1VenueProfileIdV1.POLYMARKET_US_RETAIL_DIRECT: MappingProxyType(
            {
                "production_rest_base": "https://gateway.polymarket.us",
                "websocket_url": "wss://api.polymarket.us/v1/ws/markets",
                "allowed_access_classes": (
                    PITAccessClassV1.PUBLIC_UNAUTHENTICATED_READ,
                    PITAccessClassV1.AUTHENTICATED_PUBLIC_MARKET_DATA_READ,
                ),
                "allowed_methods": (
                    PITReadActionV1.GET,
                    PITReadActionV1.WEBSOCKET_SUBSCRIBE,
                    PITReadActionV1.WEBSOCKET_UNSUBSCRIBE,
                ),
                "allowed_paths": ("/v1/markets", "/v1/markets/{slug}/book"),
                "allowed_channels": ("markets",),
                "wire_dialect_policy": (
                    "CAMEL_CASE_STRING_ENUM_THEN_ONE_EXPLICIT_PRE_DATA_"
                    "ERROR_FALLBACK_TO_SNAKE_CASE_NUMERIC_ENUM"
                ),
                "sequence_model": "PROVIDER_NUMERIC_SEQUENCE_UNAVAILABLE",
                "snapshot_model": (
                    "NONMERGED_WEBSOCKET_TOP_LEVEL_REPLACEMENT_AND_REST_FULL_BOOK"
                ),
                "recovery_model": "NEW_EPOCH_DIALECT_LOCK_COMPLETE_FRAME_AND_PARITY",
                "heartbeat_model": "ADAPTIVE_MONOTONIC_OBSERVED_HEARTBEAT_DEADLINE",
                "depth_class": (
                    PITDepthClassV2.PROVIDER_PUBLISHED_TOP_LEVELS_CURRENT_STATE_FRAME
                ),
                "credential_alias_required": True,
                "provider_publication_time_available": False,
            }
        ),
        Stage1VenueProfileIdV1.KALSHI_US_DCM_DIRECT: MappingProxyType(
            {
                "production_rest_base": (
                    "https://external-api.kalshi.com/trade-api/v2"
                ),
                "websocket_url": (
                    "wss://external-api-ws.kalshi.com/trade-api/ws/v2"
                ),
                "allowed_access_classes": (
                    PITAccessClassV1.PUBLIC_UNAUTHENTICATED_READ,
                    PITAccessClassV1.AUTHENTICATED_PUBLIC_MARKET_DATA_READ,
                ),
                "allowed_methods": (
                    PITReadActionV1.GET,
                    PITReadActionV1.WEBSOCKET_SUBSCRIBE,
                    PITReadActionV1.WEBSOCKET_UNSUBSCRIBE,
                    PITReadActionV1.WEBSOCKET_RECOVERY,
                    PITReadActionV1.WEBSOCKET_PONG,
                ),
                "allowed_paths": (
                    "/markets",
                    "/markets/{ticker}/orderbook",
                    "/portfolio/account_limits",
                    "/historical/trades",
                ),
                "allowed_channels": (
                    "orderbook_delta",
                    "trade",
                    "market_lifecycle_v2",
                    "server_ping",
                ),
                "wire_dialect_policy": "KALSHI_TRADE_API_WS_V2_FIXED_POINT",
                "sequence_model": "INTEGER_sid_seq_EXACT_NEXT",
                "snapshot_model": "orderbook_snapshot_OR_get_snapshot_REPLACEMENT",
                "recovery_model": "get_snapshot_OR_NEW_SUBSCRIPTION_EPOCH",
                "heartbeat_model": "SERVER_PING_10_SECONDS_TWO_MISSES_PLUS_5_SECONDS",
                "depth_class": PITDepthClassV2.INCREMENTAL_FROM_COMPLETE_ANCHOR,
                "credential_alias_required": True,
                "provider_publication_time_available": False,
            }
        ),
    }
)


def _pit_profile_protocol_policy_v2(
    profile_id: Stage1VenueProfileIdV1,
) -> Mapping[str, object]:
    if type(profile_id) is not Stage1VenueProfileIdV1 or profile_id not in (
        PIT_SELECTED_SCOPE_V2.selected_profile_ids
    ):
        raise ValueError("profile is outside the exact selected PIT scope")
    return _PIT_PROFILE_PROTOCOL_POLICY_V2[profile_id]


@dataclass(frozen=True, slots=True)
class PITSafetySeedAndCalibrationEnvelopeV2:
    source_receipt_activation_age_hours: int = 24
    gemini_public_rest_ceiling_per_minute: int = 120
    gemini_ordinary_rest_target_per_second: Decimal = Decimal("1")
    gemini_recovery_reserve_fraction: Decimal = Decimal("0.50")
    gemini_transport_probe_seconds: int = 10
    gemini_transport_invalidation_seconds: int = 25
    polymarket_key_ceiling_per_second: int = 20
    polymarket_public_ip_ceiling_per_second: int = 20
    polymarket_recovery_reserve_fraction: Decimal = Decimal("0.25")
    polymarket_pre_observation_heartbeat_seconds: int = 30
    polymarket_heartbeat_floor_seconds: int = 10
    polymarket_heartbeat_cap_seconds: int = 120
    polymarket_backoff_base_seconds: Decimal = Decimal("1")
    kalshi_heartbeat_invalidation_seconds: int = 25
    kalshi_recovery_reserve_fraction: Decimal = Decimal("0.50")
    checkpoint_event_threshold: int = 10_000
    checkpoint_time_threshold_seconds: int = 30
    raw_volatile_memory_ring_minutes: int = 15
    wall_clock_uncertainty_target_ns: int = 5_000_000
    normalized_retention_hot_days: int = 90
    normalized_retention_warm_days: int = 365
    live_self_tuning_allowed: bool = False

    def __post_init__(self) -> None:
        integer_ranges = {
            "source_receipt_activation_age_hours": (0, 24),
            "gemini_public_rest_ceiling_per_minute": (120, 120),
            "gemini_transport_probe_seconds": (5, 30),
            "gemini_transport_invalidation_seconds": (15, 60),
            "polymarket_key_ceiling_per_second": (20, 20),
            "polymarket_public_ip_ceiling_per_second": (20, 20),
            "polymarket_pre_observation_heartbeat_seconds": (10, 120),
            "polymarket_heartbeat_floor_seconds": (10, 10),
            "polymarket_heartbeat_cap_seconds": (120, 120),
            "kalshi_heartbeat_invalidation_seconds": (20, 40),
            "checkpoint_event_threshold": (1_000, 100_000),
            "checkpoint_time_threshold_seconds": (5, 120),
            "raw_volatile_memory_ring_minutes": (0, 30),
            "wall_clock_uncertainty_target_ns": (1_000_000, 50_000_000),
            "normalized_retention_hot_days": (90, 90),
            "normalized_retention_warm_days": (365, 365),
        }
        for name, (minimum, maximum) in integer_ranges.items():
            value = getattr(self, name)
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f"{name} is outside the frozen safety range")
        decimal_ranges = {
            "gemini_ordinary_rest_target_per_second": (
                Decimal("0.1"),
                Decimal("1"),
            ),
            "gemini_recovery_reserve_fraction": (
                Decimal("0.25"),
                Decimal("0.75"),
            ),
            "polymarket_recovery_reserve_fraction": (
                Decimal("0.25"),
                Decimal("0.50"),
            ),
            "polymarket_backoff_base_seconds": (
                Decimal("1"),
                Decimal("1E+100"),
            ),
            "kalshi_recovery_reserve_fraction": (
                Decimal("0.25"),
                Decimal("0.75"),
            ),
        }
        for name, (minimum, maximum) in decimal_ranges.items():
            value = getattr(self, name)
            if type(value) is not Decimal or not minimum <= value <= maximum:
                raise ValueError(f"{name} is outside the frozen safety range")
        if type(self.live_self_tuning_allowed) is not bool or self.live_self_tuning_allowed:
            raise ValueError("live safety-seed self-tuning is forbidden")

    def backoff_upper_seconds(
        self,
        *,
        base_seconds: Decimal,
        cap_seconds: Decimal,
        consecutive_failure_index: int,
    ) -> Decimal:
        if (
            type(base_seconds) is not Decimal
            or type(cap_seconds) is not Decimal
            or type(consecutive_failure_index) is not int
            or base_seconds < 0
            or cap_seconds < 0
            or consecutive_failure_index < 0
        ):
            raise ValueError("backoff arguments require exact nonnegative values")
        return min(
            cap_seconds,
            base_seconds * (Decimal(2) ** consecutive_failure_index),
        )

    def _polymarket_heartbeat_deadline_seconds(
        self,
        observed_epoch_intervals_seconds: tuple[Decimal, ...],
    ) -> Decimal:
        if type(observed_epoch_intervals_seconds) is not tuple or any(
            type(value) is not Decimal or not value.is_finite() or value <= 0
            for value in observed_epoch_intervals_seconds
        ):
            raise ValueError(
                "heartbeat calibration requires exact positive Decimal intervals"
            )
        if len(observed_epoch_intervals_seconds) < 5:
            return Decimal(self.polymarket_pre_observation_heartbeat_seconds)
        ordered = tuple(sorted(observed_epoch_intervals_seconds))
        nearest_rank_index = ((95 * len(ordered) + 99) // 100) - 1
        adaptive = Decimal(3) * ordered[nearest_rank_index]
        return min(
            Decimal(self.polymarket_heartbeat_cap_seconds),
            max(Decimal(self.polymarket_heartbeat_floor_seconds), adaptive),
        )

    def _full_jitter_backoff_seconds(
        self,
        *,
        base_seconds: Decimal,
        cap_seconds: Decimal,
        consecutive_failure_index: int,
        uniform_sampler: Callable[[Decimal, Decimal], Decimal],
    ) -> Decimal:
        if not callable(uniform_sampler):
            raise ValueError("full-jitter backoff requires an injected sampler")
        upper = self.backoff_upper_seconds(
            base_seconds=base_seconds,
            cap_seconds=cap_seconds,
            consecutive_failure_index=consecutive_failure_index,
        )
        sampled = uniform_sampler(Decimal(0), upper)
        if (
            type(sampled) is not Decimal
            or not sampled.is_finite()
            or sampled < 0
            or sampled > upper
        ):
            raise ValueError("injected full-jitter sample is outside [0, upper]")
        return sampled


PIT_SAFETY_SEED_AND_CALIBRATION_ENVELOPE_V2 = (
    PITSafetySeedAndCalibrationEnvelopeV2()
)
