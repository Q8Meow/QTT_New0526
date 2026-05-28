from .helpers import counts


def test_pr159r_orphan_target_count_zero(pr159r_artifacts):
    assert counts(pr159r_artifacts)["orphan_target_count"] == 0

