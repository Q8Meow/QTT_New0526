from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_no_order_execution_or_order_authority():
    main = support.main_report()

    assert main["production_order_authority_count"] == 0
    assert main["order_authority_created"] is False
    assert all(receipt["order_authority_allowed_flag"] is False for receipt in support.gate_receipts())
    assert all(
        receipt["production_order_authority_allowed_flag"] is False
        for receipt in support.gate_receipts()
    )
