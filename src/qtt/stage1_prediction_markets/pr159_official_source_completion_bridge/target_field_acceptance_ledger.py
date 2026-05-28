"""PR159 target-field acceptance ledger construction."""

from __future__ import annotations

from typing import Any, Mapping

from . import constants as c


def build_acceptance_ledger(accepted_packets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for packet in accepted_packets:
        accepted_packet_id = str(packet["accepted_packet_id"])
        records.append(
            {
                "ledger_record_id": f"PR159_LEDGER__{accepted_packet_id}",
                "accepted_packet_id": accepted_packet_id,
                "target_id_or_row_id": packet.get("target_id_or_row_id"),
                "target_field_id": packet["target_field_id"],
                "source_population": packet.get("source_population"),
                "source_packet_integrity_digest_if_schema_supported": None,
                "revalidation_due_class": packet["revalidation_class"],
                "materiality_class": packet["materiality_class"],
                "downstream_routes": [
                    c.FutureRoute.PR161_ATOMICROWS_SOURCE_VALUE_MATERIALIZATION.value,
                    c.FutureRoute.PR164_SCORING_RANKING_BRIDGE.value,
                ],
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return sorted(records, key=lambda item: item["ledger_record_id"])
