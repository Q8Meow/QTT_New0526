from tests.pr169_dash1_ui1.conftest import boot_data, ui_text


def test_ui1_trade_workbench_visible() -> None:
    workbench = boot_data()["trade_workbench"]
    assert workbench["workbench_id"] == "OWNER_TRADE_WORKBENCH"
    assert workbench["local_static_preview_only"] is True
    assert "Trade Workbench" in ui_text()
    assert "OwnerTradeIntentV1" in ui_text()
