from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_rejects_unknown_cash_component_for_new_exposure():
    rejections = support.unknown_rejections()
    forecastex_gate = next(
        receipt for receipt in support.gate_receipts() if receipt["venue_id"] == "FORECASTEX_IBKR"
    )

    assert len(rejections) == 1
    assert rejections[0]["cash_component_class"] == "UNKNOWN_OR_UNRECONCILED_COMPONENT"
    assert rejections[0]["runtime_cash_field_map_state"] == "REJECTED_UNKNOWN_CASH_COMPONENT"
    assert forecastex_gate["new_or_increased_exposure_allowed_fixture"] is False
    assert "UNKNOWN_CASH_COMPONENT_PRESENT" in forecastex_gate["blocked_reason_codes"]
