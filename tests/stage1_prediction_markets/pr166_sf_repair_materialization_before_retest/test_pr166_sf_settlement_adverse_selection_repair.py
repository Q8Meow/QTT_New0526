from .conftest import assert_rows


def test_pr166_sf_settlement_adverse_repair_has_actions(pr166_sf_records):
    rows = assert_rows(pr166_sf_records, "PR166_SF_SettlementAdverseRepairLedger.report.json")
    assert rows[0]["settlement_drag_repair_action"]
    assert rows[0]["adverse_selection_repair_action"]
    assert rows[0]["settlement_uncertainty_penalty"] >= 0
