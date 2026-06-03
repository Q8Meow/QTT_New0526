"""Quantum metadata-only rejection audit."""

from __future__ import annotations

from typing import Any


def quantum_metadata_only_rejection_records(quantum: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rejected = [record for record in quantum if record.get("quantum_metadata_only_flag")]
    return [
        {
            "audit_id": "PR162D_R1_QUANTUM_METADATA_ONLY_REJECTION_AUDIT",
            "quantum_metadata_only_count": len(rejected),
            "rejected_quantum_metadata_only_candidate_ids": [record["candidate_id"] for record in rejected],
            "validation_status": "PASS_NO_QUANTUM_METADATA_ONLY_RECORDS" if not rejected else "FAIL",
            "live_order_authority": False,
        }
    ]
