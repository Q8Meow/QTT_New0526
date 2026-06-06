def test_pr164_review_provenance_handoff(records, summary):
    rows = records("PR163_B_PR164ReviewProvenanceHandoff.report.json")
    assert len(rows) == summary["candidate_packet_universe_count"]
    assert all(row["review_required"] and row["review_evidence_refs"] for row in rows)
    assert all(not row["source_acceptance_created"] for row in rows)
