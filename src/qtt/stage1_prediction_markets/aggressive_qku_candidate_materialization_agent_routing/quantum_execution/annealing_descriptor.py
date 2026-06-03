"""Annealing objective descriptor."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnnealingDescriptor:
    descriptor_id: str
    source_problem_ref: str
    reads: int
    sampler_family: str = "BQM_OR_CQM_ANNEALING_DRY_RUN"
