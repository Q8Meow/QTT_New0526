from .pr162d_test_support import assert_online_cache_offline_safe


def test_pr162d_online_scouting_cache_makes_ci_offline_safe():
    assert_online_cache_offline_safe()
