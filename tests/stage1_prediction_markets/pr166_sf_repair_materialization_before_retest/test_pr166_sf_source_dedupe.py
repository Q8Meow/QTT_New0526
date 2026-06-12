from .conftest import assert_rows


def test_pr166_sf_source_dedupe_preserves_candidate_lane(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_SourceDedupeLedger.report.json")
    assert len(rows) == 10
    assert all(row["source_disagreement_status"] for row in rows)
    assert sum(row["preserved_disagreement_count"] for row in rows) == 0
