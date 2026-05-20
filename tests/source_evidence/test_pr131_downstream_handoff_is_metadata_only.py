from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_downstream_handoff_is_metadata_only():
    handoff = support.downstream_handoff()

    assert handoff["downstream_may_consume_metadata_only"] is True
    assert handoff["downstream_may_resolve_credentials"] is False
    assert handoff["downstream_may_call_provider"] is False
    assert handoff["contains_secrets"] is False
    assert handoff["contains_production_authority"] is False
