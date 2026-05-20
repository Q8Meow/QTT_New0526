from __future__ import annotations

from dataclasses import dataclass


STAGE1_VENUE_IDS = ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
SHARED_SCOPE_IDS = ("PREDICTION_MARKETS_GENERAL",)

PRODUCER_REPO_PR = "PR131"
PRODUCER_ROADMAP_PR = "PR113"
PACKAGE_AUTHORITY_CLASS = "READINESS_METADATA_ONLY_NOT_CREDENTIAL_AUTHORITY"
CREATED_BY = "CODEX_PR131_FIXTURE_OR_VALIDATOR"
SCHEMA_VERSION = "PR131_CREDENTIAL_READINESS_SCHEMA_V1"
DETERMINISTIC_FIXTURE_TIME = "2026-05-20T00:00:00Z"

DOWNSTREAM_PR_IDS = ("PR114", "PR115", "PR116")

ALLOWED_ALIAS_CLASSES = (
    "FIXTURE_CREDENTIAL_ALIAS_PLACEHOLDER",
    "OWNER_APPROVAL_REQUIRED_ALIAS_PLACEHOLDER",
    "FUTURE_CREDENTIAL_PROVIDER_ALIAS_REF",
    "FUTURE_VAULT_ALIAS_REF",
)

SECRET_LIKE_REJECTION_CLASSES = (
    "RAW_API_KEY",
    "RAW_BEARER_TOKEN",
    "RAW_OAUTH_TOKEN",
    "RAW_SESSION_COOKIE",
    "RAW_SESSION_IDENTIFIER",
    "RAW_PRIVATE_KEY",
    "RAW_WALLET_SECRET",
    "RAW_PASSWORD",
    "RAW_RECOVERY_PHRASE",
    "RAW_DEVICE_SECRET",
    "TOKEN_LIKE_UNREDACTED_VALUE",
    "SECRET_DIGEST_OF_RAW_SECRET",
    "ENVIRONMENT_VARIABLE_SECRET_LOOKUP",
    "SECRET_MANAGER_LIVE_LOOKUP",
    "PROVIDER_PATH_LIVE_RESOLUTION",
    "UNREDACTED_AUTHORIZATION_HEADER",
    "UNREDACTED_SIGNING_KEY_MATERIAL",
)

AUTHORITY_ZERO_FLAGS = (
    "raw_secret_capture_allowed",
    "raw_secret_hashing_allowed",
    "live_credential_resolution_allowed",
    "production_credential_authority_created",
    "production_connector_authority_created",
    "order_authority_created",
    "private_state_fetch_created",
    "network_io_created",
    "quantum_execution_created",
    "profit_evidence_created",
    "replay_result_created",
    "paper_result_created",
    "atomicrows_bundle_consumed",
    "atomicrows_bundle_created",
    "atomicrows_sha_created",
)

ZERO_COUNT_INVARIANTS = (
    "raw_secret_stored_count",
    "raw_secret_printed_count",
    "raw_secret_hash_created_count",
    "secret_like_value_hashed_count",
    "environment_variable_read_count",
    "secret_manager_call_count",
    "credential_provider_call_count",
    "network_io_count",
    "production_connector_client_count",
    "private_state_fetch_count",
    "order_authority_count",
    "order_execution_count",
    "replay_result_count",
    "paper_result_count",
    "profit_evidence_count",
    "quantum_backend_simulator_optimizer_execution_count",
    "atomicrows_bundle_consumed_count",
    "atomicrows_bundle_created_count",
    "atomicrows_bundle_edited_count",
    "atomicrows_sha_created_count",
)

ALLOWED_ACTION_IDS = (
    "READ_MANDATORY_ROADMAP_MASTER_PLAN_SOURCE_EVIDENCE_FILES",
    "INSPECT_PR129_PR130_ARTIFACTS",
    "CREATE_PR131_SCHEMAS",
    "CREATE_PR131_FIXTURES",
    "CREATE_PR131_VALIDATORS",
    "CREATE_PR131_GENERATED_REPORTS",
    "CREATE_PR131_TESTS",
    "INTEGRATE_PR131_VALIDATOR_INTO_VALIDATION_GATES",
    "RUN_LOCAL_VALIDATION_COMMANDS",
)

BLOCKED_ACTION_IDS = (
    "READ_OR_STORE_REAL_SECRETS",
    "PRINT_RAW_SECRETS",
    "HASH_RAW_SECRETS",
    "READ_ENVIRONMENT_VARIABLES_FOR_CREDENTIALS",
    "CALL_CREDENTIAL_PROVIDER",
    "CALL_SECRETS_MANAGER",
    "CALL_VENUE_API",
    "IMPORT_NETWORK_OR_CLIENT_LIBRARIES_FOR_PR131",
    "CREATE_PRODUCTION_CONNECTOR_CLIENT",
    "FETCH_ACCOUNT_OR_PRIVATE_STATE",
    "SUBMIT_CANCEL_REDUCE_CLOSE_ORDERS",
    "RUN_REPLAY_PAPER_OR_LIVE_TRADING",
    "EXECUTE_QUANTUM_BACKEND_SIMULATOR_OPTIMIZER",
    "MUTATE_ATOMICROWS_BUNDLE_OR_SHA",
    "EDIT_MASTER_PLAN_CURRENT_WITHOUT_OWNER_APPROVAL",
)

READINESS_STATES = (
    "READY_FOR_METADATA_HANDOFF",
    "BLOCKED_SECRET_LIKE_PAYLOAD",
    "BLOCKED_MISSING_PR130_HANDOFF",
    "BLOCKED_MALFORMED_PR130_HANDOFF",
    "BLOCKED_SCOPE_MISMATCH",
    "BLOCKED_ALIAS_NAMESPACE_VIOLATION",
)

DISALLOWED_SCOPE_USES = (
    "LIVE_CREDENTIAL_RESOLUTION",
    "PRODUCTION_CONNECTOR_CLIENT",
    "VENUE_API_CALL",
    "PRIVATE_STATE_FETCH",
    "ORDER_SUBMISSION",
    "ORDER_CANCELLATION",
    "ORDER_REDUCTION",
    "ORDER_CLOSE",
    "REPLAY_EXECUTION",
    "PAPER_EXECUTION",
    "PROFIT_EVIDENCE_CREATION",
    "QUANTUM_EXECUTION",
)

ALLOWED_REDACTED_SECRET_EXAMPLES = (
    "REDACTED_SECRET_EXAMPLE_RAW_API_KEY",
    "REDACTED_SECRET_EXAMPLE_BEARER_TOKEN",
    "REDACTED_SECRET_EXAMPLE_OAUTH_TOKEN",
    "REDACTED_SECRET_EXAMPLE_SESSION_COOKIE",
    "REDACTED_SECRET_EXAMPLE_PRIVATE_KEY",
    "REDACTED_SECRET_EXAMPLE_WALLET_SECRET",
    "REDACTED_SECRET_EXAMPLE_PASSWORD",
    "REDACTED_SECRET_EXAMPLE_RECOVERY_PHRASE",
    "REDACTED_SECRET_EXAMPLE_DEVICE_SECRET",
    "REDACTED_SECRET_EXAMPLE_SECRET_DIGEST",
)

BANNED_IMPORT_MODULES = (
    "requests",
    "httpx",
    "aiohttp",
    "urllib.request",
    "websockets",
    "boto3",
    "botocore",
    "hvac",
    "keyring",
    "secretstorage",
    "azure.identity",
    "google.cloud.secretmanager",
    "kubernetes",
    "dotenv",
)

VENUE_ALIAS_CLASSES = {
    "KALSHI": "FIXTURE_CREDENTIAL_ALIAS_PLACEHOLDER",
    "POLYMARKET": "OWNER_APPROVAL_REQUIRED_ALIAS_PLACEHOLDER",
    "FORECASTEX_IBKR": "FUTURE_CREDENTIAL_PROVIDER_ALIAS_REF",
}
SHARED_SCOPE_ALIAS_CLASSES = {
    "PREDICTION_MARKETS_GENERAL": "FUTURE_VAULT_ALIAS_REF",
}


def zero_authority_flags() -> dict[str, bool]:
    return {field: False for field in AUTHORITY_ZERO_FLAGS}


def zero_count_invariants() -> dict[str, int]:
    return {field: 0 for field in ZERO_COUNT_INVARIANTS}


def common_record_fields(record_type: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": record_type,
        "created_by": CREATED_BY,
        "authority_class": PACKAGE_AUTHORITY_CLASS,
        **zero_authority_flags(),
    }


@dataclass(frozen=True)
class ScopeRef:
    scope_kind: str
    value: str

    @property
    def field_name(self) -> str:
        return "venue_id" if self.scope_kind == "venue" else "scope_id"


def stage1_scope_refs() -> tuple[ScopeRef, ...]:
    return tuple(ScopeRef("venue", venue_id) for venue_id in STAGE1_VENUE_IDS) + tuple(
        ScopeRef("shared_scope", scope_id) for scope_id in SHARED_SCOPE_IDS
    )


def alias_class_for(scope_ref: ScopeRef) -> str:
    if scope_ref.scope_kind == "venue":
        return VENUE_ALIAS_CLASSES[scope_ref.value]
    return SHARED_SCOPE_ALIAS_CLASSES[scope_ref.value]
