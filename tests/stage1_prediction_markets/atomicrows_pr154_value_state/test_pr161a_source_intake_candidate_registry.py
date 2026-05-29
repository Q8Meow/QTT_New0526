from .pr161a_test_support import records, summary


def test_pr161a_source_intake_candidate_registry_counts():
    assert len(records("source_intake")) == summary()["source_intake_candidate_count"]
    assert summary()["official_source_candidate_count"] == 338
    assert summary()["open_research_candidate_count"] >= 530
    assert summary()["github_research_pattern_candidate_count"] >= 59

