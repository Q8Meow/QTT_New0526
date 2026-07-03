from tests.pr169_dash1_ui1.conftest import boot_data


def test_ui1_light_mode_not_separate_dashboard_state() -> None:
    data = boot_data()
    assert data["theme_contract"]["light_mode_not_separate_dashboard_state"] is True
    assert data["mobile_navigation"]["uses_same_OwnerDashboardStateV1"] is True
    assert data["conversation_state"]["uses_owner_dashboard_state_model"] is True
