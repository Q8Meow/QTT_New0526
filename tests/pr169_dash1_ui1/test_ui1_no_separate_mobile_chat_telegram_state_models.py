from tests.pr169_dash1_ui1.conftest import boot_data, ui_doc


def test_ui1_no_separate_mobile_chat_telegram_state_models() -> None:
    data = boot_data()
    boundary = ui_doc("owner_dashboard_dash1_ui1_renderer_boundary.generated.json")
    assert boundary["second_mobile_state_model"] is False
    assert boundary["second_chat_state_model"] is False
    assert data["mobile_navigation"]["uses_same_OwnerDashboardStateV1"] is True
    assert data["communication_parity"]["single_conversation_state_model"] is True
