from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_no_network_io_or_production_connector_client():
    assert support.main_report()["network_io_created_count"] == 0
    assert support.main_report()["production_connector_client_count"] == 0
    assert all(receipt["network_io_allowed_flag"] is False for receipt in support.read_receipts())
    assert all(
        receipt["production_connector_use_allowed_flag"] is False
        for receipt in support.read_receipts()
    )
