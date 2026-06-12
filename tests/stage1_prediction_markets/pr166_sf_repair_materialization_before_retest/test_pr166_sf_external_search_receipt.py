from .conftest import assert_rows


def test_pr166_sf_external_search_receipt_records_attempts(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_ExternalSearchReceipt.report.json")
    assert len(rows) == 10
    assert all(row["network_available_flag"] is True for row in rows)
    assert all(row["retrieval_attempted_flag"] is True for row in rows)
    assert all(row["source_truth_acceptance_count"] == 0 for row in rows)
