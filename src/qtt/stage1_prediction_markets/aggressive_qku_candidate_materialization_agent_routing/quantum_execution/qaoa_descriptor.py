"""QAOA objective descriptor."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QAOADescriptor:
    descriptor_id: str
    source_problem_ref: str
    reps: int
    optimizer: str
    sampler_mode: str = "DRY_RUN_OR_LOCAL_IF_AVAILABLE"
