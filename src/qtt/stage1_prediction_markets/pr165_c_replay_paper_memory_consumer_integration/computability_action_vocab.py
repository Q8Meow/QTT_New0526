"""Computability action lattice for PR165-C."""

from __future__ import annotations

COMPUTABILITY_ACTIONS = (
    "COMPUTABLE_READY",
    "COMPUTABLE_WITH_PROVISIONAL_VALUE",
    "COMPUTABLE_AFTER_REPAIR",
    "COMPUTABLE_AFTER_RETEST",
    "COMPUTABLE_AFTER_QUANTUM_FORMULATION_REPAIR",
)


def is_computability_action(value: str) -> bool:
    return value in COMPUTABILITY_ACTIONS
