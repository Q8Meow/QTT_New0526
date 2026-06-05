def test_source_candidate_to_binding_map(summary, records):
    rows = records("PR162R_B_SourceCandidateToBindingMap.report.json")
    assert len(rows) == summary["source_candidate_to_binding_rows"] > 0
    assert all(row["no_source_acceptance"] for row in rows)
