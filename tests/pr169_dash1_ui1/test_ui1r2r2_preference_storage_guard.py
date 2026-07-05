from tests.pr169_dash1_ui1.r2r2_contract_assertions import assert_preferences_no_private_state


def test_ui1r2r2_preference_storage_guard() -> None:
    assert_preferences_no_private_state()
