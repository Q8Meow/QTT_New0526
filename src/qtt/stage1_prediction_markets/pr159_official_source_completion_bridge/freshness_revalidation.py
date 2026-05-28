"""Freshness and revalidation helpers for PR159."""

from __future__ import annotations

from typing import Any, Mapping


def build_freshness_audit(source_records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "official_source_ref": source["official_source_ref"],
            "freshness_state": source["freshness_state"],
            "source_version_or_date_or_null": source["source_version_or_date_or_null"],
            "materiality_basis": ",".join(source["field_classes"]),
            "requires_event_revalidation_before_binding": True,
            "connector_binding_created": False,
            "live_trading_authority_created": False,
        }
        for source in sorted(source_records, key=lambda item: item["official_source_ref"])
    ]

