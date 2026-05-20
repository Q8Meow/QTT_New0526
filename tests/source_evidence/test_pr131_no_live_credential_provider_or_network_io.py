from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_no_live_credential_provider_or_network_io():
    assert support.main_report()["credential_provider_call_count"] == 0
    assert support.main_report()["network_io_created_count"] == 0
    assert all(record["credential_provider_called"] is False for record in support.alias_records())
    assert all(record["network_io_created"] is False for record in support.alias_records())
