"""Quantum-ready default helper for PR161A."""

from __future__ import annotations

from . import constants as c


def quantum_ready_default_basis() -> str:
    return c.DefaultBasis.QUANTUM_READY_QTT_CANDIDATE_DEFAULT.value

