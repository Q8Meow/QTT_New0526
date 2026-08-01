"""Deterministic schema version 1 for the non-production SQLite reference adapter."""

from __future__ import annotations

from types import MappingProxyType


REFERENCE_SCHEMA_VERSION_V1 = "1"

APPEND_ONLY_TABLES_V1 = (
    "receipt_records",
    "value_lineage_edges",
    "economic_events",
    "journal_transactions",
    "journal_postings",
    "state_transitions",
    "idempotency_claims",
    "outbox_intents",
    "reversal_links",
    "reconciliation_breaks",
)

REFERENCE_SCHEMA_V1 = (
    "CREATE TABLE IF NOT EXISTS qku_schema_version (singleton INTEGER PRIMARY KEY CHECK(singleton=1), schema_version TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS receipt_records (record_id TEXT PRIMARY KEY, effective_at TEXT NOT NULL, recorded_at TEXT NOT NULL, aggregate_id TEXT NOT NULL, payload_json TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS value_lineage_edges (lineage_edge_id TEXT PRIMARY KEY, producer_record_id TEXT NOT NULL, consumer_record_id TEXT NOT NULL, effective_at TEXT NOT NULL, recorded_at TEXT NOT NULL, payload_json TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS economic_events (economic_event_id TEXT PRIMARY KEY, aggregate_id TEXT NOT NULL, event_sequence INTEGER NOT NULL, effective_at TEXT NOT NULL, recorded_at TEXT NOT NULL, payload_json TEXT NOT NULL, UNIQUE(aggregate_id,event_sequence))",
    "CREATE TABLE IF NOT EXISTS journal_transactions (journal_transaction_id TEXT PRIMARY KEY, effective_at TEXT NOT NULL, recorded_at TEXT NOT NULL, payload_json TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS journal_postings (posting_id TEXT PRIMARY KEY, journal_transaction_id TEXT NOT NULL REFERENCES journal_transactions(journal_transaction_id), effective_at TEXT NOT NULL, recorded_at TEXT NOT NULL, payload_json TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS state_transitions (transition_id TEXT PRIMARY KEY, aggregate_id TEXT NOT NULL, aggregate_version_after INTEGER NOT NULL, effective_at TEXT NOT NULL, recorded_at TEXT NOT NULL, payload_json TEXT NOT NULL, UNIQUE(aggregate_id,aggregate_version_after))",
    "CREATE TABLE IF NOT EXISTS idempotency_claims (claim_record_id TEXT PRIMARY KEY, parent_claim_id TEXT, idempotency_key TEXT, canonical_request_json TEXT, result_record_ref TEXT, created_at TEXT NOT NULL, payload_json TEXT NOT NULL, UNIQUE(idempotency_key), UNIQUE(parent_claim_id))",
    "CREATE TABLE IF NOT EXISTS outbox_intents (outbox_intent_id TEXT PRIMARY KEY, aggregate_id TEXT NOT NULL, payload_record_ref TEXT NOT NULL, created_at TEXT NOT NULL, payload_json TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS reversal_links (reversal_receipt_id TEXT PRIMARY KEY, original_ref TEXT NOT NULL, reversal_transaction_ref TEXT NOT NULL, effective_at TEXT NOT NULL, recorded_at TEXT NOT NULL, payload_json TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS reconciliation_breaks (break_receipt_id TEXT PRIMARY KEY, reconciliation_run_id TEXT NOT NULL, effective_at TEXT NOT NULL, recorded_at TEXT NOT NULL, payload_json TEXT NOT NULL)",
)

REFERENCE_SCHEMA_COLUMNS_V1 = MappingProxyType({
    "qku_schema_version": ("singleton", "schema_version"),
    "receipt_records": ("record_id", "effective_at", "recorded_at", "aggregate_id", "payload_json"),
    "value_lineage_edges": ("lineage_edge_id", "producer_record_id", "consumer_record_id", "effective_at", "recorded_at", "payload_json"),
    "economic_events": ("economic_event_id", "aggregate_id", "event_sequence", "effective_at", "recorded_at", "payload_json"),
    "journal_transactions": ("journal_transaction_id", "effective_at", "recorded_at", "payload_json"),
    "journal_postings": ("posting_id", "journal_transaction_id", "effective_at", "recorded_at", "payload_json"),
    "state_transitions": ("transition_id", "aggregate_id", "aggregate_version_after", "effective_at", "recorded_at", "payload_json"),
    "idempotency_claims": ("claim_record_id", "parent_claim_id", "idempotency_key", "canonical_request_json", "result_record_ref", "created_at", "payload_json"),
    "outbox_intents": ("outbox_intent_id", "aggregate_id", "payload_record_ref", "created_at", "payload_json"),
    "reversal_links": ("reversal_receipt_id", "original_ref", "reversal_transaction_ref", "effective_at", "recorded_at", "payload_json"),
    "reconciliation_breaks": ("break_receipt_id", "reconciliation_run_id", "effective_at", "recorded_at", "payload_json"),
})

REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1 = MappingProxyType(
    {
        "receipt_records": "record_id",
        "value_lineage_edges": "lineage_edge_id",
        "economic_events": "economic_event_id",
        "journal_transactions": "journal_transaction_id",
        "journal_postings": "posting_id",
        "state_transitions": "transition_id",
        "idempotency_claims": "claim_record_id",
        "outbox_intents": "outbox_intent_id",
        "reversal_links": "reversal_receipt_id",
        "reconciliation_breaks": "break_receipt_id",
    }
)


def append_only_trigger_statements_v1() -> tuple[str, ...]:
    statements: list[str] = []
    for table in APPEND_ONLY_TABLES_V1:
        statements.extend(
            (
                f"CREATE TRIGGER IF NOT EXISTS {table}_reject_update BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT, 'append-only table'); END",
                f"CREATE TRIGGER IF NOT EXISTS {table}_reject_delete BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT, 'append-only table'); END",
            )
        )
    return tuple(statements)


PRODUCTION_PERSISTENCE_SELECTION_STATE_V1 = (
    "NO_DEFAULT_REQUIRES_SEPARATE_RUNTIME_PLATFORM_AUTHORIZATION_AND_BENCHMARK"
)

if (
    len(APPEND_ONLY_TABLES_V1) != 10
    or len(set(APPEND_ONLY_TABLES_V1)) != 10
    or set(REFERENCE_IDENTITY_COLUMN_BY_TABLE_V1) != set(APPEND_ONLY_TABLES_V1)
):
    raise RuntimeError("reference persistence registry must contain ten authoritative append-only tables")
