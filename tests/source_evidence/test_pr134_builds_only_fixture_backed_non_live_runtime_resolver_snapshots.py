from .pr134_runtime_resolver_snapshot_support import artifacts


def test_pr134_builds_only_fixture_backed_non_live_runtime_resolver_snapshots():
    for snapshot in artifacts()["runtime_resolver_snapshots"]:
        assert snapshot["fixture_runtime_resolver_snapshot_created"] is True
        assert snapshot["live_runtime_resolver_authority_created"] is False
        assert snapshot["live_market_data_fetch_created"] is False
        assert snapshot["network_io_created"] is False
        assert snapshot["runtime_resolver_snapshot_is_feature_vector"] is False
        assert snapshot["runtime_resolver_snapshot_is_trading_signal"] is False
        assert snapshot["runtime_resolver_snapshot_is_order_authority"] is False
