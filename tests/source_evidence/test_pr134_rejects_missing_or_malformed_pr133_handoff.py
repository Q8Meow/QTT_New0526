from .pr134_runtime_resolver_snapshot_support import assert_malformed, failure_codes, mutable_artifacts


def test_pr134_rejects_missing_or_malformed_pr133_handoff():
    assert_malformed("malformed_missing_pr133_handoff.v1.fixture.json", "MISSING_PR133_HANDOFF")

    malformed = mutable_artifacts()
    malformed["orderbook_event_state_snapshot_downstream_handoff"]["handoff_id"] = "WRONG"
    assert "MALFORMED_PR133_HANDOFF" in failure_codes(malformed)
