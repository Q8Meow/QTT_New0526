from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_no_private_state_fetch():
    assert support.main_report()["private_state_fetch_created_count"] == 0
    assert all(record["no_private_state_fetch"] is True for record in support.readiness_receipts())
