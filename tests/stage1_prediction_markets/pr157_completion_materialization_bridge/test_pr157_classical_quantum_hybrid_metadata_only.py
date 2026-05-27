from src.qtt.stage1_prediction_markets.pr157_completion_materialization_bridge import constants as c
from tests.stage1_prediction_markets.pr157_completion_materialization_bridge.test_support import atomic_records


def test_pr157_classical_quantum_hybrid_metadata_only():
    quantum = [
        record for record in atomic_records()
        if record["source_requirement_class"] == c.AtomicRowsSourceRequirementClass.QUANTUM_CLASSICAL_METADATA_ONLY.value
    ]
    assert len(quantum) == 1103
    assert all(record["no_authority_confirmation"]["quantum_backend_execution_created"] is False for record in quantum)
    assert any(c.QuantumClassicalCompatibility.HYBRID_CLASSICAL_QUANTUM_CANDIDATE.value in record["quantum_classical_compatibility"] for record in quantum)
