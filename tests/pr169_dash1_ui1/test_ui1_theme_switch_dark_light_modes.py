from tests.pr169_dash1_ui1.conftest import boot_data, ui_text


def test_ui1_theme_switch_dark_light_modes() -> None:
    data = boot_data()
    theme = data["theme_contract"]
    text = ui_text()
    assert theme["supported_modes"] == ["DARK", "LIGHT"]
    assert ':root[data-theme="dark"]' in text
    assert ':root[data-theme="light"]' in text
    assert 'data-theme="dark"' in text
