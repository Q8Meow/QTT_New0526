from tests.pr169_dash1_ui1.conftest import SEMANTIC_COLORS, boot_data, ui_text


def test_ui1_theme_semantic_colors_stable_in_both_modes() -> None:
    data = boot_data()
    text = ui_text()
    assert data["theme_contract"]["semantic_colors"] == SEMANTIC_COLORS
    for value in SEMANTIC_COLORS.values():
        assert value in text
    assert "colors_never_the_only_carrier_of_meaning" in data["theme_contract"]
