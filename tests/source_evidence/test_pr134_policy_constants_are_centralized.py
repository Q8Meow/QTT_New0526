from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor import policy


def test_pr134_policy_constants_are_centralized():
    assert policy.STAGE1_VENUE_IDS == ("KALSHI", "POLYMARKET", "FORECASTEX_IBKR")
    assert policy.SHARED_SCOPE_IDS == ("PREDICTION_MARKETS_GENERAL",)
    assert policy.PRODUCER_REPO_PR == "PR134"
    assert policy.PRODUCER_ROADMAP_PR == "PR116"
    assert policy.UPSTREAM_REPO_PR == "PR133"
    assert policy.DOWNSTREAM_PR_IDS == ("PR117",)
    assert "READY_METADATA_ONLY" in policy.ALLOWED_RUNTIME_RESOLVER_READINESS_STATES
    assert "BLOCKED_LIVE_AUTHORITY_REQUIRED" in policy.ALLOWED_RUNTIME_RESOLVER_READINESS_STATES
    assert "atomicrows_row_records_created_count" in policy.ATOMICROWS_ZERO_AUTHORITY_FLAGS
