from __future__ import annotations

from typing import Any, Mapping, Sequence

from .materiality import FIXTURE_AUTHORITY_CLASS


def _bindings_for_packet(
    connector_bindings: Sequence[Mapping[str, Any]],
    packet_id: str,
) -> list[str]:
    return [
        str(record["connector_binding_id"])
        for record in connector_bindings
        if record.get("accepted_source_evidence_packet_id") == packet_id
        and isinstance(record.get("connector_binding_id"), str)
    ]


def _packet_by_id(
    accepted_records: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    return {
        str(record["accepted_source_evidence_packet_id"]): record
        for record in accepted_records
        if isinstance(record.get("accepted_source_evidence_packet_id"), str)
    }


def build_supersession_records(
    accepted_records: Sequence[Mapping[str, Any]],
    connector_bindings: Sequence[Mapping[str, Any]],
    *,
    deterministic_fixture_time: str,
) -> list[dict[str, Any]]:
    packets = _packet_by_id(accepted_records)
    records: list[dict[str, Any]] = []
    for superseding in accepted_records:
        superseding_packet_id = str(superseding.get("accepted_source_evidence_packet_id", ""))
        for superseded_packet_id in superseding.get("supersedes_packet_ids", []):
            if not isinstance(superseded_packet_id, str):
                continue
            superseded = packets.get(superseded_packet_id)
            affected_target_paths: list[str] = []
            if isinstance(superseded, Mapping) and isinstance(
                superseded.get("target_field_path"), str
            ):
                affected_target_paths.append(str(superseded["target_field_path"]))
            elif isinstance(superseding.get("target_field_path"), str):
                affected_target_paths.append(str(superseding["target_field_path"]))
            records.append(
                {
                    "source_supersession_record_id": (
                        f"PR125_SUPERSESSION_{superseded_packet_id}_BY_{superseding_packet_id}"
                    ),
                    "superseded_packet_id": superseded_packet_id,
                    "superseding_packet_id": superseding_packet_id,
                    "supersession_reason": superseding.get(
                        "supersession_reason",
                        "NEW_ACCEPTED_PACKET_FOR_SAME_TARGET_FIELD",
                    ),
                    "affected_target_field_paths": sorted(set(affected_target_paths)),
                    "affected_connector_binding_ids": _bindings_for_packet(
                        connector_bindings,
                        superseded_packet_id,
                    ),
                    "supersession_state": "SUPERSEDED_BY_NEW_ACCEPTED_PACKET",
                    "supersession_effective_at_fixture_time": deterministic_fixture_time,
                    "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
                    "production_source_change_authority": False,
                }
            )
    return sorted(records, key=lambda record: record["source_supersession_record_id"])
