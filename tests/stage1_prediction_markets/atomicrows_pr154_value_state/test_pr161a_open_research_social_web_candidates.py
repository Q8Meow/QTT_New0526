from .pr161a_test_support import summary


def test_pr161a_open_research_social_web_candidates():
    assert summary()["open_research_candidate_count"] >= 530
    assert summary()["social_web_forum_blog_news_candidate_count"] >= 58

