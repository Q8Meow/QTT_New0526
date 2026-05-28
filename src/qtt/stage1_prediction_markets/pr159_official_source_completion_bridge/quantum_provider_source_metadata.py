"""Quantum-provider source metadata for PR159."""

from __future__ import annotations

from typing import Any, Mapping

from .official_source_discovery import OFFICIAL_SOURCE_CATALOG


def build_quantum_metadata(records: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    source_required_quantum_rows = [
        record
        for record in records
        if any("QUANTUM" in str(item) for item in record.get("quantum_classical_compatibility", []))
    ]
    quantum_sources = [
        source
        for source in OFFICIAL_SOURCE_CATALOG
        if source["platform_scope"] == "QUANTUM_PROVIDER"
    ]
    return [
        {
            "metadata_record_id": f"PR159_QUANTUM_METADATA__{source['official_source_ref']}",
            "official_source_ref": source["official_source_ref"],
            "source_url": source["source_url"],
            "source_title": source["source_title"],
            "target_linked_source_required_row_count": len(source_required_quantum_rows),
            "metadata_only_no_backend_execution": True,
            "quantum_advantage_claim_created": False,
            "latency_superiority_claim_created": False,
            "profit_superiority_claim_created": False,
            "future_route": "PR169_QUANTUM_BACKEND_GATED_SANDBOX",
        }
        for source in quantum_sources
    ]

