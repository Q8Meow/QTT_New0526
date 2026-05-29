from .pr161a_test_support import summary


def test_pr161a_institutional_optimizer_owner_defaults():
    assert summary()["institutional_default_candidate_count"] > 0
    assert summary()["optimizer_default_candidate_count"] > 0
    assert summary()["owner_internal_default_count"] > 0

