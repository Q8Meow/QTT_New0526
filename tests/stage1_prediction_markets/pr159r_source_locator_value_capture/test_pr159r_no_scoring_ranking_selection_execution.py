from .helpers import counts


def test_pr159r_no_scoring_ranking_selection_execution(pr159r_artifacts):
    assert counts(pr159r_artifacts)["scoring_ranking_selection_execution_count"] == 0

