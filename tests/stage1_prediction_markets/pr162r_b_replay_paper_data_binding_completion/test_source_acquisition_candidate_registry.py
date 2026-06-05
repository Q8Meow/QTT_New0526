def test_source_acquisition_candidate_registry(records):
    rows = records("PR162R_B_SourceAcquisitionCandidateRegistry.report.json")
    classes = {row["source_class"] for row in rows}
    assert "OFFICIAL_SOURCE_CANDIDATE" in classes
    assert "NON_OFFICIAL_WEB_CANDIDATE" in classes
    assert "SYNTHETIC_TEST_FIXTURE" in classes
    assert all(row["live_allowed"] is False for row in rows)
