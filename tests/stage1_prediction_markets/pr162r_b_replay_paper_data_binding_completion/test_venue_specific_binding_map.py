def test_venue_specific_binding_map(records):
    rows = records("PR162R_B_VenueSpecificBindingMap.report.json")
    venues = {row["venue_scope"] for row in rows}
    assert venues == {
        "KALSHI_PREDICTION_MARKETS",
        "POLYMARKET_CLOB",
        "FORECASTEX_IBKR_EVENT_MARKETS",
        "VENUE_NEUTRAL_SYNTHETIC_FIXTURE",
    }
    assert all(row["no_live_connector_binding"] for row in rows)
