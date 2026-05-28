from .helpers import counts


def test_pr159r_no_optimizer_execution(pr159r_artifacts):
    assert counts(pr159r_artifacts)["optimizer_execution_count"] == 0

