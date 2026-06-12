from .conftest import assert_rows


def test_pr166_sf_external_signals_are_candidate_provisional(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_ExternalRepairSignalRegistry.report.json")
    assert len(rows) == 10
    assert all(row["value_source_authority_class"] == "CANDIDATE_PROVISIONAL_NOT_SOURCE_TRUTH" for row in rows)
    assert all(row["source_truth_acceptance_count"] == 0 for row in rows)
