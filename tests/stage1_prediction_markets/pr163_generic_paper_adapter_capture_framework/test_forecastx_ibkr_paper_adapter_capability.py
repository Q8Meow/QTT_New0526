def test_forecastex_ibkr_capability_keeps_private_state_out(records):
    row = next(row for row in records("PR163_PaperVenueAdapterCapabilityMatrix.report.json") if row["venue_scope"] == "FORECASTEX_IBKR_EVENT_MARKETS")
    assert "no_private_account_state" in row["supported_features"]
    assert row["private_state_fetch_allowed"] is False
