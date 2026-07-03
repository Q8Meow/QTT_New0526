from tests.pr169_dash1_ui1.conftest import boot_data, ui_text


def test_ui1_mobile_touch_targets_and_drilldown_drawer() -> None:
    nav = boot_data()["mobile_navigation"]
    text = ui_text()
    assert nav["touch_targets_minimum_px"] >= 44
    assert nav["drilldown_drawer_uses_bottom_sheet_on_mobile"] is True
    assert "min-height: 44px" in text
    assert "translateY(105%)" in text
    assert "drilldownDrawer" in text
