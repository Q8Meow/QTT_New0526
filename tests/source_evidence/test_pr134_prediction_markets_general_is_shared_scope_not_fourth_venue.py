from .pr134_runtime_resolver_snapshot_support import artifacts
from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor import policy


def test_prediction_markets_general_is_shared_scope_not_fourth_venue():
    payload = artifacts()
    shared = [
        record
        for record in payload["runtime_resolver_bindings"]
        if record.get("scope_id") == "PREDICTION_MARKETS_GENERAL"
    ]
    venues = [record for record in payload["runtime_resolver_bindings"] if record.get("venue_id")]
    assert len(shared) == 1
    assert len(venues) == 3
    assert "PREDICTION_MARKETS_GENERAL" not in policy.STAGE1_VENUE_IDS
    assert shared[0]["scope_id"] in policy.SHARED_SCOPE_IDS
