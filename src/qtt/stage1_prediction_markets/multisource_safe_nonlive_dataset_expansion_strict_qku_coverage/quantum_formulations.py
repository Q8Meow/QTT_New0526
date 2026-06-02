"""PR162C local quantum-formulation assembly helpers without backend execution."""

from __future__ import annotations


def qubo_to_ising_linear_terms(Q: list[list[float]]) -> dict[str, object]:
    if not Q or any(len(row) != len(Q) for row in Q):
        raise ValueError("Q must be a non-empty square matrix")
    h = []
    for i, row in enumerate(Q):
        diagonal = float(row[i])
        off_diagonal = sum(float(row[j]) + float(Q[j][i]) for j in range(len(Q)) if j != i)
        h.append(diagonal / 2.0 + off_diagonal / 4.0)
    return {
        "h": h,
        "variable_count": len(Q),
        "execution_status": "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE",
    }


def constraint_penalty(Ax_minus_b: float, penalty_lambda: float) -> float:
    return float(penalty_lambda) * float(Ax_minus_b) ** 2
