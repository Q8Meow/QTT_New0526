from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_no_network_or_secrets_manager_imports():
    assert support.main_report()["network_import_count"] == 0
    assert support.main_report()["secrets_manager_import_count"] == 0
    assert support.main_report()["environment_credential_read_count"] == 0
