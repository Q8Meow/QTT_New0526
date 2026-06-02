"""Local deterministic PR162B smoke execution helpers."""

from __future__ import annotations

from .quantum_formulations import exact_qubo_smoke_solve, ising_energy, qubo_energy


def quantum_smoke_records() -> list[dict[str, object]]:
    qubo_q = [[2.0, 3.0], [0.0, 4.0]]
    ising_h = [1.0, -0.5]
    ising_j = {(0, 1): 0.25}
    qubo_solution = exact_qubo_smoke_solve(qubo_q, max_variables=12)
    return [
        {
            "smoke_id": "PR162B-SMOKE-QUBO-ENERGY-001",
            "formula_ref": "PR162B-FORMULA-QUBO_OBJECTIVE_XTQX",
            "inputs": {"x": [1, 0], "Q": qubo_q},
            "observed_output": qubo_energy([1, 0], qubo_q),
            "smoke_execution_status": "SMOKE_EXECUTED_NO_TRADING_EVIDENCE",
            "creates_trading_evidence": False,
        },
        {
            "smoke_id": "PR162B-SMOKE-ISING-ENERGY-001",
            "formula_ref": "PR162B-FORMULA-ISING_ENERGY",
            "inputs": {"spins": [1, -1], "h": ising_h, "J": {"0,1": 0.25}},
            "observed_output": ising_energy([1, -1], ising_h, ising_j),
            "smoke_execution_status": "SMOKE_EXECUTED_NO_TRADING_EVIDENCE",
            "creates_trading_evidence": False,
        },
        {
            "smoke_id": "PR162B-SMOKE-QUBO-EXACT-ENUMERATION-001",
            "algorithm_ref": "PR162B-ALGORITHM-EXACT_QUBO_SMOKE_ENUMERATION_ALGORITHM",
            "inputs": {"Q": qubo_q, "max_variables": 12},
            "observed_output": qubo_solution,
            "smoke_execution_status": qubo_solution["status"],
            "creates_trading_evidence": False,
        },
    ]
