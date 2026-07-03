from tests.pr169_dash1_ui1.conftest import boot_data, ui_text


def test_ui1_no_direct_venue_submit_or_execution_router_release() -> None:
    data = boot_data()
    assert data["owner_trade_command"]["direct_venue_submit_allowed"] is False
    assert data["owner_trade_command"]["execution_router_release_authority_owned_by_UI1"] is False
    assert data["trade_workbench"]["execution_router_release_required"] is True
    assert "No direct venue submit" in ui_text()
