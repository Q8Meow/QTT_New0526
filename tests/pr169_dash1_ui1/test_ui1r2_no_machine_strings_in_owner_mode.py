from tests.pr169_dash1_ui1.r2_contract_assertions import assert_owner_mode_text_safety


def test_ui1r2_no_machine_strings_in_owner_mode() -> None:
    assert_owner_mode_text_safety()
