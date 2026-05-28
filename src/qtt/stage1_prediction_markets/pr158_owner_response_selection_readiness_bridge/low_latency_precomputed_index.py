"""Static low-latency readiness index metadata."""

from __future__ import annotations

from typing import Any, Mapping


def build(overlay_records: list[Mapping[str, Any]]) -> dict[str, Any]:
    eligible = [
        {
            "row_id": item["row_id"],
            "family_id": item["family_id"],
            "scoring_feature_role": item["scoring_feature_role"],
            "latency_path_class": item["latency_path_class"],
            "future_route": item["future_route"],
        }
        for item in overlay_records
        if item["low_latency_precomputed_index_eligible_flag"] is True
    ]
    return {
        "index_type": "PR158_PRECOMPUTED_LOW_LATENCY_SELECTION_READINESS_INDEX_STATIC_METADATA_ONLY",
        "record_count": len(eligible),
        "records": sorted(eligible, key=lambda item: item["row_id"]),
        "live_pretrade_path_parse_large_json_allowed": False,
        "live_pretrade_path_parse_master_plan_allowed": False,
        "live_pretrade_path_quantum_backend_call_allowed": False,
        "runtime_live_authority_created": False,
    }

