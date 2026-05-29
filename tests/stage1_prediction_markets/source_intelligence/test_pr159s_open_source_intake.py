from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c
from tests.stage1_prediction_markets.source_intelligence.pr159s_test_support import load


def test_pr159s_open_source_intake_accepts_non_official_candidates():
    intake = load(c.OPEN_RESEARCH_SOURCE_INTAKE_PATH)
    assert intake["record_count"] == 530
    assert intake["accepted_open_research_candidate_count"] == 530
    assert all(record["external_code_executed_flag"] is False for record in intake["records"])
    assert {
        c.OpenResearchSourceClass.ACADEMIC_PAPER.value,
        c.OpenResearchSourceClass.PREPRINT.value,
        c.OpenResearchSourceClass.GITHUB_REPOSITORY.value,
        c.OpenResearchSourceClass.FORUM_THREAD.value,
    }.issubset({record["source_class"] for record in intake["records"]})

