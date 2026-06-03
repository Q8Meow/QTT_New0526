"""QUBO problem model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QUBOProblem:
    problem_id: str
    q_matrix: tuple[tuple[float, ...], ...]
    constant_offset: float = 0.0
    description: str = "QUBO objective x^T Q x + c"

    @property
    def variable_count(self) -> int:
        return len(self.q_matrix)


def validate_qubo_matrix(q_matrix: list[list[float]] | tuple[tuple[float, ...], ...]) -> tuple[tuple[float, ...], ...]:
    matrix = tuple(tuple(float(value) for value in row) for row in q_matrix)
    if not matrix:
        raise ValueError("QUBO matrix must not be empty")
    width = len(matrix)
    if any(len(row) != width for row in matrix):
        raise ValueError("QUBO matrix must be square")
    return matrix
