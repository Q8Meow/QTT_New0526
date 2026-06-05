def test_source_candidate_materialization_queue(summary, records):
    rows = records("PR162R_SourceCandidateMaterializationQueue.report.json")
    assert len(rows) == summary["source_candidate_materialization_row_count"]
    assert rows
    assert all(row["source_class"] == "REPO_LOCAL_ARTIFACT_CANDIDATE" for row in rows)
    assert all(row["source_locator"] for row in rows)
    assert all(row["no_accepted_source_truth_claim"] for row in rows)
