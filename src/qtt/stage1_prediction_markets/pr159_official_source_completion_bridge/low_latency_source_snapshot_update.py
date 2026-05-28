"""Low-latency precomputed-index source update metadata for PR159."""

from __future__ import annotations

from typing import Any, Mapping


def build_low_latency_updates(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": record["row_id"],
            "low_latency_source_snapshot_metadata_only": True,
            "source_ready_flag": record["accepted_source_packet_ref_or_null"] is not None,
            "live_pretrade_path_parse_large_json_allowed": False,
            "live_pretrade_path_parse_master_plan_allowed": False,
            "live_pretrade_path_quantum_backend_call_allowed": False,
            "runtime_live_authority_created": False,
        }
        for record in sorted(records, key=lambda item: item["row_id"])
    ]

