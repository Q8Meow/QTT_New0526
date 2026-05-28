from .helpers import counts


def test_pr159r_pr154_remaining_count_24(pr159r_artifacts):
    assert counts(pr159r_artifacts)["pr154_remaining_source_target_count"] == 24

