"""Ising problem model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IsingProblem:
    problem_id: str
    h: tuple[float, ...]
    j: tuple[tuple[int, int, float], ...]
    constant_offset: float = 0.0
    description: str = "Ising energy sum h_i s_i + sum J_ij s_i s_j"

    @property
    def variable_count(self) -> int:
        return len(self.h)


def validate_ising_terms(
    h: list[float] | tuple[float, ...],
    j: list[tuple[int, int, float]] | tuple[tuple[int, int, float], ...],
) -> tuple[tuple[float, ...], tuple[tuple[int, int, float], ...]]:
    fields = tuple(float(value) for value in h)
    if not fields:
        raise ValueError("Ising h must not be empty")
    couplers = []
    for i, k, value in j:
        if i == k:
            raise ValueError("Ising self-couplers are not accepted")
        if min(i, k) < 0 or max(i, k) >= len(fields):
            raise ValueError("Ising coupler index out of range")
        couplers.append((int(i), int(k), float(value)))
    return fields, tuple(couplers)
