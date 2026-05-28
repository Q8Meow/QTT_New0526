from .helpers import counts


def test_pr159r_target_universe_count_869(pr159r_artifacts):
    assert counts(pr159r_artifacts)["total_remaining_source_target_count"] == 869

