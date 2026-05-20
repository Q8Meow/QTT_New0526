from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_no_production_connector_client_or_order_authority():
    assert support.main_report()["production_connector_client_count"] == 0
    assert support.main_report()["production_connector_authority_created_count"] == 0
    assert support.main_report()["order_authority_created_count"] == 0
    assert support.main_report()["order_execution_created_count"] == 0
