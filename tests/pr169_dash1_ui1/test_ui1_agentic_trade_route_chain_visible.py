from tests.pr169_dash1_ui1.conftest import boot_data, ui_text


def test_ui1_agentic_trade_route_chain_visible() -> None:
    workbench = boot_data()["trade_workbench"]
    chain = workbench["route_chain"]
    assert chain[0] == "OwnerTradeIntentV1"
    assert "OwnerTradeCheckRequestV1" in chain
    assert "Execution_Router_release_route_provider_pending" in chain
    assert "CHECK_TRADE_WITH_QTT_AGENTS" in ui_text()
    assert workbench["direct_venue_submit_allowed"] is False
