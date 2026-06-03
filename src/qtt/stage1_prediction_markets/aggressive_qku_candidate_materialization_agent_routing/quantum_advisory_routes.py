"""Quantum advisory route helpers."""

from __future__ import annotations


def quantum_advisory_routes(routes):
    return [
        record for record in routes
        if "QUANTUM_ADVISORY_AGENT" in record.get("agent_path_refs", [])
    ]
