from tests.source_evidence import pr130_private_state_read_receipt_support as support


def test_pr130_prediction_markets_general_is_shared_scope_not_fourth_venue():
    assert support.shared_scope_metadata() == {"PREDICTION_MARKETS_GENERAL"}
    assert "PREDICTION_MARKETS_GENERAL" not in support.stage1_venues()
    assert all(
        record["platform_scope"] == "PREDICTION_MARKETS_GENERAL"
        for record in support.read_receipts()
    )
    assert support.main_report()["prediction_markets_general_treated_as_shared_scope"] is True
