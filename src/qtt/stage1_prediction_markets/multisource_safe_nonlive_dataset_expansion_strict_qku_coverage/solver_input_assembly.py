"""PR162C solver input assembly metadata without solving."""

from __future__ import annotations


def assemble_qubo_input(variable_ids: list[str], Q: list[list[float]]) -> dict[str, object]:
    if not variable_ids:
        raise ValueError("variable_ids must not be empty")
    if len(Q) != len(variable_ids) or any(len(row) != len(variable_ids) for row in Q):
        raise ValueError("Q dimensions must match variable_ids")
    return {
        "input_representation": "QUBO_MATRIX",
        "variable_ids": list(variable_ids),
        "term_count": sum(1 for row in Q for value in row if float(value) != 0.0),
        "execution_status": "SOLVER_INPUT_ASSEMBLED_NO_EVIDENCE_SOLVE",
    }
