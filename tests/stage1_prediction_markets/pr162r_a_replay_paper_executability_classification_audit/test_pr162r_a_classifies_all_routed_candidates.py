from __future__ import annotations


def test_pr162r_a_classifies_all_routed_candidates(summary, records):
    classifications = records("PR162R_A_ReplayPaperExecutabilityClassificationMatrix.report.json")
    assert summary["candidate_source_count"] == 548
    assert summary["candidates_classified_count"] == summary["candidate_source_count"]
    assert len(classifications) == summary["candidate_source_count"]
    assert len({row["candidate_id"] for row in classifications}) == len(classifications)
    assert summary["primary_classification_missing_count"] == 0
