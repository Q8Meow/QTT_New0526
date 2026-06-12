from .conftest import assert_rows


def test_pr166_sf_test_vectors_exist_for_targets(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_TestVectorRegistry.report.json")
    assert len(rows) == 6502
    for row in rows[:50]:
        assert row["test_vector_inputs"]
        assert "expected_output" in row
