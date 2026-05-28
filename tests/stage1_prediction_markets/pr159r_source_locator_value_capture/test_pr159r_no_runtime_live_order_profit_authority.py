from .helpers import counts


def test_pr159r_no_runtime_live_order_profit_authority(pr159r_artifacts):
    assert counts(pr159r_artifacts)["runtime_live_order_profit_authority_count"] == 0

