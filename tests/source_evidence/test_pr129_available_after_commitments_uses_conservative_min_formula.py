from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_available_after_commitments_uses_conservative_min_formula():
    receipts = {receipt["venue_id"]: receipt for receipt in support.available_receipts()}

    assert receipts["KALSHI"]["raw_available_after_commitments_fixture"] == {
        "amount": "65.00",
        "currency": "USD",
    }
    assert receipts["KALSHI"]["available_after_commitments_for_new_exposure_fixture"] == {
        "amount": "65.00",
        "currency": "USD",
    }
    assert support.main_report()["conservative_min_formula_applied"] is True
