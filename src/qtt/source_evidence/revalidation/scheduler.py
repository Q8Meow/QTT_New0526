from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.qtt.source_evidence.connector_semantic_consumer.ledger import load_json_object

from .materiality import FIXTURE_AUTHORITY_CLASS, classify_materiality_event
from .snapshot import build_source_change_snapshot
from .supersession import build_supersession_records


DETERMINISTIC_FIXTURE_TIME = "2026-05-19T00:00:00Z"
LIVE_CRITICAL_REVALIDATION_INTERVAL = "P1D"
LOW_RISK_REVALIDATION_INTERVAL = "P7D"
EVENT_TRIGGERED_REVALIDATION_LATENCY_CLASS = (
    "IMMEDIATE_CONTROL_PLANE_REVALIDATION_BEFORE_NEW_BINDING_OR_NEW_LIVE_USE"
)

LIVE_CRITICAL_SOURCE_FIELD_CLASSES = (
    "FEE_RULES",
    "TICK_RULES",
    "ORDER_ENTRY_FIELDS",
    "ORDER_STATUS_FIELDS",
    "ORDERBOOK_SCHEMA",
    "WEBSOCKET_SCHEMA",
    "SETTLEMENT_RULES",
    "PAYOUT_RULES",
    "RATE_LIMITS",
    "ACCOUNT_BALANCE_SEMANTICS",
    "PRIVATE_STATE_CASH_SEMANTICS",
    "MARGIN_RESERVE_LOCK_SEMANTICS",
    "ERROR_REJECT_THROTTLE_SEMANTICS",
    "EXECUTION_LIFECYCLE_SEMANTICS",
    "FILL_INTEGRITY_SEMANTICS",
    "CASHFLOW_PNL_SEMANTICS",
    "LATENCY_COMPONENT_SEMANTICS",
    "SETTLEMENT_FINALITY_SEMANTICS",
    "RECONCILIATION_SEMANTICS",
)

LOW_RISK_SOURCE_FIELD_CLASSES = (
    "NON_TARGET_FIELD_DOC_TEXT",
    "GENERAL_EXPLANATORY_DOCS",
    "UNUSED_EXAMPLES",
    "CHANGELOG_ITEMS_WITH_NO_TARGET_FIELD_DELTA",
)

STAGE1_PLATFORM_SCOPES = (
    "KALSHI",
    "POLYMARKET",
    "FORECASTEX_IBKR",
    "PREDICTION_MARKETS_GENERAL",
)

FUTURE_MARKET_FAMILY_METADATA_ONLY = (
    "STOCKS",
    "CRYPTOCURRENCY",
    "FUTURES",
    "OPTIONS",
    "EQUITIES",
    "ETFS",
    "FX",
    "COMMODITIES",
)

FIXTURE_ROOT = Path("tests/fixtures/source_evidence/pr125_revalidation_scheduler")
ACCEPTED_SOURCE_FIXTURE = FIXTURE_ROOT / "accepted_source_evidence_records.v1.fixture.json"
CONNECTOR_BINDING_FIXTURE = (
    FIXTURE_ROOT / "connector_semantic_binding_records.v1.fixture.json"
)
REVALIDATION_EVENTS_FIXTURE = FIXTURE_ROOT / "revalidation_events.v1.fixture.json"
EXPECTED_SCHEDULE_FIXTURE = (
    FIXTURE_ROOT / "expected_revalidation_schedule.v1.fixture.json"
)
EXPECTED_SUPERSESSION_FIXTURE = (
    FIXTURE_ROOT / "expected_supersession_records.v1.fixture.json"
)
EXPECTED_MATERIALITY_FIXTURE = (
    FIXTURE_ROOT / "expected_materiality_events.v1.fixture.json"
)
EXPECTED_SNAPSHOT_FIXTURE = (
    FIXTURE_ROOT / "expected_source_change_snapshot.v1.fixture.json"
)

PR125_REPORT_PATH = Path(
    "docs/master_plan/source_evidence/generated/"
    "CODEX_PR125_SOURCE_REVALIDATION_SUPERSESSION_MATERIALITY_SCHEDULER_REPORT.json"
)
SCHEDULER_REPORT_PATH = Path(
    "docs/master_plan/source_evidence/generated/SourceRevalidationScheduler.report.json"
)
SOURCE_CHANGE_SNAPSHOT_REPORT_PATH = Path(
    "docs/master_plan/source_evidence/generated/SourceChangeImpactSnapshot.report.json"
)


def _parse_fixture_time(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ValueError(f"fixture time must use Z suffix: {value}")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def _format_fixture_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )


def _interval_days(interval: str) -> int:
    if interval == LIVE_CRITICAL_REVALIDATION_INTERVAL:
        return 1
    if interval == LOW_RISK_REVALIDATION_INTERVAL:
        return 7
    raise ValueError(f"unsupported revalidation interval: {interval}")


def _source_interval(record: Mapping[str, Any]) -> str:
    source_class = str(record.get("source_field_class", ""))
    if source_class in LIVE_CRITICAL_SOURCE_FIELD_CLASSES:
        return LIVE_CRITICAL_REVALIDATION_INTERVAL
    if source_class in LOW_RISK_SOURCE_FIELD_CLASSES:
        return LOW_RISK_REVALIDATION_INTERVAL
    return LIVE_CRITICAL_REVALIDATION_INTERVAL


def _events_by_packet(events: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for event in events:
        packet_id = event.get("accepted_source_evidence_packet_id")
        declared_materiality = event.get("declared_materiality_class")
        is_no_delta_low_risk_or_info = (
            declared_materiality in {"INFO_ONLY", "LOW_RISK"}
            and event.get("target_field_delta_detected") is False
            and event.get("validator_confirms_no_target_field_delta") is True
        )
        if isinstance(packet_id, str) and not is_no_delta_low_risk_or_info:
            grouped.setdefault(packet_id, []).append(event)
    return grouped


def _superseded_packet_ids(supersession_records: Sequence[Mapping[str, Any]]) -> set[str]:
    return {
        str(record["superseded_packet_id"])
        for record in supersession_records
        if isinstance(record.get("superseded_packet_id"), str)
    }


def _next_due_time(record: Mapping[str, Any], interval: str) -> str:
    last_revalidated = _parse_fixture_time(str(record["last_revalidated_at_fixture_time"]))
    return _format_fixture_time(last_revalidated + timedelta(days=_interval_days(interval)))


def _schedule_record(
    record: Mapping[str, Any],
    *,
    deterministic_fixture_time: str,
    superseded_packet_ids: set[str],
    event_by_packet: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    packet_id = str(record["accepted_source_evidence_packet_id"])
    interval = _source_interval(record)
    next_due_at = _next_due_time(record, interval)
    fixture_now = _parse_fixture_time(deterministic_fixture_time)
    due_at = _parse_fixture_time(next_due_at)
    has_event = bool(event_by_packet.get(packet_id))
    if packet_id in superseded_packet_ids:
        revalidation_state = "SUPERSEDED"
        due_state = "SUPERSEDED"
    elif has_event:
        revalidation_state = "DUE_EVENT_TRIGGERED"
        due_state = "DUE_EVENT_TRIGGERED"
    elif fixture_now > due_at:
        revalidation_state = "STALE"
        due_state = "DUE_TIME_BASED"
    elif fixture_now == due_at:
        revalidation_state = "DUE_TIME_BASED"
        due_state = "DUE_TIME_BASED"
    else:
        revalidation_state = "FRESH"
        due_state = "NOT_DUE"

    return {
        "source_revalidation_schedule_record_id": f"PR125_REVALIDATION_SCHEDULE_{packet_id}",
        "accepted_source_evidence_packet_id": packet_id,
        "venue_id": record["venue_id"],
        "platform_scope": record["platform_scope"],
        "source_field_class": record["source_field_class"],
        "target_field_path": record["target_field_path"],
        "revalidation_interval": interval,
        "revalidation_state": revalidation_state,
        "revalidation_due_state": due_state,
        "next_revalidation_due_at_fixture_time": next_due_at,
        "deterministic_fixture_time": deterministic_fixture_time,
        "supersession_state": (
            "SUPERSEDED_BY_NEW_ACCEPTED_PACKET"
            if packet_id in superseded_packet_ids
            else "NOT_SUPERSEDED"
        ),
        "materiality_classification_required": True,
        "connector_binding_revalidation_state": (
            "SOURCE_REVALIDATION_REQUIRED"
            if revalidation_state in {"SUPERSEDED", "DUE_EVENT_TRIGGERED", "STALE"}
            else "NOT_REQUIRED_FOR_FIXTURE"
        ),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_revalidation_authority": False,
        "production_source_change_authority": False,
        "live_pretrade_use_allowed_flag": False,
        "network_io_allowed_flag": False,
        "source_retrieval_allowed_flag": False,
        "source_acceptance_allowed_flag": False,
        "connector_binding_mutation_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "live_reachability_allowed_flag": False,
    }


def _decision_receipt(schedule_record: Mapping[str, Any]) -> dict[str, Any]:
    packet_id = str(schedule_record["accepted_source_evidence_packet_id"])
    return {
        "source_revalidation_decision_receipt_id": f"PR125_REVALIDATION_DECISION_{packet_id}",
        "accepted_source_evidence_packet_id": packet_id,
        "revalidation_state": schedule_record["revalidation_state"],
        "revalidation_due_state": schedule_record["revalidation_due_state"],
        "connector_binding_revalidation_state": schedule_record[
            "connector_binding_revalidation_state"
        ],
        "decision_reason": (
            "FIXTURE_DETERMINISTIC_POLICY_EVALUATION_NO_EXTERNAL_SOURCE_LOOKUP"
        ),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_revalidation_authority": False,
        "production_source_change_authority": False,
        "live_pretrade_use_allowed_flag": False,
        "network_io_allowed_flag": False,
        "source_retrieval_allowed_flag": False,
        "source_acceptance_allowed_flag": False,
        "connector_binding_mutation_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "live_reachability_allowed_flag": False,
    }


def load_pr125_fixture_inputs(repo_root: Path) -> dict[str, Any]:
    return {
        "accepted_source_evidence_records": load_json_object(
            repo_root / ACCEPTED_SOURCE_FIXTURE
        ),
        "connector_semantic_binding_records": load_json_object(
            repo_root / CONNECTOR_BINDING_FIXTURE
        ),
        "revalidation_events": load_json_object(repo_root / REVALIDATION_EVENTS_FIXTURE),
        "expected_revalidation_schedule": load_json_object(
            repo_root / EXPECTED_SCHEDULE_FIXTURE
        ),
        "expected_supersession_records": load_json_object(
            repo_root / EXPECTED_SUPERSESSION_FIXTURE
        ),
        "expected_materiality_events": load_json_object(
            repo_root / EXPECTED_MATERIALITY_FIXTURE
        ),
        "expected_source_change_snapshot": load_json_object(
            repo_root / EXPECTED_SNAPSHOT_FIXTURE
        ),
    }


def run_revalidation_scheduler(
    accepted_records: Sequence[Mapping[str, Any]],
    connector_bindings: Sequence[Mapping[str, Any]],
    revalidation_events: Sequence[Mapping[str, Any]],
    *,
    deterministic_fixture_time: str = DETERMINISTIC_FIXTURE_TIME,
) -> dict[str, Any]:
    supersession_records = build_supersession_records(
        accepted_records,
        connector_bindings,
        deterministic_fixture_time=deterministic_fixture_time,
    )
    events_by_packet = _events_by_packet(revalidation_events)
    superseded_ids = _superseded_packet_ids(supersession_records)
    schedule_records = [
        _schedule_record(
            record,
            deterministic_fixture_time=deterministic_fixture_time,
            superseded_packet_ids=superseded_ids,
            event_by_packet=events_by_packet,
        )
        for record in accepted_records
    ]
    schedule_records.sort(key=lambda item: item["source_revalidation_schedule_record_id"])
    decision_receipts = [_decision_receipt(record) for record in schedule_records]
    materiality_events = [
        classify_materiality_event(event) for event in revalidation_events
    ]
    materiality_events.sort(key=lambda item: item["source_change_materiality_event_id"])
    source_change_snapshot = build_source_change_snapshot(
        schedule_records=schedule_records,
        supersession_records=supersession_records,
        materiality_events=materiality_events,
        deterministic_fixture_time=deterministic_fixture_time,
    )
    return {
        "deterministic_fixture_time": deterministic_fixture_time,
        "source_revalidation_schedule_records": schedule_records,
        "source_revalidation_decision_receipts": decision_receipts,
        "source_supersession_records": supersession_records,
        "source_change_materiality_events": materiality_events,
        "source_change_impact_snapshots": [source_change_snapshot],
    }
