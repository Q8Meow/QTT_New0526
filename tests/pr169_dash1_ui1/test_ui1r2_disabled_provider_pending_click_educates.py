from tests.pr169_dash1_ui1.r2_contract_assertions import assert_disabled_actions_educate, assert_next_step_route


def test_ui1r2_disabled_provider_pending_click_educates() -> None:
    assert_next_step_route("NEXT_STEP_DISABLED_PROVIDER_PENDING_EDUCATION", "disabled-action-education", "DisabledActionEducationPreviewV1")
    assert_disabled_actions_educate()
