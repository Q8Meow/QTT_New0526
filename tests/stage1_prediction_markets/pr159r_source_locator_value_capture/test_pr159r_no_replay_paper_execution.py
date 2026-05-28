from .helpers import counts


def test_pr159r_no_replay_paper_execution(pr159r_artifacts):
    assert counts(pr159r_artifacts)["replay_paper_execution_count"] == 0

