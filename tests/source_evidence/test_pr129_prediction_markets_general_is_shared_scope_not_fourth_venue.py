from tests.source_evidence import pr129_runtime_cash_component_field_map_support as support


def test_prediction_markets_general_is_shared_scope_not_fourth_venue():
    report = support.field_map_report()

    assert set(report["active_stage1_venues"]) == support.stage1_venues()
    assert set(report["shared_scope_metadata"]) == {"PREDICTION_MARKETS_GENERAL"}
    assert "PREDICTION_MARKETS_GENERAL" not in {record["venue_id"] for record in support.field_maps()}
    assert support.main_report()["fixture_stage1_venue_count"] == 3
    assert support.main_report()["shared_scope_metadata_count"] == 1
