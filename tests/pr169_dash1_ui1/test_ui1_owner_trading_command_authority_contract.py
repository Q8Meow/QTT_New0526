from tests.pr169_dash1_ui1.conftest import boot_data


def test_ui1_owner_trading_command_authority_contract() -> None:
    contract = boot_data()["owner_trade_command"]
    assert contract["owner_trading_command_authority_contract"] is True
    assert contract["dashboard_exposes_first_six_as_request_previews"] is True
    assert "OWNER_APPROVAL_AUTHORITY" in contract["authority_levels"]
    assert contract["direct_venue_submit_allowed"] is False
