from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_preserves_future_production_launch_path():
    assert support.main_report()["future_production_launch_path_preserved"] is True
    assert all(
        binding["live_use_requires_future_owner_approval"] is True
        and binding["live_use_requires_future_credential_provider_receipt"] is True
        and binding["live_use_requires_future_connector_receipt"] is True
        and binding["live_use_requires_future_source_evidence_clearance"] is True
        for binding in support.scope_bindings()
    )
