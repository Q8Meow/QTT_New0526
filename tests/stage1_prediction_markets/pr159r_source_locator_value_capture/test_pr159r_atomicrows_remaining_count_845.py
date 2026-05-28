from .helpers import counts


def test_pr159r_atomicrows_remaining_count_845(pr159r_artifacts):
    assert counts(pr159r_artifacts)["atomicrows_remaining_source_target_count"] == 845

