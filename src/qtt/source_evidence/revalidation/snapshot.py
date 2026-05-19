from __future__ import annotations

from typing import Any, Mapping, Sequence

from .materiality import FIXTURE_AUTHORITY_CLASS


def _sorted_unique(values: Sequence[str]) -> list[str]:
    return sorted(set(values))


def build_source_change_snapshot(
    *,
    schedule_records: Sequence[Mapping[str, Any]],
    supersession_records: Sequence[Mapping[str, Any]],
    materiality_events: Sequence[Mapping[str, Any]],
    deterministic_fixture_time: str,
) -> dict[str, Any]:
    stale_packet_ids = [
        str(record["accepted_source_evidence_packet_id"])
        for record in schedule_records
        if record.get("revalidation_state") == "STALE"
    ]
    superseded_packet_ids = [
        str(record["superseded_packet_id"]) for record in supersession_records
    ]
    due_packet_ids = [
        str(record["accepted_source_evidence_packet_id"])
        for record in schedule_records
        if record.get("revalidation_state")
        in {"DUE_TIME_BASED", "DUE_EVENT_TRIGGERED", "STALE", "SUPERSEDED"}
    ]
    affected_venues: list[str] = []
    affected_paths: list[str] = []
    affected_bindings: list[str] = []
    materiality_event_ids: list[str] = []
    connector_required: list[str] = []
    no_new_binding_paths: list[str] = []
    no_new_or_increased_exposure_scopes: list[str] = []
    owner_or_risk_review_required: list[str] = []

    for record in materiality_events:
        affected_venues.append(str(record["venue_id"]))
        materiality_event_ids.append(str(record["source_change_materiality_event_id"]))
        affected_paths.extend(str(path) for path in record.get("affected_target_field_paths", []))
        affected_bindings.extend(
            str(binding_id) for binding_id in record.get("affected_connector_binding_ids", [])
        )
        if record.get("connector_binding_revalidation_required") is True:
            connector_required.extend(
                str(binding_id) for binding_id in record.get("affected_connector_binding_ids", [])
            )
        if record.get("no_new_binding_required") is True:
            no_new_binding_paths.extend(
                str(path) for path in record.get("affected_target_field_paths", [])
            )
        if record.get("no_new_or_increased_exposure_required") is True:
            no_new_or_increased_exposure_scopes.extend(
                str(scope_id) for scope_id in record.get("affected_scope_ids", [])
            )
        if record.get("owner_or_risk_review_required") is True:
            owner_or_risk_review_required.append(
                str(record["source_change_materiality_event_id"])
            )

    for record in supersession_records:
        affected_paths.extend(str(path) for path in record.get("affected_target_field_paths", []))
        affected_bindings.extend(
            str(binding_id) for binding_id in record.get("affected_connector_binding_ids", [])
        )
        connector_required.extend(
            str(binding_id) for binding_id in record.get("affected_connector_binding_ids", [])
        )

    return {
        "source_change_snapshot_id": "PR125_SOURCE_CHANGE_IMPACT_SNAPSHOT_FIXTURE_V1",
        "snapshot_scope": "STAGE1_PREDICTION_MARKETS_SOURCE_REVALIDATION_FIXTURE",
        "generated_by_tool": "tools/source_revalidation_scheduler.py",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_source_change_authority": False,
        "source_change_snapshot_state": "PRECOMPUTED_CONTROL_PLANE_FIXTURE",
        "deterministic_fixture_time": deterministic_fixture_time,
        "affected_venue_ids": _sorted_unique(affected_venues),
        "affected_target_field_paths": _sorted_unique(affected_paths),
        "affected_connector_binding_ids": _sorted_unique(affected_bindings),
        "stale_accepted_packet_ids": _sorted_unique(stale_packet_ids),
        "superseded_accepted_packet_ids": _sorted_unique(superseded_packet_ids),
        "revalidation_due_packet_ids": _sorted_unique(due_packet_ids),
        "materiality_event_ids": _sorted_unique(materiality_event_ids),
        "connector_binding_revalidation_required_ids": _sorted_unique(connector_required),
        "no_new_binding_target_field_paths": _sorted_unique(no_new_binding_paths),
        "no_new_or_increased_exposure_scope_ids": _sorted_unique(
            no_new_or_increased_exposure_scopes
        ),
        "owner_or_risk_review_required_ids": _sorted_unique(owner_or_risk_review_required),
        "live_pretrade_use_allowed_flag": False,
        "live_pretrade_consumption_mode": "PRECOMPUTED_SNAPSHOT_ONLY_FOR_FUTURE_PR",
        "network_io_allowed_flag": False,
        "source_retrieval_allowed_flag": False,
        "source_acceptance_allowed_flag": False,
        "connector_binding_mutation_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "live_reachability_allowed_flag": False,
    }
