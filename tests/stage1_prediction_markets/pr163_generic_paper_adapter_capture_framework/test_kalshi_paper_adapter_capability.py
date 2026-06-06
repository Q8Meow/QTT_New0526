def test_kalshi_capability_separates_demo_and_live(records):
    row = next(row for row in records("PR163_PaperVenueAdapterCapabilityMatrix.report.json") if row["venue_scope"] == "KALSHI_PREDICTION_MARKETS")
    assert "demo_environment_separated_from_live_exchange" in row["supported_features"]
    assert row["live_connector_activation"] is False
