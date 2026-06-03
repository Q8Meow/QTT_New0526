"""BQM problem descriptor."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BQMProblem:
    problem_id: str
    linear: tuple[float, ...]
    quadratic: tuple[tuple[int, int, float], ...]
    vartype: str = "BINARY"
    offset: float = 0.0

    @property
    def variable_count(self) -> int:
        return len(self.linear)
