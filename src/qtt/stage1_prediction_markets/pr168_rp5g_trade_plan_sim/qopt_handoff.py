"""QOPT1 handoff boundary helpers."""

from __future__ import annotations


def qopt_boundary_flags() -> dict[str, object]:
    return {
        "qopt_execution_flag": False,
        "quantum_backend_execution_flag": False,
        "quantum_advantage_claim_flag": False,
        "classical_fallback_required_flag": True,
        "future_qopt1_consumer_refs": ["QOPT1"],
    }

