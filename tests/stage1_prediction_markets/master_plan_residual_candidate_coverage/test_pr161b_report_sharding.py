from .pr161b_test_support import summary


def test_pr161b_report_sharding_status_is_recorded():
    assert summary()["largest_report_size_bytes"] > 0
    assert summary()["report_sharding_status"] in {"NOT_REQUIRED_UNDER_50_MB", "REQUIRED"}
