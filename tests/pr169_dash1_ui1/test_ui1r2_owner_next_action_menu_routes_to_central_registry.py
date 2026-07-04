from tests.pr169_dash1_ui1.r2_contract_assertions import assert_action_menu, assert_next_step_router


def test_ui1r2_owner_next_action_menu_routes_to_central_registry() -> None:
    assert_action_menu()
    assert_next_step_router()
