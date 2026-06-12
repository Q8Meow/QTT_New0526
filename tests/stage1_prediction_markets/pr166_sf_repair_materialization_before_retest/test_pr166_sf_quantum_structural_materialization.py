from .conftest import assert_rows


def test_pr166_sf_quantum_structure_materializes_coefficients(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_QuantumStructureLedger.report.json")
    for row in rows[:100]:
        assert row["objective_direction"]
        assert row["variables"]
        assert row["constraints"]
        assert row["linear_coefficients"]
        assert row["comparator_baseline"]
