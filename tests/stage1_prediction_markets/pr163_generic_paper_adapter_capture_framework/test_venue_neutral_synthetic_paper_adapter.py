def test_venue_neutral_synthetic_adapter_is_executable(records):
    row = next(row for row in records("PR163_PaperVenueAdapterCapabilityMatrix.report.json") if row["venue_scope"] == "VENUE_NEUTRAL_SYNTHETIC_FIXTURE")
    assert "deterministic_orderbook" in row["supported_features"]
    assert "synthetic_fill_events" in row["supported_features"]
