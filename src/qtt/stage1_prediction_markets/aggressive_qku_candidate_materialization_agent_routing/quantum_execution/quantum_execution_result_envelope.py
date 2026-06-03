"""Quantum execution result envelopes for local non-live smoke."""

from __future__ import annotations

from typing import Any


def quantum_execution_result_envelope(
    smoke_id: str,
    problem_model_ref: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "quantum_smoke_execution_id": smoke_id,
        "problem_model_ref": problem_model_ref,
        "execution_mode": "QUANTUM_LOCAL_EXACT_SMOKE",
        "result": result,
        "result_packet_created_flag": False,
        "profit_evidence_claim_flag": False,
        "quantum_advantage_claim_flag": False,
        "live_order_authority": False,
    }
