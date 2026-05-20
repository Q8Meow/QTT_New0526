from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_available_after_commitments_clamps_negative_to_zero_for_exposure_eligibility():
    polymarket = next(
        receipt for receipt in support.available_receipts() if receipt["venue_id"] == "POLYMARKET"
    )

    assert polymarket["raw_available_after_commitments_fixture"]["amount"] == "-5.00"
    assert polymarket["available_after_commitments_for_new_exposure_fixture"]["amount"] == "0.00"
    assert polymarket["negative_available_after_commitments_clamped_to_zero_flag"] is True
    assert support.main_report()["negative_available_after_commitments_clamped_to_zero_count"] == 1
