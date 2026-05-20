from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_rejects_missing_or_malformed_pr132_handoff():
    missing = support.cloned_artifacts()
    missing["pr132_handoff"] = None
    assert any("missing PR132" in failure for failure in support.validation_failures(missing))

    malformed = support.cloned_artifacts()
    malformed["pr132_handoff"]["producer_pr"] = "PR999"
    assert any("producer_pr" in failure for failure in support.validation_failures(malformed))
