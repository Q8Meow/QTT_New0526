"""VQE and SamplingVQE objective descriptors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VQEDescriptor:
    descriptor_id: str
    hamiltonian_term_count: int
    ansatz_family: str
    estimator_mode: str = "DRY_RUN_OR_LOCAL_IF_AVAILABLE"
