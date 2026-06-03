"""Classical baseline comparator for quantum local smoke results."""

from __future__ import annotations

from typing import Any


def comparator_record(
    comparator_id: str,
    quantum_smoke_ref: str,
    quantum_value: float,
    classical_value: float,
) -> dict[str, Any]:
    return {
        "comparator_id": comparator_id,
        "quantum_smoke_ref": quantum_smoke_ref,
        "strongest_classical_comparator": "LOCAL_EXACT_ENUMERATION_BASELINE",
        "quantum_candidate_objective_value": quantum_value,
        "classical_baseline_objective_value": classical_value,
        "objective_value_delta": float(quantum_value) - float(classical_value),
        "comparator_status": "LOCAL_SMOKE_SANITY_ONLY_NOT_ADVANTAGE_EVIDENCE",
        "profit_evidence_claim_flag": False,
        "quantum_advantage_claim_flag": False,
        "live_order_authority": False,
    }
