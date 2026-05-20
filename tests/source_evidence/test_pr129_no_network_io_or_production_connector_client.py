from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_no_network_io_or_production_connector_client():
    main = support.main_report()

    assert main["network_io_created_count"] == 0
    assert main["production_connector_client_count"] == 0
    assert all(record["network_io_allowed_flag"] is False for record in support.field_maps())
    assert all(record["production_connector_use_allowed_flag"] is False for record in support.field_maps())
