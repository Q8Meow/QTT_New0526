def test_paper_venue_adapter_capability_matrix_has_all_venues(records):
    rows = records("PR163_PaperVenueAdapterCapabilityMatrix.report.json")
    venues = {row["venue_scope"] for row in rows}
    assert venues == {
        "KALSHI_PREDICTION_MARKETS",
        "POLYMARKET_CLOB",
        "FORECASTEX_IBKR_EVENT_MARKETS",
        "VENUE_NEUTRAL_SYNTHETIC_FIXTURE",
    }
    assert all(row["paper_execution_is_simulated"] for row in rows)
