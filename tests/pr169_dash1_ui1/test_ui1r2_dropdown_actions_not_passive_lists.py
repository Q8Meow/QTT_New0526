from tests.pr169_dash1_ui1.r2_contract_assertions import assert_action_menu, assert_next_step_router


def test_ui1r2_dropdown_actions_not_passive_lists() -> None:
    assert_action_menu()
    assert_next_step_router()
