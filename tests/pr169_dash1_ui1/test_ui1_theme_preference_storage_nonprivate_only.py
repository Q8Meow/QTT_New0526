from tests.pr169_dash1_ui1.conftest import THEME_STORAGE_KEY, boot_data, ui_text


def test_ui1_theme_preference_storage_nonprivate_only() -> None:
    data = boot_data()
    theme = data["theme_contract"]
    text = ui_text()
    assert theme["localStorage_key"] == THEME_STORAGE_KEY
    assert {"DARK", "LIGHT", "DARK_PRO", "MIDNIGHT_BLUE", "SLATE", "LIGHT_PRO", "LOW_GLARE", "HIGH_CONTRAST", "CUSTOM"} <= set(theme["stored_values_allowed"])
    assert theme["credential_access"] is False
    assert theme["network_call"] is False
    assert THEME_STORAGE_KEY in text
    assert "localStorage.setItem(THEME_STORAGE_KEY" in text
    assert "OWNER_SETTINGS_STORAGE_KEY" in text
