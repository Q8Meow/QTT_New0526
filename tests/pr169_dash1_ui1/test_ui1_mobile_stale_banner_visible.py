from tests.pr169_dash1_ui1.conftest import boot_data


def test_ui1_mobile_stale_banner_visible() -> None:
    data = boot_data()
    assert data["mobile_navigation"]["stale_data_banner_rendered_on_mobile_viewports"] is True
    banner = data["stale_data_banner"]
    assert banner["provider_state"] == "MATERIALIZED_IN_UI1"
    assert banner["read_only_or_actionable_mode"] == "READ_ONLY_LOCAL_STATIC"
