#!/usr/bin/env python3
"""Online documentation discovery rows for PR168-DATA1."""

from __future__ import annotations

from tools.pr168_data1_config import DOC_SOURCES, ENDPOINT_CONTRACTS, authority_flags, route_defaults
from tools.pr168_data1_http_client import PublicHttpClient


def discover_sources(discover_online: bool, now_utc: str) -> list[dict[str, object]]:
    http = PublicHttpClient()
    rows: list[dict[str, object]] = []
    for source in DOC_SOURCES:
        result = http.get_text(str(source["url"])) if discover_online else None
        rows.append(
            {
                "source_id": source["source_id"],
                "venue": source["venue"],
                "source_url": source["url"],
                "trust_tier": source["trust_tier"],
                "source_tier": "OFFICIAL_PUBLIC_API" if "OFFICIAL" in str(source["trust_tier"]) else "NON_OFFICIAL_CANDIDATE_SOURCE",
                "relevance": source["relevance"],
                "online_probe_status": result.data_status if result else "OFFLINE_NOT_PROBED",
                "http_status": result.status if result else None,
                "probe_error": result.error if result else None,
                "probe_elapsed_ms": result.elapsed_ms if result else None,
                "content_snippet": result.text_snippet[:160] if result and result.text_snippet else None,
                "discovered_at_utc": now_utc,
                **route_defaults("source_evidence"),
                **authority_flags(),
            }
        )
    return rows


def endpoint_contract_rows(now_utc: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for endpoint in ENDPOINT_CONTRACTS:
        rows.append(
            {
                "endpoint_contract_id": endpoint["endpoint_id"],
                "venue": endpoint["venue"],
                "method": endpoint["method"],
                "source_url": endpoint["url"],
                "endpoint_url_template": endpoint["url"],
                "endpoint_params": endpoint["params"],
                "auth_requirement": endpoint["auth_requirement"],
                "data_families": endpoint["data_families"],
                "historical_full_book_availability": endpoint["historical_full_book_availability"],
                "websocket_public_stream_availability": endpoint["method"] == "WSS"
                and endpoint["auth_requirement"].startswith("PUBLIC"),
                "rate_limit_notes": "respect public API limits; DATA1 uses bounded fetches and deterministic backoff",
                "source_tier": endpoint["source_tier"],
                "trust_tier": "OFFICIAL_PUBLIC_API_DOC",
                "discovered_at_utc": now_utc,
                **route_defaults("source_evidence"),
                **authority_flags(),
            }
        )
    return rows
