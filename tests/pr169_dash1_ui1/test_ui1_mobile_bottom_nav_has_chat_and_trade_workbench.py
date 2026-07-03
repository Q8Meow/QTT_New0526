from tests.pr169_dash1_ui1.conftest import boot_data, ui_text


def test_ui1_mobile_bottom_nav_has_chat_and_trade_workbench() -> None:
    nav = boot_data()["mobile_navigation"]
    assert nav["chat_tab_rendered_in_mobile_navigation"] is True
    assert nav["trade_workbench_tab_rendered_in_mobile_navigation"] is True
    text = ui_text()
    assert ">Chat<" in text
    assert ">Trade Workbench<" in text
