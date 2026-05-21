from .pr134_runtime_resolver_snapshot_support import artifacts
from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor import policy


def test_pr134_builds_fixture_runtime_resolver_snapshots_for_three_stage1_venues():
    payload = artifacts()
    venues = {
        snapshot["venue_id"]
        for snapshot in payload["runtime_resolver_snapshots"]
        if snapshot.get("venue_id")
    }
    assert venues == set(policy.STAGE1_VENUE_IDS)
    assert sum(1 for snapshot in payload["runtime_resolver_snapshots"] if snapshot.get("venue_id")) == 3
    assert all(
        snapshot["fixture_runtime_resolver_snapshot_created"] is True
        for snapshot in payload["runtime_resolver_snapshots"]
        if snapshot.get("venue_id")
    )
