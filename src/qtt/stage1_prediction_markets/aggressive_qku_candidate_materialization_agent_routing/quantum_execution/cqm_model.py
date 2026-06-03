"""CQM problem descriptor."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CQMConstraint:
    name: str
    coefficients: tuple[float, ...]
    sense: str
    rhs: float


@dataclass(frozen=True)
class CQMProblem:
    problem_id: str
    objective_linear: tuple[float, ...]
    constraints: tuple[CQMConstraint, ...]
    vartype: str = "BINARY"

    @property
    def variable_count(self) -> int:
        return len(self.objective_linear)
