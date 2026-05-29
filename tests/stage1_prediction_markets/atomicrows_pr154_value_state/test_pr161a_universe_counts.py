from .pr161a_test_support import summary


def test_pr161a_universe_counts():
    assert summary()["atomicrows_universe_observed_count"] == 4183
    assert summary()["pr154_universe_observed_count"] == 342
    assert summary()["combined_entity_processed_count"] == 4525

