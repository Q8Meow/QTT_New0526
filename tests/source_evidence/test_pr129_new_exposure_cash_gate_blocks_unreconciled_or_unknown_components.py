from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_new_exposure_cash_gate_blocks_unreconciled_or_unknown_components():
    receipts = {receipt["venue_id"]: receipt for receipt in support.gate_receipts()}

    assert receipts["KALSHI"]["new_or_increased_exposure_allowed_fixture"] is True
    assert receipts["FORECASTEX_IBKR"]["unknown_component_present_flag"] is True
    assert receipts["FORECASTEX_IBKR"]["unreconciled_component_present_flag"] is True
    assert receipts["FORECASTEX_IBKR"]["new_or_increased_exposure_allowed_fixture"] is False
    assert receipts["POLYMARKET"]["negative_or_zero_available_after_commitments_flag"] is True
