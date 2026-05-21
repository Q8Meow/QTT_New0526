from .pr134_runtime_resolver_snapshot_support import assert_malformed, failure_codes, mutable_artifacts


def test_pr134_rejects_replay_paper_live_order_profit():
    assert_malformed("malformed_replay_execution_created.v1.fixture.json", "REPLAY_EXECUTION_CREATED")
    assert_malformed("malformed_paper_execution_created.v1.fixture.json", "PAPER_EXECUTION_CREATED")
    assert_malformed("malformed_order_authority_created.v1.fixture.json", "ORDER_AUTHORITY_CREATED")
    payload = mutable_artifacts()
    payload["runtime_resolver_snapshots"][0]["live_trading_created"] = True
    assert "LIVE_TRADING_CREATED" in failure_codes(payload)
    payload = mutable_artifacts()
    payload["runtime_resolver_snapshots"][0]["profit_evidence_created"] = True
    assert "PROFIT_EVIDENCE_CREATED" in failure_codes(payload)
