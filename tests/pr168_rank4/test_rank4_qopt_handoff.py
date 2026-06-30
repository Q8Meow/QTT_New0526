from ._helpers import rows


def test_qopt_handoff_has_structure_without_execution() -> None:
    for row in rows("qopt_batch.jsonl"):
        assert row["objective_coefficients_missing"] is False
        assert row["constraints_missing_when_claimed"] is False
        assert row["interpret_back_map_missing"] is False
        assert row["qopt_execution_flag"] is False
        assert row["quantum_backend_execution_flag"] is False
        assert row["quantum_advantage_claim_flag"] is False

