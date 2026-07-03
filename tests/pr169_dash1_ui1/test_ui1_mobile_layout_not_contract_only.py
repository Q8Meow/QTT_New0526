from tests.pr169_dash1_ui1.conftest import boot_data, ui_text


def test_ui1_mobile_layout_not_contract_only() -> None:
    data = boot_data()
    nav = data["mobile_navigation"]
    text = ui_text()
    assert nav["actual_responsive_desktop_mobile_rendering"] is True
    assert nav["mobile_bottom_navigation_rendered"] is True
    assert "mobile-bottom-nav" in text
    assert "@media (max-width: 767px)" in text
