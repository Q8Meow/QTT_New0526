from tests.pr169_dash1_ui1.conftest import boot_data, ui_text


def test_ui1_theme_switch_dark_light_modes() -> None:
    data = boot_data()
    theme = data["theme_contract"]
    text = ui_text()
    assert {"DARK", "LIGHT", "DARK_PRO", "MIDNIGHT_BLUE", "SLATE", "LIGHT_PRO", "LOW_GLARE", "HIGH_CONTRAST", "CUSTOM"} <= set(theme["supported_modes"])
    assert ':root[data-theme="dark"]' in text
    assert ':root[data-theme="light"]' in text
    assert ':root[data-theme="midnight_blue"]' in text
    assert ':root[data-theme="high_contrast"]' in text
    assert 'data-theme="dark"' in text
