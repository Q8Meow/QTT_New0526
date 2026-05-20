from tests.source_evidence import pr132_market_data_ingest_support as support


def test_pr132_prediction_markets_general_is_shared_scope_not_fourth_venue():
    report = support.main_report()
    shared_index = report["PR132_MARKET_SPECIFIC_SECTION_INDEX"][
        "shared_scope_entries"
    ][0]

    assert report["prediction_markets_general_treated_as_shared_scope"] is True
    assert report["stage1_venue_count"] == 3
    assert shared_index["scope_id"] == "PREDICTION_MARKETS_GENERAL"
    assert shared_index["not_counted_as_venue"] is True
    assert "PREDICTION_MARKETS_GENERAL" not in {
        record.get("venue_id") for record in support.adapter_inputs()
    }
