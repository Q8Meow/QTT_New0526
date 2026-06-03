"""Quantum/classical comparator envelopes."""

from __future__ import annotations

from .classical_baseline_comparator import comparator_record


def quantum_comparator_result_envelope(
    comparator_id: str,
    smoke_ref: str,
    quantum_value: float,
    classical_value: float,
) -> dict[str, object]:
    return comparator_record(comparator_id, smoke_ref, quantum_value, classical_value)
