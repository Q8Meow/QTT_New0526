from .conftest import assert_rows


def test_pr166_sf_quantum_router_covers_quantum_universe(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_QuantumRepairRouter.report.json")
    assert len(rows) == 6502
    assert all(row["backend_quantum_execution_created"] is False for row in rows[:100])
    assert all(row["quantum_advantage_claim_created"] is False for row in rows[:100])
