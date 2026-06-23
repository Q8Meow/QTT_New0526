from tests.pr168_recovery1._helpers import assert_recovery1_valid, rows


def test_quantum_repair_has_classical_fallback_no_backend() -> None:
    assert_recovery1_valid()
    assert all(row["classical_fallback_exists"] is not None and not row["quantum_backend_execution_flag"] for row in rows("quantum_repair"))
