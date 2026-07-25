from pathlib import Path

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_adapter import (
    PR162EQuantumAdapterV1,
    QuantumModelKind,
)


def test_pr162e_q_mapper_is_consumed_without_backend_authority() -> None:
    root = Path(__file__).resolve().parents[4]
    rows = PR162EQuantumAdapterV1(root).load_mappings(QuantumModelKind.QUBO)
    assert rows
    assert all(row.source_owner == "PR162E_Q_QUANTUM_AUTOMAPPER" for row in rows)
    assert all(row.model_kind is QuantumModelKind.QUBO for row in rows)
    assert not any(row.backend_execution_allowed for row in rows)
