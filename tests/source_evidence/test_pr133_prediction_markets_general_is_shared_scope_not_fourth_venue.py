from tests.source_evidence import pr133_orderbook_event_state_snapshot_support as support


def test_pr133_prediction_markets_general_is_shared_scope_not_fourth_venue():
    assert "PREDICTION_MARKETS_GENERAL" not in {record.get("venue_id") for record in support.all_records()}
    assert "PREDICTION_MARKETS_GENERAL" in {record.get("scope_id") for record in support.all_records()}
    assert support.main_report()["stage1_venue_count"] == 3
    assert support.main_report()["prediction_markets_general_treated_as_shared_scope"] is True
