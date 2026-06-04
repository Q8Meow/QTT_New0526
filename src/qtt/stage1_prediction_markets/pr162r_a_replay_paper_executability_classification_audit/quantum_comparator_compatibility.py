"""Quantum comparator compatibility records."""

from __future__ import annotations

from typing import Any

from .candidate_loader import candidate_id, candidate_type


def quantum_comparator_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        if candidate_type(record) != "QUANTUM":
            continue
        rows.append(
            {
                "candidate_id": candidate_id(record),
                "quantum_family": record.get("quantum_family"),
                "quantum_comparator_ready_flag": bool(record.get("strongest_classical_comparator_mapping")),
                "classical_comparator_mapping": record.get("strongest_classical_comparator_mapping") or {},
                "quantum_backend_execution_required_flag": False,
                "no_quantum_advantage_claim": True,
                "live_order_authority": False,
            }
        )
    return rows
