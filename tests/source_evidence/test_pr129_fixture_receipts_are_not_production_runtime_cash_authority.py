from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_fixture_receipts_are_not_production_runtime_cash_authority():
    main = support.main_report()

    assert main["production_runtime_cash_authority_count"] == 0
    assert main["production_runtime_cash_receipt_authority_count"] == 0
    assert main["production_new_exposure_cash_gate_authority_count"] == 0
    assert all(record["production_runtime_cash_authority"] is False for record in support.field_maps())
    assert all(
        receipt["production_runtime_cash_receipt_authority"] is False
        for receipt in support.available_receipts()
    )
