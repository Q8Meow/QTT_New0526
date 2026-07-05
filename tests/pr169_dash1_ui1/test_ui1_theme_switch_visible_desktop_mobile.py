from tests.pr169_dash1_ui1.conftest import boot_data, ui_text


def test_ui1_theme_switch_visible_desktop_mobile() -> None:
    data = boot_data()
    assert data["theme_contract"]["theme_switch_visible_in_desktop_header"] is False
    assert data["theme_contract"]["theme_switch_visible_or_accessible_in_mobile_navigation"] is False
    assert data["theme_contract"]["theme_switch_visible_only_after_owner_opens_menu"] is True
    assert data["theme_contract"]["strict_menu_only_header_chrome"] is True
    text = ui_text()
    assert "themeDark" in text
    assert "themeLight" in text
    assert "ownerOptionsToggle" in text
    assert "ownerOptionsPanel" in text
    assert "mobileThemeToggle" not in text
