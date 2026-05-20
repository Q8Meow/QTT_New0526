from tests.source_evidence import pr131_credential_alias_readiness_support as support


def test_pr131_prediction_markets_general_is_shared_scope_not_fourth_venue():
    venue_ids = {record.get("venue_id") for record in support.alias_records()}
    scope_ids = {record.get("scope_id") for record in support.alias_records()}

    assert "PREDICTION_MARKETS_GENERAL" not in venue_ids
    assert "PREDICTION_MARKETS_GENERAL" in scope_ids
    assert support.main_report()["shared_scope_alias_count"] == 1
    assert support.main_report()["prediction_markets_general_treated_as_shared_scope"] is True
