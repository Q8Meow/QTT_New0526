from tests.pr169_dash1_ui1.conftest import MOBILE_TABS, boot_data, ui_text


def test_ui1_mobile_breakpoints_render_required_tabs() -> None:
    data = boot_data()
    text = ui_text()
    assert tuple(data["mobile_navigation"]["stable_tab_labels"]) == MOBILE_TABS
    assert "@media (max-width: 1199px)" in text
    assert "@media (max-width: 430px)" in text
    for tab in MOBILE_TABS:
        assert tab in text
