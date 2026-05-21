from .pr134_runtime_resolver_snapshot_support import artifacts, failure_codes, mutable_artifacts
from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor import policy


def test_pr134_requires_pr133_orderbook_event_state_snapshot_handoff():
    payload = artifacts()
    assert not failure_codes(payload)
    assert (
        payload["orderbook_event_state_snapshot_downstream_handoff"]["handoff_id"]
        == policy.PR133_HANDOFF_ID
    )

    missing = mutable_artifacts()
    missing["orderbook_event_state_snapshot_downstream_handoff"] = None
    assert "MISSING_PR133_HANDOFF" in failure_codes(missing)
