from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_no_environment_variable_or_secret_manager_access():
    assert support.main_report()["environment_variable_read_count"] == 0
    assert support.main_report()["secret_manager_call_count"] == 0
    assert all(record["no_environment_read"] is True for record in support.readiness_receipts())
    assert all(record["no_secret_manager_call"] is True for record in support.readiness_receipts())
